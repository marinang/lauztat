#!/usr/bin/python

"""
Parameter classes
"""


class POI(object):
    """
    Class for parameters of interest:

        **Arguments:**

            - **parameter** a parameter
            - **value** a single or a list of int/float.

        **Example:**
            poi = POI(name="Nisg", value=0)
            poi = POI(name="Nisg", value=np.linspace(0,10,10))
    """

    def __init__(self, parameter, value):

        if not hasattr(parameter, "name"):
            msg = "Please provide a parameter from zfit from instance."
            raise TypeError(msg)

        self.parameter = parameter
        self.name = parameter.name
        self.value = value

    def __repr__(self):
        repr = "POI('{0}'".format(self.name)
        if self.value is not None:
            return "{0}, value={1})".format(repr, self.value)
        else:
            return repr + ")"

    def __getitem__(self, i):
        return POI(self.parameter, self.value[i])

    def __iter__(self):
        if not hasattr(self.value, "__iter__"):
            value = [self.value]
        else:
            value = self.value

        for v in value:
            yield POI(self.parameter, v)

    def __len__(self):
        if not hasattr(self.value, "__iter__"):
            return 1
        else:
            return len(self.value)

    def __eq__(self, other):
        if not isinstance(other, POI):
            return NotImplemented

        if self.__len__() > 1:
            cond = all(self.value == other.value)
            ncond = self.name == other.name
            return cond and ncond
        else:
            cond = self.value == other.value
            ncond = self.name == other.name
            return cond and ncond

    def __hash__(self):
        return hash((self.name, self.value))
