#!/usr/bin/python
from math import exp, log, sqrt, erf, pi

badvalue = 1e-300
smallestdiv = 1e-10


class MinimalFuncCode(object):
    def __init__(self, arg):
        self.co_varnames = tuple(arg)
        self.co_argcount = len(arg)

    def append(self, varname):
        tmp = list(self.co_varnames)
        tmp.append(varname)
        self.co_varnames = tuple(tmp)
        self.co_argcount = len(self.co_varnames)


class Gaussian:
    """
    Gaussian.
    """

    def __init__(self, mean=None, sigma=None):
        self._mean = mean
        self._sigma = sigma
        self._hasmean = self._mean is not None
        self._hassigma = self._sigma is not None

        if not (self._hasmean and self._hassigma):
            self.func_code = MinimalFuncCode(["x", "mean", "sigma"])

    @property
    def mean(self):
        return self._mean

    @property
    def sigma(self):
        return self._sigma

    def _get_args(self, *args):

        mean = self.mean if self._hasmean else args[0]
        sigma = self.sigma if self._hassigma else args[1]

        return mean, sigma

    def __call__(self, x, *args):

        mean, sigma = self._get_args(*args)

        if sigma < smallestdiv:
            ret = badvalue
        else:
            d = (x-mean)/sigma
            d2 = d*d
            ret = 1/(sqrt(2*pi)*sigma)*exp(-0.5*d2)

        return ret

    def cdf(self, x, *args):

        mean, sigma = self._get_args(*args)

        xscale = sqrt(2.0) * sigma

        return 0.5*(1 + erf((x - mean)/xscale))

    def integrate(self, bound, nint_subdiv, *args):

        a, b = bound

        Fa = self.cdf(a, *args)
        Fb = self.cdf(b, *args)

        return Fb - Fa

    def log(self, x, *args):

        mean, sigma = self._get_args(*args)

        ret = log(1 / (sigma * sqrt(2*pi)))
        ret += -0.5 * ((x - mean) / sigma)**2
        return -ret


gaussian = Gaussian()
