#!/usr/bin/python
import numpy as np


class Calculator(object):

    def __init__(self, null_hypothesis, alt_hypothesis, data):
        """ __init__ function """

        msg = "Invalid type, {0}, for null hypothesis. Hypothesis required"

        if not isHypothesis(null_hypothesis):
            msg = msg.format(null_hypothesis.__class__.__name__)
            raise TypeError(msg)

        if not isHypothesis(alt_hypothesis):
            msg = msg.format(alt_hypothesis.__class__.__name__)
            raise TypeError(msg)

        if not hasattr(data, "__iter__"):
            msg = "{0} not a valid type for data.".format(data)
            raise TypeError(msg)

        pois_in_null = haspois(alt_hypothesis)
        pois_in_alt = haspois(alt_hypothesis)

        if not(pois_in_null or pois_in_alt):
            print(null_hypothesis.summary())
            print(alt_hypothesis.summary())
            msg = "At least one parameter of interest is required in one of \
                  the hypothesis."
            raise ValueError(msg)

        self._null_hypothesis = null_hypothesis
        self._alt_hypothesis = alt_hypothesis

        self._data = data

    @property
    def null_hypothesis(self):
        return self._null_hypothesis

    @property
    def alt_hypothesis(self):
        return self._alt_hypothesis

    @property
    def data(self):
        return self._data


def isHypothesis(hypo):
    if hypo.__class__.__name__ == "Hypothesis":
        return True
    else:
        return False


def hasobs(hypo):
    return len(hypo.model.obs) > 0


def haspois(hypo):
    return len(hypo.pois) > 0


def hasnuis(hypo):
    return len(hypo.nuis) > 0
