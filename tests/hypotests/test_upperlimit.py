import pytest

from lauztat.calculators import FrequentistCalculator, AsymptoticCalculator
from lauztat.config import Config
from lauztat.parameters import POI
from lauztat.hypotests import UpperLimit
import numpy as np
import os
pwd = os.path.dirname(__file__)


def test_constructors():

    with pytest.raises(TypeError):
        UpperLimit()


bounds = (0.1, 3.0)

np.random.seed(0)
tau = -2.0
beta = -1/tau
data = np.random.exponential(beta, 300)
peak = np.random.normal(1.2, 0.1, 10)
data = np.concatenate((data, peak))
data = data[(data > bounds[0]) & (data < bounds[1])]

lambda_mu = -2.022148383099551
lambda_sigma = 0.0748696


def test_freq_with_zfit():

    import zfit
    from zfit.core.loss import ExtendedUnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer

    obs = zfit.Space('x', limits=bounds)

    lambda_ = zfit.Parameter("lambda_UL_freq", -2.0, -4.0, -0.5)
    mean = zfit.Parameter("mean_UL_freq", 1.2, 0.1, 2., floating=False)
    sigma = zfit.Parameter("sigma_UL_freq", 0.1, floating=False)
    Nsig = zfit.Parameter("Nsig_UL_freq", 1., -20., len(data))
    Nbkg = zfit.Parameter("Nbkg_UL_freq", len(data), 0., len(data)*1.1)

    model_bkg = zfit.pdf.Exponential(obs=obs, lambda_=lambda_)
    signal = Nsig * zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)
    background = Nbkg * model_bkg
    tot_model = signal + background

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data, weights=None):
        constraint = zfit.constraint.nll_gaussian(params=[lambda_],
                                                  mu=[lambda_mu],
                                                  sigma=[lambda_sigma])
        loss = ExtendedUnbinnedNLL(model=model, data=data, fit_range=[obs],
                                   constraints=constraint)
        return loss

    config = Config(tot_model, data_, lossbuilder, MinuitMinimizer())

    poinull = POI(Nsig, value=np.linspace(1.0, 25, 15))
    poialt = POI(Nsig, value=0)

    def test_asy():
        calc = AsymptoticCalculator(config)
        ul_test = UpperLimit(poinull, poialt, calc, CLs=True, qtilde=False)
        return ul_test.upperlimit()

    def test_freq():
        calc = FrequentistCalculator(config, ntoysnull=5000, ntoysalt=5000)
        calc.readtoys_from_hdf5(Nsig, "{0}/toys_UL_Nsig.hdf5".format(pwd))
        ul_test = UpperLimit(poinull, poialt, calc, CLs=True, qtilde=False)
        return ul_test.upperlimit()

    ra = test_asy()
    rf = test_freq()

    assert ra["observed"] == pytest.approx(16.17701, abs=0.5)
    assert ra["exp"] == pytest.approx(11.12193, abs=0.5)
    assert ra["exp_p1"] == pytest.approx(16.1408, abs=0.5)
    assert ra["exp_p2"] == pytest.approx(22.8507, abs=0.5)
    assert ra["exp_m1"] == pytest.approx(7.8224, abs=0.5)
    assert ra["exp_m2"] == pytest.approx(5.7711, abs=0.5)

    assert ra["observed"] == pytest.approx(rf["observed"], abs=1.0)
    assert ra["exp"] == pytest.approx(rf["exp"], abs=1.0)
    assert ra["exp_p1"] == pytest.approx(rf["exp_p1"], abs=2.0)
    assert ra["exp_p2"] == pytest.approx(rf["exp_p2"], abs=3.0)
    assert ra["exp_m1"] == pytest.approx(rf["exp_m1"], abs=2.0)
    assert ra["exp_m2"] == pytest.approx(rf["exp_m2"], abs=3.0)
