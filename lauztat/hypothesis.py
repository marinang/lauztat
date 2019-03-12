from iminuit import describe
from .parameters import POI


class Hypothesis:
    """
    Class for hypothesis definition.

    **Arguments:**

        - **costfunction** callable object. Negative log-likelihood (NLL)\
        function of a model and a dataset depending on a set of nuisances and\
        parameters of interest.
        - **pois** (optional).
    """

    def __init__(self, costfunction, *pois):
        """
        __init__ function
        """

        self._costfunction = check_costfunc(costfunction)
        self._pois = check_pois(pois)
        self._parameters = describe(costfunction)

    @property
    def costfunction(self):
        """
        Returns the costfunction.
        """
        return self._costfunction

    @property
    def parameters(self):
        """
        Returns the parameters of the cost function.
        """
        return self._parameters

    @property
    def pois(self):
        """
        Returns the parameters of interest.
        """
        if len(self._pois) == 1:
            return self._pois[0]
        else:
            return list(self._pois)

    @property
    def nuis(self):
        """
        Returns nuisance parameters.
        """
        poinames = self.pois_names()
        return [p for p in self.parameters if p not in poinames]

    def add_pois(self, *pois):
        """
        Add parameters of interest to the Hypothesis.

        **Arguments:**

            -**pois** an/a list of str.
        """
        pois = check_pois(pois)
        for p in pois:
            if p in self._pois:
                raise ValueError("'{0}' already in pois".format(p))
            if p.name not in self.parameters:
                raise ValueError("Unknown parameter '{0}'".format(p))

            self._pois.append(p)

    def rm_pois(self, *pois):
        """
        Remove parameters of interest from the Hypothesis.

        **Arguments:**

            -**pois** an/a list of str.
        """
        if not isinstance(pois, (list, tuple)):
            pois = [pois]
        for p in pois:
            if p in self._pois:
                self._pois.remove(p)
            else:
                msg = "{0} not in parameters of interest."
                raise ValueError(msg.format(p))

    def pois_names(self):
        """
        Returns the names of the parameters of interests.
        """
        return [p.name for p in self._pois]

    def copy(self):
        if isinstance(self.pois, (list, tuple)):
            return Hypothesis(self.costfunction, *self.pois)
        else:
            return Hypothesis(self.costfunction, self.pois)


def check_costfunc(costfunc):
    if hasattr(costfunc, "__call__"):
        args = [1.0 for n in range(len(describe(costfunc)))]
        test_return = costfunc(*args)
        if not isinstance(test_return, (int, float)):
            msg = "Please provide a cost function that returns a number"
            msg += " (int/float)."
            raise ValueError(msg)
        return costfunc
    else:
        msg = "Please provide a callable for the cost function."
        raise TypeError(msg)


def check_pois(pois):
    if not isinstance(pois, (list, tuple)):
        pois = [pois]
    elif isinstance(pois, tuple):
        pois = list(pois)
    for p in pois:
        if not isinstance(p, POI):
            msg = "{0} not a POI.".format(p)
            raise ValueError(msg)

    return pois
