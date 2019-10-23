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

The project is currently being ported and slighty redesigned to `scikit-hep/scikit-stats <https://github.com/scikit-hep/scikit-stats>`__ package.

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

if you do a measurement to find signals S in a dataset and you find an excess, this
test answers "is the data compatible with the background only ?" with:

- H\ :sub:`0`: background only (S = 0)
- H\ :sub:`1`: presence of a signal (S ≠ 0)

The test return a p-value or a significance Z. If Z ≥ 3 there is an evidence
and if Z ≥ 5 a discovery of a signal.

Examples of significance computations for a gaussian peak over an exponential background are
provided for the `asymptotic calculator <https://github.com/marinang/lauztat/blob/master/examples/notebooks/discovery_zfit_asy.ipynb>`__
and the `frequentist calculator <https://github.com/marinang/lauztat/blob/master/examples/notebooks/discovery_zfit_freq.ipynb>`__
and can be ran in `mybinder <https://mybinder.org/v2/gh/marinang/lauztat/master?filepath=examples%2Fnotebooks%2F>`__.

Upper limit:
============

if you find a small signal excess in a dataset, but not enough to claim
an evidence or a discovery, you can exclude large signal yields S:

- H\ :sub:`0`: background + some signal (S = S\ :sub:`0`)
- H\ :sub:`1`: S < S\ :sub:`0`

S\ :sub:`0` is adjusted to a predefined p-value, typically 5%. S\ :sub:`0` is the upper
limit on the signal yield S with 95 % confidence level
(CL = 1 - p ; p = 5 % ⟺ CL = 95%).

Examples of `CLs <https://iopscience.iop.org/article/10.1088/0954-3899/28/10/313/meta>`__ upper limits on the signal yield
for a gaussian peak over an exponential background are
provided for the `asymptotic calculator <https://github.com/marinang/lauztat/blob/master/examples/notebooks/upper_limit_zfit_asy.ipynb>`__
and the `frequentist calculator <https://github.com/marinang/lauztat/blob/master/examples/notebooks/upper_limit_zfit_freq.ipynb>`__
and can be ran in `mybinder <https://mybinder.org/v2/gh/marinang/lauztat/master?filepath=examples%2Fnotebooks%2F>`__.

Confidence interval:
====================

if you do a measurement of a parameter α with an estimator ᾰ, given an observation
ᾰ\ :sub:`obs` what value of α are not rejected at a certain confidence level (typically 68%)?

- H\ :sub:`0`: α ≤ α \ :sub:`down` or α ≥ α\ :sub:`up`
- H\ :sub:`1`: α\ :sub:`down` < α < α\ :sub:`up`

α\ :sub:`down` and α\ :sub:`up` are adjusted such the test returns a p-value of 32%.

Examples of confidence intervals on the mean of a gaussian peak are
provided for the `asymptotic calculator <https://github.com/marinang/lauztat/blob/master/examples/notebooks/confidence_interval_zfit_asy.ipynb>`__
and the `frequentist calculator <https://github.com/marinang/lauztat/blob/master/examples/notebooks/confidence_interval_zfit_freq.ipynb>`__
(Feldman and Cousins confidence interval `[arxiv:9711021] <https://arxiv.org/abs/physics/9711021>`__)
and can be ran in `mybinder <https://mybinder.org/v2/gh/marinang/lauztat/master?filepath=examples%2Fnotebooks%2F>`__.
