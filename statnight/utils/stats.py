import numpy as np
from scipy import integrate

def likelihood( function, badvalue = 100000):
	def value(x, *args):
		val = function(x, *args)
		if val <= 0:
			val = badvalue
		return val
	return value

def compute_nll( function, data, weights, *args):
				
	lh = likelihood(function, badvalue = 1000000)
		
	vlh = np.vectorize(lh,  otypes=[float])
	
	values = vlh(data, *args)
	
	if weights is None:
		nll = -np.sum( np.log( values ) )
	else:
		nll = -np.sum( np.log( values ) * weights )
	
	return nll
	
def integrate1d(f, bound, nint, *args):

	def computeint(f, bound, nint, *args):
		x = np.linspace(bound[0], bound[1], nint)
		fv = np.vectorize(f)
		return integrate.simps(fv(x,*args),x)
		
	if hasattr(f, "integrate"):
		try:
			### from probfit ###
			ret = f.integrate(bound, nint, *args)
		except TypeError:
			ret = computeint(f, bound, nint, *args)
	else:
		ret = computeint(f, bound, nint, *args)
	
	return ret