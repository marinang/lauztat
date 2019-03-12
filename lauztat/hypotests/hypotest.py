from ..calculators.calculator import Calculator
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

    def __init__(self, poinull, calculator, poialt=None):
        """ __init__ function """

        msg = "Invalid type, {0}, for parameter of interest for the {1}"
        msg += " hypothesis."

        if not isinstance(poinull, POI):
            msg = msg.format(poinull.__class__.__name__, "null")
            raise TypeError(msg)

        if poialt is not None and not isinstance(poialt, POI):
            msg = msg.format(poialt.__class__.__name__, "alt")
            raise TypeError(msg)

        self._poinull = poinull
        self._poialt = poialt

        if not isinstance(calculator, Calculator):
            msg = "Invalid type, {0}, for calculator. Calculator required."
            raise TypeError(msg)
        self._calculator = calculator

    @property
    def poinull(self):
        """
        Returns the POI for the null hypothesis.
        """
        return self._poinull

    @property
    def poialt(self):
        """
        Returns the POI for the alternative hypothesis.
        """
        return self._poialt

    @property
    def calculator(self):
        """
        Returns the calculator.
        """
        return self._calculator

        # self._bestfitpoi = None
