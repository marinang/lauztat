#!/usr/bin/python
import pytest

from statnight.calculators.calculator import Calculator
from statnight.parameters import Observable, Variable
from statnight.model import Model
from scipy.stats import norm
import numpy as np


def pdf(x, mu, sigma, fs):
    return fs * norm.pdf(x, loc=mu, scale=sigma)


data = np.random.normal(0.0, 1.0, 1000)

x = Observable("x", range=(-5, 5))
mu = Variable("mu", range=(-0.5, 0.5), initvalue=0.0, initstep=0.01)
sigma = Variable("sigma", range=(0.7, 1.3), initvalue=1.0, initstep=0.01)
fs = Variable("fs", range=(0., 1.0), initvalue=0.2, initstep=0.01)

m = Model(pdf, observables=[x], variables=[mu, sigma, fs])


def test_constructors():

    null_hypothesis = m.create_hypothesis(pois={"fs": 0.0})
    alt_hypothesis = m.create_hypothesis(pois={"fs": 0.6})

    Calculator(null_hypothesis, alt_hypothesis, data)
    with pytest.raises(TypeError):
        Calculator()
    with pytest.raises(TypeError):
        Calculator(null_hypothesis, alt_hypothesis)
    with pytest.raises(TypeError):
        Calculator(null_hypothesis, alt_hypothesis)
    with pytest.raises(TypeError):
        Calculator(null_hypothesis, alt_hypothesis, null_hypothesis)
    with pytest.raises(TypeError):
        Calculator(data, alt_hypothesis, null_hypothesis)
    with pytest.raises(TypeError):
        Calculator(alt_hypothesis, data, null_hypothesis)
    with pytest.raises(ValueError):
        Calculator(m.create_hypothesis(), m.create_hypothesis(), data)


def test_methods():

    null_hypothesis = m.create_hypothesis(pois={"fs": 0.0})
    alt_hypothesis = m.create_hypothesis(pois={"fs": 0.6})

    calc = Calculator(null_hypothesis, alt_hypothesis, data)

    assert calc.null_hypothesis == null_hypothesis
    assert calc.alt_hypothesis == alt_hypothesis
    assert calc.data.all() == data.all()
