#!/usr/bin/env python

"""
Contains drivers for plotting 1D plots
"""

from ..modelSpecific import getOrgObjFromModel, labelNames
from ..fieldPlotters import Plot1D
from .fieldPlottersDriver import FieldPlottersDriver
import numpy as np
from multiprocessing import Process

#{{{Drivers1D
class Drivers1D(FieldPlottersDriver):
    """
    Class which handles the 1D plots of the fields.
    """

    #{{{Constructor
    def __init__(self            ,\
                 *args           ,\
                 skipPlots = None,\
                 marker    = "o" ,\
                 labelName   = None,\
                 **kwargs):
        #{{{docstring
        """
        This constructor:

        1. Calls the parent constructor
        2. Sets additional member data.
        3. Removes names in skipPlot from the labelNames

        Parameters
        ----------
        *args : positional arguments
            See the constructor of FieldPlottersDriver for details.
        skipPlots : sequence of str
            Sequence of string of names of plots to skip when plotting for
            several.
        marker : str
            The type of marker to be used in the plot.
        labelName : str
           Name of plot to make.
        **kwargs : keyword arguments
            See the constructor of FieldPlottersDriver for details.
        """
        #}}}

        # Call the constructor of the parent class
        super().__init__(*args, **kwargs)

        # Set member data
        self._marker  = marker
        self._labelName = labelName

        # Take out the skip plots
        if skipPlots is not None:
            for skip in skipPlots:
                labelNames.remove(skip)
    #}}}

    #{{{parPerpDriver
    def parPerpDriver(self):
        """
        Wrapper function which runs all the parallel and perpendicular plots.
        """

        # Store the original x slice
        originalXSlice = self._xSlice
        # Make sure we have perpendicular points to plot
        if self._xSlice is not slice:
            self._xSlice = slice(0, None)

        if self._useSubProcess:
            #{{{ Function call through subprocess
            proc = {}
            for labelName in labelNames:
                self._labelName = labelName
                # Create process
                proc[labelName] = Process(\
                                    target = self.single1DDriver,\
                                    args   = ()                 ,\
                                    kwargs = {}
                                   )
                # Start process
                proc[labelName].start()
            for key in proc.keys():
                # Wait for process to finish
                proc[key].join()
            #}}}
        else:
            #{{{ Normal function call
            for labelName in labelNames:
                self._labelName = labelName
                self.single1DDriver()
            #}}}

        # Restore the original x slice
        self._xSlice = originalXSlice
        # Make sure we have parallel points to plot
        if self._ySlice is not slice:
            self._ySlice = slice(0, None)

        if self._useSubProcess:
            #{{{ Function call through subprocess
            proc = {}
            for labelName in labelNames:
                self._labelName = labelName
                # Create process
                proc[labelName] = Process(\
                                    target = self.single1DDriver,\
                                    args   = ()                 ,\
                                    kwargs = {}
                                   )
                # Start process
                proc[labelName].start()
            for key in proc.keys():
                # Wait for process to finish
                proc[key].join()
            #}}}
        else:
            #{{{ Normal function call
            for labelName in labelNames:
                self._labelName = labelName
                self.single1DDriver()
            #}}}
    #}}}

    #{{{perpDriver
    def perpDriver(self):
        """
        Wrapper function which runs all the perpendicular plots.
        """

        # Make sure we have perpendicular points to plot
        if self._xSlice is not slice:
            self._xSlice = slice(0, None)

        if self._useSubProcess:
            #{{{ Function call through subprocess
            proc = {}
            for labelName in labelNames:
                self._labelName = labelName
                # Create process
                proc[labelName] = Process(\
                                    target = self.single1DDriver,\
                                    args   = ()                 ,\
                                    kwargs = {}
                                   )
                # Start process
                proc[labelName].start()
            for key in proc.keys():
                # Wait for process to finish
                proc[key].join()
            #}}}
        else:
            #{{{ Normal function call
            for labelName in labelNames:
                self._labelName = labelName
                self.single1DDriver()
            #}}}
    #}}}

    #{{{parDriver
    def parDriver(self):
        """
        Wrapper function which runs all the parallel plots.
        """

        # Make sure we have parallel points to plot
        if self._ySlice is not slice:
            self._ySlice = slice(0, None)

        if self._useSubProcess:
            #{{{ Function call through subprocess
            proc = {}
            for labelName in labelNames:
                self._labelName = labelName
                # Create process
                proc[labelName] = Process(\
                                    target = self.single1DDriver,\
                                    args   = ()                 ,\
                                    kwargs = {}
                                   )
                # Start process
                proc[labelName].start()
            for key in proc.keys():
                # Wait for process to finish
                proc[key].join()
            #}}}
        else:
            #{{{ Normal function call
            for labelName in labelNames:
                self._labelName = labelName
                self.single1DDriver()
            #}}}
    #}}}

    #{{{single1DDriver
    def single1DDriver(self):
        """
        Driver for a single 1D plot.
        """

        # Make the plotter object
        plotter = Plot1D(self._dmp_folder                           ,\
                         xguards           = self._xguards          ,\
                         yguards           = self._yguards          ,\
                         marker            = self._marker           ,\
                         xSlice            = self._xSlice           ,\
                         ySlice            = self._ySlice           ,\
                         zSlice            = self._zSlice           ,\
                         tSlice            = self._tSlice           ,\
                         convertToPhysical = self._convertToPhysical,\
                         fluctuation         = self._fluctuation        ,\
                         showPlot          = self._showPlot         ,\
                         savePlot          = self._savePlot         ,\
                         saveFolder        = self._saveFolder       ,\
                         extension         = self._extension        ,\
                         writer            = self._writer           ,\
                        )

        # Get the organization object (will depend on the model used (i.e.
        # the fields stored)
        orgObj = getOrgObjFromModel(self._dmp_folder, self._labelName)

        # Prepare the lines for plotting
        fig = orgObj.pltPrepare()

        if fig is None or len(orgObj.lines) == 0:
            # Exit as no plots will take place
            return None

        # Collect with the plotter object
        for line in orgObj.lines:
            plotter.collectLine(line)

        if orgObj.useCombinedPlot:
            orgObj.makeCombinedLine(plotter)

        # Treatment of extra lines
        if self._labelName == "mainFields":
            if "jParFields" not in labelNames\
            and orgObj.allFieldsPresent:
                # Find lnN, uEPar and uIPar
                for line in orgObj.lines:
                    if line.name == "lnN":
                        lnN = line.field
                    if line.name == "uEPar":
                        uEPar = line.field
                    if line.name == "uIPar":
                        uIPar = line.field

                # Create the jPar line
                orgObj.extraLines["jPar"].field =\
                    np.exp(lnN)*(uIPar - uEPar)
                if orgObj.extraLines["jPar"].plotPos:
                    orgObj.lines.insert(orgObj.extraLines["jPar"].plotPos,\
                                        orgObj.extraLines["jPar"])
                else:
                    orgObj.lines.append(orgObj.extraLines["jPar"])

            if "n" not in labelNames\
            and orgObj.allFieldsPresent:
                # Find lnN, uEPar and uIPar
                for line in orgObj.lines:
                    if line.name == "lnN":
                        lnN = line.field

                # Create the n line
                orgObj.extraLines["n"].field = np.exp(lnN)
                if orgObj.extraLines["n"].plotPos:
                    orgObj.lines.insert(orgObj.extraLines["n"].plotPos,\
                                        orgObj.extraLines["n"])
                else:
                    orgObj.lines.append(orgObj.extraLines["n"])

        # Get the correct units and numbers
        for line in orgObj.lines:
            line.field, _, units =\
                    plotter.helper.physicalUnitsConverter(line.field,\
                                                          line.name)

            if plotter.helper.convertToPhysical:
                if line.name == "momDensPar":
                    line.label = "$m_i$" + line.label
                if self._labelName == "mainFields":
                    line.label += r" $[{}]$".format(units)

        # Do the plot
        plotter.plotDriver(fig, orgObj, savePath = self._savePath)
    #}}}
#}}}