#!/usr/bin/env python

"""Driver which runs using PBS."""

import pickle
from time import sleep

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPy.driverHelpers import PBSSubmitter, pathMerger
from standardPlots import fourierModesPlot, growthRatesPlot

#{{{runFourierModes
def runFourierModes():
    """
    Runs the fourier modes
    """
    loopOver = zip(dmpFolders["turbulence"], dmpFolders["expand"], paramKeys, rJobs)
    for dmp_folders, steadyStatePath, key, nr in loopOver:

        collectPaths = mergeFromLinear[key]
        dmp_folders  = (dmp_folders,)
        args = (dmp_folders, steadyStatePath, collectPaths)
        sub.setJobName("fourierModes{}".format(nr))
        sub.submitFunction(fourierModesPlot, args=args)
        # Sleep 1.5 seconds to ensure that tmp files will have different names
        sleep(1.5)
#}}}

#{{{runFourierModesSliced
def runFourierModesSliced():
    """
    Runs the sliced fourier modes
    """

    loopOver = zip(dmpFolders["turbulence"],\
                   dmpFolders["expand"],\
                   paramKeys,\
                   rJobs)
    for dmp_folders, steadyStatePath, key, nr in loopOver:

        # Find tSlice
        found = False
        for tkey in tSlices.keys():
            if tkey in dmp_folders:
                tSlice = tSlices[tkey]
                found = True
                break
        if not(found):
            raise ValueError("Could not find correct slice")

        collectPaths = mergeFromLinear[key]
        dmp_folders   = (dmp_folders,)
        args = (dmp_folders, collectPaths, steadyStatePath)
        kwargs = {"tSlice":(tSlice,)}
        sub.setJobName("fourierModesSliced{}".format(nr))
        sub.submitFunction(fourierModesPlot, args=args, kwargs=kwargs)
        # Sleep 1.5 seconds to ensure that tmp files will have different names
        sleep(1.5)
#}}}

#{{{runGrowthRates
def runGrowthRates():
    """
    Runs the growth rates
    """

    # NOTE: The ordering of param is in descending order (because of the
    #       organization in PBSScan)
    dmp_folders = (mergeFromLinear["param0"][-1],)
    keys = tuple(sorted(list(mergeFromLinear.keys())))
    scanCollectPaths = tuple(mergeFromLinear[key] for key in keys)

    # NOTE: The ordering is of the keys are in descending order (because
    #       of the organization in PBSScan)
    steadyStatePaths = dmpFolders["expand"]

    # Set the indices
    tKeys     = tuple(sorted(list(tSlices.keys()), reverse=True))
    startInds = tuple(tSlices[key].start for key in tKeys)
    endInds   = tuple(tSlices[key].stop for key in tKeys)

    args = (dmp_folders, scanCollectPaths, steadyStatePaths, scanParameter, startInds, endInds)
    sub.setJobName("growthRates")
    sub.submitFunction(growthRatesPlot, args=args)
#}}}

#{{{Globals
directory = "CSDXMagFieldScanAr"
scanParameter = "B0"

with open(os.path.join(directory, "dmpFoldersDict.pickle"), "rb") as f:
        dmpFolders = pickle.load(f)

mergeFromLinear =\
        pathMerger(dmpFolders, ("linear", "turbulence", "extraTurbulence"))

paramKeys = tuple(sorted(list(mergeFromLinear.keys())))
rJobs     = range(len(paramKeys))

# Generate the submitter
sub = PBSSubmitter()
sub.setNodes(nodes=1, ppn=2)
sub.setQueue("xpresq")
sub.setWalltime("00:05:00")
#}}}

if __name__ == "__main__":

    # Run the fourier modes
    runFourierModes()
    # Set linear slices and plot the sliced fourier modes
    tSlices = {\
               "B0_0.02":slice(80,240)  ,\
               "B0_0.04":slice(800,1250),\
               "B0_0.06":slice(180,300) ,\
               "B0_0.08":slice(100,225) ,\
               "B0_0.1" :slice(80,210)  ,\
               }
    runFourierModesSliced()
    sub.setWalltime("00:10:00")
    runGrowthRates()
