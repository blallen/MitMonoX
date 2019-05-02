import sys
import os
import array
import math
import ROOT
import time

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(basedir)
from plotstyle import SimpleCanvas, RatioCanvas
from datasets import allsamples
import purity.selections as selections
import config
import utils

ROOT.gROOT.SetBatch(True)

###########################
# Setup and configuration #
###########################

snames = ['sph-16*-m']

lumi = sum(s.lumi for s in allsamples.getmany(snames))
canvas = SimpleCanvas(lumi = lumi)
rcanvas = RatioCanvas(lumi = lumi)

binning = array.array('d', map(float, selections.photonPtBinning))
pid = 'medium'
tune = 'GJetsCWIso' # 'Spring16'
extras = 'pixel-monoph' #-chargedpf'
suffix = '_' + tune

itune = selections.Tunes.index(tune)

inputFile = ROOT.TFile.Open(basedir+'/data/impurity_' + tune + '.root')
impurityGraph = inputFile.Get("barrel-" + pid + "-" + extras + "-Met0to60")

outputFile = ROOT.TFile.Open(basedir+'/data/hadronTFactor' + suffix + '.root', 'recreate')

selExprs = selections.getSelections(tune, 'barrel', 'medium')
selExprsLoose = selections.getSelections(tune, 'barrel', 'loose')
selExprsTight = selections.getSelections(tune, 'barrel', 'tight')

baseSels = {
    'met': 't1Met.pt < 60.',
    'nph': 'photons.size == 1',
    'eb': 'photons.isEB[0]',
    'hOverE': selExprs['hovere'],
    'chIso': 'photons.chIsoX[0][%d] < 11.' % itune,
    'sieie': selExprs['sieie']
}

if not selections.lowpt:
    baseSels['jet'] = 'jets.pt_[0] > 100.'

goodSels = {
    'chIso': selExprs['chiso'],
    'nhIso': selExprs['nhiso'],
    'phIso': selExprs['phiso'],
    'trigger': 'photons.triggerMatch[0][13]'
}

nomSels = {
    'chIso': '!(%s)' % selExprs['chiso'],
    'nhIso': selExprs['nhiso'],
    'phIso': selExprs['phiso']
}

tightSels = {
    'chIso': '!(%s)' % selExprs['chiso'],
    'nhIso': selExprsTight['nhiso'],
    'phIso': selExprsTight['phiso']
}

looseSels = {
    'chIso': '!(%s)' % selExprs['chiso'],
    'nhIso': selExprsLoose['nhiso'],
    'phIso': selExprsLoose['phiso']
}

if 'pixel' in extras:
    baseSels['eveto'] = 'photons.pixelVeto[0]'

if 'chargedpf' in extras:
    baseSels['pfveto'] = 'photons.chargedPFVeto[0]'

if 'monoph' in extras:
    baseSels['monoph'] = selections.Cuts['monophId']

if 'noICH' in extras:
    goodSels.pop('chIso')

if 'max' in extras:
    baseSels['chIso'] = baseSels['chIso'].replace('chIso', 'chIsoMax')
    goodSels['chIso'] = goodSels['chIso'].replace('chIso', 'chIsoMax')
    nomSels['chIso'] = nomSels['chIso'].replace('chIso', 'chIsoMax')
    tightSels['chIso'] = tightSels['chIso'].replace('chIso', 'chIsoMax')
    looseSels['chIso'] = looseSels['chIso'].replace('chIso', 'chIsoMax')

# selections concatenated with chVeto
configurations = [
    ('Nom', nomSels),
    ('Tight', tightSels),
    ('Loose', looseSels)
]


#######################
# Plot all histograms #
#######################

plotter = ROOT.MultiDraw()
plotter.setPrintLevel(1)
for sample in allsamples.getmany(snames):
    if selections.lowpt:
        plotter.addInputPath(utils.getSkimPath(sample.name, 'ph75'))
    else:
        plotter.addInputPath(utils.getSkimPath(sample.name, 'emjet'))

plotter.setBaseSelection(' && '.join(baseSels.values()))

template = ROOT.TH1D('template', ';p_{T} (GeV)', len(binning) - 1, binning)
template.Sumw2()

histograms = {}

gname = 'gpt'
gpt = template.Clone(gname)
histograms[gname] = gpt

plotter.addPlot(gpt, 'photons.scRawPt[0]', ' && '.join(goodSels.values()))

for confName, sels in configurations:
    hname = 'hpt'+confName
    hpt = template.Clone(hname)
    histograms[hname] = hpt

    plotter.addPlot(hpt, 'photons.scRawPt[0]', ' && '.join(sels.values()))

print 'Start histogram fill'
plotter.fillPlots()

outputFile.cd()

for hist in histograms.values():
    hist.Scale(1., 'width')
    hist.Write()


###############################################################
# Good photon + jet distribution and impurity-scaled versions #
###############################################################

fname = 'fpt'
fpt = gpt.Clone(fname)
fptUp = gpt.Clone(fname+'PurityUp')
fptDown = gpt.Clone(fname+'PurityDown')

for iX in range(1, fpt.GetNbinsX() + 1):
    cent = fpt.GetXaxis().GetBinCenter(iX)        

    xval = ROOT.Double(0)
    imp = ROOT.Double(0)
    err = 0

    for iP in range(0, impurityGraph.GetN()):
        impurityGraph.GetPoint(iP, xval, imp)
        low = xval - impurityGraph.GetErrorXlow(iP)
        high = xval + impurityGraph.GetErrorXhigh(iP)
        if cent > low and cent < high:
            err = impurityGraph.GetErrorY(iP)
            print iP, low, high, err
            break

    imp = imp / 100.
    err = err / 100.

    cont = fpt.GetBinContent(iX) * imp 
    stat = fpt.GetBinError(iX) * imp 
    syst = fpt.GetBinContent(iX) * err

    fpt.SetBinContent(iX, cont)
    fpt.SetBinError(iX, math.sqrt(stat * stat)) # + syst * syst))

    impUp = imp + err
    contUp = fptUp.GetBinContent(iX) * impUp 
    statUp = fptUp.GetBinError(iX) * impUp

    fptUp.SetBinContent(iX, contUp)
    fptUp.SetBinError(iX, math.sqrt(statUp * statUp)) # + syst * syst))

    impDown = imp - err
    contDown = fptDown.GetBinContent(iX) * impDown
    statDown = fptDown.GetBinError(iX) * impDown

    fptDown.SetBinContent(iX, contDown)
    fptDown.SetBinError(iX, math.sqrt(statDown * statDown)) # + syst * syst))

    print "Bin center: %.2f, imp: %.2f,  err: %.2f (%2.0f), up: %.2f, down %.2f" % (cent, imp*100, err*100, err/imp*100, impUp*100, impDown*100)

outputFile.cd()
fptUp.Write()
fptDown.Write()

#########################################################
# Comute the transfer factors for various proxy choices #
#########################################################

for confName, sels in configurations:
    hname = 'hpt'+confName

    hpt = histograms[hname]

    tname = 'tfact'+confName
    tfact = fpt.Clone(tname)
    tfact.Divide(hpt)

    tfactUp = fptUp.Clone(tname+'PurityUp')
    tfactUp.Divide(hpt)

    tfactDown = fptDown.Clone(tname+'PurityDown')
    tfactDown.Divide(hpt)

    for iX in range(1, fpt.GetNbinsX() + 1):
        print "pt: %3.0f gjets: %10.1f, fake:     %10.1f, hadron: %10.1f, tfact:     %6.2f" % (fpt.GetBinLowEdge(iX), gpt.GetBinContent(iX), fpt.GetBinContent(iX), 
                                                                                    hpt.GetBinContent(iX), tfact.GetBinContent(iX)*100)
        print "pt: %3.0f gjets: %10.1f, fakeUp:   %10.1f, hadron: %10.1f, tfactUp:   %6.2f" % (fpt.GetBinLowEdge(iX), gpt.GetBinContent(iX), fptUp.GetBinContent(iX)
                                                                                        , hpt.GetBinContent(iX), tfactUp.GetBinContent(iX)*100)
        print "pt: %3.0f gjets: %10.1f, fakeDown: %10.1f, hadron: %10.1f, tfactDown: %6.2f" % (fpt.GetBinLowEdge(iX), gpt.GetBinContent(iX), fptDown.GetBinContent(iX)
                                                                                        , hpt.GetBinContent(iX), tfactDown.GetBinContent(iX)*100)

    outputFile.cd()
    tfact.Write()
    tfactUp.Write()
    tfactDown.Write()

    canvas.cd()
    canvas.Clear()
    canvas.legend.Clear()

    canvas.legend.add(gname, title = '#gamma + jet', lcolor = ROOT.kBlack, lwidth = 2)
    canvas.legend.add(fname, title = '#gamma + jet #times impurity', lcolor = ROOT.kRed, lwidth = 2)
    canvas.legend.add(fname+'Syst', title = 'impurity #pm 1#sigma', lcolor = ROOT.kRed, lwidth = 2, lstyle = ROOT.kDashed)
    canvas.legend.add(hname, title = 'EM object + jet', lcolor = ROOT.kBlue, lwidth = 2)
    canvas.legend.setPosition(0.5, 0.7, 0.8, 0.9)

    canvas.legend.apply(gname, gpt)
    canvas.legend.apply(fname, fpt)
    canvas.legend.apply(fname+'Syst', fptUp)
    canvas.legend.apply(fname+'Syst', fptDown)
    canvas.legend.apply(hname, hpt)

    canvas.addHistogram(gpt, drawOpt = 'HIST')
    canvas.addHistogram(fpt, drawOpt = 'HIST')
    canvas.addHistogram(fptUp, drawOpt = 'HIST')
    canvas.addHistogram(fptDown, drawOpt = 'HIST')
    canvas.addHistogram(hpt, drawOpt = 'HIST')

    canvas.xtitle = 'E_{T}^{#gamma} (GeV)'
    canvas.ylimits = (1.0, 2500000.)
    canvas.SetLogy(True)

    canvas.printWeb('monophoton/hadronTFactor' + suffix, 'distributions'+confName)

    rcanvas.Clear()
    rcanvas.legend.Clear()

    # if samp == 'Down':
    rcanvas.ylimits = (0., 0.15)
    # else:
    # rcanvas.ylimits = (0., 0.05)
    rcanvas.xtitle = canvas.xtitle
    rcanvas.ytitle = "R_{h}"
    rcanvas.rtitle = "#pm 1#sigma / Nominal"
    rcanvas.rlimits = (0.8, 1.2)

    rcanvas.legend.add(tname, title = 'transfer factor', lcolor = ROOT.kBlack, lwidth = 2)
    rcanvas.legend.add(tname+'Syst', title = 'impurity #pm 1#sigma', lcolor = ROOT.kBlack, lwidth = 2, lstyle = ROOT.kDashed)
    rcanvas.legend.setPosition(0.2, 0.4, 0.4, 0.5)

    rcanvas.legend.apply(tname, tfact)
    rcanvas.legend.apply(tname+'Syst', tfactUp)
    rcanvas.legend.apply(tname+'Syst', tfactDown)

    iNom = rcanvas.addHistogram(tfact, drawOpt = 'HIST')
    iUp = rcanvas.addHistogram(tfactUp, drawOpt = 'HIST')
    iDown = rcanvas.addHistogram(tfactDown, drawOpt = 'HIST')

    rcanvas.SetLogy(False)

    rcanvas.printWeb('monophoton/hadronTFactor' + suffix, 'tfactor'+confName, hList = [iUp, iDown, iNom], rList = [iNom, iUp, iDown])
