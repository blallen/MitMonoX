#!/usr/bin/env python

import sys
import os
import array
import math
import random
import collections

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
from datasets import allsamples
from plotstyle import SimpleCanvas
from tp.efake_conf import lumiSamples, outputName, outputDir, roofitDictsDir, getBinning, PRODUCT

dataType = sys.argv[1]
binningName = sys.argv[2]

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

source = ROOT.TFile.Open(outputDir + '/fityields_' + dataType + '_' + binningName + '.root')
work = source.Get('work')
nomparams = work.data('params_nominal')

uncSource = None
if os.path.exists(outputDir + '/tpsyst_' + dataType + '_' + binningName + '.root'):
    uncSource = ROOT.TFile.Open(outputDir + '/tpsyst_' + dataType + '_' + binningName + '.root')

if PRODUCT == 'frate':
    meas = ('ee', 'eg')
else:
    meas = ('pass', 'fail')

### Set up output

outputFile = ROOT.TFile.Open(outputDir + '/' + PRODUCT + '_' + dataType + '_' + binningName + '.root', 'recreate')

yields = dict((m, ROOT.TH1D(m, '', len(binning) - 1, array.array('d', binning))) for m in meas)
result = ROOT.TH1D(PRODUCT, '', len(binning) - 1, array.array('d', binning))
resultStatOnly = result.Clone(PRODUCT + 'StatOnly')

if dataType == 'mc':
    trueYields = dict((m, ROOT.TH1D(m + '_truth', '', len(binning) - 1, array.array('d', binning))) for m in meas)
    trueResult = ROOT.TH1D(PRODUCT + '_truth', '', len(binning) - 1, array.array('d', binning))

if binLabels:
    allhistograms = yields.values() + [result, resultStatOnly]
    if dataType == 'mc':
        allhistograms.extend(trueYields.values())
        allhistograms.append(trueResult)

    for h in allhistograms:
        for ibin in range(1, len(fitBins) + 1):
            h.GetXaxis().SetBinLabel(ibin, fitBins[ibin - 1][0])

### Compute

toydists = {}

staterrs = []
systerrs = []

for iBin, (bin, _) in enumerate(fitBins):
    stat2 = 0.

    toydists[bin] = {}

    sigshift = {}
    bkgshift = {}

    for conf in meas:
        suffix = conf + '_' + bin

        for ip in range(nomparams.numEntries()):
            nompset = nomparams.get(ip)
            if nompset.find('tpconf').getLabel() == conf and nompset.find('binName').getLabel() == bin:
                break
        else:
            raise RuntimeError('Nom pset for ' + suffix + ' not found')

        nZ = nompset.find('nZ').getVal()
        
        yields[conf].SetBinContent(iBin + 1, nZ)

        err2 = 0.
        sigshift[conf] = 0.
        bkgshift[conf] = 0.

        if uncSource:
            # compute uncertainties from distributions of nZ-normalized difference of toy yields

            toydist = uncSource.Get('pull_nominal_' + suffix)

            if not toydist:
                print 'No nominal pull distribution for ' + suffix
                sys.exit(1)

            toydists[bin][conf] = toydist

            err2 += math.pow(toydist.GetRMS() * nZ, 2.)
            stat2 += math.pow(toydist.GetRMS(), 2.)

            altsig = uncSource.Get('pull_altsig_' + suffix)
            altbkg = uncSource.Get('pull_altbkg_' + suffix)

            if altsig:
                sigshift[conf] = altsig.GetMean()
            if altbkg:
                bkgshift[conf] = altbkg.GetMean()
                
        err2 += math.pow(max(abs(sigshift[conf]), abs(bkgshift[conf])) * nZ, 2.)

        yields[conf].SetBinError(iBin + 1, math.sqrt(err2))

        if dataType == 'mc':
            hsig = source.Get('truesig_' + suffix)

            compBinning = work.var('mass').getBinning('compWindow')

            ilow = hsig.FindFixBin(compBinning.lowBound())
            ihigh = hsig.FindFixBin(compBinning.highBound())
            if compBinning.highBound() == hsig.GetXaxis().GetBinLowEdge(ihigh):
                ihigh -= 1

            integral = 0.
            err2 = 0.
            while ilow <= ihigh:
                integral += hsig.GetBinContent(ilow)
                err2 += math.pow(hsig.GetBinError(ilow), 2.)
                ilow += 1

            trueYields[conf].SetBinContent(iBin + 1, integral)
            trueYields[conf].SetBinError(iBin + 1, math.sqrt(err2))
            print conf, iBin, integral, math.sqrt(err2), math.sqrt(err2) / integral

            if not uncSource:
                stat2 += err2 / integral / integral

    ratio = yields[meas[1]].GetBinContent(iBin + 1) / yields[meas[0]].GetBinContent(iBin + 1)

    if PRODUCT == 'frate':
        central = ratio
    else:
        central = 1. / (1. + ratio)

    result.SetBinContent(iBin + 1, central)
    resultStatOnly.SetBinContent(iBin + 1, central)

    # re-evaluate shift uncertainties for ratios (cancels uncertainty if shape is correlated)
    sig = (1. + sigshift[meas[1]]) / (1. + sigshift[meas[0]])
    bkg = (1. + bkgshift[meas[1]]) / (1. + bkgshift[meas[0]])
    syst2 = math.pow(max(abs(sig - 1.), abs(bkg - 1.)), 2.)

    result.SetBinError(iBin + 1, central * math.sqrt(stat2 + syst2))
    resultStatOnly.SetBinError(iBin + 1, central * math.sqrt(stat2))

    staterrs.append(central * math.sqrt(stat2))
    systerrs.append(central * math.sqrt(syst2))

    if dataType == 'mc':
        larger = trueYields[meas[0]].GetBinContent(iBin + 1) # ee or pass
        smaller = trueYields[meas[1]].GetBinContent(iBin + 1) # eg or fail
        elarger = trueYields[meas[0]].GetBinError(iBin + 1)
        esmaller = trueYields[meas[1]].GetBinError(iBin + 1)

        if PRODUCT == 'frate':
            central = smaller / larger
        else:
            central = larger / (smaller + larger)

        trueResult.SetBinContent(iBin + 1, central)
        trueResult.SetBinError(iBin + 1, central * math.sqrt(math.pow(elarger / larger, 2.) + math.pow(esmaller / smaller, 2.)))

outputFile.cd()
result.Write()
resultStatOnly.Write()
yields[meas[0]].Write()
yields[meas[1]].Write()
if dataType == 'mc':
    trueResult.Write()
    trueYields[meas[0]].Write()
    trueYields[meas[1]].Write()

### Visualize

lumi = sum(allsamples[s].lumi for s in lumiSamples)


canvas = SimpleCanvas(lumi = lumi, sim = (dataType == 'mc'))
canvas.SetGrid(False, True)
canvas.legend.setPosition(0.7, 0.8, 0.9, 0.9)
if PRODUCT == 'frate':
    canvas.legend.add(PRODUCT, 'R_{e}', opt = 'LFP', mcolor = ROOT.kBlack, lcolor = ROOT.kBlack, fcolor = ROOT.kGray, mstyle = 8)
    canvas.ylimits = (0., 0.05)
else:
    canvas.legend.add(PRODUCT, '#epsilon_{e}', opt = 'LP', color = ROOT.kBlack, mstyle = 8)
    canvas.ylimits = (0.75, 1.)

if dataType == 'mc':
    canvas.legend.add(PRODUCT + '_truth', 'MC truth', opt = 'LP', color = ROOT.kGreen, mstyle = 4)
    canvas.legend.apply(PRODUCT + '_truth', trueResult)
    canvas.addHistogram(trueResult, drawOpt = 'EP')

canvas.legend.apply(PRODUCT, result)
canvas.legend.apply(PRODUCT, resultStatOnly)
canvas.addHistogram(result, drawOpt = 'EP')
canvas.addHistogram(resultStatOnly, drawOpt = 'E4')



if ADDFIT:
    contents = {}

    print result.GetBinContent(1), result.GetBinError(1)

    # exclude bins 42 < pT < 48
    ibin = result.FindFixBin(42.)
    while ibin <= result.FindFixBin(48.):
        contents[ibin] = (result.GetBinContent(ibin), result.GetBinError(ibin))
#        result.SetBinContent(ibin, 0.)
        result.SetBinError(ibin, 1.e+6)
        ibin += 1

    xmin = result.GetXaxis().GetXmin()
    xmax = result.GetXaxis().GetXmax()

    power = ROOT.TF1('power', '[0] + [1] * TMath::Power(x - [2], [3])', xmin, xmax)
    power.SetParameters(0.01, 1., 10., -1.)
    power.SetParLimits(0, 0.005, 0.03)
    power.SetParLimits(1, 0.01, 3.)
    power.SetParLimits(2, -500., 500.)
    power.SetParLimits(3, -5., 0.)
    result.Fit(power)
    canvas.addObject(power)

    outputFile.cd()
    power.Write(PRODUCT + '_fit')

    text = 'f = %.4f + %.3f#times(p_{T} ' % (power.GetParameter(0), power.GetParameter(1))
    if power.GetParameter(2) >= 0.:
        text += ' - '
    else:
        text += ' + '
    text += '%.2f)^{%.2f}' % (abs(power.GetParameter(2)), power.GetParameter(3))

    canvas.addText(text, 0.4, 0.15, 0.6, 0.2)

    for ibin, (cont, err) in contents.items():
        result.SetBinContent(ibin, cont)
        result.SetBinError(ibin, err)

    # Throw toys and get uncertainties
    # draw one normal parameter for total systematic (assume full correlation across bins)
    # draw one normal parameter per bin for statistical
    # 68% percentile on both sides become the up & down variations

    original = tuple(power.GetParameter(i) for i in range(power.GetNpar()))

    ntoys = 200
    npx = 100

    variations = []
    for _ in range(npx):
        variations.append([])

    power.SetNpx(npx)

    for _ in range(ntoys):
        toy = result.Clone('toy')
        toy.Reset()

        psyst = random.gauss(0., 1.)

        for iBin in range(result.GetNbinsX()):
            stat = staterrs[iBin]
            syst = systerrs[iBin]

            systShift = syst * psyst
            statShift = stat * random.gauss(0., 1.)

            toy.SetBinContent(iBin + 1, result.GetBinContent(iBin + 1) + systShift + statShift)
            toy.SetBinError(iBin + 1, math.sqrt(stat * stat + syst * syst))

        # power is cloned in addObject above - we can modify its parameters
        toy.Fit(power)

        gr = ROOT.TGraph(power)
        for ix in range(npx):
            variations[ix].append(gr.GetY()[ix])

    gup = ROOT.TGraph(npx)
    gdown = ROOT.TGraph(npx)

    power.SetParameters(*original)

    for ix, var in enumerate(variations):
        x = (power.GetXmax() - power.GetXmin()) / npx * ix + power.GetXmin()
        ynom = power.Eval(x)
        
        var.sort()
        iy = 0
        while iy < ntoys and var[iy] < ynom:
            iy += 1

        up = var[int((ntoys - iy) * 0.68 + iy)]
        down = var[int(iy * 0.32)]

        gup.SetPoint(ix, x, up)
        gdown.SetPoint(ix, x, down)

    gup.SetLineStyle(ROOT.kDashed)
    gup.SetLineColor(power.GetLineColor())
    gup.SetLineWidth(power.GetLineWidth())
    canvas.addHistogram(gup, drawOpt = 'CL')

    gdown.SetLineStyle(ROOT.kDashed)
    gdown.SetLineColor(power.GetLineColor())
    gdown.SetLineWidth(power.GetLineWidth())
    canvas.addHistogram(gdown, drawOpt = 'CL')

    outputFile.cd()
    gup.Write(PRODUCT + '_fitUp')
    gdown.Write(PRODUCT + '_fitDown')

canvas.xtitle = binningTitle
canvas.printWeb(outputName, PRODUCT + '_' + dataType + '_' + binningName, logy = False)

for iBin, (bin, _) in enumerate(fitBins):
    if dataType == 'mc':
        print '%15s [%.3f +- %.3f (stat.) +- %.3f (syst.)] x 10^{-2} (mc %.3f)' % (bin, result.GetBinContent(iBin + 1) * 100., staterrs[iBin] * 100., systerrs[iBin] * 100., trueResult.GetBinContent(iBin + 1) * 100.)
    else:
        print '%15s [%.3f +- %.3f (stat.) +- %.3f (syst.)] x 10^{-2}' % (bin, result.GetBinContent(iBin + 1) * 100., staterrs[iBin] * 100., systerrs[iBin] * 100.)

if uncSource:
    for conf in meas:
        for bin, _ in fitBins:
            canvas.Clear(full = True)
            canvas.ylimits = (0., 0.1)
            canvas.xtitle = '(N_{Z}^{toy}-N_{Z}^{orig})/N_{Z}^{orig}'
    
            canvas.legend.setPosition(0.7, 0.7, 0.9, 0.9)
            canvas.legend.add('toys', title = 'Toys', opt = 'LF', color = ROOT.kBlue - 7, lwidth = 2, fstyle = 3003)

            for ip in range(nomparams.numEntries()):
                nompset = nomparams.get(ip)
                if nompset.find('tpconf').getLabel() == conf and nompset.find('binName').getLabel() == bin:
                    break
            else:
                raise RuntimeError('Nom pset for ' + suffix + ' not found')

            nZ = nompset.find('nZ').getVal()

            toydist = toydists[bin][conf]
            toydist.Scale(1. / toydist.GetSumOfWeights())
    
            canvas.legend.apply('toys', toydist)
    
            canvas.printWeb(outputName + '/toys_' + binningName, dataType + '_' + conf + '_' + bin, logy = False)

outputFile.Close()
