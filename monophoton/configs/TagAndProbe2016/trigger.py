import ROOT

ROOT.gSystem.Load('libPandaTreeObjects.so')
e = ROOT.panda.Event

ROOT.gROOT.ProcessLine('int val;')
def getEnum(cls, name):
    ROOT.gROOT.ProcessLine('val = panda::' + cls + '::TriggerObject::' + name + ';')
    return ROOT.val

measurements = {
    ('photon', 'sel'): ('sel-16b-m', 'tpegLowPt', 'probes.medium && !probes.pixelVeto && tp.mass > 60. && tp.mass < 120. && TMath::Abs(TVector2::Phi_mpi_pi(probes.phi_ - tags.phi_)) > 0.6', 'probes'),
    ('photon', 'selBCD'): (['sel-16b-m', 'sel-16c-m', 'sel-16d-m'], 'tpegLowPt', 'probes.medium && !probes.pixelVeto && tp.mass > 60. && tp.mass < 120. && TMath::Abs(TVector2::Phi_mpi_pi(probes.phi_ - tags.phi_)) > 0.6 && runNumber < 276525', 'probes'), # for photon75
    ('photon', 'dy'): (['dy-50@', 'dy-50-*'], 'tpegLowPt', 'probes.medium && !probes.pixelVeto && tp.mass > 60. && tp.mass < 120. && TMath::Abs(TVector2::Phi_mpi_pi(probes.phi_ - tags.phi_)) > 0.6', 'probes'),
    ('photon', 'elmu'): (['smu-16*-m'], 'elmu', 'photons.mediumX[][2]', 'photons'),
    ('photon', 'elmuBCD'): (['smu-16b-m', 'smu-16c-m', 'smu-16d-m'], 'elmu', 'photons.mediumX[][2]', 'photons'),
    ('photon', 'ph75'): (['sph-16b-m', 'sph-16c-m', 'sph-16d-m'], 'ph75', 'photons.medium && HLT_Photon50 && runNumber < 276525', 'photons'),
    ('photon', 'ph75h'): (['sph-16b-m', 'sph-16c-m', 'sph-16d-m'], 'ph75', 'photons.medium && HLT_Photon75 && runNumber < 276525', 'photons'),
    ('photon', 'mcph75'): (['gj04-*'], 'ph75', 'photons.medium && HLT_Photon50', 'photons'),
    ('electron', 'sel'): ('sel-16*-m', 'tp2e', 'probes.tight && tp.mass > 60. && tp.mass < 120.', 'probes'),
    ('muon', 'smu'): ('smu-16*', 'tp2m', 'probes.tight && tp.mass > 60. && tp.mass < 120.', 'probes'),
    ('vbf', 'selBCD'): (['sel-16b-m', 'sel-16c-m', 'sel-16d-m'], 'vbfe', 'electrons.triggerMatch[][%d] && dijet.size > 0 && runNumber < 276525' % getEnum('Electron', 'fEl75EBR9IsoPh'), ''),
    ('vbf', 'ph75h'): (['sph-16b-m', 'sph-16c-m', 'sph-16d-m'], 'ph75', 'photons.triggerMatch[][%d] && dijet.size > 0 && runNumber < 276525' % getEnum('Photon', 'fPh75EBR9Iso'), ''),
    ('vbf', 'dy'): (['dy-50@*', 'dy-50-*'], 'vbfe', 'electrons.triggerMatch[][%d] && dijet.size > 0' % getEnum('Electron', 'fEl75EBR9IsoPh'), ''),
    ('vbf', 'mcph75h'): (['gj04-*'], 'ph75', 'photons.triggerMatch[][%d] && dijet.size > 0' % getEnum('Photon', 'fPh75EBR9Iso'), ''),
    ('vbf', 'wlnu'): (['wlnu-*'], 'vbfe', 'electrons.triggerMatch[][%d] && dijet.size > 0' % getEnum('Electron', 'fEl75EBR9IsoPh'), '')
}

confs = {
    'photon': {
        'l1eg40': ('{col}.triggerMatch[][%d]' % getEnum('Photon', 'fSEG34IorSEG40'), '', 'L1 seed', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', (50, 0., 100.)),
            'ptwide': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(14)] + [100. + 10. * x for x in range(10)] + [200. + 20. * x for x in range(5)] + [300., 350., 400.]),
            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 175.', (25, 0., 0.05)),
            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 175.', (25, 0., 5))
        }),
        'l1all': ('{col}.triggerMatch[][%d] || {col}.triggerMatch[][%d] || {col}.triggerMatch[][%d]' % (getEnum('Photon', 'fSEG34IorSEG40'), getEnum('Photon', 'fSEG40IorSJet200'), getEnum('Photon', 'fSEG34IorSEG40IorSJet200')), '', 'L1 seed', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', (50, 0., 100.)),
            'ptwide': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(14)] + [100. + 10. * x for x in range(10)] + [200. + 20. * x for x in range(5)] + [300., 350., 400.]),
            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 175.', (25, 0., 0.05)),
            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 175.', (25, 0., 5))
        }),
        'sph165abs': ('{col}.triggerMatch[][%d]' % getEnum('Photon', 'fPh165HE10'), '', 'L1&HLT', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(14)] + [100. + 10. * x for x in range(10)] + [200. + 20. * x for x in range(5)] + [300. + 50. * x for x in range(10)]),
            'ptzoom': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(34)] + [200. + 15. * x for x in range(11)]),
            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 175.', (25, 0., 0.05)),
            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 175.', (25, 0., 5)),
            'run': ('Run', 'runNumber', '{col}.pt_ > 175.', (26, 271050., 284050.))
        }),
        'ph75r9iso': ('{col}.triggerMatch[][%d]' % getEnum('Photon', 'fPh75EBR9Iso'), '{col}.isEB', 'Photon75Iso40R9', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '{col}.r9 > 0.9', (50, 0., 100.)),
            'ptwide': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '{col}.r9 > 0.9', [30. + 10. * x for x in range(7)] + [100., 120., 140., 160., 200., 300., 400., 600.]),
            'r9': ('R^{9}', '{col}.r9', '{col}.pt_ > 80.', (30, 0.7, 1.))
        })
    },
    'electron': {
        'el27': ('{col}.triggerMatch[][%d]' % getEnum('Electron', 'fEl27Tight'), '', 'HLT', {
            'ptzoom': ('p_{T}^{e} (GeV)', '{col}.pt_', '', (50, 0., 50.)),
            'ptwide': ('p_{T}^{e} (GeV)', '{col}.pt_', '', [30. + 2. * x for x in range(85)] + [200. + 10. * x for x in range(10)]),
            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 200.', (25, 0., 0.05)),
            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 200.', (25, 0., 5)),
            'run': ('Run', 'runNumber', '{col}.pt_ > 200.', (350, 271000., 274500.)),
            'pt': ('p_{T}^{e} (GeV)', '{col}.pt_', '', [0. + 5. * x for x in range(10)] + [50. + 10. * x for x in range(6)]),
            'eta': ('#eta^{e}', '{col}.eta_', '{col}.pt_ > 50.', (25, -2.5, 2.5))
        })
    },
    'muon': {
        'mu24ortrk24': ('{col}.triggerMatch[][%d] || {col}.triggerMatch[][%d]' % (getEnum('Muon', 'fIsoMu24'), getEnum('Muon', 'fIsoTkMu24')), '', 'HLT', {
            'ptzoom': ('p_{T}^{#mu} (GeV)', '{col}.pt_', '', (50, 0., 50.)),
            'ptwide': ('p_{T}^{#mu} (GeV)', '{col}.pt_', '', [30. + 2. * x for x in range(85)] + [200. + 10. * x for x in range(10)]),
            'run': ('Run', 'runNumber', '{col}.pt_ > 200.', (350, 271000., 274500.)),
            'pt': ('p_{T}^{#mu} (GeV)', '{col}.pt_', '', [0. + 5. * x for x in range(10)] + [50. + 10. * x for x in range(6)])
        })
    },
    'vbf': {
        'vbf': ('HLT_Photon75_R9Id90_HE10_Iso40_EBOnly_VBF', '', 'VBF filter', {
            'dEtajj': ('|#Delta#eta_{jj}|', 'Max$(TMath::Abs(dijet.dEtajj * (dijet.mjj > 800.)))', 'Sum$(dijet.mjj > 500) != 0', (50, 0., 5.)),
            'mjj': ('m_{jj} (GeV)', 'Max$(TMath::Abs(dijet.mjj * (TMath::Abs(dijet.dEtajj) > 3.2)))', 'Sum$(TMath::Abs(dijet.dEtajj) > 3.2) != 0', (50, 0., 1000.))
        })
    }
}

# TTree output for fitting
fitconfs = {}
fitconfs['photon'] = []
fitconfs['electron'] = [
    ('ptzoom', 'el27')
]
fitconfs['muon'] = []
fitconfs['vbf'] = []
