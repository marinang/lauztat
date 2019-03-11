def profileLikelihood(minimizer, loss, var, value):
    with var.set_value(value) as value:
        var.floating = False
        minimum = minimizer.minimize(loss=loss)
    var.floating = True
    return minimum.fmin


def base_sampler(models, floatting_params=None, n=None, *args, **kwargs):
    if floatting_params:
        floatting_params = [f.name for f in floatting_params]

    samplers = []
    fixed_params = []
    for m in models:
        def cond(p):
            if floatting_params:
                return p.name in floatting_params
            else:
                False
        fixed = [p for p in m.get_dependents() if not cond(p)]
        fixed_params.append(fixed)

    for m, p in zip(models, fixed_params):
        n_ = n
        if n_ is None:
            if m.is_extended:
                n_ = "extended"
        sampler = m.create_sampler(n=n_, fixed_params=p)
        samplers.append(sampler)

    return samplers


def base_sample(sampler, ntoys, param=None, value=None, *args, **kwargs):
    for i in range(ntoys):
        if param and value:
            with param.set_value(value):
                for s in sampler:
                    s.resample()
        else:
            for s in sampler:
                s.resample()

        yield i


class Config(object):

    def __init__(self, models, datasets, lossbuilder, minimizer, sampler=None,
                 sample_method=None, pll=None, weights=None, bestfit=None):

        if not isinstance(models, (list, tuple)):
            models = [models]

        if not isinstance(datasets, (list, tuple)):
            datasets = [datasets]

        if weights is None:
            weights = [None for d in datasets]

        if not isinstance(weights, (list, tuple)):
            weights = [weights]

        self.models = models
        self.datasets = datasets
        self.weights = weights
        self.lossbuilder = lossbuilder
        self.minimizer = minimizer
        self.minimizer.verbosity = 0

        if pll is None:
            self.pll = profileLikelihood
        else:
            self.pll = pll

        self._sampler = sampler
        self._sample = sample_method
        self._bestfit = bestfit

    def sampler(self, floatting_params=None, *args, **kwargs):

        if self._sampler is None:
            return base_sampler(self.models, floatting_params, *args, **kwargs)
        else:
            return self._sampler(self.models, floatting_params,
                                 *args, **kwargs)

    def sample(self, sampler, ntoys, param=None, value=None):

        if self._sample is None:
            return base_sample(sampler, ntoys, param, value)
        else:
            return self._sample(sampler, ntoys, param, value)

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
            self.minimizer.verbosity = 5
            mininum = self.minimizer.minimize(loss=self.obsloss())
            self.minimizer.verbosity = 0
            self._bestfit = mininum
            return self._bestfit

    @bestfit.setter
    def bestfit(self, value):
        """
        Set the best fit values.
        """
        self._bestfit = value

    def deps_tobestfit(self):
        for m in self.models:
            for dep in m.get_dependents():
                bf_val = self.bestfit.params[dep]["value"]
                dep.set_value(bf_val)
