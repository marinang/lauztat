from .hypotest import HypoTest
from scipy.stats import norm
import matplotlib.pyplot as plt
from ..calculators import AsymptoticCalculator
from ..parameters import POI


class Discovery(HypoTest):
    def __init__(self, poinull, calculator):

        super(Discovery, self).__init__(poinull, calculator)

    def result(self, printlevel=1):
        """
        Returns the result of the discovery hypothesis test.
        """

        pnull, _ = self.calculator.pvalue(self.poinull, onesideddiscovery=True)
        pnull = pnull[0]

        Z = norm.ppf(1. - pnull)

        if printlevel > 0:
            print("\np_value for the Null hypothesis = {0}".format(pnull))
            print("Significance = {0}".format(Z))

        ret = {
               "pnull": pnull,
               "significance": Z,
               }

        return ret

    def plot_qdist(self, bins=50, log=False, histtype='step', **kwargs):

        import matplotlib.pyplot as plt

        if isinstance(self.calculator, AsymptoticCalculator):
            raise ValueError("Nothing to plot!")

        poiparam = self.poinull.parameter
        bestfitpoi = self.calculator.config.bestfit.params[poiparam]["value"]
        bestfitpoi = POI(poiparam, bestfitpoi)

        qnull = self.calculator.qnull(self.poinull)
        plt.hist(qnull, bins=bins, log=log, histtype=histtype, label="qnull")
        qobs = self.calculator.qobs(self.poinull, bestfitpoi)
        plt.axvline(qobs, color="r", label="qobs")
        plt.xlabel("q")
        plt.legend(loc="best")
