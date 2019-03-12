#!/usr/bin/python
import pytest

import zfit
from lauztat import POI
import numpy as np

mean = zfit.Parameter("mu", 1.2, 0.1, 2)


def test_pois():

    p = POI(mean, 0)
    p1 = POI(mean, 1.)
    vals = np.linspace(0., 1.0, 10)
    pn = POI(mean, vals)

    with pytest.raises(TypeError):
        POI("mean", 0)
    with pytest.raises(TypeError):
        POI(mean)

    assert p.value == 0
    assert p.name == mean.name
    assert len(p) == 1
    with pytest.raises(TypeError):
        p[0]
    assert p != p1

    assert all(pn.value == vals)
    assert len(pn) == len(vals)
    assert pn != p
    assert pn != p1
    assert pn[0] == p
    assert pn[-1] == p1

    for p_ in p:
        pass

    {p: "p", p1: "p1"}
