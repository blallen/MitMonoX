import os
import sys
import math
import ROOT

WEBDIR = os.environ['HOME'] + '/public_html/cmsplots'

ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetTextFont(42)
ROOT.gStyle.SetLabelSize(0.045, 'X')
ROOT.gStyle.SetLabelSize(0.045, 'Y')
ROOT.gStyle.SetTitleSize(0.045, 'X')
ROOT.gStyle.SetTitleSize(0.045, 'Y')
ROOT.gStyle.SetTitleOffset(1.35, 'X')
ROOT.gStyle.SetTitleOffset(1.35, 'Y')
ROOT.gStyle.SetNdivisions(208, 'X')
ROOT.gStyle.SetNdivisions(208, 'Y')
ROOT.gStyle.SetFillStyle(0)

def makeText(x1, y1, x2, y2, align = 22, font = 42, size = 0.035, ndc = True):
    if type(align) is str:
        al = 0
        if 'left' in align:
            al += 10
        elif 'right' in align:
            al += 30
        else:
            al += 20

        if 'bottom' in align:
            al += 1
        elif 'top' in align:
            al += 3
        else:
            al += 2

        align = al

    pave = ROOT.TPaveText()
    if ndc:
        pave.SetX1NDC(x1)
        pave.SetX2NDC(x2)
        pave.SetY1NDC(y1)
        pave.SetY2NDC(y2)
    else:
        pave.SetX1(x1)
        pave.SetX2(x2)
        pave.SetY1(y1)
        pave.SetY2(y2)

    pave.SetTextAlign(align)
    pave.SetTextSize(size)
    pave.SetFillStyle(0)
    pave.SetBorderSize(0)
    pave.SetMargin(0.)
    pave.SetTextFont(font)

    return pave


def makeAxis(axis, xmin = 0., xmax = 1., x = 0., ymin = 0., ymax = 1., y = 0., vmin = 0., vmax = 1., ndiv = 205, font = 42, titleSize = 0.05, log = False, blank = True, opposite = False):
    if axis == 'X':
        args = (xmin, y, xmax, y, vmin, vmax, ndiv)
    elif axis == 'Y':
        args = (x, ymin, x, ymax, vmin, vmax, ndiv)
    else:
        raise RuntimeError('Invalid axis ' + axis)

    options = 'S'
    if log:
        options += 'G'
    if blank:
        options += 'B'
    if opposite:
        if axis == 'X':
            options += '-'
        else:
            options += '+'

    args = tuple(list(args) + [options])

    gaxis = ROOT.TGaxis(*args)

    gaxis.SetLabelFont(font)
    gaxis.SetTitleFont(font)
    # if titleSize > 0.:
    #     gaxis.SetTitleOffset(ROOT.gStyle.GetTitleOffset(axis) * 0.05 / titleSize)
    gaxis.SetTitleSize(titleSize)
    gaxis.SetLabelSize(0.95 * titleSize)
    gaxis.SetTickLength(0.03)
    gaxis.SetGridLength(0.)

    return gaxis


class Legend(object):

    Attributes = [
        'LineWidth',
        'LineStyle',
        'LineColor',
        'FillStyle',
        'FillColor',
        'MarkerSize',
        'MarkerStyle',
        'MarkerColor'
    ]

    def __init__(self, x1, y1, x2, y2):
        self.legend = ROOT.TLegend(x1, y1, x2, y2)
        self.legend.SetFillStyle(0)
        self.legend.SetBorderSize(0)
        self.legend.SetTextSize(0.05)
        self.legend.SetTextFont(42)
        self.legend.SetTextAlign(12)

        self.entries = {}
        self.ncolumns = -1
        self.defaultOrder = []
        self._modified = False

    def setPosition(self, x1, y1, x2, y2, fix = True):
        self.legend.SetX1(x1)
        self.legend.SetY1(y1)
        self.legend.SetX2(x2)
        self.legend.SetY2(y2)

    def add(self, obl, title = None, opt = 'LFP', color = -1, lwidth = -1, lstyle = -1, lcolor = -1, fstyle = -1, fcolor = -1, msize = -1, mstyle = -1, mcolor = -1):
        ent = ROOT.TLegendEntry(0)

        modified = []
        if type(obl) is str:
            name = obl

        else:
            obj = obl
            name = obj.GetName()
            if title is None:
                title = obj.GetTitle()

            for at in Legend.Attributes:
                try:
                    getattr(ent, 'Set' + at)(getattr(obj, 'Get' + at)())
                    modified.append(at)
                except AttributeError:
                    pass

        ent.SetLabel(title)
        ent.SetOption(opt)

        args = [lwidth, lstyle, lcolor, fstyle, fcolor, msize, mstyle, mcolor]
        for iA in range(len(args)):
            at = Legend.Attributes[iA]
            if args[iA] == -1:
                continue

            getattr(ent, 'Set' + at)(args[iA])

        if color != -1:
            for at in Legend.Attributes:
                if 'Color' in at:
                    getattr(ent, 'Set' + at)(color)
            
        self.entries[name] = ent
        self.defaultOrder.append(name)

        self._modified = True

    def remove(self, name):
        self.entries.pop(name)
        self.defaultOrder.remove(name)

        self._modified = True

    def apply(self, name, obj, opt = 'LFP'):
        entry = self.entries[name]

        for at in Legend.Attributes:
            if 'Line' in at and 'L' not in opt:
                continue
            if 'Fill' in at and 'F' not in opt:
                continue
            if 'Marker' in at and 'P' not in opt:
                continue

            try:
                getattr(obj, 'Set' + at)(getattr(entry, 'Get' + at)())
            except AttributeError:
                pass

    @staticmethod
    def copyStyle(src, dest):
        for at in Legend.Attributes:
            try:
                getattr(dest, 'Set' + at)(getattr(src, 'Get' + at)())
            except:
                pass

    def construct(self, order = None):
        if not self._modified:
            return

        if order is True or order is None:
            order = self.defaultOrder

        self.legend.Clear()

        if self.ncolumns < 0:
            self.ncolumns = -int(math.ceil(float(len(self.entries)) / 5.))

        self.legend.SetNColumns(abs(self.ncolumns))

        for name in order:
            ent = self.entries[name]
            self.legend.AddEntry(ent, ent.GetLabel(), ent.GetOption())

        self._modified = False

    def Clear(self):
        self.legend.Clear()
        self.entries = {}
        self.defaultOrder = []

    def Draw(self, order = []):
        if self._modified:
            self.construct(order)

        self.legend.Draw()

    def __getattr__(self, name):
        return getattr(self.legend, name)


class Drawable(object):
    def __init__(self, obj, drawOpt):
        self.obj = obj
        self.drawOpt = drawOpt

    def __getattr__(self, attr):
        return getattr(self.obj, attr)

    def Clone(self, name = ''):
        clone = self.obj.Clone(name)
        return Drawable(clone, self.drawOpt)


class Histogram(Drawable):
    def __init__(self, histogram, drawOpt, useRooHist = False, binWidthNormalized = True):
        Drawable.__init__(self, histogram, drawOpt)

        self.useRooHist = useRooHist
        self.binWidthNormalized = binWidthNormalized

    def Clone(self, name = ''):
        clone = self.obj.Clone(name)
        return Histogram(clone, self.drawOpt, self.useRooHist, self.binWidthNormalized)


class SimpleCanvas(object):

    XMIN = 0.15
    XMAX = 0.95
    YMIN = 0.12
    YMAX = 0.92

    def __init__(self, name = 'cSimple', title = 'simple', lumi = -1., sim = False, cms = False, prelim = False, xmax = None):
        self.canvas = ROOT.TCanvas(name, title, 600, 600)
        self.canvas.SetTopMargin(1. - SimpleCanvas.YMAX)
        if xmax is not None:
            self.canvas.SetRightMargin(1. - xmax)
        else:
            self.canvas.SetRightMargin(1. - SimpleCanvas.XMAX)
        self.canvas.SetBottomMargin(SimpleCanvas.YMIN)
        self.canvas.SetLeftMargin(SimpleCanvas.XMIN)
        self.canvas.SetTicky(1)

        self._histograms = []
        self._objects = []

        self.legend = Legend(0.7, 0.55, 0.95, SimpleCanvas.YMAX - 0.03)

        self._logx = False
        self._logy = True

        self.xtitle = ''
        self.ytitle = 'Number of Events'

        self.xlimits = (0., -1.)
        self.ylimits = (0., -1.)

        self.title = ''
        self.textside = 'left'
        self.lumi = lumi

        self.selection = None

        self.titlePave = makeText(SimpleCanvas.XMIN, SimpleCanvas.YMAX, SimpleCanvas.XMAX, 1.)

        if cms:
            self.cmsPave = makeText(0.18, SimpleCanvas.YMAX - 0.12, 0.3, SimpleCanvas.YMAX - 0.01, align = 11, font = 62)
        else:
            self.cmsPave = None

        self.sim = sim

        self.prelim = prelim

        gDirectory = ROOT.gDirectory
        ROOT.gROOT.cd()
        self._hStore = ROOT.gROOT.mkdir(name + '_hstore')
        gDirectory.cd()

        self._needUpdate = True
        self._temporaries = []

    def __getattr__(self, name):
        return getattr(self.canvas, name)

    def _modified(self):
        self._needUpdate = True
        
        for obj in self._temporaries:
            try:
                obj.Delete()
            except:
                pass

        self._temporaries = []

    def addHistogram(self, hist, drawOpt = None, idx = -1, clone = True, asymErr = False, binWidthNormalized = True):
        """
        Any object with the following methods can be added as a "histogram":
        Draw, Get/SetMaximum/Minimum, GetX/Yaxis()
        """

        gDirectory = ROOT.gDirectory

        if idx < 0:
            idx = len(self._histograms)

        if idx > len(self._histograms):
            raise RuntimeError('Invalid histogram index ' + str(idx))

        if drawOpt is None:
            if hist.InheritsFrom(ROOT.TH1.Class()):
                drawOpt = 'HIST'
            elif hist.InheritsFrom(ROOT.TGraph.Class()):
                drawOpt = 'P'
            else:
                drawOpt = ''

        if idx == len(self._histograms):
            # new histogram
            if clone:
                self._hStore.cd()
                self._histograms.append(Histogram(hist.Clone(), drawOpt.upper(), useRooHist = asymErr, binWidthNormalized = binWidthNormalized))
            else:
                self._histograms.append(Histogram(hist, drawOpt.upper(), useRooHist = asymErr, binWidthNormalized = binWidthNormalized))

            newHist = self._histograms[-1]
            try:
                if newHist.GetSumw2().fN == 0:
                    newHist.Sumw2()
            except:
                pass

        else:
            self._histograms[idx].Add(hist)

        gDirectory.cd()

        self._modified()

        return idx


    def addObject(self, obj, clone = True, name = None, drawOpt = None):
        if clone:
            if name is None:
                self._objects.append(Drawable(obj.Clone(), drawOpt))
            else:
                self._objects.append(Drawable(obj.Clone(name), drawOpt))
        else:
            self._objects.append(Drawable(obj, drawOpt))

    def addLine(self, x1, y1, x2, y2, color = ROOT.kBlack, width = 1, style = ROOT.kSolid, cls = ROOT.TLine):
        line = cls(x1, y1, x2, y2)
        line.SetLineColor(color)
        line.SetLineWidth(width)
        line.SetLineStyle(style)
        self._objects.append(Drawable(line, None))

        self._modified()

        return line

    def addText(self, text, x1, y1, x2, y2, align = 22, font = 42, size = 0.035, ndc = True):
        pave = makeText(x1, y1, x2, y2, align = align, font = font, size = size, ndc = ndc)
        pave.AddText(text)
        self._objects.append(Drawable(pave, None))

        return pave

    def applyStyles(self):
        for hist in self._histograms:
            if hist.GetName() in self.legend.entries:
                self.legend.apply(hist.GetName(), hist)

    def Clear(self, full = False, xmax = None):
        name = self.canvas.GetName()
        title = self.canvas.GetTitle()
        ROOT.gROOT.GetListOfCanvases().Remove(self.canvas)
        self.canvas.IsA().Destructor(self.canvas)

        self.canvas = ROOT.TCanvas(name, title, 600, 600)
        self.canvas.SetTopMargin(1. - SimpleCanvas.YMAX)
        if xmax is not None:
            self.canvas.SetRightMargin(1. - xmax)
        else:
            self.canvas.SetRightMargin(1. - SimpleCanvas.XMAX)
        self.canvas.SetBottomMargin(SimpleCanvas.YMIN)
        self.canvas.SetLeftMargin(SimpleCanvas.XMIN)

        if full:
            self.legend.Clear()
            self._logx = False
            self._logy = True
            self.title = ''
            self.textside = 'left'
            self._objects = []

        for h in self._histograms:
            h.Delete()

        self._histograms = []

        self._modified()

    def Update(self, hList = None, logx = None, logy = None, drawLegend = True):
        if logx is not None:
            self.canvas.SetLogx(logx)
            self.canvas.Update()

        if logy is not None:
            self.canvas.SetLogy(logy)
            self.canvas.Update()

        if not self._needUpdate:
            return

        if logx is None:
            logx = self._logx

        if logy is None:
            logy = self._logy

        # list of histograms to draw
        if hList is None:
            hList = range(len(self._histograms))

        base = self._updateMainPad(self.canvas, hList, logx, logy, drawLegend = drawLegend)

        if base:
            if self.xtitle:
                base.GetXaxis().SetTitle(self.xtitle)
            if self.ytitle:
                base.GetYaxis().SetTitle(self.ytitle)

        self.canvas.Update()

        self._needUpdate = False

    def _updateMainPad(self, pad, hList, logx, logy, rooHists = None, drawLegend = True):
        gPad = ROOT.gPad

        pad.cd()
        pad.SetLogx(logx)
        pad.SetLogy(logy)

        base = None

        if len(hList) > 0:
            # draw base
            base = self._histograms[hList[0]]
            maximum, minimum = self._drawHist(base, True, rooHists)

            pad.Update()
   
            # draw other histograms
            for ih in hList[1:]:
                hist = self._histograms[ih]
                hmax, hmin = self._drawHist(hist, False, rooHists)

                maximum = max(maximum, hmax)
                minimum = min(minimum, hmin)

            pad.Update()

            if self.xlimits[1] > self.xlimits[0]:
                if base.InheritsFrom(ROOT.TH1.Class()):
                    base.GetXaxis().SetRangeUser(self.xlimits[0], self.xlimits[1])
                elif base.InheritsFrom(ROOT.TGraph.Class()):
                    base.GetXaxis().SetLimits(*self.xlimits)

            if self.ylimits[1] > self.ylimits[0]:
                # y range specified - override
                minimum, maximum = self.ylimits

            elif logy:
                if minimum <= 0.:
                    minimum = 1.e-5
                else:
                    minimum *= 0.2
                maximum *= 5.

            else:
                minimum = min(minimum, 0.)
                maximum *= 1.3

            base.SetMinimum(minimum)
            base.SetMaximum(maximum)

            base.GetXaxis().SetTitleOffset(1.15)
            base.GetYaxis().SetTitleOffset(1.5)

            if base.InheritsFrom(ROOT.THStack.Class()) and base.GetHistogram():
                # THStack has an absolutely retarded hard-coded weird override of minimum and maximum:
                #   if (!fHistogram->TestBit(TH1::kIsZoomed)) {
                #      if (nostack && fMaximum != -1111) fHistogram->SetMaximum(fMaximum);
                #      else {
                #         if (gPad->GetLogy())           fHistogram->SetMaximum(themax*(1+0.2*TMath::Log10(themax/themin)));
                #         else                           fHistogram->SetMaximum((1+gStyle->GetHistTopMargin())*themax);
                #      }
                #      if (nostack && fMinimum != -1111) fHistogram->SetMinimum(fMinimum);
                #      else {
                #         if (gPad->GetLogy())           fHistogram->SetMinimum(themin/(1+0.5*TMath::Log10(themax/themin)));
                #         else                           fHistogram->SetMinimum(themin);
                #      }
                #   }
                #
                # We hack our way through here by setting this kIsZoomed
                base.GetHistogram().SetBit(ROOT.TH1.kIsZoomed)
                base.GetHistogram().SetMinimum(minimum)
                base.GetHistogram().SetMaximum(maximum)

            if len(self.legend.entries) != 0 and drawLegend:
                self.legend.Draw(drawLegend)

        for obj in self._objects:
            if obj.drawOpt is None:
                obj.obj.Draw('SAME')
            else:
                obj.obj.Draw(obj.drawOpt + ' SAME')

        self.drawText()

        gPad.cd()

        return base

    def _drawHist(self, hist, first, rooHists):
        if hist.useRooHist:
            if hist.binWidthNormalized:
                tmp = hist.obj.Clone('tmp')
                for iX in range(1, tmp.GetNbinsX() + 1):
                    w = tmp.GetXaxis().GetBinWidth(iX)
                    tmp.SetBinContent(iX, tmp.GetBinContent(iX) * w)
                    tmp.SetBinError(iX, tmp.GetBinError(iX) * w)
        
                graph = ROOT.RooHist(tmp, 1.)
                tmp.Delete()
            else:
                graph = ROOT.RooHist(hist.obj)

            self._temporaries.append(graph)

            if rooHists is not None:
                rooHists[hist] = graph

            drawOpt = hist.drawOpt
            if first:
                drawOpt += 'A'
                
            graph.Draw(drawOpt)

        else:
            drawOpt = hist.drawOpt
            if first and hist.obj.InheritsFrom(ROOT.TGraph.Class()):
                drawOpt += 'A'
            elif not first and (hist.InheritsFrom(ROOT.TH1.Class()) or hist.InheritsFrom(ROOT.TF1.Class())):
                drawOpt += ' SAME'

            hist.obj.Draw(drawOpt)

        return hist.obj.GetMaximum(), hist.obj.GetMinimum()

    def _fixTHStack(self, **options):
        if 'hList' in options:
            hList = options['hList']
        else:
            hList = range(len(self._histograms))

        if len(hList) == 0:
            return

        base = self._histograms[hList[0]]

        if base.InheritsFrom(ROOT.THStack.Class()) and base.GetHistogram():
            base.GetHistogram().SetBit(ROOT.TH1.kIsZoomed, False)

    def SetLogx(self, logx):
        self._logx = logx
        self._modified()

    def SetLogy(self, logy):
        self._logy = logy
        self._modified()

    def drawText(self):
        self.titlePave.Clear()
        self.titlePave.AddText(self.title)
        self.titlePave.Draw()

        if self.cmsPave:
            if self.textside == 'right':
                self.cmsPave.SetX1NDC(0.7)
                self.cmsPave.SetX2NDC(0.92)
                self.cmsPave.SetTextAlign(31)
            else:
                self.cmsPave.SetX1NDC(0.18)
                self.cmsPave.SetX2NDC(0.4)
                self.cmsPave.SetTextAlign(11)

            self.cmsPave.Clear()

            if self.sim:
                self.cmsPave.AddText('#splitline{CMS}{#font[52]{Simulation}}')
            elif self.prelim:
                self.cmsPave.AddText('#splitline{CMS}{#font[52]{Preliminary}}')
            else:
                self.cmsPave.AddText('#splitline{CMS}{#font[52]{  }}')
    
            self.cmsPave.Draw()

            if self.lumi > 0.:
                lumiPave = makeText(0.6, SimpleCanvas.YMAX - 0.025, SimpleCanvas.XMAX - 0.1, 1., align = 32)
                self._temporaries.append(lumiPave)

                if self.lumi > 1000.:
                    lumiPave.AddText('%.1f fb^{-1} (13 TeV)' % (self.lumi / 1000.))
                else:
                    lumiPave.AddText('%.1f pb^{-1} (13 TeV)' % self.lumi)

                lumiPave.Draw()

    def printWeb(self, directory, name, **options):
        self.Update(**options)

        targetDir = WEBDIR + '/' + directory
        if not os.path.isdir(targetDir):
            os.makedirs(targetDir)

        self.canvas.Print(targetDir + '/' + name + '.pdf', 'pdf')
        self.canvas.Print(targetDir + '/' + name + '.png', 'png')
        self.canvas.Print(targetDir + '/' + name + '.C', 'C')

        self._fixTHStack(**options)

        if self.selection is not None:
            selFile = open(targetDir + '/' + name + '.txt', 'w')
            selFile.write(self.selection + ' \n')
            selFile.close()

class TwoDimCanvas(SimpleCanvas):
    """
    2D version of SimpleCanvas
    """

    def __init__(self, name = 'cTwoDim', title = 'TwoDim', lumi = -1., sim = False, cms = False, prelim = False, xmax = None):
        SimpleCanvas.__init__(self, name = name, title = title, lumi = lumi, sim = sim, cms = cms, prelim = prelim, xmax = xmax)

        ROOT.gStyle.SetTitleOffset(200., 'X')
        ROOT.gStyle.SetTitleOffset(2.6, 'Y')

        self.canvas.SetCanvasSize(1000, 1000)

        self._logy = False
        self._logz = True
        self.ztitle = ''
        self.zlimits = (0., -1.)

        if cms:
            self.cmsPave = makeText(0.18, SimpleCanvas.YMAX - 0.12, 0.3, SimpleCanvas.YMAX - 0.01, align = 11, font = 62)
        else:
            self.cmsPave = None

        self._modified()
    
    def Clear(self, full = False, xmax = None):
        SimpleCanvas.Clear(self, full = full, xmax = xmax)
        
        self.canvas.SetCanvasSize(1000, 1000)

        if full:
            self._logy = False
            self._logz = True

        self._modified()

    def Update(self, hList = None, logx = None, logy = None, logz = None, drawLegend = True):
        if logx is not None:
            self.canvas.SetLogx(logx)
            self.canvas.Update()

        if logy is not None:
            self.canvas.SetLogy(logy)
            self.canvas.Update()

        if logz is not None:
            self.canvas.SetLogz(logz)
            self.canvas.Update()

        if not self._needUpdate:
            return

        if logx is None:
            logx = self._logx

        if logy is None:
            logy = self._logy

        if logz is None:
            logy = self._logz

        # list of histograms to draw
        if hList is None:
            hList = range(len(self._histograms))

        base = self._updateMainPad(self.canvas, hList, logx, logy, logz, drawLegend = drawLegend)

        if base:
            if self.xtitle:
                base.GetXaxis().SetTitle(self.xtitle)
            if self.ytitle:
                base.GetYaxis().SetTitle(self.ytitle)
            if self.ztitle:
                base.GetZaxis().SetTitle(self.ztitle)

            base.GetXaxis().SetTitleOffset(1.3)
            base.GetYaxis().SetTitleOffset(2.3)
            base.GetZaxis().SetTitleOffset(1.45)

        self.canvas.Update()

        self._needUpdate = False

    def _updateMainPad(self, pad, hList, logx, logy, logz, rooHists = None, drawLegend = True):
        gPad = ROOT.gPad

        pad.cd()
        pad.SetLogx(logx)
        pad.SetLogy(logy)
        pad.SetLogz(logz)

        base = None

        if len(hList) > 0:
            # draw base
            base = self._histograms[hList[0]]
            maximum, minimum = self._drawHist(base, True, rooHists)

            pad.Update()
   
            # draw other histograms
            for ih in hList[1:]:
                hist = self._histograms[ih]
                hmax, hmin = self._drawHist(hist, False, rooHists)

                maximum = max(maximum, hmax)
                minimum = min(minimum, hmin)

            pad.Update()

            if self.xlimits[1] > self.xlimits[0]:
                if base.InheritsFrom(ROOT.TH1.Class()):
                    base.GetXaxis().SetRangeUser(self.xlimits[0], self.xlimits[1])
                elif base.InheritsFrom(ROOT.TGraph.Class()):
                    base.GetXaxis().SetLimits(*self.xlimits)

            if self.ylimits[1] > self.ylimits[0]:
                if base.InheritsFrom(ROOT.TH1.Class()):
                    base.GetYaxis().SetRangeUser(self.ylimits[0], self.ylimits[1])
                elif base.InheritsFrom(ROOT.TGraph.Class()):
                    base.GetYaxis().SetLimits(*self.ylimits)

            if self.zlimits[1] > self.zlimits[0]:
                # z range specified - override
                minimum, maximum = self.zlimits

            elif logz:
                if minimum <= 0.:
                    minimum = 1.e-6
                else:
                    minimum *= 0.2
                maximum *= 5.

            else:
                minimum = min(minimum, 0.)
                maximum *= 1.3

            base.SetMinimum(minimum)
            base.SetMaximum(maximum)

            if base.InheritsFrom(ROOT.THStack.Class()) and base.GetHistogram():
                base.GetHistogram().SetBit(ROOT.TH1.kIsZoomed)
                base.GetHistogram().SetMinimum(minimum)
                base.GetHistogram().SetMaximum(maximum)

            if len(self.legend.entries) != 0 and drawLegend:
                self.legend.Draw(drawLegend)

        for obj in self._objects:
            if obj.drawOpt is None:
                obj.obj.Draw('SAME')
            else:
                obj.obj.Draw(obj.drawOpt + ' SAME')

        self.drawText()

        gPad.cd()

        return base

    def SetLogz(self, logz):
        self._logz = logz
        self._modified()

class Normalizer(object):
    """
    Helper class for normalizing histograms and graphs against histograms, graphs, or functions.
    See the RatioCanvas docstring for details.
    """

    def __init__(self, normObj, errtype):
        if not normObj.InheritsFrom(ROOT.TH1.Class()) and \
                not normObj.InheritsFrom(ROOT.TGraph.Class()) and \
                not normObj.InheritsFrom(ROOT.TF1.Class()):
            raise RuntimeError('Cannot normalize with ' + str(normObj))

        self._normObj = normObj
        self._errtype = errtype

    def normalize(self, obj, name):
        if obj.InheritsFrom(ROOT.TH1.Class()):
            # normalizing a TH1

            # can be a TProfile - need to create a TH1D (cannot just clone)
            if obj.GetXaxis().GetXbins().GetSize() == 0:
                targ = ROOT.TH1D(name, '', obj.GetNbinsX(), obj.GetXaxis().GetXmin(), obj.GetXaxis().GetXmax())
            else:
                targ = ROOT.TH1D(name, '', obj.GetNbinsX(), obj.GetXaxis().GetXbins().GetArray())

            for iX in range(1, obj.GetNbinsX() + 1):
                targ.SetBinContent(iX, obj.GetBinContent(iX))
                targ.SetBinError(iX, obj.GetBinError(iX))
#            targ = obj.Clone(name)
#            if targ.InheritsFrom(ROOT.TProfile.Class()):
#                for iX in range(1, obj.GetNbinsX() + 1):
#                    targ.SetBinEntries(iX, obj.GetBinEntries(iX))

            # apply style
            tmp = Legend(0., 0., 0., 0.)
            tmp.add(obj)
            tmp.apply(obj.GetName(), targ)

            targAxis = targ.GetXaxis()

            if self._normObj.InheritsFrom(ROOT.TH1.Class()):
                # base is TH1 -> check axis consistency
                normAxis = self._normObj.GetXaxis()

                if not ROOT.TMath.AreEqualRel(normAxis.GetXmin(), targAxis.GetXmin(), 1.e-12):
                    raise RuntimeError('Inconsistent axes')
                if not ROOT.TMath.AreEqualRel(normAxis.GetXmax(), targAxis.GetXmax(), 1.e-12):
                    raise RuntimeError('Inconsistent axes')

                for iX in range(1, normAxis.GetNbins() + 1):
                    if not ROOT.TMath.AreEqualRel(normAxis.GetBinLowEdge(iX), targAxis.GetBinLowEdge(iX), 1.e-12):
                        raise RuntimeError('Inconsistent axes')
                    if not ROOT.TMath.AreEqualRel(normAxis.GetBinUpEdge(iX), targAxis.GetBinUpEdge(iX), 1.e-12):
                        raise RuntimeError('Inconsistent axes')

            for iX in range(1, targAxis.GetNbins() + 1):
                if self._normObj.InheritsFrom(ROOT.TH1.Class()):
                    # base is TH1 -> bin-by-bin norm
                    norm = self._normObj.GetBinContent(iX)
                    derr = self._normObj.GetBinError(iX)

                elif self._normObj.InheritsFrom(ROOT.TGraph.Class()):
                    # base is TGraph -> find a point in the bin
                    pnorm = -1
                    for iP in range(self._normObj.GetN()):
                        x = self._normObj.GetX()[iP]
                        if x >= targAxis.GetBinLowEdge(iX) and x < targAxis.GetBinUpEdge(iX):
                            if pnorm != -1:
                                # there is already a matching point!
                                raise RuntimeError('Multiple graph points in bin ' + str(iX))

                            pnorm = iP

                    if pnorm == -1:
                        raise RuntimeError('No graph point in bin ' + str(iX))

                    norm = self._normObj.GetY()[pnorm]
                    derr = self._normObj.GetErrorY(pnorm)

                elif self._normObj.InheritsFrom(ROOT.TF1.Class()):
                    norm = self._normObj.Integral(targAxis.GetBinLowEdge(iX), targAxis.GetBinUpEdge(iX))
                    derr = 0.

                if norm != 0.:
                    scale = 1. / norm
                else:
                    scale = 0.

                targ.SetBinContent(iX, targ.GetBinContent(iX) * scale)

                if self._errtype == 'norm':
                    targ.SetBinError(iX, targ.GetBinError(iX) * scale)
                elif self._errtype == 'quad':
                    if obj.GetBinContent(iX) > 0.:
                        nrerr = obj.GetBinError(iX) / obj.GetBinContent(iX)
                        drerr = derr * scale
                        targ.SetBinError(iX, targ.GetBinContent(iX) * math.sqrt(nrerr * nrerr + drerr * drerr))
                elif self._errtype == 'binom':
                    if norm != 0.:
                        up = ROOT.TEfficiency.ClopperPearson(int(norm), int(obj.GetBinContent(iX)), 0.6826895, True) - targ.GetBinContent(iX)
                        down = targ.GetBinContent(iX) - ROOT.TEfficiency.ClopperPearson(int(norm), int(obj.GetBinContent(iX)), 0.6826895, False)
                    else:
                        up = 0.
                        down = 0.

                    targ.SetBinError(iX, (up + down) * 0.5)

        elif obj.InheritsFrom(ROOT.TGraph.Class()):
            # normalizing a TGraph
            targ = obj.Clone(name)

            for iP in range(targ.GetN()):
                x = targ.GetX()[iP]

                if self._normObj.InheritsFrom(ROOT.TH1.Class()):
                    iX = self._normObj.FindFixBin(x)
                    norm = self._normObj.GetBinContent(iX)
                    derr = self._normObj.GetBinError(iX)

                elif self._normObj.InheritsFrom(ROOT.TGraph.Class()):
                    if not ROOT.TMath.AreEqualRel(x, self._normObj.GetX()[iP], 1.e-12):
                        raise RuntimeError('X values do not match')

                    norm = self._normObj.GetY()[iP]
                    derr = self._normObj.GetErrorY(iP)

                elif self._normObj.InheritsFrom(ROOT.TF1.Class()):
                    norm = self._normObj.Eval(x)
                    derr = 0.

                if norm != 0.:
                    scale = 1. / norm
                else:
                    scale = 0.

                targ.SetPoint(iP, x, targ.GetY()[iP] * scale)

                sym = targ.InheritsFrom(ROOT.TGraphErrors.Class())
                asym = targ.InheritsFrom(ROOT.TGraphAsymmErrors.Class())

                if self._errtype == 'norm':
                    if sym:
                        targ.SetPointError(iP, targ.GetErrorX(iP), targ.GetErrorY(iP) * scale)
                    else:
                        targ.SetPointEYlow(iP, obj.GetErrorYlow(iP) * scale)
                        targ.SetPointEYhigh(iP, obj.GetErrorYhigh(iP) * scale)

                elif self._errtype == 'quad':
                    drerr = derr * scale
                    if obj.GetY()[iP] > 0.:
                        y = targ.GetY()[iP]
                        if sym:
                            nrerr = obj.GetErrorY(iP) / obj.GetY()[iP]
                            targ.SetPointError(iP, y * math.sqrt(nrerr * nrerr + drerr * drerr))
                        else:
                            nrerrup = obj.GetErrorYhigh(iP) / obj.GetY()[iP]
                            nrerrdown = obj.GetErrorYlow(iP) / obj.GetY()[iP]
                            targ.SetPointEYlow(iP, y * math.sqrt(nrerrup * nrerrup + drerr * drerr))
                            targ.SetPointEYhigh(iP, y * math.sqrt(nrerrdown * nrerrdown + drerr * drerr))
                        
                elif self._errtype == 'binom':
                    if norm != 0.:
                        up = ROOT.TEfficiency.ClopperPearson(int(norm), int(obj.GetY()[iP]), 0.6826895, True) - targ.GetY()[iP]
                        down = targ.GetY()[iP] - ROOT.TEfficiency.ClopperPearson(int(norm), int(obj.GetY()[iP]), 0.6826895, False)
                    else:
                        up = 0.
                        down = 0.

                    if sym:
                        targ.SetPointError(iP, (up + down) * 0.5)
                    else:
                        targ.SetPointEYlow(iP, down)
                        targ.SetPointEYhigh(iP, up)

        elif obj.InheritsFrom(ROOT.TF1.Class()):
            raise RuntimeError('Not implemented')

        else:
            raise RuntimeError('Cannot normalize ' + str(obj))

        return targ


class RatioCanvas(SimpleCanvas):
    """
    Canvas with a ratio panel at the bottom. Can plot TH1, TGraph, and TF1.
    By default the "base" of the ratio plot is the first object to be added to the canvas.
    This behavior can be changed by passing the argument rList to Update(). The content of the
    list should be the histogram indices to be included in the ratio plot, and the first element
    will be used as the base.

    Ratio computation depends on the combination of base and target objects to be plotted:
                         TH1 Target    TGraph Target          TF1 Target
    TH1 Base   :    content/content        y/content     (value/content)
    TGraph Base:          content/y              y/y           (value/y)
    TF1 Base   : content*w/integral          y/value       (value/value)

    In other words, all objects are assumed to represent "differential" values. For example
    for TH1, this means the bin contents must be width-normalized number of events.
    TH1/TH1 combination is allowed only for histograms with matching bin boundaries.
    Similarly, TGraph/TGraph combination works only when abscissa (x) values align.
    TF1 target case is not implemented.

    By default, error bars in the ratio plot receive identical normalization to y values.
    You can change the behavior by setting the rerr flag:
     - 'norm': normalized numerator uncertainty (default)
     - 'quad': propagated error on ratio
     - 'binom': Clopper-Pearson binomial uncertainty (statistical, for efficiencies)

    Normalized values are set to 0 if the denominator is 0.
    """

    PLOT_YMIN = 0.32
    PLOT_YMAX = SimpleCanvas.YMAX
    RATIO_YMIN = 0.1
    RATIO_YMAX = 0.29

    def __init__(self, name = 'cRatio', title = 'Ratio', lumi = -1., sim = False, cms = False, prelim = False):
        SimpleCanvas.__init__(self, name = name, title = title, lumi = lumi, sim = sim, cms = cms, prelim = prelim)

        self.canvas.SetCanvasSize(600, 680)

        self.xaxis = makeAxis('X', xmin = SimpleCanvas.XMIN, xmax = SimpleCanvas.XMAX, y = RatioCanvas.RATIO_YMIN, titleSize = 0.045)
        # self.xaxis.SetTitleOffset(self.xaxis.GetTitleOffset() * 1.05)

        self.xaxism = makeAxis('X', xmin = SimpleCanvas.XMIN, xmax = SimpleCanvas.XMAX, y = RatioCanvas.PLOT_YMIN, titleSize = 0.)

        self.yaxis = makeAxis('Y', ymin = RatioCanvas.PLOT_YMIN, ymax = RatioCanvas.PLOT_YMAX, x = SimpleCanvas.XMIN, vmin = 0.1, vmax = 1., log = True)
        self.yaxis.SetTitleOffset(1.5)

        self.yaxisr = makeAxis('Y', ymin = RatioCanvas.PLOT_YMIN, ymax = RatioCanvas.PLOT_YMAX, x = SimpleCanvas.XMAX, vmin = 0.1, vmax = 1., titleSize = 0., log = True, opposite = True)

        self.raxis = makeAxis('Y', ymin = RatioCanvas.RATIO_YMIN, ymax = RatioCanvas.RATIO_YMAX, x = SimpleCanvas.XMIN, vmax = 2., titleSize = 0.04)
        self.raxisr = makeAxis('Y', ymin = RatioCanvas.RATIO_YMIN, ymax = RatioCanvas.RATIO_YMAX, x = SimpleCanvas.XMAX, vmax = 2., titleSize = 0., opposite = True)
        self.raxis.SetTickLength(0.09)
        self.raxisr.SetTickLength(0.09)

        self.rtitle = 'data / MC'

        self.rlimits = (0., 2.)

        self.rerr = 'norm'

        self._makePads()

        self._modified()

    def _makePads(self):
        self.canvas.Divide(2)
        
        self.plotPad = self.canvas.cd(1)
        self.plotPad.SetPad(0., 0., 1., 1.)
        self.plotPad.SetMargin(SimpleCanvas.XMIN, 1. - SimpleCanvas.XMAX, RatioCanvas.PLOT_YMIN, 1. - SimpleCanvas.YMAX) # lrbt
        self.plotPad.SetLogx(self._logx)
        self.plotPad.SetLogy(self._logy)
        
        self.ratioPad = self.canvas.cd(2)
        self.ratioPad.SetPad(SimpleCanvas.XMIN, RatioCanvas.RATIO_YMIN, SimpleCanvas.XMAX, RatioCanvas.RATIO_YMAX)
        self.ratioPad.SetMargin(0., 0., 0., 0.)

    def cd(self):
        self.plotPad.cd()

    def Clear(self, full = False):
        SimpleCanvas.Clear(self, full = full)
        self._makePads()
        if full:
            self.legend.Clear()

        for axis in [self.xaxis, self.xaxism]:
            axis.SetWmin(0.)
            axis.SetWmax(1.)
        for axis in [self.yaxis, self.yaxisr]:
            axis.SetWmin(0.1)
            axis.SetWmax(1.)
        for axis in [self.raxis, self.raxisr]:
            axis.SetWmin(self.rlimits[0])
            axis.SetWmax(self.rlimits[1])

    def Update(self, hList = None, rList = None, logx = None, logy = None, drawLegend = True):
        if not self._needUpdate:
            if logx is not None:
                self._updateAxis('x', logx)
            if logy is not None:
                self._updateAxis('y', logy)

            return

        if logx is None:
            logx = self._logx

        if logy is None:
            logy = self._logy

        gPad = ROOT.gPad
        gDirectory = ROOT.gDirectory

        self.canvas.cd()
        self.canvas.Update()

        # map the original histograms to RooHists
        rooHists = {}

        if hList is None:
            hList = range(len(self._histograms))

        base = self._updateMainPad(self.plotPad, hList, logx, logy, rooHists, drawLegend = drawLegend)

        if base:
            try:
                base.SetTickLength(0., 'X')
                base.SetTickLength(0., 'Y')
            except AttributeError:
                # either a THStack or TGraph or something else
                try:
                    base.GetHistogram().SetTickLength(0., 'X')
                    base.GetHistogram().SetTickLength(0., 'Y')
                except AttributeError:
                    # OK I give up
                    pass
            base.GetXaxis().SetNdivisions(self.xaxis.GetNdiv())
            base.GetXaxis().SetTitle('')
            base.GetXaxis().SetLabelSize(0.)
            base.GetXaxis().SetTickSize(0.)
            base.GetYaxis().SetNdivisions(self.yaxis.GetNdiv())
            base.GetYaxis().SetTitle('')
            base.GetYaxis().SetLabelSize(0.)
    
            # will be overridden by self.ytitle
            self.yaxis.SetTitle(base.GetYaxis().GetTitle())

        # now ratio plots
        self.ratioPad.cd()
        self.ratioPad.SetLogx(logx)

        # list of ratio histograms
        if rList is None:
            rList = list(hList)

        if len(rList) > 0:
            # set up ratio base
            self._hStore.cd()
            rbase = self._histograms[rList[0]].Clone('rbase')
            rbase.SetMaximum()
            rbase.SetMinimum()
            self._temporaries.append(rbase)

            normalizer = Normalizer(rbase, self.rerr)

            rframe = ROOT.TH1F('rframe', '', 1, rbase.GetXaxis().GetXmin(), rbase.GetXaxis().GetXmax())
            rframe.SetMinimum(self.rlimits[0])
            rframe.SetMaximum(self.rlimits[1])
            rframe.GetYaxis().SetNdivisions(self.raxis.GetNdiv())
            self._temporaries.append(rframe)

            rframe.Draw()
            
            # draw the base line
            if not ('P' in rbase.drawOpt or rbase.GetLineWidth() == 0):
                rline = ROOT.TLine(rframe.GetXaxis().GetXmin(), 1., rframe.GetXaxis().GetXmax(), 1.)
                rline.SetLineColor(rbase.GetLineColor())
                rline.SetLineStyle(rbase.GetLineStyle())
                rline.SetLineWidth(rbase.GetLineWidth())
                rline.Draw()
                self._temporaries.append(rline)
   
            # use rnorms to normalize others
            for ir in rList[1:]:
                hist = self._histograms[ir]
   
                self._hStore.cd()

                try:
                    obj = rooHists[hist]
                except KeyError:
                    obj = hist

                ratio = normalizer.normalize(obj, 'ratio_' + hist.GetName())
                ratio.SetTitle('')

                self._temporaries.append(ratio)

                if ratio.InheritsFrom(ROOT.TGraph.Class()):
                    ratio.Draw(hist.drawOpt + 'Z')
                else:
                    ratio.Draw(hist.drawOpt + ' SAME')

                if 'P' in hist.drawOpt or ratio.InheritsFrom(ROOT.TGraph.Class()):
                    # draw arrows and error bars for over and undershoots
                    rmed = (self.rlimits[0] + self.rlimits[1]) * 0.5
                    extrema = []

                    if ratio.InheritsFrom(ROOT.TH1.Class()):
                        for iX in range(1, ratio.GetNbinsX() + 1):
                            y = ratio.GetBinContent(iX)
                            if y < self.rlimits[0] or y > self.rlimits[1]:
                                ey = ratio.GetBinError(iX)
                                extrema.append((ratio.GetXaxis().GetBinCenter(iX), y, ey, ey))

                    else:
                        for iP in range(ratio.GetN()):
                            y = ratio.GetY()[iP]
                            if y < self.rlimits[0] or y > self.rlimits[1]:
                                if ratio.InheritsFrom(ROOT.TGraphAsymmErrors.Class()):
                                    eyhigh = ratio.GetErrorYhigh(iP)
                                    eylow = ratio.GetErrorYlow(iP)
                                elif ratio.InheritsFrom(ROOT.TGraphErrors.Class()):
                                    eyhigh = ratio.GetErrorY(iP)
                                    eylow = eyhigh
                                else:
                                    eyhigh = 0.
                                    eylow = 0.

                                extrema.append((ratio.GetX()[iP], y, eyhigh, eylow))

                    for x, y, eyhigh, eylow in extrema:
                        if (y < self.rlimits[0] and y + eyhigh < rmed - 0.8 * (rmed - self.rlimits[0])) or (y > self.rlimits[1] and y - eylow > rmed + 0.8 * (self.rlimits[1] - rmed)):
                            if y < self.rlimits[0]:
                                end = 1. - (1. - self.rlimits[0]) * 0.95
                            else:
                                end = 1. + (self.rlimits[1] - 1.) * 0.95

                            arrow = ROOT.TArrow(x, 1., x, end, ratio.GetMarkerSize() * 0.015, '|>')
                            arrow.SetFillStyle(1001)
                            arrow.SetFillColor(ratio.GetMarkerColor())
                            arrow.SetLineColor(ratio.GetLineColor())
                            arrow.SetLineStyle(ROOT.kDashed)
                            arrow.SetLineWidth(ratio.GetLineWidth())
                            self._temporaries.append(arrow)
                            arrow.Draw()

                        elif y < self.rlimits[0] or y > self.rlimits[1]:
                            if y < self.rlimits[0]:
                                low = self.rlimits[0]
                                high = min(y + eyhigh, self.rlimits[1])
                            else:
                                low = max(y - eylow, self.rlimits[0])
                                high = self.rlimits[1]

                            bar = ROOT.TLine(x, low, x, high)
                            Legend.copyStyle(ratio, bar)
                            self._temporaries.append(bar)
                            bar.Draw()

            rframe.SetTitle('')
            rframe.SetTickLength(0., 'X')
            rframe.SetTickLength(0., 'Y')
            rframe.GetXaxis().SetTitle('')
            rframe.GetXaxis().SetLabelSize(0.)
            rframe.GetXaxis().SetNdivisions(self.xaxis.GetNdiv())
            rframe.GetYaxis().SetTitle('')
            rframe.GetYaxis().SetLabelSize(0.)
            rframe.GetYaxis().SetNdivisions(self.raxis.GetNdiv())
            rframe.GetYaxis().SetRangeUser(*self.rlimits)

            # will be overridden by self.xtitle
            self.xaxis.SetTitle(rbase.GetXaxis().GetTitle())

            self.canvas.Update()

            self.ratioPad.Update()

        self.canvas.cd()
        self.canvas.Update()
        self.plotPad.Update()

        self._updateAxis('x', logx)
        self._updateAxis('y', logy)
        self._updateAxis('r')

        if self.ytitle:
            self.yaxis.SetTitle(self.ytitle)

        if self.xtitle:
            self.xaxis.SetTitle(self.xtitle)

        self.raxis.SetTitle(self.rtitle)

        self.drawText()

        gDirectory.cd()
        gPad.cd()

        self.canvas.Update()

        self._needUpdate = False

    def _updateAxis(self, ax, log = False):
        if ax == 'x':
            self.plotPad.SetLogx(log)
            self.ratioPad.SetLogx(log)
        elif ax == 'y':
            self.plotPad.SetLogy(log)

        self.canvas.Update()

        if ax == 'x':
            axes = [self.xaxis, self.xaxism]
            umin = self.plotPad.GetUxmin()
            umax = self.plotPad.GetUxmax()
        elif ax == 'y':
            axes = [self.yaxis, self.yaxisr]
            umin = self.plotPad.GetUymin()
            umax = self.plotPad.GetUymax()
        elif ax == 'r':
            axes = [self.raxis, self.raxisr]
            umin = self.rlimits[0]
            umax = self.rlimits[1]

        for axis in axes:
            opt = axis.GetOption()
            if log:
                if 'G' not in opt:
                    axis.SetOption(opt + 'G')
                axis.SetWmin(math.exp(2.302585092994 * umin))
                axis.SetWmax(math.exp(2.302585092994 * umax))
            else:
                axis.SetOption(opt.replace('G', ''))
                axis.SetWmin(umin)
                axis.SetWmax(umax)
    
            axis.Draw()
        self.canvas.Update()


class DataMCCanvas(RatioCanvas):

    def __init__(self, name = 'cDataMC', title = 'Data / MC', lumi = -1., sim = False, cms = False, prelim = False):
        RatioCanvas.__init__(self, name = name, title = title, lumi = lumi, sim = sim, cms = cms, prelim = prelim)

        self._obs = -1
        self._bkgs = []
        self._sigs = []

        self._stack = ROOT.THStack('stack', '')
        self.addHistogram(self._stack, 'HIST', clone = False)

        self.borderColor = ROOT.kBlack

    def Clear(self, full = False):
        RatioCanvas.Clear(self, full = full)

        self._obs = -1
        self._bkgs = []
        self._sigs = []

        self._stack = ROOT.THStack('stack', '')
        self.addHistogram(self._stack, 'HIST', clone = False)

    def addObs(self, obs, title = 'Observed', color = ROOT.kBlack, drawOpt = 'EP', asymErr = False):
        if self._obs == -1:
            self._hStore.cd()
            self._obs = self.addHistogram(obs, drawOpt, asymErr = asymErr)

            self.legend.add('obs', title = title, opt = 'LP', color = color, mstyle = 8, msize = 0.8)
            self.legend.apply('obs', self._histograms[self._obs].obj)

        else:
            self.addHistogram(obs, idx = self._obs)

        self._modified()

        return self._obs

    def addStacked(self, bkg, title = '', color = 0, style = 1001, idx = -1, drawOpt = 'HIST'):
        idx = self.addHistogram(bkg, drawOpt, idx = idx)

        if idx not in self._bkgs:
            # a new background
            self._bkgs.append(idx)

            bkgHist = self._histograms[idx].obj

            fillcolor = ROOT.gROOT.GetColor(color)
            if fillcolor and color != 0:
                """
                r = fillcolor.GetRed() * 0.8
                g = fillcolor.GetGreen() * 0.8
                b = fillcolor.GetBlue() * 0.8
                color = ROOT.TColor.GetColor(r, g, b)

                fillcolor = ROOT.gROOT.GetColor(color)
                """
                r = fillcolor.GetRed() * 0.8
                g = fillcolor.GetGreen() * 0.8
                b = fillcolor.GetBlue() * 0.8
                lcolor = ROOT.TColor.GetColor(r, g, b)
            else:
                lcolor = color

            self.legend.add('bkg%d' % idx, title = title, opt = 'LF', fcolor = color, mcolor = lcolor, lcolor = lcolor, fstyle = style, lwidth = 2, lstyle = ROOT.kSolid)
            self.legend.apply('bkg%d' % idx, bkgHist)

            self._stack.Add(bkgHist)

        self._modified()

        return idx

    def addSignal(self, sig, title = '', color = 0, idx = -1, drawOpt = 'HIST'):
        idx = self.addHistogram(sig, drawOpt = drawOpt, idx = idx)

        if idx not in self._sigs:
            # a new signal
            self._sigs.append(idx)

            self.legend.add('sig%d' % idx, title = title, opt = 'L', color = color, lwidth = 4, lstyle = ROOT.kSolid, fstyle = 0)
            self.legend.apply('sig%d' % idx, self._histograms[idx].obj)

        self._modified()

        return idx

    def Update(self, logx = None, logy = None, drawLegend = True):
        if not self._needUpdate:
            if logx is not None:
                self._updateAxis('x', logx)
            if logy is not None:
                self._updateAxis('y', logy)
            return

        gDirectory = ROOT.gDirectory

        if len(self._bkgs) != 0:
            first = self._histograms[self._bkgs[0]]

            self._hStore.cd()
            borderHist = first.Clone('border')
            uncertHist = first.Clone('uncert')

            for iBkg in self._bkgs[1:]:
                bkg = self._histograms[iBkg]
                borderHist.Add(bkg.obj)
                uncertHist.Add(bkg.obj)
        
            borderHist.SetLineWidth(2)
            borderHist.SetLineColor(self.borderColor)
            borderHist.SetMarkerSize(0)
            borderHist.SetMarkerStyle(0)
            borderHist.SetMarkerColor(self.borderColor)
            borderHist.SetFillStyle(0)

            uncertHist.SetFillStyle(3003)
            uncertHist.SetFillColor(ROOT.kGray + 2)
            uncertHist.SetMarkerSize(0)
            uncertHist.SetMarkerStyle(0)
            uncertHist.SetMarkerColor(ROOT.kGray + 2)
            uncertHist.SetLineWidth(0)

            self.addHistogram(borderHist, drawOpt = 'HIST', clone = False)
            iBorder = len(self._histograms) - 1
            self.addHistogram(uncertHist, drawOpt = 'E2', clone = False)
            iUncert = len(self._histograms) - 1

            # addHistogram calls _modified which clears temporaries - this line has to come after above
            self._temporaries += [borderHist, uncertHist]

            hList = [0, iBorder, iUncert] + self._sigs
            rList = [iBorder, iUncert]
            if self._obs != -1:
                hList.append(self._obs)                
                rList.append(self._obs)

            legendOrder = []
            if self._obs != -1:
                legendOrder.append('obs')
            legendOrder += ['bkg%d' % idx for idx in reversed(self._bkgs)] + ['sig%d' % idx for idx in self._sigs]

            self.legend.construct(legendOrder)

            RatioCanvas.Update(self, hList = hList, rList = rList, logx = logx, logy = logy, drawLegend = drawLegend)

            self._histograms.pop()
            self._histograms.pop()

        gDirectory.cd()

    def obsHistogram(self):
        if self._obs != -1:
            return self._histograms[self._obs]
        else:
            return None
