from iminuit import describe, Minuit
from ..parameters import Observable, Variable, Constant, GaussianConstrained
import collections
from ..utils.stats import integrate1d
import copy
from probfit import gen_toy
from scipy.stats import norm, poisson

"""
Wrappers for iminuit and pdf and loss function from probfit
"""


class func_code(object):
    def __init__(self, arg):
        self.co_varnames = tuple(arg)
        self.co_argcount = len(arg)


class ModelWrapper(object):

    def __init__(self, model, observables=[], variables=[], extended=False):
        """
        __init__ function
        """
        hascall = hasattr(model, "__call__")
        hasintegrate = hasattr(model, "integrate")

        if not(hascall and hasintegrate):
            msg = "{0} doesn't seem to be a model."
            raise ValueError(msg.format(model))

        self._model = model
        self._parameters = describe(model)
        self._extended = extended

        self._obs = check_obs(observables)
        self._vars = check_vars(variables)
        self._check_params()
        self.func_code = func_code(self.parameters)

    def copy(self):
        return ModelWrapper(self.model, self.obs, self.vars, self.extended)

    @property
    def model(self):
        return self._model

    def __call__(self, *args):
        return self.model(*args)

    def integrate(self, *args):
        return self.model.integrate(*args)

    @property
    def parameters(self):
        return self._parameters

    @property
    def extended(self):
        """
        Returns True is the model is extended, else False.
        """
        return self._extended

    @extended.setter
    def extended(self, bool):
        """
        Set True is the model is extended, else False.
        """
        self._extended = bool

    # Observables

    @property
    def observables(self):
        """
        Returns the observables of the model.
        """
        return self.obs

    @property
    def obs(self):
        """
        Returns the observables of the model, same as observables.
        """
        return list(self._obs)

    def add_obs(self, *observables):
        """
        Add observables to the model.

        **Arguments:**

            -**observables** an/a list of statnight.parameters.Observable.
        """
        obs = check_obs(observables)
        _names = [o.name for o in obs]
        for n in _names:
            if n in self.obs_names():
                raise ValueError("'{0}' already in observables.".format(n))
        self._check_params(obs)
        self._obs += obs

    def rm_obs(self, names):
        """
        Remove observables from the model.

        **Arguments:**

            -**names** a list of strings.
        """
        if not isinstance(names, list):
            names = [names]
        for n in names:
            par = next(o for o in self.obs if o.name == n)
            if par is not None:
                self._vars.remove(par)
            else:
                raise ValueError("{0} not in observables.".format(n))

    def obs_names(self):
        """
        Returns the names of the observables.
        """
        return [o.name for o in self.obs]

    # Variables

    @property
    def variables(self):
        """
        Returns the variables of the model.
        """
        return self.vars

    @property
    def vars(self):
        """
        Returns the variables of the model, same as variables.
        """
        return list(self._vars)

    def add_vars(self, *variables):
        """
        Add variables to the model.

        **Arguments:**

            -**variables** an/a list of statnight.parameters.Variable.
        """
        _vars = check_vars(variables)
        _names = [v.name for v in _vars]
        for n in _names:
            if n in self.vars_names():
                raise ValueError("'{0}' already in variables.".format(n))
        self._check_params(_vars)
        self._vars += _vars

    def rm_vars(self, names):
        """
        Remove variables from the model.

        **Arguments:**

            -**names** a list of strings.
        """
        if not isinstance(names, list):
            names = [names]
        for n in names:
            par = next(v for v in self.vars if v.name == n)
            if par is not None:
                self._vars.remove(par)
            else:
                raise ValueError("{0} not in variables.".format(n))

    def vars_names(self):
        """
        Returns the names of the variables.
        """
        return [v.name for v in self.vars]

    def parts(self):
        if hasattr(self.model, "parts"):
            return self.model.parts()
        else:
            return None

    def _check_params(self, params=None):

        obs_ = self.obs_names()
        vars_ = self.vars_names()

        if params:
            for p in params:
                if isinstance(p, Observable):
                    obs_.append(p.name)
                elif isinstance(p, (Variable, Constant)):
                    vars_.append(p.name)

        pars_ = obs_ + vars_

        pars = list(set(pars_+self.parameters))

        if len(pars) > len(self.parameters):
            unwanted_pars = [p for p in pars if p not in self.parameters]
            msg = "Unknown parameters {0} not in {1}"
            msg = msg.format(unwanted_pars, self.parameters)
            raise ValueError(msg)

        if len(pars_) > len(self.parameters) or has_duplicates(pars_):
            duplicates = []
            for p in pars_:
                if p in obs_ and p in vars_:
                    duplicates.append(p)
            duplicates = list(set(duplicates))
            msg = "{0} cannot be both in observables and in variables!"
            msg = msg.format(duplicates)
            raise ValueError(msg)

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

        return gen_toy(self.model, nsample, bound=self.obs[0].range, **kwargs)

    def todict(self):
        dict = {}
        for o in self.obs:
            dict[o.name] = o.todict()
        for v in self.vars:
            dict[v.name] = v.todict()
        dict["extended"] = self.extended
        return dict


class LossFunctionWrapper(object):

    def __init__(self, lossfunction):

        self._lossfunction = lossfunction
        self._parameters = describe(lossfunction)
        lossattrs = dir(lossfunction)

        model = next(a for a in lossattrs if a in ["model", "pdf", "f"])
        if model is None:
            raise ValueError("Model not found in loss function.")

        self._model = getattr(lossfunction, model)

        if not isinstance(self._model, ModelWrapper):
            raise ValueError("Model need to be wrapped under\
                             statnight.utils.ModelWrapper.")

        self._data = getattr(lossfunction, "data", None)
        if self._data is None:
            raise ValueError("Data not found in loss function.")

        self._weights = getattr(lossfunction, "weights", None)

        self._extinloss = getattr(lossfunction, "extended", False)

        self.func_code = func_code(self.parameters)

    def __call__(self, *args):
        kwargs = {p: args[i] for i, p in enumerate(self.parameters)}

        ret = self.lossfunction(*args)
        if not self._extinloss and self.model.extended:
            ret += integrate1d(self.model, self.model.obs[0].range, 200, *args)
        for p in self.model.vars:
            if hasattr(p, "log_evalconstraint"):
                ret += -p.log_evalconstraint(kwargs[p.name])
        return ret

    @property
    def lossfunction(self):
        return self._lossfunction

    @property
    def parameters(self):
        return self._parameters

    @property
    def model(self):
        return self._model

    @property
    def data(self):
        return self._data

    @property
    def weights(self):
        return self._weights

    def copy(self):
        lossfunction = copy.deepcopy(self.lossfunction)
        return LossFunctionWrapper(lossfunction)


class MinimizerWrapper(object):

    def __init__(self, lossfunction, **kwargs):

        if not isinstance(lossfunction, LossFunctionWrapper):
            raise ValueError("Loss function need to be wrapped under\
                             statnight.utils.LossFunctionWrapper.")
        for v in lossfunction.model.variables:
            pars = v.tominuit()
            kwargs.update(pars)

        minuit = Minuit(lossfunction, errordef=0.5, **kwargs)

        self._minuit = minuit

    def minimize(self):
        self._minuit.migrad()

    @property
    def values(self):
        return self._minuit.values

    @property
    def errors(self):
        return self._minuit.errors

    def profile(self, param, value):
        range = (value, -1.)
        prof = self._minuit.mnprofile(param, 1, range)
        if prof[1] > 0:
            print("WARNING! Large positive value for EDM for ", value)
        return prof[1]


def check_obs(observables):

    if not isinstance(observables, (list, tuple)):
        observables = [observables]
    observables = list(observables)

    if len(observables) == 0:
        return observables
    else:
        if not all(isinstance(obs, Observable) for obs in observables):
            msg = "Please provide a Observable (a list of Observable's)"
            raise ValueError(msg)
        return observables


def check_vars(variables):

    if not isinstance(variables, (list, tuple)):
        variables = [variables]
    variables = list(variables)

    validtypes = (Variable, Constant, GaussianConstrained)

    if len(variables) == 0:
        return variables
    else:
        if not all(isinstance(v, validtypes) for v in variables):
            msg = "Please provide a Variable (a list of Variable's)"
            raise ValueError(msg)
        return variables


def has_duplicates(list_of_values):
    value_dict = collections.defaultdict(int)
    for item in list_of_values:
        value_dict[item] += 1
    return any(val > 1 for val in value_dict.values())
