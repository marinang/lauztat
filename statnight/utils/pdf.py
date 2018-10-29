#!/usr/bin/python

badvalue = 1e-300
smallestdiv = 1e-10

from iminuit import describe
from math import exp, log, sqrt, erf, pi

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
			self.func_code = MinimalFuncCode(["x","mean","sigma"])
		
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
		
	def nll(self, x, *args):
		
		mean, sigma = self._get_args(*args)

		ret  = log( 1 / (sigma * sqrt(2*pi)))
		ret += -0.5 * ( (x - mean) / sigma )**2
		return -ret
		
gaussian = Gaussian()

class Exponential():
	"""
	Exponential.
	"""
	
	def __init__(self, tau=None):
		self._tau = tau
		self._hastau = self._tau is not None
		
		if not self._hastau:
			self.func_code = MinimalFuncCode(["x","tau"])
	
	@property
	def tau(self):
		return self._tau
		
	def _get_args(self, *args):
		
		tau = self.tau if self._hastau else args[0]
				
		return tau
		
	def __call__(self, x, *args):
		
		if x >= 0:
			tau = self._get_args(*args)
			ret = tau * exp( x * -tau )
		else:
			ret = 0.
	
		return ret
		
	def cdf(self, x, *args):
		
		if x >= 0:
			tau = self._get_args(*args)
			ret = 1. - exp( x * -tau )
		else:
			ret = 0.
	
		return ret
		
	def integrate(self, bound, nint_subdiv, *args):
		
		a, b = bound
		
		Fa = self.cdf(a, *args)
		Fb = self.cdf(b, *args)
				
		return Fb - Fa
		
	def nll(self, x, *args):
		
		if x >= 0:
			tau = self._get_args(*args)
			ret  = log(tau) - tau*x
		else:
			ret = -100000
		return -ret
		
exponential = Exponential()
		
#class Normalized(object):
#	
#	def __init__(self, pdf, range):
#		self.pdf = pdf
#		self.func_code = MinimalFuncCode(describe(pdf))
#		self.range = range
#		
#	def __call__(self, x, *args):
#		ret = self.pdf(x, *args)
#		norm = self.normalization(*args)
#		return ret / norm 
#		
#	def cdf(self, x, *args):
#		ret = self.pdf.cdf(x, *args)
#		norm = self.normalization(*args)
#		return ret / norm 
#		
#	def integrate(self, bound, nint_subdiv, *args):
#		ret = self.pdf.integrate(bound, nint_subdiv, *args)
#		norm = self.normalization(*args)
#		return ret / norm 
#		
#	def normalization(self, *args):
#		return self.pdf.integrate(self.range, 100, *args)
#		
#	def nll(self, x, *args):
#		return - log(self(x, *args))
#		
#class Extended(object):
#	
#	def __init__(self, pdf, extname):
#		self.pdf = pdf
#		variables = describe(pdf) += [extname]
#		self.func_code = MinimalFuncCode(variables)
#		
#	def __call__(self, x, *args):
#		ret = self.pdf(x, *args)
#		extterm = args[-1]
#		return ret * extterm 
#		
#	def cdf(self, x, *args):
#		ret = self.pdf.cdf(x, *args)
#		extterm = args[-1]
#		return ret * extterm 
#		
#	def integrate(self, bound, nint_subdiv, *args):
#		ret = self.pdf.integrate(bound, nint_subdiv, *args)
#		extterm = args[-1]
#		return ret * extterm
#		
#	def nll(self, x, *args):
#		return - log(self(x, *args))
		

