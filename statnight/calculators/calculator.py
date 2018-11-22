#!/usr/bin/python
import numpy as np


class Calculator(object):

    def __init__(self, config):
        self.config = config
        self.obsminimizer = config.obsminimizer()
        self.obsbestfit = config.bestfit
        self._obs_nll = {}

    def obs_nll(self, poi):
        ret = np.empty(len(poi))
        for i, p in enumerate(poi):
            if p.value not in self._obs_nll.keys():
                nll = self.obsminimizer.profile(p.name, p.value)
                self._obs_nll[p.value] = nll
            ret[i] = self._obs_nll[p.value]
        return ret
