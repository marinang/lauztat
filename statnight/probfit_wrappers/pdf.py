from iminuit import describe
from probfit import pdf, Normalized, Extended, AddPdfNorm, AddPdf, gen_toy
import attr
from ..parameters import Space, Parameter
import numpy as np
from scipy.stats import norm, poisson


class func_code(object):
    def __init__(self, arg):
        self.co_varnames = tuple(arg)
        self.co_argcount = len(arg)


class PDF(object):

    def __init__(self, func, parameters=[], yield_=None):
        """
        __init__ function
        """

        hascall = hasattr(func, "__call__")

        if not(hascall):
            msg = "{0} doesn't seem to be a model."
            raise ValueError(msg.format(func))

        self._func = func
        self._parameters = parameters
        self._yield = yield_
        # self._obs = None

    @property
    def func(self):
        return self._func

    @property
    def parameters(self):
        return self._parameters

    @property
    def extended(self):
        if self.get_yield() is not None:
            return True
        else:
            return False

    def get_yield(self):
        return self._yield

    @property
    def func_code(self):
        names = ["x"]
        # names += [p.name for p in self.parameters]
        return func_code(names)

    def __call__(self, x):
        args = [x]
        for p in self.parameters:
            args.append(p.value)
        return self.func(*args)

    def pdf(self, x, bounds=None):
        if isinstance(x, np.ndarray):
            ret = np.empty(x.shape)
            for i, x_ in np.ndenumerate(x):
                ret[i] = self.__call__(x_)
            return ret
        else:
            return self.__call__(x)

    def integrate(self, bounds, nint=100):
        args = [bounds, nint]
        for p in self.parameters:
            args.append(p.value)
        return self.func.integrate(*args)

    def todict(self):
        dict = {}
        for o in self.obs:
            dict[o.name] = o.todict()
        for v in self.vars:
            dict[v.name] = v.todict()
        dict["extended"] = self.extended
        return dict

    def create_extended(self, yield_):

        if not isinstance(yield_, Parameter):
            msg = "Incorrect type for 'yield'. 'Parameter' expected!"
            raise TypeError(msg)

        if self.extended:
            raise ValueError("...")

        f = Extended(self.func, yield_.name)

        params = self.parameters + [yield_]

        return PDF(f, params, yield_=yield_)

    def __mul__(self, other):

        if isinstance(other, Parameter):
            return self.create_extended(other)
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, PDF):
            return SumPDF(pdfs=[self, other])
        else:
            return NotImplemented

    def sample(self, nsample=None, **kwargs):

        if not self.extended:
            if nsample is None:
                msg = "Please provide the number of sample to generate."
                raise ValueError(msg)
        else:
            nsample = 0

        for p in self.variables:
            if isinstance(p, GaussianConstrained):
                val = norm.rvs(loc=p.mu, scale=p.sigma)
                kwargs[p.name] = val
            elif self.extended:
                if isinstance(p, Variable) and p.isyield:
                    val = poisson.rvs(mu=kwargs[p.name])
                    kwargs[p.name] = val
                    nsample += val

        return gen_toy(self.model, nsample, bound=self.obs.range, **kwargs)


pdf_funcs = dir(pdf)
to_ignore = ["_", "np", "MinimalFuncCode"]

__parameters__ = {}
__funcs__ = {}

for func in pdf_funcs:
    if any(i in func for i in to_ignore):
        continue
    f = getattr(pdf, func)
    if not hasattr(f, "__call__"):
        continue
    __funcs__[func] = f

    attr_ = attr.ib(validator=[attr.validators.instance_of(Parameter)])

    parameters = list(describe(f))
    if "x" in parameters:
        parameters.remove("x")
    if "lambda" in parameters:
        parameters.remove("lambda")
        parameters.append("lambda_")
    __parameters__[func] = parameters
    attributes = {k: attr_ for k in parameters}
    attributes["obs"] = attr.ib(validator=[attr.validators.instance_of(Space)])

    def post_init(self):
        name = self.__class__.__name__
        params = [getattr(self, p) for p in __parameters__[name]]
        f = __funcs__[name]
        bounds = self.obs.range
        f = Normalized(f, bounds)
        super(type(self), self).__init__(f, params, None)

        # self._func = Normalized(f, bounds)
        # self._parameters = params
        # self._yield = None

    attributes["__attrs_post_init__"] = post_init

    cls = attr.make_class(func, attributes, bases=(PDF,))

    globals()[func] = cls


class SumPDF(PDF):

    def __init__(self, pdfs, fracs=[]):

        valid_pdfs = isinstance(pdfs, (list, tuple))
        valid_pdfs = valid_pdfs and all(isinstance(p, PDF) for p in pdfs)

        if not valid_pdfs:
            msg = "Incorrect type for pdfs. 'list' or 'tuple' of 'PDF'"
            msg += " expected."
            raise ValueError(msg)

        valid_fracs = isinstance(fracs, (list, tuple))
        valid_fracs = valid_fracs and (all(isinstance(f, Parameter)
                                           for f in fracs)
                                       or len(fracs) == 0)

        if not valid_fracs:
            msg = "Incorrect type for fracs. 'list' or 'tuple' of 'Parameters'"
            msg += " (or empty) expected."
            raise ValueError(msg)

        self.pdfs = pdfs
        self.fracs = fracs
        funcs = [p.func for p in pdfs]

        extended_pdfs = [p.extended for p in pdfs]

        implicit = None
        extended = None
        if all(extended_pdfs):
            implicit = True
            extended = True

        # all extended except one -> fraction
        elif sum(extended_pdfs) == len(extended_pdfs) - 1:
            implicit = True
            extended = False

        # no pdf is extended -> using `fracs`
        elif not any(extended_pdfs) and fracs is not None:
            # make extended
            if len(fracs) == len(pdfs):
                implicit = False
                extended = True
            elif len(fracs) == len(pdfs) - 1:
                implicit = False
                extended = False

        value_error = implicit is None or extended is None
        if (implicit and len(fracs) > 0) or value_error:
            raise ValueError("")

        if not extended and implicit:
            raise NotImplementedError

        elif not extended and not implicit:
            func = AddPdfNorm(*funcs, facname=[f.name for f in fracs])
            params = []
            for p in pdfs:
                for p_ in p.parameters:
                    if p_ in params:
                        continue
                    else:
                        params.append(p_)
            params += fracs

            super(SumPDF, self).__init__(func, params)

        elif extended and not implicit:
            yields = fracs
            pdfs = [pdf.create_extended(yield_)
                    for pdf, yield_ in zip(pdfs, yields)]
            funcs = [p.func for p in pdfs]

            func = AddPdf(*funcs)
            params = []
            for p in pdfs:
                for p_ in p.parameters:
                    if p_ in params:
                        continue
                    else:
                        params.append(p_)
            params = list(set(params))
            params += yields

            super(SumPDF, self).__init__(func, params)

        elif extended and implicit:
            func = AddPdf(*funcs)
            params = []
            for p in pdfs:
                for p_ in p.parameters:
                    if p_ in params:
                        continue
                    else:
                        params.append(p_)

            super(SumPDF, self).__init__(func, params)
