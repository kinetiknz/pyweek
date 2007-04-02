#! /usr/bin/env python

import sys
import os
try:
    basename = os.path.dirname(__file__)
    libdir = os.path.abspath(os.path.join(basename, 'lib'))
    thirddiry = os.path.abspath(os.path.join(basename, 'thirdparty'))
    sys.path.insert(0, libdir)
    sys.path.insert(0, thirddir)
except:
    pass

import main
main.main()
