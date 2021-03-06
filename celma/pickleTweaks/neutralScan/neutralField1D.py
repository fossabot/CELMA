#!/usr/bin/env python

"""
Tweak of profile plots as a function of nn.
"""

import pickle
import matplotlib.pylab as plt
import matplotlib.lines as mlines
import numpy as np
from subprocess import Popen

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../../../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPy.plotHelpers import PlotHelper, seqCMap3

scans  = (\
          "nn_9.9e+20"              ,\
          "nn_4e+19"                ,\
          "nn_1.5e+19"              ,\
          "nn_6.666666666666668e+18",\
          "nn_2.5e+18"              ,\
         )
markers = ("*", "o", "s", "v", "^")
ls = (\
      (0, ()),\
      (0, (5, 5)),\
      (0, (3, 1, 1, 1)),\
      (0, (3, 1, 1, 1, 1, 1)),\
      (0, (1, 1)),\
     )
fields = ("n", "phi", "jPar", "om", "ui", "sA", "ue")

sD =\
    {s:{f:\
        {"ax":None,"line":None,"ls":l,"marker":m,"color":None}\
        for f in fields}\
    for s, m, l in zip(scans, markers, ls)}

for direction in ("radial", "parallel"):
    for scan in scans:
        folder = "../../CSDXNeutralScanAr/visualizationPhysical/{}/field1D".format(scan)
        picklePath = os.path.join(folder,\
                                  "mainFields-{}-1D-0.pickle".format(direction))
        with open(picklePath, "rb") as f:
            fig = pickle.load(f)

        lnAx, phiAx, nAx, omDAx, jParAx, omAx, uiAx, nuiAx, ueAx, sAx =\
                fig.get_axes()

        # Swap axes
        phiAx.set_position(omDAx.get_position())
        sAx  .set_position(nuiAx.get_position())

        fig.delaxes(lnAx)
        fig.delaxes(omDAx)
        fig.delaxes(nuiAx)

        # Modify title position
        t = fig.texts[0]
        pos = list(t.get_position())
        pos[1] = 0.75
        t.set_position(pos)
        t.set_va("bottom")

        # Color adjust
        axes = (nAx, phiAx, jParAx, omAx, uiAx, sAx, ueAx)
        colors = seqCMap3(np.linspace(0, 1, len(axes)))

        # Recolor the lines
        for ax, color in zip(axes, colors):
            line = ax.get_lines()[0]
            line.set_color(color)
            # NOTE: Using the designated setter gives a comparion error
            line._markerfacecolor = color
            line._markeredgecolor = color

        # Set the colors
        sD[scan]["n"]   ["color"] = colors[0]
        sD[scan]["phi"] ["color"] = colors[1]
        sD[scan]["jPar"]["color"] = colors[2]
        sD[scan]["om"]  ["color"] = colors[3]
        sD[scan]["ui"]  ["color"] = colors[4]
        sD[scan]["sA"]  ["color"] = colors[5]
        sD[scan]["ue"]  ["color"] = colors[6]

        # Set the lines
        sD[scan]["n"]   ["line"] = nAx   .get_lines()[0].get_data()[1]
        sD[scan]["phi"] ["line"] = phiAx .get_lines()[0].get_data()[1]
        sD[scan]["jPar"]["line"] = jParAx.get_lines()[0].get_data()[1]
        sD[scan]["om"]  ["line"] = omAx  .get_lines()[0].get_data()[1]
        sD[scan]["ui"]  ["line"] = uiAx  .get_lines()[0].get_data()[1]
        sD[scan]["sA"]  ["line"] = sAx   .get_lines()[0].get_data()[1]
        sD[scan]["ue"]  ["line"] = ueAx  .get_lines()[0].get_data()[1]

        xAxis = nAx.get_lines()[0].get_data()[0]

        # Clear the axes
        for ax in axes:
            ax.get_lines()[0].set_data((None,), (None,))

        sD[scan]["n"]   ["ax"] = nAx
        sD[scan]["phi"] ["ax"] = phiAx
        sD[scan]["jPar"]["ax"] = jParAx
        sD[scan]["om"]  ["ax"] = omAx
        sD[scan]["ui"]  ["ax"] = uiAx
        sD[scan]["sA"]  ["ax"] = sAx
        sD[scan]["ue"]  ["ax"] = ueAx

    # Plot
    for scan in scans:
        fig = sD[scans[0]]["n"]["ax"].figure
        for key in sD[scans[0]].keys():
            sD[scans[0]][key]["ax"].plot(xAxis,\
                                         sD[scan][key]["line"],\
                                         color     = sD[scan][key]["color"],\
                                         marker    = sD[scan][key]["marker"],\
                                         ms        = 5,\
                                         markevery = 7,\
                                         alpha     = 0.7,\
                                         ls        = sD[scan][key]["ls"],\
                                                 )
            sD[scans[0]][key]["ax"].autoscale(enable=True, axis="y", tight=True)

            # Put the legends on the y-axis
            handles, labels = sD[scans[0]][key]["ax"].get_legend_handles_labels()
            leg = sD[scans[0]][key]["ax"].legend()
            leg.remove()
            # Decrease fontsize by 1 to get some spacing
            sD[scans[0]][key]["ax"].set_ylabel(labels[0], fontsize=11)

    # Manually ajust the wspace as fig.subplots_adjust messes with the
    # spacing
    for key in ("phi", "om", "sA"):
        pos = sD[scans[0]][key]["ax"].get_position()
        pos = (pos.x0 + 0.05, pos.y0, pos.width, pos.height)
        sD[scans[0]][key]["ax"].set_position(pos)

    # Manually creating the legend
    handles = []

    # Used for conversion
    n0 = 1e19
    for scan in scans:
        curScan = n0/(n0+float(scan[3:]))*100
        label  = r"$d = {:d} \;\%$".format(int(curScan))
        handle = mlines.Line2D([], [],\
                       color  = "k"                    ,\
                       marker = sD[scan]["n"]["marker"],\
                       ls     = sD[scan]["n"]["ls"]    ,\
                       ms     = 5                      ,\
                       alpha  = 0.7                    ,\
                       label  =label)
        handles.append(handle)

    # Put legends outside
    sD[scans[0]]["ue"]["ax"].legend(handles=handles,\
                                    ncol=2,\
                                    bbox_to_anchor=(1.15, 0.25),\
                                    loc="upper left",\
                                    borderaxespad=0.,\
                                    bbox_transform =\
                                        sD[scans[0]]["ue"]["ax"].transAxes,\
                                    )

    if direction == "radial":
        fileName = "nnScanRad.pdf"
    elif direction == "parallel":
        fileName = "nnScanPar.pdf"

    PlotHelper.savePlot(fig, fileName)
