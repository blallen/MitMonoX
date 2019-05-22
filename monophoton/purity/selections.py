import os
import sys
import array
import collections
import time
import ROOT

from pprint import pprint

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)

if basedir not in sys.path:
    sys.path.append(basedir)

import config
import utils
from datasets import allsamples
from plotstyle import WEBDIR

### Configuration parameters ###

# Version = 'DarkPhoton'
Version = 'CustomIDSF' # 'GJetsTune'

bases = ['medium'] # ['loose', 'medium', 'tight', 'highpt'] 
mods = ['',  '-pixel', '-pixel-monoph'] #  '-pixel-chargedpf'] # , 

# Skims for Purity Calculation
sphData = ['sph-16b-m', 'sph-16c-m', 'sph-16d-m', 'sph-16e-m', 'sph-16f-m', 'sph-16g-m', 'sph-16h-m']
gjetsMc = ['gj04-100', 'gj04-200','gj04-400','gj04-600']
qcdMc = ['qcd-200', 'qcd-300', 'qcd-500', 'qcd-700', 'qcd-1000', 'qcd-1000', 'qcd-1500', 'qcd-2000']

sphLumi = sum(allsamples[s].lumi for s in sphData)

lowpt = False

### Various load-time operations ###

versionDir =  config.histDir + '/purity/' + Version
if not os.path.isdir(versionDir):
    os.makedirs(versionDir)

ROOT.gSystem.Load(config.libobjs)
e = ROOT.panda.Event

ROOT.gROOT.ProcessLine("double cutvalue;")

ROOT.gROOT.LoadMacro(basedir + '/../common/MultiDraw.cc+')

### Statics ###

Tunes = ['Spring15', 'Spring16', 'GJetsCWIso', 'ZGCWIso']
Locations = ['barrel', 'endcap']
PhotonIds = ['none', 'loose', 'medium', 'tight', 'highpt']

Samples = {
    'sphData': sphData,
    'gjetsMc': gjetsMc,
    'qcdMc': qcdMc,
    'allMc': gjetsMc + qcdMc
}

Cuts = {
    'pixelVeto': 'photons.pixelVeto[0]',
    'chargedPFVeto': 'photons.chargedPFVeto[0]',
    'mip': 'photons.mipEnergy[0] < 4.9',
    'time': 'std::abs(photons.time[0]) < 3.',
    'sieieNonzero': 'photons.sieie[0] > 0.001',
    'sipipNonzero': 'photons.sipip[0] > 0.001',
    'noisyRegion': '!(photons.eta_[0] > 0. && photons.eta_[0] < 0.15 && photons.phi_[0] > 0.527580 && photons.phi_[0] < 0.541795)'
}
Cuts['monophId'] = ' && '.join([
    Cuts['mip'],
    Cuts['time'],
    Cuts['sieieNonzero'],
    Cuts['sipipNonzero'],
    Cuts['noisyRegion']
])

photonPtVar = 'photons.scRawPt[0]'

if lowpt:
    photonPtBinning = [80., 90., 100., 120., 160., 200.]
else:
    photonPtBinning = [175,200,250,300,350,400]

PhotonPtSels = {
    'PhotonPtInclusive': '{pt} > %d'.format(pt = photonPtVar) % photonPtBinning[0],
    'PhotonPt%dtoInf' % photonPtBinning[-1]: '{pt} > %d'.format(pt = photonPtVar) % photonPtBinning[-1]
}
for low, high in zip(photonPtBinning, photonPtBinning[1:]):
    PhotonPtSels['PhotonPt%dto%d' % (low, high)] = '({pt} > %d && {pt} < %d)'.format(pt = photonPtVar) % (low, high)

pprint(PhotonPtSels)

metBinning = [0, 60, 120]
MetSels = {
    'MetInclusive': 't1Met.pt >= %d' % metBinning[0],
    'Met%dtoInf' % metBinning[-1]: 't1Met.pt >= %d' % metBinning[-1]
} 
for low, high in zip(metBinning, metBinning[1:]):
    MetSels['Met%dto%d' % (low, high)] = 't1Met.pt >= %d && t1Met.pt < %d' % (low, high)

MetSels['Met0to30'] = 't1Met.pt >= 0. && t1Met.pt < 30.'

print 'bloop'

### Functions ###

# cut values for the ID tune
def getCuts(tune):
    variables = ['hovere', 'sieie', 'chiso', 'nhiso', 'phiso']

    cuts = dict((v, {}) for v in variables)

    tname = 'panda::XPhoton::k' + tune
    
    for iLoc, loc in enumerate(Locations):
        for cutdict in cuts.values():
            cutdict[loc] = {}

        for iId, pid in enumerate(PhotonIds[1:]):
            ROOT.gROOT.ProcessLine("cutvalue = panda::XPhoton::hOverECuts[%s][%d][%d];" % (tname, iLoc, iId))
            cuts['hovere'][loc][pid] = ROOT.cutvalue
            ROOT.gROOT.ProcessLine("cutvalue = panda::XPhoton::sieieCuts[%s][%d][%d];" % (tname, iLoc, iId))
            cuts['sieie'][loc][pid] = ROOT.cutvalue
            ROOT.gROOT.ProcessLine("cutvalue = panda::XPhoton::chIsoCuts[%s][%d][%d];" % (tname, iLoc, iId))
            cuts['chiso'][loc][pid] = ROOT.cutvalue
            ROOT.gROOT.ProcessLine("cutvalue = panda::XPhoton::nhIsoCuts[%s][%d][%d];" % (tname, iLoc, iId))
            cuts['nhiso'][loc][pid] = ROOT.cutvalue
            ROOT.gROOT.ProcessLine("cutvalue = panda::XPhoton::phIsoCuts[%s][%d][%d];" % (tname, iLoc, iId))
            cuts['phiso'][loc][pid] = ROOT.cutvalue

    return cuts

# selection expressions
def getSelections(tune, location, pid):
    itune = Tunes.index(tune)

    selections = {}
    cuts = getCuts(tune)

    if lowpt:
        selections['trigger'] = 'photons.triggerMatch[0][13]'
    else:
        selections['trigger'] = '1'

    selections['fiducial'] = 'photons.isEB' if location == 'barrel' else '!photons.isEB'
    selections['hovere'] = 'photons.hOverE[0] < %f' % cuts['hovere'][location][pid]
    selections['sieie'] = 'photons.sieie[0] < %f' % cuts['sieie'][location][pid]
    selections['chiso'] = 'photons.chIsoX[0][%d] < %f' % (itune, cuts['chiso'][location][pid])
    selections['chisomax'] = 'photons.chIsoMaxX[0][%d] < %f' % (itune, cuts['chiso'][location][pid])
    selections['nhiso'] = 'photons.nhIsoX[0][%d] < %f' % (itune, cuts['nhiso'][location][pid])
    selections['phiso'] = 'photons.phIsoX[0][%d] < %f' % (itune, cuts['phiso'][location][pid])

    return selections

# Variables and associated properties
Variable = collections.namedtuple('Variable', ['name', 'expression', 'cuts', 'title', 'binning'])

def getVariable(vname, tune, location):
    cuts = getCuts(tune)[vname]

    if vname == 'sieie':
        if location == 'barrel':
            binning = (44, 0.004, 0.015)
        else:
            binning = (48, 0.016, 0.040)

        return Variable(
            'sieie',
            'photons.sieie[0]',
            cuts[location],
            '#sigma_{i#etai#eta}',
            binning
        )
    elif vname == 'chiso':
        itune = Tunes.index(tune)
        if location == 'barrel':
            binning = [0., cuts["barrel"]["medium"]] + [x * 0.1 for x in range(20, 111, 5)]
        else:
            binning = [0., cuts["endcap"]["medium"]] + [x * 0.1 for x in range(20, 111, 5)]

        return Variable(
            'chiso',
            'TMath::Max(0., photons.chIsoX[0][%d])' % itune,
            cuts[location],
            'Ch Iso (GeV)',
            binning
        )
               

# Class for making templates
class HistExtractor(object):
    def __init__(self, name, snames, variable):
        self.name = name
        self.plotter = ROOT.MultiDraw()
        for sname in snames:
            if lowpt:
                self.plotter.addInputPath(utils.getSkimPath(sname, 'ph75'))
            else:
                self.plotter.addInputPath(utils.getSkimPath(sname, 'emjet'))

        self.variable = variable

        self.categories = [] # [(name, title, sel)]

    def extract(self, binning, outFile = None, mcsf = False):
        print 'Extracting ' + self.name + ' distributions'

        if type(binning) is tuple:
            template = ROOT.TH1D('template', '', *binning)
        else:
            template = ROOT.TH1D('template', '', len(binning) - 1, array.array('d', binning))

        template.Sumw2()

        if outFile is not None:
            outFile.cd()

        histograms = []
        for ic, (name, title, sel) in enumerate(self.categories):
            if mcsf and self.variable.name == 'sieie':
                name += '_raw'

            hist = template.Clone(name)
            hist.SetTitle(title)
            histograms.append(hist)

            print 'addPlot', self.variable.name, sel

            self.plotter.addPlot(hist, self.variable.expression, sel, True)

        self.plotter.fillPlots()

        if mcsf and self.variable.name == 'sieie':
            print 'Applying data/MC scale factor to the templates'

            source = ROOT.TFile(basedir + '/data/sieie_ratio.root')
            line = source.Get('fit')

            if outFile is not None:
                outFile.cd()

            corrected = []
            for hist in histograms:
                hcorr = hist.Clone(hist.GetName().replace('_raw', ''))
                corrected.append(hcorr)
                for iX in range(1, hist.GetNbinsX() + 1):
                    hcorr.SetBinContent(iX, hist.GetBinContent(iX) * line.Eval(hist.GetXaxis().GetBinCenter(iX)))

            source.Close()

            histograms.extend(corrected)

        if outFile is not None:
            outFile.cd()
            outFile.Write()

        return histograms


def StatUncert(nReal, nFake):
    # Calculate purity and print results
    print "Number of Real photons passing selection:", nReal
    print "Number of Fake photons passing selection:", nFake
    nTotal = nReal + nFake;
    purity = float(nReal) / float(nTotal)
    print "Purity of Photons is:", purity
    
    upper = ROOT.TEfficiency.ClopperPearson(int(nTotal),int(nReal),0.6827,True)
    lower = ROOT.TEfficiency.ClopperPearson(int(nTotal),int(nReal),0.6827,False)

    upSig = upper - purity;
    downSig = purity - lower;

    return float(upSig + downSig) / 2.0;

##########################################
######### Legacy Iterative Code ##########
##########################################

def HistToTemplate(_hist,_var,_skim,_selName,_plotDir):
    # remove negative weights
    for bin in range(_hist.GetNbinsX()+1):
        binContent = _hist.GetBinContent(bin)
        if ( binContent < 0.):
            _hist.SetBinContent(bin, 0.)
            _hist.SetBinError(bin, 0.)
        binErrorLow = _hist.GetBinErrorLow(bin)
        if ( (binContent - binErrorLow) < 0.):
            _hist.SetBinError(bin, binContent)


    print _selName
    tempname = 'template_'+_skim+'_'+_selName
    print _var
    temp = ROOT.RooDataHist(tempname, tempname, ROOT.RooArgList(_var), _hist)
    
    canvas = ROOT.TCanvas()
    frame = _var.frame()
    temp.plotOn(frame)
        
    print _skim
    frame.SetTitle(_skim)
        
    frame.Draw()
        
    outName = os.path.join(_plotDir,tempname)
    canvas.SaveAs(outName+'.pdf')
    canvas.SaveAs(outName+'.png')
    canvas.SaveAs(outName+'.C')
    
    return temp

# Fitting function
def FitTemplates(_name,_title,_var,_cut,_datahist,_sigtemp,_bkgtemp):
    nEvents = _datahist.sumEntries()
    sigpdf = ROOT.RooHistPdf('sig', 'sig', ROOT.RooArgSet(_var), _sigtemp) #, 2)
    bkgpdf = ROOT.RooHistPdf('bkg', 'bkg', ROOT.RooArgSet(_var), _bkgtemp) #, 2)
    nsig = ROOT.RooRealVar('nsig', 'nsig', nEvents/2, nEvents*0.01, nEvents*1.5)
    nbkg = ROOT.RooRealVar('nbkg', 'nbkg', nEvents/2, 0., nEvents*1.5)
    model = ROOT.RooAddPdf("model", "model", ROOT.RooArgList(sigpdf, bkgpdf), ROOT.RooArgList(nsig, nbkg))
    model.fitTo(_datahist) # , Extended(True), Minimizer("Minuit2", "migrad"))
    
    canvas = ROOT.TCanvas()

    frame = _var.frame()
    frame.SetTitle(_title)
    # frame.SetMinimum(0.001)
    # frame.SetMaximum(10000)

    _datahist.plotOn(frame, ROOT.RooFit.Name("data"))
    model.plotOn(frame, ROOT.RooFit.Name("Fit"))
    model.plotOn(frame, ROOT.RooFit.Components('bkg'),ROOT.RooFit.Name("fake"),ROOT.RooFit.LineStyle(ROOT.kDashed),ROOT.RooFit.LineColor(ROOT.kGreen))
    model.plotOn(frame, ROOT.RooFit.Components('sig'),ROOT.RooFit.Name("real"),ROOT.RooFit.LineStyle(ROOT.kDashed),ROOT.RooFit.LineColor(ROOT.kRed))

    
    frame.Draw("goff")
    
    _var.setRange("selection",0.0,_cut)
    
    fReal = float(sigpdf.createIntegral(ROOT.RooArgSet(_var), "selection").getVal()) / float(sigpdf.createIntegral(ROOT.RooArgSet(_var)).getVal())
    fFake = float(bkgpdf.createIntegral(ROOT.RooArgSet(_var), "selection").getVal()) / float(bkgpdf.createIntegral(ROOT.RooArgSet(_var)).getVal())
    nReal = fReal * nsig.getVal()
    nFake = fFake * nbkg.getVal()

    # Calculate purity and print results
    print "Number of Real photons passing selection:", nReal
    print "Number of Fake photons passing selection:", nFake
    nTotal = nReal + nFake;
    purity = float(nReal) / float(nTotal)
    print "Purity of Photons is:", purity
    
    upper = ROOT.TEfficiency.ClopperPearson(int(nTotal),int(nReal),0.6827,True)
    lower = ROOT.TEfficiency.ClopperPearson(int(nTotal),int(nReal),0.6827,False)

    upSig = upper - purity;
    downSig = purity - lower;
    aveSig = float(upSig + downSig) / 2.0;

    text = ROOT.TLatex()
    text.DrawLatexNDC(0.525,0.8,"Purity: "+str(round(purity,3))+'#pm'+str(round(aveSig,3))) 

    leg = ROOT.TLegend(0.6,0.6,0.85,0.75 );
    leg.SetFillColor(ROOT.kWhite);
    leg.SetTextSize(0.03);
    # leg.SetHeader("templates LOWER<p_{T}<UPPER");
    leg.AddEntry(frame.findObject("data"), "data", "P");
    leg.AddEntry(frame.findObject("Fit"), "real+fake fit to data", "L");
    leg.AddEntry(frame.findObject("real"), "real", "L");
    leg.AddEntry(frame.findObject("fake"), "fake", "L");
    leg.Draw();

    canvas.SaveAs(_name+'.pdf')
    canvas.SaveAs(_name+'.png')
    canvas.SaveAs(_name+'.C')
    canvas.SaveAs(_name+'.root')

    canvas.SetLogy()
    canvas.SaveAs(_name+'_Logy.pdf')
    canvas.SaveAs(_name+'_Logy.png')
    canvas.SaveAs(_name+'_Logy.C')

    return (purity, aveSig, nReal, nFake)

def SignalSubtraction(_skims,_initialHists,_initialTemplates,_isoRatio,_varName,_var,_cut,_inputKey,_plotDir):
    ''' initialHists = [ fit template, signal template, subtraction template, background template ]'''
    nIter = 0
    purities = [ (1,1,1,1) ]
    # sigContams = [ (1,1) ]
    hists = list(_initialHists)
    templates = list(_initialTemplates)

    while(True):
        print "Starting on iteration:", nIter

        dataTitle = "Photon Purity in SinglePhoton DataSet Iteration "+str(nIter)
        dataName = os.path.join(WEBDIR + '/' + _plotDir,"purity_"+"v"+str(nIter)+"_"+_inputKey )
        
        print _var
        dataPurity = FitTemplates(dataName, dataTitle, _var, _cut, templates[0], templates[1], templates[-1])
       
        """
        sbTotal = templates[3].sumEntries()
        sbTrue = templates[-2].sumEntries()
        trueContam = float(sbTrue) / float(sbTotal)

        sbTotalPass = templates[3].sumEntries(_varName+' < '+str(_cut))
        sbTruePass = templates[-2].sumEntries(_varName+' < '+str(_cut))
        trueContamPass = float(sbTruePass) / float(sbTotalPass)

        print "Signal contamination:", trueContam, trueContamPass
        sigContams.append( (trueContam, trueContamPass) ) 
        """
                
        print "Purity:", dataPurity[0]
        purities.append( dataPurity )
        diff = abs(purities[-1][0] - purities[-2][0] )
        print diff 
        if ( diff < 0.001):
            break
        nIter += 1
        if nIter > 10:
            break
        
        nSigTrue = purities[-1][2]
        nSbTrue = _isoRatio * nSigTrue
            
        print "Scaling sideband shape to", nSbTrue, "photons"
            
        contamHist = hists[2].Clone()
        contamHist.Scale(float(nSbTrue) / float(contamHist.GetSumOfWeights()))
        hists.append(contamHist)

        print _var
        contamTemp = HistToTemplate(contamHist,_var,_skims[2],"v"+str(nIter)+"_"+_inputKey,_plotDir)
        templates.append(contamTemp)
    
        backHist = hists[3].Clone()
        backHist.Add(contamHist, -1)
        hists.append(backHist)

        backTemp = HistToTemplate(backHist,_var,_skims[3],"v"+str(nIter)+"_"+_inputKey,_plotDir)
        templates.append(backTemp)

    """
    for version, (purity, contam)  in enumerate(zip(purities[1:],sigContams[1:])):
        print "Purity for iteration", version, "is:", purity
        print "Signal contamination for iteration", version, "is:", contam
    
    return (purities[-1], sigContams[-1])
    """

    for version, purity  in enumerate(purities[1:]):
        print "Purity for iteration", version, "is:", purity
    return purities[-1]
     

print 'blah'


