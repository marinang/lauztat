#!/usr/bin/python
import pytest

from statnight.parameters import Observable, Variable
from statnight.model import Model, Hypothesis
from scipy.stats import norm
from statnight.utils.pdf import Gaussian
import numpy as np

np.random.seed(10)


def pdf(x, mu, sigma):
    return norm.pdf(x, loc=mu, scale=sigma)


x = Observable("x", range=(-5, 5))
mu = Variable("mu", range=(-0.5, 0.5), initvalue=0.0, initstep=0.01)
sigma = Variable("sigma", range=(0.7, 1.3), initvalue=1.0, initstep=0.01)

data = np.random.normal(0.0, 1.0, 1000)


def test_model_constructors():

    Model(pdf)
    with pytest.raises(TypeError):
        Model()
    with pytest.raises(TypeError):
        Model("PDF")
    with pytest.raises(ValueError):
        def f(x, mu):
            return "{0}_{1}".format(x, mu)
        Model(f)

    Model(pdf, observables=[x], variables=[mu, sigma])
    with pytest.raises(ValueError):
        nu = Variable("nu", range=(-0.5, 0.5))
        Model(pdf, observables=[x], variables=[nu, sigma])
    with pytest.raises(ValueError):
        Model(pdf, observables=[x], variables=[mu, sigma, x])
    with pytest.raises(ValueError):
        nu = Variable("nu", range=(-0.5, 0.5))
        Model(pdf, observables=[x], variables=[mu, sigma], ext_pars=[nu])


def test_model_methods():

    m = Model(pdf)
    assert m.pdf == pdf
    assert m.pdf(0., 0., 1.) == pdf(0., 0., 1.)
    assert m.parameters == ["x", "mu", "sigma"]
    assert m.available_parameters() == ["x", "mu", "sigma"]
    assert m.has_unassigned() is True

    m.add_obs(x)
    assert type(m.obs) == list
    assert len(m.obs) == 1
    assert m.obs == m.observables
    assert m.obs[0] == x
    with pytest.raises(ValueError):
        m.add_obs(x)
    with pytest.raises(ValueError):
        m.add_obs(mu)

    assert m.available_parameters() == ["mu", "sigma"]
    assert m.has_unassigned() is True

    m.add_vars(mu)
    assert type(m.vars) == list
    assert len(m.vars) == 1
    assert m.vars == m.variables
    assert m.vars[0] == mu
    with pytest.raises(ValueError):
        m.add_vars(mu)
    with pytest.raises(ValueError):
        m.add_vars(x)

    assert m.available_parameters() == ["sigma"]
    assert m.has_unassigned() is True

    m.add_vars(sigma)
    assert len(m.vars) == 2
    assert m.vars[1] == sigma

    assert m.available_parameters() == []
    assert m.has_unassigned() is False

    assert m.extended is False
    assert m.ext_pars == []
    m.add_ext_pars("mu")
    assert m.extended is True
    assert m.ext_pars == ["mu"]
    with pytest.raises(ValueError):
        m.add_ext_pars(x)

    assert m["x"] == x
    assert m["mu"] == mu
    assert m["sigma"] == sigma
    with pytest.raises(KeyError):
        m["nu"]

    m.rm_obs("x")
    with pytest.raises(ValueError):
        m.rm_obs("mu")
    assert len(m.obs) == 0
    m.rm_vars("sigma")
    with pytest.raises(ValueError):
        m.rm_vars("x")
    assert len(m.vars) == 1
    assert m.vars[0] == mu
    assert m.ext_pars == ["mu"]
    m.rm_vars("mu")
    assert len(m.vars) == 0
    assert m.extended is False

    m.add_vars(mu)
    m.add_ext_pars("mu")
    m.rm_ext_pars("mu")
    with pytest.raises(ValueError):
        m.rm_ext_pars("x")
    assert m.extended is False
    assert len(m.vars) == 1
    assert m.vars[0] == mu


def test_nll_function():

    m = Model(pdf, observables=[x], variables=[mu, sigma])
    nll = m.nll_function(data)
    min_nll = nll(0.0, 1.0)

    assert min_nll <= nll(-0.1, 1.0)
    assert min_nll <= nll(0.1, 1.0)
    assert min_nll <= nll(0.0, 1.5)
    assert min_nll <= nll(0.0, 0.5)
    assert min_nll <= nll(0.1, 0.5)

    constraint = Gaussian(0.2, 0.001)
    _mu = Variable("mu", range=(-0.5, 0.5), initvalue=0.0, initstep=0.01,
                   constraint=constraint)
    m = Model(pdf, observables=[x], variables=[_mu, sigma])
    nll = m.nll_function(data)

    assert nll(0.2, 1.0) <= nll(0.0, 1.0)


def test_hypothesis():

    m = Model(pdf, observables=[x], variables=[mu, sigma])

    m.create_hypothesis(pois={"mu": 0.1})
    hypothesis = m.create_hypothesis(pois={"mu": [0.8, 0.9, 1.0, 1.1, 1.2]})

    with pytest.raises(TypeError):
        m.create_hypothesis(mu)
    with pytest.raises(ValueError):
        m.create_hypothesis({"nu": 0.1})
    with pytest.raises(ValueError):
        m_ = Model(pdf, observables=[x], variables=[mu])
        m_.create_hypothesis()

    assert hypothesis.pois == [mu]
    assert hypothesis.getpoi("mu") == mu
    with pytest.raises(KeyError):
        hypothesis.getpoi("nu")
    assert hypothesis.pois == hypothesis.parametersofinterest
    assert hypothesis.poivalues == {"mu": [0.8, 0.9, 1.0, 1.1, 1.2]}
    assert hypothesis.poinames == ["mu"]
    assert hypothesis.model == m
    assert hypothesis.nuis == [sigma]
    assert hypothesis.nuis == hypothesis.nuisanceparameters
    assert hypothesis.nuisnames == ["sigma"]
    hypothesis.summary()

    hypothesis = Hypothesis(m, pois={"mu": 0.1})
    with pytest.raises(TypeError):
        Hypothesis(pois={"mu": 0.1})
    with pytest.raises(TypeError):
        Hypothesis("Model")
