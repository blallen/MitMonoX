#!/usr/bin/env python

import os
import sys
import collections
import time
import ROOT

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)

if basedir not in sys.path:
    sys.path.append(basedir)

import purity.selections as s
from purity.plotiso import plotiso
from plotstyle import WEBDIR, SimpleCanvas, RatioCanvas

ROOT.gErrorIgnoreLevel = ROOT.kWarning

ROOT.gROOT.LoadMacro(s.thisdir + '/SignalSubtraction.cc+')
ssfitter = ROOT.SSFitter.singleton()

from ROOT import *
gROOT.SetBatch(True)
gStyle.SetOptStat(0)
RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)

QUICKFIT = False # just run one main fit
FORCEHIST = True # redraw input histograms
ITERATIVE = False # use iterative method instead of SignalSubtraction.cc
DOTOYS = True

### take inputs and make sure they match a selection
loc = sys.argv[1] # barrel, endcap
pid = sys.argv[2] # (loose|medium|tight)[-optional]
pt = sys.argv[3] # Inclusive, XtoY
met = sys.argv[4] # Inclusive, XtoY

try:
    tune = sys.argv[5]
except:
    tune = 'Spring16'

inputKey = tune+'_'+loc+'_'+pid+'_PhotonPt'+pt+'_Met'+met

if loc == 'barrel':
    iloc = 0
elif loc == 'endcap':
    iloc = 1
 
try:
    ptSel = s.PhotonPtSels['PhotonPt'+pt]
except KeyError:
    print 'Inputted pt range', pt, 'not found!'
    print 'Not applying any pt selection!'
    ptSel = '(1)'

try:
    metSel = s.MetSels['Met'+met]
except KeyError:
    print 'Inputted met range', met, 'not found!'
    print 'Not applying any met selection!'
    metSel = '(1)'

### Directory stuff so that results are saved and such
versDir = s.versionDir
plotDir = os.path.join('purity', s.Version, inputKey)
print WEBDIR + '/' + plotDir
histDir = os.path.join(versDir, inputKey)
print histDir
if not os.path.exists(WEBDIR + '/' + plotDir):
    os.makedirs(WEBDIR + '/' + plotDir)
if not os.path.exists(histDir):
    os.makedirs(histDir)

### Statics

ChIsoSbSels = {
    'ChIso50to80': (5., 8.),
    'ChIso20to50': (2., 5.),
    'ChIso80to110': (8., 11.),
    'ChIso35to50': (3.5, 5.),
    'ChIso50to75': (5., 7.5),
    'ChIso75to90': (7.5, 9.),
    'ChIso40to60': (4., 6.),
    'ChIso60to80': (6., 8.),
    'ChIso80to100': (8., 10.)
}

pids = pid.split('-')
pid = pids[0]
extras = pids[1:]

if pid == 'loose':
    ipid = 0
elif pid == 'medium':
    ipid = 1
elif pid == 'tight':
    ipid = 2
elif pid == 'highpt':
    ipid = 3

itune = s.Tunes.index(tune)

### Get ChIso Curve for true photons
if not QUICKFIT:
    print ''
    print 'Generating chIso histograms for SR-CR extrapolation..'
    print ''

    isoFile = TFile.Open(os.path.join(versDir, inputKey, 'chiso.root'))

    if FORCEHIST or not isoFile:
        plotiso(loc, '-'.join(pids), pt, met, tune)

        isoFile = TFile.Open(os.path.join(versDir, inputKey, 'chiso.root'))

    # SB / signal region transfer factor
    isoTF = {}
    
    for chkey in ChIsoSbSels:
        isoTF[chkey] = {}

        splits = chkey.strip('ChIso').split('to')
        minIso = float(splits[0])/10.0
        maxIso = float(splits[1])/10.0
    
        for label in ['rawmc', 'scaledmc']:
            isoHist = isoFile.Get(label)
    
            ### Get Sig and Sideband fractions
            minIsoBin = 1
            maxIsoBin = isoHist.GetNbinsX()
            for bin in range(isoHist.GetNbinsX()+1):
                binLowEdge = isoHist.GetXaxis().GetBinLowEdge(bin)
                if (binLowEdge == minIso):
                    minIsoBin = bin
                binUpEdge = isoHist.GetXaxis().GetBinUpEdge(bin)
                if (binUpEdge == maxIso):
                    maxIsoBin = bin
            sbFrac = isoHist.Integral(minIsoBin,maxIsoBin)

            # NOTE: Taking the first bin as the signal fraction
            sigFrac = isoHist.GetBinContent(1)

            isoTF[chkey][label] = sbFrac / sigFrac


### Set up for making templates
var = s.getVariable('sieie', tune, loc)

selections = s.getSelections(tune, loc, pid)

# high-pt jet + met + photon pt + photon hOverE/NHIso/PhIso
baseSel = ' && '.join([
#     'event.metFilters.dupECALClusters',
    metSel,    
    ptSel,
    selections['fiducial'],
    selections['hovere'],
    selections['nhiso'],
    selections['phiso']
])

if 'pixel' in extras:
    baseSel += ' && ' + s.Cuts['pixelVeto']
if 'monoph' in extras:
    baseSel += ' && ' + s.Cuts['monophId']
if 'chargedpf' in extras:
    baseSel += ' && ' + s.Cuts['chargedPFVeto']

sigSels = []
if 'noICH' not in extras:
    if 'max' in extras:
        sigSels.append(selections['chisomax'])
    else:
        sigSels.append(selections['chiso'])

sigSels.append(selections['trigger'])

sigSel = ' && '.join(sigSels)

ChIsoNear = 'ChIso35to50'
ChIsoNominal = 'ChIso50to75'
ChIsoFar = 'ChIso75to90'

if 'max' in extras:
    v = 'photons.chIsoMaxX[0][%d]' % itune
else:
    v = 'photons.chIsoX[0][%d]' % itune

expr = '{v} > %f && {v} < %f'.format(v = v)
sbSel = expr % ChIsoSbSels[ChIsoNominal]
sbSelNear = expr % ChIsoSbSels[ChIsoNear]
sbSelFar  = expr % ChIsoSbSels[ChIsoFar]

truthSel =  '(photons.matchedGenId[0] == -22)'

# get initial templates
print '\n'
print '#####################################'
print '######## Doing initial skims ########'
print '#####################################'
print '\n'

if not os.path.exists(os.path.join(histDir, 'initialHists.root')) or FORCEHIST:
    sphDataExt = s.HistExtractor('sphData', s.sphData, var)
    gjetsMcExt = s.HistExtractor('gjetsMc', s.gjetsMc, var)
    gjetsMcExt.plotter.setConstantWeight(s.sphLumi)
    
    print 'setBaseSelection(' + baseSel + ')'
    sphDataExt.plotter.setBaseSelection(baseSel)
    
    print 'setBaseSelection(' + baseSel + ' && ' + truthSel + ')'
    gjetsMcExt.plotter.setBaseSelection(baseSel + ' && ' + truthSel)
    
    sphDataExt.categories.append(('FitSinglePhoton', 'Fit Template from SinglePhoton Data', sigSel))
    sphDataExt.categories.append(('TempBkgdSinglePhoton', 'Background Template from SinglePhoton Data', sbSel))
    sphDataExt.categories.append(('TempBkgdSinglePhotonNear', 'Near Background Template from SinglePhoton Data', sbSelNear))
    sphDataExt.categories.append(('TempBkgdSinglePhotonFar', 'Far Background Template from SinglePhoton Data', sbSelFar))

    gjetsMcExt.categories.append(('TempSignalGJets', 'Signal Template from #gamma+jets MC', sigSel))
    gjetsMcExt.categories.append(('TempSidebandGJets', 'Sideband Template from #gamma+jets MC', sbSel))
    gjetsMcExt.categories.append(('TempSidebandGJetsNear', 'Near Sideband Template from #gamma+jets MC', sbSelNear))
    gjetsMcExt.categories.append(('TempSidebandGJetsFar', 'Far Sideband Template from #gamma+jets MC', sbSelFar))

    histFile = TFile.Open(os.path.join(histDir, 'initialHists.root'), 'recreate')
    
    start = time.time()
    dataTemplates = sphDataExt.extract(var.binning, histFile, mcsf = False)
    print 'Took', (time.time() - start), 'seconds to extract data templates'
    
    start = time.time()
    mcTemplates = gjetsMcExt.extract(var.binning, histFile, mcsf = True)
    print 'Took', (time.time() - start), 'seconds to extract MC templates'

    hDataTarg = dataTemplates[0]
    hDataBkgNom = dataTemplates[1]
    hDataBkgNear = dataTemplates[2]
    hDataBkgFar = dataTemplates[3]
    hMCSignalRaw = mcTemplates[0]
    hMCSBNomRaw = mcTemplates[1]
    hMCSignal = mcTemplates[4]
    hMCSBNom = mcTemplates[5]
    hMCSBNear = mcTemplates[6]
    hMCSBFar = mcTemplates[7]
    
    histFile.Write()

else:
    histFile = TFile.Open(os.path.join(histDir, 'initialHists.root'))

    hDataTarg = histFile.Get('FitSinglePhoton')
    hDataBkgNom = histFile.Get('TempBkgdSinglePhoton')
    hDataBkgNear = histFile.Get('TempBkgdSinglePhotonNear')
    hDataBkgFar = histFile.Get('TempBkgdSinglePhotonFar')
    hMCSignalRaw = histFile.Get('TempSignalGJets_raw')
    hMCSBNomRaw = histFile.Get('TempSidebandGJets_raw')
    hMCSignal = histFile.Get('TempSignalGJets')
    hMCSBNom = histFile.Get('TempSidebandGJets')
    hMCSBNear = histFile.Get('TempSidebandGJetsNear')
    hMCSBFar = histFile.Get('TempSidebandGJetsFar')

### plot "estimated" contamination in the sidebands
scanvas = SimpleCanvas(lumi = s.sphLumi)
def plotSigContam(hdata, hmc, name = '', pdir = plotDir):
    scanvas.Clear(full = True)
    scanvas.titlePave.SetX2NDC(0.5)
    scanvas.legend.setPosition(0.7, 0.7, 0.9, 0.9)
    scanvas.legend.add('obs', title = 'Data sideband', opt = 'LP', color = ROOT.kBlack, mstyle = 8)
    scanvas.legend.add('sig', title = '#gamma+jets MC', opt = 'L', lcolor = ROOT.kRed, lwidth = 2, lstyle = ROOT.kDashed)

    scanvas.legend.apply('obs', hdata)
    scanvas.legend.apply('sig', hmc)
    
    hdata.SetTitle('')

    scanvas.addHistogram(hdata, drawOpt = 'EP')
    scanvas.addHistogram(hmc, drawOpt = 'HIST')

    scanvas.xtitle = '#sigma_{i#etai#eta}'

    contam = hmc.Integral() / hdata.Integral() * 100.
    text = 'Sig. Contam: {contam}%'.format(contam = round(contam,1))
    scanvas.addText(text, 0.225, 0.4, 0.4, 0.6)

    scanvas.ylimits = (0.1, 1e6)

    scanvas.printWeb(pdir + '/sbcontam' , 'sbcontam_' + name, logy = False)

plotSigContam(hDataBkgNom, hMCSBNom, name = 'nominal')
plotSigContam(hDataBkgNear, hMCSBNear, name = 'near')
plotSigContam(hDataBkgFar, hMCSBFar, name = 'far')

canvas = RatioCanvas(lumi = s.sphLumi)

# allowing the bin edge to be lower than the actual cut (makes the purity higher!)
cutBin = hDataTarg.FindBin(var.cuts[pid])

FitResult = collections.namedtuple('FitResult', ['purity', 'aveSig', 'nReal', 'nFake'])

def plotSSFit(fitter, purity, nReal, name = '', pdir = plotDir):
    fitter.preparePlot()

    target = fitter.getTarget()
    total = fitter.getTotal()
    sig = fitter.getSignal()
    sigcr = fitter.getSignalCR()
    bkg = fitter.getBackground()
    subbkg = fitter.getSubtractedBackground()

    plotSigContam(bkg, sigcr, name = name + '_postfit', pdir = pdir)

    canvas.Clear(full = True)
    canvas.rtitle = 'data / fit'
    canvas.titlePave.SetX2NDC(0.5)
    canvas.legend.setPosition(0.7, 0.7, 0.9, 0.9)
    canvas.legend.add('obs', title = 'Observed', opt = 'LP', color = ROOT.kBlack, mstyle = 8)
    canvas.legend.add('fit', title = 'Fit', opt = 'L', lcolor = ROOT.kBlue, lwidth = 2, lstyle = ROOT.kSolid)
    canvas.legend.add('sig', title = 'Sig component', opt = 'L', lcolor = ROOT.kRed, lwidth = 2, lstyle = ROOT.kDashed)
    canvas.legend.add('bkg', title = 'Unsubtracted bkg', opt = 'L', lcolor = ROOT.kMagenta, lwidth = 2, lstyle = ROOT.kDashed)
    canvas.legend.add('subbkg', title = 'Subtracted bkg', opt = 'L', lcolor = ROOT.kGreen, lwidth = 2, lstyle = ROOT.kDashed)

    canvas.legend.apply('obs', target)
    canvas.legend.apply('fit', total)
    canvas.legend.apply('sig', sig)
    canvas.legend.apply('bkg', bkg)
    canvas.legend.apply('subbkg', subbkg)
    
    target.SetTitle('')

    iTarget = canvas.addHistogram(target, drawOpt = 'EP')
    iFit = canvas.addHistogram(total, drawOpt = 'HIST')
    canvas.addHistogram(sig, drawOpt = 'HIST')
    canvas.addHistogram(bkg, drawOpt = 'HIST')
    canvas.addHistogram(subbkg, drawOpt = 'HIST')

    text = '#splitline{Purity: ' + str(round(purity,3)) + '}{N_{True #gamma}: ' + str(int(nReal)) + '}'
    canvas.addText(text, 0.4, 0.3, 0.7, 0.5) 
    canvas.xtitle = '#sigma_{i#etai#eta}'

    canvas.printWeb(pdir, 'ssfit_' + name + '_logy', rList = [iFit, iTarget], logy = True)
    
def runSSFit(datasb, mcsb, sbRatio, name = '', pdir = plotDir, mcsig = hMCSignal):
    if not ITERATIVE:
        ssfitter.initialize(hDataTarg, mcsig, datasb, mcsb, sbRatio)
        ssfitter.fit()

        purity = ssfitter.getPurity(cutBin)
        nReal = ssfitter.getNsig(cutBin)
        nFake = ssfitter.getNbkg(cutBin)
        aveSig = s.StatUncert(nReal, nFake)

        if name:
            if not 'toy' in name:
                print 'plotting'
                plotSSFit(ssfitter, purity, nReal, name, pdir)

    else:
        skims = ['Target', 'Signal', 'Contam', 'Sideband']
        hists = [hDataTarg, mcsig, mcsb, datasb]
        rooVar = ROOT.RooRealVar(var.name, var.title, var.binning[1], var.binning[2])
        templates = [s.HistToTemplate(hist, rooVar, skims[iH], 'v0_'+inputKey, pdir) for iH, hist in enumerate(hists)]
        (purity, aveSig, nReal, nFake) = s.SignalSubtraction(skims, hists, templates, sbRatio, var.name, rooVar, var.cuts[pid], inputKey, pdir)


    return FitResult(purity, aveSig, nReal, nFake)


print '\n'
print '##################################################'
print '######## Doing initial purity calculation ########'
print '##################################################'
print '\n'

### Get nominal value

if QUICKFIT:
    # no signal subtraction
    nominalPurity = runSSFit(hDataBkgNom, hMCSBNom, 0., 'nominal').purity
    print "Purity: %f +- %f" % nominalPurity
    sys.exit(0)

nominalRatio = isoTF[ChIsoNominal]['rawmc']

nominalResult = runSSFit(hDataBkgNom, hMCSBNom, nominalRatio, 'nominal')

print '\n'
print '###################################################'
print '######## Doing ch iso sideband uncertainty ########'
print '###################################################'
print '\n'

### Get chiso sideband near uncertainty

nearResult = runSSFit(hDataBkgNear, hMCSBNear, isoTF[ChIsoNear]['rawmc'], 'near')

### Get chiso sideband far uncertainty

farResult = runSSFit(hDataBkgFar, hMCSBFar, isoTF[ChIsoFar]['rawmc'], 'far')

sidebandUncertainty = max(abs(nominalResult.purity - nearResult.purity), abs(nominalResult.purity - farResult.purity))
sidebandUncYield = max(abs(nominalResult.nReal - nearResult.nReal), abs(nominalResult.nReal - farResult.nReal))

print sidebandUncertainty, sidebandUncYield

print '\n'
print '###############################################'
print '######## Doing ch iso dist uncertainty ########'
print '###############################################'
print '\n'

### Get chiso dist uncertainty

scaledResult = runSSFit(hDataBkgNom, hMCSBNom, isoTF[ChIsoNominal]['scaledmc'], 'scaled')

scaledUncertainty = abs(nominalResult.purity - scaledResult.purity)
scaledUncYield = abs(nominalResult.nReal - scaledResult.nReal)

print '\n'
print '###################################################'
print '######## Doing background stat uncertainty ########'
print '###################################################'
print '\n'

NTOYS = 200

if DOTOYS:
    ### Get background stat uncertainty
    toyPlot = ROOT.TH1F("toyplot","Impurity Difference from Background Template Toys", 200, -0.010, 0.010)
    toyPlotYield = ROOT.TH1F("toyplotyield","True Photon Yield Difference from Background Template Toys", 200, -1000, 1000)
    toysDir = os.path.join(histDir,'toys')
    if not os.path.exists(toysDir):
        os.makedirs(toysDir)

    eventsToGenerate = int(hDataBkgNom.GetSumOfWeights())
    print eventsToGenerate

    for iToy in range(1, NTOYS + 1):
        print "\n###############\n#### Toy "+str(iToy)+" ####\n###############\n"

        toyHist = hDataBkgNom.Clone('toyhist')
        toyHist.Reset()
        toyHist.FillRandom(hDataBkgNom, eventsToGenerate)

        toyHist.Draw()

        tempName = os.path.join(toysDir, 'toy%d' % iToy)
        canvas.SaveAs(tempName+'.pdf')
        canvas.SaveAs(tempName+'.png')
        canvas.SaveAs(tempName+'.C')

        toyResult = runSSFit(toyHist, hMCSBNom, nominalRatio, 'toy%d' % iToy, pdir = toysDir)

        purityDiff = toyResult.purity - nominalResult.purity
        print "Purity diff is:", purityDiff
        toyPlot.Fill(purityDiff)

        yieldDiff = toyResult.nReal - nominalResult.nReal
        print "Yield diff is:", yieldDiff
        toyPlotYield.Fill(yieldDiff)

    bkgdUncertainty = toyPlot.GetStdDev()
    bkgdUncYield = toyPlotYield.GetStdDev()

    tcanvas = SimpleCanvas(lumi = s.sphLumi, name = 'toys')
    toyPlot.SetTitle('')

    tcanvas.legend.add('toys', title = 'toys', opt = 'L', lcolor = ROOT.kBlue, lwidth = 2, lstyle = ROOT.kSolid)
    tcanvas.legend.apply('toys', toyPlot)
    tcanvas.addHistogram(toyPlot)

    tcanvas.xtitle = 'Impurity Difference (%)'
    tcanvas.ytitle = '# of Toys'
    
    tcanvas.printWeb(plotDir, 'ssfit_toy_dist', logy = False)
    
    tcanvas.Clear()
    toyPlotYield.SetTitle('')
    
    tcanvas.legend.apply('toys', toyPlotYield)
    tcanvas.addHistogram(toyPlotYield)

    tcanvas.xtitle = '#Delta(# of True Photons)'
    tcanvas.ytitle = '# of Toys'
    
    tcanvas.printWeb(plotDir, 'ssfit_toyyield_dist', logy = False)
    

else:
    bkgdUncertainty = 0.
    bkgdUncYield = 0.

print '\n'
print '################################################'
print '######## Doing signal shape uncertainty ########'
print '################################################'
print '\n'

shapeResult = runSSFit(hDataBkgNom, hMCSBNomRaw, nominalRatio, 'shape', mcsig = hMCSignalRaw)

shapeUncertainty = abs(nominalResult.purity - shapeResult.purity)
shapeUncYield = abs(nominalResult.purity - shapeResult.purity)

print '\n'
print '#################################'
print '######## Showing results ########'
print '#################################'
print '\n'

print "Nominal purity is:", nominalResult.purity
print "Sideband uncertainty is:", sidebandUncertainty
print "Method uncertainty is:", scaledUncertainty
print "Signal shape uncertainty is:", shapeUncertainty
print "Background stat uncertainty is:", bkgdUncertainty
totalUncertainty = ( (sidebandUncertainty**2) + (scaledUncertainty)**2 + (shapeUncertainty)**2 + (bkgdUncertainty)**2 )**(0.5)
totalUncYield = ( (sidebandUncYield)**2 + (scaledUncYield)**2 + (shapeUncYield)**2 + (bkgdUncYield)**2 )**(0.5)

print "Total uncertainty is:", totalUncertainty

if ITERATIVE:
    outFileName = WEBDIR + '/' + plotDir + '/results_iterative.out'
else:
    outFileName = WEBDIR + '/' + plotDir + '/results.out'

outFile = file(outFileName, 'w')

for key in histFile.GetListOfKeys():
    hist = histFile.Get(key.GetName())
    if hist.InheritsFrom(ROOT.TH1.Class()):
        outFile.write('%s has %f events \n' % (hist.GetName(), hist.Integral()))

outFile.write( "\n\n# of real photons is: "+str(nominalResult.nReal)+'\n' )
outFile.write( "Sideband unc yield is: "+str(sidebandUncYield)+'\n' )
outFile.write( "Method unc yield is: "+str(scaledUncYield)+'\n' ) 
outFile.write( "Signal shape unc yield is: "+str(shapeUncYield)+'\n' ) 
outFile.write( "Background stat unc yield is: "+str(bkgdUncYield)+'\n' )
outFile.write( "Total unc yield is: "+str(totalUncYield)+'\n\n\n' )

outFile.write( "Nominal purity is: "+str(nominalResult.purity)+'\n' )
outFile.write( "Sideband uncertainty is: "+str(sidebandUncertainty)+'\n' )
outFile.write( "Method uncertainty is: "+str(scaledUncertainty)+'\n' ) 
outFile.write( "Signal shape uncertainty is: "+str(shapeUncertainty)+'\n' ) 
outFile.write( "Background stat uncertainty is: "+str(bkgdUncertainty)+'\n' )
outFile.write( "Total uncertainty is: "+str(totalUncertainty)+'\n' )

outFile.close()
