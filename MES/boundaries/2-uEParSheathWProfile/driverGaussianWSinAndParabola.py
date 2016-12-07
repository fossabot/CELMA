#!/usr/bin/env python

"""Method of exact solution driver"""

from bout_runners.bout_runners import basic_runner
import numpy as np
import sys, os
# If we add to sys.path, then it must be an absolute path
common_dir = os.path.abspath('./../../')
# Sys path is a list of system paths
sys.path.append(common_dir)

from common.python.postProcessingMES import perform_MES_test

# The options for the run
# =============================================================================
# Spatial domain (+2 adds the ghost points)
ny = [2**n for n in range(4, 12)]

# Additional options
remove_old = True
directory  = "gaussianWSinAndParabola"
make       = True
nproc      = 4
# =============================================================================


# Create the runner
# =============================================================================
my_runs = basic_runner(\
            directory  = directory ,\
            nproc      = nproc ,\
            # Spatial domain
            ny         = ny,\
            # Copy the source file
            cpy_source = True  ,\
            make       = make  ,\
            # Sort the runs by the spatial domain
            sort_by    = 'spatial_domain'
            )
# =============================================================================


# Perform the run
# =============================================================================
my_runs.execute_runs(\
                     remove_old = remove_old,\
                     # Set the proper directory
                     post_processing_function = perform_MES_test,\
                     post_process_after_every_run = False,\
                     # Below are the kwargs arguments being passed to
                     # the post processing function
                     show_plot     = False    ,\
                     use_dx        = False    ,\
                     use_dy        = True     ,\
                     use_dz        = False    ,\
                     xy_error_plot = True     ,\
                     yguards       = True     ,\
                    )
# =============================================================================