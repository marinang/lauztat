import pytest

from lauztat.calculators import FrequentistCalculator
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

    calc = FrequentistCalculator(config, ntoysnull=5000, ntoysalt=5000)

    calc.readtoys_from_hdf5(Nsig, "{0}/toys_UL_Nsig.hdf5".format(pwd))

    poinull = POI(Nsig, value=np.linspace(1.0, 25, 15))
    poialt = POI(Nsig, value=0)
    ul_test = UpperLimit(poinull, poialt, calc, CLs=True, qtilde=False)

    result = ul_test.upperlimit()

    assert result["observed"] == pytest.approx(15.9665, abs=0.01)
    assert result["exp"] == pytest.approx(10.4231, abs=0.01)
    assert result["exp_p1"] == pytest.approx(14.8135, abs=0.01)
    assert result["exp_p2"] == pytest.approx(20.6654, abs=0.01)
    assert result["exp_m1"] == pytest.approx(7.2897, abs=0.01)
    assert result["exp_m2"] == pytest.approx(5.3179, abs=0.01)
