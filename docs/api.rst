.. _api:

API Documentation
======================

.. _parameters:

Parameters
----------

.. currentmodule:: statnight.parameters

.. autoclass:: Observable

.. autoclass:: Variable

    .. automethod:: tominuit

.. autoclass:: Constant

    .. automethod:: tominuit

.. _model:

Model
-----

.. currentmodule:: statnight.model

.. autoclass:: Model

    .. automethod:: pdf()

    .. automethod:: parameters()

    .. automethod:: observables()

    .. automethod:: add_obs

    .. automethod:: variables()

    .. automethod:: add_vars

    .. automethod:: __getitem__

    .. automethod:: ext_pars()

    .. automethod:: add_ext_pars

    .. automethod:: extended()

    .. automethod:: create_hypothesis

.. autoclass:: Hypothesis

    .. automethod:: pois()

    .. automethod:: poinames()

    .. automethod:: poivalues()

    .. automethod:: getpoi

    .. automethod:: model()

    .. automethod:: nuis()

    .. automethod:: nuisnames()

    .. automethod:: summary

.. _Calculator:

Asymptotic calculator
---------------------

.. currentmodule:: statnight.calculators.asymptotic_calculator

.. autoclass:: AsymptoticCalculator

    .. automethod:: qtilde()

    .. automethod:: onesided()

    .. automethod:: onesideddiscovery()

    .. automethod:: CLs()

    .. automethod:: bestfitpoi()

    .. automethod:: pvalues()

    .. automethod:: result

    .. automethod:: upperlimit

    .. automethod:: plot
