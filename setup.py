#!/usr/bin/python

import sys
import os

from setuptools import find_packages
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

major, minor = sys.version_info[:2]

tr = ["pytest", "jupyter", "papermill", "jsonschema==2.6.0"]
tr += ["jupyter_client", "h5py"]
ir = ["attrs>=18.2.0", "scipy", "numpy", "zfit"]

if major >= 3 and minor >= 5:
    ir += ["matplotlib"]
else:
    ir += ["matplotlib<3.0"]

if major < 3 or (major == 3 and minor <= 4):
    ir += ["ipython<6.0", "ipykernel<5.0.0", "jupyter-console<=5.0.0"]
    tr += ["jupyter_client"]

with open(os.path.join(here, 'README.rst'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

setup(name="lauztat",
      version="1.1.2",
      packages=find_packages(exclude=["tests"]),
      scripts=[],
      data_files=["README.rst"],
      description="Pure python statistic tools for high energy physics.",
      long_description=readme.replace(":math:", ""),
      author="Matthieu Marinangeli",
      author_email="matthieu.marinangeli@epfl.ch",
      maintainer="Matthieu Marinangeli",
      maintainer_email="matthieu.marinangeli@epfl.ch",
      url="https://github.com/marinang/lauztat",
      download_url="",
      license="",
      test_suite="tests",
      install_requires=ir,
      setup_requires=["pytest-runner"],
      dependency_links=['https://github.com/zfit/zfit/tarball/develop'],
      tests_require=tr,
      classifiers=[
          "Intended Audience :: Science/Research",
          "Operating System :: MacOS",
          "Operating System :: POSIX",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Topic :: Scientific/Engineering :: Physics",
          ],
      platforms="Any",
      )
