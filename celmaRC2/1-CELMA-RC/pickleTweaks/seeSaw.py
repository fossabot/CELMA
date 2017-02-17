#!/usr/bin/env python

"""
Creation of the see-saw comparison.
"""

import pickle
import matplotlib.pylab as plt
import numpy as np

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPy.plotHelpers import SizeMaker, PlotHelper, seqCMap3

nys = (16, 24, 32, 42, 50)
# Initialize jPar
jPar = {}

# Collect from ny scan
path = "../CSDXNyScan/visualizationPhysical/ny_{}/field1D/mainFields-parallel-1D-0.pickle"

for ny in nys:
    with open(path.format(ny), "rb") as f:
        fig = pickle.load(f)

    jPar[ny] = {}

    jParAx = fig.get_axes()[4]
    jPar[ny]["data"] = jParAx.get_lines()[0].get_data()
    jPar[ny]["leg"]  = r"$n_z = {}$".format(ny)
    plt.close(fig)

# Collect from fieldScan
path = "../CSDXMagFieldScanAr/visualizationPhysical/B0_0.06/field1D/mainFields-parallel-1D-0.pickle"
with open(path, "rb") as f:
    fig = pickle.load(f)

jParAx = fig.get_axes()[4]
data   = jParAx.get_lines()[0].get_data()
ny = len(data[0])
nys = list(nys)
nys.append(ny)
nys = tuple(nys)
jPar[ny] = {}
jPar[ny]["data"] = data
jPar[ny]["leg"]  = r"$n_z = {}$".format(ny)
plt.close(fig)

fig, ax = plt.subplots(figsize = SizeMaker.standard(w=4))

colors = seqCMap3(np.linspace(0, 1, len(nys)))

for ny, color in zip(nys, colors):
    ax.plot(jPar[ny]["data"][0], jPar[ny]["data"][1],\
            label = jPar[ny]["leg"], alpha =0.7,\
            color = color
            )

ax.set_xlabel(r"$z\;[\mathrm{m}]$")
ax.set_ylabel(r"$j_\| \;[\mathrm{Cm}^{-2}\mathrm{s}^{-1}]$")
PlotHelper.makePlotPretty(ax)
PlotHelper.savePlot(fig, "jParRipple.pdf")
