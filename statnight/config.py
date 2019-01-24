

class Config(object):

    def __init__(self, models, datasets, lossbuilder, minimizer, weights=None,
                 bestfit={}):

        if not isinstance(models, (list, tuple)):
            models = [models]

        if not isinstance(datasets, (list, tuple)):
            datasets = [datasets]

        if weights is None:
            weights = [None for d in datasets]

        if not isinstance(weights, (list, tuple)):
            weights = [weights]

        self.models = [m.copy() for m in models]
        self.datasets = datasets
        self.weights = weights
        self.lossbuilder = lossbuilder
        self.minimizer = minimizer
        self._bestfit = bestfit

    def obsloss(self):
        return self.lossbuilder(self.models, self.datasets, self.weights)

    def obsminimizer(self):
        if not hasattr(self, "_obsminimizer"):
            self._obsminimizer = self.minimizer(self.obsloss())
        return self._obsminimizer

    def loop(self):
        for n in range(len(self.models)):
            m = self.models[n]
            d = self.datasets[n]
            w = self.weights[n]
            yield (m, d, w)

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
