#!/usr/bin/python
import pytest

from statnight.parameters import Observable, Variable, Constant
from statnight.model import Model, Hypothesis
from scipy.stats import norm
from statnight.utils.pdf import Gaussian
import numpy as np

np.random.seed(10)

def pdf(x, mu, sigma):
	return norm.pdf(x, loc=mu, scale=sigma)
	
x     = Observable("x", range=(-5,5))
mu    = Variable("mu", range=(-0.5,0.5), initvalue=0.0, initstep=0.01)
sigma = Variable("sigma", range=(0.7,1.3), initvalue=1.0, initstep=0.01)

data = np.random.normal(0.0, 1.0, 1000)

def test_model_constructors():

	m = Model(pdf)
	with pytest.raises(TypeError):
		Model()
	with pytest.raises(TypeError):
		Model("PDF")
	with pytest.raises(ValueError):
		def f(x, mu):
			return "{0}_{1}".format(x, mu)
		Model(f)
		
	m = Model(pdf, observables=[x], variables=[mu, sigma])
	with pytest.raises(ValueError):
		nu = Variable("nu", range=(-0.5,0.5))
		Model(pdf, observables=[x], variables=[nu, sigma])
	with pytest.raises(ValueError):
		Model(pdf, observables=[x], variables=[mu, sigma, x])
	with pytest.raises(ValueError):
		nu = Variable("nu", range=(-0.5,0.5))
		Model(pdf, observables=[x], variables=[mu, sigma], ext_pars=[nu])
		
def test_model_methods():
	
	m = Model(pdf)
	assert m.pdf == pdf
	assert m.pdf(0., 0., 1.) == pdf(0., 0., 1.)
	assert m.parameters == ["x", "mu", "sigma"]
	
	m.add_obs(x)
	assert type(m.obs) == list
	assert len(m.obs)  == 1
	assert m.obs == m.observables
	assert m.obs[0] == x
	with pytest.raises(ValueError):
			m.add_obs(x)
	with pytest.raises(ValueError):
			m.add_obs(mu)
			
	m.add_vars(mu)
	assert type(m.vars) == list
	assert len(m.vars)  == 1
	assert m.vars == m.variables
	assert m.vars[0] == mu
	with pytest.raises(ValueError):
		m.add_vars(mu)
	with pytest.raises(ValueError):
		m.add_vars(x)
		
	m.add_vars(sigma)
	assert len(m.vars)  == 2
	assert m.vars[1] == sigma
	
	assert m.extended == False
	assert m.ext_pars == []
	m.add_ext_pars("mu")
	assert m.extended == True
	assert m.ext_pars == ["mu"]
	with pytest.raises(ValueError):
		m.add_ext_pars(x)
		
	assert m["x"] == x
	assert m["mu"] == mu
	assert m["sigma"] == sigma
		
	m.rm_obs("x")
	assert len(m.obs)  == 0
	m.rm_vars("sigma")
	assert len(m.vars)  == 1
	assert m.vars[0] == mu
	assert m.ext_pars == ["mu"]
	m.rm_vars("mu")
	assert len(m.vars)  == 0
	assert m.extended == False
	
	m.add_vars(mu)
	m.add_ext_pars("mu")
	m.rm_ext_pars("mu")
	assert m.extended == False
	assert len(m.vars)  == 1
	assert m.vars[0] == mu
	
def test_nll_function():
	
	m = Model(pdf, observables=[x], variables=[mu, sigma])
	nll = m.nll_function(data)
	min_nll = nll(0.0, 1.0)
	
	assert min_nll <= nll(-0.1, 1.0)
	assert min_nll <= nll(0.1, 1.0)
	assert min_nll <= nll(0.0, 1.5)
	assert min_nll <= nll(0.0, 0.5)
	assert min_nll <= nll(0.1, 0.5)
	
	constraint = Gaussian(0.1, 0.0000001)
	_mu = Variable("mu", range=(-0.5,0.5), initvalue=0.0, initstep=0.01, 
				   constraint=constraint)
	m = Model(pdf, observables=[x], variables=[_mu, sigma])
	nll = m.nll_function(data)
	
	assert nll(0.1, 1.0) <= min_nll
	
def test_hypothesis():
	
	m = Model(pdf, observables=[x], variables=[mu, sigma])
	
	m.create_hypothesis(pois={"mu":0.1})
	m.create_hypothesis(pois={"mu":[0.8,0.9,1.0,1.1,1.2]})
	
	with pytest.raises(TypeError):
		m.create_hypothesis(mu)
	with pytest.raises(ValueError):
		m.create_hypothesis({"nu":0.1})
	
	
	
		
		