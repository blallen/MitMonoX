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

logger.info('Applying vbfg setting.')

ROOT.gROOT.ProcessLine("int idtune;")
ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kSpring16;")

selconf = {
    'photonFullSelection': [
        'HOverE',
        'Sieie',
        'NHIso',
        'PhIso',
        'CHIso',
        'EVeto',
        'ChargedPFVeto'
    ],
    'photonIDTune': ROOT.idtune,
    'photonWP': 1,
    'photonSF': (0.995, 0.008, ['kPt'], (0.993, .006)),
    'hadronTFactorSource': (datadir + '/hadronTFactor_Spring16_lowpt.root', '_spring16'), # file name, suffix
    'electronTFactor': datadir + '/efakepf_data_lowpt.root/frate_fit',
    'electronTFactorUnc': 'frate_fit',
    'hadronProxyDef': ['!CHIso', '+CHIso11'],
    'ewkCorrSource': 'ewk_corr.root'
}

selconf['vbfTrigger'] = 'HLT_Photon75_R9Id90_HE10_Iso40_EBOnly_VBF'
selconf['vbfCtrlTrigger'] = 'HLT_Photon75_R9Id90_HE10_IsoM'
selconf['selTrigger'] = 'HLT_Ele27_WPTight_Gsf'
selconf['smuTrigger'] = 'HLT_IsoMu24_OR_HLT_IsoTkMu24'

## Common modifiers

execfile(thisdir + '/../2016Common/selectors_common.py')

##################
# BASE SELECTORS #
##################

def vbfgBase(sample, rname):
    """
    Base for VBF + photon.
    """

    selector = ROOT.EventSelector(rname)

    selector.setPreskim('superClusters.rawPt > 80. && Sum$(chsAK4Jets.pt_ > 50.) > 2') # 1 for the photon

    selector.addOperator(ROOT.HLTFilter(selconf['vbfTrigger']))

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'JetCleaning',
        'DijetSelection',
        'BjetVeto',
        'CopyMet'
    ]

    if not sample.data:
        operators.append('MetVariations')

    operators += [
        'AddTrailingPhotons',
        'PhotonMt',
        'PhotonMetDPhi',
        'JetMetDPhi'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setIDTune(1)
    photonSel.setMinPt(80.)

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireTight(False)
    leptonSel.setRequireMedium(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)

    jetCleaning = selector.findOperator('JetCleaning')
    jetCleaning.setCleanAgainst(ROOT.cTaus, False)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        # nominal 9.76182e-01 + 1.03735e-04 * x  -> has 43499 entries in efficiency.root ptwide_pass histogram
        # alt 9.82825e-01 + 1.37474e-05 * x  -> 29315 entries
        # taking the sqrt(N)-weighted average for nominal
        triggersf_photon = ROOT.PhotonPtWeight(ROOT.TF1('trigsf_ph_nominal', '0.9792 + 6.317e-05 * x', 80., 1000.), 'trigeff_ph')
        # single photon measurement
        triggersf_photon.addVariation("trigsf_photonUp", ROOT.TF1('trigeff_ph_up', '9.76182e-01 + 1.03735e-04 * x', 80., 1000.))
        # symmetric reflection of Down about nominal
        triggersf_photon.addVariation("trigsf_photonDown", ROOT.TF1('trigeff_ph_down', '0.9822 + 2.260e-05 * x', 80., 1000.))

        selector.addOperator(triggersf_photon)

        triggersf_vbf = ROOT.DEtajjWeight(ROOT.TF1('trigsf_vbf_nominal', '1.00989e+00 - 1.04419e-02 * x', 3., 10.), 'trigeff_vbf')
        triggersf_vbf.setDijetSelection(dijetSel)
        selector.addOperator(triggersf_vbf)

        su.addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)        

        selector.addOperator(ROOT.AddGenJets())

    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)

    return selector

def vbflBase(sample, rname):
    """
    VBF + lepton(s).
    """

    selconf['puweightSource'] = ('puweight_vbf75', datadir + '/pileup_vbf75.root')

    selector = ROOT.EventSelector(rname)

    selector.setPreskim('Sum$(chsAK4Jets.pt_ > 50.) > 1')

    trig = ROOT.HLTFilter(selconf['vbfTrigger'])
    trig.setIgnoreDecision(True)
    selector.addOperator(trig)

    operators = [
        'MetFilters',
        'LeptonSelection',
        'JetCleaning',
        'DijetSelection',
        'BjetVeto',
        'CopyMet',
        'JetMetDPhi',
        'Met'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(0.)
    dijetSel.setMinMjj(0.)

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        su.addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)

    return selector

#####################
# DERIVED SELECTORS #
#####################

def vbfg(sample, rname):
    """
    VBF + photon candidate sample.
    """

    selector = vbfgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        digenjetSel = ROOT.DijetSelection('DigenjetSelection')
        digenjetSel.setMinDEta(0.)
        digenjetSel.setMinMjj(0.)
        digenjetSel.setJetType(ROOT.DijetSelection.jGen)
        selector.addOperator(digenjetSel)

        addIDSFWeight(sample, selector)

#        if sample.name.startswith('gj'):
#            dijetSel = selector.findOperator('DijetSelection')
#            plots = ROOT.TFile.Open('/data/t3home000/yiiyama/monophoton/plots/vbfgloCtrl.root')
#            dijetSel.setDEtajjReweight(plots)

    return selector

def vbfgCtrl(sample, rname):
    """
    VBF + photon control sample.
    """

    selector = vbfg(sample, rname)

    selector.setPreskim('superClusters.rawPt > 80.')

    selector.removeOperator(selconf['vbfTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['vbfCtrlTrigger']))

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(0.)
    dijetSel.setMinMjj(0.)

    return selector

def vbfgLJCtrl(sample, rname):
    """
    VBF + photon control sample using leading 2 jets only.
    """

    selector = vbfgCtrl(sample, rname)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setLeadingOnly(True)

    return selector

def vbfgEfake(sample, rname):
    """
    VBF + photon e->photon fake control sample.
    """

    selector = vbfgBase(sample, rname)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def vbfgHfake(sample, rname):
    """
    VBF + photon had->photon fake control sample.
    """

    selector = vbfgBase(sample, rname)

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
    setupPhotonSelection(photonSel, changes = ['!CHIso', '+CHIso11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def vbfgHfakeCtrl(sample, rname):
    """
    VBF + photon had->photon fake control sample (low MET).
    """

    selector = vbfgBase(sample, rname)

    selector.setPreskim('superClusters.rawPt > 80.')

    selector.removeOperator(selconf['vbfTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['vbfCtrlTrigger']))

    selector.findOperator('DijetSelection').setIgnoreDecision(True)

    # fake rate function obtained from hadron_fake/direct.py
    hproxyWeight = ROOT.TF1('hproxyWeight', 'TMath::Exp(-0.0173 * x - 0.178)', 80., 600.)

    weight = ROOT.PhotonPtWeight(hproxyWeight, 'vbfhtfactor')
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = selconf['hadronProxyDef'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def vbfgWHadCtrl(sample, rname):
    """
    VBF + photon control sample for Wgamma, replacing the lepton and neutrino with jets.
    """

    selector = vbfg(sample, rname)

    selector.setPreskim('superClusters.rawPt > 80.')

    selector.removeOperator(selconf['vbfTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['vbfCtrlTrigger']))

    selector.findOperator('DijetSelection').setIgnoreDecision(True)

    ijet = selector.index('JetCleaning')
    selector.addOperator(ROOT.WHadronizer(), ijet)

    return selector

def vbfem(sample, rname):
    """
    VBF + EM jet.
    """

    selector = vbfgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'), changes = ['-Sieie', '+Sieie15', '-CHIso', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose', '-EVeto'])

    if not sample.data:
        addIDSFWeight(sample, selector)

    return selector

def vbfzee(sample, rname):
    """
    VBF + Zee sample for e-fake validation.
    """

    selector = vbfgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        addIDSFWeight(sample, selector)

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(1, 0)

    return selector

def vbfzeeEfake(sample, rname):
    """
    VBF + Zee sample for e-fake validation.
    """

    selector = vbfzee(sample, rname)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def vbfe(sample, rname):
    """
    VBF + single electron.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(1, 0)

    return selector

def vbfm(sample, rname):
    """
    VBF + single muon.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 1)

    return selector

def vbfee(sample, rname):
    """
    VBF + double electron.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(2, 0)

    return selector

def vbfmm(sample, rname):
    """
    VBF + single muon.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 2)

    return selector

def ph75(sample, rname):
    selector = ROOT.EventSelector(rname)
    vbfgSetting()

    selector.setPreskim('superClusters.rawPt > 50.')

    selector.addOperator(ROOT.HLTFilter('HLT_Photon50_OR_HLT_Photon75'))

    hltph50 = ROOT.HLTFilter('HLT_Photon50')
    hltph50.setIgnoreDecision(True)
    selector.addOperator(hltph50)
    hltph75 = ROOT.HLTFilter('HLT_Photon75')
    hltph75.setIgnoreDecision(True)
    selector.addOperator(hltph75)
    hltph75vbf = ROOT.HLTFilter(selconf['vbfTrigger'])
    hltph75vbf.setIgnoreDecision(True)
    selector.addOperator(hltph75vbf)

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
        'PhotonMetDPhi',
        'JetMetDPhi',
        'PhotonJetDPhi',
        'PhotonMt',
        'DijetSelection'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(50.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])
    setupPhotonSelection(photonSel, changes = ['-Sieie', '-CHIso', '+Sieie15', '+CHIso11'])

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

        su.addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)

    return selector

def signalRaw(sample, rname):
    """
    Ignore decisions of all cuts to compare shapes for different simulations.
    """

    selector = vbfg(sample, rname)

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
