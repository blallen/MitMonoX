import sys
import os
import math

thisdir = os.path.dirname(os.path.realpath(__file__))
execfile(thisdir + '/../2016Common/plotconfig_common.py')

import ROOT

mtBinning = [0., 25., 50., 75., 100., 125., 150., 175., 200., 225., 250., 275., 300.]
mtWideBinning = [0., 300., 350., 400., 450., 500., 550., 600., 650.]
combinedFitPtBinning = [175.0, 200., 250., 300., 400., 600., 1000.0]

mtPhoMetUp = 'TMath::Sqrt(2. * t1Met.ptCorrUp * photons.scRawPt[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.phiCorrUp - photons.phi_[0]))))'
mtPhoMetDown = 'TMath::Sqrt(2. * t1Met.ptCorrDown * photons.scRawPt[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.phiCorrDown - photons.phi_[0]))))'

baseSels = {
    'photonPt175': 'photons.scRawPt[0] > 175.',
    'met150': 't1Met.pt > 150.',
    'mtPhoMet300': 'photons.mt[0] < 300.',
    'minJetDPhi0.5': 't1Met.minJetDPhi > 0.5',
    'vbfVeto': 'pdijet.size == 0'
}

hfakeSels = 'photons.nhIsoX[0][1] < 2.725 && photons.phIsoX[0][1] < 2.571 && photons.chIsoX[0][1] > 0.441'

baseSel = ' && '.join(baseSels.values())

def getConfig(confName):
    global baseSels

    if 'gghg' in confName and confName not in ['gghgj', 'gghgg']:
        config = PlotConfig('gghg')

        monophData = photonData
        if 'Blind' in confName:
            monophData = photonDataPrescaled

        for sname in monophData:
            if type(sname) == tuple:
                config.addObs(*sname)
            else:
                config.addObs(sname)

        config.baseline = baseSel 
        config.fullSelection = ''

        config.addSig('dph', 'Dark Photon', samples = ['dph-*'], scale = 0.1)
        config.addSig('dphv', 'Dark Photon (VBF)', samples = ['dphv-*'], scale = 0.1)

        config.addSigPoint('dph-nlo-125', 'H_{125}(#gamma, #gamma_{D})', color = ROOT.kCyan)
        config.addSigPoint('dphv-nlo-125', 'H_{125}(#gamma, #gamma_{D}) (VBF)', color = ROOT.kGreen)

        config.addBkg('gg', '#gamma#gamma', samples = gg, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        # config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        # config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = top, color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('hfake', 'Hadronic fakes', samples = monophData, region = 'gghHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff), cut = hfakeSels)
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma, Z#rightarrowll+#gamma', samples = ['znng-130-o', 'zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-o'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = monophData, region = 'gghEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        if confName == 'gghgFakeRandom':
            config.addBkg('fakemet', 'Fake E_{T}^{miss}', samples = gj04, region = 'fakeMetRandom', color = ROOT.TColor.GetColor(0x66, 0x66, 0x66), norm = 5.)
        elif confName == 'gghgNoGSFix':
            config.addBkg('fakemet', 'Fake E_{T}^{miss}', samples = monophData, region = 'gghgNoGSFix', color = ROOT.TColor.GetColor(0x66, 0x66, 0x66), norm = 5.)
        elif confName != 'gghgNoFake':
            config.addBkg('fakemet', 'Fake E_{T}^{miss}', samples = gj04, region = 'fakeMet50', color = ROOT.TColor.GetColor(0x66, 0x66, 0x66), norm = 5.)

        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')
        noMtPhoMet = config.baseline.replace(baseSels['mtPhoMet300'], '1')
        noMet = config.baseline.replace(baseSels['met150'], '1')
        
        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', sensitive = True) # , ymax = 5.4)
        # config.addPlot('mtPhoMetUp', 'M_{T#gamma}', mtPhoMetUp, mtBinning, unit = 'GeV', sensitive = True, ymax = 5.1)
        # config.addPlot('mtPhoMetDown', 'M_{T#gamma}', mtPhoMetDown, mtBinning, unit = 'GeV', sensitive = True, ymax = 5.1)
        config.addPlot('mtPhoMetDPhiCut', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = 't1Met.photonDPhi > 0.5', sensitive = True)
        config.addPlot('mtPhoMetWide', 'M_{T#gamma}', 'photons.mt[0]', mtWideBinning, unit = 'GeV', applyBaseline = False, cut = noMtPhoMet, overflow = True, sensitive = True)
        config.addPlot('recoilScan', 'E_{T}^{miss}', 't1Met.pt', [0. + 25. * x for x in range(21)], unit = 'GeV', applyBaseline = False, cut = noMet, overflow = True, sensitive = True)
        config.addPlot('recoilPhi', '#phi_{E_{T}^{miss}}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5), sensitive = True)
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (20, -math.pi, math.pi))
        config.addPlot('nphotons', 'N_{#gamma}', 'photons.size', (4, 0., 4.))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 0., math.pi), overflow = True, sensitive = True)
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (13, 0., math.pi), cut = 'jets.pt_ > 30.', sensitive = True)
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet, sensitive = True)
        config.addPlot('dPhiPhoJetMin', 'min#Delta#phi(#gamma, j)', 'photons.minJetDPhi[0]', (14, 0., math.pi), sensitive = True)
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.), sensitive = True)
        config.addPlot('njetsHighPt', 'N_{jet} (p_{T} > 100 GeV)', 'Sum$(jets.pt_ > 100.)', (10, 0., 10.), sensitive = True) 
        config.addPlot('jetPt', 'p_{T}^{jet}', 'jets.pt_', [0., 100., 200., 300., 400., 600., 1000.], unit = 'GeV', cut = 'jets.pt_ > 30', overflow = True, sensitive = True)
        config.addPlot('phoPtOverMet', 'E_{T}^{#gamma}/E_{T}^{miss}', 'photons.scRawPt[0] / t1Met.pt', (30, 0., 3.), sensitive = True)
        config.addPlot('phoPtOverJetPt', 'E_{T}^{#gamma}/p_{T}^{jet}', 'photons.scRawPt[0] / jets.pt_[0]', (30, 0., 3.), sensitive = True)
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.), sensitive = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (40, 0., 0.020))
        config.addPlot('sipip', '#sigma_{i#phi i#phi}', 'photons.sipip[0]', (40, 0., 0.020))
        config.addPlot('r9', 'r9', 'photons.r9[0]', (25, 0.7, 1.2))
    
        # Standard MC systematic variations
        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['efake', 'hfake', 'fakemet']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECUp'), ('t1Met.pt', 't1Met.ptCorrUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECDown'), ('t1Met.pt', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

            if group.name in ['zg', 'wg']:
                continue

            group.variations.append(Variation('minorQCDscale', reweight = 0.033))

        for gname in ['zg', 'wg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation('vgQCDscale', reweight = 'qcdscale')) # temporary off until figure out how to apply
            group.variations.append(Variation('EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation('EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation('EWKgamma', reweight = 'ewkgamma'))

        # Specific systematic variations
        proxyDefCuts = (
            'photons.nhIso < 0.264 && photons.phIso < 2.362',
            'photons.nhIso < 10.910 && photons.phIso < 3.630'
        )
        config.findGroup('hfake').variations.append(Variation('hfakeTfactor', reweight = 'proxyDef', cuts = proxyDefCuts))
        config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        config.findGroup('efake').variations.append(Variation('egfakerate', reweight = 'egfakerate'))
        if confName not in ['gghgNoFake', 'gghgFakeRandom', 'gghgNoGSFix']:
            config.findGroup('fakemet').variations.append(Variation('fakemetShape', normalize = True, regions = ('fakeMet75', 'fakeMet25')))

    elif confName == 'gghgj':
        config = PlotConfig('gghg', photonData)

        config.baseline = 'photons.scRawPt[0] > 325. && photons.minJetDPhi[0] > 0.5'
        config.fullSelection = ''

        config.addSig('dph', 'Dark Photon', samples = ['dph-*'], scale = 0.1)

        config.addSigPoint('dph-125', 'H_{125}(#gamma, #gamma_{D}) #times 0.1', color = ROOT.kCyan)

        # config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        # config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = top, color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma, Z#rightarrowll+#gamma', samples = ['znng-130-o', 'zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-p'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'gghEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('gg', '#gamma#gamma', samples = gg, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'gghHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff), cut = hfakeSels)
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))

        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', sensitive = True, ymax = 5.1)
        config.addPlot('recoilScan', 'E_{T}^{miss}', 't1Met.pt', [0. + 25. * x for x in range(21)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('recoilPhi', '#phi_{E_{T}^{miss}}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5), sensitive = True)
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (20, -math.pi, math.pi))
        config.addPlot('nphotons', 'N_{#gamma}', 'photons.size', (4, 0., 4.))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 0., math.pi), overflow = True, sensitive = True)
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (13, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (14, 0., math.pi), overflow = True)
        config.addPlot('dPhiPhoJetMin', 'min#Delta#phi(#gamma, j)', 'photons.minJetDPhi[0]', (14, 0., math.pi), applyBaseline = False, cut = 'photons.scRawPt[0] > 325.', sensitive = True)
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.), sensitive = True)
        config.addPlot('njetsHighPt', 'N_{jet} (p_{T} > 100 GeV)', 'Sum$(jets.pt_ > 100.)', (10, 0., 10.), sensitive = True) 
        config.addPlot('jetPt', 'p_{T}^{jet}', 'jets.pt_', [0., 100., 200., 300., 400., 600., 1000.], unit = 'GeV', cut = 'jets.pt_ > 30', overflow = True, sensitive = True)
        config.addPlot('phoPtOverMet', 'E_{T}^{#gamma}/E_{T}^{miss}', 'photons.scRawPt[0] / t1Met.pt', (30, 0., 3.), sensitive = True)
        config.addPlot('phoPtOverJetPt', 'E_{T}^{#gamma}/p_{T}^{jet}', 'photons.scRawPt[0] / jets.pt_[0]', (30, 0., 3.), sensitive = True)
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.), sensitive = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (40, 0., 0.020))
        config.addPlot('sipip', '#sigma_{i#phi i#phi}', 'photons.sipip[0]', (40, 0., 0.020))
        config.addPlot('r9', 'r9', 'photons.r9[0]', (25, 0.7, 1.2))
    
        # Standard MC systematic variations
        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['efake', 'hfake']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECUp'), ('t1Met.pt', 't1Met.ptCorrUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECDown'), ('t1Met.pt', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

            if group.name in ['zg', 'wg']:
                continue

            group.variations.append(Variation('minorQCDscale', reweight = 0.033))

        for gname in ['zg', 'wg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation('vgQCDscale', reweight = 'qcdscale')) # temporary off until figure out how to apply

        # Specific systematic variations
        proxyDefCuts = (
            'photons.nhIso < 0.264 && photons.phIso < 2.362',
            'photons.nhIso < 10.910 && photons.phIso < 3.630'
        )
        config.findGroup('hfake').variations.append(Variation('hfakeTfactor', reweight = 'proxyDef', cuts = proxyDefCuts))
        config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        config.findGroup('efake').variations.append(Variation('egfakerate', reweight = 'egfakerate'))
        config.findGroup('wg').variations.append(Variation('EWK', reweight = 'ewk'))
        config.findGroup('zg').variations.append(Variation('EWK', reweight = 'ewk'))


    elif confName == 'gghm':

        dPhiPhoMet = 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.realPhi))'
        dPhiJetMetMin = '((jets.size == 0) * 4. + (jets.size == 1) * TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[0] - t1Met.realPhi)) + MinIf$(TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.realPhi)), jets.size > 1 && Iteration$ < 4))'
        dRPhoParton  = 'TMath::Sqrt(TMath::Power(photons.eta_[0] - promptFinalStates.eta_, 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - promptFinalStates.phi_), 2.))'
#        MinIf$() somehow returns 0 when there is only one jet
        mt = 'TMath::Sqrt(2. * t1Met.realMet * muons.pt_[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.realPhi - muons.phi_[0]))))'

        config = PlotConfig('gghm', photonData)

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && ' + mt + ' < 160.' 
        config.fullSelection = 't1Met.pt > 150.'

        # config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'gghmHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'gghmEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = top, color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-p'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))

        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')
        noMtPhoMet = config.baseline.replace(baseSels['mtPhoMet300'], '1')
        noMet = config.baseline.replace(baseSels['met150'], '1')

        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', sensitive = True, ymax = 1.0)
        # config.addPlot('mtPhoMetUp', 'M_{T#gamma}', mtPhoMetUp, mtBinning, unit = 'GeV', sensitive = True, ymax = 1.0)
        # config.addPlot('mtPhoMetDown', 'M_{T#gamma}', mtPhoMetDown, mtBinning, unit = 'GeV', sensitive = True, ymax = 1.0)
        config.addPlot('mtPhoMetDPhiCut', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = 't1Met.photonDPhi > 0.5', sensitive = True)
        config.addPlot('mtPhoMetWide', 'M_{T#gamma}', 'photons.mt[0]', mtWideBinning, unit = 'GeV', applyBaseline = False, cut = noMtPhoMet, overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [0. + 25. * x for x in range(21)], unit = 'GeV', applyBaseline = False, cut = noMet, overflow = True, sensitive = True)
        config.addPlot('recoilPhi', '#phi_{recoil}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('realMet', 'E_{T}^{miss}', 't1Met.realMet', [25. * x for x in range(21)], unit = 'GeV', overflow = True)
        config.addPlot('realMetOverMuPt', 'E_{T}^{miss}/p_{T}^{#mu}', 't1Met.realMet / muons.pt_[0]', (20, 0., 10.), overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., math.pi))
        config.addPlot('dRPhoMu', '#DeltaR(#gamma, #mu)', 'TMath::Sqrt(TMath::Power(photons.eta_[0] - muons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[0]), 2.))', (10, 0., 4.))
        config.addPlot('mt', 'M_{T}', mt, [0. + 20. * x for x in range(9)], unit = 'GeV', overflow = True)
        config.addPlot('muPt', 'p_{T}^{#mu}', 'muons.pt_[0]', [0., 50., 100., 150., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('muEta', '#eta_{#mu}', 'muons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('muPhi', '#phi_{#mu}', 'muons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiMuMet', '#Delta#phi(#mu, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(muons.phi_[0] - t1Met.realPhi))', (13, 0., math.pi))
        config.addPlot('muIso', 'I^{#mu}_{comb.}/p_{T}', '(muons.chIso[0] + TMath::Max(muons.nhIso[0] + muons.phIso[0] - 0.5 * muons.puIso[0], 0.)) / muons.pt_[0]', (20, 0., 0.4), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{leading j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{leading j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{leading j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake' or group.name == 'efake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('muonSF', reweight = 0.01)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECUp'), ('t1Met.realMet', 't1Met.ptCorrUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECDown'), ('t1Met.realMet', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

        for gname in ['zg', 'wg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation('vgQCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation('EWK', reweight = 'ewk'))

        config.findGroup('top').variations.append(Variation('minorQCDscale', reweight = 0.033))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))


    elif confName == 'gghe':

        dPhiPhoMet = 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.realPhi))'
        dPhiJetMetMin = '(jets.size == 0) * 4. + (jets.size == 1) * TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[0] - t1Met.realPhi)) + MinIf$(TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.realPhi)), jets.size > 1 && Iteration$ < 4)'
        dRPhoParton  = 'TMath::Sqrt(TMath::Power(photons.eta_[0] - promptFinalStates.eta_, 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - promptFinalStates.phi_), 2.))'
#        MinIf$() somehow returns 0 when there is only one jet
        mt = 'TMath::Sqrt(2. * t1Met.realMet * electrons.pt_[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.realPhi - electrons.phi_[0]))))'
        mass = 'TMath::Sqrt(2. * photons.scRawPt[0] * electrons.pt_[0] * (TMath::CosH(photons.eta_[0] - electrons.eta_[0]) - TMath::Cos(photons.phi_[0] - electrons.phi_[0])))'

        config = PlotConfig('gghe', photonData)

        # config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && ' + mt + ' < 160. && t1Met.realMet > 50.' 
        # config.baseline = baseSels['photonPt175'] + ' && ' + baseSels['mtPhoMet300'] + ' && t1Met.realMet < 50.'
        config.baseline = baseSels['photonPt175'] + ' && ' + baseSels['mtPhoMet300']
        # config.fullSelection = 't1Met.pt > 150.'

        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('gg', '#gamma#gamma', samples = gg, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        # config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'ggheHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'ggheEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99), cut = 'Sum$(electrons.tight && electrons.pt_ > 30.) != 0')
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = top, color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-o'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))

        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')
        noMtPhoMet = config.baseline.replace(baseSels['mtPhoMet300'], '1')
        noMet = config.baseline.replace(baseSels['met150'], '1')

        config.addPlot('mass', 'M_{ee}', mass, (30, 60., 120.), unit = 'GeV')
        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV')
        config.addPlot('mtPhoMetOnZ', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = '{mass} > 80. && {mass} < 100.'.format(mass = mass))
        # config.addPlot('mtPhoMetUp', 'M_{T#gamma}', mtPhoMetUp, mtBinning, unit = 'GeV', sensitive = True, ymax = 0.5)
        # config.addPlot('mtPhoMetDown', 'M_{T#gamma}', mtPhoMetDown, mtBinning, unit = 'GeV', sensitive = True, ymax = 0.5)
        # config.addPlot('mtPhoMetDPhiCut', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = 't1Met.photonDPhi > 0.5', sensitive = True)
        # config.addPlot('mtPhoMetWide', 'M_{T#gamma}', 'photons.mt[0]', mtWideBinning, unit = 'GeV', applyBaseline = False, cut = noMtPhoMet, overflow = True)
        # config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [0. + 25. * x for x in range(21)], unit = 'GeV', applyBaseline = False, cut = noMet, overflow = True, sensitive = True)
        # config.addPlot('recoilPhi', '#phi_{recoil}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('realMet', 'E_{T}^{miss}', 't1Met.realMet', [25. * x for x in range(21)], unit = 'GeV', overflow = True)
        config.addPlot('realMetOverElPt', 'E_{T}^{miss}/p_{T}^{e}', 't1Met.realMet / electrons.pt_[0]', (20, 0., 10.), overflow = True)
        # config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        # config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.realPhi))', (13, 0., math.pi))
        config.addPlot('dEtaPhoEl', '#Delta#eta(#gamma, e)', 'TMath::Abs(photons.eta_[0] - electrons.eta_[0])', (10, 0., 5.))
        # config.addPlot('mt', 'M_{T}', mt, [0. + 20. * x for x in range(9)], unit = 'GeV', overflow = True)
        # config.addPlot('elPt', 'p_{T}^{e}', 'electrons.pt_[0]', [0., 50., 100., 150., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        # config.addPlot('elEta', '#eta_{e}', 'electrons.eta_[0]', (10, -2.5, 2.5))
        # config.addPlot('elPhi', '#phi_{e}', 'electrons.phi_[0]', (10, -math.pi, math.pi))
        # config.addPlot('dPhiElMet', '#Delta#phi(e, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(electrons.phi_[0] - t1Met.realPhi))', (13, 0., math.pi))
        # config.addPlot('elIso', 'I^{e}_{comb.}/p_{T}', '(electrons.chIso[0] + TMath::Max(electrons.nhIso[0] + electrons.phIso[0] - electrons.isoPUOffset[0], 0.)) / electrons.pt_[0]', (20, 0., 0.4), overflow = True)
        # config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        # config.addPlot('jetPt', 'p_{T}^{leading j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        # config.addPlot('jetEta', '#eta_{leading j}', 'jets.eta_[0]', (10, -5., 5.))
        # config.addPlot('jetPhi', '#phi_{leading j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet)
        # config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake' or group.name == 'efake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('electronSF', reweight = 0.02)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECUp'), ('t1Met.realMet', 't1Met.ptCorrUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECDown'), ('t1Met.realMet', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

        for gname in ['zg', 'wg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation('vgQCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation('EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation('EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation('EWKgamma', reweight = 'ewkgamma'))

        config.findGroup('top').variations.append(Variation('minorQCDscale', reweight = 0.033))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        config.findGroup('efake').variations.append(Variation('egfakerate', reweight = 'egfakerate'))

    elif confName == 'zeenlo':

        config = PlotConfig('tpeg', photonData)
        
        config.baseline = 'tags.pt_ > 30. && TMath::Abs(tags.eta_) < 2.4 && tags.tight && probes.scRawPt > 175. && probes.isEB && probes.mediumX[][1] && !probes.pixelVeto'
        config.fullSelection = 'probes.ptdiff > 150.' # 'TMath::Abs(TVector2::Phi_mpi_pi(tags.phi_ - probes.phi_)) > 3. && TMath::Abs(tags.pt_ - probes.pt_) > 150.'

        # config.addBkg('diboson', 'Diboson', samples =  ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('wglo', 'W#gamma', samples = ['wglo'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('tt', 'Top', samples = ['tt'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        # config.addBkg('zjets', 'Z+jets', samples = dy, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa), scale = 1.21)
        config.addBkg('zjets', 'Z+jets', samples = dyn, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa), scale = 1.03)

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', (20, 0., 1000.), unit = 'GeV', overflow = True)
        config.addPlot('metPhi', '#phi_{E_{T}^{miss}}', 't1Met.phi', (10, -math.pi, math.pi))
        config.addPlot('htReco', 'H_{T}^{reco}', 'Sum$(jets.pt_)', (100, 0., 2000.), overflow = True)
        # config.addPlot('htGen', 'H_{T}^{gen}', 'Sum$(partons.pt_ * (TMath::Abs(partons.pdgid) < 6 || partons.pdgid == 21))', (200, 0., 2000.), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_', (50, 0., 2000.), unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_', (10, -math.pi, math.pi))
        config.addPlot('tagPt', 'p_{T}^{tag}', 'tags.pt_', (20, 0., 200.), unit = 'GeV', overflow = True)
        config.addPlot('tagEta', '#eta_{tag}', 'tags.eta_', (10, -2.5, 2.5))
        config.addPlot('tagPhi', '#phi_{tag}', 'tags.phi_', (10, -math.pi, math.pi))
        config.addPlot('probePt', 'p_{T}^{probe}', 'probes.scRawPt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('probeEta', '#eta_{probe}', 'probes.eta_', (10, -2.5, 2.5))
        config.addPlot('probePhi', '#phi_{probe}', 'probes.phi_', (10, -math.pi, math.pi))
        config.addPlot('probePtDiff', 'p_{T}^{pred} - p_{T}^{probe}', 'probes.ptdiff', (40, -500., 500.))
        config.addPlot('probePtDiffWide', 'p_{T}^{pred} - p_{T}^{probe}', 'probes.ptdiff', (80, -1000., 1000.))
        # config.addPlot('zPt', 'p_{T}^{Z}', 'z.pt[0]', (20, 0., 1000.), unit = 'GeV')
        # config.addPlot('zEta', '#eta_{Z}', 'z.eta[0]', (10, -5., 5.))
        # config.addPlot('zPhi', '#phi_{Z}', 'z.phi[0]', (10, -math.pi, math.pi))
        config.addPlot('zMass', 'm_{Z}', 'tp.mass', (50, 0., 1000.), unit = 'GeV')
        config.addPlot('zMassDiff', 'm_{Z}', 'tp.mass', (50, 0., 100.), unit = 'GeV', cut = 'probes.ptdiff > 500.')
        config.addPlot('dRTagProbe', '#DeltaR(tag, probe)', 'TMath::Sqrt(TMath::Power(tags.eta_ - probes.eta_, 2.) + TMath::Power(TVector2::Phi_mpi_pi(tags.phi_ - probes.phi_), 2.))', (10, 0., 4.))
        config.addPlot('dRTagProbeDiff', '#DeltaR(tag, probe)', 'TMath::Sqrt(TMath::Power(tags.eta_ - probes.eta_, 2.) + TMath::Power(TVector2::Phi_mpi_pi(tags.phi_ - probes.phi_), 2.))', (10, 0., 4.), cut = 'probes.ptdiff > 500.')
        config.addPlot('dEtaTagProbe', '#Delta#eta(tag, probe)', 'TMath::Abs(tags.eta_ - probes.eta_)', (10, 0., 4.))
        config.addPlot('dEtaTagProbeDiff', '#Delta#eta(tag, probe)', 'TMath::Abs(tags.eta_ - probes.eta_)', (10, 0., 4.), cut = 'probes.ptdiff > 500.')
        config.addPlot('dPhiTagProbe', '#Delta#phi(tag, probe)', 'TMath::Abs(TVector2::Phi_mpi_pi(tags.phi_ - probes.phi_))', (10, 0., math.pi))
        config.addPlot('dPhiTagProbeDiff', '#Delta#phi(tag, probe)', 'TMath::Abs(TVector2::Phi_mpi_pi(tags.phi_ - probes.phi_))', (10, 0., math.pi), cut = 'probes.ptdiff > 500.')
        config.addPlot('dThetaTagProbe', '#Theta(tag, probe)', 'TMath::Abs(TMath::ACos(1 - TMath::Power(tp.mass, 2) / ( 2 * tags.pt_ * probes.pt_ * TMath::CosH(tags.eta_) * TMath::CosH(probes.eta_))))', (10, 0., math.pi))
        config.addPlot('dThetaTagProbeDiff', '#Theta(tag, probe)', 'TMath::Abs(TMath::ACos(1 - TMath::Power(tp.mass, 2) / ( 2 * tags.pt_ * probes.pt_ * TMath::CosH(tags.eta_) * TMath::CosH(probes.eta_))))', (10, 0., math.pi), cut = 'probes.ptdiff > 500.')
        config.addPlot('dPtTagProbe', 'p_{T}^{tag} - p_{T}^{probe}', 'tags.pt_ - probes.pt_', (20, -500., 500.), unit = 'GeV')


        
        for plot in list(config.plots):
            if plot.name not in ['met']:
                config.plots.append(plot.clone('BackToBack' + plot.name, applyFullSel = True))
        

    elif confName == 'gghgg':

        config = PlotConfig('gghg', photonData)

        config.baseline = baseSel.replace('t1Met.pt', 'photons.scRawPt[1]').replace(baseSels['mtPhoMet300'], '1')
        config.fullSelection = ''

        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        # config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = top, color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'gghHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'gghEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('gg', '#gamma#gamma', samples = gg, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        

        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')
        noMtPhoMet = config.baseline.replace(baseSels['mtPhoMet300'], '1')
        # noMet = config.baseline.replace(baseSels['met150'], '1')

        # config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetUp', 'M_{T#gamma}', mtPhoMetUp, mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetDown', 'M_{T#gamma}', mtPhoMetDown, mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetDPhiCut', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = 't1Met.photonDPhi > 0.5', sensitive = True)
        # config.addPlot('mtPhoMetWide', 'M_{T#gamma}', 'photons.mt[0]', mtWideBinning, unit = 'GeV', applyBaseline = False, cut = noMtPhoMet, overflow = True)
        config.addPlot('realMet', 'E_{T}^{miss}', 't1Met.pt', [10. * x for x in range(21)], unit = 'GeV', overflow = True)
        config.addPlot('pho1Pt', 'E_{T}^{#gamma1}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('pho1Eta', '#eta^{#gamma1}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('pho1Phi', '#phi^{#gamma1}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('pho2Pt', 'E_{T}^{#gamma2}', 'photons.scRawPt[1]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('pho2Eta', '#eta^{#gamma2}', 'photons.eta_[1]', (10, -1.5, 1.5))
        config.addPlot('pho2Phi', '#phi^{#gamma2}', 'photons.phi_[1]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 0., math.pi), overflow = True, sensitive = True)
        config.addPlot('dPhiPhoPho', '#Delta#phi(#gamma_{1}, #gamma_{2})', 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - photons.phi_[1]))', (13, 0., math.pi), overflow = True)
        config.addPlot('dPtPhoPho', '#Delta#E_{T}(#gamma_{1}, #gamma_{2})', 'TMath::Abs(photons.scRawPt[0] - photons.scRawPt[1])', [0., 25., 50., 75., 100., 125., 150., 200., 250., 300., 350., 400., 500.], overflow = True, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - photons.phi_[1])) > 3. && jets.size == 0')
        config.addPlot('dPtPhoPhoFull', '#Delta#E_{T}(#gamma_{1}, #gamma_{2})', 'TMath::Abs(photons.scRawPt[0] - photons.scRawPt[1])', [0., 25., 50., 75., 100., 125., 150., 200., 250., 300., 350., 400., 500.], overflow = True)
        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (10, 0., 0.020))
        config.addPlot('sipip', '#sigma_{i#phi i#phi}', 'photons.sipip[0]', (10, 0., 0.020))
        config.addPlot('r9', 'r9', 'photons.r9[0]', (25, 0.7, 1.2))
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{leading j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{leading j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{leading j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet, overflow = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

#        Standard MC systematic variations
        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['efake', 'hfake']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelvetoSF', reweight = 0.01))
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECUp'), ('t1Met.pt', 't1Met.ptCorrUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECDown'), ('t1Met.pt', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

            if group.name in ['zg', 'wg']:
                continue

            group.variations.append(Variation('minorQCDscale', reweight = 0.033))

#        Specific systematic variations
        # TODO use cuts
#        config.findGroup('hfake').variations.append(Variation('hfakeTfactor', region = ('hfakeTight', 'hfakeLoose')))
        config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        config.findGroup('efake').variations.append(Variation('egfakerate', reweight = 'egfakerate'))


    elif confName == 'gghmm':
        mass = 'TMath::Sqrt(2. * muons.pt_[0] * muons.pt_[1] * (TMath::CosH(muons.eta_[0] - muons.eta_[1]) - TMath::Cos(muons.phi_[0] - muons.phi_[1])))'
        dR2_00 = 'TMath::Power(photons.eta_[0] - muons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[0]), 2.)'
        dR2_01 = 'TMath::Power(photons.eta_[0] - muons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[1]), 2.)'

        print photonData
        config = PlotConfig('gghmm', photonData)

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && dimu.oppSign && dimu.mass[0] > 60. && dimu.mass[0] < 120.'
        config.fullSelection = 't1Met.pt > 150.'

        # config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        # config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'gghmmHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('top', 't#bar{t}#gamma', samples = ['ttg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')
        noMtPhoMet = config.baseline.replace(baseSels['mtPhoMet300'], '1')
        noMet = config.baseline.replace(baseSels['met150'], '1')

        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetUp', 'M_{T#gamma}', mtPhoMetUp, mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetDown', 'M_{T#gamma}', mtPhoMetDown, mtBinning, unit = 'GeV', sensitive = True)
        config.addPlot('mtPhoMetDPhiCut', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = 't1Met.photonDPhi > 0.5', sensitive = True)
        config.addPlot('mtPhoMetWide', 'M_{T#gamma}', 'photons.mt[0]', mtWideBinning, unit = 'GeV', applyBaseline = False, cut = noMtPhoMet, overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [0. + 25. * x for x in range(21)], unit = 'GeV', applyBaseline = False, cut = noMet, overflow = True, sensitive = True)
        config.addPlot('recoilPhi', '#phi_{recoil}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., math.pi))
        config.addPlot('dRPhoMu', '#DeltaR(#gamma, #mu)_{min}', 'TMath::Sqrt(TMath::Min(%s, %s))' % (dR2_00, dR2_01), (10, 0., 4.))
        config.addPlot('dimumass', 'M_{#mu#mu}', 'dimu.mass[0]', (12, 60., 120.), unit = 'GeV', overflow = True)
        config.addPlot('zPt', 'p_{T}^{Z}', 'dimu.pt[0]', combinedFitPtBinning, unit = 'GeV')
        config.addPlot('zEta', '#eta_{Z}', 'dimu.eta[0]', (10, -5., 5.))
        config.addPlot('zPhi', '#phi_{Z}', 'dimu.phi[0]', (10, -math.pi, math.pi))
        config.addPlot('mu0Pt', 'p_{T}^{leading #mu}', 'muons.pt_[0]', [100., 125., 150., 175., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('mu0Eta', '#eta_{leading #mu}', 'muons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('mu0Phi', '#phi_{leading #mu}', 'muons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('mu1Pt', 'p_{T}^{trailing #mu}', 'muons.pt_[1]', [0. + 10 * x for x in range(5)] + [50., 75., 100., 150., 200.], unit = 'GeV', overflow = True)
        config.addPlot('mu1Eta', '#eta_{trailing #mu}', 'muons.eta_[1]', (10, -2.5, 2.5))
        config.addPlot('mu1Phi', '#phi_{trailing #mu}', 'muons.phi_[1]', (10, -math.pi, math.pi))
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('muonSF', reweight = 0.02)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECUp'), ('t1Met.realMet', 't1Met.ptCorrUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECDown'), ('t1Met.realMet', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

        for gname in ['zg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation('vgQCDscale', reweight = 'qcdscale'))

        config.findGroup('zg').variations.append(Variation('EWK', reweight = 'ewk'))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        config.findGroup('top').variations.append(Variation('minorQCDscale', reweight = 0.033))


    elif confName == 'gghee':
        mass = 'TMath::Sqrt(2. * electrons.pt_[0] * electrons.pt_[1] * (TMath::CosH(electrons.eta_[0] - electrons.eta_[1]) - TMath::Cos(electrons.phi_[0] - electrons.phi_[1])))'
        dR2_00 = 'TMath::Power(photons.eta_[0] - electrons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[0]), 2.)'
        dR2_01 = 'TMath::Power(photons.eta_[0] - electrons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[1]), 2.)'

        config = PlotConfig('gghee', photonData)

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && diel.oppSign && diel.mass[0] > 60. && diel.mass[0] < 120.'
        config.fullSelection = 't1Met.pt > 150.'

        # config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        # config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'ggheeHfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('top', 't#bar{t}#gamma', samples = ['ttg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')
        noMtPhoMet = config.baseline.replace(baseSels['mtPhoMet300'], '1')
        noMet = config.baseline.replace(baseSels['met150'], '1')

        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetUp', 'M_{T#gamma}', mtPhoMetUp, mtBinning, unit = 'GeV', sensitive = True)
        # config.addPlot('mtPhoMetDown', 'M_{T#gamma}', mtPhoMetDown, mtBinning, unit = 'GeV', sensitive = True)
        config.addPlot('mtPhoMetDPhiCut', 'M_{T#gamma}', 'photons.mt[0]', mtBinning, unit = 'GeV', cut = 't1Met.photonDPhi > 0.5', sensitive = True)
        config.addPlot('mtPhoMetWide', 'M_{T#gamma}', 'photons.mt[0]', mtWideBinning, unit = 'GeV', applyBaseline = False, cut = noMtPhoMet, overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [0. + 25. * x for x in range(21)], unit = 'GeV', applyBaseline = False, cut = noMet, overflow = True, sensitive = True)
        config.addPlot('recoilPhi', '#phi_{recoil}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., math.pi))
        config.addPlot('dRPhoEl', '#DeltaR(#gamma, e)_{min}', 'TMath::Sqrt(TMath::Min(%s, %s))' % (dR2_00, dR2_01), (10, 0., 4.))
        config.addPlot('dielmass', 'M_{ee}', 'diel.mass[0]', (12, 60., 120.), unit = 'GeV', overflow = True)
        config.addPlot('zPt', 'p_{T}^{Z}', 'diel.pt[0]', combinedFitPtBinning, unit = 'GeV')
        config.addPlot('zEta', '#eta_{Z}', 'diel.eta[0]', (10, -5., 5.))
        config.addPlot('zPhi', '#phi_{Z}', 'diel.phi[0]', (10, -math.pi, math.pi))
        config.addPlot('el0Pt', 'p_{T}^{leading e}', 'electrons.pt_[0]', [100., 125., 150., 175., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('el0Eta', '#eta_{leading e}', 'electrons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('el0Phi', '#phi_{leading e}', 'electrons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('el1Pt', 'p_{T}^{trailing e}', 'electrons.pt_[1]', [0. + 10 * x for x in range(5)] + [50., 75., 100., 150., 200.], unit = 'GeV', overflow = True)
        config.addPlot('el1Eta', '#eta_{trailing e}', 'electrons.eta_[1]', (10, -2.5, 2.5))
        config.addPlot('el1Phi', '#phi_{trailing e}', 'electrons.phi_[1]', (10, -math.pi, math.pi))
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('electronSF', reweight = 0.04)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECUp'), ('t1Met.realMet', 't1Met.ptCorrUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiJECDown'), ('t1Met.realMet', 't1Met.ptCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.pt', 't1Met.ptGECUp')]
            replDown = [('t1Met.realMinJetDPhi', 't1Met.realMinJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.pt', 't1Met.ptGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

        for gname in ['zg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation('vgQCDscale', reweight = 'qcdscale'))

        config.findGroup('zg').variations.append(Variation('EWK', reweight = 'ewk'))
        config.findGroup('top').variations.append(Variation('minorQCDscale', reweight = 0.033))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))


    else:
        raise RuntimeError('Unknown configuration ' + confName)

    return config
