from .hypotest import HypoTest
import numpy as np
from scipy.interpolate import interp1d
#import matplotlib.pyplot as plt
from ..parameters import POI


class ConfidenceInterval(HypoTest):
    def __init__(self, poinull, poialt, calculator,
                 qtilde=False, alpha=0.32):

        super(ConfidenceInterval, self).__init__(poinull, calculator, poialt)

        self._alpha = alpha
        self._pvalues = {}
        self._qtilde = qtilde

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha

    @property
    def qtilde(self):
        """
        Returns True if qtilde statistic is used, else False.
        """
        return self._qtilde

    @qtilde.setter
    def qtilde(self, qtilde):
        """
        Set True if qtilde statistic is used, else False.
        """
        self._qtilde = qtilde

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

        poinull = self.poinull
        poialt = self.poialt

        pnull, palt = self.calculator.pvalue(poinull, poialt,
                                             qtilde=self.qtilde,
                                             onesided=False)

        p_values = {}
        p_values["clsb"] = pnull
        p_values["clb"] = palt

        sigmas = [0.0, 1.0, 2.0, -1.0, -2.0]

        exp_pvalf = self.calculator.expected_pvalue

        result = exp_pvalf(self.poinull, self.poialt, sigmas, CLs=False)

        p_values["exp"] = result[0]
        p_values["exp_p1"] = result[1]
        p_values["exp_p2"] = result[2]
        p_values["exp_m1"] = result[3]
        p_values["exp_m2"] = result[4]

        return p_values

    def interval(self, printlevel=1):
        """
        Returns the confidence level on the parameter of interest.
        """

        pvalues = self.pvalues()
        poivalues = self.poinull.value
        poialt = self.poialt
        poiname = self.poinull.name

        p = pvalues["clsb"]
        pois = interp1d(p, poivalues, kind='cubic')
        p_m = p[poivalues < pois(max(p))]
        p_p = p[poivalues > pois(max(p))]
        poivalues_m = poivalues[poivalues < pois(max(p))]
        poivalues_p = poivalues[poivalues > pois(max(p))]
        pois_m = interp1d(p_m, poivalues_m, kind='cubic')
        pois_p = interp1d(p_p, poivalues_p, kind='cubic')
        poi_m = float(pois_m(self.alpha))
        poi_p = float(pois_p(self.alpha))

        bands = {}
        bands["observed"] = poialt.value
        bands["band_p"] = poi_p
        bands["band_m"] = poi_m

        if printlevel > 0:

            msg = "Confidence interval on {0}:\n"
            msg += "\t{band_m} < {0} < {band_p} at {1:.2f}% C.L."
            print(msg.format(poiname, 1-self.alpha, **bands))

        return bands
