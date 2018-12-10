import os
import math

from main.plotutil import *

thisdir = os.path.dirname(os.path.realpath(__file__))
execfile(thisdir + '/../2016Common/plotconfig_common.py')

import ROOT

def getConfig(confName):
    if confName == 'tp2m':

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

    else:
        raise RuntimeError('Unknown configuration ' + confName)

    return config
