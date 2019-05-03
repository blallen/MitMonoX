import sys
import os

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
from plotstyle import RatioCanvas

import ROOT

canvas = None
lumi = 1.
plotDir = ''

plotBinningT = (60, 60., 120.)
plotBinningT2 = (30, 60., 120.)

def plotFit(mass, targHist, model, dataType, suffix, bkgModel = 'nombkgModel', hmcbkg = None, alt = '', plotName = ''):
    global canvas

    if canvas is None:
        canvas = RatioCanvas(lumi = lumi, sim = (dataType == 'mc'))

    canvas.Clear(full = True)
    canvas.rtitle = '(data - fit) / #sigma_{data}'
    canvas.titlePave.SetX2NDC(0.5)
    canvas.legend.setPosition(0.6, 0.7, 0.9, 0.9)
    canvas.legend.add('obs', title = 'Observed', opt = 'LP', color = ROOT.kBlack, mstyle = 8)
    canvas.legend.add('fit', title = 'Fit', opt = 'L', lcolor = ROOT.kBlue, lwidth = 2, lstyle = ROOT.kSolid)
    canvas.legend.add('bkg', title = 'Background', opt = 'L', lcolor = ROOT.kGreen, lwidth = 2, lstyle = ROOT.kDashed)
    if hmcbkg:
        canvas.legend.add('mcbkg', title = 'Background (MC truth)', opt = 'LF', lcolor = ROOT.kRed, lwidth = 1, fcolor = ROOT.kRed, fstyle = 3003)

    if targHist.sumEntries() > 500.:
        plotBinning = plotBinningT
    else:
        plotBinning = plotBinningT2

    frame = mass.frame()
    targHist.plotOn(frame, ROOT.RooFit.Binning(*plotBinning))
    model.plotOn(frame)
    model.plotOn(frame, ROOT.RooFit.Components(bkgModel + '_' + suffix), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kGreen))
    frame.SetTitle('')
    frame.SetMinimum(0.)

    canvas.addHistogram(frame, clone = True, drawOpt = '')
    if hmcbkg:
        htruth = hmcbkg.Rebin(hmcbkg.GetNbinsX() / plotBinning[0], 'truth')
        canvas.legend.apply('mcbkg', htruth)
        canvas.addHistogram(htruth)

    canvas.rlimits = (-2.15, 2.15)
    canvas.xtitle = "m_{ee} (GeV)" 
    
    canvas.Update(rList = [], logy = False)

    frame.Print()

    # adding ratio pad
    fitcurve = frame.findObject(model.GetName() + '_Norm[mass]')

    hresid = targHist.createHistogram('residual', mass, ROOT.RooFit.Binning(*plotBinning))

    rdata = ROOT.TGraphErrors(hresid.GetNbinsX())

    for iP in range(rdata.GetN()):
        x = hresid.GetXaxis().GetBinCenter(iP + 1)
        nData = hresid.GetBinContent(iP + 1)
        statErr = hresid.GetBinError(iP + 1)
        nFit = fitcurve.interpolate(x)
        if statErr > 0.:
            rdata.SetPoint(iP, x, (nData - nFit) / statErr)
        else:
            rdata.SetPoint(iP, x, (nData - nFit))
        # rdata.SetPointError(iP, 0., dmet.GetBinError(iP + 1) / norm)

    rdata.SetMarkerStyle(8)
    rdata.SetMarkerColor(ROOT.kBlack)
    rdata.SetLineColor(ROOT.kBlack)

    canvas.ratioPad.cd()

    rframe = ROOT.TH1F('rframe', '', 1, *plotBinning[1:])
    rframe.GetYaxis().SetRangeUser(-2.15, 2.15)
    rframe.Draw()

    line = ROOT.TLine(plotBinning[1], 0., plotBinning[2], 0.)
    line.SetLineWidth(2)
    line.SetLineColor(ROOT.kBlue)
    line.Draw()

    rdata.Draw('EP')

    canvas._needUpdate = False

    if not plotName:
        plotName = 'fit_' + dataType + '_' + suffix
    if alt:
        plotName += '_' + alt

    canvas.printWeb(plotDir, plotName, logy = False)

    rframe.Delete()
    if hmcbkg:
        htruth.Delete()
    hresid.Delete()
