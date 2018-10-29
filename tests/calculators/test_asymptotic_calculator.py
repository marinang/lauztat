#!/usr/bin/python

import pytest
import sys
import papermill as pm
import os

def test_notebook_example():
	
	location = "docs/examples/notebooks"
	
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
	
	assert obs_ul_nsig         == pytest.approx(10.4269, abs=0.05)
	assert exp_ul_nsig         == pytest.approx(10.7644, abs=0.05)
	assert exp_ul_nsig_p1sigma == pytest.approx(14.9781, abs=0.05)
	assert exp_ul_nsig_m1sigma == pytest.approx( 7.7548, abs=0.05)
	
	os.remove(outputnb)