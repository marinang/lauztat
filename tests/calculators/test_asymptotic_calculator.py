#!/usr/bin/python
import pytest
import sys
import papermill as pm
import os

location = "docs/examples/notebooks"


def test_notebook_upperlimit():

    outputnb = '{0}/output.ipynb'.format(location)
    common_kwargs = {
        'output': str(outputnb),
        'kernel_name': 'python{0}'.format(sys.version_info.major),
        }

    nb = "{0}/upperlimit_asymptotics.ipynb".format(location)

    pm.execute_notebook(nb, **common_kwargs)

    nb = pm.read_notebook(outputnb)

    obs_ul_nsig = nb.data["obs_ul_nsig"]
    exp_ul_nsig = nb.data["exp_ul_nsig"]
    exp_ul_nsig_p1sigma = nb.data["exp_ul_nsig_p1sigma"]
    exp_ul_nsig_m1sigma = nb.data["exp_ul_nsig_m1sigma"]

    assert obs_ul_nsig == pytest.approx(10.4269, abs=0.05)
    assert exp_ul_nsig == pytest.approx(10.7644, abs=0.05)
    assert exp_ul_nsig_p1sigma == pytest.approx(14.9781, abs=0.05)
    assert exp_ul_nsig_m1sigma == pytest.approx(7.7548, abs=0.05)

    os.remove(outputnb)


def test_notebook_discovery():

    outputnb = '{0}/output.ipynb'.format(location)
    common_kwargs = {
        'output': str(outputnb),
        'kernel_name': 'python{0}'.format(sys.version_info.major),
        }

    nb = "{0}/discovery_asymptotics.ipynb".format(location)

    pm.execute_notebook(nb, **common_kwargs)

    nb = pm.read_notebook(outputnb)

    pnull = nb.data["pnull"]
    significance = nb.data["significance"]
    clb = nb.data["clb"]
    clsb = nb.data["clsb"]

    assert pnull <= 3E-7
    assert significance >= 5
    assert significance == pytest.approx(5.26, abs=0.005)
    assert clb <= 3E-7
    assert pnull == clb
    assert clsb == pytest.approx(0.535, abs=0.005)

    os.remove(outputnb)
