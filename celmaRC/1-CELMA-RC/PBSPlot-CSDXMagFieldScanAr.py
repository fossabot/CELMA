#!/usr/bin/env python

"""Driver which plots the results of the simulations."""

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

# Set linear slices
tSlices = {\
           "B0_0.02":slice(80,240)  ,\
           "B0_0.04":slice(800,1250),\
           "B0_0.06":slice(180,300) ,\
           "B0_0.08":slice(100,225) ,\
           "B0_0.1" :slice(80,210)  ,\
           }
pltSub.setLinearPhaseTSlices(tSlices)

# Set saturated turbulence slices
tSlices = {\
           "B0_0.02":None,\
           "B0_0.04":None,\
           "B0_0.06":slice(1200,None),\
           "B0_0.08":slice(1000,None),\
           "B0_0.1" :None,\
           }
pltSub.setSatTurbTSlices(tSlices)

# Run the post-processing
# pltSub.updatePlotSuperKwargs({"extension" : "pdf"})
pltSub.runCominedPlots()
pltSub.runEnergy(sliced=False)
pltSub.runEnergy(sliced=True)
pltSub.runFourierModes(sliced=False)
pltSub.runFourierModes(sliced=True)
pltSub.runGrowthRates()
pltSub.runPerformance(allFolders=False)
pltSub.runPerformance(allFolders=True)
pltSub.runPosOfFluct()
pltSub.runPSD2D()
pltSub.runSkewKurt()
pltSub.runZonalFlow()

# Run the animations
pltSub.updatePlotSuperKwargs({"extension" : None})
# pltSub.sub.setWalltime("01:00:00")
# pltSub.sub.setNodes(nodes=1, ppn=20)
# pltSub.runFields1DAnim()
# pltSub.sub.setQueue("fatq")
# pltSub.sub.setWalltime("04:00:00")
# pltSub.runFields2DAnim(fluct=True)
# pltSub.runFields2DAnim(fluct=False)
