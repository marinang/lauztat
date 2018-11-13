from .hypotest import HypoTest
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from ..parameters import POI


class UpperLimit(HypoTest):
    def __init__(self, null_hypothesis, alt_hypothesis, calculator,
                 qtilde=False, alpha=0.05, CLs=True):

        super(UpperLimit, self).__init__(null_hypothesis, alt_hypothesis,
                                         calculator)

        self._scanvalues = None
        self._pvalues = {}
        self._alpha = alpha
        self._CLs = CLs
        self._bestfitpoi = None

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha

    @property
    def CLs(self):
        return self._CLs

    @CLs.setter
    def CLs(self, CLs):
        self._CLs = CLs

    @property
    def bestfitpoi(self):
        if self._bestfitpoi is None:
            msg = "Get fit best values for parameter of interest for the null"
            msg += " hypothesis!"
            print(msg)
            self.null_minuit().migrad()
            poiname = self.null_hypothesis.pois.name
            poival = self.null_minuit().values[poiname]
            bestfitpoi = POI(poiname, poival)
            self._bestfitpoi = bestfitpoi
        return self._bestfitpoi

    @bestfitpoi.setter
    def bestfitpoi(self, bestfitpoi):
        self._bestfitpoi = bestfitpoi

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

        bestpoi = self.bestfitpoi
        nll_bpoiv_null = self.null_nll(bestpoi)

        poiname = self.null_hypothesis.pois.name

        for i, poinull in np.ndenumerate(self.scanvalues):

            poinull = POI(poiname, poinull)

            nll_pv_null = self.null_nll(poinull)

            if poialt > poinull:
                qnull = 0
            elif poialt.value < 0 and self.qtilde:
                qnull = 2*(nll_pv_null - nll_0_null)
            else:
                qnull = 2*(nll_pv_null - nll_bpoiv_null)

            pnull, palt = self.calculator.pvalue(qnull, poinull, althypo,
                                                 qtilde=self.qtilde,
                                                 onesided=True)

            p_values["clsb"][i] = pnull
            p_values["clb"][i] = palt

            exp_pval = self.calculator.expected_pvalue

            p_values["exp"][i] = exp_pval(poinull, poialt, 0, self.CLs)
            p_values["exp_p1"][i] = exp_pval(poinull, poialt, 1, self.CLs)
            p_values["exp_p2"][i] = exp_pval(poinull, poialt, 2, self.CLs)
            p_values["exp_m1"][i] = exp_pval(poinull, poialt, -1, self.CLs)
            p_values["exp_m2"][i] = exp_pval(poinull, poialt, -2, self.CLs)

        p_values["cls"] = p_values["clsb"] / p_values["clb"]

        return p_values

    def upperlimit(self, printlevel=1):
        """
        Returns the upper limit of the parameter of interest.
        """

        pvalues = self.pvalues()
        poivalues = self.scanvalues
        poialt = self.alt_hypothesis.pois
        poiname = poialt.name

        if self.CLs:
            p_ = pvalues["cls"]
        else:
            p_ = pvalues["clsb"]

        pois = interp1d(p_, poivalues, kind='cubic')
        poiul = POI(poiname, float(pois(self.alpha)))

        exp_poi = self.calculator.expected_poi

        bands = {}
        bands["median"] = exp_poi(poiul, poialt, 0.0, self.alpha, self.CLs)
        bands["band_p1"] = exp_poi(poiul, poialt, 1.0, self.alpha, self.CLs)
        bands["band_p2"] = exp_poi(poiul, poialt, 2.0, self.alpha, self.CLs)
        bands["band_m1"] = exp_poi(poiul, poialt, -1.0, self.alpha, self.CLs)
        bands["band_m2"] = exp_poi(poiul, poialt, -2.0, self.alpha, self.CLs)

        if printlevel > 0:

            msg = "Observed upper limit: {0} = {1}"
            print(msg.format(poiname, poiul.value))
            msg = "Expected upper limit: {0} = {1}"
            print(msg.format(poiname, bands["median"]))
            msg = "Expected upper limit +1 sigma: {0} = {1}"
            print(msg.format(poiname, bands["band_p1"]))
            msg = "Expected upper limit -1 sigma: {0} = {1}"
            print(msg.format(poiname, bands["band_m1"]))
            msg = "Expected upper limit +2 sigma: {0} = {1}"
            print(msg.format(poiname, bands["band_p2"]))
            msg = "Expected upper limit -2 sigma: {0} = {1}"
            print(msg.format(poiname, bands["band_m2"]))

        bands["observed"] = poiul.value

        return bands

    def plot(self, ax=None, show=True, **kwargs):
        """
        Plot the pvalues obtained with CLsb/CLb/CLs, and using the asimov
        datasets (median p_value, +bands), scanned for the different values of
        the parameter of interest.

            **Arguments:**
                - **ax** (optionnal) matplotlib axis
                - **show** (optionnal) show the plot. default **True**.
        """

        pvalues = self.pvalues()
        scanvalues = self.scanvalues
        alpha = self.alpha

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))

        if self.CLs:
            cls_clr = "r"
            clsb_clr = "b"
        else:
            cls_clr = "b"
            clsb_clr = "r"

        ax.plot(scanvalues, pvalues["cls"], label="Observed CL$_{s}$",
                marker=".", color='k', markerfacecolor=cls_clr,
                markeredgecolor=cls_clr, linewidth=2.0, ms=11)
        ax.plot(scanvalues, pvalues["clsb"], label="Observed CL$_{s+b}$",
                marker=".", color='k', markerfacecolor=clsb_clr,
                markeredgecolor=clsb_clr, linewidth=2.0, ms=11,
                linestyle=":")
        ax.plot(scanvalues, pvalues["clb"], label="Observed CL$_{b}$",
                marker=".", color='k', markerfacecolor="k",
                markeredgecolor="k", linewidth=2.0, ms=11)
        ax.plot(scanvalues, pvalues["exp"],
                label="Expected CL$_{s}-$Median", color='k',
                linestyle="--", linewidth=1.5, ms=10)
        ax.plot([scanvalues[0], scanvalues[-1]], [alpha, alpha], color='r',
                linestyle='-', linewidth=1.5)
        ax.fill_between(scanvalues, pvalues["exp"], pvalues["exp_p1"],
                        facecolor="lime",
                        label="Expected CL$_{s} \\pm 1 \\sigma$")
        ax.fill_between(scanvalues, pvalues["exp"], pvalues["exp_m1"],
                        facecolor="lime")
        ax.fill_between(scanvalues, pvalues["exp_p1"], pvalues["exp_p2"],
                        facecolor="yellow",
                        label="Expected CL$_{s} \\pm 2 \\sigma$")
        ax.fill_between(scanvalues, pvalues["exp_m1"], pvalues["exp_m2"],
                        facecolor="yellow")

        if self.CLs:
            ax.set_ylim(-0.01, 1.1)
        else:
            ax.set_ylim(-0.01, 0.55)
        ax.set_ylabel("p-value")
        ax.set_xlabel(self.null_hypothesis.pois.name)
        ax.legend(loc="best", fontsize=14)

        if show:
            plt.show()
