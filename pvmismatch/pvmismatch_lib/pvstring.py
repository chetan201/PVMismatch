# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 14:07:12 2012

@author: mmikofski
"""

import numpy as np
from copy import deepcopy
from matplotlib import pyplot as plt
# use absolute imports instead of relative, so modules are portable
from pvmismatch.pvmismatch_lib.pvconstants import PVconstants, NUMBERMODS
from pvmismatch.pvmismatch_lib.pvmodule import PVmodule


class PVstring(object):
    """
    PVstring - A class for PV strings.
    """

    def __init__(self, numberMods=NUMBERMODS, pvmods=None,
                 pvconst=PVconstants()):
        """
        Constructor
        """
        self.pvconst = pvconst
        self.numberMods = numberMods
        if pvmods is None:
            # use deepcopy instead of making each object in for-loop, 2x faster
            pvmods = PVmodule(pvconst=self.pvconst)
        if isinstance(pvmods, PVmodule):
            pvmods = [deepcopy(pvmods) for _ in xrange(self.numberMods)]
            # reset pvconsts in all pvcells and pvmodules
            for p in pvmods:
                for c in p.pvcells:
                    c.pvconst = self.pvconst
                p.pvconst = self.pvconst

        if len(pvmods) != self.numberMods:
            # TODO: use pvmismatch exceptions
            raise Exception("Number of modules doesn't match.")
        self.numberMods = len(pvmods)
        self.pvmods = pvmods
        self.Istring, self.Vstring, self.Pstring = self.calcString()

    @property
    def Imod(self):
        return np.array([mod.Imod.flatten() for mod in self.pvmods])

    @property
    def Vmod(self):
        return np.array([mod.Vmod.flatten() for mod in self.pvmods])

    def calcString(self):
        """
        Calculate string I-V curves.
        Returns (Istring, Vstring, Pstring) : tuple of numpy.ndarray of float
        """
        # Imod is already set to the range from Vrbd to the minimum current
        meanIsc = np.mean([pvmod.Isc.mean() for pvmod in self.pvmods])
        Istring, Vstring = self.pvconst.calcSeries(self.Imod, self.Vmod,
                                                   meanIsc, self.Imod.max())
        Pstring = Istring * Vstring
        return (Istring, Vstring, Pstring)

    def setSuns(self, Ee):
        """
        Set irradiance on cells in modules of string in system.
        If Ee is ...
        ... scalar, then sets the entire string to that irradiance.
        ... a dictionary, then each key refers to a module in the string,
        and the corresponding value are passed to
        :meth:`~pvmodules.PVmodules.setSuns()`

        Example::
        Ee={0: {'cells': (1,2,3), 'Ee': (0.9, 0.3, 0.5)}}  # set module 0
        Ee=0.91  # set all modules to 0.91 suns
        Ee={12: 0.77}  # set module with index 12 to 0.77 suns
        Ee={8: [0.23 (0, 1, 2)], 7: [(0.45, 0.35), (71, 72)]}

        :param Ee: irradiance [W/m^2]
        :type Ee: dict or float
        """
        if np.isscalar(Ee):
            for pvmod in self.pvmods:
                pvmod.setSuns(Ee)
        else:
            for pvmod, cell_Ee in Ee.iteritems():
                if hasattr(cell_Ee, 'keys'):
                    self.pvmods[pvmod].setSuns(**cell_Ee)
                else:
                    self.pvmods[pvmod].setSuns(*cell_Ee)
        # update modules
        self.Istring, self.Vstring, self.Pstring = self.calcString()

    def plotStr(self):
        """
        Plot string I-V curves.
        Returns strPlot : matplotlib.pyplot figure
        """
        strPlot = plt.figure()
        plt.subplot(2, 1, 1)
        plt.plot(self.Vstring, self.Istring)
        plt.title('String I-V Characteristics')
        plt.ylabel('String Current, I [A]')
        plt.ylim(ymin=0)
        plt.grid()
        plt.subplot(2, 1, 2)
        plt.plot(self.Vstring, self.Pstring)
        plt.title('String P-V Characteristics')
        plt.xlabel('String Voltage, V [V]')
        plt.ylabel('String Power, P [W]')
        plt.grid()
        return strPlot
