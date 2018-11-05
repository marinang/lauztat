#!/usr/bin/python
import pytest
import sys
import papermill as pm
import os
from statnight.calculators import AsymptoticCalculator
from statnight.parameters import Observable, Variable
from statnight.model import Model
from scipy.stats import norm
import numpy as np

location = "docs/examples/notebooks"


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

    AsymptoticCalculator(null_hypothesis, alt_hypothesis, data)

    with pytest.raises(ValueError):
        AsymptoticCalculator(m.create_hypothesis(), m.create_hypothesis(),
                             data)
    AsymptoticCalculator(null_hypothesis, m.create_hypothesis(), data)

    AsymptoticCalculator(m.create_hypothesis(), alt_hypothesis, data)


def test_properties():

    null_hypothesis = m.create_hypothesis(pois={"fs": 0.0})
    alt_hypothesis = m.create_hypothesis(pois={"fs": 0.6})

    calc = AsymptoticCalculator(null_hypothesis, alt_hypothesis, data)

    assert calc.qtilde is False
    assert calc.onesided is True
    assert calc.onesideddiscovery is False
    assert calc.CLs is True

    calc.qtilde = True
    assert calc.qtilde is True
    calc.onesided = False
    assert calc.onesided is False
    calc.onesideddiscovery = True
    assert calc.onesideddiscovery is True
    calc.CLs = False
    assert calc.CLs is False


# def test_notebook_upperlimit():
#
#     outputnb = '{0}/output.ipynb'.format(location)
#     common_kwargs = {
#         'output': str(outputnb),
#         'kernel_name': 'python{0}'.format(sys.version_info.major),
#         }
#
#     nb = "{0}/upperlimit_asymptotics.ipynb".format(location)
#
#     pm.execute_notebook(nb, **common_kwargs)
#
#     nb = pm.read_notebook(outputnb)
#
#     obs_ul_nsig = nb.data["obs_ul_nsig"]
#     exp_ul_nsig = nb.data["exp_ul_nsig"]
#     exp_ul_nsig_p1sigma = nb.data["exp_ul_nsig_p1sigma"]
#     exp_ul_nsig_m1sigma = nb.data["exp_ul_nsig_m1sigma"]
#
#     assert obs_ul_nsig == pytest.approx(10.4269, abs=0.05)
#     assert exp_ul_nsig == pytest.approx(10.7644, abs=0.05)
#     assert exp_ul_nsig_p1sigma == pytest.approx(14.9781, abs=0.05)
#     assert exp_ul_nsig_m1sigma == pytest.approx(7.7548, abs=0.05)
#
#     os.remove(outputnb)
#
#
# def test_notebook_discovery():
#
#     outputnb = '{0}/output.ipynb'.format(location)
#     common_kwargs = {
#         'output': str(outputnb),
#         'kernel_name': 'python{0}'.format(sys.version_info.major),
#         }
#
#     nb = "{0}/discovery_asymptotics.ipynb".format(location)
#
#     pm.execute_notebook(nb, **common_kwargs)
#
#     nb = pm.read_notebook(outputnb)
#
#     pnull = nb.data["pnull"]
#     significance = nb.data["significance"]
#     clb = nb.data["clb"]
#     clsb = nb.data["clsb"]
#
#     assert pnull <= 3E-7
#     assert significance >= 5
#     assert significance == pytest.approx(5.26, abs=0.005)
#     assert clb <= 3E-7
#     assert pnull == clb
#     assert clsb == pytest.approx(0.535, abs=0.005)
#
#     os.remove(outputnb)
