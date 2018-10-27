#!/usr/bin/python

import sys
import os.path

from setuptools import find_packages
from setuptools import setup

setup(  name = "statnight",
	version = "v1.0",
	packages = find_packages(exclude = ["tests"]),
	scripts = [],
	data_files = ["README.md"],
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
	install_requires = ["iminuit", "numpy", "scipy"],
	setup_requires = ["pytest-runner"],
	tests_require = ["pytest"],
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
		