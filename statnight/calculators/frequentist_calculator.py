# -*- coding: utf-8 -*-
# !/usr/bin/python
from .calculator import Calculator, qdist
from ..parameters import POI
import numpy as np
from scipy.stats import norm
from scipy.interpolate import InterpolatedUnivariateSpline


class FrequentistCalculator(Calculator):
    """
    Class for for frequentist calculators.
    """

    def __init__(self, config, ntoysnull=1000, ntoysalt=1000):
        """
        __init__ function
        """

        super(FrequentistCalculator, self).__init__(config)

        self._toysresults = {}
        self._minimizers = {}
        self.ntoysnull = ntoysnull
        self.ntoysalt = ntoysalt

    def dotoys(self, poigen, ntoys, poieval, printfreq=0.2):

        config = self.config
        models = config.models
        minimizer = config.minimizer.copy()
        weights = config.weights
        minimizer.verbosity = 0
        g_param = poigen.parameter
        g_value = poigen.value

        result = {"bestfit": {"values": np.empty(ntoys),
                              "nll": np.empty(ntoys)}}
        result["nll"] = {}
        for p in poieval:
            result["nll"][p] = np.empty(ntoys)

        printfreq = ntoys * printfreq

        samplers, toys = config.sampler(int(ntoys*1.2), g_param, g_value,
                                        models)

        loss = config.lossbuilder(models, samplers, weights)

        i = 0
        for i in range(ntoys):
            converged = False
            toprint = i % printfreq == 0
            while converged is False:
                next(toys)
                bf = minimizer.minimize(loss=loss)
                converged = bf.converged
                if not converged:
                    continue
                bf = bf.params[g_param]["value"]
                result["bestfit"]["values"][i] = bf
                result["bestfit"]["nll"][i] = config.pll(loss, g_param, bf)
                for p in poieval:
                    param_ = p.parameter
                    val_ = p.value
                    result["nll"][p][i] = config.pll(loss, param_, val_)

            if toprint:
                print("{0} toys generated, fitted and scanned!".format(i+1))

            if i > ntoys:
                break
            i += 1

        return result

    def add_toys(self, poi, toys):
        bf = toys["bestfit"]["values"]
        nllbf = toys["bestfit"]["nll"]

        nlldict = {}
        for k, v in toys["nll"]:
            poi_ = POI(poi.name, k)
            nlldict[poi_] = v

        toyresult = {"bestfit": {"values": bf, "nll": nllbf}, "nll": nlldict}
        self._toysresults[poi] = toyresult

    def dotoys_null(self, poinull):

        ntoys = self.ntoysnull

        for p in poinull:
            if p in self._toysresults.keys():
                continue
            msg = "Generating null hypothesis toys for {0}."
            print(msg.format(p))

            toeval = [p]
            if p.value != 0:
                p_ = POI(p.parameter, 0.0)
                toeval.append(p_)

            toyresult = self.dotoys(p, ntoys, toeval)

            self._toysresults[p] = toyresult

    def dotoys_alt(self, poialt, poinull):

        ntoys = self.ntoysalt

        for p in poialt:

            if p in self._toysresults.keys():
                continue
            msg = "Generating alt hypothesis toys for {0}."
            print(msg.format(p))

            toeval = [p]
            for p_ in poinull:
                toeval.append(p_)
            if 0. not in poinull.value:
                p_ = POI(poinull.parameter, 0.0)
                toeval.append(p_)

            toyresult = self.dotoys(p, ntoys, toeval)

            self._toysresults[p] = toyresult

    def poi_bestfit(self, poigen, qtilde=False):
        bf = self._toysresults[poigen]["bestfit"]["values"]
        if qtilde:
            bf = np.where(bf < 0, 0, bf)
        return bf

    def nll_bestfit(self, poigen, qtilde=False):
        nll = self._toysresults[poigen]["bestfit"]["nll"]
        if qtilde:
            bf = self._toysresults[poigen]["bestfit"]["values"]
            nll_zero = self.nll(poigen, POI(poigen.parameter, 0.))
            nll = np.where(bf < 0, nll_zero, nll)
        return nll

    def nll(self, poigen, poi):
        return self._toysresults[poigen]["nll"][poi]

    def q(self, nll1, nll2):
        return 2*(nll1 - nll2)

    def qnull(self, poi, qtilde=False):
        nll1 = self.nll(poi, poi)
        nll2 = self.nll_bestfit(poi, qtilde)
        return self.q(nll1, nll2)

    def qalt(self, poi, poialt, qtilde=False):
        nll1 = self.nll(poialt, poi)
        nll2 = self.nll_bestfit(poialt, qtilde)
        return self.q(nll1, nll2)

    def pvalue_q(self, qobs, poinull, poialt=None, qtilde=False, onesided=True,
                 onesideddiscovery=False):

        def pvalue_i(qdist, qobs):
            p = len(qdist[qdist > qobs])/len(qdist)
            return p

        self.dotoys_null(poinull)

        needpalt = not(onesided and poialt is None)

        if needpalt:
            self.dotoys_alt(poialt, poinull)

        pnull = np.empty(len(poinull))
        if needpalt:
            palt = np.empty(len(poinull))
        else:
            palt = None

        for i, p in enumerate(poinull):
            qnulldist = self.qnull(p, qtilde)
            bestfitnull = self.poi_bestfit(p, qtilde)
            qnulldist = qdist(qnulldist, bestfitnull, p.value, onesided,
                              onesideddiscovery)
            pnull[i] = pvalue_i(qnulldist, qobs[i])
            if needpalt:
                qaltdist = self.qalt(p, poialt, qtilde)
                bestfitalt = self.poi_bestfit(poialt, qtilde)
                qaltdist = qdist(qaltdist, bestfitalt, p.value, onesided,
                                 onesideddiscovery)
                palt[i] = pvalue_i(qaltdist, qobs[i])

        return pnull, palt

    def pvalue(self, poinull, poialt=None, qtilde=False, onesided=True,
               onesideddiscovery=False):

        poiparam = poinull.parameter

        bf = self.config.bestfit.params[poiparam]["value"]
        if qtilde and bf < 0:
            bestfitpoi = POI(poiparam, 0)
        else:
            bestfitpoi = POI(poiparam, bf)

        qobs = self.qobs(poinull, bestfitpoi)

        qobs = qdist(qobs, bestfitpoi.value, poinull.value, onesided,
                     onesideddiscovery)

        return self.pvalue_q(qobs, poinull, poialt, qtilde, onesided,
                             onesideddiscovery)

    def expected_pvalue(self, poinull, poialt, nsigma, CLs=True):

        ps = {ns: {"p_clsb": np.empty(len(poinull)),
                   "p_clb": np.empty(len(poinull))} for ns in nsigma}

        for i, p in enumerate(poinull):

            qnulldist = self.qnull(p)
            qaltdist = self.qalt(p, poialt)

            p_clsb_i = np.empty(qnulldist.shape)
            p_clb_i = np.empty(qaltdist.shape)

            lqnulldist = len(qnulldist)
            lqaltdist = len(qaltdist)

            for j, q in np.ndenumerate(qaltdist):

                if j[0] < lqnulldist:
                    p_clsb_i[j] = (len(qnulldist[qnulldist >= q])/lqnulldist)
                p_clb_i[j] = (len(qaltdist[qaltdist >= q])/lqaltdist)

            for ns in nsigma:
                frac = norm.cdf(ns)*100
                ps[ns]["p_clsb"][i] = np.percentile(p_clsb_i, frac)
                ps[ns]["p_clb"][i] = np.percentile(p_clb_i, frac)

        ret = []
        for ns in nsigma:
            if CLs:
                p_cls = ps[ns]["p_clsb"] / ps[ns]["p_clb"]
                ret.append(np.where(p_cls < 0, 0, p_cls))
            else:
                p_clsb = ps[ns]["p_clsb"]
                ret.append(np.where(p_clsb < 0, 0, p_clsb))

        return ret

    def expected_poi(self, poinull, poialt, nsigma, alpha=0.05, qtilde=False,
                     onesided=True, onesideddiscovery=False):

        qt = qtilde
        os = onesided
        osd = onesideddiscovery

        bf = self.poi_bestfit(poialt, qtilde)
        nll_bf_alt = self.nll_bestfit(poialt, qtilde)

        q = {p: self.q(self.nll(poialt, p), nll_bf_alt) for p in poinull}
        q = {p: qdist(q[p], bf, p.value, True, False) for p in poinull}

        def getqi(i):
            qi = np.empty(len(poinull))
            for j, p in enumerate(poinull):
                qi[j] = q[p][i]
            return qi

        values = []

        for i in range(len(bf)):
            qi = getqi(i)
            pvalues, _ = self.pvalue_q(qi, poinull, poialt, qt, os, osd)
            pvalues = pvalues - alpha

            s = InterpolatedUnivariateSpline(poinull.value, pvalues)
            val = s.roots()

            if len(val) > 0:
                values.append(val[0])

        values = np.array(values)

        ret = []
        for ns in nsigma:
            frac = norm.cdf(ns)*100
            ret.append(np.percentile(values, frac))

        return ret


def gentoys(models, ntoys, nsamples=None, **kwargs):
    toys = []
    for n in range(ntoys):
        toy = []
        for i in range(len(models)):
            m = models[i]
            n = nsamples[i]
            toy.append(m.sample(n, **kwargs))
        toys.append(toy)
    return toys
