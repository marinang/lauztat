#!/usr/bin/python

from .calculator import Calculator
import iminuit
import math
from scipy.stats import norm
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from ..utils.stats import integrate1d

class AsymptoticCalculator(Calculator):
	
	def __init__(self, null_hypothesis, alt_hypothesis, data, qtilde=False, onesided=True, 
				 onesideddiscovery=False, CLs=True):
		
		super().__init__(null_hypothesis, alt_hypothesis, data)
				
		if len(null_hypothesis.pois) > 1 or len(alt_hypothesis.pois) > 1:
			raise ValueError("Asymptotic calculator valid only for one paramater of interest.")
			
		elif len(null_hypothesis.pois) == 1 and len(alt_hypothesis.pois) == 0:
			null_poi_name = null_hypothesis.poinames[0]
			print("{0} = 0 assumed for the alternative hypothesis.".format(null_poi_name))
			self._poi = null_hypothesis.getpoi(null_poi_name)
			self._poi_null_val = self.null_hypothesis.poivalues[null_poi_name]
			self._poi_alt_val = 0.
			
		elif len(null_hypothesis.pois) == 0 and len(alt_hypothesis.pois) == 1:
			alt_poi_name  = alt_hypothesis.poinames[0]
			print("{0} = 0 assumed for the null hypothesis.".format(alt_poi_name))
			self._poi = alt_hypothesis.getpoi(alt_poi_name)
			self._poi_null_val = 0.
			self._poi_alt_val = self.alt_hypothesis.poivalues[alt_poi_name]
			
		else:
			null_poi_name = null_hypothesis.poinames[0]
			alt_poi_name  = alt_hypothesis.poinames[0]
			
			if null_poi_name !=alt_poi_name:
				raise ValueError("Different names for parameters of interest in null and" 
				                +" alternative hypothesis.")
				
			poi_name = null_hypothesis.poinames[0]
			self._poi = null_hypothesis.model[alt_poi_name]
			self._poi_null_val = self.null_hypothesis.poivalues[poi_name]
			self._poi_alt_val = self.alt_hypothesis.poivalues[poi_name]
			
		self._qtilde = qtilde
		self._onesided = onesided
		self._onesideddiscovery = onesideddiscovery
		self._CLs = CLs
		self._null_nll = {}
		self._asy_nll  = {}
	
	@property	
	def qtilde(self):
		return self._qtilde
		
	@qtilde.setter	
	def qtilde(self, qtilde):
		if not isinstance(qtilde, bool):
			raise ValueError("qtilde must set to True/False, not {0}.".format(qtilde))
		self._qtilde = qtilde
		
	@property	
	def onesided(self):
		return self._onesided
		
	@onesided.setter	
	def onesided(self, onesided):
		if not isinstance(onesided, bool):
			raise ValueError("onesided must set to True/False, not {0}.".format(onesided))
		self._onesided = onesided
		
	@property	
	def onesideddiscovery(self):
		return self._onesideddiscovery
		
	@onesideddiscovery.setter	
	def onesideddiscovery(self, onesideddiscovery):
		if not isinstance(onesideddiscovery, bool):
			raise ValueError("onesideddiscovery must set to True/False, not {0}.".format(onesideddiscovery))
		self._onesideddiscovery = onesideddiscovery
		
	@property	
	def CLs(self):
		return self._CLs
		
	@CLs.setter	
	def CLs(self, CLs):
		if not isinstance(CLs, bool):
			raise ValueError("CLs must set to True/False, not {0}.".format(CLs))
		self._CLs = CLs
							
	def null_minuit(self):
		if hasattr(self, "_null_minuit"):
			return self._null_minuit
		else:
			if self._poi.name in self.null_hypothesis.poinames:
				hypo = self.null_hypothesis
			elif self._poi.name in self.alt_hypothesis.poinames:
				hypo = self.alt_hypothesis
				
			lh = hypo.model.nll_function(self.data, weights=None)
			
			params = {}
			
			for v in hypo.model.variables:
				pars = v.tominuit()
				params.update(pars)

			self._null_minuit = iminuit.Minuit(lh, pedantic=True, errordef=0.5, **params)
			return self._null_minuit
			
	def asy_minuit(self):
		if hasattr(self, "_asy_minuit"):
			return self._asy_minuit
		else:
			if self._poi.name in self.null_hypothesis.poinames:
				hypo = self.null_hypothesis
			elif self._poi.name in self.alt_hypothesis.poinames:
				hypo = self.alt_hypothesis
				
			asy_likelihood = hypo.model.nll_function(self.asymov_dataset()[0], 
											          weights=self.asymov_dataset()[1])
			self._asy_likelihood = asy_likelihood 
			
			params = {}
			
			for v in hypo.model.variables:
				pars = v.tominuit()
				params.update(pars)
				
			self._asy_minuit = iminuit.Minuit(asy_likelihood, pedantic=False, errordef=0.5, 
											  **params)
			return self._asy_minuit
	
	@property			
	def bestfitpoi(self):
		if hasattr(self, "_best_fit_poi"):
			return self._best_fit_poi	
		else:
			print("Get fit best value for parameter interest!")
			
			self.null_minuit().migrad()
			values = self.null_minuit().values
			self._best_fit_poi = values[self._poi.name]
			
			return self._best_fit_poi
			
	@bestfitpoi.setter
	def bestfitpoi(self, value):
		self._best_fit_poi = value
			
	def asymov_dataset(self):
		
		if hasattr(self, "_asymov_dataset"):
			return self._asymov_dataset	
		else:
			alt_LH = self.alt_hypothesis.model.nll_function(self.data, weights=None)
			params = {}
			
			for v in self.alt_hypothesis.model.variables:
				pars = v.tominuit()
				params.update(pars)
				if v.name == self._poi.name:
					params["fix_{0}".format(self._poi.name)] = True
					poiv = self._poi_alt_val
					params["{0}".format(self._poi.name)] = poiv

			minuit_alt =  iminuit.Minuit(alt_LH, pedantic=False, errordef=0.5, **params)
			print("Get fit best values for nuisance parameters for alternative hypothesis!")
			minuit_alt.migrad()
			
			pdf_alt = self.alt_hypothesis.model.pdf
			bounds = self.alt_hypothesis.model.obs[0].range
			
			self._asymov_dataset = generate_asymov_dataset(pdf_alt, minuit_alt.values, bounds)
			return self._asymov_dataset	
			
	def null_nll(self, poi_val):
		
		if not poi_val in self._null_nll.keys():
			self._null_nll[poi_val] = compute_NLL(self.null_minuit(), self._poi.name, poi_val)
			
		return self._null_nll[poi_val]
		
	def asymov_nll(self, poi_val):
		
		if not poi_val in self._asy_nll.keys():
			self._asy_nll[poi_val] = compute_NLL(self.asy_minuit(), self._poi.name, poi_val)
				
		return self._asy_nll[poi_val]
		
	def alt_nll(self, poi_value):
		return self.asymov_nll(poi_value)
			
	def _scan_nll(self):
		
		poi_values = self._poi_null_val
		poi_alt    = self._poi_alt_val
		
		if not hasattr(poi_values, "__iter__") and isinstance(poi_values, (int,float)):
			_shape = 1
		else:
			_shape = len(poi_values)
		
		p_values = {
					"clsb":   np.zeros(_shape),
					"clb":    np.zeros(_shape),
					"exp":    np.zeros(_shape),
					"exp_p1": np.zeros(_shape),
					"exp_p2": np.zeros(_shape),
					"exp_m1": np.zeros(_shape),
					"exp_m2": np.zeros(_shape)
					}
					
		if self.qtilde:
			nll_0_null = self.null_nll(0)
			
		if not self.onesideddiscovery:
			bestpoi = self.bestfitpoi
			nll_poiv_null = self.null_nll(bestpoi)
		else:
			nll_poiv_null  = self.null_nll(poi_alt)

		nll_poiv_alt   = self.alt_nll(poi_alt)

		nll_0_alt = self.alt_nll(0)
		
		for i, pv in np.ndenumerate(poi_values):

			nll_pv_null = self.null_nll(pv)
			nll_pv_alt = self.alt_nll(pv)	
			
			if self.onesided and poi_alt > pv:
				qnull = 0
			elif self.onesideddiscovery and poi_alt < pv:
				qnull = 0
			elif poi_alt < 0 and self.qtilde:
				qnull = 2*(nll_pv_null - nll_0_null)
			else:
				qnull = 2*(nll_pv_null - nll_poiv_null)
				
			qalt   = 2*(nll_pv_alt - nll_poiv_alt)	
			
			if qalt < 0:
				qalt = 0.0000001
				
			pnull, palt = Pvalues(qnull, qalt, self.qtilde, self.onesided, self.onesideddiscovery)
			
			p_values["clsb"][i] = pnull
			p_values["clb"][i]  = palt
			
			doublesided = not self.onesided and not self.onesideddiscovery
			
			if self.onesided or self.onesideddiscovery:
				p_values["exp"][i] = Expected_Pvalue( qalt, 0, self.CLs)  
				p_values["exp_p1"][i] = Expected_Pvalue( qalt, 1, self.CLs) 
				p_values["exp_p2"][i] = Expected_Pvalue( qalt, 2, self.CLs) 
				p_values["exp_m1"][i] = Expected_Pvalue( qalt, -1,self.CLs) 
				p_values["exp_m2"][i] = Expected_Pvalue( qalt, -2, self.CLs) 
			else:
				pvalues_2sided = Expected_Pvalues_2sided(pnull, palt)
				p_values["exp"][i] = pvalues_2sided[0] 
				p_values["exp_p1"][i] = pvalues_2sided[1] 
				p_values["exp_p2"][i] = pvalues_2sided[2]
				p_values["exp_m1"][i] = pvalues_2sided[3]
				p_values["exp_m2"][i] = pvalues_2sided[4]
				
		p_values["cls"] = p_values["clsb"] / p_values["clb"]
					
		return p_values
			
	def pvalues(self):
		if hasattr(self, "_p_values"):
			return self._p_values
		else:
			self._p_values = self._scan_nll()
			return self._p_values
			
	def upperlimit(self, alpha = 0.05, printlevel = 1):
		
		poi_name = self._poi.name
		p_values = self.pvalues()
		poi_values = self._poi_null_val
		poi_alt    = self._poi_alt_val
		
		bestpoi = self.bestfitpoi
		
		if self.CLs:
			p_ = p_values["cls"] 
		else:
			p_ = p_values["clsb"]
				
		if not (self.onesided or self.onesideddiscovery):
			pois1 = interp1d(p_, poi_values, kind='cubic')
			poi_values_ = poi_values[poi_values > pois1(max(p_))]
			p_ = p_[poi_values > pois1(max(p_))]
			pois2 = interp1d(p_, poi_values_, kind='cubic')
			poi_ul = float(pois2(alpha))
		else:
			pois = interp1d(p_, poi_values, kind='cubic')
			poi_ul = float(pois(alpha))
						
		nll_0_alt = compute_NLL(self._asy_minuit, poi_name, poi_alt)
		nll_ul_alt = compute_NLL(self._asy_minuit, poi_name, poi_ul)		
		qalt   = 2*(nll_ul_alt - nll_0_alt)

		sigma = math.sqrt( (poi_ul - poi_alt) **2 / qalt )
		
		bands = {} 
		bands["median"]  = Expected_POI(poi_alt, sigma,  0.0, alpha, self.CLs)
		bands["band_p1"] = Expected_POI(poi_alt, sigma,  1.0, alpha, self.CLs)
		bands["band_p2"] = Expected_POI(poi_alt, sigma,  2.0, alpha, self.CLs)
		bands["band_m1"] = Expected_POI(poi_alt, sigma, -1.0, alpha, self.CLs)
		bands["band_m2"] = Expected_POI(poi_alt, sigma, -2.0, alpha, self.CLs)
		
		if printlevel > 0:
		
			print("Observed upper limit: {0} = {1}".format(poi_name, poi_ul))
			print("Expected upper limit: {0} = {1}".format(poi_name, bands["median"]))
			print("Expected upper limit +1 sigma: {0} = {1}".format(poi_name, bands["band_p1"]))
			print("Expected upper limit -1 sigma: {0} = {1}".format(poi_name, bands["band_m1"]))
			print("Expected upper limit +2 sigma: {0} = {1}".format(poi_name, bands["band_p2"]))
			print("Expected upper limit -2 sigma: {0} = {1}".format(poi_name, bands["band_m2"]))
		
		bands["observed"] = poi_ul
		
		return bands
		
	def result(self, alpha = 0.05, printlevel = 1):
		
		poi_alt = self._poi_alt_val
		
		nll_0_null = self.null_nll(0)
		nll_0_alt  = self.alt_nll(0)
					
		if not self.onesideddiscovery:
			bestpoi = self.bestfitpoi
			nll_poiv_null = self.null_nll(bestpoi)
		else:
			nll_poiv_null  = self.null_nll(poi_alt)

		nll_poiv_alt   = self.alt_nll(poi_alt)
		
		qnull  = 2*(nll_0_null - nll_poiv_null)
		qalt   = 2*(nll_0_alt - nll_poiv_alt)
		
		pnull, palt = Pvalues(qnull, qalt, self.qtilde, self.onesided, self.onesideddiscovery)
		
		clsb = palt
		clb  = pnull
		cls  = clsb / clb
		if self.onesided or self.onesided:
			Z = norm.ppf(1. - pnull)
		else:
			Z = norm.ppf(1. - pnull/2.)
			
		if printlevel > 0:
			
			print("p_value for the Null hypothesis = {0}".format(pnull))
			print("Significance = {0}".format(Z))
			print("CL_b = {0}".format(clb))
			print("CL_s+b = {0}".format(clsb))
			print("CL_s = {0}".format(cls))
				
	def plot(self, alpha = 0.05, ax = None, show = True, **kwargs):
		
		p_values = self.pvalues()
		poi_values = self._poi_null_val
		poi_alt    = self._poi_alt_val
		
		if ax == None:
			fig, ax = plt.subplots(figsize=(10,8))
			
		if self.CLs:
			cls_clr  = "r"
			clsb_clr = "b"
		else:
			cls_clr  = "b"
			clsb_clr = "r"
			
			
		_ = ax.plot(poi_values, p_values["cls"], label = "Observed CL$_{s}$", marker = ".", color='k', 
		            markerfacecolor = cls_clr, markeredgecolor = cls_clr, linewidth = 2.0, ms = 11)
			
		_ = ax.plot(poi_values, p_values["clsb"], label = "Observed CL$_{s+b}$", marker = ".", color='k', 
		            markerfacecolor = clsb_clr, markeredgecolor = clsb_clr, linewidth = 2.0, ms = 11, linestyle=":")
			
		_ = ax.plot(poi_values, p_values["clb"], label = "Observed CL$_{b}$", marker = ".", color='k', 
		            markerfacecolor = "k", markeredgecolor = "k", linewidth = 2.0, ms = 11)
		
		_ = ax.plot(poi_values, p_values["exp"], label = "Expected CL$_{s}-$Median", color='k', linestyle="--", 
		            linewidth = 1.5, ms = 10)
		
		_ = ax.plot([poi_values[0], poi_values[-1]], [alpha, alpha], color='r', linestyle='-', linewidth=1.5)
		
		_ = ax.fill_between(poi_values, p_values["exp"], p_values["exp_p1"], facecolor = "lime", 
		                    label = "Expected CL$_{s} \pm 1 \sigma$")
		
		_ = ax.fill_between(poi_values, p_values["exp"], p_values["exp_m1"], facecolor = "lime")
		
		_ = ax.fill_between(poi_values, p_values["exp_p1"], p_values["exp_p2"], facecolor = "yellow", 
		                    label = "Expected CL$_{s} \pm 2 \sigma$")
		
		_ = ax.fill_between(poi_values, p_values["exp_m1"], p_values["exp_m2"], facecolor = "yellow")
		
		if self.CLs:
			ax.set_ylim(-0.01,1.1)
		else:
			ax.set_ylim(-0.01,0.55)
		ax.set_ylabel("p-value")
		ax.set_xlabel(self._poi.name)
		ax.legend(loc="best", fontsize = 14)
		
		if show:
			plt.show()
			
					
#################################################################################################
				
def generate_asymov_dataset(pdf, params_values, bounds, nbins=100):
	
	def bin_expectation_value(bin_low, bin_high):

		params = list(iminuit.describe(pdf))[1:]
		args = []
		for p in params:
			args.append(params_values[p])
		args = tuple(args)

		ret = integrate1d(pdf, (bin_low, bin_high), 100, *args)
		
		return ret
		
	bins_edges = np.linspace(bounds[0], bounds[1], nbins + 1)
	data_asy   = np.zeros(nbins)
	weight_asy = np.zeros(nbins)
	
	for nb in range(nbins):
		
		low_bin = bins_edges[nb]
		high_bin = bins_edges[nb+1]
		bin_center = low_bin + (high_bin - low_bin)/2
		
		exp_val = bin_expectation_value(low_bin, high_bin)
								
		data_asy[nb]   = bin_center
		weight_asy[nb] = exp_val
		
	return data_asy, weight_asy
	
def compute_NLL( minuit, poi, val, npoints=1 ):
	
	range=(val,-1.)
	
	nll_curve = minuit.mnprofile(poi, npoints, range)	
	
	return nll_curve[1]
	
def Pvalues( qnull, qalt, qtilde=False, onesided=True, onesideddiscovery=False):
	
	pnull = -1.
	palt  = -1.	
	
	if not qtilde:
		if onesided or onesideddiscovery:
			pnull = 1. - norm.cdf(math.sqrt(qnull))
			palt  = 1. - norm.cdf(math.sqrt(qnull) - math.sqrt(qalt))
		else:
			pnull = (1. - norm.cdf(math.sqrt(qnull)))*2.
			palt  =	1. - norm.cdf(math.sqrt(qnull) + math.sqrt(qalt))
			palt += 1. - norm.cdf(math.sqrt(qnull) - math.sqrt(qalt))		
	else:		
		if onesided :
			if qnull > qalt and qalt > 0.:
				pnull = 1. - norm.cdf( ( qnull + qalt ) / ( 2. * math.sqrt(qalt) ) )
				palt  = 1. - norm.cdf( ( qnull - qalt ) / ( 2. * math.sqrt(qalt) ) )
			elif qnull <= qalt and qalt > 0.:
				pnull = 1. - norm.cdf(math.sqrt(qnull))
				palt  = 1. - norm.cdf(math.sqrt(qnull) - math.sqrt(qalt))
			
						
	return pnull, palt	
	
def Expected_Pvalue(qalt, nsigma, CLs = True):
	
	p_clsb = 1 - norm.cdf(math.sqrt(qalt) - nsigma )
	
	if CLs:
		p_clb = norm.cdf(nsigma)
		p_cls = p_clsb / p_clb
		return max(p_cls, 0.)
	else:
		return max(p_clsb, 0.)
		
def Expected_Pvalues_2sided(pnull, palt):
	
	sqrtqnull = norm.ppf(1 - pnull/2)

	def paltfunct( offset, pval, icase):
		def func(x):
			ret   = 1. - norm.cdf(x + offset)
			ret  += 1. - norm.cdf(icase*(x - offset))
			ret  -= pval
			return ret
		return func
			
	f = paltfunct( sqrtqnull, palt, -1.)
	sqrtqalt = brentq(f, 0, 20)
	
	fmed = paltfunct( sqrtqalt, norm.cdf(0), 1.)
	sqrtqalt_med = brentq(fmed, 0, 20)
	p_med = 2.*(1-norm.cdf(sqrtqalt_med))
	
	fp1 = paltfunct( sqrtqalt, norm.cdf(1), 1.)
	sqrtqalt_p1 = brentq(fp1, 0, 20)
	p_p1 = 2.*(1-norm.cdf(sqrtqalt_p1))
	
	fp2 = paltfunct( sqrtqalt, norm.cdf(2), 1.)
	sqrtqalt_p2 = brentq(fp2, 0, 20)
	p_p2 = 2.*(1-norm.cdf(sqrtqalt_p2))
	
	fm1 = paltfunct( sqrtqalt, norm.cdf(-1), 1.)
	sqrtqalt_m1 = brentq(fm1, 0, 20)
	p_m1 = 2.*(1-norm.cdf(sqrtqalt_m1))
	
	fm2 = paltfunct( sqrtqalt, norm.cdf(-2), 1.)
	sqrtqalt_m2 = brentq(fm2, 0, 20)
	p_m2 = 2.*(1-norm.cdf(sqrtqalt_m2))

	return p_med, p_p1, p_p2, p_m1, p_m2
	
def Expected_POI(poi_alt, sigma, n = 0.0, alpha = 0.05, CLs = False):
		
	if CLs:
		ret = poi_alt + sigma * (norm.ppf(1 - alpha*norm.cdf(n)) + n)
	else:
		ret = poi_alt + sigma * (norm.ppf(1 - alpha) + n)
		
	return ret