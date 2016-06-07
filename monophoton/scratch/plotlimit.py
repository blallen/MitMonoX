import sys
import os
import array
import math
import re
import collections
import ROOT

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
import config

def truncateContour(contour, base):
    x = ROOT.Double()
    y = ROOT.Double()

    iP = contour.GetN() - 1
    while iP >= 0:
        contour.GetPoint(iP, x, y)
        if base.GetBinContent(base.FindBin(x, y)) != 0.:
            break

        iP -= 1
        
    contour.Set(iP + 1)

    iP = 0
    while iP < contour.GetN():
        contour.GetPoint(iP, x, y)
        if base.GetBinContent(base.FindBin(x, y)) != 0.:
            break

        iP += 1

    shift = iP
    for iP in range(contour.GetN() - shift):
        contour.GetPoint(iP + shift, x, y)
        contour.SetPoint(iP, x, y)

    contour.Set(contour.GetN() - shift)

def closeContour(contour, base):
    # currently disabled

    x = ROOT.Double()
    y = ROOT.Double()

    contour.GetPoint(0, x, y)
    xBegin = float(x)
    yBegin = float(y)
    contour.GetPoint(contour.GetN() - 1, x, y)
    xEnd = float(x)
    yEnd = float(y)

    xmin = base.GetXaxis().GetXmin()
    ymin = base.GetYaxis().GetXmin()
    xmax = base.GetXaxis().GetXmax()
    ymax = base.GetYaxis().GetXmax()
    xw = base.GetXaxis().GetBinWidth(1)
    yw = base.GetYaxis().GetBinWidth(1)

    if abs(xBegin - xEnd) < xw and abs(yBegin - yEnd) < yw:
        return

    if xBegin - xmin < xw or yBegin - ymin < yw:
        contour.GetPoint(1, x, y)
        xNext = float(x)
        yNext = float(y)
        xExtr = max(xBegin + (xBegin - xNext) / (yBegin - yNext) * (ymin - yBegin), xmin)
        yExtr = max(yBegin + (yBegin - yNext) / (xBegin - xNext) * (xmin - xBegin), ymin)
        contour.Set(contour.GetN() + 1)
        for iP in range(contour.GetN() - 1, 0, -1):
            contour.GetPoint(iP - 1, x, y)
            contour.SetPoint(iP, x, y)
        x = ROOT.Double(xExtr)
        y = ROOT.Double(yExtr)
        contour.SetPoint(0, x, y)

    if xEnd - xmin < xw or yEnd - ymin < yw:
        contour.GetPoint(contour.GetN() - 2, x, y)
        xNext = float(x)
        yNext = float(y)
        x = ROOT.Double(max(xEnd + (xEnd - xNext) / (yEnd - yNext) * (ymin - yEnd), xmin))
        y = ROOT.Double(max(yEnd + (yEnd - yNext) / (xEnd - xNext) * (xmin - xEnd), ymin))
        contour.Set(contour.GetN() + 1)
        contour.SetPoint(contour.GetN() - 1, x, y)

    if xmax - xBegin < xw or ymax - yBegin < yw:
        contour.GetPoint(1, x, y)
        xNext = float(x)
        yNext = float(y)
        xExtr = min(xBegin + (xBegin - xNext) / (yBegin - yNext) * (ymax - yBegin), xmax)
        yExtr = min(yBegin + (yBegin - yNext) / (xBegin - xNext) * (xmax - xBegin), ymax)
        contour.Set(contour.GetN() + 1)
        for iP in range(contour.GetN() - 1, 0, -1):
            contour.GetPoint(iP - 1, x, y)
            contour.SetPoint(iP, x, y)
        x = ROOT.Double(xExtr)
        y = ROOT.Double(yExtr)
        contour.SetPoint(0, x, y)

    if xmax - xEnd < xw or ymax - yEnd < yw:
        contour.GetPoint(contour.GetN() - 2, x, y)
        xNext = float(x)
        yNext = float(y)
        x = ROOT.Double(max(xEnd + (xEnd - xNext) / (yEnd - yNext) * (ymax - yEnd), xmax))
        y = ROOT.Double(max(yEnd + (yEnd - yNext) / (xEnd - xNext) * (xmax - xEnd), ymax))
        contour.Set(contour.GetN() + 1)
        contour.SetPoint(contour.GetN() - 1, x, y)


model = sys.argv[1]

sourcedir = '/scratch5/yiiyama/studies/monophoton/limits/' + model

limits = {}

for fname in os.listdir(sourcedir):
    matches = re.match('dm[av]fs-([0-9]+)-([0-9]+)', fname)
    if not matches:
        continue

    mmed = float(matches.group(1))
    mdm = float(matches.group(2))

    point = (mmed, mdm)

    source = ROOT.TFile.Open(sourcedir + '/' + fname)
    tree = source.Get('limit')
    if tree.GetEntries() != 6:
        source.Close()
        continue

    tree.SetEstimate(7)
    tree.Draw('limit', '', 'goff')
    limit = tree.GetV1()

    limits[point] = tuple([limit[i] for i in range(6)])

    source.Close()

canvas = ROOT.TCanvas('c1', 'c1', 800, 800)
#canvas.SetLogx()
#canvas.SetLogy()
canvas.SetLogz()

#mmeds = array.array('d', [10. * math.pow(1.1, i) for i in range(51)])
#mdms = array.array('d', [10. * math.pow(1.1, i) for i in range(51)])
mmeds = array.array('d', [100. + 20. * i for i in range(51)])
mdms = array.array('d', [10. * i for i in range(51)])
htemplate = ROOT.TH2D('template', ';M_{med} (GeV);M_{DM} (GeV)', len(mmeds) - 1, mmeds, len(mdms) - 1, mdms)

output = ROOT.TFile.Open('../data/' + model + '.root', 'recreate')

#ROOT.gStyle.SetPalette(1)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetNumberContours(99)
ROOT.TColor.InitializeColors()
stops = array.array('d', [0., 2./3., 1.])
red = array.array('d', [0xff, 0xff, 0x11])
green = array.array('d', [0x33, 0xff, 0x33])
blue = array.array('d', [0x11, 0xff, 0xff])

for a in [red, green, blue]:
    for iP in range(3):
        a[iP] /= 0xff

pstart = ROOT.TColor.CreateGradientColorTable(3, stops, red, green, blue, 255)
colors = array.array('i', [pstart + i for i in range(255)])

ROOT.gStyle.SetPalette(255, colors)

interpolations = {
    'dmvfs': [
        ((600., 300.), (825., 400.), (725., 300.)),
        ((825., 300.), (1000., 400.), (900., 350.)),
        ((400., 200.), (600., 300.), (500., 250.)),
        ((600., 200.), (725., 300.), (650., 250.)),
        ((300., 150.), (400., 200.), (350., 175.)),
        ((300., 100.), (400., 150.), (350., 125.)),
        ((200., 100.), (300., 150.), (250., 125.)),
        ((200., 25.), (300., 50.), (250., 38.)),
        ((400., 150.), (525., 200), (450., 175.)),
        ((300., 100.), (300., 150.), (300., 125.)),
        ((100., 50.), (200., 100.), (150., 75.)),
        ((200., 100.), (300., 150.), (280., 140.)),
        ((200., 50.), (300., 100.), (220., 60.)),
        ((825., 100.), (825., 150.), (825., 125.))
    ],
    'dmafs': [
        ((725., 300.), (925., 400.), (825., 350.)),
        ((825., 300.), (925., 400.), (875., 350.)),
        ((525., 200.), (725., 300.), (625., 250.)),
        ((600., 200.), (725., 300.), (650., 250.)),
        ((400., 150.), (525., 200.), (450., 175.)),
        ((200., 50.), (300., 100.), (230., 65.)),
        ((200., 25.), (300., 100.), (250., 65.)),
        ((10., 150.), (100., 50.), (90., 60.)),
        ((175., 50.), (300., 100.), (200., 60.)),
        ((175., 50.), (300., 125.), (200., 70.)),
        ((175., 50.), (300., 125.), (250., 110.)),
        ((100., 50.), (200., 100.), (120., 60.)),
        ((125., 50.), (200., 100.), (150., 70.)),
        ((325., 100.), (400., 150.), (380., 140.)),
        ((825., 100.), (825., 150.), (825., 125.)),
        ((400., 100.), (400., 150.), (400., 125.)),
        ((300., 125.), (400., 150.), (340., 130.))
    ]
}

histograms = {}
contours = collections.defaultdict(list)

for iL, name in enumerate(['exp2down', 'exp1down', 'exp', 'exp1up', 'exp2up', 'obs']):
    gr = ROOT.TGraph2D(len(limits))
    gr.SetName(name)

    textDump = open(config.webDir + '/limits/' + model + '_' + name + '.txt', 'w')
    textDump.write('Fast Sim Points \n')
    textDump.write('%-6s %5s %5s %6s \n' % ('point', 'mMed', 'mDM', 'limit'))
    for iP, (point, larr) in enumerate(sorted(limits.items())):
        gr.SetPoint(iP, point[0], point[1], larr[iL])
        textDump.write('%-6d %5d %5d %6.2f \n' % (iP, point[0], point[1], larr[iL]))

    output.cd()
    gr.Write(name)


    if model in interpolations:
        iP = gr.GetN()
        gr.Set(iP + len(interpolations[model]))

        for edge1, edge2, point in interpolations[model]:
            # add the point of closest approach to point on the line segment between edge1 and edge2
            z1 = limits[edge1][iL]
            z2 = limits[edge2][iL]

            dx = edge1[0] - edge2[0]
            dy = edge1[1] - edge2[1]
            x = (dx * (point[0] * dx + point[1] * dy) + dy * (-edge1[0] * edge2[1] + edge1[1] * edge2[0])) / (dx * dx + dy * dy)
            y = (dy * (point[0] * dx + point[1] * dy) - dx * (-edge1[0] * edge2[1] + edge1[1] * edge2[0])) / (dx * dx + dy * dy)
            z = (z1 * edge2[0] + z2 * edge1[0]) / (edge1[0] + edge2[0])

            gr.SetPoint(iP, x, y, z)
            iP += 1

    textDump.write('\nInterpolated Points \n')
    textDump.write('%5s %5s %6s \n' % ('mMed', 'mDM', 'limit'))

    hist = htemplate.Clone(name + '_int')
    for iX in range(1, hist.GetNbinsX() + 1):
        for iY in range(1, hist.GetNbinsY() + 1):
            z = gr.Interpolate(hist.GetXaxis().GetBinCenter(iX), hist.GetYaxis().GetBinCenter(iY))
            hist.SetBinContent(iX, iY, z)

    for iX in range(1, hist.GetNbinsX() + 1):
        for iY in range(1, hist.GetNbinsY() + 1):
            if hist.GetBinContent(iX, iY) == 0.:
                neighbors = [hist.GetBinContent(iX + 1, iY), hist.GetBinContent(iX - 1, iY), hist.GetBinContent(iX, iY + 1), hist.GetBinContent(iX, iY - 1)]
                nonzero = [z for z in neighbors if z != 0.]
                mean = sum(nonzero) / len(nonzero)

                hist.SetBinContent(iX, iY, mean)
                textDump.write('%5d %5d %6.2f \n' % (hist.GetXaxis().GetBinCenter(iX), hist.GetYaxis().GetBinCenter(iY), mean))

        textDump.close()

    output.cd()
    hist.Write()

    hist.SetMinimum(0.01)
    hist.SetMaximum(10.)
    hist.Draw('colz')

    canvas.Print(config.webDir + '/limits/' + model + '_' + name + '.pdf')
    canvas.Print(config.webDir + '/limits/' + model + '_' + name + '.png')

    histograms[name] = hist

    if name == 'exp':
        pgr = ROOT.TGraph(len(limits))
        for iP, point in enumerate(limits.keys()):
            pgr.SetPoint(iP, point[0], point[1])

        pgr.SetMarkerStyle(4)
        pgr.SetMarkerColor(ROOT.kBlack)

        pgr.Draw('P')

        if model in interpolations:
            interp = interpolations[model]
            agr = ROOT.TGraph(len(interp))
            segments = []

            for iP in range(len(interp)):
                agr.SetPoint(iP, gr.GetX()[iP + len(limits)], gr.GetY()[iP + len(limits)])
                line = ROOT.TLine(*(interp[iP][0] + interp[iP][1]))
                line.SetLineStyle(ROOT.kDashed)
                line.SetLineColor(ROOT.kBlack)
                line.SetLineWidth(1)
                segments.append(line)

        agr.SetMarkerStyle(8)
        agr.SetMarkerColor(ROOT.kBlack)

        agr.Draw('P')
        for line in segments:
            line.Draw()

        canvas.Print(config.webDir + '/limits/' + model + '_' + name + '_points.pdf')
        canvas.Print(config.webDir + '/limits/' + model + '_' + name + '_points.png')

    clevel = array.array('d', [1.])
    contsource = hist.Clone('contsource_' + name)
    contsource.SetContour(1, clevel)
    contsource.Draw('CONT LIST')
    canvas.Update()
    contList = ROOT.gROOT.GetListOfSpecials().FindObject('contours').At(0)
    for iC, contour in enumerate(contList):
        if contour.GetY()[0] > contour.GetX()[0] * 0.5 + 100.:
            continue

        cont = contour.Clone()
        output.cd()
        cont.SetName(name + '_cont%d' % iC)
        cont.Write(name + '_cont%d' % iC)
        contours[name].append(cont)
    
    contsource.Delete()

    if name == 'obs':
        for shift, cl in [('obs1up', 0.8), ('obs1down', 1.2)]:
            clevel = array.array('d', [cl])
            contsource = hist.Clone('contsource_' + shift)
            contsource.SetContour(1, clevel)
            contsource.Draw('CONT LIST')
            canvas.Update()
            contList = ROOT.gROOT.GetListOfSpecials().FindObject('contours').At(0)
            for iT, contour in enumerate(contList):
                if contour.GetY()[0] > contour.GetX()[0] * 0.5 + 100.:
                    continue

                cont = contour.Clone()
                output.cd()
                cont.SetName(shift + '_cont%d' % iC)
                cont.Write(shift + '_cont%d' % iC)
                contours[shift].append(cont)
            
            contsource.Delete()
        

histograms['obs'].Draw('COLZ')
for cont in contours['exp']:
    cont.SetLineColor(ROOT.kBlue)
    cont.SetLineWidth(2)
    cont.Draw('CL')
for cont in contours['exp1up']:
    cont.SetLineColor(ROOT.kBlue)
    cont.SetLineWidth(1)
    cont.SetLineStyle(ROOT.kDashed)
    cont.Draw('CL')
for cont in contours['exp1down']:
    cont.SetLineColor(ROOT.kBlue)
    cont.SetLineWidth(1)
    cont.SetLineStyle(ROOT.kDashed)
    cont.Draw('CL')
for cont in contours['obs']:
    cont.SetLineColor(ROOT.kBlack)
    cont.SetLineWidth(2)
    cont.Draw('CL')
for cont in contours['obs1up']:
    cont.SetLineColor(ROOT.kBlack)
    cont.SetLineWidth(1)
    cont.Draw('CL')
for cont in contours['obs1down']:
    cont.SetLineColor(ROOT.kBlack)
    cont.SetLineWidth(1)
    cont.Draw('CL')

legend = ROOT.TLegend(0.1, 0.8, 0.4, 0.9)
legend.SetBorderSize(0)
#legend.SetFillStyle(0)
legend.AddEntry(contours['exp'][0], 'Expected #pm 1 #sigma_{exp}', 'L')
legend.AddEntry(contours['obs'][0], 'Observed #pm 1 #sigma_{theory}', 'L')
legend.Draw()

canvas.Print(config.webDir + '/limits/' + model + '_exclusion.pdf')
canvas.Print(config.webDir + '/limits/' + model + '_exclusion.png')

output.Close()
