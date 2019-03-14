#!/usr/bin/python
import numpy as np
from ..parameters import POI
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

    def qobs(self, poinull, onesided=True, onesideddiscovery=False,
             qtilde=False):
        print("Compute qobs for the null hypothesis!")

        poiparam = poinull.parameter

        bf = self.config.bestfit.params[poiparam]["value"]
        if qtilde and bf < 0:
            bestfitpoi = POI(poiparam, 0)
        else:
            bestfitpoi = POI(poiparam, bf)

        nll_poinull_obs = self.obs_nll(poinull)
        nll_bestfitpoi_obs = self.obs_nll(bestfitpoi)
        qobs = self.q(nll_poinull_obs, nll_bestfitpoi_obs)

        qobs = self.qdist(qobs, bestfitpoi.value, poinull.value,
                          onesided=onesided,
                          onesideddiscovery=onesideddiscovery)

        return qobs

    @classmethod
    def q(cls, nll1, nll2):
        q = 2*(nll1 - nll2)
        return q

    @classmethod
    def qdist(cls, q, bestfit, poival, onesided=True,
              onesideddiscovery=False):
        sel = ~(np.isnan(q) | np.isinf(q))
        q = q[sel]
        if isinstance(bestfit, np.ndarray):
            bestfit = bestfit[sel]
        zeros = np.zeros(q.shape)

        if onesideddiscovery:
            condition = (bestfit < poival) | (q < 0)
            q = np.where(condition, zeros, q)
        elif onesided:
            condition = (bestfit > poival) | (q < 0)
            q = np.where(condition, zeros, q)
        else:
            q = q

        return q
