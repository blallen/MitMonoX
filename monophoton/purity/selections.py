import os
import array
import ROOT

Version = 'simpletree5'

ROOT.gSystem.Load('libMitFlatDataFormats.so')
ROOT.gSystem.AddIncludePath('-I' + os.environ['CMSSW_BASE'] + '/src/MitFlat/DataFormats/interface')
TemplateGeneratorPath = os.path.join(os.environ['CMSSW_BASE'],'src/MitMonoX/monophoton/purity','TemplateGenerator.cc+')
ROOT.gROOT.LoadMacro(TemplateGeneratorPath)

Locations = [ 'barrel', 'endcap' ]
PhotonIds = [ 'loose', 'medium', 'tight' ]

hOverECuts = {}
sieieCuts = {}
chIsoCuts = {}
nhIsoCuts = {}
phIsoCuts = {}

ROOT.gROOT.ProcessLine("double cut;")
for loc in Locations:
    hOverECuts[loc] = {}
    sieieCuts[loc] = {}
    chIsoCuts[loc] = {}
    nhIsoCuts[loc] = {}
    phIsoCuts[loc] = {}
    
    for pid in PhotonIds:
        ROOT.gROOT.ProcessLine("cut = simpletree::Photon::hOverECuts["+str(Locations.index(loc))+"]["+str(PhotonIds.index(pid))+"];")
        # print "hOverE", loc, pid, ROOT.cut
        hOverECuts[loc][pid] = ROOT.cut
        ROOT.gROOT.ProcessLine("cut = simpletree::Photon::sieieCuts["+str(Locations.index(loc))+"]["+str(PhotonIds.index(pid))+"];")
        # print "sieie", loc, pid, ROOT.cut
        sieieCuts[loc][pid] = ROOT.cut
        ROOT.gROOT.ProcessLine("cut = simpletree::Photon::chIsoCuts["+str(Locations.index(loc))+"]["+str(PhotonIds.index(pid))+"];")
        # print "chIso", loc, pid, ROOT.cut
        chIsoCuts[loc][pid] = ROOT.cut
        ROOT.gROOT.ProcessLine("cut = simpletree::Photon::nhIsoCuts["+str(Locations.index(loc))+"]["+str(PhotonIds.index(pid))+"];")
        # print "nhIso", loc, pid, ROOT.cut
        nhIsoCuts[loc][pid] = ROOT.cut
        ROOT.gROOT.ProcessLine("cut = simpletree::Photon::phIsoCuts["+str(Locations.index(loc))+"]["+str(PhotonIds.index(pid))+"];")
        # print "phIso", loc, pid, ROOT.cut
        phIsoCuts[loc][pid] = ROOT.cut

from ROOT import *

# nTuple location
ntupledir = '/scratch5/yiiyama/hist/'+Version+'/t2mit/filefi/042/'

ChIsoSbBins = range(20,101,5)

# Variables and associated properties
# variable Enum, sideband Enum, selection Enum, roofit variable ( region : roofit variable, nbins, variable binning), cut dict for purity
Variables = { "sieie"  : (kSigmaIetaIeta,kChIso,kLoose, { "barrel"  : (RooRealVar('sieie', '#sigma_{i#etai#eta}', 0.004, 0.015), 44, [0.004,0.011,0.015] )
                                                          ,"endcap" : (RooRealVar('sieie', '#sigma_{i#etai#eta}', 0.016, 0.040), 48, [0.016,0.030,0.040] ) } 
                          , sieieCuts )
              ,"sieieScaled"  : (kSigmaIetaIetaScaled,kChIso,kLoose, { "barrel"  : (RooRealVar('sieieScaled', '#sigma_{i#etai#eta}^{Scaled}', 0.004, 0.015), 44, [0.004,0.011,0.015] )
                                                                       ,"endcap" : (RooRealVar('sieieScaled', '#sigma_{i#etai#eta}^{Scaled}', 0.016, 0.040), 48, [0.016,0.030,0.040] ) } 
                           , sieieCuts )
              ,"chiso" : (kChargedHadronIsolation,kChIso,kLoose, { "barrel"  : (RooRealVar('chiso', 'Ch Iso (GeV)', 0.0, 10.0), 20, [0.0,1.0,1.5,1.79]+[float(x)/10.0 for x in ChIsoSbBins] )
                                                                   ,"endcap" : (RooRealVar('chiso', 'Ch Iso (GeV)', 0.0, 10.0), 20, [0.0,1.0,1.5,1.79]+[float(x)/10.0 for x in ChIsoSbBins] ) }
                          , chIsoCuts )
              ,"phiso" : (kPhotonIsolation,kSieie,kLoose, { "barrel"  : (RooRealVar('phiso', 'Ph Iso (GeV)', 0., 10.0), 100, [0.0,5.0,10.0] )
                                                            ,"endcap" : (RooRealVar('phiso', 'Ph Iso (GeV)', 0., 10.0), 100, [0.0,5.0,10.0] ) } 
                          , phIsoCuts ) } 

# Samples for skimming
Regions = { "Wgamma" : [ ( 'TempSignalWgPhotons',kPhoton,405.271,ntupledir+'WGToLNuG_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                         ,('TempBkgdSingleMuon',kBackground,-1,ntupledir+'SingleMuon+Run2015C-PromptReco-v1+AOD')
                         ,('TempBkgdWJetsToLNu',kBackground,60290,ntupledir+'WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                         ,('FitSingleMuon',kPhoton,-1,ntupledir+'SingleMuon+Run2015C-PromptReco-v1+AOD')
                         ,('FitWJetsToLNu',kPhoton,60290,ntupledir+'WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM' ) ]
            
            ,"Monophoton" : [ ( 'TempSignalGJets',kPhoton, [ 
                ( 'TempSignalGJetsHt040to100',23080,ntupledir+'GJets_HT-40To100_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempSignalGJetsHt100to200',9110,ntupledir+'GJets_HT-100To200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempSignalGJetsHt200to400',2281,ntupledir+'GJets_HT-200To400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempSignalGJetsHt400to600',273,ntupledir+'GJets_HT-400To600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempSignalGJetsHt600toInf',94.5,ntupledir+'GJets_HT-600ToInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM') ] )
                              ,('TempBkgdSinglePhoton',kBackground, [ 
                ( 'TempBkgdSinglePhotonD',-1,ntupledir+'SinglePhoton+Run2015D-PromptReco-v3+AOD')               
                #,('TempBkgdSinglePhotonC',-1,ntupledir+'SinglePhoton+Run2015C-PromptReco-v1+AOD') 
                ] )
                              ,('TempBkgdQCD',kBackground, [ 
                ( 'TempBkgdQCDHt200to300',1735000,ntupledir+'QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v2+AODSIM')
                ,('TempBkgdQCDHt300to500',366800,ntupledir+'QCD_HT300to500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v2+AODSIM')
                ,('TempBkgdQCDHt500to700',29370,ntupledir+'QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempBkgdQCDHt700to1000',6524,ntupledir+'QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempBkgdQCDHt1000to1500',1064,ntupledir+'QCD_HT1000to1500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v2+AODSIM') ] )
                              ,( 'TempBkgdGJets',kBackground, [ 
                ( 'TempBkgdGJetsHt040to100',23080,ntupledir+'GJets_HT-40To100_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempBkgdGJetsHt100to200',9110,ntupledir+'GJets_HT-100To200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempBkgdGJetsHt200to400',2281,ntupledir+'GJets_HT-200To400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempBkgdGJetsHt400to600',273,ntupledir+'GJets_HT-400To600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('TempBkgdGJetsHt600toInf',94.5,ntupledir+'GJets_HT-600ToInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM') ] )
                              ,('FitSinglePhoton',kPhoton, [ 
                ( 'FitSinglePhotonD',-1,ntupledir+'SinglePhoton+Run2015D-PromptReco-v3+AOD')
                #,('FitSinglePhotonC',-1,ntupledir+'SinglePhoton+Run2015C-PromptReco-v1+AOD') 
                ] )
                              ,('FitQCD',kPhoton, [ 
                ( 'FitQCDHt200to300',1735000,ntupledir+'QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v2+AODSIM')
                ,('FitQCDHt300to500',366800,ntupledir+'QCD_HT300to500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v2+AODSIM')
                ,('FitQCDHt500to700',29370,ntupledir+'QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('FitQCDHt700to1000',6524,ntupledir+'QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('FitQCDHt1000to1500',1064,ntupledir+'QCD_HT1000to1500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v2+AODSIM') ] ) ]
            ,"ShapeChIso" : [ ( 'ShapeChIsoGJets',kPhoton, [ 
                ( 'ShapeChIsoGJetsHt040to100',23080,ntupledir+'GJets_HT-40To100_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('ShapeChIsoGJetsHt100to200',9110,ntupledir+'GJets_HT-100To200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('ShapeChIsoGJetsHt200to400',2281,ntupledir+'GJets_HT-200To400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('ShapeChIsoGJetsHt400to600',273,ntupledir+'GJets_HT-400To600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                ,('ShapeChIsoGJetsHt600toInf',94.5,ntupledir+'GJets_HT-600ToInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM') ] ) 
                              ,('TempBkgdSinglePhoton',kBackground, [ 
                ( 'TempBkgdSinglePhotonD',-1,ntupledir+'SinglePhoton+Run2015D-PromptReco-v3+AOD')               
                #,('TempBkgdSinglePhotonC',-1,ntupledir+'SinglePhoton+Run2015C-PromptReco-v1+AOD') 
                ] ) 
                              ,('FitSinglePhoton',kPhoton, [ 
                ( 'FitSinglePhotonD',-1,ntupledir+'SinglePhoton+Run2015D-PromptReco-v3+AOD')
                #,('FitSinglePhotonC',-1,ntupledir+'SinglePhoton+Run2015C-PromptReco-v1+AOD') 
                ] ) ]
            ,"ElectronIso" : [ ( 'TempSignalWgPhotons',kPhoton,-1,ntupledir+'WGToLNuG_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM')
                               ,('TempSignalWgElectrons',kElectron,-1,ntupledir+'WGToLNuG_TuneCUETP8M1_13TeV-madgraphMLM-pythia8+RunIISpring15DR74-Asympt25ns_MCRUN2_74_V9-v1+AODSIM') ] }
               
# Function for making templates!
def HistExtractor(_temp,_var,_skim,_sel,_skimDir,_varBins):
    print '\nStarting template:', _skim[0]
        
    inName = os.path.join(_skimDir,_skim[1]+'.root')
    print 'Making template from:', inName
    generator = TemplateGenerator(_skim[2], _temp, inName)
    if _varBins:
        generator.setTemplateBinning((len(_var[2])-1),array.array('d', _var[2]))
    else:
        generator.setTemplateBinning(_var[1], _var[0].getMin(), _var[0].getMax())
    
    print 'Applying selection:'
    print _sel, '\n'
    tempH = generator.makeTemplate(_skim[0], _sel)

    return tempH
        
def HistToTemplate(_hist,_var,_skim,_selName,_plotDir):
    # remove negative weights
    for bin in range(_hist.GetNbinsX()+1):
        binContent = _hist.GetBinContent(bin)
        if ( binContent< 0.):
            _hist.SetBinContent(bin, 0.)
            _hist.SetBinError(bin, 0.)
        binErrorLow = _hist.GetBinErrorLow(bin)
        if ( (binContent - binErrorLow) < 0.):
            _hist.SetBinError(bin, binContent)

    print _selName
    tempname = 'template_'+_skim[0]+'_'+_selName
    temp = RooDataHist(tempname, tempname, RooArgList(_var[0]), _hist)
    
    canvas = TCanvas()
    frame = _var[0].frame()
    temp.plotOn(frame)
        
    print _skim[3]
    frame.SetTitle(_skim[3])
        
    frame.Draw()
        
    outName = os.path.join(_plotDir,tempname)
    canvas.SaveAs(outName+'.pdf')
    canvas.SaveAs(outName+'.png')
    canvas.SaveAs(outName+'.C')

    canvas.SetLogy()
    canvas.SaveAs(outName+'_Logy.pdf')
    canvas.SaveAs(outName+'_Logy.png')
    canvas.SaveAs(outName+'_Logy.C')

    return temp

# Fitting function
def FitTemplates(_name,_title,_var,_cut,_datahist,_sigtemp,_bkgtemp):
    nEvents = _datahist.sumEntries()
    sigpdf = RooHistPdf('sig', 'sig', RooArgSet(_var), _sigtemp) #, 2)
    bkgpdf = RooHistPdf('bkg', 'bkg', RooArgSet(_var), _bkgtemp) #, 2)
    nsig = RooRealVar('nsig', 'nsig', nEvents/2, 0., nEvents*1.5)
    nbkg = RooRealVar('nbkg', 'nbkg', nEvents/2, 0., nEvents*1.5)
    model = RooAddPdf("model", "model", RooArgList(sigpdf, bkgpdf), RooArgList(nsig, nbkg))
    model.fitTo(_datahist) # , Extended(True), Minimizer("Minuit2", "migrad"))
    
    canvas = TCanvas()

    frame = _var.frame()
    frame.SetTitle(_title)

    _datahist.plotOn(frame, RooFit.Name("data"))
    model.plotOn(frame, RooFit.Name("Fit"))
    model.plotOn(frame, RooFit.Components('bkg'),RooFit.Name("fake"),RooFit.LineStyle(kDashed),RooFit.LineColor(kGreen))
    model.plotOn(frame, RooFit.Components('sig'),RooFit.Name("real"),RooFit.LineStyle(kDashed),RooFit.LineColor(kRed))

    
    frame.Draw("goff")
    
    _var.setRange("selection",0.0,_cut)
    
    fReal = float(sigpdf.createIntegral(RooArgSet(_var), "selection").getVal()) / float(sigpdf.createIntegral(RooArgSet(_var)).getVal())
    fFake = float(bkgpdf.createIntegral(RooArgSet(_var), "selection").getVal()) / float(bkgpdf.createIntegral(RooArgSet(_var)).getVal())
    nReal = fReal * nsig.getVal()
    nFake = fFake * nbkg.getVal()

    # Calculate purity and print results
    print "Number of Real photons passing selection:", nReal
    print "Number of Fake photons passing selection:", nFake
    nTotal = nReal + nFake;
    purity = float(nReal) / float(nTotal)
    print "Purity of Photons is:", purity
    
    upper = TEfficiency.ClopperPearson(int(nTotal),int(nReal),0.6827,True)
    lower = TEfficiency.ClopperPearson(int(nTotal),int(nReal),0.6827,False)

    upSig = upper - purity;
    downSig = purity - lower;
    aveSig = float(upSig + downSig) / 2.0;

    text = TLatex()
    text.DrawLatexNDC(0.525,0.8,"Purity: "+str(round(purity,3))+'#pm'+str(round(aveSig,3))) 

    leg = TLegend(0.6,0.6,0.85,0.75 );
    leg.SetFillColor(kWhite);
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
    
    canvas.SetLogy()
    canvas.SaveAs(_name+'_Logy.pdf')
    canvas.SaveAs(_name+'_Logy.png')
    canvas.SaveAs(_name+'_Logy.C')

    return (purity, aveSig, nReal, nFake)

# Names for plots for Purity Calculation
PlotNames = { "Wlike" : ("Photon Purity in SingleMuon DataSet","Photon Purity in WJets Monte Carlo","Photon Purity in WJets MC Truth")
              ,"Monophoton" : ("Photon Purity in SinglePhoton DataSet","Photon Purity in #gamma+jets and QCD MC")
              ,"MonophotonBkgdComp" : ("Sideband Signal Contamination in SinglePhoton DataSet", "Sideband Signal Contamination in #gamma+jets and QCD MC") }
             
# Skims for Purity Calculation
Measurement = { "Wlike_old" : [ ('TempSignal','TempSignal',kPhoton,'Signal Template from MC') # (selection name, skim file to read from, template type, template title)
                                ,('TempBkgdData','TempBkgdData',kBackground,'Background Template from Data')
                                ,('TempBkgdMc','TempBkgdMc',kBackground,'Background Template from MC')
                                ,('FitData','FitData',kPhoton,'Fit Template from Data')
                                ,('FitMc','FitMc',kPhoton,'Fit Template from MC')
                                ,('McTruthSignal','FitMc',kPhoton,'Signal Template from MC Truth')
                                ,('McTruthBkgd','FitMc',kBackground,'Background Template from MC Truth') ]
                ,"Wlike" : [ ('TempSignalWgPhotons','TempSignalWgPhotons',kPhoton,r'Signal Template from W#gamma#rightarrowl#nu#gamma MC')
                             ,('TempBkgdSingleMuon','TempBkgdSingleMuon',kBackground,'Background Template from SingleMuon Data')
                             ,('TempBkgdWJetsToLNu','TempBkgdWJetsToLNu',kBackground,r'Background Template from W+jets#rightarrowl#nu MC')
                             ,('FitSingleMuon','FitSingleMuon',kPhoton,'Fit Template from SingleMuon Data')
                             ,('FitWJetsToLNu','FitWJetsToLNu',kPhoton,r'Fit Template from W+jets#rightarrowl#nu MC')
                             ,('WJetsTruthSignal','FitWJetsToLNu',kPhoton,r'Signal Template from W+jets#rightarrowl#nu MC Truth')
                             ,('WJetsTruthBkgd','FitWJetsToLNu',kBackground,r'Background Template from W+jets#rightarrowl#nu MC Truth') ]
                ,"Monophoton" : [ ( 'TempSignalGJets','TempSignalGJets',kPhoton,r'Signal Template from #gamma+jets MC')
                                  ,('FitSinglePhoton','FitSinglePhoton',kPhoton,'Fit Template from SinglePhoton Data')
                                  ,('FitGJetsQCD','FitGJetsQCD',kPhoton,r'Fit Template from #gamma+jets and QCD MC')
                                  ,('GJetsQCDTruthSignal','FitGJetsQCD',kPhoton,r'Truth Signal from #gamma+jets MC Truth')
                                  ,('GJetsQCDTruthBkgd','FitGJetsQCD',kBackground,r'Truth Background from QCD MC Truth') 
                                  ,('TempBkgdSinglePhoton','TempBkgdSinglePhoton',kBackground,'Background Template from SinglePhoton Data')
                                  ,('TempBkgdGJetsQCD','TempBkgdGJetsQCD',kBackground,'Background Template from QCD MC') ]
                ,"MonophotonBkgdComp" : [ ( 'TempSignalGJets','TempSignalGJets',kPhoton,r'Signal Template from #gamma+jets MC')
                                  ,('FitSinglePhoton','TempBkgdSinglePhoton',kPhoton,'Fit Template from SinglePhoton Data')
                                  ,('FitGJetsQCD','TempBkgdGJetsQCD',kPhoton,r'Fit Template from #gamma+jets and QCD MC')
                                  ,('GJetsQCDTruthSignal','TempBkgdGJetsQCD',kPhoton,r'Truth Signal from #gamma+jets MC Truth')
                                  ,('GJetsQCDTruthBkgd','TempBkgdGJetsQCD',kBackground,r'Truth Background from QCD MC Truth') 
                                  ,('TempBkgdSinglePhoton','TempBkgdSinglePhoton',kBackground,'Background Template from SinglePhoton Data')
                                  ,('TempBkgdGJetsQCD','TempBkgdGJetsQCD',kBackground,'Background Template from QCD MC') ]
                ,"MonophotonBkgdCompOld" : [ ( 'BackCompTotal','FitGJetsQCD',kBackground,'Total Background from QCD MC')
                                          ,('BackCompTrue','FitGJetsQCD',kBackground,'True Photons in Sideband from QCD MC')
                                          ,('BackCompFake','FitGJetsQCD',kBackground,"Fake Photons in Sideband from QCD MC") ]
                ,"CompGammaE" : [ ( 'TempSignalWgPhotons','TempSignalWgPhotons',kPhoton)
                                  ,('TempSignalWgElectrons','TempSignalWgElectrons',kElectron) ] }

# Selections for Purity Calculation
locationSels = {}
locationSels["barrel"] = '(TMath::Abs(selPhotons.eta) < 1.5)'
locationSels["endcap"] = '((TMath::Abs(selPhotons.eta) > 1.5) && (TMath::Abs(selPhotons.eta) < 2.4))'

hOverESels = {} 
sieieSels = {} 
chIsoSels = {}
nhIsoSels = {}
phIsoSels = {}
SigmaIetaIetaSels = {}
PhotonIsolationSels = {}

for loc in Locations:
    hOverESels[loc] = {}
    sieieSels[loc] = {}
    chIsoSels[loc] = {}
    nhIsoSels[loc] = {}
    phIsoSels[loc] = {}
    SigmaIetaIetaSels[loc] = {}
    PhotonIsolationSels[loc] = {}
    
    for pid in PhotonIds:
        hOverESel = '(selPhotons.hOverE < '+str(hOverECuts[loc][pid])+')'
        sieieSel = '(selPhotons.sieie < '+str(sieieCuts[loc][pid])+')'
        sieieSelWeighted = '( (0.891832 * selPhotons.sieie + 0.0009133) < '+str(sieieCuts[loc][pid])+')'
        chIsoSel = '(selPhotons.chIso < '+str(chIsoCuts[loc][pid])+')'
        nhIsoSel = '(selPhotons.nhIso < '+str(nhIsoCuts[loc][pid])+')'
        phIsoSel = '(selPhotons.phIso < '+str(phIsoCuts[loc][pid])+')'
        hOverESels[loc][pid] = hOverESel 
        sieieSels[loc][pid] = sieieSel
        chIsoSels[loc][pid] = chIsoSel
        nhIsoSels[loc][pid] = nhIsoSel
        phIsoSels[loc][pid] = phIsoSel
        SigmaIetaIetaSel = '('+locationSels[loc]+' && '+hOverESel+' && '+nhIsoSel+' && '+phIsoSel+')'
        PhotonIsolationSel = '('+locationSels[loc]+' && '+hOverESel+' && '+chIsoSel+' && '+nhIsoSel+')'
        # print loc, pid, SigmaIetaIetaSel, chIsoSel
        SigmaIetaIetaSels[loc][pid] = SigmaIetaIetaSel
        PhotonIsolationSels[loc][pid] = PhotonIsolationSel

cutChIsoBarrelVLoose = '(selPhotons.chIso < 4.44)'
cutChIsoBarrelSLoose = '(selPhotons.chIso < 8.44)'
        
cutIsLoose = '(selPhotons.loose)'
cutIsMedium = '(selPhotons.medium)'
cutIsTight = '(selPhotons.tight)'

cutMatchedToPhoton = '(TMath::Abs(selPhotons.matchedGen) == 22)'
cutMatchedToReal = '('+cutMatchedToPhoton+' && (!selPhotons.hadDecay) && (selPhotons.drParton > 0.5))' 
# cutMatchedToHadDecay = '('+cutMatchedToPhoton+' && (selPhotons.hadDecay))'

cutPhotonPtLow = range(20,220,40)
cutPhotonPtHigh = range(150,351,100) #  # [150]+range(200,301,50)+[500] # [150, 200, 300, 400] #
PhotonPtSels = [ [ ('PhotonPt'+str(cutPhotonPtHigh[0])+'toInf', '((selPhotons.pt > '+str(cutPhotonPtHigh[0])+'))') ]
                 + [ ('PhotonPt'+str(low)+'to'+str(high), '((selPhotons.pt > '+str(low)+') && (selPhotons.pt < '+str(high)+'))') for low, high in zip(cutPhotonPtHigh, cutPhotonPtHigh[1:]) ] 
                 + [ ('PhotonPt'+str(cutPhotonPtHigh[-1])+'toInf', '((selPhotons.pt > '+str(cutPhotonPtHigh[-1])+'))') ]
                 ,[ ( 'PhotonPt20to60', '((selPhotons.pt > 20) && (selPhotons.pt < 60) )')
                    ,('PhotonPt60to100', '((selPhotons.pt > 60) && (selPhotons.pt < 100) )')
                    ,('PhotonPt100to140', '((selPhotons.pt > 100) && (selPhotons.pt < 140) )')
                    ,('PhotonPt140to180', '((selPhotons.pt > 140) && (selPhotons.pt < 180) )')
                    ,('PhotonPt180toInf', '((selPhotons.pt > 180) )') ] ]

cutMet = [000,100,250]
MetSels = [ ('Met'+str(cutMet[0])+'toInf', '((t1Met.met > '+str(cutMet[0])+'))') ] 
MetSels = MetSels + [ ('Met'+str(low)+'to'+str(high),'((t1Met.met  >'+str(low)+') && (t1Met.met < '+str(high)+'))') for low, high in zip(cutMet,cutMet[1:]) ]
MetSels = MetSels + [ ('Met'+str(cutMet[-1])+'toInf', '((t1Met.met > '+str(cutMet[-1])+'))') ]

'''
cutChIsoSb = range(3,11,2)
ChIsoSbSels = [ ('ChIso'+str(low)+'to'+str(high), '((selPhotons.chIso > '+str(low)+') && (selPhotons.chIso < '+str(high)+'))') for low, high in zip(cutChIsoSb, cutChIsoSb[1:]) ]
ChIsoSbSels = ChIsoSbSels + [ ('ChIso'+str(1.79)+'to'+str(3), '((selPhotons.chIso > '+str(1.79)+') && (selPhotons.chIso < '+str(3.0)+'))') ]
'''

ChIsoSbBins = range(10,105,5)
ChIsoSbSels = [ ('ChIso'+str(low)+'to'+str(high), '((selPhotons.chIso > '+str(float(low)/10.0)+') && (selPhotons.chIso < '+str(float(high)/10.0)+'))') for low, high in zip(ChIsoSbBins[:-4], ChIsoSbBins[4:]) ]
ChIsoSbSels = ChIsoSbSels + [ ('ChIso'+str(1.79)+'to'+str(3.79), '((selPhotons.chIso > '+str(1.79)+') && (selPhotons.chIso < '+str(3.79)+'))') ]

#for sel in ChIsoSbSels:
#   print sel 

cutSingleMuon = '(muons.size == 1)'
cutElectronVeto = '(electrons.size == 0)'
cutTauVeto = '(ntau == 0)'
cutMet20 = '(t1Met.met > 20)'
cutWlike = '('+cutSingleMuon+' && '+cutElectronVeto+' && '+cutTauVeto+' && '+cutMet20+')'

Selections = { }

for loc in Locations:
    for pid in PhotonIds:
        for ChIsoSbSel in ChIsoSbSels:
            sigSel = SigmaIetaIetaSels[loc][pid]+' && '+chIsoSels[loc][pid]
            sbCompSel = SigmaIetaIetaSels[loc][pid]+' && '+ChIsoSbSels[0][1] # FOR SIDEBAND COMPOSITION ONLY
            sbSel = SigmaIetaIetaSels[loc][pid]+' && '+ChIsoSbSel[1]
            
            Selections[loc+'_'+pid+'_inclusive'] = [ 
                sigSel+' && '+cutMatchedToReal
                ,sbSel
                ,sbSel
                ,sigSel
                ,sigSel
                ,sigSel+' && '+cutMatchedToReal
                ,sigSel+' && !'+cutMatchedToReal ]
               
            Selections[loc+'_'+pid+'_Wlike'] = [ 
                sigSel+' && '+cutWlike+' && '+cutMatchedToReal
                ,sbSel+' && '+cutWlike
                ,sbSel+' && '+cutWlike
                ,sigSel+' && '+cutWlike
                ,sigSel+' && '+cutWlike
                ,sigSel+' && '+cutWlike+' && '+cutMatchedToReal
                ,sigSel+' && '+cutWlike+' && !'+cutMatchedToReal ]
            
            Selections[loc+'_'+pid+'_Wlike_vloose'] = [ 
                sigSel+' && '+cutWlike+' && '+cutMatchedToReal
                ,sbSel+' && '+cutWlike+' && !'+cutChIsoBarrelVLoose
                ,sbSel+' && '+cutWlike+' && !'+cutChIsoBarrelVLoose
                ,sigSel+' && '+cutWlike
                ,sigSel+' && '+cutWlike
                ,sigSel+' && '+cutWlike+' && '+cutMatchedToReal
                ,sigSel+' && '+cutWlike+' && !'+cutMatchedToReal  ]

                

            sigSels = [ sigSel+' && '+cutMatchedToReal
                        ,sigSel
                        ,sigSel
                        ,sigSel+' && '+cutMatchedToReal
                        ,sigSel+' && !'+cutMatchedToReal
                        ]
            '''
            sigSels = [ sigSel+' && '+cutMatchedToReal # FOR SIDEBAND COMPOSITION ONLY
                        ,sbCompSel
                        ,sbCompSel
                        ,sbCompSel+' && '+cutMatchedToReal
                        ,sbCompSel+' && !'+cutMatchedToReal
                        ]
            '''

            sbSels = [ sbSel+' && !'+cutChIsoBarrelVLoose
                       ,sbSel+' && '+cutChIsoBarrelVLoose
                       ,sbSel+' && !'+cutChIsoBarrelVLoose+' && '+cutChIsoBarrelSLoose
                       ,sbSel+' && !'+cutChIsoBarrelSLoose ]
            
            bkgSels = [ sbSel, sbSel ]

            baseSels = sigSels+bkgSels
            baseKey = loc+'_'+pid+'_'+ChIsoSbSel[0]
            
            compNames = [ 'real', 'low', 'med', 'high' ]
            compMatch = ['',' && '+cutMatchedToReal,' && !'+cutMatchedToReal]
        
            for ptCut in PhotonPtSels[0]:
                ptSels = [sel+' && '+ptCut[1] for sel in baseSels]
                ptKey = baseKey+'_'+ptCut[0]
                Selections[ptKey] = ptSels
              
                compSels = [sbSel+' && '+ptCut[1]+sel for sel in compMatch]
                compKey = ptKey+'_comp'
                Selections[compKey] = compSels

                for metCut in MetSels:
                    metSels = [sel+' && '+metCut[1] for sel in ptSels]
                    metKey = ptKey+'_'+metCut[0]
                    Selections[metKey] = metSels
            
                    compSels = [sbSel+' && '+ptCut[1]+' && '+metCut[1]+sel for sel in compMatch]
                    compKey = metKey+'_comp'

                    Selections[compKey] = compSels
                
            for cut in PhotonPtSels[1]:
                cuts = [ sigSel+' && '+cut[1]+' && '+cutWlike+' && '+cutMatchedToReal
                         ,sbSel+' && '+cut[1]+' && '+cutWlike
                         ,sbSel+' && '+cut[1]+' && '+cutWlike
                         ,sigSel+' && '+cut[1]+' && '+cutWlike
                         ,sigSel+' && '+cut[1]+' && '+cutWlike
                         ,sigSel+' && '+cut[1]+' && '+cutWlike+' && '+cutMatchedToReal
                         ,sigSel+' && '+cut[1]+' && '+cutWlike+' && !'+cutMatchedToReal ]
                Selections[loc+'_'+pid+'_'+cut[0]+'_Wlike'] = cuts
