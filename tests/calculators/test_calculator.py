#!/usr/bin/python
import pytest

from lauztat.calculators.calculator import Calculator
from lauztat.config import Config
from lauztat.parameters import POI
import numpy as np


def test_constructors():

    with pytest.raises(TypeError):
        Calculator()


def test_with_zfit():

    import zfit
    from zfit.core.loss import UnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer

    data = np.random.normal(1.2, 0.1, 10000)

    obs = zfit.Space('x', limits=(0.1, 2.0))

    mean = zfit.Parameter("mcalc", 1.2, 0.1, 2.)
    sigma = zfit.Parameter("scalc", 0.1, 0.02, 0.2)
    model = zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data, weights=None):
        loss = UnbinnedNLL(model=model, data=data, fit_range=[obs])
        return loss

    minimizer = MinuitMinimizer()

    config = Config(model, data_, lossbuilder, minimizer)

    calc = Calculator(config)

    assert calc.minimizer == minimizer
    calc.obsbestfit
    assert calc.obsbestfit == config.bestfit

    mean_poi = POI(mean, [1.15, 1.2, 1.25])
    mean_nll = calc.obs_nll(mean_poi)

    assert mean_nll[0] >= mean_nll[1]
    assert mean_nll[2] >= mean_nll[1]

    assert calc.obs_nll(mean_poi[0]) == mean_nll[0]
    assert calc.obs_nll(mean_poi[1]) == mean_nll[1]
    assert calc.obs_nll(mean_poi[2]) == mean_nll[2]
