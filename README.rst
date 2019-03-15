lauztat
^^^^^^^

.. image:: https://travis-ci.org/marinang/lauztat.svg?branch=master
    :target: https://travis-ci.org/marinang/lauztat

.. image:: https://dev.azure.com/matthieumarinangeli/matthieumarinangeli/_apis/build/status/marinang.lauztat?branchName=master
    :alt: Build Status
    :target: https://dev.azure.com/matthieumarinangeli/matthieumarinangeli/_build?definitionId=1

.. image:: https://img.shields.io/azure-devops/tests/matthieumarinangeli/matthieumarinangeli/1.svg?compact_message
    :alt: Test Status
    :target: https://dev.azure.com/matthieumarinangeli/matthieumarinangeli/_build?definitionId=1

.. image:: https://img.shields.io/coveralls/github/marinang/lauztat.svg
    :alt: Coveralls github
    :target: https://coveralls.io/github/marinang/lauztat?branch=master

.. image:: https://api.codacy.com/project/badge/Grade/f78242fbdbd34ef8a21a9f9055b6c898
    :alt: Codacy Badge
    :target: https://app.codacy.com/app/marinang/lauztat?utm_source=github.com&utm_medium=referral&utm_content=marinang/lauztat&utm_campaign=Badge_Grade_Dashboard

.. image:: https://mybinder.org/badge_logo.svg
    :target: https://mybinder.org/v2/gh/marinang/lauztat/master?filepath=examples%2Fnotebooks%2F

.. image:: https://img.shields.io/pypi/v/lauztat.svg
    :alt: PyPI
    :target: https://pypi.org/project/lauztat/

.. image:: https://img.shields.io/pypi/pyversions/lauztat.svg
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/lauztat/

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.2593789.svg
    :target: https://doi.org/10.5281/zenodo.2593789



Pure python statistics tools for high energy physics using `zfit <https://github.com/zfit/zfit>`__ as
a backend for maximum likelihood fits.

Tests for discovery, upper limits and confidence intervals are provided based on likelihood ratios
in a frequentist approach (using pseudo-experiments) or using asymptotic formulae from
"Asymptotic formulae for likelihood-based tests of new physics" `[arxiv:1007.1727] <https://arxiv.org/abs/1007.1727>`__.

lauztat has been developed at EPFL, Lausanne Switzerland (laus' or lauz is how the cool kids call Lausanne).

Installation
------------

Install ``lauztat`` like any other Python package:

.. code-block:: bash

    pip install lauztat                       # maybe with sudo or --user, or in virtualenv

Dependencies
------------

- `Numpy <https://scipy.org/install.html>`__
- `zfit <https://github.com/zfit/zfit>`__
- `matplotlib <https://matplotlib.org/users/installing.html>`__ (optionnal)

Getting started
---------------

Usual HEP results can be recast in terms of hypothesis testing where you have to
choose a null H\ :sub:`0` and an alternative H\ :sub:`1` hypothesis, H\ :sub:`0`
being the one you want to disprove.
To do a test you will need your data (and weights), a model, a loss function builder
and a minimizer as input to a calculator (*FrequentistCalculator* or *AsymptoticCalculator*).

Discovery:
==========

if you do a measurement to find signals S in a dataset and you find an excess this
test answers "is the data compatible with the background only ?" with:

- H\ :sub:`0`: background only (S = 0)
- H\ :sub:`1`: presence of a signal (S ≠ 0)

The test return a p-value or a significance Z. If Z ≥ 3 there is an evidence
and if Z ≥ 5 a discovery of a signal.

example:
########

Search for a gaussian peak over an exponential background. The parameter of interest
is the signal yield N\ :sub:`sig`. 19 ± 7 signals events are found.

.. image:: https://github.com/marinang/lauztat/blob/master/docs/fit_discovery_ex.png
    :alt: fit_discovery_ex

.. code-block:: python

  >>> from lauztat.parameters import POI
  >>> from lauztat.hypotests import Discovery
  >>> from lauztat.calculators import AsymptoticCalculator
  >>> from lauztat.config import Config

  >>> import zfit
  >>> from zfit import ztf
  >>> from zfit.core.loss import ExtendedUnbinnedNLL, UnbinnedNLL
  >>> from zfit.minimizers.minimizer_minuit import MinuitMinimizer

  >>> def lossbuilder(model, data, weights=None):
  >>>     loss = ExtendedUnbinnedNLL(model=model, data=data, fit_range=[obs])
  >>>     return loss

  >>> config = Config(tot_model, data_, lossbuilder, MinuitMinimizer())

  >>> calc = AsymptoticCalculator(config)

  >>> poinull = POI(Nsig, value=0)
  >>> discovery_test = Discovery(poinull, calc)

  >>> discovery_test.result()

  p_value for the Null hypothesis = 0.0007571045219983974
  Significance = 3.171946490372666

Upper limit:
============

if you find a small signal excess in a dataset, but not enough to claim
an evidence or a discovery, you can exclude large signal yields S:

- H\ :sub:`0`: background + some signal (S = S\ :sub:`0`)
- H\ :sub:`1`: S < S\ :sub:`0`

S\ :sub:`0` is adjusted to a predefined p-value, typically 5%. S\ :sub:`0` is the upper
limit on the signal yield S with 95 % confidence level
(CL = 1 - p ; p = 5 % ⟺ CL = 95%).

example:
########

Search for a gaussian peak over an exponential background. The parameter of interest
is the signal yield N\ :sub:`sig`. 5 ± 5 signals events are found. The CLs method
is applied to find the upper limit on N\ :sub:`sig`.

.. image:: https://github.com/marinang/lauztat/blob/master/docs/fit_upper_limit_ex.png
    :alt: fit_upper_limit_ex

.. code-block:: python

  >>> from lauztat.hypotests import UpperLimit
  >>> poinull = POI(Nsig, value=np.linspace(0.0, 25, 20))
  >>> poialt = POI(Nsig, value=0)
  >>> ul_test = UpperLimit(poinull, poialt, calc, CLs=True, qtilde=False)
  >>> ul_test.upperlimit()

  Observed upper limit: Nsig = 16.177011346146557
  Expected upper limit: Nsig = 11.603516889161947
  Expected upper limit +1 sigma: Nsig = 16.145671793312022
  Expected upper limit -1 sigma: Nsig = 8.359388717422624
  Expected upper limit +2 sigma: Nsig = 21.644416205737596
  Expected upper limit -2 sigma: Nsig = 6.22672400601805

.. image:: https://github.com/marinang/lauztat/blob/master/docs/brazilian_plot.png
    :alt: brazilian_plot

Confidence interval:
====================

if you do a measurement of a parameter *e* with an estimator *ê*, given an observation
ê\ :sub:`obs` what value of e are not rejected at a certain confidence level (typically 68%)?

- H\ :sub:`0`: e\ :sub:`down` < e < e\ :sub:`up`
- H\ :sub:`1`: e = ê\ :sub:`obs`

e\ :sub:`down` and e\ :sub:`up` are adjusted such the test returns a p-value of 32 %.

example:
########

Measurement of the mean of a gaussian peak found to be 1.21 ± 0.02. We compute a Feldman Cousins
confidence interval on the mean parameter at 68% CL.

.. image:: https://github.com/marinang/lauztat/blob/master/docs/fit_ci_ex.png
    :alt: fit_ci_ex

.. code-block:: python

  >>> from lauztat.calculators import FrequentistCalculator
  >>> calc = FrequentistCalculator(config, ntoysnull=2000, ntoysalt=2000)
  >>> poinull = POI(mean, value=np.linspace(1.15, 1.26, 100))
  >>> poialt = POI(mean, value=1.21)
  >>> ci_test = ConfidenceInterval(poinull, poialt, calc, qtilde=False)
  >>> ci_test.interval()
  Confidence interval on mean:
	1.1890518753693258 < mean < 1.2249924635033214 at 68% C.L.

.. image:: https://github.com/marinang/lauztat/blob/master/docs/ci_1_cl_plot.png
    :alt: ci_1_cl_plot
