#!/usr/bin/env python

""" Contains the PlotHelper class """

from .plotNumberFormatter import plotNumberFormatter
from boutdata import collect
from boututils.options import BOUTOptions
from matplotlib.ticker import MaxNLocator, FuncFormatter
import scipy.constants as cst
import numpy as np

#{{{PlotHelper
class PlotHelper(object):
    """Contains common routines used when making plots"""

    #{{{__init__
    def  __init__(self,\
                  path,\
                  t,\
                  xguards           = False,\
                  yguards           = False,\
                  convertToPhysical = False):
        #{{{docstring
        """
        The constructor for PlotHelper, which:

        * Sets the member data
        * Collects the coordinates (excluding t)
        * Makes the conversion dictionary

        Parameters
        ----------
        path : str
            The path to collect from.
        t : array
            The time array.
        xguards : bool
            If xguards should be included when collecting.
        yguards : bool
            If yguards should be included when collecting.
        convertToPhysical : bool
            Whether or not to convert to physical units.
        """
        #}}}

        # Set the member data
        self._path              = path
        self._xguards           = xguards
        self._yguards           = yguards
        self.convertToPhysical = convertToPhysical
        self.t                  = t

        # Get the coordinates
        self.rho, self.theta, self.z = self._getCoordinates()

        # Get the conversionDict
        self._convDict = self._getConversionDict()

        # Get the convert the coordinates, and get the txt dictionaries
        self.tTxtDict, self.rhoTxtDict, self.thetaTxtDict, self.zTxtDict =\
                self._coordinatesConvert()

        # Makes the strings which are used for titles and labels
        self._makeStrings()
    #}}}

    #{{{_getCoordinates
    def _getCoordinates(self):
        #{{{docstring
        """
        Collects the coordinates.

        NOTE: t is collected on its own due to the possibility to slice in
              t.

        Returns
        -------
        rho : array
            The rho coordinate.
        theta : array
            The theta coordinate.
        z : array
            The z coordinate.
        """
        #}}}

        #{{{rho
        dx = collect("dx"                   ,\
                     path    = self._path   ,\
                     xguards = self._xguards,\
                     yguards = self._yguards,\
                     info    = False)
        MXG = collect("MXG"                  ,\
                      path    = self._path   ,\
                      xguards = self._xguards,\
                      yguards = self._yguards,\
                      info    = False)

        nPoints = dx.shape[0]
        dx      = dx[0,0]

        if self._xguards:
            innerPoints = nPoints - 2*MXG
        else:
            innerPoints = nPoints

        # By default there is no offset in the cylinder
        # For comparision with other codes, an offset option is set
        # Read the input file
        myOpts = BOUTOptions(self._path)
        # Read in geom offset
        try:
            offset = eval(myOpts.geom["offset"])
            spacing = "\n"*3
            print("{0}!!!WARNING: 'offset' found in BOUT.inp, "
                  "running as annulus!!!{0}".format(spacing))
            rho = offset + dx * np.array(np.arange(0.5, innerPoints))
        except KeyError:
            # This is the default
            rho = dx * np.array(np.arange(0.5, innerPoints))

        if self._xguards:
            # Insert the first and last grid point
            rho = np.insert(rho, 0, - 0.5*dx)
            rho = np.append(rho, rho[-1] + dx)
        #}}}

        #{{{z
        dy  = collect("dy"                   ,\
                      path    = self._path   ,\
                      xguards = self._xguards,\
                      yguards = self._yguards,\
                      info    = False)
        MYG = collect("MYG"                  ,\
                      path    = self._path   ,\
                      xguards = self._xguards,\
                      yguards = self._yguards,\
                      info    = False)

        nPoints  = dy.shape[1]
        dy = dy[0,0]

        if self._yguards:
            innerPoints = nPoints - 2*MYG
        else:
            innerPoints = nPoints

        z = dy * np.array(np.arange(0.5, innerPoints))

        if self._yguards:
            # Insert the first and last grid point
            z = np.insert(z, 0, - 0.5*dy)
            z = np.append(z, z[-1] + dy)
        #}}}

        #{{{theta
        dz = collect("dz"                   ,\
                     path    = self._path   ,\
                     xguards = self._xguards,\
                     yguards = self._yguards,\
                     info    = False)
        MZ       = collect("MZ"                   ,\
                           path    = self._path   ,\
                           xguards = self._xguards,\
                           yguards = self._yguards,\
                           info    = False)

        # Subtract the unused plane
        innerPoints = MZ - 1

        theta = dz * np.array(np.arange(0.0, innerPoints))

        # Convert to degrees
        theta * (180/np.pi)
        #}}}

        return rho, theta, z
    #}}}

    #{{{_getConversionDict
    def _getConversionDict(self):
        #{{{docstring
        """
        Get the conversion dictionary, sets convertToPhysical to False
        if the normalization parameters are not found.

        Returns
        -------
        convDict : dictionary
        """
        #}}}

        convDict = {}
        if self.convertToPhysical:
            try:
                normalizers = ["omCI", "rhoS", "n0", "Te0"]
                for normalizer in normalizers:
                    convDict[normalizer] =\
                            collect(normalizer, path=self._path, info=False)

            except ValueError:
                # An OSError is thrown if the file is not found
                message = ("{0}{1}WARNING: Normalized quantities not found. "
                           "The time remains normalized".format("\n"*3,"!"*3))
                print(message)

                # Reset convertToPhysical
                self.convertToPhysical = False

        return convDict
    #}}}

    #{{{_coordinatesConvert
    def _coordinatesConvert(self):
        #{{{docstring
        """
        Converts t, rho and z if convertToPhysical is True

        Returns
        -------
        tTxtDict : dictionary
            Used to format strings with the time.
            Contains the keys:
            * Normalization - The normalization string
            * Units - The units string
        rhoTxtDict : dictionary
            Used to format strings with rho.
            Contains the keys:
            * Normalization - The normalization string
            * Units - The units string
        thetaTxtDict : dictionary
            Empty dict which is later going to be used to format strings
            with theta.
        zTxtDict : dictionary
            Used to format strings with z.
            Contains the keys:
            * Normalization - The normalization string
            * Units - The units string
        """
        #}}}
        # Process values, and get normalization and units
        self.t, tNormalization, tUnits =\
                self.physicalUnitsConverter(self.t, "t")
        self.rho, rhoNormalization, rhoUnits =\
                self.physicalUnitsConverter(self.rho, "rho")
        self.z, zNormalization, zUnits =\
               self.physicalUnitsConverter(self.z, "z")

        # String formatting
        tTxtDict     = {"normalization":tNormalization  , "units":tUnits}
        rhoTxtDict   = {"normalization":rhoNormalization, "units":rhoUnits}
        thetaTxtDict = {}
        zTxtDict     = {"normalization":zNormalization  , "units":zUnits}

        return tTxtDict, rhoTxtDict, thetaTxtDict, zTxtDict
    #}}}

    #{{{_makeStrings
    def _makeStrings(self):
        #{{{docstring
        """
        Expands the TxTDicts, so that they can easily be used when
        formatting text for labels and titles.
        """
        #}}}

        # Set generic string templates
        self.rhoTxtDict["rhoTxt"] =\
                r"$\rho{0[normalization]}$".format(self.rhoTxtDict)
        self.zTxtDict["zTxt"] =\
                r"$z{0[normalization]}$".format(self.zTxtDict)
        self.thetaTxtDict["constThetaTxt"] =\
                r"$\theta={:d}^{{\circ}}$"
        # Set label and title templates
        if self.convertToPhysical:
            self.rhoTxtDict["rhoTxtLabel"] = "{0[rhoTxt]} $[{0[units]}]$".\
                        format(self.rhoTxtDict)
            self.rhoTxtDict["constRhoTxt"] =\
                        r"{0[rhoTxt]} $=$ {0[value]} ${0[units]}$"
            self.zTxtDict["zTxtLabel"] = "{0[zTxt]} $[{0[units]}]$".\
                        format(self.zTxtDict)
            self.zTxtDict["constZTxt"] =\
                    r"{0[zTxt]} $=$ {0[value]} ${0[units]}$"
            self.tTxtDict["tTxt"] =\
                r"$\mathrm{{t}}{0[normalization]}$ $=$ {0[value]} ${0[units]}$"
            self.tTxtDict["tTxtLabel"] =\
                r"$\mathrm{{t}}{0[normalization]}$ $[{0[units]}]$"
        else:
            self.rhoTxtDict["rhoTxtLabel"] = "{0[rhoTxt]}".\
                                             format(self.rhoTxtDict)
            self.rhoTxtDict["constRhoTxt"] = r"{0[rhoTxt]} $=$ {0[value]}"
            self.zTxtDict  ["zTxtLabel"] = "{0[zTxt]}".\
                                           format(self.zTxtDict)
            self.zTxtDict  ["constZTxt"] = r"{0[zTxt]} $=$ {0[value]}"
            self.tTxtDict["tTxt"] =\
                r"$\mathrm{{t}}{0[normalization]}$ $=$ {0[value]}"
            self.tTxtDict  ["tTxtLabel"] = r"$t{0[normalization]}$"
    #}}}

    #{{{makePlotPretty
    def makePlotPretty(self                   ,\
                       ax                     ,\
                       xprune   = "lower"     ,\
                       yprune   = None        ,\
                       rotation = "horizontal",\
                       loc      = "best"      ,\
                       ):
        """
        Routine that fixes some beauty-mistakes in matplotlib

        Parameters
        ----------
        ax : axis
            The axis to fix.
        xprune : str
            What ticks should be pruned on the x axis.
        yprune : str
            What ticks should be pruned on the y axis.
        rotation : [str | int]
            Rotation of the x axis.
        loc : str
            Location of the legend
        """

        # Avoid silly top value (only for non-log axes)
        try:
            ax.get_yaxis().get_major_formatter().set_useOffset(False)
        except:
            pass
        # Format the tick labels
        ax.set_xticklabels(ax.xaxis.get_majorticklabels(), rotation=rotation)
        ax.get_xaxis().set_major_formatter(FuncFormatter(plotNumberFormatter))
        ax.get_yaxis().set_major_formatter(FuncFormatter(plotNumberFormatter))
        # Plot the legend
        leg = ax.legend(loc       = loc ,\
                        fancybox  = True,\
                        numpoints = 1   ,\
                        )
        leg.get_frame().set_alpha(0.5)
        # Plot the grid
        ax.grid()
        # Make sure no collision between the ticks
        ax.xaxis.set_major_locator(MaxNLocator(prune=xprune))
        ax.yaxis.set_major_locator(MaxNLocator(prune=yprune))
    #}}}

    #{{{savePlot
    def savePlot(self, fig, fileName, extraArtists=None):
        """
        Saves the figure

        Parameters
        ----------
        fig: figure
            The figure.
        fileName : str
            Full path of the plot.
        extraArtist : tuple
            Tuple of bbox_extra_artists to be saved
        """

        fig.savefig(fileName,\
                    transparent = True             ,\
                    bbox_inches = "tight"          ,\
                    bbox_extra_artists=extraArtists,\
                    pad_inches  = 0                ,\
                    )

        print("Saved to {}".format(fileName))
    #}}}


    #{{{physicalUnitsConverter
    def physicalUnitsConverter(self, var, varName):
        #{{{docstring
        """
        Calculates physical parameters from the normalized if
        convertToPhysical is set. Returns the units.

        Parameters
        ----------
        var : array
            The variable.
        varName : str
            Name of the variable.

        Returns
        -------
        var : array
            The variable after eventual processing.
        normalization : str
            The normalization which will be plotted. Does not contain $ for
            LaTeX. An empty string is returned if convertToPhysical is True.
        units : str
            The units which will be plotted. Does not contains $ for
            LaTeX. An empty string is returned if convertToPhysical is False.
        """
        #}}}

        if self.convertToPhysical:
            normalization = ""
            # Calculate back to physical units
            if varName == "n":
                var *= self._convDict["n0"]
                units = r"\mathrm{m}^{-3}"
            elif varName == "vort":
                var *= self._convDict["omCI"]
                units = r"\mathrm{s}^{-1}"
            elif varName == "vortD":
                var *= self._convDict["omCI"]*\
                       self._convDict["n0"]
                units = r"\mathrm{m}^{-3}\mathrm{s}^{-1}"
            elif varName == "phi":
                var *= self._convDict["Te0"]/cst.e
                units = r"\mathrm{J}\mathrm{C}^{-1}"
            elif varName == "jPar":
                var *= cst.e*\
                    self._convDict["rhoS"]*\
                    self._convDict["omCI"]*\
                    self._convDict["n0"]
                units = r"\mathrm{C}\mathrm{s}^{-1}"
            elif varName == "momDensPar":
                # momDensPar is divided by m_i, so we need to multiply
                # by m_i again here
                var *= cst.m_p*\
                    self._convDict["rhoS"]*\
                    self._convDict["omCI"]*\
                    self._convDict["n0"]
                units = r"\mathrm{kg }\mathrm{m}^{-2}\mathrm{s}^{-1}"
            elif varName == "uIPar":
                var *= self._convDict["rhoS"]*\
                       self._convDict["omCI"]
                units = r"\mathrm{ms}^{-1}"
            elif varName == "uEPar":
                var *= self._convDict["rhoS"]*\
                       self._convDict["omCI"]
                units = r"\mathrm{ms}^{-1}"
                # Generic for velocities
            elif varName == "u":
                var *= self._convDict["rhoS"]*\
                       self._convDict["omCI"]
                units = r"\mathrm{ms}^{-1}"
            elif varName == "S":
                var *= self._convDict["omCI"]*\
                       self._convDict["n0"]
                units = r"\mathrm{m}^{-3}\mathrm{s}^{-1}"
            elif varName == "t":
                var /= self._convDict["omCI"]
                units = r"\mathrm{s}"
            elif varName == "rho":
                var *= self._convDict["rhoS"]
                units = r"\mathrm{m}"
            elif varName == "z":
                var *= self._convDict["rhoS"]
                units = r"\mathrm{m}"
            elif "EE" in varName:
                # NOTE: The masses are not included in the integral
                var *= cst.m_e*\
                       self._convDict["n0"]*\
                       (self._convDict["rhoS"]*self._convDict["omCI"])**2*\
                       (self._convDict["rhoS"])**3
                units = r"\mathrm{kgm}^2\mathrm{s}^{-2}"
            elif "EI" in varName:
                # NOTE: The masses are not included in the integral
                var *= cst.m_p*\
                       self._convDict["n0"]*\
                       (self._convDict["rhoS"]*self._convDict["omCI"])**2*\
                       (self._convDict["rhoS"])**3
                units = r"\mathrm{kgm}^2\mathrm{s}^{-2}"
            else:
                units = " "
        else:
            units = ""
            # Return normalization
            if varName == "n":
                normalization = r"/n_0"
            elif varName == "vort":
                normalization = r"/\omega_{{ci}}"
            elif varName == "vortD":
                normalization = r"/\omega_{{ci}}n_0"
            elif varName == "phi":
                normalization = r" q/T_{{e,0}}"
            elif varName == "jPar":
                normalization = r"/n_0c_sq"
            elif varName == "momDensPar":
                normalization = r"/m_in_0c_s"
            elif varName == "uIPar":
                normalization = r"/c_s"
            elif varName == "uEPar":
                normalization = r"/c_s"
            elif varName == "S":
                normalization = r"/\omega_{{ci}}n_0"
            elif varName == "t":
                normalization = r"\omega_{{ci}}"
            elif varName == "rho":
                normalization = r"/\rho_s"
            elif varName == "z":
                normalization = r"/\rho_s"
            elif "EE" in varName:
                # NOTE: The masses are not included in the integral
                var *= cst.m_e/cst.m_p
                normalization = r"/m_in_0c_s^2\rho_s^3"
            elif "EI" in varName:
                # NOTE: The masses are not included in the integral
                normalization = r"/m_in_0c_s^2\rho_s^3"
            else:
                normalization = " "

        return var, normalization, units
    #}}}
#}}}