#!/usr/bin/python
import pytest

from lauztat.calculators import FrequentistCalculator
from lauztat.config import Config
from lauztat.parameters import POI
import numpy as np


def test_constructors():

    with pytest.raises(TypeError):
        FrequentistCalculator()


# @pytest.mark.skip()
def test_with_zfit():

    import zfit
    from zfit.core.loss import UnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer
    zfit.settings.set_seed(34)

    data = np.random.normal(1.2, 0.1, 10000)

    obs = zfit.Space('x', limits=(0.1, 2.0))

    mean = zfit.Parameter("m_fcalc", 1.2, 0.1, 2.5)
    sigma = zfit.Parameter("s_fcalc", 0.1, 0.02, 0.2)
    model = zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data, weights=None):
        loss = UnbinnedNLL(model=model, data=data, fit_range=[obs])
        return loss

    minimizer = MinuitMinimizer()

    def sampler(models, *args, **kwargs):
        samplers = []
        for m in models:
            sampler = m.create_sampler(n=10000, fixed_params=[sigma])
            samplers.append(sampler)
        return samplers

    def sampling(samplers, ntoys, param, value):
        for i in range(ntoys):
            with param.set_value(value):
                for s in samplers:
                    s.resample()
            yield i

    config = Config(model, data_, lossbuilder, minimizer, sampler=sampler,
                    sample_method=sampling)

    calc = FrequentistCalculator(config, ntoysnull=100, ntoysalt=100)

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

    poinull = POI(mean, 1.2)
    poialt = POI(mean, 1.6)

    calc.dotoys_null(poinull, poialt)
    calc.dotoys_alt(poialt, poinull)

    pnull, palt = calc.pvalue(poinull, poialt)

    assert 0 < pnull < 0.5
    assert palt == pytest.approx(0.0, abs=0.01)

    calc.toys_to_hdf5("toys.hdf5")

    calc2 = FrequentistCalculator(config)

    calc2.readtoys_from_hdf5(mean, "toys.hdf5")

    calc.pvalue(poinull, poialt)
