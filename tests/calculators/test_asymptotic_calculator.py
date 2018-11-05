#!/usr/bin/python
import pytest
from statnight.calculators import AsymptoticCalculator
from statnight.parameters import Observable, Variable, Constant
from statnight.model import Model
from scipy.stats import norm
from statnight.utils.pdf import Gaussian, gaussian, exponential
import numpy as np
import matplotlib
matplotlib.use('Agg')

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

    alt_hypothesis2 = m.create_hypothesis(pois={"fs": 0.6, "mu": 0.2})

    with pytest.raises(ValueError):
        AsymptoticCalculator(null_hypothesis, alt_hypothesis2, data)

    null_hypothesis = m.create_hypothesis(pois={"fs": 0.0})
    alt_hypothesis = m.create_hypothesis(pois={"mu": 0.6})

    with pytest.raises(ValueError):
        AsymptoticCalculator(null_hypothesis, alt_hypothesis, data)


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
    with pytest.raises(ValueError):
        calc.qtilde = "True"
    calc.onesided = False
    assert calc.onesided is False
    with pytest.raises(ValueError):
        calc.onesided = "True"
    calc.onesideddiscovery = True
    assert calc.onesideddiscovery is True
    with pytest.raises(ValueError):
        calc.onesideddiscovery = "True"
    calc.CLs = False
    assert calc.CLs is False
    with pytest.raises(ValueError):
        calc.CLs = "True"


class SignalBackgroundModel(object):

    def __init__(self, bounds):
        self._bounds = bounds

    def exp_norm(self, x, tau):
        ret = exponential(x, tau)
        norm = exponential.integrate(self._bounds, 100, tau)
        return ret/norm

    def gauss_norm(self, x, mu, sigma):
        ret = gaussian(x, mu, sigma)
        norm = gaussian.integrate(self._bounds, 100, mu, sigma)
        return ret / norm

    def exp_ext(self, x, tau, Nbkg):
        ret = self.exp_norm(x, tau)
        return ret * Nbkg

    def gauss_ext(self, x, mu, sigma, Nsig):
        ret = self.gauss_norm(x, mu, sigma)
        return ret * Nsig

    def __call__(self, x, mu, sigma, Nsig, tau, Nbkg):
        ret = self.gauss_ext(x, mu, sigma, Nsig)
        ret += self.exp_ext(x, tau, Nbkg)
        return ret


def test_upperlimit():

    bounds = (0.1, 3.0)

    np.random.seed(0)
    tau = -2.0
    beta = -1/tau
    data = np.random.exponential(beta, 300)
    peak = np.random.normal(1.2, 0.1, 4)
    data = np.concatenate((data, peak))
    data = data[(data > 0.1) & (data < 3)]

    totpdf = SignalBackgroundModel(bounds)

    model_sb = Model(totpdf)
    model_sb.add_obs(Observable("x", range=bounds))

    mean = Constant("mu", value=1.2)
    sigma = Constant("sigma", value=0.1)
    Nsig = Variable("Nsig", range=(-10, len((data))), initvalue=0.0,
                    initstep=1.0)
    tau_constraint = Gaussian(mean=2.02224, sigma=0.0750417)
    tau = Variable("tau", range=(0.1, 5.0), initvalue=0.5, initstep=0.05,
                   constraint=tau_constraint)
    Nbkg = Variable("Nbkg", range=(0, len((data))*1.1), initvalue=len(data),
                    initstep=1.0)

    model_sb.add_vars([mean, sigma, Nsig, tau, Nbkg])
    model_sb.add_ext_pars(["Nsig", "Nbkg"])

    pois = {"Nsig": np.linspace(0.1, 12, 60)}
    null_hypothesis = model_sb.create_hypothesis(pois)

    alt_hypothesis = model_sb.create_hypothesis({"Nsig": 0})

    calc = AsymptoticCalculator(null_hypothesis, alt_hypothesis, data)
    calc.qtilde = False
    calc.CLs = True

    calc.bestfitpoi = -0.613242
    calc.bestfitpoi

    ul = calc.upperlimit()

    assert ul["observed"] == pytest.approx(10.4269, abs=0.05)
    assert ul["median"] == pytest.approx(10.7644, abs=0.05)
    assert ul["band_p1"] == pytest.approx(14.9781, abs=0.05)
    assert ul["band_m1"] == pytest.approx(7.7548, abs=0.05)

    calc.plot(show=False)



def test_discovery():

    bounds = (0.1, 3.0)

    np.random.seed(0)
    tau = -2.0
    beta = -1/tau
    data = np.random.exponential(beta, 300)
    peak = np.random.normal(1.2, 0.1, 40)
    data = np.concatenate((data, peak))
    data = data[(data > bounds[0]) & (data < bounds[1])]

    totpdf = SignalBackgroundModel(bounds)

    model_sb = Model(totpdf)
    model_sb.add_obs(Observable("x", range=bounds))

    mean = Constant("mu", value=1.2)
    sigma = Constant("sigma", value=0.1)
    Nsig = Variable("Nsig", range=(-10, len((data))), initvalue=0.0,
                    initstep=1.0)
    tau = Variable("tau", range=(0.1, 5.0), initvalue=0.5, initstep=0.05)
    Nbkg = Variable("Nbkg", range=(0, len((data))*1.1), initvalue=len(data),
                    initstep=1.0)

    model_sb.add_vars([mean, sigma, Nsig, tau, Nbkg])
    model_sb.add_ext_pars(["Nsig", "Nbkg"])

    null_hypothesis = model_sb.create_hypothesis({"Nsig": 0})

    pois = {"Nsig": 34.9159}
    alt_hypothesis = model_sb.create_hypothesis(pois)

    calc = AsymptoticCalculator(null_hypothesis, alt_hypothesis, data)
    calc.qtilde = False
    calc.CLs = True
    calc.onesideddiscovery = True

    result = calc.result()

    assert result["pnull"] <= 3E-7
    assert result["significance"] >= 5
    assert result["significance"] == pytest.approx(5.26, abs=0.005)
    assert result["clb"] <= 3E-7
    assert result["clb"] == result["pnull"]
    assert result["clsb"] == pytest.approx(0.535, abs=0.005)
