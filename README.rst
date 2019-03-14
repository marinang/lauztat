lauztat
^^^^^^^

.. image:: https://travis-ci.org/marinang/lauztat.svg?branch=master
    :target: https://travis-ci.org/marinang/lauztat

.. image:: https://dev.azure.com/matthieumarinangeli/matthieumarinangeli/_apis/build/status/marinang.lauztat?branchName=master
    :alt: Build Status
    :target: https://dev.azure.com/matthieumarinangeli/matthieumarinangeli/_build?definitionId=1

.. image:: https://img.shields.io/pypi/pyversions/lauztat.svg
    :alt: PyPI - Python Version

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

Pure python statistics tools for high energy physics using `zfit <https://github.com/zfit/zfit>`__ as
a backend for maximum likelihood fits.

Tests for discovery, upper limits and confidence intervals are provided based on likelihood ratios
in a frequentist approach (using pseudo-experiments) or using asymptotic formulae from
"Asymptotic formulae for likelihood-based tests of new physics" `[arxiv:1007.1727] <https://arxiv.org/abs/1007.1727>`__.

lauztat has been developed at EPFL in Lausanne Switzerland (laus' or lauz is how the cool kids call Lausanne).



dependencies:
=============

- `Numpy <https://scipy.org/install.html>`__
- `zfit <https://github.com/zfit/zfit>`__
- `matplotlib <https://matplotlib.org/users/installing.html>`__ (optionnal)
