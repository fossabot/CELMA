#!/usr/bin/env python

"""
Contains drivers for the probes
"""




# FIXME: Probably not need this







from .postProcessorDriver import PostProcessorDriver

#{{{StatsAndSignalsDrivers
class StatsAndSignalsDrivers(PostProcessorDriver):
    """
    Class which handles the stats and signal data.
    """

    #{{{Constructor
    def __init__(self                  ,\
                 *args                 ,\
                 paths           = None,\
                 **kwargs):
        #{{{docstring
        """
        This constructor:

        1. Calls the parent constructor
        2. Sets additional member data.

        Parameters
        ----------
        *args : positional arguments
            See the constructor of PostProcessorDriver for details.
        paths : sequence (not string)
            What folders to be investigated
        **kwargs : keyword arguments
            See the constructor of PostProcessorDriver for details.
        """
        #}}}

        # Call the constructor of the parent class
        super().__init__(*args, **kwargs)

        # Set member data
        self._paths   = paths
        self._pltSize = (12, 9)

        # Convert the paths (if only one of them)
        if self._scanParameters and len(self._dmp_folders) == 1:
            self._paths = tuple(self._convertToCurrentScanParameters(path)
                                for path in paths)
    #}}}
#}}}