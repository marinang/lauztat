import pytest

from lauztat.calculators import FrequentistCalculator, AsymptoticCalculator
from lauztat.config import Config
from lauztat.parameters import POI
from lauztat.hypotests import ConfidenceInterval
import numpy as np
import os
import matplotlib as mpl
mpl.use('Agg')
pwd = os.path.dirname(__file__)


def test_constructors():

    with pytest.raises(TypeError):
        ConfidenceInterval()


bounds = (0.1, 3.0)

# Data and signal

np.random.seed(0)
tau = -2.0
beta = -1/tau
data = np.random.exponential(beta, 500)
peak = np.random.normal(1.2, 0.1, 80)
data = np.concatenate((data, peak))
data = data[(data > bounds[0]) & (data < bounds[1])]


def test_with_zfit():

    import zfit
    from zfit.core.loss import ExtendedUnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer

    obs = zfit.Space('x', limits=bounds)

    mean = zfit.Parameter("mean_ci", 1.2, 0.5, 2.0)
    sigma = zfit.Parameter("sigma_ci", 0.1, 0.02, 0.2)
    lambda_ = zfit.Parameter("lambda_ci", -2.0, -4.0, -1.0)
    Nsig = zfit.Parameter("Nsig_ci", 20., 0., len(data))
    Nbkg = zfit.Parameter("Nbkg_ci", len(data), 0., len(data)*1.1)

    model_bkg = zfit.pdf.Exponential(obs=obs, lambda_=lambda_)
    signal = Nsig * zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)
    background = Nbkg * model_bkg
    tot_model = signal + background

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data, weights=None):
        loss = ExtendedUnbinnedNLL(model=model, data=data, fit_range=[obs])
        return loss

    config = Config(tot_model, data_, lossbuilder, MinuitMinimizer())

    poinull = POI(mean, value=np.linspace(1.15, 1.26, 30))
    mean_bf = config.bestfit.params[mean]["value"]

    def test_asy():
        calc = AsymptoticCalculator(config)
        ci = ConfidenceInterval(poinull, calc)
        ret = ci.interval()
        ci.plot()
        return ret

    ra = test_asy()

    assert ra["band_m"] <= mean_bf <= ra["band_p"]
    assert ra["band_m"] == pytest.approx(1.1890518753693258, rel=0.01)
    assert ra["band_p"] == pytest.approx(1.2249924635033214, rel=0.01)
