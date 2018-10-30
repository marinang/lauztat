#!/usr/bin/python

from iminuit import describe
import attr
from attr import attrs, attrib

def check_range(instance=None, range=None, value=None):
	if value and not (isinstance(value, (list, tuple)) and len(value) == 2 and all(isinstance(v, (float, int)) for v in value)):
		raise TypeError("Please provide a tuple/list with lower and upper limits for the range of this parameter.")
	if value[0] >= value[1]:
		raise ValueError("Lower limit of the range should be strictly lower the the upper limit.")
		
def check_initvalue(instance=None, initvalue=None, value=None):
	if value != -1:
		_range = instance.range
		if not(value >= _range[0] and value <= _range[1]):
			raise ValueError("Please provide a number between given range: {0}.".format(_range))

def check_initstep(instance=None, initstep=None, value=None):
	_range = instance.range
	if value != -1:
		if value >= (_range[1] - _range[0]):
			raise ValueError("Initial step should be strictly lower than the range:{0}.".format(_range))

def check_constraint(instance=None, constraint=None, value=None ):
	if value:
		if hasattr(value, "__call__"):
			pars = describe(value)
			if len(pars) > 1:
				raise TypeError("Please provide a function with of single argument.")
				
			test_return = value(0.0)
			if not isinstance(test_return, (int, float)):
				raise ValueError("Please provide a function that returns a number (int/float).")
		else:
			raise TypeError("Please provide a function with one argument returning a number (int/float).")

############################# Parameters ##################################

@attrs
class Object(object):
	pass

@attrs
class Named(Object):
	name = attrib(validator=attr.validators.instance_of(str))

@attrs(repr=False)				
class Range(Object):
	range = attrib(validator=check_range)
									
	def __repr__(self):
		return "Range({})".format(self.range)
		
@attrs(repr=False, slots=True)				
class Observable(Named, Range):
		
	def __repr__(self):
		return "Observable('{0}', range={1})".format(self.name, self.range)

@attrs(repr=False, slots=True)		
class Constant(Named):
	value = attr.ib(type=(int,float), validator=attr.validators.instance_of((int,float)))
			
	def tominuit(self):
		ret = {}
		ret[self.name] = self.value
		ret["fix_{0}".format(self.name)] = True
		return ret
		
	def __repr__(self):
		return "Constant('{0}', value={1})".format(self.name, self.value)

@attrs(repr=False, slots=True)				
class Variable(Named, Range):
	
	initvalue  = attr.ib(type=(int,float), 
						 validator=[attr.validators.instance_of((int,float)), check_initvalue], 
						 default=-1.)
	initstep   = attr.ib(type=(int,float), 
						 validator=[attr.validators.instance_of((int,float)), check_initstep], 
						 default=-1.)
	constraint = attr.ib(type=(int,float), 
						 validator=check_constraint, 
						 default=None)
								
	def __attrs_post_init__(self):
		if self.initvalue == -1:
			self.initvalue = self.range[0] + (self.range[1] - self.range[0])/2.
		if self.initstep  == -1:
			self.initstep  = (self.range[1] - self.range[0])/100.
				
	def tominuit(self):
		ret = {}
		ret[self.name] = self.initvalue
		ret["limit_{0}".format(self.name)] = self.range
		ret["error_{0}".format(self.name)] = self.initstep
		return ret
				
	def __repr__(self):
		basis = "Variable('{0}', initvalue={1}, range={2}, initstep={3}".format(self.name, 
				self.initvalue, self.range, self.initstep)
		
		if self.constraint:
			return basis + ", constraint={0})".format(self.constraint)
		else:
			return basis + ")"

										

