#!/usr/bin/env python

import sys
import os
import array
import math
import collections
from subprocess import Popen, PIPE

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
from datasets import allsamples
from plotstyle import WEBDIR, SimpleCanvas
from tp.efake_conf import lumiSamples, outputName, outputDir, roofitDictsDir, getBinning

binningName = sys.argv[1]

ADDFIT = False

binningTitle, binning, fitBins = getBinning(binningName)

binLabels = False
if len(binning) == 0:
    binLabels = True
    binning = range(len(fitBins) + 1)

sys.argv = []

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gSystem.Load('libRooFit.so')
ROOT.gSystem.Load(roofitDictsDir + '/libCommonRooFit.so') # defines KeysShape

ROOT.gStyle.SetNdivisions(510, 'X')

dataSource = ROOT.TFile.Open(outputDir + '/eff_data_' + binningName + '.root')
mcSource = ROOT.TFile.Open(outputDir + '/eff_mc_' + binningName + '.root')

outputFile = ROOT.TFile.Open(outputDir + '/scaleFactor_' + binningName + '.root', 'RECREATE')

dataEff = dataSource.Get('eff')
mcEff = mcSource.Get('eff')
mcTruthEff = mcSource.Get('eff_truth')

scaleFactor = dataEff.Clone('scaleFactor')
scaleFactor.Divide(mcEff)

sfTruth = dataEff.Clone('sf_truth')
sfTruth.Divide(mcTruthEff)

outputFile.cd()
scaleFactor.Write()
sfTruth.Write()
dataEff.Write('dataEff')
mcEff.Write('mcEff')
mcTruthEff.Write('mcTruthEff')

### Visualize

lumi = sum(allsamples[s].lumi for s in lumiSamples)

# scaleFactor.SetMaximum(1.05)

canvas = SimpleCanvas(lumi = lumi)
canvas.SetGrid(False, False)
canvas.legend.setPosition(0.7, 0.8, 0.9, 0.9)


canvas.legend.add('sf', 'Fit', opt = 'LP', color = ROOT.kBlack, mstyle = 8)
canvas.legend.add('sf_truth', 'Truth', opt = 'LP', color = ROOT.kGreen, mstyle = 4)
canvas.ylimits = (0.95, 1.05)
canvas.ytitle = 'Scale Factor'

canvas.legend.apply('sf_truth', sfTruth)
canvas.addHistogram(sfTruth, drawOpt = 'EP')

canvas.legend.apply('sf', scaleFactor)
canvas.addHistogram(scaleFactor, drawOpt = 'EP')

if ADDFIT:
    flat = ROOT.TF1('flat', '[0]', scaleFactor.GetXaxis().GetXmin(), scaleFactor.GetXaxis().GetXmax())
    flat.SetParameter(0, 1.)
    flat.SetParLimits(0, 0.95, 1.05)

    sfTruth.Fit(flat)
    canvas.addObject(flat)

    linear = ROOT.TF1('linear', '[0] + [1] * x', scaleFactor.GetXaxis().GetXmin(), scaleFactor.GetXaxis().GetXmax())
    linear.SetParameters(1., 0.01)
    linear.SetParLimits(0, 0.95, 1.05)
    linear.SetParLimits(1, -0.0001, 0.0001)

    sfTruth.Fit(linear)
    canvas.addObject(linear)

    text = 'flat = %.3f #pm %.3f' % (flat.GetParameter(0), flat.GetParError(0))
    canvas.addText(text, 0.3, 0.25, 0.5, 0.2)

    text = 'line = %.6f + %.6f * p_{T}' % (linear.GetParameter(0), linear.GetParameter(1))
    canvas.addText(text, 0.3, 0.35, 0.5, 0.25)



canvas.xtitle = binningTitle
canvas.printWeb(outputName, 'scaleFactor_' + binningName, logy = False)

print 'Fit Results:'
for iBin, (bin, _) in enumerate(fitBins):
    print '%15s [%.3f +- %.3f]' % (bin, scaleFactor.GetBinContent(iBin + 1), scaleFactor.GetBinError(iBin + 1))

print '\nTruth Results:'
for iBin, (bin, _) in enumerate(fitBins):
    print '%15s [%.3f +- %.3f]' % (bin, sfTruth.GetBinContent(iBin + 1), sfTruth.GetBinError(iBin + 1))

outFileName = 'table_' + binningName + '.tex'
outDir = WEBDIR + '/' + outputName
outFilePath = outDir + '/' + outFileName
outFile = open(outFilePath, 'w')

outFile.write(r"\documentclass{article}")
outFile.write("\n")
outFile.write(r"\usepackage[paperwidth=115mm, paperheight=58mm, margin=5mm]{geometry}")
outFile.write("\n")
outFile.write(r"\begin{document}")
outFile.write("\n")
outFile.write(r"\pagenumbering{gobble}")
outFile.write("\n")

# table header based on ID
outFile.write(r"\begin{tabular}{ |c|c|c| }")
outFile.write("\n")
outFile.write(r"\hline")
outFile.write("\n")
outFile.write(r"\multicolumn{3}{ |c| }{Custom ID Scale Factor for high $p_{T}$ photons} \\")
outFile.write("\n")
outFile.write(r"\hline")
outFile.write("\n")

# column headers: | pT Range | nominal+/-unc | uncA uncB uncC uncD |
try:
    (var, unit) = binningTitle.split(' ')
    varString = ' $' + var + '$ ' + unit 
except:
    var = binningTitle
    varString = ' $' + var + '$ '

outFile.write(varString + r" & MC Fit & Truth \\") # \multicolumn{3}{ |c| }{Relative Uncertainty} \\")
# outFile.write("\n")
# outFile.write(r" (GeV) & & SF & Data Eff. & MC Eff \\")
outFile.write(r"\hline")
outFile.write("\n")

for iBin, (bin, _) in enumerate(fitBins):
    print bin
    print bin.split('_')
    (_, low, high) = bin.split('_')
    binString = ' (' + low + ', ' + high + ') '

    # fill in row with sf / uncertainty values properly
    nomString = '$%.3f \\pm %.3f$' % (scaleFactor.GetBinContent(iBin + 1), scaleFactor.GetBinError(iBin + 1))
    truthString = '$%.3f \\pm %.3f$' % (sfTruth.GetBinContent(iBin + 1), sfTruth.GetBinError(iBin + 1))
    # systString = '%.4f & %.4f & %.4f' % tuple([sf[1] / sf[0]] + list(sf[2:]))
    rowString = binString + ' & ' + nomString + ' & ' + truthString + r' \\'

    outFile.write(rowString)
    outFile.write('\n')

# end table
outFile.write(r"\hline")
outFile.write("\n")
outFile.write(r"\end{tabular}")
outFile.write("\n")

# end tex file
outFile.write(r"\end{document}")
outFile.close()

# convert tex to pdf
pdflatex = Popen( ["pdflatex",outFilePath,"-interaction nonstopmode"]
                  ,stdout=PIPE,stderr=PIPE,cwd=outDir)
pdfout = pdflatex.communicate()
print pdfout[0]
if not pdfout[1] == "":
    print pdfout[1]

# convert tex/pdf to png
convert = Popen( ["convert",outFilePath.replace(".tex",".pdf")
                  ,outFilePath.replace(".tex",".png") ]
                 ,stdout=PIPE,stderr=PIPE,cwd=outDir)
conout = convert.communicate()
print conout[0]
if not conout[1] == "":
    print conout[1]    

outputFile.Close()
