#!/usr/bin/python

import numpy as np

class Calculator:
	
	def __init__(self, null_hypothesis, alt_hypothesis, data = []):
		""" __init__ function """
		
		if not isHypothesis(null_hypothesis):
			raise ValueError("Invalid type, {0}, for null hypothesis. Hypothesis required".format(null_hypothesis.__class__.__name__))
			
#		if not ( len(null_hypothesis.obs) > 0 and len(null_hypothesis.pois) > 0 and len(null_hypothesis.nuis) > 0):
#			print(null_hypothesis.summary)
#			raise NotImplementedError("Null hypothesis not ready to be used.")
			
		if not isHypothesis(alt_hypothesis):
			raise ValueError("Invalid type, {0}, for alternate hypothesis. Hypothesis required".format(alt_hypothesis.__class__.__name__))
			
		pois_in_null = ( len(null_hypothesis.obs) > 0 and len(null_hypothesis.pois) > 0 and len(null_hypothesis.nuis) > 0)
		pois_in_alt  = ( len(alt_hypothesis.obs) > 0 and len(alt_hypothesis.pois) > 0 and len(alt_hypothesis.nuis) > 0)
		
		if not( pois_in_null or pois_in_alt ):
			print(null_hypothesis.summary)
			print(alt_hypothesis.summary)
			raise NotImplementedError("At least one parameter of interest is required in one of the hypothesis.")
			
#		if not ( len(alt_hypothesis.obs) > 0 and len(alt_hypothesis.pois) > 0 and len(alt_hypothesis.nuis) > 0):
#			print(alt_hypothesis.summary)
#			raise NotImplementedError("Alternate hypothesis not ready to be used.")
			
	
		self._null_hypothesis = null_hypothesis	
		self._alt_hypothesis = alt_hypothesis
		
		self._data = data

	@property
	def null_hypothesis(self):
		return self._null_hypothesis
		
	@property
	def alt_hypothesis(self):
		return self._alt_hypothesis
		
	@property
	def data(self):
		return self._data
		
	@data.setter
	def data(self, data):
		
		if not isinstance(data, np.ndarray):
			raise ValueError("Please provide data as numpy array.")
		
		self._data = data
		
def isHypothesis( hypo ):
	
	if hypo.__class__.__name__ == "Hypothesis":
		return True
	else:
		return False
		
	