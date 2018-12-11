import os
import math
import importlib

import main.plotutil as pu
import configs.common.plotconfig_2017 as common

import ROOT

config = pu.plotConfig

if pu.confName == 'tp2m':
    config.name = 'tp2m'
    config.addObs(common.muonData)

    config.cut['highMet'] = 't1Met.pt > 75.'

    config.addBkg('wjets', 'W+jets', samples = wlnu, color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
    config.addBkg('diboson', 'Diboson', samples =  ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
    config.addBkg('tt', 'Top', samples = ['tt'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
    config.addBkg('zjets', 'Z+jets', samples = dyn, color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

    config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [25 * x for x in range(2, 4)] + [100 + 50 * x for x in range(0, 8)], unit = 'GeV', overflow = True)
    config.addPlot('dPhiZJet', '#Delta#phi(Z, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_))', (15, 0., math.pi))
    config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(t1Met.phi - jets.phi_))', (15, 0., math.pi))
    config.addPlot('dPhiZMet', '#Delta#phi(Z, E_{T}^{miss})', 'dPhiZMet', (15, 0., math.pi))
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
            config.plots.append(plot.clone(plot.name + 'HighMet', cutName = 'highMet'))

elif pu.confName == 'zeeJets':
    config.name = 'zeeJets'
    config.addObs(common.electronData)

    config.aliases['ZPeak'] = 'z.mass > 81. && z.mass < 101. && z.oppSign == 1'
    config.aliases['ZJBacktoback'] = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_[0])) > 3.'
    config.aliases['ZMetAligned'] = 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi)) < 0.5'
    config.aliases['oneHardJet'] = 'jets.size == 1 && jets.pt_[0] > 100.'
    config.aliases['moderateMet'] = 't1Met.pt > 50. && t1Met.minJetDPhi > 0.5'

    config.baseline = 'ZJBacktoback && ZMetAligned && ZPeak && oneHardJet && moderateMet'

    config.cuts['zjFree'] = 'ZMetAligned && zPeak && oneHardJet && moderateMet'
    config.cuts['zmetFree'] = 'ZJBacktoback && zPeak && oneHardJet && moderateMet'
    config.cuts['highMet'] = '__baseline__ && t1Met.pt > 75.'

    config.addBkg('wjets', 'W+jets', samples = wlnun, color = ROOT.TColor.GetColor(0xff, 0x44, 0x99))
    config.addBkg('diboson', 'Diboson', samples =  ['ww', 'wz', 'zz'], color = ROOT.TColor.GetColor(0xff, 0xee, 0x99))
    config.addBkg('tt', 'Top', samples = ['tt'], color = ROOT.TColor.GetColor(0x55, 0x44, 0xff))
    config.addBkg('zjets', 'Z+jets', samples = ['dy-50'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

    config.addPlot('met', 'E_{T}^{miss}', 't1Met.pt', [25 * x for x in range(2, 4)] + [100 + 50 * x for x in range(0, 8)], unit = 'GeV', overflow = True)
    config.addPlot('dPhiZJet', '#Delta#phi(Z, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - jets.phi_))', (15, 0., math.pi), cutName = 'zjFree')
    config.addPlot('dPhiJetMet', '#Delta#phi(E_{T}^{miss}, jet)', 'TMath::Abs(TVector2::Phi_mpi_pi(t1Met.phi - jets.phi_))', (15, 0., math.pi), cutName = 'zjFree')
    config.addPlot('dPhiZMet', '#Delta#phi(Z, E_{T}^{miss})', 'TMath::Abs(TVector2::Phi_mpi_pi(z.phi - t1Met.phi))', (15, 0., math.pi), cutName = 'zmetFree')
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
            config.plots.append(plot.clone(plot.name + 'HighMet', cutName = 'highMet'))

elif pu.confName == 'zmumu':
    config.name = 'zmumu'
    config.addObs(common.muonData)

    config.baseline = 'muons.tight[0] && muons.tight[1]'
    config.cuts['highMet'] = '__baseline__ && t1Met.pt > 100.'

    config.addBkg('dy', 'Z+jets', samples = ['dy-50'], color = ROOT.TColor.GetColor(0x99, 0xff, 0xaa))

    config.addPlot('nVertex', 'N_{vertex}', 'npv', (20, 0., 80.), logy = False)
    config.addPlot('rho', '#rho', 'rho', (20, 0., 80.), logy = False)
    config.addPlot('nVertexHighMet', 'N_{vertex}', 'npv', (20, 0., 80.), cutName = 'highMet', logy = False)
    config.addPlot('rhoHighMet', '#rho', 'rho', (20, 0., 80.), cutName = 'highMet', logy = False)

else:
    raise RuntimeError('Unknown configuration ' + pu.confName)
