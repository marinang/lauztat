# -*- coding: utf-8 -*-
# !/usr/bin/python

from .calculator import Calculator
from scipy.stats import norm
import numpy as np
from ..utils.stats import integrate1d
from ..parameters import Constant, POI
from numba import jit


class AsymptoticCalculator(Calculator):
    """
    Class for for asymptotic calculators. Can be used only with one parameter
    of interest.

    See G. Cowan, K. Cranmer, E. Gross and O. Vitells: Asymptotic formulae for
    likelihood- based tests of new physics. Eur. Phys. J., C71:1–19, 2011
    """

    def __init__(self, config):
        """
        __init__ function
        """

        super(AsymptoticCalculator, self).__init__(config)

        self._asymov_dataset = {}
        self._asymov_minimizer = {}
        self._asymov_nll = {}

    def asymov_dataset(self, poi):
        if poi not in self._asymov_dataset.keys():
            models = []
            for m in self.config.models():
                model = m.copy()
                model.rm_vars(poi.name)
                model.add_vars(Constant(poi.name, poi.value))
                models.append(model)

            datasets = self.config.datasets
            weights = self.config.weights

            loss = self.config.lossbuilder(models, datasets, weights)

            minimizer = self.config.minimizer(loss)

            msg = "\nGet fit best values for nuisance parameters for the"
            msg += " alternative hypothesis!"
            print(msg)
            minimizer.minimize()
            values = minimizer.values

            asydatasets = []

            for m in models:
                bounds = m.obs[0].range
                asydatasets.append(generate_asymov_dataset(m, values, bounds))

            self._asymov_dataset[poi] = asydatasets

        return self._asymov_dataset[poi]

    def asymov_minimizer(self, poi):
        if poi not in self._asymov_minimizer.keys():
            models = [m.copy for m in self.config.models]
            datasets = []
            weights = []

            for ad in self.asymov_dataset(poi):
                datasets.append(ad[0])
                weights.append(ad[1])

            loss = self.config.lossbuilder(models, datasets, weights)

            self._asymov_minimizer[poi] = self.config.minimizer(loss)

        return self._asymov_minimizer[poi]

    def asymov_nll(self, poi, poialt):
        ret = np.empty(len(poi))
        for i, p in enumerate(poi):
            if p not in self._asymov_nll.keys():
                nll = self.asymov_minimizer(poialt).profile(p.name, p.value)
                self._asymov_nll[p] = nll
            ret[i] = self._asymov_nll[p]
        return ret

    def pvalue(self, poinull, poialt=None, qtilde=False, onesided=True,
               onesideddiscovery=False):

        poiname = poinull.name

        bf = self.config.bestfit[poiname]
        if qtilde and bf < 0:
            bestfitpoi = POI(poiname, 0)
        else:
            bestfitpoi = POI(poiname, bf)

        nll_poinull_obs = self.obs_nll(poinull)
        nll_bestfitpoi_obs = self.obs_nll(bestfitpoi)
        qobs = 2*(nll_poinull_obs - nll_bestfitpoi_obs)

        qobs = qdist(qobs, bestfitpoi.value, poinull.value, onesided,
                     onesideddiscovery)

        sqrtqobs = np.sqrt(qobs)

        needpalt = not(onesided and poialt is None)

        if needpalt:
            nll_poinull_asy = self.asymov_nll(poinull, poialt)
            nll_poialt_asy = self.asymov_nll(poialt, poialt)
            qalt = 2*(nll_poinull_asy - nll_poialt_asy)
            qalt = qdist(qalt, 0, poinull.value, onesided, onesideddiscovery)
            sqrtqalt = np.sqrt(qalt)
        else:
            palt = None

        if not qtilde:
            if onesided or onesideddiscovery:
                pnull = 1. - norm.cdf(sqrtqobs)
                if needpalt:
                    palt = 1. - norm.cdf(sqrtqobs - sqrtqalt)
            else:
                pnull = (1. - norm.cdf(sqrtqobs))*2.
                if needpalt:
                    palt = 1. - norm.cdf(sqrtqobs + sqrtqalt)
                    palt += 1. - norm.cdf(sqrtqobs - sqrtqalt)
        else:
            if onesided:
                pnull1 = 1. - norm.cdf((qobs + qalt) / (2. * sqrtqalt))
                pnull2 = 1. - norm.cdf(sqrtqobs)
                pnull = np.where(qobs > qalt, pnull1, pnull2)

                if needpalt:
                    palt1 = 1. - norm.cdf((qobs - qalt) / (2. * sqrtqalt))
                    palt2 = 1. - norm.cdf(sqrtqobs - sqrtqalt)
                    palt = np.where(qobs > qalt, palt1, palt2)

        return pnull, palt

    def expected_pvalue(self, poinull, poialt, nsigma, CLs=True):

        nll_poinull_asy = self.asymov_nll(poinull, poialt)
        nll_poialt_asy = self.asymov_nll(poialt, poialt)

        qalt = 2*(nll_poinull_asy - nll_poialt_asy)
        qalt = np.where(qalt < 0, 0, qalt)

        ret = []
        for ns in nsigma:
            p_clsb = 1 - norm.cdf(np.sqrt(qalt) - ns)
            if CLs:
                p_clb = norm.cdf(ns)
                p_cls = p_clsb / p_clb
                ret.append(np.where(p_cls < 0, 0, p_cls))
            else:
                ret.append(np.where(p_clsb < 0, 0, p_clsb))

        return ret

    def expected_poi(self, poinull, poialt, nsigma, alpha=0.05,
                     CLs=False):

        nll_poinull_asy = self.asymov_nll(poinull, poialt)
        nll_poialt_asy = self.asymov_nll(poialt, poialt)

        qalt = 2*(nll_poinull_asy - nll_poialt_asy)
        qalt = np.where(qalt < 0, 0, qalt)

        sigma = np.sqrt((poinull.value - poialt.value)**2 / qalt)

        ret = []
        for ns in nsigma:
            if CLs:
                exp = poialt.value
                exp += sigma * (norm.ppf(1 - alpha*norm.cdf(ns)) + ns)
            else:
                exp = poialt.value + sigma * (norm.ppf(1 - alpha) + ns)
            ret.append(float(exp))

        return ret


def generate_asymov_dataset(model, params, bounds, nbins=100):

    def bin_expectation_value(bin_low, bin_high):

        args = []
        for p in model.parameters[1:]:
            args.append(params[p])
        args = tuple(args)
        ret = integrate1d(model, (bin_low, bin_high), 100, *args)

        return ret

    bins_edges = np.linspace(bounds[0], bounds[1], nbins + 1)
    data_asy = np.zeros(nbins)
    weight_asy = np.zeros(nbins)

    for nb in range(nbins):

        low_bin = bins_edges[nb]
        high_bin = bins_edges[nb+1]
        bin_center = low_bin + (high_bin - low_bin)/2

        exp_val = bin_expectation_value(low_bin, high_bin)

        data_asy[nb] = bin_center
        weight_asy[nb] = exp_val

    return data_asy, weight_asy


@jit(nopython=True)
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

# def Expected_Pvalues_2sided(pnull, palt):
#
#     sqrtqnull = norm.ppf(1 - pnull/2)
#
#     def paltfunct(offset, pval, icase):
#         def func(x):
#             ret = 1. - norm.cdf(x + offset)
#             ret += 1. - norm.cdf(icase*(x - offset))
#             ret -= pval
#             return ret
#         return func
#
#     f = paltfunct(sqrtqnull, palt, -1.)
#     sqrtqalt = brentq(f, 0, 20)
#
#     fmed = paltfunct(sqrtqalt, norm.cdf(0), 1.)
#     sqrtqalt_med = brentq(fmed, 0, 20)
#     p_med = 2.*(1-norm.cdf(sqrtqalt_med))
#
#     fp1 = paltfunct(sqrtqalt, norm.cdf(1), 1.)
#     sqrtqalt_p1 = brentq(fp1, 0, 20)
#     p_p1 = 2.*(1-norm.cdf(sqrtqalt_p1))
#
#     fp2 = paltfunct(sqrtqalt, norm.cdf(2), 1.)
#     sqrtqalt_p2 = brentq(fp2, 0, 20)
#     p_p2 = 2.*(1-norm.cdf(sqrtqalt_p2))
#
#     fm1 = paltfunct(sqrtqalt, norm.cdf(-1), 1.)
#     sqrtqalt_m1 = brentq(fm1, 0, 20)
#     p_m1 = 2.*(1-norm.cdf(sqrtqalt_m1))
#
#     fm2 = paltfunct(sqrtqalt, norm.cdf(-2), 1.)
#     sqrtqalt_m2 = brentq(fm2, 0, 20)
#     p_m2 = 2.*(1-norm.cdf(sqrtqalt_m2))
#
#     return p_med, p_p1, p_p2, p_m1, p_m2
