import sys
import os
import array
import logging
import fnmatch

import config
import main.skimutils as su

logger = logging.getLogger(__name__)

datadir = config.baseDir + '/data'

import ROOT
ROOT.gSystem.Load(config.libobjs)
e = ROOT.panda.Event

## Selector-dependent configurations

from configs.common.selconf import selconf

logger.info('Applying ggh setting.')

ROOT.gROOT.ProcessLine("int idtune;")
ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kFall17;")

selconf['photonFullSelection'] = [
    'HOverE',
    'Sieie',
    'NHIso',
    'PhIso',
    'CHIso',
    'EVeto',
    'ChargedPFVeto',
    'NoisyRegion'
]
selconf['photonIDTune'] = ROOT.idtune
selconf['photonWP'] = 1
selconf['photonSF'] = (0.995, 0.008, ['kPt'], (0.993, .006))
selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_Spring16.root', '_Spring16')
selconf['electronTFactor'] = datadir + '/efakepf_data_ptalt2.root/frate'
selconf['electronTFactorUnc'] = ''
selconf['hadronProxyDef'] = ['!CHIso', '+CHIso11']
selconf['ewkCorrSource'] = 'ewk_corr.root'
selconf['sphTrigger'] = 'HLT_Photon200'
selconf['ecalNoiseMap'] = [
    (0, -52, 196),
    (0, 55, 67),
    (0, 58, 74),
    (0, 72, 67),
    (0, 73, 299),
    (0, 79, 67)
]

## Common modifiers

import configs.common.selectors_gen as sg
import configs.common.selectors_photon as sp

##################
# BASE SELECTORS #
##################

def gghgBase(sample, rname, selcls = None):
    """
    For low MT case.
    Monophoton candidate-like selection (high-pT photon, lepton veto, dphi(photon, MET) and dphi(jet, MET)). 
    Base for other selectors.
    """

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 210. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'DijetSelection',
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
    photonSel.setMinPt(220.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.findOperator('PhotonJetDPhi').setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        sg.addPUWeight(sample, selector)
        sg.addPDFVariation(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('Met').setThreshold(100.)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

def gghlBase(sample, rname, flavor, selcls = None):
    """
    Base for n-lepton + photon selection.
    For MC, we could use PartonSelector, but for interest of clarity and comparing cut flow
    with the other groups, we let events with all flavors pass.
    """

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 210. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))
    else:
        partons = ROOT.PartonFlavor()
        if flavor == ROOT.lElectron:
            partons.setRequiredPdgId(11)
        elif flavor == ROOT.lMuon:
            partons.setRequiredPdgId(13)

        partons.setIgnoreDecision(True)
        selector.addOperator(partons)

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'DijetSelection',
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
    photonSel.setMinPt(220.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)

    sp.setupPhotonSelection(photonSel)

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

        sg.addPUWeight(sample, selector)
        sp.addIDSFWeight(sample, selector)
        sg.addPDFVariation(sample, selector)

        if flavor == ROOT.lElectron:
            sp.addElectronIDSFWeight(sample, selector)
        else:
            sp.addMuonIDSFWeight(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('Met').setThreshold(100.)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

#####################
# DERIVED SELECTORS #
#####################

def gghg(sample, rname):
    """
    GGH + photon candidate sample.
    """

    selector = gghgBase(sample, rname)

    sp.setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        sp.addIDSFWeight(sample, selector)

    return selector

def gghgNoE(sample, rname):
    """
    Full monophoton selection filtering out electron events.
    """

    selector = gghgBase(sample, rname, selcls = ROOT.PartonSelector)
    selector.setRejectedPdgId(11)

    sp.setupPhotonSelection(selector.findOperator('PhotonSelection'))

    sp.addIDSFWeight(sample, selector)

    return selector

def fakeMetRandom(sample, rname):
    """
    Full monophoton selection with a random fraction of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def fakeMet25(sample, rname):
    """
    Full monophoton selection without with 25% of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    fakeMet.setFraction(0.25)
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def fakeMet50(sample, rname):
    """
    Full monophoton selection without with 50% of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    fakeMet.setFraction(0.50)
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def fakeMet75(sample, rname):
    """
    Full monophoton selection without with 75% of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    fakeMet.setFraction(0.75)
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def gghEfake(sample, rname):
    """
    GGH + photon e->photon fake control sample.
    """

    selector = gghgBase(sample, rname)

    sp.modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def gghHfake(sample, rname):
    """
    GGH + photon had->photon fake control sample.
    """

    selector = gghgBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = su.getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = su.getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = su.getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = su.getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    sp.modHfake(selector)

    weight = selector.findOperator('hadProxyWeight')

    weight.addVariation('proxyDefUp', hadproxyTightWeight)
    weight.addVariation('proxyDefDown', hadproxyLooseWeight)
    weight.addVariation('purityUp', hadproxyPurityUpWeight)
    weight.addVariation('purityDown', hadproxyPurityDownWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    sp.setupPhotonSelection(photonSel, changes = ['!CHIso', '+CHIso11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    sp.setupPhotonSelection(photonSel, veto = True)

    return selector

def gghe(sample, rname, selcls = None):
    """
    GGH + single electron.
    """

    selector = gghlBase(sample, rname, ROOT.lElectron, selcls = selcls)
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

def ggheLowPt(sample, rname, selcls = None):
    """
    GGH + single electron starting from single electron trigger.
    """

    selector = gghlBase(sample, rname, ROOT.lElectron, selcls = selcls)
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

def ggheEfake(sample, rname):
    selector = gghe(sample, rname, selcls = ROOT.ZeeEventSelector)

    sp.modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def ggheHfake(sample, rname):
    selector = gghe(sample, rname)

    sp.modHfake(selector)

    return selector

def gghm(sample, rname, selcls = None):
    """
    GGH + single muon.
    """

    selector = gghlBase(sample, rname, ROOT.lMuon, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(0, 1)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lMuon)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    return selector

def gghmEfake(sample, rname):
    selector = gghm(sample, rname)

    sp.modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def gghmHfake(sample, rname):
    selector = gghm(sample, rname)

    sp.modHfake(selector)

    return selector

def gghee(sample, rname):
    """
    GGH + double electron.
    """

    selector = gghlBase(sample, rname, ROOT.lElectron)
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

def gghmm(sample, rname):
    """
    GGH + single muon.
    """

    selector = gghlBase(sample, rname, ROOT.lMuon)
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

def signalRaw(sample, rname):
    """
    Ignore decisions of all cuts to compare shapes for different simulations.
    """

    selector = gghg(sample, rname)

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
