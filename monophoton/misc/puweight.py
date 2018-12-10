#!/usr/bin/env python

import sys
import os
import importlib
import ROOT

mcConfs = [
    ('2016_25ns_SpringMC_PUScenarioV1_PoissonOOTPU', 'PUSpring16'),
    ('2016_25ns_Moriond17MC_PoissonOOTPU', 'PUMoriond17'),
    ('2017_25ns_WinterMC_PUScenarioV1_PoissonOOTPU', 'PU2017')
]

dataSource = ROOT.TFile.Open(sys.argv[2])
if not dataSource:
    sys.exit(1)

outputFile = ROOT.TFile.Open(sys.argv[1], 'recreate')

dataDist = dataSource.Get('pileup').Clone('data')
dataDist.Scale(1. / dataDist.GetSumOfWeights())

dataDist.Write()

for mcScenario, scenarioName in mcConfs:
    mix = importlib.import_module('SimGeneral.MixingModule.mix_' + mcScenario + '_cfi').mix
    npvs = mix.input.nbPileupEvents.probFunctionVariable.value() # list of integers
    probs = mix.input.nbPileupEvents.probValue.value() # list of floats

    gr = ROOT.TGraph(len(npvs) + 1)
    for i in range(len(npvs)):
        gr.SetPoint(i, float(npvs[i]), probs[i])
    gr.SetPoint(len(npvs), npvs[-1] + 1., 0.)
    
    mcDist = ROOT.TH1D(scenarioName, '', dataDist.GetNbinsX(), 0., dataDist.GetXaxis().GetXmax())
    mcDist.Sumw2()
    
    for bin in range(1, mcDist.GetNbinsX() + 1):
        # assuming bin boundaries are always integers (i.e. there is no graph kink within the bin), we can Eval the graph and compute the area of the trapezoid
        xmin = mcDist.GetXaxis().GetBinLowEdge(bin)
        xmax = mcDist.GetXaxis().GetBinUpEdge(bin)
        ymin = gr.Eval(xmin)
        ymax = gr.Eval(xmax)
        mcDist.SetBinContent(bin, (ymin + ymax) * (xmax - xmin) * 0.5)
    
    mcDist.Scale(1. / mcDist.GetSumOfWeights())
    
    for bin in range(1, mcDist.GetNbinsX() + 1):
        mcDist.SetBinError(bin, 0.)

    mcDist.Write()

    puweight = dataDist.Clone('puweight_' + scenarioName)
    
    puweight.Divide(mcDist)
    
    for bin in range(1, puweight.GetNbinsX() + 1):
        puweight.SetBinError(bin, 0.)
        # HACK
        if puweight.GetBinContent(bin) > 4.:
            puweight.SetBinContent(bin, 4.)
    
    puweight.Write()

outputFile.Close()
