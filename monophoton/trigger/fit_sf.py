import os
import sys

from datasets import allsamples
from plotstyle import SimpleCanvas
import config
import utils

import ROOT

canvas = SimpleCanvas()
canvas.legend.setPosition(0.7, 0.3, 0.9, 0.5)

#source = ROOT.TFile(config.histDir + '/trigger/scalefactor_photon_selBCD_dy.root')
#source = ROOT.TFile(config.histDir + '/trigger/scalefactor_photon_ph75_mcph75.root')
source = ROOT.TFile(config.histDir + '/trigger/scalefactor_vbf_selBCD_wlnu.root')

#graph = source.Get('ph75r9iso_ptwide')
graph = source.Get('vbf_mjj')

#func = ROOT.TF1('line', '[0] + [1] * x', 80., 600.)
func = ROOT.TF1('line', '[0]', 550., 1000.)
#func.SetParameters(0.98, 0.)
func.SetParameters(0.98)

graph.Fit(func)

graph.Draw('AEP')


