#!/usr/bin/python

############################# Parameters ##################################

class Object:
	def __init__(self, **kwargs):
		pass

class Named(Object):
	def __init__(self, **kwargs):
		name = kwargs["name"]
		super().__init__(**kwargs)
		self._name = name
			
	@property
	def name(self):
		return self._name
				
class Range(Object):
	def __init__(self, **kwargs):
		range = kwargs["range"]
		super().__init__(**kwargs)
		check_range(range)
		self._range = range
							
	@property
	def range(self):
		return self._range
		
	@range.setter
	def range(self, _range):
		check_range(_range)
		self._range = _range
						
class Observable(Named, Range):
	
	def __init__(self, name, range):
		super().__init__(name=name, range=range)
						
	def __repr__(self):
		return "Observable('{0}', range={1})".format(self.name, self.range)
		
class Constant(Named):
	
	def __init__(self, name, value):
		super().__init__(name=name)
		
		self._value = value
		
	@property
	def value(self):
		return self._value
		
	@value.setter
	def value(self, _value):
		if not isinstance(_value, (int,float)):
			raise ValueError("Please provide a number (int/float).")
		self._value = _value
		
	def tominuit(self):
		ret = {}
		ret[self.name] = self.value
		ret["fix_{0}".format(self.name)] = True
		return ret
		
	def __repr__(self):
			return "Constant('{0}', value={1})".format(self.name, self.value)
					
class Variable(Named, Range):
	
	def __init__(self, name, range=None, initvalue=None, initstep=None, constraint=None):
		super().__init__(name=name, range=range)
		
		self._initvalue = check_initvalue(initvalue, range)
		self._initstep = check_initstep(initstep, range)
		check_contraint(constraint)
		self._constraint = constraint
		
	@property
	def initvalue(self):
		return self._initvalue
		
	@initvalue.setter
	def initvalue(self, _initvalue):
		check_initvalue(_initvalue, self.range)
		self._initvalue = _initvalue
		
	@property
	def initstep(self):
		return self._initstep
		
	@initvalue.setter
	def initvalue(self, _initstep):
		check_initstep(_initstep, self.range)
		self._initstep = _initstep
		
	@property
	def constraint(self):
		return self._constraint
		
	@constraint.setter
	def constraint(self, _constraint):
		check_constraint(_constraint)
		sself._constraint = _constraint
		
	def tominuit(self):
		ret = {}
		ret[self.name] = self.initvalue
		ret["limit_{0}".format(self.name)] = self.range
		ret["error_{0}".format(self.name)] = self.initstep
		return ret
				
	def __repr__(self):
		basis = "Variable('{0}', initvalue={1}, range={2}, initstep={3}".format(self.name, self.initvalue, self.range, self.initstep)
		
		if self.constraint:
			return basis + ", constraint={0})".format(self.constraint)
		else:
			return basis + ")"
				
def check_range(_range):
	if _range and not (isinstance(_range, (list, tuple)) and len(_range) == 2 and all(isinstance(v, (float, int)) for v in _range)):
		raise ValueError("Please provide a tuple/list with lower and upper limits for the range of this parameter.")
		
def check_initvalue(_initvalue, _range):
	if _range:
		if _initvalue != None:
			if not (isinstance(_initvalue, (int, float)) and _initvalue >= _range[0] and _initvalue <= _range[1]):
				raise ValueError("Please provide a number (int/float) between given range: {0}.".format(_range))
			else:
				return _initvalue
		else:
			return (_range[1] - _range[0])/2.
	else:
		raise ValueError("Please provide a range for this paramater.")

def check_initstep(_initstep, _range):
	if _initstep != None:
		if not isinstance(_initstep, (int, float)):
			raise ValueError("Please provide a a number (int/float) for the initial step of this parameter.")
		else:
			return _initstep
	else:
		if _range:
			return (_range[1] - _range[0])/100
		else:
			raise ValueError("Please provide a range for this paramater.")
				
def check_contraint( _constraint ):
	if _constraint:
		if hasattr(_constraint, "__call__"):
			pars = describe(_constraint)
			if len(pars) > 1:
				raise ValueError("Please provide a function with of single argument.")
				
			test_return = _constraint(0.0)
			if not isinstance(test_return, (int, float)):
				raise ValueError("Please provide a function that returns a number (int/float).")
		else:
			raise ValueError("Please provide a function with one argument returning a number (int/float).")
										

