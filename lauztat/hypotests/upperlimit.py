from .hypotest import HypoTest
from scipy.interpolate import InterpolatedUnivariateSpline
from ..parameters import POI
from ..calculators import AsymptoticCalculator


class UpperLimit(HypoTest):
    def __init__(self, poinull, poialt, calculator,
                 qtilde=False, alpha=0.05, CLs=True):

        super(UpperLimit, self).__init__(poinull, calculator, poialt)

        self._pvalues = {}
        self._alpha = alpha
        self._CLs = CLs
        self._qtilde = qtilde

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
        self._pvalues = self._scannll()

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
        self._pvalues = self._scannll()

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

        pvaluef = self.calculator.pvalue

        pnull, palt = pvaluef(self.poinull, self.poialt, qtilde=self.qtilde,
                              onesided=True)

        p_values = {"clsb": pnull, "clb": palt}

        sigmas = [0.0, 1.0, 2.0, -1.0, -2.0]

        exp_pvalf = self.calculator.expected_pvalue

        result = exp_pvalf(self.poinull, self.poialt, sigmas, self.CLs)

        p_values["exp"] = result[0]
        p_values["exp_p1"] = result[1]
        p_values["exp_p2"] = result[2]
        p_values["exp_m1"] = result[3]
        p_values["exp_m2"] = result[4]

        p_values["cls"] = p_values["clsb"] / p_values["clb"]

        return p_values

    def upperlimit(self, printlevel=1):
        """
        Returns the upper limit of the parameter of interest.
        """

        pvalues = self.pvalues()
        poinull = self.poinull
        poivalues = poinull.value
        poiname = poinull.name
        poiparam = poinull.parameter

        bestfitpoi = self.calculator.config.bestfit.params[poiparam]["value"]
        sel = poivalues > bestfitpoi

        if self.CLs:
            k = "cls"
        else:
            k = "clsb"

        values = {}
        if isinstance(self.calculator, AsymptoticCalculator):
            keys = [k]
        else:
            keys = [k, "exp", "exp_p1", "exp_m1", "exp_p2", "exp_m2"]

        for k_ in keys:
            p_ = pvalues[k_]
            pvals = poivalues
            if k_ not in ["exp_m1", "exp_m2"]:
                p_ = p_[sel]
                pvals = pvals[sel]
            p_ = p_ - self.alpha

            s = InterpolatedUnivariateSpline(pvals, p_)
            val = s.roots()

            if len(val) > 0:
                poiul = val[0]
            else:
                poiul = None
            if k_ == k:
                k_ = "observed"

            values[k_] = poiul

        if isinstance(self.calculator, AsymptoticCalculator):
            poiul = POI(poiparam, poiul)
            exp_poi = self.calculator.expected_poi
            sigmas = [0.0, 1.0, 2.0, -1.0, -2.0]
            kwargs = dict(poinull=poiul, poialt=self.poialt, nsigma=sigmas,
                          alpha=self.alpha, CLs=self.CLs)

            results = exp_poi(**kwargs)
            keys = ["exp", "exp_p1", "exp_p2", "exp_m1", "exp_m2"]

            for r, k_ in zip(results, keys):
                values[k_] = r

        if printlevel > 0:

            msg = "\nObserved upper limit: {0} = {1}"
            print(msg.format(poiname, values["observed"]))
            msg = "Expected upper limit: {0} = {1}"
            print(msg.format(poiname, values["exp"]))
            msg = "Expected upper limit +1 sigma: {0} = {1}"
            print(msg.format(poiname, values["exp_p1"]))
            msg = "Expected upper limit -1 sigma: {0} = {1}"
            print(msg.format(poiname, values["exp_m1"]))
            msg = "Expected upper limit +2 sigma: {0} = {1}"
            print(msg.format(poiname, values["exp_p2"]))
            msg = "Expected upper limit -2 sigma: {0} = {1}"
            print(msg.format(poiname, values["exp_m2"]))

        return values

    def plot(self, ax=None, show=True, **kwargs):
        """
        Plot the pvalues obtained with CLsb/CLb/CLs, and using the asimov
        datasets (median p_value, +bands), scanned for the different values of
        the parameter of interest.

            **Arguments:**
                - **ax** (optionnal) matplotlib axis
                - **show** (optionnal) show the plot. default **True**.
        """

        import matplotlib.pyplot as plt

        pvalues = self.pvalues()
        poivalues = self.poinull.value
        poiname = self.poinull.name
        alpha = self.alpha

        if ax is None:
            _, ax = plt.subplots(figsize=(10, 8))

        if self.CLs:
            cls_clr = "r"
            clsb_clr = "b"
        else:
            cls_clr = "b"
            clsb_clr = "r"

        ax.plot(poivalues, pvalues["cls"], label="Observed CL$_{s}$",
                marker=".", color='k', markerfacecolor=cls_clr,
                markeredgecolor=cls_clr, linewidth=2.0, ms=11)
        ax.plot(poivalues, pvalues["clsb"], label="Observed CL$_{s+b}$",
                marker=".", color='k', markerfacecolor=clsb_clr,
                markeredgecolor=clsb_clr, linewidth=2.0, ms=11,
                linestyle=":")
        ax.plot(poivalues, pvalues["clb"], label="Observed CL$_{b}$",
                marker=".", color='k', markerfacecolor="k",
                markeredgecolor="k", linewidth=2.0, ms=11)
        ax.plot(poivalues, pvalues["exp"],
                label="Expected CL$_{s}-$Median", color='k',
                linestyle="--", linewidth=1.5, ms=10)
        ax.plot([poivalues[0], poivalues[-1]], [alpha, alpha], color='r',
                linestyle='-', linewidth=1.5)
        ax.fill_between(poivalues, pvalues["exp"], pvalues["exp_p1"],
                        facecolor="lime",
                        label="Expected CL$_{s} \\pm 1 \\sigma$")
        ax.fill_between(poivalues, pvalues["exp"], pvalues["exp_m1"],
                        facecolor="lime")
        ax.fill_between(poivalues, pvalues["exp_p1"], pvalues["exp_p2"],
                        facecolor="yellow",
                        label="Expected CL$_{s} \\pm 2 \\sigma$")
        ax.fill_between(poivalues, pvalues["exp_m1"], pvalues["exp_m2"],
                        facecolor="yellow")

        if self.CLs:
            ax.set_ylim(-0.01, 1.1)
        else:
            ax.set_ylim(-0.01, 0.55)
        ax.set_ylabel("p-value")
        ax.set_xlabel(poiname)
        ax.legend(loc="best", fontsize=14)

        if show:
            plt.show()

    def plot_qdist(self, poinull, bins=50, log=False, histtype='step',
                   **kwargs):

        import matplotlib.pyplot as plt

        if isinstance(self.calculator, AsymptoticCalculator):
            raise ValueError("Nothing to plot!")

        poiparam = poinull.parameter
        bestfitpoi = self.calculator.config.bestfit.params[poiparam]["value"]
        bestfitpoi = POI(poiparam, bestfitpoi)

        qnull = self.calculator.qnull(poinull)
        plt.hist(qnull, bins=bins, log=log, histtype=histtype, label="qnull",
                 color="r")

        qalt = self.calculator.qalt(poinull, self.poialt)
        plt.hist(qalt, bins=bins, log=log, histtype=histtype, label="qalt",
                 color="b")

        qobs = self.calculator.qobs(poinull, bestfitpoi)
        plt.axvline(qobs, color="k", label="qobs")

        plt.xlabel("q")
        plt.legend(loc="best")
