from .hypotest import HypoTest
from scipy.stats import norm


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
            print("p_value for the Null hypothesis = {0}".format(pnull))
            print("Significance = {0}".format(Z))

        ret = {
               "pnull": pnull,
               "significance": Z,
               }

        return ret
