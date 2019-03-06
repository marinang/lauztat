from iminuit import describe
from probfit import UnbinnedLH, SimultaneousFit, BinnedLH
from .pdf import PDF
from ..parameters import Space, Parameter
import numpy as np


class func_code(object):
    def __init__(self, arg):
        self.co_varnames = tuple(arg)
        self.co_argcount = len(arg)


class Loss(object):

    def __init__(self):
        pass


class UnbinnedNLL(Loss):

    def __init__(self, model, data, fit_range):

        super(Loss, self).__init__()

        if not isinstance(model, PDF):
            msg = "Incorrect type for 'model'. 'PDF' expected."
            raise TypeError(msg)

        self.model = model

        if not isinstance(data, np.ndarray):
            msg = "Incorrect type for 'data'. 'np.ndarray' expected."
            raise TypeError(msg)

        self.data = data

        if not isinstance(fit_range, Space):
            msg = "Incorrect type for 'fit_range'. 'Space' expected."
            raise TypeError(msg)

        self.fit_range = fit_range

        self.func_code = func_code([])

        self._parameters = model.parameters

        self._loss = UnbinnedLH(model, data)

    @property
    def parameters(self):
        return self._parameters

    @property
    def loss(self):
        return self._loss

    def loss_function(self, parameters=None):

        if parameters is None:
            floatings = [p for p in self.parameters if p.floating]
            # fixed_params = [p for p in self.parameters if not p.floating]
        else:
            msg = "Incorrect type for 'parameters'. list or tuple of"
            msg += " 'Parameter' expected."

            if not isinstance(parameters, (list, tuple)):
                raise TypeError(msg)
            elif not all(isinstance(p, Parameter) for p in parameters):
                raise TypeError(msg)

            floatings = [p for p in parameters if p.floating]
            # fixed_params = [p for p in self.parameters if p not in floatings]

        def ret(*args):

            assert len(args) == len(floatings)

            for i, f in enumerate(floatings):
                f.set_value(args[i])

            return self.loss()

        return Function(ret, floatings), floatings

    @property
    def errordef(self):
        return self.loss.default_errordef()

    def __call__(self):
        #args = [p.value for p in self.parameters]
        #ret = self.loss(*args)
        return self.loss()

    def value(self):
        return self.__call__()


class ExtendedUnbinnedNLL(UnbinnedNLL):

    def __init__(self, model, data, fit_range):

        super(ExtendedUnbinnedNLL, self).__init__(model, data, fit_range)

        self._loss = UnbinnedLH(model, data, extended=True,
                                extended_bound=fit_range.range)


class Function(object):

    def __init__(self, func, parameters):

        self.func = func
        self.parameters = [p.name for p in parameters]
        self.func_code = func_code(self.parameters)

    def __call__(self, *args):
        return self.func(*args)
