#!/usr/bin/python

"""
Parameter classes
"""

from iminuit import describe
import attr
from attr import attrs, attrib
from .utils.pdf import gaussian


def check_range(instance=None, range=None, value=None):
    """
    Validator for range attribute in Range class.
    """
    has2elements = len(value) == 2
    allnumbers = all(isinstance(v, (float, int)) for v in value)
    if not (has2elements and allnumbers):
        raise TypeError("Please provide a tuple/list with lower and upper \
        limits for the range parameter.")
    if value[0] >= value[1]:
        raise ValueError("Lower limit of the range should be strictly lower \
        the the upper limit.")


def check_initvalue(instance=None, initvalue=None, value=None):
    """
    Validator for initvalue attribute in Variable class.
    """
    if value != -1:
        _range = instance.range
        if not(value >= _range[0] and value <= _range[1]):
            raise ValueError("Please provide a number between given range: \
            {0}.".format(_range))


def check_initstep(instance=None, initstep=None, value=None):
    """
    Validator for initstep attribute in Variable class.
    """
    _range = instance.range
    if value != -1:
        if value >= (_range[1] - _range[0]):
            raise ValueError("Initial step should be strictly lower than the \
            range:{0}.".format(_range))


def check_pos(instance=None, attribute=None, value=None):
    """
    Validator for strictly positive number attribute.
    """
    name = attribute.name
    if value <= 0:
        raise ValueError("{0} should be strictly positive.".format(name))


def check_constraint(instance=None, constraint=None, value=None):
    """
    Validator for comstraint attribute in Variable class.
    """
    if value:
        if hasattr(value, "__call__"):
            pars = describe(value)
            if len(pars) > 1:
                raise TypeError("Please provide a function with of single \
                argument.")

            test_return = value(0.0)
            if not isinstance(test_return, (int, float)):
                raise ValueError("Please provide a function that returns a \
                number (int/float).")
        else:
            raise TypeError("Please provide a function with one argument \
            returning a number (int/float).")

# Parameter classes


@attrs
class Named(object):
    """
    Class for named objects.
    """

    name = attrib(validator=attr.validators.instance_of(str))


@attrs()
class Range(object):
    """
    Class for object with a numerical range, i.e. Range((0,10)).
    """

    range = attrib(validator=[attr.validators.instance_of((tuple, list)),
                              check_range])


@attrs(repr=False, slots=True)
class Observable(Named, Range):
    """
    Class for physics observables.

        **Arguments:**

            - **name** a string
            - **range** a tuple with lower and upper limits of the range

        **Example:**
            obs = Observable(name="x", range=(0,100))
    """

    def __repr__(self):
        return "Observable('{0}', range={1})".format(self.name, self.range)


@attrs(repr=False, slots=True)
class Constant(Named):
    """
    Class for constant paramaters:

        **Arguments:**

            - **name** a string
            - **value** a number (int/float)

        **Example:**
            const = Constant(name="mu", value="1.2")
    """

    value = attr.ib(type=(int, float),
                    validator=attr.validators.instance_of((int, float)))

    def tominuit(self):
        """
        Returns a dictionnary of parameters for iminuit.
        """
        ret = {}
        ret[self.name] = self.value
        ret["fix_{0}".format(self.name)] = True
        return ret

    def __repr__(self):
        return "Constant('{0}', value={1})".format(self.name, self.value)


@attrs(repr=False, slots=True)
class Variable(Named, Range):
    """
    Class for variable paramaters.

        **Arguments:**

            - **name** a string
            - **value** a tuple with lower and upper limits of the range
            - **initvalue** (optionnal). a number (int/float) inside the range
            - **initstep** (optionnal). a number (int/float) lower than the
            range size

        **Examples:**
            var = (name="sigma", range=(0, 5))
            var = (name="sigma", range=(0, 5), initvalue=2.5, initstep=0.1)
    """

    initvalue = attr.ib(type=(int, float),
                        validator=[attr.validators.instance_of((int, float)),
                                   check_initvalue],
                        default=-1.)
    initstep = attr.ib(type=(int, float),
                       validator=[attr.validators.instance_of((int, float)),
                                  check_initstep],
                       default=-1.)

    def __attrs_post_init__(self):
        if self.initvalue == -1:
            self.initvalue = self.range[0] + (self.range[1] - self.range[0])/2.
        if self.initstep == -1:
            self.initstep = (self.range[1] - self.range[0])/100.

    def tominuit(self):
        """
        Returns a dictionnary of parameters for iminuit.
        """
        ret = {}
        ret[self.name] = self.initvalue
        ret["limit_{0}".format(self.name)] = self.range
        ret["error_{0}".format(self.name)] = self.initstep
        return ret

    def __repr__(self):
        rep = "Variable('{0}', initvalue={1}, range={2}, initstep={3})"
        rep = rep.format(self.name, self.initvalue, self.range, self.initstep)
        return rep


@attrs(repr=False, slots=True)
class POI(Named):
    """
    Class for parameters of interest:

        **Arguments:**

            - **name** a string
            - **value** (optional) a number (int/float)

        **Example:**
            poi = POI(name="Nisg", value="0")
            poi = POI(name="Nisg")
    """

    value = attr.ib(type=(int, float),
                    validator=attr.validators.instance_of((int, float)),
                    default=-99999999)

    def __attrs_post_init__(self):
        if self.value == -99999999:
            self.value = None

    def tominuit(self):
        """
        Returns a dictionnary of parameters for iminuit.
        """
        ret = {}
        if self.value:
            ret[self.name] = self.value
            ret["fix_{0}".format(self.name)] = True
        return ret

    def __repr__(self):
        repr = "POI('{0}'".format(self.name)
        if self.value is not None:
            return "{0}, value={1})".format(repr, self.value)
        else:
            return repr + ")"


@attrs(repr=False, slots=True)
class GaussianConstrained(Named, Range):
    """
    Class for gaussian constrained paramaters.

        **Arguments:**

            - **name** a string
            - **value** a tuple with lower and upper limits of the range
            - **mu** a number (int/float). Mean value of the gaussian.
            - **sigma** a number > 0 (int/float). Sigma of the gaussian.
            - **initstep** (optionnal). a number (int/float) lower than the
            range size

    """

    mu = attr.ib(type=(int, float),
                 validator=[attr.validators.instance_of((int, float))])
    sigma = attr.ib(type=(int, float),
                    validator=[attr.validators.instance_of((int, float)),
                               check_pos])
    initstep = attr.ib(type=(int, float),
                       validator=[attr.validators.instance_of((int, float)),
                                  check_initstep], default=-1.)

    def __attrs_post_init__(self):
        if self.initstep == -1:
            self.initstep = (self.range[1] - self.range[0])/100.

    def tominuit(self):
        """
        Returns a dictionnary of parameters for iminuit.
        """
        ret = {}
        ret[self.name] = self.mu
        ret["limit_{0}".format(self.name)] = self.range
        ret["error_{0}".format(self.name)] = self.initstep
        return ret

    def evalconstraint(self, param):
        return gaussian(param, self.mu, self.sigma)

    def log_evalconstraint(self, param):
        return gaussian.log(param, self.mu, self.sigma)

    def __repr__(self):
        rep = "GaussianConstrained('{0}', mu={1}, sigma={2}, range={3},"
        rep += " initstep={4})"
        rep = rep.format(self.name, self.mu, self.sigma, self.range,
                         self.initstep)

        return rep
