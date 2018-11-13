from ..hypothesis import Hypothesis
from ..calculators.calculator import Calculator
from ..utils.wrappers import MinuitWrapper
from ..parameters import POI


class HypoTest(object):
    """
    Basic class for hypothesis test.

    **Arguments:**
        - **null_hypothesis** a statnight.model.Hypothesis representing the
        null hypothesis of the test.
        - **null_hypothesis** a statnight.model.Hypothesis representing the
        alterrnative hypothesis of the test.
    """

    def __init__(self, null_hypothesis, alt_hypothesis, calculator,
                 qtilde=False):
        """ __init__ function """

        msg = "Invalid type, {0}, for {1} hypothesis. Hypothesis required."

        if not isinstance(null_hypothesis, Hypothesis):
            msg = msg.format(null_hypothesis.__class__.__name__, "null")
            raise TypeError(msg)

        if not isinstance(alt_hypothesis, Hypothesis):
            msg = msg.format(alt_hypothesis.__class__.__name__, "alt")
            raise TypeError(msg)

        pois_in_null = haspois(null_hypothesis)
        pois_in_alt = haspois(alt_hypothesis)

        if not(pois_in_null or pois_in_alt):
            print(null_hypothesis.summary())
            print(alt_hypothesis.summary())
            msg = "At least one parameter of interest is required in one of "
            msg += "the hypothesis."
            raise ValueError(msg)
        self._null_hypothesis = null_hypothesis
        self._alt_hypothesis = alt_hypothesis

        if not isinstance(calculator, Calculator):
            msg = "Invalid type, {0}, for calculator. Calculator required."
            raise TypeError(msg)
        self._calculator = calculator

        checkqtilde(qtilde)
        self._qtilde = qtilde

        self._null_nll = {}

    @property
    def null_hypothesis(self):
        """
        Returns the null hypothesis.
        """
        return self._null_hypothesis

    @property
    def alt_hypothesis(self):
        """
        Returns the alternative hypothesis.
        """
        return self._alt_hypothesis

    @property
    def calculator(self):
        """
        Returns the calculator.
        """
        return self._calculator

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

    def null_minuit(self):
        if hasattr(self, "_null_minuit"):
            return self._null_minuit
        else:
            hypo = self.null_hypothesis
            lh = hypo.costfunction

            self._null_minuit = MinuitWrapper(lh, pedantic=True)
            return self._null_minuit

    def null_nll(self, poi):

        if poi.value not in self._null_nll.keys():
            self._null_nll[poi.value] = compute_1D_NLL(self.null_minuit(),
                                                       poi.name, poi.value)

            return self._null_nll[poi.value]


def haspois(hypo):
    def ispoi(p):
        return isinstance(p, POI)
    if isinstance(hypo.pois, (list, tuple)):
        nonzero = len(hypo.pois) > 0
        allpois = all(ispoi(p) for p in hypo.pois)
        return nonzero and allpois
    else:
        return ispoi(hypo.pois)


def checkqtilde(qtilde):
    if not isinstance(qtilde, bool):
        raise TypeError("Qtilde must set to True or False.")


def compute_1D_NLL(minuit, poi, val, npoints=1):

    range = (val, -1.)

    nll_curve = minuit.mnprofile(poi, npoints, range)

    return nll_curve[1]
