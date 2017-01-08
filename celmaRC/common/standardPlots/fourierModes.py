#!/usr/bin/env python

"""Post-processor for fourierModes"""

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPy.fourierModes import DriverFourierModes

#{{{fourierModesPlot
def fourierModesPlot(dmp_folders, collectPaths, steadyStatePath, tSlice = None):
    #{{{docstring
    """
    Runs the standard fourier modes plot

    Parameters
    ----------
    dmp_folders : tuple
        Tuple of the dmp_folders
    collectPaths : tuple
        Tuple of the paths to collect from
    steadyStatePath : str
        The corresponding steady state path
    tSlice : [None|Slice]
        How to slice the time.
    """
    #}}}

    useSubProcess = False

    varName           = "n"
    convertToPhysical = True
    nModes            = 7

    xInd              = None
    yInd              = 16
    zInd              = None
    nPoints           = 1
    equallySpace      = "x"

    if tSlice is not None:
        sliced = True
    else:
        sliced = False

    indicesArgs   = (xInd, yInd, zInd)
    indicesKwargs = {"tSlice"          : tSlice         ,\
                     "nPoints"         : nPoints        ,\
                     "equallySpace"    : equallySpace   ,\
                     "steadyStatePath" : steadyStatePath,\
                     }

    plotSuperKwargs = {\
                        "showPlot"        : False ,\
                        "savePlot"        : True  ,\
                        "savePath"        : None  ,\
                        "extension"       : None  ,\
                        # NOTE: No implemented func which doesn't
                        #       require theRunName yet
                        "savePathFunc"    : None  ,\
                        "dmp_folders"     : None  ,\
                        "timeStampFolder" : False ,\
                        "sliced"          : sliced,\
                       }

    dFM = DriverFourierModes(
                     # DriverFourierModes
                     dmp_folders                ,\
                     indicesArgs                ,\
                     indicesKwargs              ,\
                     plotSuperKwargs            ,\
                     varName           = varName,\
                     nModes            = nModes ,\
                     # DriverPointsSuperClass
                     convertToPhysical = convertToPhysical,\
                     # DriverSuperClass
                     collectPaths  = collectPaths ,\
                     useSubProcess = useSubProcess,\
                          )
    dFM.driverFourierMode()
#}}}
