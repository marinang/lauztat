#!/usr/bin/python
import numpy as np
# from numba import jit


class Calculator(object):

    def __init__(self, config):
        self.config = config
        self.minimizer = config.minimizer
        self.obsbestfit = config.bestfit
        self.pll = config.pll
        self._obs_nll = {}

    def obs_nll(self, poi):
        ret = np.empty(len(poi))
        for i, p in enumerate(poi):
            if p not in self._obs_nll.keys():
                nll = self.pll(self.minimizer, self.config.obsloss(),
                               p.parameter, p.value)
                self._obs_nll[p] = nll
            ret[i] = self._obs_nll[p]
        return ret

    def qobs(self, poinull, bestfitpoi):
        print("Compute qobs for the null hypothesis!")
        nll_poinull_obs = self.obs_nll(poinull)
        nll_bestfitpoi_obs = self.obs_nll(bestfitpoi)
        qobs = 2*(nll_poinull_obs - nll_bestfitpoi_obs)
        return qobs


# @jit(nopython=True)
def qdist(qdist, bestfit, poival, onesided=True, onesideddiscovery=False):
    zeros = np.zeros(qdist.shape)
    if onesideddiscovery:
        condition = (bestfit < poival) | (qdist < 0)
        q = np.where(condition, zeros, qdist)
    elif onesided:
        condition = (bestfit > poival) | (qdist < 0)
        q = np.where(condition, zeros, qdist)
    else:
        q = qdist
    return q
