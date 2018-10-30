#!/usr/bin/python

import collections
import iminuit
from .parameters import Observable, Variable, Constant
from .utils.stats import compute_nll, integrate1d
import math


class Model:

    def __init__(self, pdf, observables=[], variables=[], ext_pars=[]):
        """ __init__ function """

        self._pdf = check_pdf(pdf)
        self._parameters = describe(pdf)

        self._obs = check_obs(observables)
        self._vars = check_vars(variables)
        self._ext_pars = check_ext_pars(ext_pars)
        self._check_params()

    @property
    def pdf(self):
        return self._pdf

    @property
    def parameters(self):
        return self._parameters

    def _available_parameters(self):
        _params = self.obs_names() + self.vars_names()
        return [p for p in self.parameters if p not in _params]

    def __getitem__(self, name):

        if name not in self.parameters:
            msg = "Unknown parameter {0} not in {1}"
            msg = msg.format(name, self.parameters)
            raise KeyError(msg)

        if name in self.obs_names():
            for o in self.obs:
                if o.name == name:
                    return o

        if name in self.vars_names():
            for v in self._vars:
                if v.name == name:
                    return v

    def create_hypothesis(self, pois={}):

        if len(self.obs) + len(self.vars) < len(self.parameters):
            _params = self.obs_names() + self.vars_names()
            not_assigned = [p for p in self.parameters if p not in _params]
            raise ValueError("{0} have still to be assigned to \
                    observables/variables.".format(not_assigned))

        return Hypothesis(self, pois)

    # Observables

    @property
    def obs(self):
        return list(self._obs)

    @property
    def observables(self):
        return self.obs

    def add_obs(self, observables):
        obs = check_obs(observables)
        _names = [o.name for o in obs]
        for n in _names:
            if n in self.obs_names():
                raise ValueError("'{0}' already in observables.".format(n))
        self._check_params(_names)
        self._obs += obs

    def rm_obs(self, name):
        if not isinstance(name, list):
            name = [name]
        for n in name:
            if n in self.obs_names():
                self._obs.remove(self[n])
            else:
                raise ValueError("{0} not in observables.".format(n))

    def obs_names(self):
        return [o.name for o in self.obs]

    # Variables

    @property
    def vars(self):
        return list(self._vars)

    @property
    def variables(self):
        return self.vars

    def add_vars(self, variables):
        _vars = check_vars(variables)
        _names = [v.name for v in _vars]
        for n in _names:
            if n in self.vars_names():
                raise ValueError("'{0}' already in variables.".format(n))
        self._check_params(_names)
        self._vars += _vars

    def rm_vars(self, name):
        if not isinstance(name, list):
            name = [name]
        for n in name:
            if n in self.vars_names():
                self._vars.remove(self[n])
                if n in self.ext_pars:
                    self._ext_pars.remove(n)
            else:
                raise ValueError("{0} not in variables.".format(n))

    def vars_names(self):
        return [v.name for v in self.vars]

    # Extended

    @property
    def ext_pars(self):
        return list(self._ext_pars)

    def add_ext_pars(self, ext_par):
        ext_par = check_ext_pars(ext_par)
        for e in ext_par:
            if e in self.ext_pars:
                msg = "'{0}' already in extended parameters."
                msg = msg.format(e)
                raise ValueError(msg)
        self._check_params(ext_par)
        self._ext_pars += ext_par

    def rm_ext_pars(self, name):
        if not isinstance(name, list):
            name = [name]
        for n in name:
            if n in self.ext_pars:
                self._ext_pars.remove(n)
            else:
                raise ValueError("{0} not in extended parameters.".format(n))

    @property
    def extended(self):
        if len(self.ext_pars) > 0:
            return True
        else:
            return False

    def _check_params(self, params=None):

        obs_ = self.obs_names()
        vars_ = self.vars_names()
        ext_pars = self.ext_pars
        pars_ = obs_ + vars_

        if params:
            if all(isinstance(p, Observable) for p in params):
                obs_ += params
            elif all(isinstance(p, Variable) for p in params):
                vars_ += params
            else:
                ext_pars += params

        pars = list(set(pars_+ext_pars+self.parameters))

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

        ext_in_obs = [e for e in ext_pars if e in obs_]
        if len(ext_in_obs):
            msg = "{0} cannot be both in observables and in \
            extended parameters!"
            msg = msg.format(ext_in_obs)
            raise ValueError(msg)

    def nll_function(self, data, weights=None):

        def compute_null(*args):

            kwargs = {v.name: args[i] for i, v in enumerate(self.variables)}

            nll = compute_nll(self.pdf, data, weights, *args)

            if self.extended:
                nll += integrate1d(self.pdf, self.obs[0].range, 100, *args)

            for v in self.variables:
                if isinstance(v, Variable) and v.constraint is not None:
                    fromstatnight = "statnight.utils.pdf" in repr(v.constraint)
                    hasnll = hasattr(v.constraint, "nll")
                    if fromstatnight and hasnll:
                        nll += v.constraint.nll(kwargs[v.name])
                    else:
                        nll += -math.log(v.constraint(kwargs[v.name]))
                else:
                    continue

            return nll

        doc = "def f("+",".join(self.vars_names())+")"
        compute_null.__doc__ = doc

        return compute_null


# Hypothesis


class Hypothesis:

    def __init__(self, model, pois={}):
        """ __init__ function """

        if not isinstance(model, Model):
            raise TypeError("Please provide a Model.")

        if not isinstance(pois, dict):
            msg = "Please provide a dictionnary with the name of "
            msg += "the pois as keys and their and their value as"
            msg += " values."
            raise TypeError(msg)

        unknown_pois = [p for p in pois.keys() if p not in model.vars_names()]
        if len(unknown_pois) > 0:
            msg = "Unknown parameters {0} not in {1}"
            msg = msg.format(unknown_pois, model.vars_names())
            raise ValueError(msg)

        self._model = model
        self._pois = [model[p] for p in pois.keys()]
        self._poivalues = pois

        def in_pois(x):
            return x.name in self.poinames
        self._nuis = [v for v in model.variables if not in_pois(v)]

    @property
    def pois(self):
        return self._pois

    @property
    def poivalues(self):
        return dict(self._poivalues)

    @property
    def poinames(self):
        return [p.name for p in self.pois]

    @property
    def parametersofinterest(self):
        return self.pois

    def getpoi(self, name):

        if name not in self.poinames:
            msg = "Unknown parameter {0} not in {1}"
            msg = msg.format(name, self.poinames)
            raise KeyError(msg)
        else:
            for p in self.pois:
                if p.name == name:
                    return p

    @property
    def model(self):
        return self._model

    @property
    def nuis(self):
        return self._nuis

    @property
    def nuisanceparameters(self):
        return self.nuis

    @property
    def nuisnames(self):
        return [n.name for n in self.nuis]

    def _summary(self):

        obs_names = self.model.obs_names()
        nuis_names = [n.name for n in self.nuis]

        toprint = "Observables: {0}\n".format(obs_names)
        toprint += "Paramaters of interest: {0}\n".format(self.poivalues)
        toprint += "Nuisance parameters: {0}\n".format(nuis_names)
        toprint += "Extended parameters: {0}\n".format(self.model.ext_pars)

        return toprint

    def summary(self):
        print(self._summary())

    def __repr__(self):
        ret = "Hypothesis object: \n"
        ret += self._summary()
        return ret

# UTILITIEs


def check_pdf(_pdf):
    if hasattr(_pdf, "__call__"):
        args = [1.0 for n in range(len(describe(_pdf)))]
        test_return = _pdf(*args)
        if not isinstance(test_return, (int, float)):
            msg = "Please provide a function that returns a number"
            msg += " (int/float)."
            raise ValueError(msg)
        return _pdf
    else:
        msg = "Please provide a probability density function returning"
        msg += "a number (int/float)."
        raise TypeError(msg)


def check_obs(observables):

    if not isinstance(observables, list):
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

    if not isinstance(variables, list):
        variables = [variables]
    variables = list(variables)

    if len(variables) == 0:
        return variables
    else:
        if not all(isinstance(v, (Variable, Constant)) for v in variables):
            msg = "Please provide a Variable (a list of Variable's)"
            raise ValueError(msg)
        return variables


def check_ext_pars(ext_pars):

    if not isinstance(ext_pars, list):
        ext_pars = [ext_pars]
    ext_pars = list(ext_pars)

    if len(ext_pars) == 0:
        return ext_pars
    else:
        if not all(isinstance(e, str) for e in ext_pars):
            msg = "Please provide a list of strings for the extended"
            msg += "  parameters."
            raise ValueError(msg)
        return ext_pars


def describe(function):
    return iminuit.describe(function)


def has_duplicates(list_of_values):
    value_dict = collections.defaultdict(int)
    for item in list_of_values:
        value_dict[item] += 1
    return any(val > 1 for val in value_dict.values())


def haspdf(hypothesis):

    if isinstance(hypothesis, Hypothesis) and hypothesis.pdf is not None:
        return True
    else:
        return False
