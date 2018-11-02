#!/usr/bin/python

"""
Parameter classes
"""

from iminuit import describe
import attr
from attr import attrs, attrib


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


@attrs(repr=False)
class Range(object):
    """
    Class for object with a numerical range, i.e. Range((0,10)).
    """

    range = attrib(validator=[attr.validators.instance_of((tuple, list)),
                              check_range])

    def __repr__(self):
        return "Range({})".format(self.range)


@attrs(repr=False, slots=True)
class Observable(Named, Range):
    """
    Class for physics observables:
        obs = Observable(name="x", range=(0,100))
    """

    def __repr__(self):
        return "Observable('{0}', range={1})".format(self.name, self.range)


@attrs(repr=False, slots=True)
class Constant(Named):
    """
    Class for constant paramaters:
        const = Constant(name="mu", value="1.2")
    """

    value = attr.ib(type=(int, float),
                    validator=attr.validators.instance_of((int, float)))

    def tominuit(self):
        ret = {}
        ret[self.name] = self.value
        ret["fix_{0}".format(self.name)] = True
        return ret

    def __repr__(self):
        return "Constant('{0}', value={1})".format(self.name, self.value)


@attrs(repr=False, slots=True)
class Variable(Named, Range):
    """
    Class for variable paramaters:
        var = (name="sigma", range=(0, 5))
        var = (name="sigma", range=(0, 5), initvalue=2.5, initstep=0.1)
        var = (name="sigma", range=(0, 5), constraint= lambda x: (x-2)**2
    """

    initvalue = attr.ib(type=(int, float),
                        validator=[attr.validators.instance_of((int, float)),
                                   check_initvalue],
                        default=-1.)
    initstep = attr.ib(type=(int, float),
                       validator=[attr.validators.instance_of((int, float)),
                                  check_initstep],
                       default=-1.)
    constraint = attr.ib(type=(int, float),
                         validator=check_constraint,
                         default=None)

    def __attrs_post_init__(self):
        if self.initvalue == -1:
            self.initvalue = self.range[0] + (self.range[1] - self.range[0])/2.
        if self.initstep == -1:
            self.initstep = (self.range[1] - self.range[0])/100.

    def tominuit(self):
        ret = {}
        ret[self.name] = self.initvalue
        ret["limit_{0}".format(self.name)] = self.range
        ret["error_{0}".format(self.name)] = self.initstep
        return ret

    def __repr__(self):
        basis = "Variable('{0}', initvalue={1}, range={2}, initstep={3}"
        basis = basis.format(self.name, self.initvalue,
                             self.range, self.initstep)

        if self.constraint:
            return basis + ", constraint={0})".format(self.constraint)

        return basis + ")"
