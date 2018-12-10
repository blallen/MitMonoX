import os
import logging

import config
import main.skimutils as su

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
datadir = basedir + '/data'

logger = logging.getLogger(__name__)

import ROOT

## Selector-dependent configurations

logger.info('Applying monophoton setting.')

ROOT.gROOT.ProcessLine("int idtune;")
ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kGJetsCWIso;")

selconf = {
    'photonFullSelection': [
        'HOverE',
        'Sieie',
        'NHIso',
        'PhIso',
        'CHIsoMax',
        'EVeto',
        'MIP49',
        'Time',
        'SieieNonzero',
        'SipipNonzero',
        'NoisyRegion',
        'R9Unity'
    ],
    'photonIDTune': ROOT.idtune,
    'photonWP': 1,
    'photonSF': (1.002, 0.007, ['kPt'], (0.984, .009)),
    'hadronTFactorSource': (datadir + '/hadronTFactor_GJetsCWIso.root', '_GJetsCWIso'),
    'electronTFactor': 0.0303,
    'electronTFactorUnc': 0.0726,
    'hadronProxyDef': ['!CHIsoMax', '+CHIsoMax11'],
    'ewkCorrSource': 'ewk_corr.root',
    'sphTrigger': 'HLT_Photon165_HE10',
    'smuTrigger': 'HLT_IsoMu24_OR_HLT_IsoTkMu24'
}

def setEWKSource(inflection):
    logger.info('Changing EWK inflection point to ' + str(int(inflection)))
    selconf['ewkCorrSource'] = 'ewk_corr_' + str(int(inflection)) + '.root'

def resetEWKSource():
    selconf['ewkCorrSource'] = 'ewk_corr.root'

## Common modifiers

execfile(thisdir + '/../2016Common/selectors_common.py')    

##################
# BASE SELECTORS #
##################

def monophotonBase(sample, rname, selcls = None):
    """
    Monophoton candidate-like selection (high-pT photon, lepton veto, dphi(photon, MET) and dphi(jet, MET)).
    Base for other selectors.
    """

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters'
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'Met',
        'PhotonMetDPhi',
        'JetMetDPhi',
        'PhotonJetDPhi',
        'PhotonPtOverMet',
        'PhotonMt'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(175.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)
    # leptonSel.setIgnoreDecision(True)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.findOperator('PhotonJetDPhi').setMetVariations(metVar)

        selector.addOperator(ROOT.PartonKinematics())
        
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        su.addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

def emjetBase(sample, rname):
    """
    Base selector for EM+Jet control region. For MC, a gen-level photon is required.
    """

    selector = monophotonBase(sample, rname)

    selector.removeOperator('PhotonMt')

    selector.findOperator('Met').setThreshold(0.)
    selector.findOperator('Met').setCeiling(170.)
    selector.findOperator('Met').setIgnoreDecision(False)

    photonSel = selector.findOperator('PhotonSelection')

    jets = ROOT.HighPtJetSelection()
    jets.setJetPtCut(100.)
    selector.addOperator(jets)

    dijetSel = ROOT.DijetSelection()
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)
    selector.addOperator(dijetSel)

    if not sample.data:
        genPhotonSel = ROOT.GenParticleSelection("GenPhotonSelection")
        genPhotonSel.setPdgId(22)
        genPhotonSel.setMinPt(140.)
        genPhotonSel.setMaxEta(1.7)

        # selector.addOperator(genPhotonSel, 1)

    return selector

def leptonBase(sample, rname, flavor, selcls = None):
    """
    Base for n-lepton + photon selection.
    For MC, we could use PartonSelector, but for interest of clarity and comparing cut flow
    with the other groups, we let events with all flavors pass.
    """

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))
    else:
        partons = ROOT.PartonFlavor()
        if flavor == ROOT.lElectron:
            partons.setRequiredPdgId(11)
        elif flavor == ROOT.lMuon:
            partons.setRequiredPdgId(13)

        selector.addOperator(partons)

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters',
        'LeptonRecoil',
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'PhotonMetDPhi',
        'JetMetDPhi',
        'Met',
        'PhotonPtOverMet',
        'PhotonMt'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    jetDPhi = selector.findOperator('JetMetDPhi')
    jetDPhi.setMetSource(ROOT.kInMet)

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)

    setupPhotonSelection(photonSel)

    selector.findOperator('LeptonRecoil').setFlavor(flavor)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        realMetVar = ROOT.MetVariations('RealMetVar')
        realMetVar.setMetSource(ROOT.kInMet)
        realMetVar.setPhotonSelection(photonSel)

        selector.findOperator('PhotonMetDPhi').setMetVariations(metVar)
        
        jetDPhi.setMetVariations(realMetVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        su.addPUWeight(sample, selector)
        addIDSFWeight(sample, selector)
        addPDFVariation(sample, selector)

        if flavor == ROOT.lElectron:
            addElectronIDSFWeight(sample, selector)
        else:
            addMuonIDSFWeight(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)

    if not sample.data:
        selector.findOperator('PartonFlavor').setIgnoreDecision(True)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

def elmu(sample, rname):
    """
    1e, 1mu. mostly ttbar
    """

    selector = ROOT.EventSelector(rname)

    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    selector.setPreskim('muons.size > 0 && electrons.size > 0')

    selector.addOperator(ROOT.MetFilters())

    leptons = ROOT.LeptonSelection()
    leptons.setN(1, 1)
    leptons.setStrictMu(False)
    leptons.setStrictEl(False)
    leptons.setRequireTight(False)
    selector.addOperator(leptons)

    # NOTE: photon selection is not cleaned up against leptons and we want it that way - we are interested also in photons overlapping with electrons
    photonSel = ROOT.PhotonSelection()
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])
    setupPhotonSelection(photonSel, changes = ['-EVeto'])
    photonSel.setMinPt(30.)
    photonSel.setIgnoreDecision(True)
    selector.addOperator(photonSel)

    jets = ROOT.JetCleaning()
    jets.setCleanAgainst(ROOT.cTaus, False)
    selector.addOperator(jets)

    selector.addOperator(ROOT.CopyMet())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        su.addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

    return selector

#####################
# DERIVED SELECTORS #
#####################

def monoph(sample, rname):
    """
    Full monophoton selection.
    """

    selector = monophotonBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        addIDSFWeight(sample, selector)

    return selector

def monophNoE(sample, rname):
    """
    Full monophoton selection filtering out electron events.
    """

    selector = monophotonBase(sample, rname, selcls = ROOT.PartonSelector)
    selector.setRejectedPdgId(11)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    addIDSFWeight(sample, selector)

    return selector

def monophNoLVeto(sample, rname):
    """
    Full monophoton selection without lepton veto (for lepton veto eff. scale factor measurement)
    """

    selector = monoph(sample, rname)

    selector.findOperator('LeptonSelection').setIgnoreDecision(True)

    return selector

def monophNoGSFix(sample, rname):
    """
    Full monophoton selection using originalPt / pt * scRawPt
    """

    selector = monoph(sample, rname)

    # replaces outPhoton.scRawPt with originalPt / pt * scRawPt
    # all downstream operators should be using outPhoton
    selector.findOperator('PhotonSelection').setUseOriginalPt(True)

    # copy metMuOnlyFix instead of t1Met
    selector.findOperator('CopyMet').setUseGSFix(False)

    return selector

def signalRaw(sample, rname):
    """
    Ignore decisions of all cuts to compare shapes for different simulations.
    """

    selector = monoph(sample, rname)

    selector.setPreskim('')

    cuts = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'PhotonMetDPhi',
        'JetMetDPhi',
        'Met'
    ]

    for cut in cuts:
        selector.findOperator(cut).setIgnoreDecision(True)

    selector.findOperator('PhotonSelection').setMinPt(30.)
    selector.findOperator('LeptonSelection').setN(0, 0)
    
    dimuMass = ROOT.Mass()
    dimuMass.setPrefix('dimu')
    dimuMass.setMin(60.)
    dimuMass.setMax(120.)
    dimuMass.setCollection1(ROOT.cMuons)
    dimuMass.setCollection2(ROOT.cMuons)
    dimuMass.setIgnoreDecision(True)
    selector.addOperator(dimuMass)

    dielMass = ROOT.Mass()
    dielMass.setPrefix('diel')
    dielMass.setMin(60.)
    dielMass.setMax(120.)
    dielMass.setCollection1(ROOT.cElectrons)
    dielMass.setCollection2(ROOT.cElectrons)
    dielMass.setIgnoreDecision(True)
    selector.addOperator(dielMass)

    return selector

def efake(sample, rname):
    """
    Candidate-like but with inverted electron veto
    """

    selector = monophotonBase(sample, rname)

    modEfake(selector, selections = ['!EVeto'])

    return selector

def emjet(sample, rname):
    """
    EM Object is candidate-like. used for photon purity measurement and hadronTFactor derivation.
    """

    selector = emjetBase(sample, rname)

    if not sample.data:
        # measure the parton-level dR between gamma and q/g.
        selector.addOperator(ROOT.GJetsDR())

    photonSel = selector.findOperator('PhotonSelection')
    
    setupPhotonSelection(photonSel, changes = ['-Sieie', '+Sieie15', '-CHIsoMax', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose', '-EVeto', '-MIP49', '-Time', '-SieieNonzero', '-SipipNonzero'])
        
    return selector

def hfake(sample, rname):
    """
    Candidate-like but with inverted CHIso.
    """

    selector = monophotonBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = su.getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = su.getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = su.getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = su.getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    modHfake(selector)

    weight = selector.findOperator('hadProxyWeight')

    weight.addVariation('proxyDefUp', hadproxyTightWeight)
    weight.addVariation('proxyDefDown', hadproxyLooseWeight)
    weight.addVariation('purityUp', hadproxyPurityUpWeight)
    weight.addVariation('purityDown', hadproxyPurityDownWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    setupPhotonSelection(photonSel, changes = ['!CHIsoMax', '+CHIsoMax11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def hfakeVtx(sample, rname):
    """
    Candidate-like but with inverted CHIso and vertex-adjusted proxy weighting.
    """

    selector = monophotonBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = su.getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = su.getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = su.getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = su.getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    isoTFactor = su.getFromFile(filename, 'tfactNom', 'tfactNom' + suffix)
    noIsoTFactor = su.getFromFile(datadir + '/hadronTFactorNoICH.root', 'tfactNom')
    isoVertexScore = su.getFromFile(datadir + '/vertex_scores.root', 'iso')
    noIsoVertexScore = su.getFromFile(datadir + '/vertex_scores.root', 'noIso')
    rcProb = su.getFromFile(datadir + '/randomcone.root', 'chIso')

    vtxWeight = ROOT.VtxAdjustedJetProxyWeight(isoTFactor, isoVertexScore, noIsoTFactor, noIsoVertexScore)

    vtxWeight.setRCProb(rcProb, 1.163)
    vtxWeight.addVariation('proxyDefUp', hadproxyTightWeight)
    vtxWeight.addVariation('proxyDefDown', hadproxyLooseWeight)
    vtxWeight.addVariation('purityUp', hadproxyPurityUpWeight)
    vtxWeight.addVariation('purityDown', hadproxyPurityDownWeight)

    selector.addOperator(vtxWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    setupPhotonSelection(photonSel, changes = ['!CHIsoMax', '+CHIsoMax11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def gjets(sample, rname):
    """
    For GJets MC study. 
    """
    
    selector = emjetBase(sample, rname)

    if not sample.data:
        # measure the parton-level dR between gamma and q/g.
        selector.addOperator(ROOT.GJetsDR())

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = ['-Sieie', '-CHIsoMax', '+Sieie15', '+CHIsoMax11'])
    photonSel.addSelection(False, ROOT.PhotonSelection.Sieie12, ROOT.PhotonSelection.CHIso)
    setupPhotonSelection(photonSel, veto = True)
    
    return selector

def gjets325(sample, rname):
    """
    For GJets MC study. 
    """
    
    selector = emjetBase(sample, rname)

    selector.setPreskim('superClusters.rawPt > 300. && TMath::Abs(superClusters.eta) < 1.4442')

    jets = selector.findOperator('HighPtJetSelection')
    jets.setIgnoreDecision(True)

    if not sample.data:
        # measure the parton-level dR between gamma and q/g.
        selector.addOperator(ROOT.GJetsDR())

    photonSel = selector.findOperator('PhotonSelection')
    setupPhotonSelection(photonSel)
    photonSel.setMinPt(325.)
    
    return selector

def gjSmeared(sample, rname):
    """
    Candidate-like, with a smeared MET distribution.
    """

    selector = monophotonBase(sample, rname, selcls = ROOT.SmearingSelector)

    params = {}
    paramsFile = file(datadir + '/gjSmearParams_linear.txt', 'r')
    for line in paramsFile:
        param = line.split()
        params[param[0]] = (param[1], param[2])
    paramsFile.close()

    smearing = ROOT.TF1('smearing', 'TMath::Landau(x, [0], [1]*(1. + [2]*x))', 0., 100.)
    mean = params['mean'][0]
    sigmar = params['sigmar'][0]
    alpha = params['alpha'][0]
    smearing.SetParameters(mean, sigmar, alpha) # measured in gjets/smearfit.py
    selector.setNSamples(1)
    selector.setFunction(smearing)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    addIDSFWeight(sample, selector)

    return selector

def dijet(sample, rname):
    """
    Dijet events with no overlap removal for jet vertex score study.
    """

    selector = ROOT.EventSelector(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    photonSel = ROOT.PhotonSelection()
    
    setupPhotonSelection(photonSel, changes = ['!Sieie'])
    setupPhotonSelection(photonSel, veto = True)

    selector.addOperator(photonSel)

    jets = ROOT.JetClustering()
    jets.setMinPt(30.)
    jets.setOverwrite(True)
    selector.addOperator(jets)

    photonSel.setIgnoreDecision(True)

#    jetSel = ROOT.HighPtJetSelection()
#    jetSel.setJetPtCut(150.)
#    jetSel.setNMin(2)
#    jetSel.setNMax(2)
#    selector.addOperator(jetSel)

    selector.addOperator(ROOT.JetScore())

    selector.addOperator(ROOT.CopyMet())

    if not sample.data:
        addPDFVariation(sample, selector)

    return selector

def halo(sample, rname):
    """
    Candidate sample but with inverted MIP cut and halo tag.
    """

    selector = monophotonBase(sample, rname)

    photonSel = selector.findOperator('PhotonSelection')

    # setting up loose to allow variations at plot level
    setupPhotonSelection(photonSel, changes = ['-MIP49', '-Sieie'])
    setupPhotonSelection(photonSel, veto = True)

    selector.findOperator('MetFilters').allowHalo()

    return selector

def trivialShower(sample, rname):
    """
    Candidate sample but with inverted sieie cut.
    """

    selector = monophotonBase(sample, rname)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = ['-SieieNonzero', '-SipipNonzero'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def diel(sample, rname):
    selector = leptonBase(sample, rname, ROOT.lElectron)
    selector.findOperator('LeptonSelection').setN(2, 0)

    dielMass = ROOT.Mass()
    dielMass.setPrefix('diel')
    dielMass.setMin(60.)
    dielMass.setMax(120.)
    dielMass.setCollection1(ROOT.cElectrons)
    dielMass.setCollection2(ROOT.cElectrons)
    dielMass.setIgnoreDecision(True)
    selector.addOperator(dielMass)

    dielSign = ROOT.OppositeSign()
    dielSign.setPrefix('diel')
    dielSign.setCollection1(ROOT.cElectrons)
    dielSign.setCollection2(ROOT.cElectrons)
    dielSign.setIgnoreDecision(True)
    selector.addOperator(dielSign)

    if not sample.data:
        electronLooseSF = su.getFromFile(datadir + '/egamma_electron_loose_SF_2016.root', 'EGamma_SF2D', 'electronLooseSF') # x: sc eta, y: pt
        electronTrackSF = su.getFromFile(datadir + '/egamma_electron_reco_SF_2016.root', 'EGamma_SF2D', 'electronTrackSF') # x: sc eta, y: npv

        idsf = selector.findOperator('ElectronSF')
        idsf.addFactor(electronLooseSF)
        idsf.setNParticles(2)

        track = selector.findOperator('ElectronTrackSF')
        track.addFactor(electronTrackSF)
        track.setNParticles(2)

    return selector

def dielAllPhoton(sample, rname):
    selector = diel(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lElectron)
    selector.addOperator(vtx)

    electrons = selector.findOperator('LeptonSelection')
    electrons.setRequireTight(True)

    photons = selector.findOperator('PhotonSelection')
    photons.resetSelection()
    photons.addSelection(True, ROOT.PhotonSelection.HOverE)

    return selector

def dielHfake(sample, rname):
    selector = diel(sample, rname)
        
    modHfake(selector)

    return selector

def monoel(sample, rname, selcls = None):
    selector = leptonBase(sample, rname, ROOT.lElectron, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(1, 0)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lElectron)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    metCut = ROOT.Met('RealMetCut')
    metCut.setMetSource(ROOT.kInMet)
    metCut.setThreshold(50.)
    metCut.setIgnoreDecision(True)
    selector.addOperator(metCut)

    return selector

def monoelHfake(sample, rname):
    selector = monoel(sample, rname)
    
    modHfake(selector)

    return selector

def monoelEfake(sample, rname):
    selector = monoel(sample, rname, selcls = ROOT.ZeeEventSelector)
    selector.findOperator('LeptonSelection').setStrictEl(False)

    modEfake(selector, selections = ['!EVeto'])

    return selector

def monoelQCD(sample, rname):
    selector = monoel(sample, rname)

    # by inserting FakeElectron before LeptonSelection, electron collection size
    # is already bumped up by the number of fake electrons. LeptonSelection will
    # count the number of output electron collection.
    idx = selector.index('LeptonSelection')
    selector.addOperator(ROOT.FakeElectron(), idx)

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)

    return selector

def dimu(sample, rname):
    selector = leptonBase(sample, rname, ROOT.lMuon)
    selector.findOperator('LeptonSelection').setN(0, 2)

    dimuMass = ROOT.Mass()
    dimuMass.setPrefix('dimu')
    dimuMass.setMin(60.)
    dimuMass.setMax(120.)
    dimuMass.setCollection1(ROOT.cMuons)
    dimuMass.setCollection2(ROOT.cMuons)
    dimuMass.setIgnoreDecision(True)
    selector.addOperator(dimuMass)

    dimuSign = ROOT.OppositeSign()
    dimuSign.setPrefix('dimu')
    dimuSign.setCollection1(ROOT.cMuons)
    dimuSign.setCollection2(ROOT.cMuons)
    dimuSign.setIgnoreDecision(True)
    selector.addOperator(dimuSign)

    if not sample.data:
        muonLooseSF = su.getFromFile(datadir + '/muo_muon_idsf_2016.root', 'Loose_ScaleFactor') # x: abs eta, y: pt
        muonTrackSF = su.getFromFile(datadir + '/muonpog_muon_tracking_SF_ichep.root', 'htrack2') # x: npv

        idsf = selector.findOperator('MuonSF')
        idsf.addFactor(muonLooseSF)
        idsf.setNParticles(2)

        track = selector.findOperator('MuonTrackSF')
        track.addFactor(muonTrackSF)
        track.setNParticles(2)

    return selector

def dimuAllPhoton(sample, rname):
    selector = dimu(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    muons = selector.findOperator('LeptonSelection')
    muons.setRequireTight(False)
    muons.setRequireMedium(True)

    photons = selector.findOperator('PhotonSelection')
    photons.resetSelection()
    photons.addSelection(True, ROOT.PhotonSelection.HOverE)

    return selector

def dimuHfake(sample, rname):
    selector = dimu(sample, rname)

    modHfake(selector)

    return selector

def monomu(sample, rname, selcls = None):
    selector = leptonBase(sample, rname, ROOT.lMuon, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(0, 1)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lMuon)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    return selector

def monomuLowPt(sample, rname, selcls = None):
    selector = leptonBase(sample, rname, ROOT.lMuon, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(0, 1)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lMuon)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    selector.removeOperator(selconf['sphTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))
    photons = selector.findOperator('PhotonSelection')
    photons.setMinPt(10.)

    return selector

def monomuAllPhoton(sample, rname):
    selector = monomu(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    muons = selector.findOperator('LeptonSelection')
    muons.setRequireMedium(True)

    photons = selector.findOperator('PhotonSelection')
    photons.resetSelection()
    photons.addSelection(True, ROOT.PhotonSelection.HOverE)

    return selector

def monomuHfake(sample, rname):
    selector = monomu(sample, rname)

    modHfake(selector)

    return selector

def monomuEfake(sample, rname):
    selector = monomu(sample, rname)

    modEfake(selector, selections = ['!EVeto'])

    return selector

def wenu(sample, rname):
    """
    Candidate-like selection but for W->enu, no pixel veto on the photon.
    """

    selector = monophotonBase(sample, rname, selcls = ROOT.PartonSelector)
    selector.setRequiredPdgId(11)

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(15.)

    setupPhotonSelection(photonSel, changes = ['-EVeto'])

    return selector

def monoelVertex(sample, rname):
    """
    Monoel-like selection with e or mu, with LeptonVertex
    """

    selector = monoel(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lElectron)
    selector.addOperator(vtx)

    return selector

def monomuVertex(sample, rname):
    """
    Monomu-like selection with e or mu, with LeptonVertex
    """

    selector = monomu(sample, rname)

    leptons = selector.findOperator('LeptonSelection')
    leptons.setRequireTight(False)
    leptons.setRequireMedium(True)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    return selector

def dielVertex(sample, rname):
    """
    Diel-like selection with e or mu, with LeptonVertex
    """

    selector = diel(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lElectron)
    selector.addOperator(vtx)

    return selector

def dimuVertex(sample, rname):
    """
    Dimu-like selection with e or mu, with LeptonVertex
    """

    selector = dimu(sample, rname)

    leptons = selector.findOperator('LeptonSelection')
    leptons.setRequireTight(True)
#    leptons.setRequireMedium(True)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    return selector

def monoph250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = monoph(sample, rname)
    setEWKSource(250)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoph300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = monoph(sample, rname)
    setEWKSource(300)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoph400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = monoph(sample, rname)
    setEWKSource(400)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoph500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = monoph(sample, rname)
    setEWKSource(500)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoph600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = monoph(sample, rname)
    setEWKSource(600)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def dimu250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = dimu(sample, rname)
    setEWKSource(250)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def dimu300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = dimu(sample, rname)
    setEWKSource(300)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def dimu400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = dimu(sample, rname)
    setEWKSource(400)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def dimu500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = dimu(sample, rname)
    setEWKSource(500)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def dimu600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = dimu(sample, rname)
    setEWKSource(600)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def diel250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = diel(sample, rname)
    setEWKSource(250)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def diel300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = diel(sample, rname)
    setEWKSource(300)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def diel400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = diel(sample, rname)
    setEWKSource(400)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def diel500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = diel(sample, rname)
    setEWKSource(500)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def diel600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = diel(sample, rname)
    setEWKSource(600)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monomu250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = monomu(sample, rname)
    setEWKSource(250)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monomu300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = monomu(sample, rname)
    setEWKSource(300)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monomu400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = monomu(sample, rname)
    setEWKSource(400)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monomu500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = monomu(sample, rname)
    setEWKSource(500)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monomu600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = monomu(sample, rname)
    setEWKSource(600)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoel250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = monoel(sample, rname)
    setEWKSource(250)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoel300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = monoel(sample, rname)
    setEWKSource(300)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoel400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = monoel(sample, rname)
    setEWKSource(400)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoel500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = monoel(sample, rname)
    setEWKSource(500)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector

def monoel600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = monoel(sample, rname)
    setEWKSource(600)
    addKfactor(sample, selector)
    resetEWKSource()

    return selector
