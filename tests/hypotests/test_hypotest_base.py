#!/usr/bin/python
import pytest

from lauztat.calculators.calculator import Calculator
from lauztat.hypotests.hypotest import HypoTest
from lauztat.config import Config
from lauztat.parameters import POI
import numpy as np


def test_constructors():

    with pytest.raises(TypeError):
        HypoTest()


def test_with_zfit():

    import zfit
    from zfit.core.loss import UnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer

    data = np.random.normal(1.2, 0.1, 10000)

    obs = zfit.Space('x', limits=(0.1, 2.0))

    mean = zfit.Parameter("m_hypo", 1.2, 0.1, 2.)
    sigma = zfit.Parameter("s_hypo", 0.1, 0.02, 0.2)
    model = zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data, weights=None):
        loss = UnbinnedNLL(model=model, data=data, fit_range=[obs])
        return loss

    minimizer = MinuitMinimizer()

    config = Config(model, data_, lossbuilder, minimizer)

    calc = Calculator(config)

    poinull = POI(mean, value=np.linspace(1.0, 1.4, 15))

    with pytest.raises(TypeError):
        HypoTest(poinull=poinull, calculator=calc, poialt="poialt")
        HypoTest(calc, poinull)
        HypoTest("calc", "poinull")
        HypoTest(poinull, "calc")
        HypoTest("poinull", calc)

    test = HypoTest(poinull=poinull, calculator=calc)

    assert test.calculator == calc
    assert test.poinull == poinull
    assert test.poialt is None
