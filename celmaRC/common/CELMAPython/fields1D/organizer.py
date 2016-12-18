#!/usr/bin/env python

from .line import Line
from ..plotHelpers import seqCMap2
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from boututils.datafile import DataFile
import os


"""
Contains the organizer class
"""

#{{{class Organizer
class Organizer(object):
    """
    Class which organizes several lines in a 1D plot.

    This class is responsible for

    * Organization of the lines
    * Make all axes
    * Setting proper names on figures and files
    * Making a combined line if useCombinedPlot is true
    """

    #{{{Constructor
    def __init__(self                    ,\
                 pltName                 ,\
                 combLineName    = None  ,\
                 cols            = 2     ,\
                 useCombinedPlot = False ,\
                 forceCombined   = True  ,\
                 path            = "data",\
                 ):
        """
        The constructor initializes the sequence of lines

        Parameters
        ----------
        pltName : str
            Name of the plot written in LaTeX format, but without the $
        combLineName : [None | str]
            If the string is set, then the organizer will try to collect
            ddt(combLineName) in makeCombinedLine.
        cols : int
            The total number of columns to be used in the plot
        useCombinedPlot : bool
            Toggles if a plot of combined lines are to be plotted
        forceCombined : bool
            Will still plot combined lines, even if lines are not found
        path : str
            Path to collect from
        """

        # Set member data from input
        self._cols           = cols
        self.useCombinedPlot = useCombinedPlot
        self.pltName         = pltName
        self.combLineName    = combLineName
        self._forceCombined   = forceCombined

        # Initialize non-input members
        self._pltSize         = (18,12)
        self.combLine         = None
        self.combLineLineObjs = []
        self.lines            = []
        self.extraLines       = {}
        self.axes             = []

        # Variables collectable in the dump file
        dataFileVars = DataFile(os.path.join(path,"BOUT.dmp.0.nc")).list()
        # Make everything lowercase in order to easen comparison
        self._dataFileVars = tuple(el.lower() for el in dataFileVars)
    #}}}

    #{{{pltPrepare
    def pltPrepare(self):
        """
        Prepares the lines in a plot for plotting.
        Call this function before calling collect.

        1. Check that a line is collectable.
        2. Add extra lines (combination of fields etc.) if any.
        3. Check if any plot pos have been given.
           If yes, lines will be rearranged.
        4. Set the color of each plot.
        5. Finds the bottom axes.
        6. Creates the figure and axes.
        7. Returns the figure.
        """

        # Check that lines are collectable
        notFound = []
        for line in self.lines:
            lowerCaseLin = line.name.lower()
            if lowerCaseLin not in self._dataFileVars:
                if self._forceCombined:
                    message = ("{0}!!! Warning: {1} could not be found. "
                               "A combined line will still be plotted as "
                               "forceCombined is set to True.{0}")
                else:
                    message = "{0}!!! Warning: {1} could not be found{0}"
                print(message.format("\n"*2, line.name))
                notFound.append(line)
        for missing in notFound:
            self.lines.remove(missing)
            if not(self._forceCombined):
                self.useCombinedPlot = False

        # Append lines with eventual extra lines
        # The extra lines are treated specially since they are not
        # collectable
        nExtraLines = len(self.extraLines.keys())
        if nExtraLines > 0:
            for key in self.extraLines.keys():
                # Insert the extraLines into self.lines
                self.lines.append(self.extraLines[key])

        # Organize the lines
        newLines = [None]*len(self.lines)
        # Make a copy as we are going to pop the list
        self.allFieldsPresent = True
        for line in self.lines:
            if line.plotPos:
                # Get index in self line
                index = self.lines.index(line)
                try:
                    newLines[line.plotPos] = line
                except IndexError:
                    # If not all the fields are saved
                    print(("WARNING: Could not properly position\n\n"))
                    self.allFieldsPresent = False
                    break
        if len(self.lines) > 0 and self.allFieldsPresent:
            # Get the free indices in newLines
            indices = tuple(i for i, el in enumerate(newLines) if el is None)
            for index, line in zip(indices, self.lines):
                newLines[index] = line

        if self.allFieldsPresent:
            # Reassign
            self.lines = newLines
        else:
            print(("Removing extra lines as positioning failed"))
            for key in self.extraLines.keys():
                # Insert the extraLines into self.lines
                self.lines.remove(self.extraLines[key])

        # Set the colors
        colorSpace = np.arange(len(self.lines))
        colors = seqCMap2(np.linspace(0, 1, len(colorSpace)))

        for lineNr, line in enumerate(self.lines):
            line.color = colors[lineNr]

        # If a combined line is to be plotted
        if self.useCombinedPlot:
            # Make a line object
            self.combLine = Line(name  = "ddt({})".format(self.combLineName),\
                                 label = r"\partial_t " + self.pltName ,\
                                 )
            # Make the lastline black, and append it to the lines
            self.combLine.color = "k"
            self.lines.append(self.combLine)

        # Calculate the number of rows
        rows = int(np.ceil(len(self.lines)/self._cols))

        # Create the figure
        fig = plt.figure(figsize = self._pltSize)
        gs  = GridSpec(rows, self._cols)

        # Make the axes
        for lineNr, line in enumerate(self.lines):
            if lineNr == 0:
                # Need an initial line
                line.ax = fig.add_subplot(gs[lineNr])
                firstAx = line.ax
            else:
                line.ax = fig.add_subplot(gs[lineNr], sharex=firstAx)

        for col in range(1, self._cols+1):
            try:
                self.lines[-col].bottomAx = True
            except IndexError:
                # Only one column
                if self.useCombinedPlot:
                    print("WARNING: Only combLine found. Will not plot!!!\n\n")
                    plt.close(fig)
                    return None
                break

        # Pop the combined line in order not to collect it
        if self.useCombinedPlot:
            self.combLine = self.lines.pop()

        # Pop the extra lines in order not to collect them
        if nExtraLines > 0 and self.allFieldsPresent:
            for key in self.extraLines.keys():
                # Update the extraLines, and remove them from
                # self.lines, in order not to collect them
                ind = self.lines.index(self.extraLines[key])
                self.extraLines[key] = self.lines.pop(ind)

        fig.canvas.set_window_title(self.pltName)

        return fig
    #}}}

    #{{{makeCombinedLine
    def makeCombinedLine(self, plotter):
        """
        Makes a combined line.
        To be called after all other lines are collected.

        The routine will first try to collect ddt of the labelName. If
        this is not available, a sum of the lines is used instead.

        Parameters
        ----------
        plotter : plotter object
            Containing the collectLine function
        """

        try:
            plotter.collectLine(self.combLine)
            print("ddt was collected")
        except OSError:
            # OSError is thrown if filed is not found

            # Initialize the field
            self.combLine.field = np.zeros(self.lines[0].field.shape)

            for line in self.lines:
                self.combLine.field += line.field

            print("ddt was obtained by summation")

        # Re-add the combLine to the list
        self.lines.append(self.combLine)
    #}}}
#}}}