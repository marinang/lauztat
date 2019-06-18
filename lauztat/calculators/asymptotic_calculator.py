# -*- coding: utf-8 -*-
# !/usr/bin/python

from .calculator import Calculator
from scipy.stats import norm
from ..util import convert_dataset, eval_pdf
import numpy as np


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
        self._asymov_loss = {}
        self._asymov_nll = {}

    def asymov_dataset(self, poi):
        if poi not in self._asymov_dataset.keys():
            models = self.config.models
            minimizer = self.config.minimizer
            oldverbose = minimizer.verbosity
            minimizer.verbosity = 5

            loss = self.config.obsloss()

            poiparam = poi.parameter
            poivalue = poi.value

            msg = "\nGet fit best values for nuisance parameters for the"
            msg += " alternative hypothesis!"
            print(msg)

            with poiparam.set_value(poivalue):
                poiparam.floating = False
                asymin = minimizer.minimize(loss=loss)
                poiparam.floating = True

            minimizer.verbosity = oldverbose

            values = asymin.params
            values[poiparam] = {"value": poivalue}

            asydatasets = []

            for m in models:
                space = m.space
                asydatasets.append(generate_asymov_dataset(m, values, space))

            self._asymov_dataset[poi] = asydatasets

        return self._asymov_dataset[poi]

    def asymov_loss(self, poi):
        if poi not in self._asymov_loss.keys():
            config = self.config
            models = config.models
            obsdata = config.datasets
            datasets = []

            for i, ad in enumerate(self.asymov_dataset(poi)):
                data = convert_dataset(obsdata[i], ad[0], ad[1])
                datasets.append(data)

            loss = config.lossbuilder(models, datasets)

            self._asymov_loss[poi] = loss

        return self._asymov_loss[poi]

    def asymov_nll(self, poi, poialt):
        config = self.config
        minimizer = config.minimizer

        ret = np.empty(len(poi))
        for i, p in enumerate(poi):
            if p not in self._asymov_nll.keys():
                loss = self.asymov_loss(poialt)
                nll = config.pll(minimizer, loss, p.parameter, p.value)
                self._asymov_nll[p] = nll
            ret[i] = self._asymov_nll[p]
        return ret

    def pvalue(self, poinull, poialt=None, qtilde=False, onesided=True,
               onesideddiscovery=False):

        qobs = self.qobs(poinull, onesided=onesided, qtilde=qtilde,
                         onesideddiscovery=onesideddiscovery)

        sqrtqobs = np.sqrt(qobs)

        needpalt = poialt is not None

        if needpalt:
            nll_poinull_asy = self.asymov_nll(poinull, poialt)
            nll_poialt_asy = self.asymov_nll(poialt, poialt)
            qalt = self.q(nll_poinull_asy, nll_poialt_asy)
            qalt = self.qdist(qalt, 0, poinull.value, onesided=onesided,
                              onesideddiscovery=onesideddiscovery)
            sqrtqalt = np.sqrt(qalt)
        else:
            palt = None
            
        # 1 - norm.cdf(x) == norm.cdf(-x) 

        if onesided or onesideddiscovery:
            pnull = 1. - norm.cdf(sqrtqobs)
            if needpalt:
                palt = 1. - norm.cdf(sqrtqobs - sqrtqalt)
        else:
            pnull = (1. - norm.cdf(sqrtqobs))*2.
            if needpalt:
                palt = 1. - norm.cdf(sqrtqobs + sqrtqalt)
                palt += 1. - norm.cdf(sqrtqobs - sqrtqalt)
                
        if qtilde and needpalt:
            cond = (qobs > qalt) & (qalt > 0)
            
            pnull_2 = 1. - norm.cdf((qobs + qalt) / (2. * sqrtqalt))
            palt_2 = 1. - norm.cdf((qobs - qalt) / (2. * sqrtqalt))
            
            if not (onesided or onesideddiscovery):
                pnull_2 += 1. - norm.cdf(sqrtqobs) 
                palt_2 += 1. - norm.cdf(sqrtqobs + sqrtqalt)
                
            pnull = np.where(cond, pnull, pnull_2)
            palt = np.where(cond, palt, palt_2)

        return pnull, palt
        

    def expected_pvalue(self, poinull, poialt, nsigma, CLs=True):

        nll_poinull_asy = self.asymov_nll(poinull, poialt)
        nll_poialt_asy = self.asymov_nll(poialt, poialt)

        qalt = self.q(nll_poinull_asy, nll_poialt_asy)
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

        qalt = self.q(nll_poinull_asy, nll_poialt_asy)
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


def generate_asymov_dataset(model, params, space, nbins=100):

    bounds = space.limit1d
    bins_edges = np.linspace(*bounds, nbins+1)
    data_asy = bins_edges[0: -1] + np.diff(bins_edges)/2

    weight_asy = eval_pdf(model, data_asy, params)
    weight_asy *= (space.area() / nbins)

    return data_asy, weight_asy


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
