#!/usr/bin/env python

"""
Comparison of radial current balance.
"""

import pickle
import matplotlib.pylab as plt
import numpy as np
import scipy.constants as cst
from boututils.options import BOUTOptions

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../../../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPy.plotHelpers import (SizeMaker,\
                                 PlotHelper,\
                                 plotNumberFormatter,\
                                 seqCMap3)

#{{{Collect normalization and title from nnScan
nn = 9.9e+20
path = "../../CSDXNeutralScanAr/visualizationNormalized/nn_{}/field1D/jPar-radial-1D-0.pickle".format(nn)
with open(path, "rb") as f:
    fig = pickle.load(f)

axes = fig.get_axes()

for ax in axes[:-1]:
    fig.delaxes(ax)

oldNnAx = axes[-1]

# Convert to physical
inputFileOpts = BOUTOptions("../../CSDXNeutralScanAr")
n0  = eval(inputFileOpts.input["n0"])
Te0 = eval(inputFileOpts.input["Te0"])*cst.e
B0  = eval(inputFileOpts.input["B0"])
if inputFileOpts.input["gas"] != "Ar":
    raise ValueError("This routine is only made for Ar gas")

mi  = 39.948*cst.u
e   = cst.e

omCI = e*B0/mi
cS   = np.sqrt(Te0/mi)
rhoS = cS/omCI

# From normalization of parallel current equation
factor = omCI*n0*e*cS

# Obtain the suptitle
suptitle = fig.texts[0].get_text()

# Close the figure
plt.close(fig)
#}}}

# Make new ax to plot to
fig, (normalAx ,nnAx) = plt.subplots(ncols=2,\
                                    figsize = SizeMaker.array(2,1, aSingle=0.5))
size = "large"

#{{{Extract and plot nn
# Find the min and the max
maxmin = []
for line in oldNnAx.get_lines():
    x, y = line.get_data()
    x *= rhoS
    y *= factor
    maxmin.append((np.max(y), np.min(y)))
    nnAx.plot(x,y, color=line.get_color())

# Set the texts
maxInd = np.argmax(tuple(curVal[0] for curVal in maxmin))
minInd = np.argmin(tuple(curVal[1] for curVal in maxmin))

boltzmann   = nnAx.get_lines()[minInd]
resistivity = nnAx.get_lines()[maxInd]

boltzmannTxt = r"$\mu n\partial_{\parallel}\left(T_e \ln(n) - \phi \right)$"
nnAx.text(0.04, -2e10, boltzmannTxt, color=boltzmann.get_color(),\
           va="center", ha="center", size=size,\
           bbox={"facecolor":"white",\
                 "edgecolor":"none" ,\
                 "boxstyle" :"round",\
                 "alpha"    :0.9},\
           )

resTxt = r"$n\nu_{en}u_{e,\parallel}$"
nnAx.text(0.04, 2e10, resTxt, color=resistivity.get_color(),\
           va="center", ha="center", size=size,\
           bbox={"facecolor":"white",\
                 "edgecolor":"none" ,\
                 "boxstyle" :"round",\
                 "alpha"    :0.9},\
           )

ddtTxt = r"$\partial_t j_\parallel$"
nnAx.text(0.04, 0, ddtTxt, color="k",\
           va="center", ha="center", size=size,\
           bbox={"facecolor":"white",\
                 "edgecolor":"none" ,\
                 "boxstyle" :"round",\
                 "alpha"    :0.9},\
           )

nnAx.set_xlabel(r"$\rho\;[\mathrm{m}]$")
nnAx.set_ylabel(r"$[\mathrm{C}\mathrm{m}^{-2}\mathrm{s}^{-2}]$")

# Create new title
nnAx.set_title(r"$d=1\%$")

PlotHelper.makePlotPretty(nnAx, legend=False, rotation=45)
#}}}

#{{{Extract and plot no neutral
nn = 0
path = "../../CSDXMagFieldScanAr/visualizationNormalized/B0_0.06/field1D/jPar-radial-1D-0.pickle"
with open(path, "rb") as f:
    normalFig = pickle.load(f)

axes = normalFig.get_axes()

for ax in axes[:-1]:
    normalFig.delaxes(ax)

noNeutralAx = axes[-1]

# Find the min and the max
maxmin = []
for line in noNeutralAx.get_lines():
    x, y = line.get_data()
    x *= rhoS
    y *= factor
    maxmin.append((np.max(y), np.min(y)))
    normalAx.plot(x,y, color=line.get_color())

# Set the texts
maxInd = np.argmax(tuple(curVal[0] for curVal in maxmin))
minInd = np.argmin(tuple(curVal[1] for curVal in maxmin))

boltzmann   = normalAx.get_lines()[minInd]
resistivity = normalAx.get_lines()[maxInd]

boltzmannTxt = r"$\mu n\partial_{\parallel}\left(T_e \ln(n) - \phi \right)$"
normalAx.text(0.045, -1.8e9, boltzmannTxt, color=boltzmann.get_color(),\
           va="center", ha="center", size=size,\
           bbox={"facecolor":"white",\
                 "edgecolor":"none" ,\
                 "boxstyle" :"round",\
                 "alpha"    :0.9},\
           )

resTxt = r"$-0.51 \nu_{ei}j_{\parallel}$"
normalAx.text(0.06, 1.8e9, resTxt, color=resistivity.get_color(),\
           va="center", ha="center", size=size,\
           bbox={"facecolor":"white",\
                 "edgecolor":"none" ,\
                 "boxstyle" :"round",\
                 "alpha"    :0.9},\
           )

ddtTxt = r"$\partial_t j_\parallel$"
normalAx.text(0.015, 0, ddtTxt, color="k",\
           va="center", ha="center", size=size,\
           bbox={"facecolor":"white",\
                 "edgecolor":"none" ,\
                 "boxstyle" :"round",\
                 "alpha"    :0.9},\
           )

normalAx.set_xlabel(r"$\rho\;[\mathrm{m}]$")
normalAx.set_ylabel(r"$[\mathrm{C}\mathrm{m}^{-2}\mathrm{s}^{-2}]$")

# Create new title
normalAx.set_title(r"$d=100\%$")

PlotHelper.makePlotPretty(normalAx, legend=False, rotation=45)
#}}}

# Create new title
theSplit = suptitle.split("=")
rho = float(theSplit[1].split("$")[2])*rhoS
t   = eval(theSplit[-1].split("$")[2].\
           replace("{","").replace("}","").replace("\\cdot 10^","e"))/omCI

fig.suptitle((r"$z={}\;\mathrm{{m}}\quad"
                 r"\theta=0^{{\circ}}\quad t={}\;\mathrm{{s}}$").\
        format(plotNumberFormatter(rho,0).replace("$",""),\
               plotNumberFormatter(t,0)  .replace("$","")\
        ),
        y = 1.15
        )

fig.subplots_adjust(wspace=0.7)
PlotHelper.savePlot(fig, "jParBalanceNnCompareRad.pdf")