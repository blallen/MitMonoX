import os
import sys
from array import array
from pprint import pprint
import ROOT
ROOT.gROOT.SetBatch(True)

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)

if basedir not in sys.path:
    sys.path.append(basedir)

from datasets import allsamples
import config
import utils
import purity.selections as s

def formatHist(hist, ytitle, lstyle = ROOT.kDashed):
    hist.SetLineWidth(3)
    hist.SetLineStyle(lstyle)
    hist.SetStats(False)

    hist.GetXaxis().SetTitle("CH Iso (GeV)")
    hist.GetYaxis().SetTitle(ytitle)
    
    hist.GetXaxis().SetLabelSize(0.045)
    hist.GetXaxis().SetTitleSize(0.045)
    hist.GetYaxis().SetLabelSize(0.045)
    hist.GetYaxis().SetTitleSize(0.045)

    hist.GetDirectory().cd()
    hist.Write()

def printHist(histograms, drawOpt, name, pdir, logy = False):
    canvas = ROOT.TCanvas()
    leg = ROOT.TLegend(0.725, 0.7, 0.875, 0.85);
    leg.SetFillColor(ROOT.kWhite);
    leg.SetTextSize(0.03);

    dopt = drawOpt
    icolor = 1
    for hist in histograms:
        hist.SetLineColor(icolor)
        icolor += 1
        hist.Draw(dopt)
        if 'same' not in dopt:
            dopt += ' same'

        leg.AddEntry(hist, hist.GetName(), 'L')

    leg.Draw()
    
    if logy:
        canvas.SetLogy()
        canvas.SaveAs(pdir + '/' + name + '_logy.pdf')
        canvas.SaveAs(pdir + '/' + name + '_logy.png')
        # canvas.SaveAs(name+'_Logy.C')

    else:
        canvas.SaveAs(pdir + '/' + name + '.pdf')
        canvas.SaveAs(pdir + '/' + name + '.png')
        # canvas.SaveAs(name+'.C')


def plotiso(loc, pid, pt, met, tune):
    inputKey = tune+'_'+loc+'_'+pid+'_PhotonPt'+pt+'_Met'+met
    
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
    
    var = s.getVariable('chiso', tune, loc)
    
    versDir = s.versionDir
    WEBDIR = os.environ['HOME'] + '/public_html/cmsplots'
    plotDir = os.path.join(WEBDIR, 'purity', s.Version, inputKey, 'chiso')
    histDir = os.path.join(versDir, inputKey)
    if not os.path.exists(plotDir):
        os.makedirs(plotDir)
    if not os.path.exists(histDir):
        os.makedirs(histDir)
   
    pids = pid.split('-')
    pid = pids[0]
    extras = pids[1:]

    selections = s.getSelections(tune, loc, pid)

    itune = s.Tunes.index(tune)

    ### Plot I_{CH} from sph data and gjets MC

    # selection on H/E & INH & IPh
    baseSel = ' && '.join([
        ptSel,
        metSel,
        selections['fiducial'],
        selections['hovere'],
        selections['nhiso'],
        selections['phiso']
    ])
    if 'pixel' in extras:
        baseSel = baseSel + ' && ' + s.Cuts['pixelVeto']
    if 'monoph' in extras:
        baseSel = baseSel + ' && ' + s.Cuts['monophId']
    if 'max' in extras:
        baseSel = baseSel.replace('chIso', 'chIsoMax')
        var = s.Variable('TMath::Max(0., photons.chIsoMaxX[0][%d])' % itune, *var[1:])

    truthSel = '(photons.matchedGenId == -22)'

    # output file
    outName = 'chiso' #  + inputKey
    print 'plotiso writing to', histDir + '/' + outName + '.root'
    outFile = ROOT.TFile(histDir + '/' + outName + '.root', 'RECREATE')

    # don't use var.binning for binning
    binning = [0., var.cuts[pid]] + [0.1 * x for x in range(20, 111, 5)]

    # make the data iso distribution for reference
    extractor = s.HistExtractor('sphData', s.Samples['sphData'], var)
    print 'setBaseSelection(' + baseSel + ')'
    extractor.plotter.setBaseSelection(baseSel)
    extractor.categories.append(('data', 'I_{CH} Distribution from SinglePhoton Data', ''))
    hist = extractor.extract(binning, outFile = outFile)[0]
    hist.Scale(1. / hist.GetSumOfWeights())

    formatHist(hist, 'Events')
    printHist([hist], 'HIST', outName + '_data', plotDir, logy = True)

    extractor = s.HistExtractor('gjetsMc', s.Samples['gjetsMc'], var)
    print 'setBaseSelection(' + baseSel + ' && ' + truthSel + ')'
    extractor.plotter.setBaseSelection(baseSel + ' && ' + truthSel)
    extractor.categories.append(('rawmc', 'I_{CH} Distribution from #gamma+jets MC', ''))
    raw = extractor.extract(binning, outFile = outFile)[0]
    raw.Scale(1. / raw.GetSumOfWeights())

    formatHist(raw, 'Events')

    ### Plot I_{CH} from sph data and dy MC Zee samples

    eSelScratch = ' && '.join([
        'tp.mass > 81 && tp.mass < 101',
        metSel,
        selections['fiducial'],
        selections['hovere'],
        selections['nhiso'],
        selections['phiso'],
        selections['sieie']
    ])

    eSel = 'weight * (' + eSelScratch.replace("photons", "probes") + ')'
    eExpr = var.expression.replace('photons', 'probes')

    print 'Extracting electron MC distributions'

    mcTree = ROOT.TChain('events')
    for sample in allsamples.getmany('dy-50-*'):
        mcTree.Add(utils.getSkimPath(sample.name, 'tpeg'))

    print 'Draw(' + eExpr + ', ' + eSel + ')'
    
    mcHist = raw.Clone("emc")
    mcHist.Reset()
    mcTree.Draw(eExpr + ">>emc", eSel, 'goff')
    mcHist.Scale(1. / mcHist.GetSumOfWeights())

    formatHist(mcHist, 'Events')

    print 'Extracting electron data distributions'
    
    dataTree = ROOT.TChain('events')
    for sample in s.Samples['sphData']:
        dataTree.Add(utils.getSkimPath(sample, 'tpeg'))

    print 'Draw(' + eExpr + ', ' + eSel + ')'

    dataHist = raw.Clone("edata")
    dataHist.Reset()
    dataTree.Draw(eExpr + ">>edata", eSel, 'goff')
    dataHist.Scale(1. / dataHist.GetSumOfWeights())

    formatHist(dataHist, 'Events')

    printHist([mcHist, dataHist], 'HIST', outName + '_electrons', plotDir, logy = True)

    scaled = raw.Clone("scaledmc")

    scaleHist = raw.Clone("escale")
    scaleHist.SetTitle("Data/MC Scale Factors from Electrons")
    scaleHist.Reset()
    for iBin in range(1,scaleHist.GetNbinsX()+1):
        dataValue = dataHist.GetBinContent(iBin)
        dataError = dataHist.GetBinError(iBin)
    
        mcValue = mcHist.GetBinContent(iBin)
        mcError = mcHist.GetBinError(iBin)
    
        if mcValue == 0 or dataValue == 0:
            ratio = 1
            error = 0.05
        else:
            ratio = dataValue / mcValue 
            error = ratio * ( (dataError / dataValue)**2 + (mcError / mcValue)**2 )**(0.5)
    
        scaleHist.SetBinContent(iBin, ratio)
        scaled.SetBinContent(iBin, ratio * scaled.GetBinContent(iBin))
        scaleHist.SetBinError(iBin, error)

    scaled.Scale(1. / scaled.GetSumOfWeights())

    formatHist(scaled, 'Events')
    formatHist(scaleHist, 'Scale Factor', lstyle = ROOT.kSolid)

    printHist([scaleHist], '', outName + '_scale', plotDir, logy = False)
    printHist([raw, scaled], 'HIST', outName + '_photons', plotDir, logy = True)

    outFile.Close()


if __name__ == '__main__':
    import sys

    loc = sys.argv[1]
    pid = sys.argv[2]
    pt = sys.argv[3]
    met = sys.argv[4]
    
    try:
        tune = sys.argv[5]
    except:
        tune = 'Spring16'

    plotiso(loc, pid, pt, met, tune)
