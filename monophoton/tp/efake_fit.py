#!/usr/bin/env python

import sys
import os
import array
import math
import shutil

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
import config
import utils
from datasets import allsamples
from tp.efake_conf import skimConfig, lumiSamples, outputName, outputDir, roofitDictsDir, getBinning, itune, fitBinningT, dataSource, tpconfs
import tp.efake_plot as efake_plot

dataType = sys.argv[1] # "data" or "mc"
binningName = sys.argv[2] # see efake_conf

fitBins = getBinning(binningName)[2]

lumi = sum(allsamples[s].lumi for s in lumiSamples)

efake_plot.lumi = lumi
efake_plot.plotDir = outputName + '/fit_' + binningName

sys.argv = []

import ROOT
ROOT.gROOT.SetBatch(True)

# ROOT.gSystem.Load('libRooFit.so')
ROOT.gROOT.LoadMacro(basedir + '/../common/MultiDraw.cc+')
ROOT.gSystem.Load(roofitDictsDir + '/libCommonRooFit.so') # defines KeysShape

### Files ###

inputName = outputDir + '/fittemplates_' + dataType + '_' + binningName + '.root'

tmpInName = '/tmp/' + os.environ['USER'] + '/efake/' + os.path.basename(inputName)
try:
    os.makedirs(os.path.dirname(tmpInName))
except OSError:
    pass

if os.path.exists(inputName):
    # copy input to local area
    shutil.copy(inputName, tmpInName)

inputFile = ROOT.TFile.Open(tmpInName, 'READ')

outputName = outputDir + '/fityields_' + dataType + '_' + binningName + '.root'

tmpOutName = '/tmp/' + os.environ['USER'] + '/efake/' + os.path.basename(outputName)
try:
    os.makedirs(os.path.dirname(tmpOutName))
except OSError:
    pass

if os.path.exists(outputName):
    # make a backup
    shutil.copy(outputName, outputName.replace('.root', '_old.root'))

outputFile = ROOT.TFile.Open(tmpOutName, 'RECREATE')

### Setup ###

print 'Starting common setup.'

fitBinning = ROOT.RooUniformBinning(fitBinningT[1], fitBinningT[2], fitBinningT[0])
compBinning = ROOT.RooUniformBinning(60., 120., 60)

initVals = {
    'nbkg': 100.,
    'nsignal': 100.
}
if dataType == 'data':
    initVals.update({
        'mZ': 91.2,
        'gammaZ': 2.5,
        'm0': 0.,
        'sigma': 1.,
        'alpha': 2.,
        'n': 1.5
    })

# template of templates. used in both runModes
template = ROOT.TH1D('template', '', *fitBinningT)

# workspace
work = inputFile.Get('work')

if dataType == 'data':
    mcSource = ROOT.TFile.Open(outputDir + '/fityields_mc_' + binningName + '.root')
    mcWork = mcSource.Get('work')

# convenience
def addToWS(obj):
    fcn = getattr(work, 'import')
    if obj.InheritsFrom(ROOT.RooAbsData.Class()):
        # need a dummy argument to execute the correct overload
        fcn(obj, ROOT.RooFit.Rename(obj.GetName()))
    else:
        fcn(obj, ROOT.RooFit.Silence())

mass = work.var('mass')
mass.setBinning(compBinning, 'compWindow')

weight = work.var('weight')
ntarg = work.var('ntarg') # effective number of entries (differs from htarg integral in MC)
nbkg = work.var('nbkg')
nsignal = work.var('nsignal')
nZ = work.var('nZ')
mZ = work.var('mZ')
gammaZ = work.var('gammaZ')
m0 = work.var('m0')
sigma = work.var('sigma')
alpha = work.var('alpha')
n = work.var('n')

tpconf = work.arg('tpconf')
binName = work.arg('binName')

# smearing parameters are unused in dataType == mc but we'll just leave them here
nompset = ROOT.RooArgSet(tpconf, binName, ntarg, nbkg, nsignal, nZ, mZ, gammaZ)
nompset.add(m0)
nompset.add(sigma)
nompset.add(alpha)
nompset.add(n)
altsigpset = ROOT.RooArgSet(tpconf, binName, nbkg, nsignal, mZ, gammaZ)
altbkgpset = ROOT.RooArgSet(tpconf, binName, nbkg, nsignal, mZ, gammaZ, m0)
altbkgpset.add(sigma)
altbkgpset.add(alpha)
altbkgpset.add(n)

nomparams = ROOT.RooDataSet('params_nominal', 'Nominal params', nompset)
altsigparams = ROOT.RooDataSet('params_altsig', 'Altsig params', altsigpset)
altbkgparams = ROOT.RooDataSet('params_altbkg', 'Altbkg params', altbkgpset)

print 'Finished common setup.'

### Run fits ###

# fit variables
massset = ROOT.RooArgSet(mass) # for convenience
masslist = ROOT.RooArgList(mass) # for convenience

for bin, _ in fitBins:
    print 'Run fits for', bin

    binName.setLabel(bin)

    sigModelName = 'sigModel_' + bin
    sigDataName = 'sigData_' + bin

    if dataSource == 'sph':
        altsigModel = work.factory('BreitWigner::altsigModel_{bin}(mass, mZ, gammaZ)'.format(bin = bin))

    elif dataSource == 'sel' or dataSource == 'smu':
        # get signal template
        if dataType == 'mc':
            hsig = inputFile.Get('sig_' + bin)

            sigData = ROOT.RooDataHist('sigData_' + bin, 'sig', masslist, hsig)

        elif dataType == 'data':
            sigData = mcWork.data(sigDataName)
            if not sigData:
                print 'No dataset ' + sigDataName + ' found in ' + mcSource.GetName() + '.'
                sys.exit(1)

        # no smearing
        addToWS(sigData)
        altsigModel = work.factory('HistPdf::altsigModel_{bin}({{mass}}, sigData_{bin}, 2)'.format(bin = bin))

    addToWS(altsigModel)

    res = work.factory('CBShape::res_{bin}(mass, m0, sigma, alpha, n)'.format(bin = bin))
    sigModel = work.factory('FCONV::sigModel_{bin}(mass, altsigModel_{bin}, res_{bin})'.format(bin = bin))
    addToWS(sigModel)

    print 'Made sigModel_' + bin

    intComp = sigModel.createIntegral(massset, 'compWindow')
    intFit = sigModel.createIntegral(massset, 'fitWindow')

    for conf in tpconfs:
        tpconf.setLabel(conf)

        suffix = conf + '_' + bin

        htarg = inputFile.Get('target_' + suffix)
        print 'htarg limits:', htarg.GetXaxis().GetXmin(), htarg.GetXaxis().GetXmax(), htarg.GetSumOfWeights()
        outputFile.cd()
        htarg.Write()
        inputFile.cd()

        if dataType == 'mc':
            ntarg.setVal(math.pow(htarg.GetSumOfWeights(), 2.) / sum(htarg.GetSumw2()[iBin] for iBin in range(1, htarg.GetNbinsX() + 1)))
        else:
            ntarg.setVal(htarg.GetSumOfWeights())
        
        targHist = ROOT.RooDataHist('target_' + suffix, 'target', masslist, htarg)
        targ = targHist

# unbinned fit
#        ttarg = inputFile.Get(targName)
#        if dataType == 'mc':
#            targ = ROOT.RooDataSet(targName, 'target', ttarg, ROOT.RooArgSet(mass, weight), '', 'weight')
#        else:
#            targ = ROOT.RooDataSet(targName, 'target', ttarg, ROOT.RooArgSet(mass))

        addToWS(targ)

        print 'Made target_' + suffix

        ### Make muon+probe background template - this is not the actual background template (see below)
        tMuBkg = inputFile.Get('mubkgtree_' + suffix)
        if tMuBkg.GetEntries() < 50000.:
            print 'Making mubkg from mubkgtree'

            mubkgModel = ROOT.KeysShape('mubkgModel_' + suffix, 'mubkgModel', mass, tMuBkg, 'weight', 0.5, 8)
            
            hMuBkg = mubkgModel.createHistogram('mubkg', mass, ROOT.RooFit.Binning(fitBinning))
            hMuBkg.SetName('mubkg_' + suffix)
        else:
            print 'Making mubkg from mubkg histogram'

            hMuBkg = inputFile.Get('mubkg_' + suffix)
            dMuBkg = ROOT.RooDataHist('dmubkg_' + suffix, 'mubkg', masslist, hMuBkg)
            addToWS(dMuBkg)

            mubkgModel = work.factory('HistPdf::mubkgModel_{suffix}({{mass}}, dmubkg_{suffix}, 2)'.format(suffix = suffix))

        addToWS(mubkgModel)

        outputFile.cd()
        hMuBkg.SetDirectory(outputFile)
        hMuBkg.Write()

        ### Make electron+probe background template
        elbkgModel = None
        hElBkg = None
        if dataType == 'mc':
            tElBkg = inputFile.Get('truebkgtree_' + suffix)
            if tElBkg.GetEntries() < 50000.:
                print 'Making elbkg from truebkgtree'

                elbkgModel = ROOT.KeysShape('elbkgModel_' + suffix, 'elbkgModel', mass, tElBkg, 'weight', 0.5, 8)

                hElBkg = elbkgModel.createHistogram('elbkg', mass, ROOT.RooFit.Binning(fitBinning))
                hElBkg.SetName('elbkg_' + suffix)
            else:
                print 'Making elbkg from elbkg histogram'

                hElBkg = inputFile.Get('truebkg_' + suffix).Clone('elbkg_' + suffix)
                dElBkg = ROOT.RooDataHist('delbkg_' + suffix, 'elbkg', masslist, hElBkg)
                addToWS(dElBkg)

                elbkgModel = work.factory('HistPdf::elbkgModel_{suffix}({{mass}}, delbkg_{suffix}, 2)'.format(suffix = suffix))

            addToWS(elbkgModel)
            outputFile.cd()
            hElBkg.SetDirectory(outputFile)
            hElBkg.Write()

        ### set up bkg templates
        altbkgModel = None
        nombkgModel = None
        if conf in ['pass', 'fail']:
            altbkgModel = work.factory('Polynomial::altbkgModel_{suffix}(mass, a_1[0.1, 0., 1.])'.format(suffix = suffix))
            addToWS(altbkgModel)

            nombkgModel = mubkgModel.clone('nombkgModel_' + suffix)
            addToWS(nombkgModel)            

        elif conf in ['ee', 'eg']:
            altbkgModel = mubkgModel.clone('altbkgModel_' + suffix)
            addToWS(altbkgModel)

            if dataType == 'data':                
                scalePdf = mcWork.pdf('elmuscale_' + suffix)
                addToWS(scalePdf)
                
            elif dataType == 'mc':
                hMuBkg.Scale(1. / hMuBkg.GetSumOfWeights())
                hElBkg.Scale(1. / hElBkg.GetSumOfWeights())

                outputFile.cd()
                elmuscale = hElBkg.Clone('elmuscale_' + suffix)
                elmuscale.Divide(hMuBkg)

                elmuscale.Write()

                scaleHist = ROOT.RooDataHist('elmuscaleData_' + suffix, 'elmuscale', masslist, elmuscale)
                scalePdf = ROOT.RooHistPdf('elmuscale_' + suffix, 'elmuscale', massset, scaleHist, 2)
                addToWS(scaleHist)
                addToWS(scalePdf)

            nombkgModel = work.factory('PROD::nombkgModel_{suffix}(mubkgModel_{suffix}, elmuscale_{suffix})'.format(suffix = suffix))
            addToWS(nombkgModel)

            hNomBkg = nombkgModel.createHistogram('nombkg', mass, ROOT.RooFit.Binning(fitBinning))
            hNomBkg.SetName('nombkg_' + suffix)
            outputFile.cd()
            hNomBkg.SetDirectory(outputFile)
            hNomBkg.Write()

        print 'Made bkgModel_' + suffix

        # full fit PDF
        model = work.factory('SUM::model_{suffix}(nbkg * nombkgModel_{suffix}, nsignal * sigModel_{bin})'.format(suffix = suffix, bin = bin))
        addToWS(model)

        print 'Made model_' + suffix

        if dataType == 'mc':
            hTrueBkg = inputFile.Get('truebkg_' + suffix)
            hTrueSig = inputFile.Get('truesig_' + suffix)
            outputFile.cd()
            hTrueBkg.Write()
            hTrueSig.Write()
            inputFile.cd()
        else:
            hTrueBkg = None

        # nominal fit
        mZ.setConstant()
        gammaZ.setConstant()

        for vname, val in initVals.items():
            work.var(vname).setVal(val)
        nsignal.setVal(targ.sumEntries() * 0.9)
    
        model.fitTo(targ, ROOT.RooFit.SumW2Error(True), ROOT.RooFit.Save(True))

        nZ.setVal(nsignal.getVal() * (intComp.getVal() / intFit.getVal()))

        print '################ nZ =', nZ.getVal(), '###################'

        nomparams.add(nompset)

        efake_plot.plotFit(mass, targHist, model, dataType, suffix, hmcbkg = hTrueBkg, alt = '')

        if dataSource == 'smu':
            continue
   
        # altbkg fit
        model = work.factory('SUM::model_altbkg_{suffix}(nbkg * altbkgModel_{suffix}, nsignal * sigModel_{bin})'.format(suffix = suffix, bin = bin))

        for vname, val in initVals.items():
            work.var(vname).setVal(val)
        nsignal.setVal(targ.sumEntries() * 0.9)
    
        model.fitTo(targ, ROOT.RooFit.SumW2Error(True), ROOT.RooFit.Save(True))

        altbkgparams.add(altbkgpset)

        efake_plot.plotFit(mass, targHist, model, dataType, suffix, bkgModel = 'altbkgModel', hmcbkg = hTrueBkg, alt = 'altbkg')

        if dataType == 'data':
            # altsig fit
            mZ.setConstant(False)
            gammaZ.setConstant(False)
    
            model = work.factory('SUM::model_altsig_{suffix}(nbkg * nombkgModel_{suffix}, nsignal * altsigModel_{bin})'.format(suffix = suffix, bin = bin))
    
            for vname, val in initVals.items():
                work.var(vname).setVal(val)
            nsignal.setVal(targ.sumEntries() * 0.9)
        
            model.fitTo(targ, ROOT.RooFit.SumW2Error(True), ROOT.RooFit.Save(True))
    
            altsigparams.add(altsigpset)
    
            efake_plot.plotFit(mass, targHist, model, dataType, suffix, hmcbkg = hTrueBkg, alt = 'altsig')

addToWS(nomparams)
addToWS(altsigparams)
addToWS(altbkgparams)

outputFile.cd()
work.Write()

work = None
outputFile.Close()

shutil.copy(tmpOutName, outputName)
