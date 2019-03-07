

class Config(object):

    def __init__(self, models, datasets, lossbuilder, minimizer, pll,
                 sampler=None, weights=None, constraints=None, bestfit={}):

        if not isinstance(models, (list, tuple)):
            models = [models]

        if not isinstance(datasets, (list, tuple)):
            datasets = [datasets]

        if weights is None:
            weights = [None for d in datasets]

        if not isinstance(weights, (list, tuple)):
            weights = [weights]

        self.models = models
        self.constraints = constraints
        self.datasets = datasets
        self.weights = weights
        self.lossbuilder = lossbuilder
        self.minimizer = minimizer
        self.pll = pll
        self.sampler = sampler
        self._bestfit = bestfit

    def obsloss(self):
        return self.lossbuilder(self.models, self.datasets, self.weights)

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
            mininum = self.minimizer.minimize(loss=self.obsloss())
            self._bestfit = mininum
            return self._bestfit

    @bestfit.setter
    def bestfit(self, value):
        """
        Set the best fit values.
        """
        self._bestfit = value
