#!/usr/bin/env python

"""Driver which plots the results of the simulations."""

import numpy as np

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from standardPlots import PlotSubmitter

directory = "CSDXMagFieldScanAr"
scanParameter = "B0"

# Create the plotSubmitter
pltSub = PlotSubmitter(directory, scanParameter)

# Toggle to not parallelize
pltSub.sub.toggleSubmitOrRun()

# Run the animations
pltSub.runFields1DAnim(useMultiProcess=False)
pltSub.runFields2DAnim(fluct=True)
pltSub.runFields2DAnim(fluct=False)