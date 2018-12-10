import fnmatch
import logging
import ROOT

import config
import main.skimutils as su
from configs.common.selconf import selconf

logger = logging.getLogger(__name__)

datadir = config.baseDir + '/data'

#######################
## UTILITY FUNCTIONS ##
#######################

def setupPhotonSelection(operator, veto = False, changes = []):
    ##### !!!!! IMPORTANT - NOTE THE RESETS #####
    if veto:
        operator.resetVeto()
    else:
        operator.resetSelection()

    sels = list(selconf['photonFullSelection'])

    for change in changes:
        if change.startswith('-'):
            try:
                sels.remove(change[1:])
            except ValueError:
                pass
        elif change.startswith('+'):
            sels.append(change[1:])
        elif change.startswith('!'):
            try:
                sels.remove(change[1:])
            except ValueError:
                pass

            sels.append(change)

    if veto:
        for sel in sels:
            if sel.startswith('!'):
                operator.addVeto(False, getattr(ROOT.PhotonSelection, sel[1:]))
            else:
                operator.addVeto(True, getattr(ROOT.PhotonSelection, sel))
    else:
        for sel in sels:
            if sel.startswith('!'):
                operator.addSelection(False, getattr(ROOT.PhotonSelection, sel[1:]))
            else:
                operator.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    for subdet, ix, iy in selconf['ecalNoiseMap']:
        operator.addNoiseMask(subdet, ix, iy)

######################
# SELECTOR MODIFIERS #
######################

def addIDSFWeight(sample, selector):
    x, y, variables, (pvSF, pvUnc) = selconf['photonSF']

    if type(x) is str and type(y) is str:
        filename, histname = x, y
        logger.info('Adding photon ID scale factor from ' + filename)
    
        idsf = ROOT.IDSFWeight(ROOT.cPhotons, 'photonSF')
        idsf.addFactor(su.getFromFile(filename, histname, newname = 'photonSF'))
        variables_compiled = tuple(map(lambda s: getattr(ROOT.IDSFWeight, s), variables))
        idsf.setVariable(*variables_compiled)
        selector.addOperator(idsf)
    
    else:
        sf, unc = x, y
        logger.info('Adding numeric photon ID scale factor')

        idsf = ROOT.ConstantWeight(sf, 'photonSF')
        idsf.setUncertaintyUp(unc)
        idsf.setUncertaintyDown(unc)
        selector.addOperator(idsf)

    pvsf = ROOT.ConstantWeight(pvSF, 'pixelVetoSF')
    pvsf.setUncertaintyUp(pvUnc)
    pvsf.setUncertaintyDown(pvUnc)
    selector.addOperator(pvsf)

def addElectronIDSFWeight(sample, selector):
    logger.info('Adding electron ID scale factor (ICHEP)')

    electronTightSF = su.getFromFile(datadir + '/egamma_electron_tight_SF_2016.root', 'EGamma_SF2D', 'electronTightSF') # x: sc eta, y: pt
    electronTrackSF = su.getFromFile(datadir + '/egamma_electron_reco_SF_2016.root', 'EGamma_SF2D', 'electronTrackSF') # x: sc eta, y: npv

    idsf = ROOT.IDSFWeight(ROOT.cElectrons, 'ElectronSF')
    idsf.addFactor(electronTightSF)
    idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

    track = ROOT.IDSFWeight(ROOT.cElectrons, 'ElectronTrackSF')
    track.addFactor(electronTrackSF)
    track.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kNpv)
    selector.addOperator(track)

def addMuonIDSFWeight(sample, selector):
    logger.info('Adding muon ID scale factor (ICHEP)')

    muonTightSF = su.getFromFile(datadir + '/muo_muon_idsf_2016.root', 'Tight_ScaleFactor', 'muonTightSF') # x: abs eta, y: pt
    muonTrackSF = su.getFromFile(datadir + '/muonpog_muon_tracking_SF_ichep.root', 'htrack2', 'muonTrackSF',) # x: npv

    idsf = ROOT.IDSFWeight(ROOT.cMuons, 'MuonSF')
    idsf.addFactor(muonTightSF)
    idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

    track = ROOT.IDSFWeight(ROOT.cMuons, 'MuonTrackSF')
    track.addFactor(muonTrackSF)
    track.setVariable(ROOT.IDSFWeight.kNpv)
    selector.addOperator(track)

def addElectronVetoSFWeight(sample, selector):
    logger.info('Adding electron veto scale factor (ICHEP)')

    # made using misc/SFmerge.py
    electronVetoSF = su.getFromFile(datadir + '/egamma_electron_veto_SF_2016.root', 'EGamma_VetoSF2D', 'electronVetoSF') # x: sc eta, y: pt

    idsf = ROOT.IDSFWeight(ROOT.nCollections, 'ElectronVetoSF')
    failingElectrons = selector.findOperator('LeptonSelection').getFailingElectrons()
    idsf.addCustomCollection(failingElectrons)
    idsf.addFactor(electronVetoSF)
    idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

def addMuonVetoSFWeight(sample, selector):
    logger.info('Adding muon veto scale factor (ICHEP)')

    # made using misc/SFmerge.py
    muonVetoSF = su.getFromFile(datadir + '/muo_muon_idsf_2016.root', 'LooseVeto_ScaleFactor', 'muonVetoSF') # x: abs eta, y: pt

    idsf = ROOT.IDSFWeight(ROOT.nCollections, 'MuonVetoSF')
    failingMuons = selector.findOperator('LeptonSelection').getFailingMuons()
    idsf.addCustomCollection(failingMuons)
    idsf.addFactor(muonVetoSF)
    idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

def addKfactor(sample, selector):
    """
    Apply the k-factor corrections.
    """

    if sample.name in ['znng-130-o', 'zllg-130-o', 'zllg-300-o', 'wnlg-130-o', 'wnlg-130-p']:
        sname = sample.name.replace('-p', '-o').replace('zllg', 'znng').replace('300-o', '130-o')

        print selector
        addQCDKfactor(sample, sname, selector)
        addEWKKfactor(sample, sname, selector)

    elif fnmatch.fnmatch(sample.name, 'gj-*') or fnmatch.fnmatch(sample.name, 'gj04-*') or fnmatch.fnmatch(sample.name, 'gje-*'):
        sname = sample.name.replace('gj04', 'gj').replace('gje', 'gj')

        addQCDKfactor(sample, sname, selector)
    
    elif sample.name == 'wglo':
        corr = ROOT.TF1('kfactor', '1.45', 80., 600.)
        qcd = ROOT.PhotonPtWeight(corr, 'QCDCorrection')
        qcd.setPhotonType(ROOT.PhotonPtWeight.kParton)
        selector.addOperator(qcd)

def addQCDKfactor(sample, sname, selector):
    corr = su.getFromFile(datadir + '/kfactor.root', sname, newname = sname + '_kfactor')
    if not corr:
        raise RuntimeError('kfactor not found for ' + sample.name)

    qcd = ROOT.PhotonPtWeight(corr, 'QCDCorrection')
    if 'gj-' in sname:
        qcd.setPhotonType(ROOT.PhotonPtWeight.kPostShower)
    else:
        qcd.setPhotonType(ROOT.PhotonPtWeight.kParton)

    for variation in ['renUp', 'renDown', 'facUp', 'facDown', 'scaleUp', 'scaleDown']:
        vcorr = su.getFromFile(datadir + '/kfactor.root', sname + '_' + variation)
        if vcorr:
            logger.info('applying qcd var %s %s', variation, sample.name)
            qcd.addVariation('qcd' + variation, vcorr)

    selector.addOperator(qcd)

def addEWKKfactor(sample, sname, selector):
    corrFile = selconf['ewkCorrSource']
    print corrFile

    if sname.startswith('znng'):
        logger.info('applying ewk %s', sample.name)

        corr = su.getFromFile(datadir + '/' + corrFile, sname, newname = sname + '_ewkcorr')
        ewk = ROOT.PhotonPtWeight(corr, 'EWKNLOCorrection')
        ewk.setPhotonType(ROOT.PhotonPtWeight.kParton)

        for variation in ['straightUp', 'straightDown', 'twistedUp', 'twistedDown', 'gammaUp', 'gammaDown']:
            vcorr = su.getFromFile(datadir + '/' + corrFile, sname + '_' + variation)
            if vcorr:
                logger.info('applying ewk var %s %s', variation, sample.name)
                ewk.addVariation('ewk' + variation, vcorr)

        selector.addOperator(ewk)

    elif sample.name.startswith('wnlg'):
        logger.info('applying ewk %s', sample.name)

        suffix = '_p'
        corrp = su.getFromFile(datadir + '/' + corrFile, sname + suffix, newname = sname + suffix + '_ewkcorr')
        suffix = '_m'
        corrm = su.getFromFile(datadir + '/' + corrFile, sname + suffix, newname = sname + suffix + '_ewkcorr')

        ewk = ROOT.PhotonPtWeightSigned(corrp, corrm, 'EWKNLOCorrection')

        for variation in ['straightUp', 'straightDown', 'twistedUp', 'twistedDown', 'gammaUp', 'gammaDown']:
            vcorrp = su.getFromFile(datadir + '/' + corrFile, sname + '_p_' + variation)
            vcorrm = su.getFromFile(datadir + '/' + corrFile, sname + '_m_' + variation)
            ewk.addVariation('ewk' + variation, vcorrp, vcorrm)

        selector.addOperator(ewk)

def modHfake(selector):
    """Append PhotonPtWeight with hadProxyWeight and set up the photon selections."""

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyWeight = su.getFromFile(filename, 'tfactNom', 'tfactNom' + suffix)

    weight = ROOT.PhotonPtWeight(hadproxyWeight, 'hadProxyWeight')
    weight.setPhotonType(ROOT.PhotonPtWeight.kReco)
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = selconf['hadronProxyDef'])
    setupPhotonSelection(photonSel, veto = True)

def modEfake(selector, selections = []):
    """Append PhotonPtWeight with eproxyWeight and set up the photon selections."""

    nom = selconf['electronTFactor']
    unc = selconf['electronTFactorUnc']

    if type(nom) is str:
        # nom = file.root/obj
        filename = nom[:nom.find('.root') + 5]
        objname = nom[nom.find('.root') + 6:]
        logger.info('Adding electron fake rate from %s/%s', filename, objname)
    
        eproxyWeight = su.getFromFile(filename, objname)
        weight = ROOT.PhotonPtWeight(eproxyWeight, 'egfakerate')
        selector.addOperator(weight)

        if unc:
            if type(unc) is bool:
                weight.useErrors(True) # use errors of eleproxyWeight as syst. variation
            else:
                up = su.getFromFile(filename, unc + 'Up')
                weight.addVariation('egfakerateUp', up)
                down = su.getFromFile(filename, unc + 'Down')
                weight.addVariation('egfakerateDown', down)
    
    elif type(nom) is float:
        frate = nom
        logger.info('Adding numeric electron fake rate %f +- %f', frate, unc)

        weight = ROOT.ConstantWeight(frate, 'egfakerate')
        weight.setUncertaintyUp(unc)
        weight.setUncertaintyDown(unc)
        selector.addOperator(weight)

    else:
        logger.info('Adding electron fake rate from TF1 ' + nom.GetTitle())

        # type is TF1
        weight = ROOT.PhotonPtWeight(nom, 'egfakerate')
        selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = selections + ['-EVeto', '-ChargedPFVeto'])
    setupPhotonSelection(photonSel, veto = True)
