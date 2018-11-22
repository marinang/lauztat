

class Config(object):

    def __init__(self, model, data, lossbuilder, minimizer, weights=None,
                 bestfit={}):

        self.model = model.copy()
        self.data = data
        self.weights = weights
        self.lossbuilder = lossbuilder
        self.minimizer = minimizer
        self._bestfit = bestfit

    def obsloss(self):
        return self.lossbuilder(self.model, self.data, self.weights)

    def obsminimizer(self):
        if not hasattr(self, "_obsminimizer"):
            self._obsminimizer = self.minimizer(self.obsloss())
        return self._obsminimizer

    @property
    def bestfit(self):
        """
        Returns the best fit values.
        """
        if getattr(self, "_bestfit", None):
            return self._bestfit
        else:
            print("Get fit best values!")
            self.obsminimizer().minimize()
            values = self.obsminimizer().values
            self._bestfit = values
            return self._bestfit

    @bestfit.setter
    def bestfit(self, value):
        """
        Set the best fit values.
        """
        self._bestfit = value
