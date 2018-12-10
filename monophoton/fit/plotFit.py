#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True
import os
import re
import math

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)

commondir = os.path.dirname(basedir) + '/common'
if commondir not in sys.path:
    sys.path.append(commondir)

from datasets import allsamples
from plotstyle import RatioCanvas, Legend
import workspace_config as wc

config = sys.argv[1]
pdir = sys.argv[2]

if config == 'monoph':
    import parameters
    from main.plotconfig import getConfig as getConfig
elif config == 'vbf':
    import parameters_vbf as parameters
    from main.plotconfig_vbf import getConfigVBF as getConfig
elif config == 'ggh':
    import parameters_ggh as parameters
    from main.plotconfig_ggh import getConfigGGH as getConfig

import ROOT
ROOT.gROOT.SetBatch(True)

if pdir == 'c':
    print 'CR only'
    mlfit = ROOT.TFile.Open(sys.argv[3] + '_CRonly')
else:
    print 'full'
    mlfit = ROOT.TFile.Open(sys.argv[3] + '_full')

if pdir == 'p':
    postfitDir = mlfit.Get('shapes_prefit')
elif pdir == 'b' or pdir == 'c':
    postfitDir = mlfit.Get('shapes_fit_b') 
elif pdir == 's':
    postfitDir = mlfit.Get('shapes_fit_s')
else:
    print 'Please choose prefit (p), CR-only (c), b-only (b), or s+b (s) directory to use for plotting.'
    sys.exit(0)

SIMPLE = False

workspace = ROOT.TFile.Open(wc.config.outname).Get('wspace')
x = workspace.arg('x')

def printRegionHeader(name, hist):
    nbins = hist.GetNbinsX()

    if pdir == 'p':
        fit = 'pre-fit'
    elif pdir == 'c':
        fit = 'CR-only post-fit'
    elif pdir == 'b':
        fit = 'background-only post-fit'
    elif pdir == 's':
        fit = 'signal-plus-background post-fit'
    
    tstr = '\\begin{table} \n\\begin{center} \n\\begin{tabular}{ |c|'
    hstr = r'\multicolumn{' + str(nbins+1) + r'}{ |c| }{Estimated ' + fit + ' bin-by-bin yields for ' + name + r' region} \\'
    pstr = '%15s' % r'$E_{T}^{\gamma}$'
    
    for iBin in range(1, nbins + 1):
        tstr += 'c|'
        pstr += ' & %19s' % ( '[%3.0f, %4.0f]' % (hist.GetBinLowEdge(iBin), hist.GetBinLowEdge(iBin+1)))

    tstr += ' }'
    pstr += r' \\'

    print tstr
    print r'\hline' 
    print hstr
    print r'\hline' 
    print pstr
    print r'\hline' 

def printRegionFooter(name, lumi, thist, dhist):
    if pdir == 'p':
        fitl = 'pre-fit'
        fits = 'prefit'
    elif pdir == 'c':
        fitl = 'CR-only post-fit'
        fits = 'CRonly'
    elif pdir == 'b':
        fitl = 'background-only post-fit'
        fits = 'bonly'
    elif pdir == 's':
        fitl = 'signal-plus-background post-fit'
        fits = 'splusb'
        
    cstr = r'\caption{Estimated ' + fitl + ' bin-by-bin yields in the ' + name + ' region.}'
    lstr = r'\label{tab:' + fits + '_binbybin_' + name + '}'
 
    print r'\hline' 
    printBinByBin('total', thist)
    print r'\hline' 
    printBinByBin('data', dhist)
    print r'\hline'
    print r'\end{tabular}'
    print r'\end{center}'
    print cstr
    print lstr
    print r'\end{table}'
    print ''

def printBinByBin(name, hist):
    pstr = '%15s' % name
    
    for iBin in range(1, hist.GetNbinsX() + 1):
        width = hist.GetBinWidth(iBin)
        pstr += ' & $%6.1f \\pm %5.1f $' % (width * hist.GetBinContent(iBin), width * hist.GetBinError(iBin))
    
    pstr += r' \\'

    print pstr

for key in postfitDir.GetListOfKeys():
    region = key.GetName()

    if 'total' in region:
        continue

    prefitFile = ROOT.TFile.Open(wc.config.sourcename.format(region = region))
    prefitDir = prefitFile.Get(parameters.distribution)

    prefitTotal = prefitDir.Get('bkgtotal_syst')
    prefitTotal.Scale(1., 'width')
    prefitUnc = prefitTotal.Clone('prefitUnc')
    prefitRatio = ROOT.TGraphAsymmErrors(prefitTotal.GetNbinsX())
    prefitRatio.SetName('prefitRatio')
    prefitUncRatio = prefitTotal.Clone('prefitUncRatio')

    if pdir == 's':
        postfitTotal = postfitDir.Get(region + '/total')
    else:
        postfitTotal = postfitDir.Get(region + '/total_background')
    postfitUnc = postfitTotal.Clone('postfitUnc')
    postfitRatio = ROOT.TGraphAsymmErrors(postfitTotal.GetNbinsX())
    postfitRatio.SetName('postfitRatio')
    postfitUncRatio = postfitTotal.Clone('postfitUncRatio')

    dataHist = postfitTotal.Clone("dataHist")
    dataHist.Reset()

    data = postfitDir.Get(region + '/data')
    x = ROOT.Double(0.)
    y = ROOT.Double(0.)
    for iBin in range(1, dataHist.GetNbinsX() + 1):
        width = dataHist.GetXaxis().GetBinWidth(iBin)

        data.GetPoint(iBin-1, x, y)
        ywidth = y * width
        yerr = math.sqrt(ywidth)

        dataHist.SetBinContent(iBin, ywidth)
        dataHist.SetBinError(iBin, yerr)

    obs = ROOT.RooHist(dataHist, 1.)
    obs.SetName('data_obs')

    dataHist.Scale(1., 'width')

    for iBin in range(1, dataHist.GetNbinsX()+1):
        data = dataHist.GetBinContent(iBin)
#        if data == 0:
#            data = 1
        dataerr = dataHist.GetBinError(iBin)
#        if dataerr == 0:
#            dataerr = 1
        dataerrUp = obs.GetErrorYhigh(iBin - 1)
        dataerrDown = obs.GetErrorYlow(iBin - 1)

        x = dataHist.GetXaxis().GetBinCenter(iBin)
        w = dataHist.GetXaxis().GetBinWidth(iBin)
        eylow = obs.GetErrorYlow(iBin - 1)
        eyhigh = obs.GetErrorYhigh(iBin - 1)

        prefitcontent = prefitTotal.GetBinContent(iBin)
        prefiterror = prefitTotal.GetBinError(iBin)
        prefitscale = data / prefitcontent

        prefitRatio.SetPoint(iBin - 1, x, data * prefitscale)
        prefitRatio.SetPointError(iBin - 1, w * 0.5, w * 0.5, eylow * prefitscale, eyhigh * prefitscale)
        prefitUncRatio.SetBinContent(iBin, prefitcontent * prefitscale)
        prefitUncRatio.SetBinError(iBin, prefiterror * prefitscale)

        postfitcontent = postfitTotal.GetBinContent(iBin)
        postfiterror = postfitTotal.GetBinError(iBin)
        postfitscale = data / postfitcontent

        postfitRatio.SetPoint(iBin - 1, x, data * postfitscale)
        postfitRatio.SetPointError(iBin - 1, w * 0.5, w * 0.5, eylow * postfitscale, eyhigh * postfitscale)
        postfitUncRatio.SetBinContent(iBin, postfitcontent * postfitscale)
        postfitUncRatio.SetBinError(iBin, postfiterror * postfitscale)

    floatNames = []

    allVars = workspace.allVars()
    vitr = allVars.iterator()
    while True:
        v = vitr.Next()
        if not v:
            break

        matches = re.match('mu_([^_]+)_' + region + '_bin[0-9]+', v.GetName())
        if matches and not v.isConstant():
            proc = matches.group(1)
            if proc not in floatNames:
                floatNames.append(proc)

        matches = re.match('([^_]+)_' + region + '_([^_]+)_([^_]+)_bin[0-9]+_tf', v.GetName())
        if matches:
            proc = matches.group(1)
            if proc not in floatNames:
                floatNames.append(proc)

            floatName = matches.group(1)

    if len(floatNames) != 0:
        postfitSub = postfitTotal.Clone('subdominant')
        for proc in floatNames:
            postfitSub.Add(postfitDir.Get(region + '/' + proc), -1.)
    else:
        postfitSub = None

    plotConfig = getConfig(region)
    
    lumi = 0.
    for sample in plotConfig.obs.samples:
        lumi += sample.lumi / plotConfig.prescales[sample]
    
    if not SIMPLE:
        printRegionHeader(region, prefitTotal)
    
    if pdir == 's':
        pftitle = 'Sig.+bkgd. fit'
    elif pdir == 'c':
        pftitle = 'CR-only fit'
    else:
        pftitle = 'Bkgd. fit'

    canvas = RatioCanvas(lumi = lumi, name = region, prelim = False)
    canvas.legend.ncolumns = 1

    # y coordinates will be adjusted later
    resultLegend = Legend(0.35, 0., 0.7, 1.)
    resultLegend.add('obs', title = 'Data', opt = 'ELP', color = ROOT.kBlack, mstyle = 8, msize = 0.8)
    resultLegend.add('prefit', title = 'Pre-fit', opt = 'LF', color = ROOT.kRed, lstyle = ROOT.kDashed, lwidth = 2, fstyle = 3004, mstyle = 8, msize = 0.8)
    if postfitSub and SIMPLE:
        resultLegend.add('subdom', title = 'Subdominant', opt = 'F', fcolor = ROOT.kGray, fstyle = 1001)
    resultLegend.add('postfit', title = pftitle, opt = 'LF', color = ROOT.kBlue, lstyle = ROOT.kSolid, lwidth = 2, fstyle = 3005, mstyle = 8, msize = 0.8)

    obs.SetTitle('')
    prefitTotal.SetTitle('')
    postfitTotal.SetTitle('')
    if postfitSub and SIMPLE:
        postfitSub.SetTitle('')

    resultLegend.apply('obs', obs)
    resultLegend.apply('obs', dataHist)

    resultLegend.apply('prefit', prefitTotal, opt = 'L')
    resultLegend.apply('prefit', prefitUnc, opt = 'F')
    resultLegend.apply('prefit', prefitRatio, opt = 'LP')
    resultLegend.apply('prefit', prefitUncRatio, opt = 'F')

    resultLegend.apply('postfit', postfitTotal, opt = 'L')
    resultLegend.apply('postfit', postfitUnc, opt = 'F')
    resultLegend.apply('postfit', postfitRatio, opt = 'LP')
    resultLegend.apply('postfit', postfitUncRatio, opt = 'F')
        
    if postfitSub and SIMPLE:
        resultLegend.apply('subdom', postfitSub)
    
    # reuse dataHist for unity line in ratio pad
    dataHist.SetLineColor(ROOT.kBlack)
    # dataHist.SetLineStyle(ROOT.kDashed)
    dataHist.SetLineWidth(2)

    iObs = canvas.addHistogram(obs)
    iPreUnc = canvas.addHistogram(prefitUnc, drawOpt = 'E2')
    iPre = canvas.addHistogram(prefitTotal, drawOpt = 'HIST')
    iPostUnc = canvas.addHistogram(postfitUnc, drawOpt = 'E2')
    iPost = canvas.addHistogram(postfitTotal, drawOpt = 'HIST')

    iLine = canvas.addHistogram(dataHist, drawOpt = 'HIST')
    iPreUncRatio = canvas.addHistogram(prefitUncRatio, drawOpt = 'E2')
    iPreRatio = canvas.addHistogram(prefitRatio, drawOpt = 'EP')
    iPostUncRatio = canvas.addHistogram(postfitUncRatio, drawOpt = 'E2')
    iPostRatio = canvas.addHistogram(postfitRatio, drawOpt = 'EP')

    if SIMPLE:
        if postfitSub:
            iSub = canvas.addHistogram(postfitSub)
            hList = [iSub, iPreUnc, iPre, iPostUnc, iPost, iObs]
        else:
            hList = [iPreUnc, iPre, iPostUnc, iPost, iObs]

    else:
        stackHist = postfitTotal.Clone('stack')
        stackHist.Reset()
        
        groupHists = []
        groupList = []

        for group in plotConfig.bkgGroups:
            ghist = postfitDir.Get(region + '/' + group.name).Clone()
            ghist.SetTitle('')

            if len(groupHists):
                # we just overlay bunch of histograms instead of using THStack
                ghist.Add(groupHists[-1])

            groupHists.append(ghist)

        if pdir == 's':
            try:
                shist = postfitDir.Get(region + '/total_signal').Clone()
                resultLegend.add('signal', title = 'Signal', opt = 'F', fcolor = ROOT.kBlack, fstyle = 3002)

                printBinByBin('signal', shist)
                resultLegend.apply('signal', shist)
                shist.SetTitle('')

                if len(groupHists):
                    shist.Add(groupHists[-1])

                iS = canvas.addHistogram(shist)
                groupList.append(iS)

            except ReferenceError:
                print region + ' region has no signal processes.'
                pass

        # merge groups
        # component groups must be adjacently defined in plotconfig
        groupMerge = []

        if config == 'monoph':
            if 'monoph' in region or 'horizontal' in region or 'vertical' in region:
                groupMerge = [
                    ('other', ('vvg', 'top', 'gg', 'wjets', 'gjets'), 'Other SM', ROOT.TColor.GetColor(0xff, 0xbb, 0x55)),
                    ('noncol', ('halo', 'spike'), 'Noncollision', ROOT.TColor.GetColor(0xaa, 0xaa, 0xaa))
                ]
            elif 'mono' in region:
                groupMerge = [
                    ('other', ('zg', 'vvg', 'gg'), 'Other SM', ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
                ]
            elif 'di' in region:
                groupMerge = [
                    ('ttvv', ('vvg', 'top'), 't#bar{t}#gamma/VV#gamma', ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
                ]

        added = set()

        for group, ghist in reversed(zip(plotConfig.bkgGroups, groupHists)):
            for aggrName, groups, title, color in groupMerge:
                if group.name in groups:
                    name = aggrName
                    title = title
                    color = color
                    break
            else:
                name = group.name
                title = group.title
                color = group.color

            # just to filter out merged groups that are already added (we only use the first = all merged histogram)
            if name in added:
                continue

            added.add(name)

            if 'Hadronic' in title:
                title = title.replace('Hadronic', 'Hadron')

            canvas.legend.add(name, title = title, opt= 'F', fcolor = color, fstyle = 1001)
            canvas.legend.apply(name, ghist)

            iG = canvas.addHistogram(ghist)
            groupList.append(iG)

        for iG in groupList:
            ghist = canvas._histograms[iG].obj.Clone()

            if iG+1 == len(canvas._histograms):
                printBinByBin(ghist.GetName(), ghist)
                continue

            shist = canvas._histograms[iG+1].obj.Clone()

            ghist.Add(shist, -1.)
            printBinByBin(ghist.GetName(), ghist)

        printRegionFooter(region, lumi, postfitTotal, dataHist)
            # print name, ghist.Integral()

        if pdir != 's':
            try:
                shist = mlfit.Get('shapes_prefit').Get(region + '/total_signal').Clone()
                resultLegend.add('signal', title = 'Signal', opt = 'L', color = ROOT.kMagenta, lstyle = ROOT.kSolid, lwidth = 3)

                resultLegend.apply('signal', shist)
                shist.SetTitle('')

                iS = canvas.addHistogram(shist)
                groupList.append(iS)
            
            except ReferenceError:
                print region + ' region has no signal processes.'
                pass

        hList = groupList + [iPreUnc, iPre, iPostUnc, iPost, iObs]

    canvas.rlimits = (0.0, 2.5)
    if 'monoph' in region or 'horizontal' in region or 'vertical' in region:
        canvas.ylimits = (0.0003, 100.)
        rlabel = region
    elif 'mono' in region:
        canvas.ylimits = (0.0003, 60.)
        if 'mu' in region:
            rlabel = '#mu#gamma'
        elif 'el' in region:
            rlabel = 'e#gamma'
    elif 'di' in region:
        canvas.ylimits = (0.0003, 8.)
        if 'mu' in region:
            rlabel = '#mu#mu#gamma'
        elif 'el' in region:
            rlabel = 'ee#gamma'

    canvas.cmsPave.SetTextSize(0.04)
    canvas.addText(rlabel, 0.185, 0.82, 0.35, 0.86, size = 0.04, align = 12)

    resultLegend.setPosition(0.4, 0.88 - 0.04 * len(resultLegend.entries), 0.63, 0.88)
    canvas.legend.setPosition(0.63, 0.88 - 0.04 * len(canvas.legend.entries), 0.9, 0.88)

    resultLegend.SetTextSize(0.04)
    canvas.legend.SetTextSize(0.04)

    if config == 'monoph':
        canvas.xtitle = 'E_{T}^{#gamma} [GeV]'
    else:
        canvas.xtitle = 'M_{T}(#gamma, E_{T}^{miss}) [GeV]'
    canvas.ytitle = 'Events / GeV'
    canvas.rtitle = 'Data / Pred.'

    if pdir == 'p':
        outname = 'prefit_' + region
    elif pdir == 'c':
        outname = 'CRonly_' + region 
    elif pdir == 'b':
        outname = 'bonly_' + region
    elif pdir == 's':
        outname = 'splusb_' + region

    resultLegend.construct()
    canvas.addObject(resultLegend.legend, clone = False)

    canvas.Update(hList = hList, rList = [iLine, iPreUncRatio, iPostUncRatio, iPreRatio, iPostRatio], logy = True)

    zeroBins = []
    for iBin in range(1, dataHist.GetNbinsX() + 1):
        if dataHist.GetBinContent(iBin) == 0.:
            zeroBins.append(iBin)

    if len(zeroBins) != 0:
        # OK we need to manually edit the ratio histograms after all the acrobat of making inverted ratios..
        for prim in canvas.ratioPad.GetListOfPrimitives():
            name = prim.GetName().replace('ratio_', '')
            if name not in ['prefitUncRatio', 'postfitUncRatio', 'prefitRatio', 'postfitRatio']:
                continue

            if 'prefit' in name:
                orig = prefitTotal
            else:
                orig = postfitTotal

            for iBin in zeroBins:
                scale = 1. / orig.GetBinContent(iBin)

                if 'Unc' in name:
                    # prim is a TH1
                    prim.SetBinContent(iBin, 1.)
                    prim.SetBinError(iBin, orig.GetBinError(iBin) * scale)
                else:
                    # prim is a TGraphAsymmErrors
                    prim.SetPoint(iBin - 1, prim.GetX()[iBin - 1], 0.)
                    prim.SetPointEYhigh(iBin - 1, obs.GetErrorYhigh(iBin - 1) * scale)

    canvas.printWeb('EXO16053/fit', outname, hList = hList, rList = [iLine, iPreUncRatio, iPostUncRatio, iPreRatio, iPostRatio], logy = True)

    canvas.Clear()

    dataHist.Delete()
    if postfitSub:
        postfitSub.Delete()
