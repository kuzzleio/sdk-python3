#!/usr/bin/env python

"""
setup.py file for SWIG example
"""

import os
from distutils.core import setup, Extension

setup (name = 'kcore',
       version = '0.0.1',
       author      = "Kuzzle",
       description = """Kuzzle sdk""",
       py_modules = ["kcore"],
       )
