#!/usr/bin/env python

"""
setup.py file for SWIG example
"""

import os
from distutils.core import setup, Extension

# cwd = os.path.dirname(os.path.realpath(__file__))
# kuzzle_module = Extension('kuzzlesdk',
#                            sources=[ cwd + '/kcore_wrap.cxx' ],
#                            swig_opts=['-c++', '-py3']
#                            )

setup (name = 'kcore',
       version = '0.0.1',
       author      = "Kuzzle",
       description = """Kuzzle sdk""",
      #  ext_modules = ["kuzzlesdk"],
       py_modules = ["kcore"],
       )
