# -*- coding: utf-8 -*-
# !/usr/bin/python

from .calculator import Calculator
from iminuit import Minuit, describe
import math
from scipy.stats import norm
import numpy as np
from scipy.optimize import brentq
from ..utils.stats import integrate1d
from ..utils.wrappers import MinuitWrapper, LossFunctionWrapper
from ..parameters import Constant


class AsymptoticCalculator(Calculator):
    """
    Class for for asymptotic calculators. Can be used only with one parameter
    of interest.

    See G. Cowan, K. Cranmer, E. Gross and O. Vitells: Asymptotic formulae for
    likelihood- based tests of new physics. Eur. Phys. J., C71:1–19, 2011

    **Arguments:**

        - **null_hypothesis** a statnight.model.Hypothesis representing the \
        null hypothesis of the test.
        - **null_hypothesis** a statnight.model.Hypothesis representing the \
        alterrnative hypothesis of the test.
        - **data** a numpy array. The data on which the hypothesis is tested.
        - **qtilde** bool (optionnal). Set the test statistic to qtilde \
        default **False**.
        - **onesided** bool (optionnal). Set the test statistic for one sided \
        upper limit. default **True**.
        - **onesideddiscovery** bool (optionnal). Set the test statistic for \
        one sided discovery. default **False**.
        - **CLs** bool (optionnal). Use CLs for computing upper limit. \
        default **True**.
    """

    def __init__(self):
        """
        __init__ function
        """

        self._asy_nll = {}
        self._alt_hypothesis = None

    def asymov_dataset(self):

        if hasattr(self, "_asymov_dataset"):
            return self._asymov_dataset
        else:
            hypo = self._alt_hypothesis
            costfunc = hypo.costfunction
            model = costfunc.model.copy()
            data = costfunc.data
            weights = costfunc.weights

            poi = hypo.pois
            model.rm_vars(poi.name)
            model.add_vars(Constant(poi.name, poi.value))

            if isinstance(costfunc, LossFunctionWrapper):
                lossclass = type(costfunc.lossfunction)
            else:
                lossclass = type(costfunc)
            lossbuilder = LossFunctionWrapper.from_lossfunction

            alt_costfunc = lossbuilder(lossclass, model, data, weights)

            minuit_alt = MinuitWrapper(alt_costfunc)
            msg = "Get fit best values for nuisance parameters for the"
            msg += " alternative hypothesis!"
            print(msg)
            minuit_alt.migrad()

            bounds = (min(data), max(data))

            self._asymov_dataset = generate_asymov_dataset(model,
                                                           minuit_alt.values,
                                                           bounds)
            return self._asymov_dataset

    def asy_minuit(self):
        if hasattr(self, "_asy_minuit"):
            return self._asy_minuit
        else:
            hypo = self._alt_hypothesis
            costfunc = hypo.costfunction
            model = costfunc.model.copy()

            data = self.asymov_dataset()[0]
            weights = self.asymov_dataset()[1]

            if isinstance(costfunc, LossFunctionWrapper):
                lossclass = type(costfunc.lossfunction)
            else:
                lossclass = type(costfunc)
            lossbuilder = LossFunctionWrapper.from_lossfunction

            alt_costfunc = lossbuilder(lossclass, model, data, weights)

            self._asy_minuit = MinuitWrapper(alt_costfunc)
            return self._asy_minuit

    def asy_nll(self, poi):

        if poi.value not in self._asy_nll.keys():
            self._asy_nll[poi.value] = compute_1D_NLL(self.asy_minuit(),
                                                      poi.name, poi.value)

        return self._asy_nll[poi.value]

    def pvalue(self, qnull, poinull, alt_hypothesis, qtilde=False,
               onesided=True, onesideddiscovery=False):

        self._alt_hypothesis = alt_hypothesis
        poialt = alt_hypothesis.pois

        nll_poia_alt = self.asy_nll(poialt)

        nll_poin_alt = self.asy_nll(poinull)

        qalt = 2*(nll_poin_alt - nll_poia_alt)

        if qalt < 0:
            qalt = 0.0000001

        pnull = -1.
        palt = -1.

        sqrtqnull = math.sqrt(qnull)
        sqrtqalt = math.sqrt(qalt)

        if not qtilde:
            if onesided or onesideddiscovery:
                pnull = 1. - norm.cdf(sqrtqnull)
                palt = 1. - norm.cdf(sqrtqnull - sqrtqalt)
            else:
                pnull = (1. - norm.cdf(sqrtqnull))*2.
                palt = 1. - norm.cdf(sqrtqnull + sqrtqalt)
                palt += 1. - norm.cdf(sqrtqnull - sqrtqalt)
        else:
            if onesided:
                if qnull > qalt and qalt > 0.:
                    pnull = 1. - norm.cdf((qnull + qalt) / (2. * sqrtqalt))
                    palt = 1. - norm.cdf((qnull - qalt) / (2. * sqrtqalt))
                elif qnull <= qalt and qalt > 0.:
                    pnull = 1. - norm.cdf(sqrtqnull)
                    palt = 1. - norm.cdf(sqrtqnull - sqrtqalt)

        return pnull, palt

    def expected_pvalue(self, poinull, poialt, nsigma, CLs=True):

        nll_poia_alt = self.asy_nll(poialt)

        nll_poin_alt = self.asy_nll(poinull)

        qalt = 2*(nll_poin_alt - nll_poia_alt)

        if qalt < 0:
            qalt = 0.0000001

        p_clsb = 1 - norm.cdf(math.sqrt(qalt) - nsigma)

        if CLs:
            p_clb = norm.cdf(nsigma)
            p_cls = p_clsb / p_clb
            return max(p_cls, 0.)
        else:
            return max(p_clsb, 0.)

    def expected_poi(self, poinull, poialt, n=0.0, alpha=0.05,
                     CLs=False):

        nll_poia_alt = self.asy_nll(poialt)
        nll_poin_alt = self.asy_nll(poinull)
        qalt = 2*(nll_poin_alt - nll_poia_alt)

        sigma = math.sqrt((poinull.value - poialt.value)**2 / qalt)

        if CLs:
            ret = poialt.value + sigma * (norm.ppf(1 - alpha*norm.cdf(n)) + n)
        else:
            ret = poialt.value + sigma * (norm.ppf(1 - alpha) + n)

        return ret


def compute_1D_NLL(minuit, poi, val, npoints=1):

    range = (val, -1.)

    nll_curve = minuit.mnprofile(poi, npoints, range)

    return nll_curve[1]


def generate_asymov_dataset(pdf, params_values, bounds, nbins=100):

    def bin_expectation_value(bin_low, bin_high):

        params = list(describe(pdf))[1:]
        args = []
        for p in params:
            args.append(params_values[p])
        args = tuple(args)

        ret = integrate1d(pdf, (bin_low, bin_high), 100, *args)

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
