#!/usr/bin/python

badvalue = 1e-300
smallestdiv = 1e-10

from math import exp, log, sqrt, erf, pi

class Gaussian:
	"""
	Gaussian.
	"""
	
	def __init__(self, mean=None, sigma=None):
		self._mean = mean
		self._sigma = sigma
		
	@property
	def mean(self):
		return self._mean
	
	@property
	def sigma(self):
		return self._sigma
		
	def _get_args(self, *args):
		
		mean = self.mean if self.mean is not None else args[0]
		sigma = self.sigma if self.sigma is not None else args[1]
		
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
		
	def integrate(self, bound, nint_subdiv, *arg):
		
		a, b = bound
		
		mean, sigma = self._get_args(*args)
		
		PiBy2 = pi/2.0
		rootPiBy2 = sqrt(PiBy2)
		xscale = sqrt(2.0) * sigma
				
		if sigma < smallestdiv:
			ret = badvalue
		else:
			ret  = erf((b - mean)/xscale)
			ret -= erf((a - mean)/xscale)
			ret *= 0.5
			
		return ret
		
	def nll(self, x, *args):
		
		mean, sigma = self._get_args(*args)

		ret  = log( 1 / (sigma * sqrt(2*pi)))
		ret += -0.5 * ( (x - mean) / sigma )**2
		return -ret
		
gaussian = Gaussian()
