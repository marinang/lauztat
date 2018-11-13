from .hypotest import HypoTest
import numpy as np
from scipy.interpolate import interp1d
#import matplotlib.pyplot as plt
from ..parameters import POI


class ConfidenceInterval(HypoTest):
    def __init__(self, null_hypothesis, alt_hypothesis, calculator,
                 qtilde=False, alpha=0.32):

        super(ConfidenceInterval, self).__init__(null_hypothesis,
                                                 alt_hypothesis, calculator)

        self._alpha = alpha
        self._pvalues = {}
        self._scanvalues = None
        self._bestfitpoi = None

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha

    @property
    def scanvalues(self):
        return self._scanvalues

    @scanvalues.setter
    def scanvalues(self, iterable):
        if not hasattr(iterable, "__iter__"):
            raise TypeError("{0} not an iterable.".format(iterable))
        else:
            self._scanvalues = iterable
            self._pvalues = {}

    def pvalues(self):
        """
        Returns p-values scanned for the values of the parameters of interest
        in the null hypothesis.
        """
        if self._pvalues:
            return self._pvalues
        else:
            self._pvalues = self._scannll()
            return self._pvalues

    def _scannll(self):

        althypo = self.alt_hypothesis
        poialt = althypo.pois

        _shape = len(self.scanvalues)

        p_values = {
                "clsb":   np.zeros(_shape),
                "clb":    np.zeros(_shape),
                "exp":    np.zeros(_shape),
                "exp_p1": np.zeros(_shape),
                "exp_p2": np.zeros(_shape),
                "exp_m1": np.zeros(_shape),
                "exp_m2": np.zeros(_shape)
                }

        if self.qtilde:
            nll_0_null = self.null_nll(0)

        nll_poia_null = self.null_nll(poialt)

        poiname = self.null_hypothesis.pois.name

        for i, poinull in np.ndenumerate(self.scanvalues):

            poinull = POI(poiname, poinull)

            nll_poin_null = self.null_nll(poinull)

            if poialt.value < 0 and self.qtilde:
                qnull = 2*(nll_poin_null - nll_0_null)
            else:
                qnull = 2*(nll_poin_null - nll_poia_null)

            self.null_nll

            pnull, palt = self.calculator.pvalue(qnull, poinull, althypo,
                                                 qtilde=self.qtilde,
                                                 onesided=False)

            p_values["clsb"][i] = pnull
            p_values["clb"][i] = palt

            exp_pval = self.calculator.expected_pvalue

            p_values["exp"][i] = exp_pval(poinull, poialt, 0, CLs=False)
            p_values["exp_p1"][i] = exp_pval(poinull, poialt, 1, CLs=False)
            p_values["exp_p2"][i] = exp_pval(poinull, poialt, 2, CLs=False)
            p_values["exp_m1"][i] = exp_pval(poinull, poialt, -1, CLs=False)
            p_values["exp_m2"][i] = exp_pval(poinull, poialt, -2, CLs=False)

        p_values["cls"] = p_values["clsb"] / p_values["clb"]

        return p_values

    def interval(self, printlevel=1):
        """
        Returns the confidence level on the parameter of interest.
        """

        pvalues = self.pvalues()
        poivalues = self.scanvalues
        poialt = self.alt_hypothesis.pois
        poiname = poialt.name

        p = pvalues["clsb"]
        pois = interp1d(p, poivalues, kind='cubic')
        p_m = p[poivalues < pois(max(p))]
        p_p = p[poivalues > pois(max(p))]
        poivalues_m = poivalues[poivalues < pois(max(p))]
        poivalues_p = poivalues[poivalues > pois(max(p))]
        pois_m = interp1d(p_m, poivalues_m, kind='cubic')
        pois_p = interp1d(p_p, poivalues_p, kind='cubic')
        poi_m = POI(poiname, float(pois_m(self.alpha)))
        poi_p = POI(poiname, float(pois_p(self.alpha)))

        #exp_poi = self.calculator.expected_poi

        bands = {}
        bands["observed"] = poialt.value
        # bands["band_p"] = exp_poi(poi_p, poialt, 1.0, self.alpha, CLs=False)
        # bands["band_m"] = exp_poi(poi_m, poialt, -1.0, self.alpha, CLs=False)
        bands["band_p"] = poi_p.value
        bands["band_m"] = poi_m.value

        if printlevel > 0:

            msg = "Confidence interval on {0}:\n"
            msg += "\t{band_m} < {0} < {band_p} at {1:.2f}% C.L."
            print(msg.format(poiname, 1-self.alpha, **bands))

        return bands
