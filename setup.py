#!/usr/bin/python

import sys
import os.path

from setuptools import find_packages
from setuptools import setup

major, minor = sys.version_info[:2]

tr = ["pytest", "jupyter", "papermill", "jsonschema==2.6.0"]
tr += ["jupyter_client", "zfit"]
ir = ["iminuit", "numpy", "scipy", "attrs>=18.2.0"]

if major >= 3 and minor >= 5:
	ir += ["matplotlib"]
else:
	ir += ["matplotlib<3.0"]

if major < 3 or (major == 3 and minor <= 4):
	ir += ["ipython<6.0", "ipykernel<5.0.0", "jupyter-console<=5.0.0"]
	tr += ["jupyter_client"]

setup(  name = "statnight",
	version = "1.0",
	packages = find_packages(exclude = ["tests"]),
	scripts = [],
	data_files = ["README.rst"],
	description = "Pure python statistic tools for high energy physics, based on iminuit.",
	long_description = "",
	author = "Matthieu Marinangeli",
	author_email = "matthieu.marinangeli@epfl.ch",
	maintainer = "Matthieu Marinangeli",
	maintainer_email = "matthieu.marinangeli@epfl.ch",
	url = "https://github.com/marinang/statrise",
	download_url = "",
	license = "",
	test_suite = "tests",
	install_requires = ir,
	setup_requires = ["pytest-runner"],
    dependency_links=['https://github.com/zfit/zfit/tree/develop#egg=zfit-1.0'],
	tests_require = tr,
	classifiers = [
			"Intended Audience :: Science/Research",
			"Operating System :: MacOS",
			"Operating System :: POSIX",
			"Operating System :: Unix",
			"Programming Language :: Python",
			"Programming Language :: Python :: 3.4",
			"Programming Language :: Python :: 3.5",
			"Programming Language :: Python :: 3.6",
			"Programming Language :: Python :: 3.7",
			"Topic :: Scientific/Engineering :: Physics",
			],
	platforms = "Any",
		)
