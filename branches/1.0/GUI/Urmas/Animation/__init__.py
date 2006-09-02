# This file makes this directory a Python package.
# Animation

import sys, os, string

print __path__
my_name = os.path.basename (__path__[0])

# hacks to allow local names and prevents unnecessary reloading of
# modules.
for mod_name in ('mayavi.Common', 'mayavi.Base', 'mayavi.Base.Objects'):
        if sys.modules.has_key (mod_name):
        	local = string.replace (mod_name, 'mayavi', 'mayavi.' + my_name)
        	sys.modules[local] = sys.modules[mod_name]
