# -*- coding: utf-8 -*-
# !/usr/bin/python
from .calculator import Calculator, qdist
from ..parameters import POI
import numpy as np
from scipy.stats import norm
# from scipy.interpolate import InterpolatedUnivariateSpline
import h5py
np.warnings.filterwarnings('ignore')


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

        self.sampler = {}
        self.loss_toys = {}

    def dotoys(self, poigen, ntoys, poieval, printfreq=0.2):
        config = self.config
        models = config.models
        weights = config.weights
        minimizer = config.minimizer
        g_param = poigen.parameter
        g_value = poigen.value

        try:
            sampler = self.sampler[g_param]
        except KeyError:
            sampler = self.config.sampler(floatting_params=[g_param])
            self.sampler[g_param] = sampler

        try:
            loss_toys = self.loss_toys[g_param]
        except KeyError:
            loss_toys = self.config.lossbuilder(models, sampler, weights)
            self.loss_toys[g_param] = loss_toys

        result = {"bestfit": {"values": np.empty(ntoys),
                              "nll": np.empty(ntoys)}}
        result["nll"] = {}
        for p in poieval:
            result["nll"][p] = np.empty(ntoys)

        printfreq = ntoys * printfreq

        toys = self.config.sample(sampler, int(ntoys*1.2), g_param, g_value)

        for i in range(ntoys):
            converged = False
            toprint = i % printfreq == 0
            while converged is False:
                try:
                    next(toys)
                except StopIteration:
                    to_gen = ntoys - i
                    toys = self.config.sample(sampler, int(to_gen*1.2),
                                              g_param, g_value)
                    next(toys)

                bf = minimizer.minimize(loss=loss_toys)
                converged = bf.converged

                if not converged:
                    config.deps_tobestfit()
                    continue

                bf = bf.params[g_param]["value"]
                result["bestfit"]["values"][i] = bf
                nll = config.pll(minimizer, loss_toys, g_param, bf)
                result["bestfit"]["nll"][i] = nll

                for p in poieval:
                    param_ = p.parameter
                    val_ = p.value
                    nll = config.pll(minimizer, loss_toys, param_, val_)
                    result["nll"][p][i] = nll

            if toprint:
                print("{0} toys generated, fitted and scanned!".format(i))

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

    def toys_to_hdf5(self, filename):
        f = h5py.File(filename, "w")

        for k, v in self._toysresults.items():
            # k = POI("name", poivalue)
            poigenv = str(k.value)
            f.create_group(poigenv)
            for j, l in v.items():
                # j in ['bestfit', 'nll']
                f[poigenv].create_group(j)
                for o, p in l.items():
                    # if j = 'bestfit' , o in ['values', 'nll']
                    # if j = 'nll', o = poival
                    if not isinstance(o, str):
                        o = str(o.value)
                    f[poigenv][j].create_dataset(o, data=p)

        print("Toys successfully saved to '{0}' !".format(filename))

    def readtoys_from_hdf5(self, parameter, filename):
        toys = {}
        f = h5py.File(filename, "r")

        for k, v in f.items():
            # k = poigen
            if isinstance(k, str):
                k = float(k)
            k_ = {}
            toys[POI(parameter, float(k))] = k_
            for j, l in v.items():
                # j in ['bestfit', 'nll']
                j_ = {}
                k_[j] = j_
                for o, p in l.items():
                    if isinstance(o, str) and j == "nll":
                        o = POI(parameter, float(o))
                    j_[o] = np.asarray(p)
                    # if j = 'bestfit' , o in ['values', 'nll']
                    # if j = 'nll', o = poival

        f.close()
        self._toysresults = toys
        print("Toys successfully read from '{0}' !".format(filename))

    def dotoys_null(self, poinull, poialt, qtilde=False):

        ntoys = self.ntoysnull

        for p in poinull:
            if p in self._toysresults.keys():
                continue
            msg = "Generating null hypothesis toys for {0}."
            print(msg.format(p))

            toeval = [p]
            if poialt is not None:
                for palt in poialt:
                    toeval.append(palt)
            if qtilde:
                poi0 = POI(poinull.parameter, 0.)
                if poi0 not in toeval:
                    toeval.append(poi0)

            toyresult = self.dotoys(p, ntoys, toeval)

            self._toysresults[p] = toyresult

    def dotoys_alt(self, poialt, poinull, qtilde=False):

        ntoys = self.ntoysalt

        for p in poialt:

            if p in self._toysresults.keys():
                continue
            msg = "Generating alt hypothesis toys for {0}."
            print(msg.format(p))

            toeval = [p]
            if poinull is not None:
                for p_ in poinull:
                    toeval.append(p_)
            if qtilde:
                poi0 = POI(poinull.parameter, 0.)
                if poi0 not in toeval:
                    toeval.append(poi0)

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
            qdist = qdist[~(np.isnan(qdist) | np.isinf(qdist))]
            p = len(qdist[qdist >= qobs])/len(qdist)
            return p

        self.dotoys_null(poinull, poialt, qtilde)

        needpalt = not(onesided and poialt is None)

        if needpalt:
            self.dotoys_alt(poialt, poinull, qtilde)

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

    def expected_pvalue(self, poinull, poialt, nsigma, CLs=True, qtilde=False,
                        onesided=True, onesideddiscovery=False):

        ps = {ns: {"p_clsb": np.empty(len(poinull)),
                   "p_clb": np.empty(len(poinull))} for ns in nsigma}

        for i, p in enumerate(poinull):

            qnulldist = self.qnull(p)
            bestfitnull = self.poi_bestfit(p, qtilde)
            qnulldist = qdist(qnulldist, bestfitnull, p.value, onesided,
                              onesideddiscovery)
            qnulldist = qnulldist[~(np.isnan(qnulldist) | np.isinf(qnulldist))]

            qaltdist = self.qalt(p, poialt)
            bestfitalt = self.poi_bestfit(poialt, qtilde)
            qaltdist = qdist(qaltdist, bestfitalt, p.value, onesided,
                             onesideddiscovery)
            qaltdist = qaltdist[~(np.isnan(qaltdist) | np.isinf(qaltdist))]

            p_clsb_i = np.empty(qnulldist.shape)
            p_clb_i = np.empty(qaltdist.shape)

            lqnulldist = len(qnulldist)
            lqaltdist = len(qaltdist)

            for j, q in np.ndenumerate(qaltdist):
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

    # def expected_poi(self, poinull, poialt, nsigma, alpha=0.05, CLs=True,
    #                  qtilde=False, onesided=True, onesideddiscovery=False):
    #
    #     qt = qtilde
    #     os = onesided
    #     osd = onesideddiscovery
    #
    #     bf = self.poi_bestfit(poialt, qtilde)
    #     nll_bf_alt = self.nll_bestfit(poialt, qtilde)
    #
    #     q = {}
    #     for p in poinull:
    #         q_ = self.q(self.nll(poialt, p), nll_bf_alt)
    #         sel = ~(np.isnan(q_) | np.isinf(q_))
    #         q_ = q_[sel]
    #         bf_ = bf[sel]
    #         q_ = qdist(q_, bf_, p.value, True, False)
    #         q[p] = q_
    #
    #     # q = {p: self.q(self.nll(poialt, p), nll_bf_alt) for p in poinull}
    #     # q = {p: qdist(q[p], bf, p.value, True, False) for p in poinull}
    #     # q = {p: q[p][] for p in poinull}
    #     # z[~(np.isnan(z) | np.isinf(z))]
    #
    #     def getqi(i):
    #         qi = np.empty(len(poinull))
    #         for j, p in enumerate(poinull):
    #             qi[j] = q[p][i]
    #         return qi
    #
    #     values = []
    #
    #     for i in range(len(bf)):
    #         qi = getqi(i)
    #         pnull, palt = self.pvalue_q(qi, poinull, poialt, qt, os, osd)
    #
    #         if CLs:
    #             pvalues = pnull / palt
    #         else:
    #             pvalues = pnull
    #
    #         pvalues = pvalues - alpha
    #
    #         s = InterpolatedUnivariateSpline(poinull.value, pvalues)
    #         val = s.roots()
    #
    #         if len(val) > 0:
    #             values.append(val[0])
    #
    #     values = np.array(values)
    #
    #     ret = []
    #     for ns in nsigma:
    #         frac = norm.cdf(ns)*100
    #         ret.append(np.percentile(values, frac))
    #
    #     return ret


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
