#!/usr/bin/env python

"""Driver which runs using PBS."""

from bout_runners import PBS_runner
import numpy as np

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath('./../common')
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPython.drivers import postBoutRunner

# The options for the run
# =============================================================================
# *****************************************************************************
ownFilterType = "none"
Sn = [2.25e22, 2e22, 1.5e22, 1.125e22, 2.25e21, 2.225e20]
# *****************************************************************************
# Set the spatial domain
nz = 1
# Set the temporal domain
restart    = None
remove_old = False
timestep   = [2e3]
nout       = [2]
directory  = "a1-KiwiFlatSourceScan"
# Shall we make?
make       = False
# =============================================================================


# The options for the post processing function
# =============================================================================
xguards    = False
yguards    = False
xSlice     = 0
ySlice     = 65
zSlice     = 0
tSlice     = slice(0, None)
showPlot   = False
savePlot   = True
axisEqualParallel = False
theRunName = "0-KiwiFlat-SourceScan"
# =============================================================================


# The PBS options
# =============================================================================
# Specify the numbers used for the BOUT runs
nproc                 = 48
BOUT_nodes            = 3
BOUT_ppn              = 16
BOUT_walltime         = '06:00:00'
BOUT_run_name         = theRunName
post_process_nproc    = 1
post_process_nodes    = 1
post_process_ppn      = 20
post_process_walltime = '0:29:00'
post_process_queue    = 'xpresq'
post_process_run_name = 'post' + theRunName.capitalize()
# =============================================================================


# Create the runner
# =============================================================================
myRuns = PBS_runner(\
            directory  = directory ,\
            nproc      = nproc ,\
            # Set spatial domain
            nz         = nz,\
            # Set temporal domain
            nout       = nout  ,\
            timestep   = timestep,\
            # Copy the source file
            cpy_source = True  ,\
            make       = make  ,\
            restart    = restart,\
            additional = [
                          ('tag',theRunName,0),\
                          ('ownFilters', 'type', ownFilterType),\
                          ('input'     , 'Sn',   Sn),\
                         ],\
            # PBS options
            BOUT_nodes            = BOUT_nodes           ,\
            BOUT_ppn              = BOUT_ppn             ,\
            BOUT_walltime         = BOUT_walltime        ,\
            BOUT_run_name         = BOUT_run_name        ,\
            post_process_nproc    = post_process_nproc   ,\
            post_process_nodes    = post_process_nodes   ,\
            post_process_ppn      = post_process_ppn     ,\
            post_process_walltime = post_process_walltime,\
            post_process_queue    = post_process_queue   ,\
            post_process_run_name = post_process_run_name,\
            )
# =============================================================================


# Perform the run
# =============================================================================
myRuns.execute_runs(\
                     remove_old               = remove_old,\
                     post_processing_function = postBoutRunner,\
                     # This function will be called every time after
                     # performing a run
                     post_process_after_every_run = True,\
                     # Below are the kwargs arguments being passed to
                     # the post processing function
                     # Switches
                     driverName        = "plot1DAnd2DDriver",\
                     xguards           = xguards           ,\
                     yguards           = yguards           ,\
                     xSlice            = xSlice            ,\
                     ySlice            = ySlice            ,\
                     zSlice            = zSlice            ,\
                     tSlice            = tSlice            ,\
                     axisEqualParallel = axisEqualParallel ,\
                     savePlot          = savePlot          ,\
                     saveFolderFunc    = "scanWTagSaveFunc",\
                     theRunName        = theRunName        ,\
                    )
# =============================================================================