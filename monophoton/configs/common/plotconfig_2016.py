import sys
import os
import math

import config as globalConf

argv = list(sys.argv)
sys.argv = []
import ROOT
black = ROOT.kBlack # need to load something from ROOT to actually import
sys.argv = argv

photonDataICHEP = ['sph-16b-m', 'sph-16c-m', 'sph-16d-m']
photonData = ['sph-16b-m', 'sph-16c-m', 'sph-16d-m', 'sph-16e-m', 'sph-16f-m', 'sph-16g-m', 'sph-16h-m']
photonDataPrescaled = [
    ('sph-16b-m', 5),
    ('sph-16c-m', 5),
    ('sph-16d-m', 5),
    ('sph-16e-m', 5),
    ('sph-16f-m', 5),
    ('sph-16g-m', 5),
    ('sph-16h-m', 5)
]
muonData = ['smu-16b-m', 'smu-16c-m', 'smu-16d-m', 'smu-16e-m', 'smu-16f-m', 'smu-16g-m', 'smu-16h-m']
electronData = ['sel-16b-m', 'sel-16c-m', 'sel-16d-m', 'sel-16e-m', 'sel-16f-m', 'sel-16g-m', 'sel-16h-m']

gj = ['gj-100', 'gj-200', 'gj-400', 'gj-600']
gje = ['gje-100', 'gje-200', 'gje-400', 'gje-600']
gj04 = ['gj04-100', 'gj04-200', 'gj04-400', 'gj04-600']
wlnu = ['wlnu@', 'wlnu-70', 'wlnu-100', 'wlnu-200', 'wlnu-400', 'wlnu-600', 'wlnu-800', 'wlnu-1200', 'wlnu-2500']
wlnun = ['wlnun-0', 'wlnun-50', 'wlnun-100', 'wlnun-250', 'wlnun-400', 'wlnun-600']
dy = ['dy-50@', 'dy-50-100', 'dy-50-200', 'dy-50-400', 'dy-50-600', 'dy-50-800', 'dy-50-1200', 'dy-50-2500']
dyn = ['dyn-50@', 'dyn-50-50', 'dyn-50-100', 'dyn-50-250', 'dyn-50-400', 'dyn-50-650']
qcd = ['qcd-200', 'qcd-300', 'qcd-500', 'qcd-700', 'qcd-1000', 'qcd-1500', 'qcd-2000']
top = ['ttg', 'tg']
gg = ['gg-40', 'gg-80']
minor = gg + ['zllg-130-o', 'zllg-300-o']

dPhiPhoMet = 'TVector2::Phi_mpi_pi(photons.phi_[0] - t1Met.phi)'
mtPhoMet = 'TMath::Sqrt(2. * t1Met.pt * photons.scRawPt[0] * (1. - TMath::Cos(photons.phi_[0] - t1Met.phi)))'
fitTemplateExpression = '( ( (photons.scRawPt[0] - 175.) * (photons.scRawPt[0] < 1000.) + 800. * (photons.scRawPt[0] > 1000.) ) * TMath::Sign(1, TMath::Abs(TMath::Abs(TVector2::Phi_mpi_pi(TVector2::Phi_mpi_pi(photons.phi_[0] + 0.005) - 1.570796)) - 1.570796) - 0.5) )'




