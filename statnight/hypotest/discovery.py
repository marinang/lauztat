from .hypotest import HypoTest
from scipy.stats import norm


class Discovery(HypoTest):
    def __init__(self, null_hypothesis, alt_hypothesis, calculator,
                 qtilde=False):

        super(Discovery, self).__init__(null_hypothesis, alt_hypothesis,
                                        calculator, qtilde)

    def result(self, printlevel=1):
        """
        Returns the result of the discovery hypothesis test.
        """

        althypo = self.alt_hypothesis
        poinull = self.null_hypothesis.pois
        poialt = althypo.pois

        nll_poia_null = self.null_nll(poialt)

        nll_poin_null = self.null_nll(poinull)

        qnull = 2*(nll_poin_null - nll_poia_null)

        pnull, palt = self.calculator.pvalue(qnull, poinull, althypo,
                                             qtilde=self.qtilde,
                                             onesideddiscovery=True)

        clsb = palt
        clb = pnull
        Z = norm.ppf(1. - pnull)

        if printlevel > 0:
            print("p_value for the Null hypothesis = {0}".format(pnull))
            print("Significance = {0}".format(Z))
            print("CL_b = {0}".format(clb))
            print("CL_s+b = {0}".format(clsb))

        ret = {
               "pnull": pnull,
               "significance": Z,
               "clb": clb,
               "clsb": clsb,
               }

        return ret
