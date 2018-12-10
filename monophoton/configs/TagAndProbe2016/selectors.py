import os
import logging

logger = logging.getLogger(__name__)

import ROOT

## Selector-dependent configurations

selconf = {
    'sphTrigger': 'HLT_Photon165_HE10',
    'selTrigger': 'HLT_Ele27_WPTight_Gsf',
    'smuTrigger': 'HLT_IsoMu24_OR_HLT_IsoTkMu24'
}

## Common modifiers

import configs.common.selectors_gen as sg

## Specific modifier

def setSampleId(sample, selector):
    """Set the sample ID on TagAndProbeSelector."""

    if sample.data:
        selector.setSampleId(0)
    elif sample.name.startswith('dy'):
        selector.setSampleId(1)
    elif sample.name.startswith('tt'):
        selector.setSampleId(2)
    elif sample.name.startswith('wg'):
        selector.setSampleId(3)
    elif sample.name.startswith('gg'):
        selector.setSampleId(4)
    else:
        selector.setSampleId(99)

##################
# BASE SELECTORS #
##################

def zmumu(sample, rname):
    """
    Just dimuon. 
    """
    selector = ROOT.EventSelector(rname)

    selector.setPreskim('muons.size > 1')

    selector.addOperator(ROOT.MetFilters())

    leptons = ROOT.LeptonSelection()
    leptons.setN(0, 2)
    leptons.setStrictMu(False)
    leptons.setRequireTight(False)
    selector.addOperator(leptons)

    # LeptonVertex loads pfCandidates - turning it off for speedup
#    vtx = ROOT.LeptonVertex()
#    vtx.setSpecies(ROOT.lMuon)
#    selector.addOperator(vtx)

    mass = ROOT.Mass()
    mass.setPrefix('dimu')
    mass.setMin(60.)
    mass.setMax(120.)
    mass.setCollection1(ROOT.cMuons)
    mass.setCollection2(ROOT.cMuons)
    selector.addOperator(mass)

    jets = ROOT.JetCleaning()
    jets.setCleanAgainst(ROOT.cPhotons, False)
    jets.setCleanAgainst(ROOT.cElectrons, False)
    jets.setCleanAgainst(ROOT.cTaus, False)
    selector.addOperator(jets)

    selector.addOperator(ROOT.CopyMet())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        sg.addPUWeight(sample, selector)
        sg.addPDFVaraition(sample, selector)

    return selector

def TagAndProbeBase(sample, rname):
    """
    Base for Z->ll tag and probe stuff.
    """

    selector = ROOT.EventSelector(rname)

    operators = [
        'MetFilters',
        'LeptonSelection',
        'TauVeto',
        'TagAndProbePairZ',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters',
        'JetMetDPhi',
        'Met'
    ]
    
    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw))

        sg.addPUWeight(sample, selector)

    selector.findOperator('LeptonSelection').setN(0, 0)

    selector.findOperator('LeptonSelection').setIgnoreDecision(True)
    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    # selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cElectrons, False)
    selector.findOperator('Met').setThreshold(50.)
    selector.findOperator('Met').setIgnoreDecision(True)

    return selector

def tagprobeBase(sample, rname):
    """
    Base for selectors skimming tag & probe input trees.
    """

    selector = ROOT.TagAndProbeSelector(rname)

    setSampleId(sample, selector)

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw))
        sg.addPUWeight(sample, selector)

    return selector

#####################
# DERIVED SELECTORS #
#####################

def zeeJets(sample, rname):
    """
    Require Z->ee plus at least one high pt jet.
    """

    selector = TagAndProbeBase(sample, rname)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']), 0)

    tnp = selector.findOperator('TagAndProbePairZ')
    tnp.setTagSpecies(ROOT.cElectrons)
    tnp.setProbeSpecies(ROOT.cElectrons)

    b2b = ROOT.ZJetBackToBack()
    b2b.setTagAndProbePairZ(selector.findOperator('TagAndProbePairZ'))
    b2b.setMinJetPt(100.)
    b2b.setMinDeltaPhi(3.)
    selector.addOperator(b2b)

    return selector

def zmmJets(sample, rname):
    """
    Require Z->mumu plus at least one high pt jet.
    """

    selector = TagAndProbeBase(sample, rname)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']), 0)

    tnp = selector.findOperator('TagAndProbePairZ')
    tnp.setTagSpecies(ROOT.cMuons)
    tnp.setProbeSpecies(ROOT.cMuons)

    b2b = ROOT.ZJetBackToBack()
    b2b.setTagAndProbePairZ(selector.findOperator('TagAndProbePairZ'))
    b2b.setMinJetPt(100.)
    b2b.setMinDeltaPhi(3.)
    selector.addOperator(b2b)

    return selector

def tpeg(sample, rname):
    """
    Electron + photon tag & probe run on SinglePhoton dataset.
    """

    evtType = ROOT.kTPEG

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(evtType)

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    tp = ROOT.TPLeptonPhoton(evtType)

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(evtType))

    prb = ROOT.TPTriggerMatch.kProbe

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGNonIsoOrWithJetAndTau')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200')
    trig.addTriggerFilter('hltEG200HEFilter')
    selector.addOperator(trig)

    return selector

def tpmg(sample, rname):
    """
    Muon + photon tag & probe run on SinglePhoton dataset.
    """

    evtType = ROOT.kTPMG

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(evtType)

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    tp = ROOT.TPLeptonPhoton(evtType)

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(evtType))

    prb = ROOT.TPTriggerMatch.kProbe

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGNonIsoOrWithJetAndTau')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200')
    trig.addTriggerFilter('hltEG200HEFilter')
    selector.addOperator(trig)

    return selector

def tpegLowPt(sample, rname):
    """
    Electron + photon tag & probe run on SingleElectron dataset or MC.
    """

    evtType = ROOT.kTPEG

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(evtType)

    selector.setPreskim('Sum$(superClusters.rawPt > 25.) != 0')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    tp = ROOT.TPLeptonPhoton(evtType)
    tp.setMinProbePt(25.)
    if sample.data:
        tp.setMinTagPt(30.)

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(evtType))

    tag = ROOT.TPTriggerMatch.kTag

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele27')
    trig.addTriggerFilter('hltEle27WPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele32')
    trig.addTriggerFilter('hltEle32L1DoubleEGWPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele35L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGor')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele35')
    trig.addTriggerFilter('hltEle35noerWPTightGsfTrackIsoFilter')
    selector.addOperator(trig)
    
    prb = ROOT.TPTriggerMatch.kProbe

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGNonIsoOrWithJetAndTau')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200')
    trig.addTriggerFilter('hltEG200HEFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon75L1Seed')
    trig.addTriggerFilter('hltL1sSingleEG40')
    trig.addTriggerFilter('hltL1sSingleEG40to50')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon75')
    trig.addTriggerFilter('hltEG75R9Id90HE10IsoMTrackIsoFilter')
    trig.addTriggerFilter('hltEG75R9Id90HE10IsoMEBOnlyTrackIsoFilter')
    selector.addOperator(trig)

    return selector

def tpmgLowPt(sample, rname):
    """
    Muon + photon tag & probe run on SingleMuon dataset or MC.
    """

    evtType = ROOT.kTPMG

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(evtType)

    selector.setPreskim('Sum$(superClusters.rawPt > 25.) != 0')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    tp = ROOT.TPLeptonPhoton(evtType)
    tp.setMinProbePt(25.)
    if sample.data:
        tp.setMinTagPt(30.)

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(evtType))

#    tag = ROOT.TPTriggerMatch.kTag
#
#    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele27')
#    trig.addTriggerFilter('hltEle27WPTightGsfTrackIsoFilter')
#    selector.addOperator(trig)

    prb = ROOT.TPTriggerMatch.kProbe

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGNonIsoOrWithJetAndTau')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon200')
    trig.addTriggerFilter('hltEG200HEFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon75L1Seed')
    trig.addTriggerFilter('hltL1sSingleEG40')
    trig.addTriggerFilter('hltL1sSingleEG40to50')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'photon75')
    trig.addTriggerFilter('hltEG75R9Id90HE10IsoMTrackIsoFilter')
    trig.addTriggerFilter('hltEG75R9Id90HE10IsoMEBOnlyTrackIsoFilter')
    selector.addOperator(trig)

    return selector

def tpmmg(sample, rname):
    """
    Dimuon + photon tag & probe.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTPMMG)

    selector.setPreskim('Sum$(superClusters.rawPt > 25.) != 0')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    tp = ROOT.TPLeptonPhoton(ROOT.kTPMMG)
    tp.setMinProbePt(25.)
    tp.setMinTagPt(30.)

    selector.addOperator(tp)

    # for lepton veto efficiency measurement; just write electron and muon sizes
    veto = ROOT.TPLeptonVeto(ROOT.kTPMMG)
    veto.setIgnoreDecision(True)
    selector.addOperator(veto)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTPMMG))

#    tag = ROOT.TPTriggerMatch.kTag
#
#    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele27')
#    trig.addTriggerFilter('hltEle27WPTightGsfTrackIsoFilter')
#    selector.addOperator(trig)

    return selector

def tp2e(sample, rname):
    """
    Dielectron T&P.
    """

    evtType = ROOT.kTP2E

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(evtType)

    selector.setPreskim('electrons.size > 1')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    tp = ROOT.TPDilepton(evtType)
    tp.setMinProbePt(25.)
    tp.setMinTagPt(35.)
    tp.setTagTriggerMatch(True)

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(evtType))

    tag = ROOT.TPTriggerMatch.kTag

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele27')
    trig.addTriggerFilter('hltEle27WPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele32')
    trig.addTriggerFilter('hltEle32L1DoubleEGWPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele35L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGor')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, tag, 'ele35')
    trig.addTriggerFilter('hltEle35noerWPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    prb = ROOT.TPTriggerMatch.kProbe

    trig = ROOT.TPTriggerMatch(evtType, prb, 'ele27')
    trig.addTriggerFilter('hltEle27WPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'ele32')
    trig.addTriggerFilter('hltEle32L1DoubleEGWPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'ele35L1Seed')
    trig.addTriggerFilter('hltL1sSingleEGor')
    selector.addOperator(trig)

    trig = ROOT.TPTriggerMatch(evtType, prb, 'ele35')
    trig.addTriggerFilter('hltEle35noerWPTightGsfTrackIsoFilter')
    selector.addOperator(trig)

    return selector

def tp2m(sample, rname):
    """
    Dimuon T&P.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTP2M)

    selector.setPreskim('muons.size > 1')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    tp = ROOT.TPDilepton(ROOT.kTP2M)
    tp.setMinProbePt(25.)
    tp.setMinTagPt(30.)

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTP2M))

#    prb = ROOT.TPTriggerMatch.kProbe
#
#    trig = ROOT.TPTriggerMatch(evtType, prb, 'ele27')
#    trig.addTriggerFilter('hltEle27WPTightGsfTrackIsoFilter')
#    selector.addOperator(trig)

    return selector
