#!/usr/bin/python
import pytest

from statnight.parameters import Object, Named, Range, Observable, Variable, Constant

def test_constructors():	
	o = Object()
	
	n = Named(name="n")
	with pytest.raises(TypeError):
		Named()
		
	r = Range(range=(1,2))
	with pytest.raises(TypeError):
		Range()
	with pytest.raises(TypeError):
		Range(1)
	with pytest.raises(TypeError):
		Range(range=1)
	with pytest.raises(TypeError):
		Range(range=[1])
	with pytest.raises(TypeError):
		Range(range=[1,"2"])
	with pytest.raises(ValueError):
			Range(range=[1,-1])
		
	obs = Observable("obs", (1,2))
	with pytest.raises(TypeError):
		Observable("obs")
	with pytest.raises(TypeError):
		Observable("obs", [1])
	with pytest.raises(TypeError):
		Observable("obs", [1,"2"])
	with pytest.raises(ValueError):
		Observable("obs",range=[1,-1])
	
	const = Constant("const", 1.4)
	with pytest.raises(TypeError):
		Constant("const")
	with pytest.raises(TypeError):
		Constant("const", "3")
	
	var = Variable("var", (1,2))
	with pytest.raises(TypeError):
		Variable("var")
	with pytest.raises(TypeError):
		Variable("var", [1,"2"])
	with pytest.raises(ValueError):
		Variable("var", [1, -1])
	with pytest.raises(ValueError):
		Variable("var", range=(1,2), initvalue=3)
	with pytest.raises(TypeError):
		Variable("var", range=(1,2), initvalue="3")
	with pytest.raises(TypeError):
		Variable("var", range=(1,2), initstep="0.1")
	with pytest.raises(ValueError):
		Variable("var", range=(1,2), initstep=1)
	with pytest.raises(TypeError):
		Variable("var", range=(1,2), constraint="1")
	with pytest.raises(TypeError):
		def f(a, b):
			return a*b
		Variable("var", range=(1,2), constraint=f)
	with pytest.raises(ValueError):
		def f(a):
			return str(a)
		Variable("var", range=(1,2), constraint=f)
		
def test_properties():
	
	n = Named(name="n")
	assert n.name == "n"
	
	r = Range(range=(1,2))
	assert r.range == (1,2)
	
	obs = Observable("obs", (1,2))
	assert obs.name == "obs"
	assert obs.range == (1,2)
	
	const = Constant("const", 1.4)
	assert const.name == "const"
	assert const.value == 1.4
			
	var = Variable("var", (1,2))
	assert var.name == "var"
	assert var.range == (1,2)
	assert var.initvalue == 1.5
	assert var.initstep  == 0.01
	assert var.constraint == None
	
	def f(a):
		return a+2
		
	var = Variable("var", (1,2), initvalue=1.3, initstep=0.3, constraint=f)
	assert var.name == "var"
	assert var.range == (1,2)
	assert var.initvalue == 1.3
	assert var.initstep  == 0.3
	assert var.constraint == f
			
def test_methods():
	
	const = Constant("const", 1.4)
	minuit_const = const.tominuit()
	assert len(minuit_const.keys()) == 2
	assert minuit_const["const"] == 1.4
	assert minuit_const["fix_const"] == True
	
	var = Variable("var", (1,2))
	minuit_var = var.tominuit()
	assert len(minuit_var.keys()) == 3
	assert minuit_var["var"] == var.initvalue
	assert minuit_var["limit_var"] == var.range
	assert minuit_var["error_var"] == var.initstep
	
def test_repr():
	
	obs = Observable("obs", (1,2))
	assert repr(obs) == "Observable('obs', range=(1, 2))"
	
	const = Constant("const", 1.4)
	assert repr(const) == "Constant('const', value=1.4)"
	
	var = Variable("var", (1,2))
	assert repr(var) == "Variable('var', initvalue=1.5, range=(1, 2), initstep=0.01)"
	
	def f(a):
		return (a-2)**2
	var = Variable("var", (1,2), initvalue=1.2, initstep=0.1, constraint=f)
	assert repr(var) == "Variable('var', initvalue=1.2, range=(1, 2), initstep=0.1, constraint={0})".format(f)