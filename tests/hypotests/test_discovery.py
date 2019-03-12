import pytest

from lauztat.calculators import FrequentistCalculator, AsymptoticCalculator
from lauztat.config import Config
from lauztat.parameters import POI
from lauztat.hypotests import Discovery
import numpy as np
import os
pwd = os.path.dirname(__file__)


def test_constructors():

    with pytest.raises(TypeError):
        Discovery()


bounds = (0.1, 3.0)

# Data and signal

np.random.seed(0)
tau = -2.0
beta = -1/tau
data = np.random.exponential(beta, 300)
peak = np.random.normal(1.2, 0.1, 25)
data = np.concatenate((data, peak))
data = data[(data > bounds[0]) & (data < bounds[1])]


def test_with_zfit():

    import zfit
    from zfit.core.loss import ExtendedUnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer

    obs = zfit.Space('x', limits=bounds)

    mean = zfit.Parameter("m_disco", 1.2, 0.1, 2., floating=False)
    sigma = zfit.Parameter("s_disco", 0.1, floating=False)
    lambda_ = zfit.Parameter("l_disco", -2.0, -4.0, -1.0)
    Nsig = zfit.Parameter("Ns_disco", 20., -20., len(data))
    Nbkg = zfit.Parameter("Nbkg_disco", len(data), 0., len(data)*1.1)

    signal = Nsig * zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)
    background = Nbkg * zfit.pdf.Exponential(obs=obs, lambda_=lambda_)
    tot_model = signal + background

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data):
        loss = ExtendedUnbinnedNLL(model=model, data=data, fit_range=[obs])
        return loss

    config = Config(tot_model, data_, lossbuilder, MinuitMinimizer())

    poinull = POI(Nsig, value=0)

    def test_asy():
        calc = AsymptoticCalculator(config)
        discovery_test = Discovery(poinull, calc)
        r = discovery_test.result()
        return r

    def test_freq():
        calc = FrequentistCalculator(config, ntoysnull=5000)
        calc.readtoys_from_hdf5(Nsig, "{0}/toys_Disco_Nsig.hdf5".format(pwd))
        discovery_test = Discovery(poinull, calc)
        r = discovery_test.result()
        return r

    ra = test_asy()
    rf = test_freq()

    assert ra["pnull"] == pytest.approx(rf["pnull"], abs=0.05)
    assert rf["significance"] == pytest.approx(ra["significance"], abs=0.05)
