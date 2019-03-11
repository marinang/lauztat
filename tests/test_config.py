import pytest
from statnight.config import Config
import numpy as np


def test_with_zfit():

    import tensorflow as tf
    import zfit
    from zfit.core.loss import UnbinnedNLL
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer

    data = np.random.normal(1.2, 0.1, 10000)

    obs = zfit.Space('x', limits=(0.1, 2.0))

    mean = zfit.Parameter("mean", 1.2, 0.1, 2.)
    sigma = zfit.Parameter("sigma", 0.1, 0.02, 0.2)
    model = zfit.pdf.Gauss(obs=obs, mu=mean, sigma=sigma)

    data_ = zfit.data.Data.from_numpy(obs=obs, array=data)

    def lossbuilder(model, data, weights=None):
        loss = UnbinnedNLL(model=model, data=data, fit_range=[obs])
        return loss

    config = Config(model, data_, lossbuilder, MinuitMinimizer())

    bf = config.bestfit

    assert bf.params[mean]["value"] == pytest.approx(1.2, 0.01)
    assert bf.params[sigma]["value"] == pytest.approx(0.1, 0.01)

    # test sampling

    sampler = config.sampler(n=len(data))
    toys = config.sample(sampler, 2)
    next(toys)
    toy1 = zfit.run(sampler)

    assert np.mean(toy1) == pytest.approx(1.2, abs=0.01)
    assert np.std(toy1) == pytest.approx(0.1, abs=0.01)

    next(toys)
    toy2 = zfit.run(sampler)
    assert np.mean(toy2) == pytest.approx(1.2, abs=0.01)
    assert np.std(toy2) == pytest.approx(0.1, abs=0.01)

    assert np.mean(toy1) == pytest.approx(np.mean(toy2), abs=0.01)
    assert np.std(toy1) == pytest.approx(np.std(toy2), abs=0.01)

    with pytest.raises(StopIteration):
        next(toys)
