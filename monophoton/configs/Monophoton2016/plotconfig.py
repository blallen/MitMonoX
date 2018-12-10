import os
import math

from main.plotutil import *

thisdir = os.path.dirname(os.path.realpath(__file__))
execfile(thisdir + '/../2016Common/plotconfig_common.py')

import ROOT

wiscFitPtBinning = [175., 190., 250., 400., 700., 1000.]
mtPhoMetBinning = [0., 200., 300., 400., 500., 600., 700., 800., 1000., 1200.]
#combinedFitPtBinning = [175.0, 200., 225., 250., 275., 300., 325., 350., 400., 450., 500., 600., 800., 1000.0]
combinedFitPtBinning = [175.0, 200., 250., 300., 400., 600., 1000.0]
fitTemplateBinning = [-1 * (bin - 175.) for bin in reversed(combinedFitPtBinning)] + [bin - 175. for bin in combinedFitPtBinning[1:]]

baseSels = {
    'photonPt175': 'photons.scRawPt[0] > 175.',
    'met170': 't1Met.pt > 170.',
    'photonDPhi0.5': 't1Met.photonDPhi > 0.5',
    'minJetDPhi0.5': 't1Met.minJetDPhi > 0.5',
    'photonPtOverMet1.4': '(photons.scRawPt[0] / t1Met.pt) < 1.4',
#    'mtPhoMet100': 'mtPhoMet > 100.'
}

hfakeSels = 'photons.nhIsoX[0][2] < 2.792 && photons.phIsoX[0][2] < 2.176 && photons.chIsoMaxX[0][2] > 1.146'

baseSel = ' && '.join(baseSels.values())

def getConfig(confName):
    global baseSels

    if 'monoph' in confName or 'horizontal' in confName or 'vertical' in confName:
        config = PlotConfig('monoph')

        monophData = photonData
        if 'ICHEP' in confName:
            monophData = photonDataICHEP
        elif 'Blind' in confName:
            monophData = photonDataPrescaled

        for sname in monophData:
            if type(sname) == tuple:
                config.addObs(*sname)
            else:
                config.addObs(sname)

        if '0' in confName:
            vgRegion = confName.strip('HighPhi').strip('LowPhi')
        else:
            vgRegion = config.name

        config.fullSelection = 'muons.size == 0 && electrons.size == 0' # photons.scRawPt[0] > 600.'

        if 'LowPhi' in confName or 'horizontal' in confName:
            config.baseline = baseSel + ' && (TMath::Abs(TMath::Abs(TVector2::Phi_mpi_pi(TVector2::Phi_mpi_pi(photons.phi_[0] + 0.005) - {halfpi})) - {halfpi}) < 0.5)'.format(halfpi = math.pi * 0.5)
            phiFactor = 1. / math.pi
        elif 'HighPhi' in confName or 'vertical' in confName:
            config.baseline = baseSel + ' && (TMath::Abs(TMath::Abs(TVector2::Phi_mpi_pi(TVector2::Phi_mpi_pi(photons.phi_[0] + 0.005) - {halfpi})) - {halfpi}) > 0.5)'.format(halfpi = math.pi * 0.5)
            phiFactor = (math.pi - 1.) / math.pi
        else:
            config.baseline = baseSel
            phiFactor = 1.

        spikeNorm = phiFactor * 23.9 * config.effLumi() / 35900.

        # config.addSig('dmv', 'DM V', samples = ['dmv-*'])
        # config.addSig('dma', 'DM A', samples = ['dma-*'])
        config.addSig('dmvlo', 'DM V LO', samples = ['dmvlo-*'])
        config.addSig('dmalo', 'DM A LO', samples = ['dmalo-*'])
        config.addSig('dmvh', 'DM V NLO', samples = ['dmvh-*'])
        config.addSig('dmah', 'DM A NLO', samples = ['dmah-*'])
        # config.addSig('add', 'ADD', samples = ['add-*'])
        # config.addSig('dmvp', 'DM V', samples = ['dmvp-*'])
        # config.addSig('dph', 'DPH', samples = ['dph-*'])

        # config.addSigPoint('add-3-8', '#scale[0.7]{ADD +8d M_{D} = 3 TeV}', color = ROOT.kRed)
        # config.addSigPoint('dmvlo-1000-1', 'DMV 1000 LO', color = ROOT.kBlue)
        config.addSigPoint('dmvh-1000-1', 'DMV 1000', color = ROOT.kBlue)
        # config.addSigPoint('dmvp-1000-1', 'DMV1000', color = ROOT.kCyan)
        # config.addSigPoint('dph-1000', 'DPH1000', color = ROOT.kCyan)

        lowDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], 't1Met.minJetDPhi < 0.5')

        config.addBkg('halo', 'Beam halo', samples = monophData, region = 'halo', color = ROOT.TColor.GetColor(0x55, 0x55, 0x55), cut = 'metFilters.globalHalo16 && photons.mipEnergy[0] > 4.9', scale = 1. / 3000.)
        config.addBkg('spike', 'Spikes', samples = monophData, region = 'offtimeIso', color = ROOT.TColor.GetColor(0xaa, 0xaa, 0xaa), norm = spikeNorm) # 8.9
        if 'Merged' in confName:
            config.addBkg('minor', 'Other SM', samples = ['ttg', 'tg', 'ww', 'wz', 'zz'] + minor + wlnun + gj, color = ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
        else:
            config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xcc, 0x88, 0x44))
            config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
            config.addBkg('gg', '#gamma#gamma', samples = minor, color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
            config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0x55, 0xbb, 0x66))
            config.addBkg('gjets', '#gamma + jets', samples = gj, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc)) # , altbaseline = lowDPhiJet, scale = 0.147)
        config.addBkg('hfake', 'Hadron fakes', samples = monophData, region = 'hfake', color = ROOT.TColor.GetColor(0x55, 0x66, 0xff), cut = hfakeSels)
        config.addBkg('efake', 'Electron fakes', samples = monophData, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-p'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130-o'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        noDPhiPhoton = config.baseline.replace(baseSels['photonDPhi0.5'], '1')
        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')

        # config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False, sensitive = True)
        config.addPlot('cutcount', 'events', '0.5', [0., 1.], overflow = True, applyFullSel = True, sensitive = True)
        config.addPlot('cutcountHighPt', 'events', '0.5', [0., 1.], cut = 'photons.scRawPt[0] > 400.', overflow = True, applyFullSel = True, sensitive = True)
        config.addPlot('recoil', 'E_{T}^{miss}', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True, sensitive = True)
        # config.addPlot('recoilScan', 'E_{T}^{miss}', 't1Met.pt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True, sensitive = True)
        # config.addPlot('mtPhoMetFullDPhi', 'M_{T#gamma}', mtPhoMet, (12, 0., 1200.), unit = 'GeV', overflow = True, applyBaseline = False, cut = noDPhiPhoton, sensitive = True)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, sensitive = True, ymax = 200., ymin = 0.0003)
        config.addPlot('phoPtFine', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175.0, 200., 250., 300., 400., 500., 600., 700., 800., 900., 1000., 1250., 1500.], unit = 'GeV', overflow = True, applyFullSel = True, sensitive = True)
        # config.addPlot('phoPtWisc', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', wiscFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, sensitive = True)
        # config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (20, -math.pi, math.pi))
        config.addPlot('nphotons', 'N_{#gamma}', 'photons.size', (4, 0., 4.))
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 0., math.pi), applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('dPhiPhoMetFine', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 2.5, 3.15), sensitive = True, applyBaseline = False, cut = noDPhiPhoton)
        # config.addPlot('dPhiPhoMetFineHighPt', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 2.5, 3.15), sensitive = True, applyBaseline = False, cut = noDPhiPhoton + ' && photons.scRawPt[0] > 600.')
        config.addPlot('dPhiPhoMetSuperFine', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (10, 2.9, 3.15), sensitive = True, applyBaseline = False, cut = noDPhiPhoton)
        # config.addPlot('dPhiPhoMetSuperFineHighPt', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (10, 2.9, 3.15), sensitive = True, applyBaseline = False, cut = noDPhiPhoton + ' && photons.scRawPt[0] > 600.')
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (13, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet)
        config.addPlot('dPhiPhoJetMin', 'min#Delta#phi(#gamma, j)', 'photons.minJetDPhi[0]', (14, 0., math.pi))
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.))
        # config.addPlot('njetsHighPt', 'N_{jet} (p_{T} > 100 GeV)', 'Sum$(jets.pt_ > 100.)', (10, 0., 10.)) # , cut = 'jets.pt_ > 100.')
        config.addPlot('jetPt', 'p_{T}^{jet}', 'jets.pt_', [0., 100., 200., 300., 400., 600., 1000.], unit = 'GeV', cut = 'jets.pt_ > 30', overflow = True)
        config.addPlot('phoPtOverMet', 'E_{T}^{#gamma}/E_{T}^{miss}', 'photons.scRawPt[0] / t1Met.pt', (30, 0., 3.), overflow = True)
        config.addPlot('phoPtOverJetPt', 'E_{T}^{#gamma}/p_{T}^{jet}', 'photons.scRawPt[0] / jets.pt_[0]', (20, 0., 10.), overflow = True)
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.), sensitive = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (40, 0., 0.020))
        config.addPlot('sipip', '#sigma_{i#phi i#phi}', 'photons.sipip[0]', (40, 0., 0.020))
        config.addPlot('r9', 'r9', 'photons.r9[0]', (25, 0.7, 1.2))
        config.addPlot('etaWidth', 'etaWidth', 'photons.etaWidth[0]', (30, 0.005, .020))
        config.addPlot('phiWidth', 'phiWidth', 'photons.phiWidth[0]', (18, 0., 0.05))
        config.addPlot('time', 'time', 'photons.time[0]', (20, -5., 5.), unit = 'ns')
        config.addPlot('timeSpan', 'timeSpan', 'photons.timeSpan[0]', (20, -20., 20.), unit = 'ns')
        """
        config.addPlot('dPhiJetMetMinPhi3', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (14, 0., math.pi), applyBaseline = False, cut = noDPhiJet + ' && photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8')
        config.addPlot('phoEtaPhi3', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5), cut = 'photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8')
        config.addPlot('phoPtOverMetPhi3', 'E_{T}^{#gamma}/E_{T}^{miss}', 'photons.scRawPt[0] / t1Met.pt', (30, 0., 3.), cut = 'photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8', overflow = True)
        config.addPlot('phoPtOverJetPtPhi3', 'E_{T}^{#gamma}/p_{T}^{jet}', 'photons.scRawPt[0] / jets.pt_[0]', (20, 0., 10.), cut = 'photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8', overflow = True)
        config.addPlot('njetsPhi3', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (6, 0., 6.), ymax = 5.e+3, cut = 'photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8')
        config.addPlot('jetPtPhi3', 'p_{T}^{jet}', 'jets.pt_', [0., 100., 200., 300., 400., 600., 1000.], unit = 'GeV', cut = 'jets.pt_ > 30 && photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8', overflow = True)
        config.addPlot('timeSpanPhi3', 'timeSpan', 'photons.timeSpan[0]', (20, -20., 20.), unit = 'ns', cut = 'photons.phi_[0] > 2.2 && photons.phi_[0] < 2.8')
        config.addPlot('timeSpanNonPhi3', 'timeSpan', 'photons.timeSpan[0]', (20, -20., 20.), unit = 'ns', cut = 'photons.phi_[0] < 2.2 || photons.phi_[0] > 2.8')
        """

        if 'PtSplit' in confName:
            for plot in list(config.plots):
                if plot.name not in ['phoPtHighMet', 'photPtScan', 'phoPtWisc']:
                    plot.logy = False
                    if plot.cut != '':
                        config.plots.append(plot.clone(plot.name + "HighPhoPt", cut = '(' + plot.cut + ') && photons.scRawPt[0] > 600.'))
                        config.plots.append(plot.clone(plot.name + "LowPhoPt", cut = '(' + plot.cut + ') && photons.scRawPt[0] < 600.'))
                    else:
                        config.plots.append(plot.clone(plot.name + "HighPhoPt", cut = 'photons.scRawPt[0] > 600.'))
                        config.plots.append(plot.clone(plot.name + "LowPhoPt", cut = 'photons.scRawPt[0] < 600.'))
                    if plot.name != 'count':
                        config.plots.remove(plot)

        # Standard MC systematic variations
        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['efake', 'hfake', 'halo', 'spike']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))
            # group.variations.append(Variation('muonVetoSF', reweight = 'MuonVetoSF'))
            group.variations.append(Variation('electronVetoSF', reweight = 'ElectronVetoSF'))
            

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
            group.variations.append(Variation(gname + 'QCDscale', reweight = 'qcdscale')) 
            group.variations.append(Variation(gname + 'EWKoverall', reweight = 'ewkstraight')) 
            group.variations.append(Variation(gname + 'EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation(gname + 'EWKgamma', reweight = 'ewkgamma'))

        # Specific systematic variations
        config.findGroup('spike').variations.append(Variation('spikeNorm', reweight = 0.33))
        haloCuts = (
            'metFilters.globalHalo16 && photons.mipEnergy[0] > 2.45',
            'metFilters.globalHalo16 && photons.mipEnergy[0] > 9.8'
        )
        config.findGroup('halo').variations.append(Variation('haloShape', cuts = haloCuts))
        proxyDefCuts = (
            'photons.nhIso < 0.264 && photons.phIso < 2.362',
            'photons.nhIso < 10.910 && photons.phIso < 3.630'
        )
        config.findGroup('hfake').variations.append(Variation('hfakeTfactor', reweight = 'proxyDef', cuts = proxyDefCuts))
        config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
#        config.findGroup('hfake').variations.append(Variation('vertex', reweight = 0.5))
        config.findGroup('efake').variations.append(Variation('egfakerate', reweight = 'egfakerate'))

    elif 'dimu' in confName:
        mass = 'TMath::Sqrt(2. * muons.pt_[0] * muons.pt_[1] * (TMath::CosH(muons.eta_[0] - muons.eta_[1]) - TMath::Cos(muons.phi_[0] - muons.phi_[1])))'
        dR2_00 = 'TMath::Power(photons.eta_[0] - muons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[0]), 2.)'
        dR2_01 = 'TMath::Power(photons.eta_[0] - muons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[1]), 2.)'

        config = PlotConfig('dimu', photonData)

        if '0' in confName:
            vgRegion = confName
        else:
            vgRegion = config.name

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && dimu.oppSign && dimu.mass[0] > 60. && dimu.mass[0] < 120.'  # met is the recoil (Operator LeptonRecoil)
        config.fullSelection = 'muons.size == 2 && electrons.size == 0'

        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xcc, 0x88, 0x44))
        config.addBkg('top', 't#bar{t}#gamma', samples = ['ttg'], color = ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'dimuHfake', color = ROOT.TColor.GetColor(0x55, 0x66, 0xff))
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        noDPhiPhoton = config.baseline.replace(baseSels['photonDPhi0.5'], '1')
        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')

        config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False)
        config.addPlot('recoil', 'Recoil', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMetFullDPhi', 'M_{T#gamma}', mtPhoMet, (12, 0., 1200.), unit = 'GeV', overflow = True, applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, ymax = 5., ymin = 0.0003)
        config.addPlot('phoPtWisc', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', wiscFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True)
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('dPhiPhoMetMt100', '#Delta#phi(#gamma, U)', "t1Met.photonDPhi", (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton + ' && ' + mtPhoMet + ' > 100.', overflow = True)
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
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., 3.50), applyBaseline = False, cut = noDPhiJet)
#        config.addPlot('dPhiJetRecoilMin', 'min#Delta#phi(U, j)', 'TMath::Abs(t1Met.minJetDPhi)', (14, 0., 3.50), cut = 'jets.size != 0')
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
#        config.addPlot('partonID', 'PGD ID', 'TMath::Abs(photons.matchedGen[0])', (31, 0., 31.), overflow = True)

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('muonSF', reweight = 0.02)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))
            # group.variations.append(Variation('muonVetoSF', reweight = 'MuonVetoSF'))
            group.variations.append(Variation('electronVetoSF', reweight = 'ElectronVetoSF'))

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
            group.variations.append(Variation(gname + 'QCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation(gname + 'EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation(gname + 'EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation(gname + 'EWKgamma', reweight = 'ewkgamma'))

        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        for gname in ['top', 'vvg']:
            config.findGroup(gname).variations.append(Variation('minorQCDscale', reweight = 0.033))


    elif 'diel' in confName:
        mass = 'TMath::Sqrt(2. * electrons.pt_[0] * electrons.pt_[1] * (TMath::CosH(electrons.eta_[0] - electrons.eta_[1]) - TMath::Cos(electrons.phi_[0] - electrons.phi_[1])))'
        dR2_00 = 'TMath::Power(photons.eta_[0] - electrons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[0]), 2.)'
        dR2_01 = 'TMath::Power(photons.eta_[0] - electrons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[1]), 2.)'

        config = PlotConfig('diel', photonData)

        if '0' in confName:
            vgRegion = confName
        else:
            vgRegion = config.name

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && diel.oppSign && diel.mass[0] > 60. && diel.mass[0] < 120.' # met is the recoil (Operator LeptonRecoil)
        config.fullSelection = 'muons.size == 0 && electrons.size == 2'

        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xcc, 0x88, 0x44))
        config.addBkg('top', 't#bar{t}#gamma', samples = ['ttg'], color = ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'dielHfake', color = ROOT.TColor.GetColor(0x55, 0x66, 0xff))
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        noDPhiPhoton = config.baseline.replace(baseSels['photonDPhi0.5'], '1')
        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')

        config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False)
        config.addPlot('recoil', 'Recoil', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMetFullDPhi', 'M_{T#gamma}', mtPhoMet, (12, 0., 1200.), unit = 'GeV', overflow = True, applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, ymax = 5., ymin = 0.0003)
        config.addPlot('phoPtWisc', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', wiscFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True)
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', 't1Met.realPhotonDPhi', (13, 0., 3.25))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('dPhiPhoMetMt100', '#Delta#phi(#gamma, U)', "t1Met.photonDPhi", (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton + ' && ' + mtPhoMet + ' > 100.', overflow = True)
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
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., 3.50), applyBaseline = False, cut = noDPhiJet)
#        config.addPlot('dPhiJetRecoilMin', 'min#Delta#phi(U, j)', 'TMath::Abs(t1Met.minJetDPhi)', (14, 0., 3.50), cut = 'jets.size != 0')
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
#        config.addPlot('partonID', 'PGD ID', 'TMath::Abs(photons.matchedGen[0])', (31, 0., 31.), overflow = True)

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('electronSF', reweight = 0.04)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))
            # group.variations.append(Variation('muonVetoSF', reweight = 'MuonVetoSF'))
            group.variations.append(Variation('electronVetoSF', reweight = 'ElectronVetoSF'))

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
            group.variations.append(Variation(gname + 'QCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation(gname + 'EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation(gname + 'EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation(gname + 'EWKgamma', reweight = 'ewkgamma'))

        for gname in ['top', 'vvg']:
            config.findGroup(gname).variations.append(Variation('minorQCDscale', reweight = 0.033))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))


    elif 'monomu' in confName:

        dPhiPhoMet = 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.realPhi))'
        dPhiJetMetMin = '((jets.size == 0) * 4. + (jets.size == 1) * TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[0] - t1Met.realPhi)) + MinIf$(TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.realPhi)), jets.size > 1 && Iteration$ < 4))'
        dRPhoParton  = 'TMath::Sqrt(TMath::Power(photons.eta_[0] - promptFinalStates.eta_, 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - promptFinalStates.phi_), 2.))'
#        MinIf$() somehow returns 0 when there is only one jet
        mt = 'TMath::Sqrt(2. * t1Met.realMet * muons.pt_[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.realPhi - muons.phi_[0]))))'

        config = PlotConfig('monomu', photonData)

        if '0' in confName:
            vgRegion = confName
        else:
            vgRegion = config.name

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && ' + mt + ' < 160.' # met is the recoil, mt cut to synch with monoel region
        config.fullSelection = 'muons.size == 1 && electrons.size == 0'

#        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'monoelEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99)) # zero contribution
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xcc, 0x88, 0x44))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'monomuHfake', color = ROOT.TColor.GetColor(0x55, 0x66, 0xff))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-p'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))

        noDPhiPhoton = config.baseline.replace(baseSels['photonDPhi0.5'], '1')
        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')

        config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False)
        config.addPlot('recoil', 'Recoil', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('recoilPhi', '#phi_{recoil}', 't1Met.phi', (30, -math.pi, math.pi))
        config.addPlot('realMet', 'E_{T}^{miss}', 't1Met.realMet', [25. * x for x in range(21)], unit = 'GeV', overflow = True)
        config.addPlot('realMetOverMuPt', 'E_{T}^{miss}/p_{T}^{#mu}', 't1Met.realMet / muons.pt_[0]', (20, 0., 10.), overflow = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMetFullDPhi', 'M_{T#gamma}', mtPhoMet, (12, 0., 1200.), unit = 'GeV', overflow = True, applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, ymax = 20., ymin = 0.0003)
        config.addPlot('phoPtWisc', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', wiscFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True)
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('dPhiPhoRealMet', '#Delta#phi(#gamma, E_{T}^{miss})', 't1Met.realPhotonDPhi', (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('dPhiPhoMetMt100', '#Delta#phi(#gamma, U)', "t1Met.photonDPhi", (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton + ' && ' + mtPhoMet + ' > 100.', overflow = True)
        config.addPlot('dRPhoMu', '#DeltaR(#gamma, #mu)', 'TMath::Sqrt(TMath::Power(photons.eta_[0] - muons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[0]), 2.))', (10, 0., 4.))
        config.addPlot('met', 'E_{T}^{miss}', 't1Met.realMet', [50. * x for x in range(6)] + [300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('mt', 'M_{T}', mt, [0. + 20. * x for x in range(9)], unit = 'GeV', overflow = True)
#        config.addPlot('mtNMinusOne', 'M_{T}', mt, [0. + 20. * x for x in range(9)] + [200., 300., 400., 500.], unit = 'GeV', overflow = True, applyBaseline = False, cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170. && t1Met.photonDPhi > 2. && t1Met.realMinJetDPhi > 0.5')
        config.addPlot('muPt', 'p_{T}^{#mu}', 'muons.pt_[0]', [0., 50., 100., 150., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('muEta', '#eta_{#mu}', 'muons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('muPhi', '#phi_{#mu}', 'muons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiMuMet', '#Delta#phi(#mu, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(muons.phi_[0] - t1Met.realPhi))', (13, 0., 3.25))
        config.addPlot('muIso', 'I^{#mu}_{comb.}/p_{T}', '(muons.chIso[0] + TMath::Max(muons.nhIso[0] + muons.phIso[0] - 0.5 * muons.puIso[0], 0.)) / muons.pt_[0]', (20, 0., 0.4), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{leading j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{leading j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{leading j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., 3.50), applyBaseline = False, cut = noDPhiJet)
#        config.addPlot('dPhiJetRecoilMin', 'min#Delta#phi(U, j)', 'TMath::Abs(t1Met.minJetDPhi)', (14, 0., 3.50), cut = 'jets.size != 0')
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
        config.addPlot('phoEtaRecoilPeak', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5), cut = 't1Met.pt > 225 && t1Met.pt < 275')
        config.addPlot('phoPtRecoilPeak', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, cut = 't1Met.pt > 225 && t1Met.pt < 275')
        config.addPlot('muPtOverMetRecoilPeak', 'p_{T}^{#mu}/E_{T}^{miss}', 'muons.pt_[0] / t1Met.realMet', (20, 0., 2.), cut = 't1Met.pt > 225 && t1Met.pt < 275')
        config.addPlot('metPhiRecoilPeak', '#phi(E_{T}^{miss})', 't1Met.realPhi', (20, -math.pi, math.pi), cut = 't1Met.pt > 225 && t1Met.pt < 275')
        config.addPlot('recoilPhiRecoilPeak', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi), cut = 't1Met.pt > 225 && t1Met.pt < 275')
#        config.addPlot('partonID', 'PGD ID', 'TMath::Abs(photons.matchedGen[0])', (31, 0., 31.), overflow = True)

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake' or group.name == 'efake':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('muonSF', reweight = 0.01)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))
            # group.variations.append(Variation('muonVetoSF', reweight = 'MuonVetoSF'))
            group.variations.append(Variation('electronVetoSF', reweight = 'ElectronVetoSF'))

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
            group.variations.append(Variation(gname + 'QCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation(gname + 'EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation(gname + 'EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation(gname + 'EWKgamma', reweight = 'ewkgamma'))

        for gname in ['top', 'vvg']:
            config.findGroup(gname).variations.append(Variation('minorQCDscale', reweight = 0.033))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))


    elif 'monoel' in confName:

        dPhiPhoMet = 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.realPhi))'
        dPhiJetMetMin = '(jets.size == 0) * 4. + (jets.size == 1) * TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[0] - t1Met.realPhi)) + MinIf$(TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.realPhi)), jets.size > 1 && Iteration$ < 4)'
        dRPhoParton  = 'TMath::Sqrt(TMath::Power(photons.eta_[0] - promptFinalStates.eta_, 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - promptFinalStates.phi_), 2.))'
#        MinIf$() somehow returns 0 when there is only one jet
        mt = 'TMath::Sqrt(2. * t1Met.realMet * electrons.pt_[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.realPhi - electrons.phi_[0]))))'

        config = PlotConfig('monoel', photonData)

        if '0' in confName:
            vgRegion = confName
        else:
            vgRegion = config.name

        config.baseline = baseSel.replace('minJetDPhi', 'realMinJetDPhi') + ' && ' + mt + ' < 160. && t1Met.realMet > 50.' # met is the recoil, real MET cut to reject QCD, mt cut to reject QCD
        config.fullSelection = 'muons.size == 0 && electrons.size == 1'

#        config.addBkg('qcd', 'QCD+#gammajets', samples = photonData, region = 'monoelQCD', color = ROOT.TColor.GetColor(0x44, 0xff, 0x99), norm = 25.)
        config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xcc, 0x88, 0x44))
        config.addBkg('gg', '#gamma#gamma', samples = ['gg-40', 'gg-80'], color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'monoelEfake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'monoelHfake', color = ROOT.TColor.GetColor(0x55, 0x66, 0xff))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0xff, 0xbb, 0x55))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-p'], region = vgRegion, color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))

        noDPhiPhoton = config.baseline.replace(baseSels['photonDPhi0.5'], '1')
        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')

        config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False)
        config.addPlot('recoil', 'Recoil', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('recoilScan', 'Recoil', 't1Met.pt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMetFullDPhi', 'M_{T#gamma}', mtPhoMet, (12, 0., 1200.), unit = 'GeV', overflow = True, applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, ymax = 20., ymin = 0.0003)
        config.addPlot('phoPtWisc', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', wiscFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True)
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', 't1Met.realPhotonDPhi', (13, 0., 3.25))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, U)', 't1Met.photonDPhi', (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('dPhiPhoMetMt100', '#Delta#phi(#gamma, U)', "t1Met.photonDPhi", (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton + '&& ' + mt + ' < 160. && ' + mtPhoMet + ' > 100.', overflow = True)
        config.addPlot('met', 'E_{T}^{miss}', 't1Met.realMet', [50. * x for x in range(6)] + [300., 400., 500.], unit = 'GeV', applyBaseline = False, overflow = True)
        config.addPlot('mt', 'M_{T}', mt, [0. + 20. * x for x in range(9)], unit = 'GeV', overflow = True)
        config.addPlot('mtNMinusOne', 'M_{T}', mt, [0. + 20. * x for x in range(9)] + [200., 300., 400., 500.], unit = 'GeV', overflow = True, applyBaseline = False, cut = baseSel.replace('minJetDPhi', 'realMinJetDPhi'))
        config.addPlot('elPt', 'p_{T}^{e}', 'electrons.pt_[0]', [0., 50., 100., 150., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('elEta', '#eta_{e}', 'electrons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('elPhi', '#phi_{e}', 'electrons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiElMet', '#Delta#phi(e, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(electrons.phi_[0] - t1Met.realPhi))', (13, 0., 3.25))
        config.addPlot('elIso', 'I^{e}_{comb.}/p_{T}', '(electrons.chIso[0] + TMath::Max(electrons.nhIso[0] + electrons.phIso[0] - electrons.isoPUOffset[0], 0.)) / electrons.pt_[0]', (20, 0., 0.4), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{leading j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{leading j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{leading j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.realMinJetDPhi', (14, 0., 3.50), applyBaseline = False, cut = noDPhiJet)
#        config.addPlot('dPhiJetRecoilMin', 'min#Delta#phi(U, j)', 'TMath::Abs(t1Met.minJetDPhi)', (14, 0., 3.50), cut = 'jets.size != 0')
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
#        config.addPlot('partonID', 'PGD ID', 'TMath::Abs(photons.matchedGen[0])', (31, 0., 31.), overflow = True)

#        Standard MC systematic variations
        for group in config.bkgGroups:
            if group.name == 'hfake' or group.name == 'efake' or group.name == 'qcd':
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('electronSF', reweight = 0.02)) # apply flat for now
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))
            # group.variations.append(Variation('muonVetoSF', reweight = 'MuonVetoSF'))
            group.variations.append(Variation('electronVetoSF', reweight = 'ElectronVetoSF'))

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
            group.variations.append(Variation(gname + 'QCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation(gname + 'EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation(gname + 'EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation(gname + 'EWKgamma', reweight = 'ewkgamma'))

        for gname in ['top', 'gg', 'vvg']:
            config.findGroup(gname).variations.append(Variation('minorQCDscale', reweight = 0.033))
        # config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))


    elif confName == 'phistack':
        config = PlotConfig('monoph', photonData)

        config.baseline = baseSel
        config.fullSelection = ''

        config.addSigPoint('add-5-2', 'ADD n=5 M_{D}=2TeV', color = 41) # 0.07069/pb
        config.addSigPoint('dmv-1000-150', 'DM V M_{med}=1TeV M_{DM}=150GeV', color = 46) # 0.01437/pb
        config.addSigPoint('dma-500-1', 'DM A M_{med}=500GeV M_{DM}=1GeV', color = 30) # 0.07827/pb

        config.addBkg('minor', '#gamma#gamma, Z#rightarrowll+#gamma', samples = minor, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
#        config.addBkg('halo', 'Beam halo', samples = photonData, region = 'haloMETLoose', color = ROOT.TColor.GetColor(0xff, 0x99, 0x33))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'hfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        config.addPlot('phoPhiHighMet', '#phi^{#gamma}', 'photons.phi_[0]', (20, -math.pi, math.pi), logy = False, applyFullSel = True, blind = 'full', ymax = 8., sensitive = True)


    elif confName == 'lowmt':

        config = PlotConfig('monoph', photonData)

        baseSels['photonDPhi0.5'] = 't1Met.photonDPhi < 0.5'
        config.baseline = ' && '.join(baseSels.values())
        config.fullSelection = 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[0] - t1Met.phi)) < 3.0'

        config.addBkg('minor', '#gamma#gamma, Z#rightarrowll+#gamma', samples = minor, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
#        config.addBkg('qcd', 'QCD', samples = qcd, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'hfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
        config.addBkg('multiboson', 'multiboson', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-o'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [100. + 10. * x for x in range(5)] + [150. + 50. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('metLowSx', 'E_{T}^{miss}', 't1Met.pt', [100. + 10. * x for x in range(5)] + [150. + 50. * x for x in range(6)], cut = 'photons.e4[0] / photons.emax[0] > 0.5', unit = 'GeV', overflow = True)
        config.addPlot('metHighSx', 'E_{T}^{miss}', 't1Met.pt', [100. + 10. * x for x in range(5)] + [150. + 50. * x for x in range(6)], cut = 'photons.e4[0] / photons.emax[0] < 0.5', unit = 'GeV', overflow = True)
        config.addPlot('sumEt', '#SigmaE_{T}', 't1Met.sumETRaw', [1000. + 50. * x for x in range(40)], unit = 'GeV', overflow = True)
        config.addPlot('sumEtHighSx', '#SigmaE_{T}', 't1Met.sumETRaw', [1000. + 50. * x for x in range(40)], cut = 'photons.e4[0] / photons.emax[0] < 0.5', unit = 'GeV', overflow = True)
        config.addPlot('significance', 'E_{T}^{miss} / #SigmaE_{T}', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (20, 0., 20.), unit = '#sqrt{GeV}', overflow = True)
        config.addPlot('significanceHighSx', 'E_{T}^{miss} / #SigmaE_{T}', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (20, 0., 20.), cut = 'photons.e4[0] / photons.emax[0] < 0.5', unit = '#sqrt{GeV}', overflow = True)
        config.addPlot('phoPt', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(9)] + [400. + 50. * x for x in range(5)], unit = 'GeV')
        config.addPlot('phoPtLowSx', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 15. * x for x in range(20)], cut = 'photons.e4[0] / photons.emax[0] > 0.5', unit = 'GeV', logy = False)
        config.addPlot('phoPtHighSx', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 30. * x for x in range(25)], cut = 'photons.e4[0] / photons.emax[0] < 0.5', unit = 'GeV', overflow = True)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 15. * x for x in range(20)], cut = 't1Met.pt > 170.', unit = 'GeV', logy = False)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5), applyFullSel = True)
        config.addPlot('phoEtaLowSx', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5), cut = 'photons.e4[0] / photons.emax[0] > 0.5', applyFullSel = True)
        config.addPlot('phoEta2Jets', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5), cut = 'jets.size == 2', applyFullSel = True)
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (20, -math.pi, math.pi), applyFullSel = True, logy = False)
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', 'TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.phi)', (20, -math.pi, math.pi), cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170. && t1Met.minJetDPhi > 0.5', applyBaseline = False, logy = False)
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', 'TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.phi)', (10, -0.5, 0.5), logy = False)
        config.addPlot('dPhiPhoMetHighSx', '#Delta#phi(#gamma, E_{T}^{miss})', 'TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.phi)', (20, -math.pi, math.pi), cut = 'photons.e4[0] / photons.emax[0] < 0.5', logy = False)
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJet1Met', '#Delta#phi(E_{T}^{miss}, j1)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[0] - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_[0] > 30.')
        config.addPlot('dPhiJet2Met', '#Delta#phi(E_{T}^{miss}, j2)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_[1] - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_[1] > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (30, 0., math.pi), overflow = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', 'photons.mt[0]', (10, 0., 200.), applyFullSel = True, unit = 'GeV', logy = False)
        config.addPlot('mtPhoMetHighSx', 'M_{T#gamma}', 'photons.mt[0]', (30, 0., 300.), cut = 'photons.e4[0] / photons.emax[0] < 0.5', applyFullSel = True, unit = 'GeV')
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi_', (20, -math.pi, math.pi), applyFullSel = True, logy = False)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.), applyFullSel = True)
        config.addPlot('jetPt', 'p_{T}^{j1}', 'jets.pt_[0]', (30, 30., 800.), cut = 'jets.size != 0', applyFullSel = True, unit = 'GeV')
        config.addPlot('jetPtHighSx', 'p_{T}^{j1}', 'jets.pt_[0]', (30, 30., 1600.), cut = 'jets.size != 0 && photons.e4[0] / photons.emax[0] < 0.5', overflow = True, unit = 'GeV')
        config.addPlot('jetPtLowSx', 'p_{T}^{j1}', 'jets.pt_[0]', (30, 30., 1600.), cut = 'jets.size != 0 && photons.e4[0] / photons.emax[0] > 0.5', overflow = True, unit = 'GeV')
        config.addPlot('jetEta', '#eta^{j1}', 'jets.eta_[0]', (30, -5., 5.), cut = 'jets.size != 0', applyFullSel = True)
        config.addPlot('jet2Pt', 'p_{T}^{j2}', 'jets.pt_[1]', (30, 30., 800.), cut = 'jets.size > 1', applyFullSel = True, unit = 'GeV')
        config.addPlot('jet2Eta', '#eta^{j2}', 'jets.eta_[1]', (30, -5., 5.), cut = 'jets.size > 1', applyFullSel = True)
        config.addPlot('r9', 'R_{9}', 'photons.r9', (50, 0.5, 1.), applyFullSel = True)
        config.addPlot('r9HighSx', 'R_{9}', 'photons.r9', (50, 0.5, 1.), cut = 'photons.e4[0] / photons.emax[0] < 0.5', applyFullSel = True)
        config.addPlot('swissCross', '1-S4/S1', '1. - photons.e4[0] / photons.emax[0]', (10, 0., 1.))
        config.addPlot('sipip', '#sigma_{i#phii#phi}', 'photons.sipip[0]', (50, 0., 0.02))
        config.addPlot('sipipLowSx', '#sigma_{i#phii#phi}', 'photons.sipip[0]', (50, 0., 0.02), cut = 'photons.e4[0] / photons.emax[0] > 0.5')

        """
        for plot in list(config.plots):
            if plot.name not in ['dPhiJetMet', 'dPhiJet1Met', 'dPhiJet2Met', 'dPhiJetMetMin']:
                config.plots.append(plot.clone(plot.name + 'JetCleaned', applyFullSel = True))
        #        config.plots.remove(plot)
        """


    elif confName == 'lowdphi':

        config = PlotConfig('monoph', photonData)

        baseSels['minJetDPhi0.5'] = 't1Met.minJetDPhi < 0.5'
        config.baseline = ' && '.join(baseSels.values())
        config.fullSelection = ''

        config.addSig('dmvlo', 'DM V', samples = ['dmvlo-*'])
        config.addSig('dph', 'Dark Photon', samples = ['dph-*'])

        config.addSigPoint('dmvlo-1000-1', 'DMV1000', color = ROOT.kGreen)
        # config.addSigPoint('dph-125', 'DPH125', color = ROOT.kRed)
        # config.addSigPoint('dph-1000', 'DPH1000', color = ROOT.kMagenta)

        config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('halo', 'Beam halo', samples = photonData, region = 'halo', color = ROOT.TColor.GetColor(0xff, 0x99, 0x33), cut = 'metFilters.globalHalo16 && photons.mipEnergy[0] > 4.9', norm = 8.75 * config.effLumi() / 12900.)
        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'hfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('minor', '#gamma#gamma, Z#rightarrowll+#gamma', samples = minor, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-o'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))

        noDPhiPhoton = config.baseline.replace(baseSels['photonDPhi0.5'], '1')
        noDPhiJet = config.baseline.replace(baseSels['minJetDPhi0.5'], '1')

        config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False, sensitive = True)
        config.addPlot('recoil', 'E_{T}^{miss}', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('recoilScan', 'E_{T}^{miss}', 't1Met.pt', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('mtPhoMetFullDPhi', 'M_{T#gamma}', mtPhoMet, (12, 0., 1200.), unit = 'GeV', overflow = True, applyBaseline = False, cut = noDPhiPhoton)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, sensitive = True)
        config.addPlot('phoPtWisc', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', wiscFitPtBinning, unit = 'GeV', overflow = True, applyFullSel = True, sensitive = True)
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(14)], unit = 'GeV', overflow = True, sensitive = True)
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton, overflow = True)
        config.addPlot('dPhiPhoMetMt100', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (13, 0., 3.25), applyBaseline = False, cut = noDPhiPhoton + ' && ' + mtPhoMet + ' > 100.', overflow = True)
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (30, 0., math.pi), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (10, 0., 10.))
        config.addPlot('jetPt', 'p_{T}^{jet}', 'jets.pt_', [0., 100., 200., 300., 400., 600., 1000.], unit = 'GeV', cut = 'jets.pt_ > 30', overflow = True)
        config.addPlot('jetEta', '#eta^{j}', 'jets.eta_', (20, -5., 5.), cut = 'jets.size != 0')
        config.addPlot('jetAbsEta', '#eta^{j}', 'TMath::Abs(jets.eta_)', (10, 0., 5.), cut = 'jets.size != 0')
        config.addPlot('njetsHightPt', 'N_{jet} (p_{T} > 100 GeV)', 'jets.size', (10, 0., 10.), cut = 'jets.pt_ > 100.')
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.), sensitive = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['efake', 'hfake', 'halo']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('pixelVetoSF', reweight = 'pixelVetoSF'))
            group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECUp'), ('t1Met.met', 't1Met.metCorrUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECDown'), ('t1Met.met', 't1Met.metCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.met', 't1Met.metGECUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.met', 't1Met.metGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

            if group.name in ['zg', 'wg']:
                continue

            group.variations.append(Variation('minorQCDscale', reweight = 0.033))

        for gname in ['zg', 'wg']:
            group = config.findGroup(gname)
            group.variations.append(Variation('vgPDF', reweight = 'pdf'))
            group.variations.append(Variation(gname + 'QCDscale', reweight = 'qcdscale'))
            group.variations.append(Variation(gname + 'EWKoverall', reweight = 'ewkstraight'))
            group.variations.append(Variation(gname + 'EWKshape', reweight = 'ewktwisted'))
            group.variations.append(Variation(gname + 'EWKgamma', reweight = 'ewkgamma'))

#        Specific systematic variations
        # TODO use cuts
#        config.findGroup('halo').variations.append(Variation('haloShape', region = ('haloMIPLoose', 'haloLoose')))
        # config.findGroup('halo').variations.append(Variation('haloNorm', reweight = 1.0))
#        config.findGroup('hfake').variations.append(Variation('hfakeTfactor', region = ('hfakeTight', 'hfakeLoose')))
        config.findGroup('hfake').variations.append(Variation('purity', reweight = 'purity'))
        config.findGroup('efake').variations.append(Variation('egfakerate', reweight = 'egfakerate'))
        config.findGroup('gjets').variations.append(Variation('gjetsTF', reweight = 0.5))


    elif confName == 'photonjet':

        config = PlotConfig('monoph', photonData)

        config.baseline = 'photons.scRawPt[0] > 175. && (t1Met.minJetDPhi < 0.5 || t1Met.photonDPhi < 0.5) && t1Met.pt > 100. && TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - jets.phi_[0])) > 3. && jets.size == 1 && jets.pt_[0] > 100.'
        config.fullSelection = '' # 'photons.scRawPt[0] > 350.'

        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
        config.addBkg('halo', 'Beam halo', samples = photonData, region = 'haloMETLoose', color = ROOT.TColor.GetColor(0xff, 0x99, 0x33))
        config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('minor', '#gamma#gamma, Z#rightarrowll+#gamma', samples = minor, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'hfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc)) # , scale = 1.5)

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True)
#        config.addPlot('metWide', 'E_{T}^{miss}', 't1Met.pt', [0. + 10. * x for x in range(10)] + [100. + 20. * x for x in range(5)] + [200. + 50. * x for x in range(9)], unit = 'GeV', overflow = True)
        config.addPlot('metDPhiWeighted', 'E_{T}^{miss}', '(t1Met.pt) * TMath::Sign(1, (t1Met.photonDPhi - 1.570796))', list(reversed([-200. - 50. * x for x in range(9)])) + list(reversed([-120 - 20. * x for x in range(4)])) +[ -100., 0.] +  [100. + 20. * x for x in range(5)] + [200. + 50. * x for x in range(9)], unit = 'GeV', overflow = True)
#        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, (22, 200., 1300.), unit = 'GeV', overflow = True)
        config.addPlot('phoPt', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175. + 25. * x for x in range(5)] + [300., 350., 400., 450.] + [500. + 100. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('jetPt', 'E_{T}^{j}', 'jets.pt_[0]', [175. + 25. * x for x in range(5)] + [300., 350., 400., 450.] + [500. + 100. * x for x in range(6)], unit = 'GeV', overflow = True)
#        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi))
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (30, 0., math.pi), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (10, 0., 10.))
        config.addPlot('jetEta', '#eta^{j}', 'jets.eta_', (20, -5., 5.), cut = 'jets.size != 0')
        config.addPlot('jetAbsEta', '#eta^{j}', 'TMath::Abs(jets.eta_)', (10, 0., 5.), cut = 'jets.size != 0')
#        config.addPlot('njetsHightPt', 'N_{jet} (p_{T} > 100 GeV)', 'jets.size', (10, 0., 10.), cut = 'jets.pt_ > 100.')
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.))
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

        for plot in list(config.plots):
            if plot.name not in ['phoPt', 'phoPtHighMet']:
                config.plots.append(plot.clone(plot.name + 'HighPhoPt', applyFullSel = True))


    elif confName == 'gjets':

        config = PlotConfig('emjet', photonData)

        baseSels = {}

        baseSels['met170'] = 't1Met.pt < 60.'
        baseSels['fiducial'] = 'photons.isEB'
        baseSels['hovere'] = 'photons.hOverE[0] < 0.26'
        baseSels['nhiso'] = 'photons.nhIsoX[0][2] < 2.792'
        baseSels['phiso'] = 'photons.phIsoX[0][2] < 2.176'
        baseSels['chiso'] = 'photons.chIsoX[0][2] < 1.146'

        config.baseline = ' && '.join(baseSels.values())
        config.fullSelection = '' # 'photons.pixelVeto[0]'

        # config.addBkg('fakes', samples = photonData, region = 'emjet', cut = 'photons.chIsoX[0] > 5.0 && photons.chIsoX[0][2] < 7.5', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
#        config.addBkg('top', 't#bar{t}', samples = ['tt'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
#        config.addBkg('wjets', 'W(e#nu) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))

        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (40, 0., 0.020))
        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [100. + 10. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, (22, 200., 1300.), unit = 'GeV', overflow = True)
        config.addPlot('phoPt', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175.] + [180. + 10. * x for x in range(12)] + [300., 350., 400., 450.] + [500. + 100. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi))
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (30, 0., math.pi), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (10, 0., 10.))
        config.addPlot('jetEta', '#eta^{j}', 'jets.eta_', (20, -5., 5.), cut = 'jets.size != 0')
        config.addPlot('jetAbsEta', '#eta^{j}', 'TMath::Abs(jets.eta_)', (10, 0., 5.), cut = 'jets.size != 0')
        config.addPlot('njetsHightPt', 'N_{jet} (p_{T} > 100 GeV)', 'jets.size', (10, 0., 10.), cut = 'jets.pt_ > 100.')
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.))
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

        for plot in list(config.plots):
            config.plots.append(plot.clone(plot.name + 'PixelVeto', applyFullSel = True))

        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['fakes']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            # group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            # group.variations.append(Variation('pixelVetoSF', reweight = 0.01))
            # group.variations.append(Variation('leptonVetoSF', reweight = 0.02))

            if group.name in ['vvg']:
                continue

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECUp'), ('t1Met.met', 't1Met.metCorrUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiJECDown'), ('t1Met.met', 't1Met.metCorrDown')]
            group.variations.append(Variation('jec', replacements = (replUp, replDown)))

            replUp = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECUp'), ('photons.scRawPt', 'photons.ptVarUp'), ('t1Met.met', 't1Met.metGECUp')]
            replDown = [('t1Met.minJetDPhi', 't1Met.minJetDPhiGECDown'), ('photons.scRawPt', 'photons.ptVarDown'), ('t1Met.met', 't1Met.metGECDown')]
            group.variations.append(Variation('gec', replacements = (replUp, replDown)))

            if group.name in ['zg', 'wg']:
                continue

            group.variations.append(Variation('minorQCDscale', reweight = 0.033))


    elif confName == 'tp2m':

        config = PlotConfig('tp2m', muonData)

        config.baseline = ''
        config.fullSelection = 't1Met.pt > 75.'

#        config.addBkg('wjets', 'W+jets', samples = wlnu, color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
#        config.addBkg('diboson', 'Diboson', samples =  ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('tt', 'Top', samples = ['tt'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('zjets', 'Z+jets', samples = dyn, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

#        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [25 * x for x in range(2, 4)] + [100 + 50 * x for x in range(0, 8)], unit = 'GeV', overflow = True)
#        config.addPlot('dPhi', '#Delta#phi(Z, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_))', (15, 0., math.pi), applyBaseline = False, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi)) < 0.5 && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5')
#        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(t1Met.phi - jets.phi_))', (15, 0., math.pi), applyBaseline = False, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi)) < 0.5 && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt_[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5')
#        config.addPlot('dPhiZMet', '#Delta#phi(Z, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi))', (15, 0., math.pi), applyBaseline = False, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_[0])) > 3. && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt_[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5')
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_[0]', (20, 0., 1000.), unit = 'GeV')
#        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_[0]', (10, -5., 5.))
#        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('tagPt', 'p_{T}^{tag}', 'tag.pt_[0]', (20, 0., 200.), unit = 'GeV')
#        config.addPlot('tagEta', '#eta_{tag}', 'tag.eta_[0]', (10, -2.5, 2.5))
#        config.addPlot('tagPhi', '#phi_{tag}', 'tag.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('probePt', 'p_{T}^{probe}', 'probe.pt_[0]', (10, 0., 100.), unit = 'GeV')
#        config.addPlot('probeEta', '#eta_{probe}', 'probe.eta_[0]', (10, -2.5, 2.5))
#        config.addPlot('probePhi', '#phi_{probe}', 'probe.phi_[0]', (10, -math.pi, math.pi))
#        config.addPlot('metPhi', '#phi_{E_{T}^{miss}}', 't1Met.phi', (10, -math.pi, math.pi))
#        config.addPlot('zPt', 'p_{T}^{Z}', 'z.pt[0]', (20, 0., 1000.), unit = 'GeV')
#        config.addPlot('zEta', '#eta_{Z}', 'z.eta[0]', (10, -5., 5.))
#        config.addPlot('zPhi', '#phi_{Z}', 'z.phi[0]', (10, -math.pi, math.pi))
#        config.addPlot('zMass', 'm_{Z}', 'z.mass[0]', (10, 81., 101.), unit = 'GeV')

#        for plot in list(config.plots):
#            if plot.name not in ['met']:
#                config.plots.append(plot.clone(plot.name + 'HighMet', applyFullSel = True))


    elif confName == 'zeeJets':

        config = PlotConfig('zeeJets', electronData)

        config.baseline = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_[0])) > 3. && TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi)) < 0.5 && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt_[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5'
        config.fullSelection = 't1Met.pt > 75.'

        config.addBkg('wjets', 'W+jets', samples = wlnun, color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('diboson', 'Diboson', samples =  ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('tt', 'Top', samples = ['tt'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('zjets', 'Z+jets', samples = ['dy-50'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [25 * x for x in range(2, 4)] + [100 + 50 * x for x in range(0, 8)], unit = 'GeV', overflow = True)
        config.addPlot('dPhi', '#Delta#phi(Z, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_))', (15, 0., math.pi), applyBaseline = False, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi)) < 0.5 && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt_[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5')
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(t1Met.phi - jets.phi_))', (15, 0., math.pi), applyBaseline = False, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi)) < 0.5 && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt_[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5')
        config.addPlot('dPhiZMet', '#Delta#phi(Z, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi))', (15, 0., math.pi), applyBaseline = False, cut = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_[0])) > 3. && z.mass > 81. && z.mass < 101. && z.oppSign == 1 && jets.size == 1 && jets.pt_[0] > 100. && t1Met.pt > 50. && t1Met.minJetDPhi > 0.5')
        config.addPlot('jetPt', 'p_{T}^{j}', 'jets.pt_[0]', (20, 0., 1000.), unit = 'GeV')
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('tagPt', 'p_{T}^{tag}', 'tag.pt_[0]', (20, 0., 200.), unit = 'GeV')
        config.addPlot('tagEta', '#eta_{tag}', 'tag.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('tagPhi', '#phi_{tag}', 'tag.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('probePt', 'p_{T}^{probe}', 'probe.pt_[0]', (10, 0., 100.), unit = 'GeV')
        config.addPlot('probeEta', '#eta_{probe}', 'probe.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('probePhi', '#phi_{probe}', 'probe.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('metPhi', '#phi_{E_{T}^{miss}}', 't1Met.phi', (10, -math.pi, math.pi))
        config.addPlot('zPt', 'p_{T}^{Z}', 'z.pt[0]', (20, 0., 1000.), unit = 'GeV')
        config.addPlot('zEta', '#eta_{Z}', 'z.eta[0]', (10, -5., 5.))
        config.addPlot('zPhi', '#phi_{Z}', 'z.phi[0]', (10, -math.pi, math.pi))
        config.addPlot('zMass', 'm_{Z}', 'z.mass[0]', (10, 81., 101.), unit = 'GeV')

        for plot in list(config.plots):
            if plot.name not in ['met']:
                config.plots.append(plot.clone(plot.name + 'HighMet', applyFullSel = True))

    elif confName == 'invChIsoMax':

        config = PlotConfig('monoph', photonDataICHEP)

        config.baseline = 'photons.scRawPt[0] > 175. && photons.chIsoMax > 0.441 && t1Met.minJetDPhi > 0.5 && t1Met.photonDPhi > 2. && t1Met.pt > 170.'
        config.fullSelection = 't1Met.pt > 170.'

        config.addBkg('minor', '#gamma#gamma, Z#rightarrowll+#gamma', samples = minor, color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
        config.addBkg('vvg', 'VV#gamma', samples = ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
        config.addBkg('spike', 'Spikes', samples = photonDataICHEP, region = 'offtime', color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff), norm = 30.5 * 12.9 / 36.4)
#        config.addBkg('halo', 'Beam halo', samples = photonData, region = 'halo', color = ROOT.TColor.GetColor(0xff, 0x99, 0x33), norm = 15.) # norm set here
        config.addBkg('hfake', 'Hadronic fakes', samples = photonDataICHEP, region = 'hfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('efake', 'Electron fakes', samples = photonDataICHEP, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('wg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130'], color = ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('zg', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [170., 190., 250., 400., 700., 1000.], unit = 'GeV', overflow = True)
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi))
        config.addPlot('phoPt', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175.] + [180. + 10. * x for x in range(12)] + [300., 350., 400., 450.] + [500. + 100. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (20, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (30, 0., math.pi), applyBaseline = False, cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170. && t1Met.minJetDPhi > 0.5', overflow = True)
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (30, 0., math.pi), applyBaseline = False, cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170 && t1Met.photonDPhi > 2.', overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.), overflow = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
        config.addPlot('chIso', 'CH Iso', 'photons.chIsoS16[0]', (10, 0., 1.0), overflow = True)
        config.addPlot('chIsoMax', 'Max CH Iso', 'photons.chIsoMax[0]', (20, 0., 10.), overflow = True)
        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (40, 0., 0.020))
        config.addPlot('sipip', '#sigma_{i#phi i#phi}', 'photons.sipip[0]', (40, 0., 0.020))
        config.addPlot('r9', 'r9', 'photons.r9[0]', (25, 0.7, 1.2))
        config.addPlot('swissCross', '1-S4/S1', '1. - photons.e4[0] / photons.emax[0]', (50, 0., 1.))
        config.addPlot('e2e9', 'E2/E9', '(photons.emax[0] + photons.e2nd[0]) / photons.e33[0]', (25, 0.7, 1.2))

        for plot in list(config.plots):
            if plot.name not in ['met', 'metWide']:
                config.plots.append(plot.clone(plot.name + 'HighMet', applyFullSel = True))
                config.plots.remove(plot)

        config.getPlot('phoPtHighMet').binning = combinedFitPtBinning


    elif confName == 'diph':

        config = PlotConfig('monoph', photonData)

        config.baseline = 'photons.size == 2 && photons.scRawPt[0] > 175. && photons.scRawPt[1] > 170. && TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - photons.phi_[1])) > 0.5 && photons.scRawPt[0] / photons.scRawPt[1] < 1.4'
        config.fullSelection = ''

        #config.addBkg('zg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o', 'zllg-300-o'], color = ROOT.TColor.GetColor(0x22, 0x22, 0x22))
        # config.addBkg('wjets', 'W(#mu,#tau) + jets', samples = wlnun, color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))
        # config.addBkg('top', 't#bar{t}#gamma/t#gamma', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
        config.addBkg('hfake', 'Hadronic fakes', samples = photonData, region = 'hfake', color = ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))
        config.addBkg('gjets', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))
        config.addBkg('efake', 'Electron fakes', samples = photonData, region = 'efake', color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
        config.addBkg('gg', '#gamma#gamma', samples = ['gg-40', 'gg-80'], color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff))

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [10. * x for x in range(6)] + [60. + 20. * x for x in range(4)], unit = 'GeV', overflow = True)
        config.addPlot('phoPt', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175.] + [180. + 10. * x for x in range(12)] + [300., 350., 400., 450.] + [500. + 100. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (10, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('recoil', 'Recoil', 'photons.scRawPt[1]', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('recoilEta', '#eta^{recoil}', 'photons.eta_[1]', (10, -1.5, 1.5))
        config.addPlot('recoilPhi', '#phi^{recoil}', 'photons.phi_[1]', (10, -math.pi, math.pi))
        config.addPlot('dPhiPhoRecoil', '#Delta#phi(#gamma, U)', 'TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - photons.phi_[1]))', (13, 0., 3.25), applyBaseline = False, cut = 'photons.size == 2 && photons.scRawPt[0] > 175. && photons.loose[1] && photons.scRawPt[1] > 170. && t1Met.minJetDPhi > 0.5 && photons.scRawPt[0] / photons.scRawPt[1] < 1.4')
        config.addPlot('sieie', '#sigma_{i#eta i#eta}', 'photons.sieie[0]', (10, 0., 0.020))
        config.addPlot('sipip', '#sigma_{i#phi i#phi}', 'photons.sipip[0]', (10, 0., 0.020))
        config.addPlot('r9', 'r9', 'photons.r9[0]', (25, 0.7, 1.2))
        config.addPlot('njets', 'N_{jet}', 'jets.size', (6, 0., 6.))
        config.addPlot('jetPt', 'p_{T}^{leading j}', 'jets.pt_[0]', [0., 50., 100.]  + [200. + 200. * x for x in range(5)], unit = 'GeV', overflow = True)
        config.addPlot('jetEta', '#eta_{leading j}', 'jets.eta_[0]', (10, -5., 5.))
        config.addPlot('jetPhi', '#phi_{leading j}', 'jets.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (14, 0., 3.50), applyBaseline = False, cut = 'photons.size == 2 && photons.scRawPt[0] > 175. && photons.loose[1] && photons.scRawPt[1] > 170. && TMath::Abs(TVector2::Phi_mpi_pi(photons.phi_[0] - photons.phi_[1])) > 0.5 && photons.scRawPt[0] / photons.scRawPt[0]', overflow = True)
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))


#        Standard MC systematic variations
        for group in config.bkgGroups + config.sigGroups:
            if group.name in ['efake', 'hfake']:
                continue

            group.variations.append(Variation('lumi', reweight = 0.027))

            group.variations.append(Variation('photonSF', reweight = 'photonSF'))
            group.variations.append(Variation('customIDSF', reweight = 0.055))
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
        config.findGroup('efake').variations.append(Variation('egFakerate', reweight = 0.079))


    elif confName == 'nosel':

        config = PlotConfig('signalRaw', photonData)

        config.baseline = '' # 'photons.scRawPt[0] > 130. && t1Met.pt > 100.'
        config.fullSelection = 'photons.scRawPt[0] > 175. && t1Met.pt > 170.'

        dR2_pho0mu0 = 'TMath::Power(photons.eta_[0] - muons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[0]), 2.)'
        dR2_pho0mu1 = 'TMath::Power(photons.eta_[0] - muons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[1]), 2.)'
        dR2_pho0el0 = 'TMath::Power(photons.eta_[0] - electrons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[0]), 2.)'
        dR2_pho0el1 = 'TMath::Power(photons.eta_[0] - electrons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[1]), 2.)'

        config.addSig('dmv', 'DM V', samples = ['dmv-500-1', 'dmv-1000-1', 'dmv-2000-1'], norm = 1.)
        config.addSig('dma', 'DM A', samples = ['dma-500-1', 'dma-1000-1', 'dma-2000-1'], norm = 1.)
        config.addSig('dph', 'Dark Photon', samples = ['dph-*'], norm = 1.)
        config.addSig('hbb', 'Dark Photon', samples = ['hbb-*'], norm = 1.)
        config.addSig('add', 'ADD', samples = ['add-3-*'], norm = 1.)
#        config.addSig('dmewk', 'DM EWK', samples = ['dmewk-*'])
        config.addSig('dmvlo', 'DM V', samples = ['dmvlo-500-1', 'dmvlo-1000-1', 'dmvlo-2000-1'], norm = 1.)
        config.addSig('dmalo', 'DM A', samples = ['dmalo-1000-1', 'dmvlo-2000-1'], norm = 1.)

        config.addSigPoint('add-3-8', '#scale[0.7]{ADD +8d M_{D} = 3 TeV}', color = ROOT.kRed)
        config.addSigPoint('dmvlo-1000-1', 'DMV1000', color = ROOT.kGreen)
        config.addSigPoint('dmalo-1000-1', 'DMA1000', color = ROOT.kBlue)
        config.addSigPoint('dph-125', 'DPH125', color = ROOT.kCyan)
        config.addSigPoint('dph-1000', 'DPH1000', color = ROOT.kMagenta)
        """
        config.addSigPoint('add-3-3', '#scale[0.7]{ADD +3d M_{D} = 3 TeV}', color = ROOT.kRed)
        config.addSigPoint('add-3-4', '#scale[0.7]{ADD +4d M_{D} = 3 TeV}', color = ROOT.kBlue)
        config.addSigPoint('add-3-5', '#scale[0.7]{ADD +5d M_{D} = 3 TeV}', color = ROOT.kGreen)
        config.addSigPoint('add-3-6', '#scale[0.7]{ADD +6d M_{D} = 3 TeV}', color = ROOT.kMagenta)
        config.addSigPoint('add-3-8', '#scale[0.7]{ADD +8d M_{D} = 3 TeV}', color = ROOT.kCyan)

        config.addSigPoint('dph-125', 'DPH125', color = ROOT.kRed)
    #    config.addSigPoint('dph-nlo-125', 'DPH125-NLO', color = ROOT.kBlue)
        config.addSigPoint('dph-200', 'DPH200', color = ROOT.kBlue)
        config.addSigPoint('dph-300', 'DPH300', color = ROOT.kGreen)
        config.addSigPoint('dph-400', 'DPH400', color = ROOT.kMagenta)
        config.addSigPoint('dph-500', 'DPH500', color = ROOT.kCyan)
        config.addSigPoint('dph-600', 'DPH600', color = ROOT.kRed+1)
        config.addSigPoint('dph-700', 'DPH700', color = ROOT.kBlue+1)
        config.addSigPoint('dph-800', 'DPH800', color = ROOT.kGreen+1)
        config.addSigPoint('dph-900', 'DPH900', color = ROOT.kMagenta+1)
        config.addSigPoint('dph-1000', 'DPH1000', color = ROOT.kCyan+1)
        """

#        config.addBkg('wnlg', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130-o'], color = ROOT.kWhite) # ROOT.TColor.GetColor(0x99, 0xee, 0xff))
#        config.addBkg('wnlg-nlo', 'W#rightarrowl#nu+#gamma', samples = ['wnlg-130'], color = ROOT.kWhite) # ROOT.TColor.GetColor(0x99, 0xee, 0xff))
        config.addBkg('znng', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130-o'], color = ROOT.kWhite, norm = 1.) # ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
#        config.addBkg('znng-nlo', 'Z#rightarrow#nu#nu+#gamma', samples = ['znng-130'], color = ROOT.kWhite) # ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
#        config.addBkg('zllg', 'Z#rightarrowll+#gamma', samples = ['zllg-130-o'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))
#        config.addBkg('zllg-nlo', 'Z#rightarrowll+#gamma', samples = ['zllg-130'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

#        config.addPlot('fitTemplate', 'E_{T}^{#gamma}', fitTemplateExpression, fitTemplateBinning, unit = 'GeV', applyFullSel = True, overflow = False)
#        config.addPlot('metHigh', 'E_{T}^{miss}', 't1Met.pt', combinedFitPtBinning, unit = 'GeV', overflow = True) # , cut = 'photons.scRawPt[0] > 175.')
        config.addPlot('metScan', 'E_{T}^{miss}', 't1Met.pt', (80, 0., 2000.), unit = 'GeV', overflow = True) # , cut = 'photons.scRawPt[0] > 175.')
#        config.addPlot('mtPhoMet', 'M_{T#gamma}', mtPhoMet, mtPhoMetBinning, unit = 'GeV', overflow = True, ymax = 2500)
        config.addPlot('mtPhoMetScan', 'M_{T#gamma}', mtPhoMet, (40, 0., 2000.), unit = 'GeV', overflow = True, ymax = 2500)
        config.addPlot('phoPtScan', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', (80, 0., 2000.), unit = 'GeV') # , overflow = True)
#        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (40, -1.5, 1.5))
        config.addPlot('phoPhi', '#phi^{#gamma}', 'photons.phi_[0]', (40, -math.pi, math.pi))
        config.addPlot('dPhiPhoMet', '#Delta#phi(#gamma, E_{T}^{miss})', "t1Met.photonDPhi", (26, 0., 3.25)) # , applyBaseline = False, cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170. && t1Met.minJetDPhi > 0.5', overflow = True)
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (40, -math.pi, math.pi))
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (26, 0., 3.25), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (28, 0., 3.50)) # , applyBaseline = False, cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170 && t1Met.photonDPhi > 0.5', overflow = True)
        config.addPlot('dPhiPhoJetMin', 'min#Delta#phi(#gamma, j)', 'photons.minJetDPhi[0]', (28, 0., 3.50)) # , applyBaseline = False, cut = 'photons.scRawPt[0] > 175. && t1Met.pt > 170. && t1Met.minJetDPhi > 0.5 && t1Met.photonDPhi > 0.5', overflow = True)
        config.addPlot('njets', 'N_{jet}', 'jets.size', (10, 0., 10.))
#        config.addPlot('jetPt', 'p_{T}^{jet}', 'jets.pt_', [0., 100., 200., 300., 400., 600., 1000.], unit = 'GeV', cut = 'jets.pt_ > 30', overflow = True)
        config.addPlot('jetPtScan', 'p_{T}^{jet}', 'jets.pt_', (80, 0., 2000.), unit = 'GeV', cut = 'jets.pt_ > 30', overflow = True)
        config.addPlot('jetEta', '#eta_{j}', 'jets.eta_', (40, -5., 5.))
        config.addPlot('jetPhi', '#phi_{j}', 'jets.phi_', (40, -math.pi, math.pi))
        config.addPlot('genHiggsPt', 'Gen #p_{T}^{H}', 'partons.pt_', (40, 0., 2000.), cut = 'partons.pdgid == 25.')
        """
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))
        config.addPlot('mu0Pt', 'p_{T}^{leading #mu}', 'muons.pt_[0]', [0. + 10 * x for x in range(10)] + [100., 125., 150., 175., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('mu0Eta', '#eta_{leading #mu}', 'muons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('mu0Phi', '#phi_{leading #mu}', 'muons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('mu1Pt', 'p_{T}^{trailing #mu}', 'muons.pt_[1]', [0. + 10 * x for x in range(5)] + [50., 75., 100., 150., 200.], unit = 'GeV', overflow = True)
        config.addPlot('mu1Eta', '#eta_{trailing #mu}', 'muons.eta_[1]', (10, -2.5, 2.5))
        config.addPlot('mu1Phi', '#phi_{trailing #mu}', 'muons.phi_[1]', (10, -math.pi, math.pi))
        config.addPlot('el0Pt', 'p_{T}^{leading e}', 'electrons.pt_[0]', [0. + 10 * x for x in range(10)] + [100., 125., 150., 175., 200., 250., 300., 400., 500.], unit = 'GeV', overflow = True)
        config.addPlot('el0Eta', '#eta_{leading e}', 'electrons.eta_[0]', (10, -2.5, 2.5))
        config.addPlot('el0Phi', '#phi_{leading e}', 'electrons.phi_[0]', (10, -math.pi, math.pi))
        config.addPlot('el1Pt', 'p_{T}^{trailing e}', 'electrons.pt_[1]', [0. + 10 * x for x in range(5)] + [50., 75., 100., 150., 200.], unit = 'GeV', overflow = True)
        config.addPlot('el1Eta', '#eta_{trailing e}', 'electrons.eta_[1]', (10, -2.5, 2.5))
        config.addPlot('el1Phi', '#phi_{trailing e}', 'electrons.phi_[1]', (10, -math.pi, math.pi))
        config.addPlot('dimuMass', 'M_{#mu#mu}', 'dimu.mass[0]', (36, 0., 180.), unit = 'GeV', overflow = True)
        config.addPlot('dimuPt', 'p_{T}^{Z}', 'dimu.pt[0]', (80, 0., 2000.), unit = 'GeV')
        config.addPlot('dimuEta', '#eta_{Z}', 'dimu.eta[0]', (10, -5., 5.))
        config.addPlot('dimuPhi', '#phi_{Z}', 'dimu.phi[0]', (10, -math.pi, math.pi))
        config.addPlot('dielMass', 'M_{ee}', 'diel.mass[0]', (36, 0., 180.), unit = 'GeV', overflow = True)
        config.addPlot('dielPt', 'p_{T}^{Z}', 'diel.pt[0]',  (80, 0., 2000.), unit = 'GeV')
        config.addPlot('dielEta', '#eta_{Z}', 'diel.eta[0]', (10, -5., 5.))
        config.addPlot('dielPhi', '#phi_{Z}', 'diel.phi[0]', (10, -math.pi, math.pi))
        config.addPlot('dRPhoMu0', '#DeltaR(#gamma, #mu_{leading})', 'TMath::Sqrt(TMath::Power(photons.eta_[0] - muons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[0]), 2.))', (10, 0., 4.))
        config.addPlot('dRPhoMu1', '#DeltaR(#gamma, #mu_{trailing})', 'TMath::Sqrt(TMath::Power(photons.eta_[0] - muons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - muons.phi_[1]), 2.))', (10, 0., 4.))
        config.addPlot('dRPhoMuMin', '#DeltaR(#gamma, #mu)_{min}', 'TMath::Sqrt(TMath::Min(%s, %s))' % (dR2_pho0mu0, dR2_pho0mu1), (10, 0., 4.))
        config.addPlot('dRPhoEl0', '#DeltaR(#gamma, e_{leading})', 'TMath::Sqrt(TMath::Power(photons.eta_[0] - electrons.eta_[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[0]), 2.))', (10, 0., 4.))
        config.addPlot('dRPhoEl1', '#DeltaR(#gamma, e_{trailing})', 'TMath::Sqrt(TMath::Power(photons.eta_[0] - electrons.eta_[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi_[0] - electrons.phi_[1]), 2.))', (10, 0., 4.))
        config.addPlot('dRPhoElMin', '#DeltaR(#gamma, e)_{min}', 'TMath::Sqrt(TMath::Min(%s, %s))' % (dR2_pho0el0, dR2_pho0el1), (10, 0., 4.))
        """

        for plot in list(config.plots):
            plot.sensitive = True
    #        if plot.name not in ['metScan', 'metHigh']:
            config.plots.append(plot.clone(plot.name + 'HighMet', applyFullSel = True))

#        config.getPlot('phoPtHighMet').binning = combinedFitPtBinning

        config.sensitiveVars = [v.name for v in config.plots]

        for plot in list(config.plots): # need to clone the list first!
            plot.logy = True
            plot.blind = 'full'
            plot.ymax = 1.

            if 'Phi' in plot.name or 'Eta' in plot.name or 'njets' in plot.name:
                continue

            plot.ymin = 1.0E-06

    elif confName == 'emjet':

        config = PlotConfig('emjet', photonData)

#        config.baseline = 't1Met.pt < 60. && jets.pt_[0] > 100. && photons.hOverE[0] < 0.0102 && photons.nhIso[0] + (0.0148 - 0.0112) * photons.scRawPt[0] + (0.000017 - 0.000028) * photons.scRawPt[0] * photons.scRawPt[0] < 7.005 && photons.phIso[0] + (0.0047 - 0.0043) * photons.scRawPt[0] < 3.271 && photons.chIso[0] < 1.163 && photons.pixelVeto[0]'
        config.baseline = 't1Met.pt < 60. && jets.pt_[0] > 100. && photons.medium[0] && photons.pixelVeto[0]'
        config.fullSelection = ''

        config.addBkg('gj', '#gamma + jets', samples = gj, color = ROOT.kBlue, cut = 'photons.matchedGenId[0] == -22')
        config.addBkg('gj04', '#gamma + jets', samples = gj04, color = ROOT.TColor.GetColor(0xff, 0xaa, 0xcc), cut = 'photons.matchedGenId[0] == -22')
#        config.addBkg('gg', '#gamma#gamma', samples = ['gg-80'], color = ROOT.TColor.GetColor(0xbb, 0x66, 0xff), cut = 'photons.matchedGenId[0] == -22')
#        config.addBkg('top', '#gamma + t(t)', samples = ['ttg', 'tg'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff), cut = 'photons.matchedGenId[0] == -22')

        config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [10. * x for x in range(16)], unit = 'GeV', overflow = True)
        config.addPlot('phoPt', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', [175.] + [180. + 10. * x for x in range(12)] + [300., 350., 400., 450.] + [500. + 100. * x for x in range(6)], unit = 'GeV', overflow = True)
        config.addPlot('phoPtHighMet', 'E_{T}^{#gamma}', 'photons.scRawPt[0]', combinedFitPtBinning, unit = 'GeV', overflow = True)
        config.addPlot('phoEta', '#eta^{#gamma}', 'photons.eta_[0]', (20, -1.5, 1.5))
        config.addPlot('chIso', 'I_{CH}', 'TMath::Max(0., photons.chIso[0])', (40, 0., 2.), unit = 'GeV')
        config.addPlot('nhIso', 'I_{NH}', 'TMath::Max(0., photons.nhIso[0])', (40, 0., 10.), unit = 'GeV')
        config.addPlot('phIso', 'I_{Ph}', 'TMath::Max(0., photons.phIso[0])', (40, 0., 5.), unit = 'GeV')
        config.addPlot('sieie', '#sigma_{i#etai#eta}', 'photons.sieie[0]', (44, 0.004, 0.015))
        config.addPlot('etaWidth', 'etaWidth', 'photons.etaWidth[0]', (30, 0.005, .020))
        config.addPlot('phiWidth', 'phiWidth', 'photons.phiWidth[0]', (18, 0., 0.05))
        config.addPlot('metPhi', '#phi(E_{T}^{miss})', 't1Met.phi', (20, -math.pi, math.pi))
        config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, j)', 'TMath::Abs(TVector2::Phi_mpi_pi(jets.phi_ - t1Met.phi))', (30, 0., math.pi), cut = 'jets.pt_ > 30.')
        config.addPlot('dPhiJetMetMin', 'min#Delta#phi(E_{T}^{miss}, j)', 't1Met.minJetDPhi', (30, 0., math.pi), overflow = True)
        config.addPlot('njets', 'N_{jet}', 'Sum$(jets.pt_ > 30.)', (10, 0., 10.))
        config.addPlot('detajj', '#Delta#eta^{jj}', 'dijet.dEtajj[0]', (40, 0., 10.))
        config.addPlot('detajjHighMet', '#Delta#eta^{jj}', 'dijet.dEtajj[0]', (40, 0., 10.), applyBaseline = False, cut = 't1Met.pt > 100. && jets.pt_[0] > 100. && photons.medium[0] && photons.pixelVeto[0]')
        config.addPlot('detajjNonMetAligned', '#Delta#eta^{jj}', 'dijet.dEtajj[0]', (40, 0., 10.), cut = 't1Met.minJetDPhi > 1.')
        config.addPlot('mjj', 'm^{jj}', 'dijet.mjj[0]', (40, 0., 5000.), unit = 'GeV', sensitive = True)
        config.addPlot('jet1Pt', 'p_T^{j1}', 'jets.pt_[0]', (40, 0., 1000.), cut = 'jets.size != 0')
        config.addPlot('jet2Pt', 'p_T^{j2}', 'jets.pt_[1]', (40, 0., 1000.), cut = 'jets.size > 1')
        config.addPlot('jetEta', '#eta^{j}', 'jets.eta_', (20, -5., 5.), cut = 'jets.size != 0')
        config.addPlot('jetAbsEta', '#eta^{j}', 'TMath::Abs(jets.eta_)', (10, 0., 5.), cut = 'jets.size != 0')
        config.addPlot('njetsHightPt', 'N_{jet} (p_{T} > 100 GeV)', 'jets.size', (10, 0., 10.), cut = 'jets.pt_ > 100.')
        config.addPlot('metSignif', 'E_{T}^{miss} Significance', 't1Met.pt / TMath::Sqrt(t1Met.sumETRaw)', (15, 0., 30.))
        config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 40.))

    else:
        raise RuntimeError('Unknown configuration ' + confName)

    return config
