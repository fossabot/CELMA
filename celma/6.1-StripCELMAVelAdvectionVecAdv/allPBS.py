#!/usr/bin/env python

"""Running all the PBS scripts"""

import os
import re

# Mode can be 'all', 'noRestart' or 'restart'
mode = 'all'

# Make
print('Now making')
os.system('make clean && make')
# Find all files
files = [f for f in os.listdir('.') if os.path.isfile(f)]
# Find files matching a specific pattern
string_to_find = 'PBSDriver-\d'
files = [f for f in files if re.search(string_to_find, f) != None]
# Filter according to mode
if mode == 'all':
    pass
elif mode == 'noRestart':
    files1 = [f for f in files if 'restart' not in f]
    files2 = [f for f in files if 'Restart' not in f]
    files = [*files1, *files2]
elif mode == 'restart':
    files1 = [f for f in files if 'restart' in f]
    files2 = [f for f in files if 'Restart' in f]
    files = [*files1, *files2]
else:
    raise RuntimeError("Mode '{}' not recognized".format(mode))

# Call the file
for f in files:
    print('\n'*3 + '='*60)
    print('Running the {} script'.format(f))
    print('='*60 + '\n'*3)
    os.system('python ' + f)
