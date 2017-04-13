#!/usr/bin/env python

"""Method of exact solution driver"""

from bout_runners.bout_runners import basic_runner
import numpy as np
import sys, os
# If we add to sys.path, then it must be an absolute path
common_dir = os.path.abspath('./../../../common')
# Sys path is a list of system paths
sys.path.append(common_dir)

from CELMAPy.MES import perform_MES_test_vol as postProcess

# The options for the run
# =============================================================================
# Additional options
remove_old  = False
directory   = "yHat"
make        = True
nproc       = 4
maxNumber   = 512
fromToRange = range(4, 11)
# =============================================================================


# dz option
# =============================================================================
# Spatial domain (+2 adds the ghost points)
ny = [2**n + 2 for n in fromToRange]
nx = [maxNumber]*len(ny)
nz = [maxNumber]*len(ny)

# Create the runner
dz_runs = basic_runner(\
            directory  = directory ,\
            nproc      = nproc ,\
            # Spatial domain
            nx         = nx,\
            ny         = ny,\
            nz         = nz,\
            # Copy the source file
            cpy_source = True  ,\
            make       = make  ,\
            # Sort the runs by the spatial domain
            sort_by    = 'spatial_domain'
            )
# =============================================================================


# Perform the runs
# =============================================================================
dz_runs.execute_runs(\
                     remove_old = remove_old,\
                     # Set the proper directory
                     post_processing_function = postProcess,\
                     post_process_after_every_run = False,\
                     # Below are the kwargs arguments being passed to
                     # the post processing function
                     show_plot     = True ,\
                     use_dx        = False,\
                     use_dy        = True ,\
                     use_dz        = False,\
                     extension     = 'pdf',\
                    )
# =============================================================================
