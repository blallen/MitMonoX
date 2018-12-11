measurements = {
    ('photon', 'sel'): ('sel-17*', 'tpegLowPt', '(tags.hltmatchele27 || tags.hltmatchele32 || tags.hltmatchele35) && probes.medium && !probes.pixelVeto && tp.mass > 60. && tp.mass < 120. && TMath::Abs(TVector2::Phi_mpi_pi(probes.phi_ - tags.phi_)) > 0.6', 'probes'),
    ('photon', 'smu'): ('smu-17*', 'tpmgLowPt', 'tags.hltmatchmu27 && probes.medium', 'probes'),
    ('photon', 'dy'): (['dy-50'], 'tpegLowPt', '(tags.hltmatchele27 || tags.hltmatchele32 || tags.hltmatchele35) && probes.medium && !probes.pixelVeto && tp.mass > 60. && tp.mass < 120. && TMath::Abs(TVector2::Phi_mpi_pi(probes.phi_ - tags.phi_)) > 0.6', 'probes'),
#    ('photon', 'ph75'): (['sph-17b', 'sph-17c', 'sph-17d'], 'ph75', 'photons.medium && HLT_Photon50 && runNumber < 276525', 'photons'),
#    ('photon', 'ph75h'): (['sph-17b', 'sph-17c', 'sph-17d'], 'ph75', 'photons.medium && HLT_Photon75 && runNumber < 276525', 'photons'),
    ('photon', 'mcph75'): (['gj04-*'], 'ph75', 'photons.medium && HLT_Photon50', 'photons'),
    ('electron', 'sel'): ('sel-17*', 'tp2e', 'probes.tight && tp.mass > 60. && tp.mass < 120.', 'probes'),
    ('muon', 'smu'): ('smu-17*', 'tp2m', 'probes.tight && tp.mass > 60. && tp.mass < 120.', 'probes'),
#    ('vbf', 'ph75h'): (['sph-17b', 'sph-17c', 'sph-17d'], 'ph75', 'photons.triggerMatch[][%d] && dijet.size > 0 && runNumber < 276525' % getEnum('Photon', 'fPh75EBR9Iso'), ''),
#    ('vbf', 'dy'): (['dy-50@*', 'dy-50-*'], 'vbfe', 'electrons.triggerMatch[][%d] && dijet.size > 0' % getEnum('Electron', 'fEl75EBR9IsoPh'), ''),
#    ('vbf', 'mcph75h'): (['gj04-*'], 'ph75', 'photons.triggerMatch[][%d] && dijet.size > 0' % getEnum('Photon', 'fPh75EBR9Iso'), ''),
#    ('vbf', 'wlnu'): (['wlnu-*'], 'vbfe', 'electrons.triggerMatch[][%d] && dijet.size > 0' % getEnum('Electron', 'fEl75EBR9IsoPh'), '')
}

confs = {
    'photon': {
        'l1eg': ('{col}.hltmatchphoton200L1Seed', '', 'L1 seed', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', (50, 0., 100.)),
            'ptwide': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(14)] + [100. + 10. * x for x in range(10)] + [200. + 20. * x for x in range(5)] + [300., 350., 400.]),
            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 70.', (25, 0., 0.05)),
            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 70.', (25, 0., 5)),
            'run': ('Run', 'runNumber', '{col}.pt_ > 70.', (26, 294927, 306462))
        }),
        'sph200abs': ('{col}.hltmatchphoton200', '', 'L1&HLT', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(14)] + [100. + 10. * x for x in range(10)] + [200. + 20. * x for x in range(5)] + [300. + 50. * x for x in range(10)]),
            'ptzoom': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '', [30. + 5. * x for x in range(54)] + [300. + 10. * x for x in range(6)]),
            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 220.', (25, 0., 0.05)),
            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 220.', (25, 0., 5)),
            'run': ('Run', 'runNumber', '{col}.pt_ > 220.', (26, 294927, 306462))
        }),
        'ph75r9iso': ('{col}.hltmatchphoton75', '{col}.isEB', 'Photon75Iso40R9', {
            'pt': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '{col}.r9 > 0.9', (50, 0., 100.)),
            'ptwide': ('p_{T}^{#gamma} (GeV)', '{col}.pt_', '{col}.r9 > 0.9', [30. + 10. * x for x in range(7)] + [100., 120., 140., 160., 200., 300., 400., 600.]),
            'r9': ('R^{9}', '{col}.r9', '{col}.pt_ > 80.', (30, 0.7, 1.)),
            'run': ('Run', 'runNumber', '{col}.pt_ > 80.', (26, 294927, 306462))
        })
    },
#    'electron': {
#        'el27': ('{col}.triggerMatch[][%d]' % getEnum('Electron', 'fEl27Tight'), '', 'HLT', {
#            'ptzoom': ('p_{T}^{e} (GeV)', '{col}.pt_', '', (50, 0., 50.)),
#            'ptwide': ('p_{T}^{e} (GeV)', '{col}.pt_', '', [30. + 2. * x for x in range(85)] + [200. + 10. * x for x in range(10)]),
#            'hOverE': ('H/E', '{col}.hOverE', '{col}.pt_ > 200.', (25, 0., 0.05)),
#            'hcalE': ('E^{HCAL} (GeV)', '{col}.pt_ * TMath::CosH({col}.eta_) * {col}.hOverE', '{col}.pt_ > 200.', (25, 0., 5)),
#            'run': ('Run', 'runNumber', '{col}.pt_ > 200.', (350, 271000., 274500.)),
#            'pt': ('p_{T}^{e} (GeV)', '{col}.pt_', '', [0. + 5. * x for x in range(10)] + [50. + 10. * x for x in range(6)]),
#            'eta': ('#eta^{e}', '{col}.eta_', '{col}.pt_ > 50.', (25, -2.5, 2.5))
#        })
#    },
#    'muon': {
#        'mu24ortrk24': ('{col}.triggerMatch[][%d] || {col}.triggerMatch[][%d]' % (getEnum('Muon', 'fIsoMu24'), getEnum('Muon', 'fIsoTkMu24')), '', 'HLT', {
#            'ptzoom': ('p_{T}^{#mu} (GeV)', '{col}.pt_', '', (50, 0., 50.)),
#            'ptwide': ('p_{T}^{#mu} (GeV)', '{col}.pt_', '', [30. + 2. * x for x in range(85)] + [200. + 10. * x for x in range(10)]),
#            'run': ('Run', 'runNumber', '{col}.pt_ > 200.', (350, 271000., 274500.)),
#            'pt': ('p_{T}^{#mu} (GeV)', '{col}.pt_', '', [0. + 5. * x for x in range(10)] + [50. + 10. * x for x in range(6)])
#        })
#    },
    'vbf': {
        'vbf': ('HLT_Photon75_R9Id90_HE10_Iso40_EBOnly_VBF', '', 'VBF filter', {
            'dEtajj': ('|#Delta#eta_{jj}|', 'Max$(TMath::Abs(dijet.dEtajj * (dijet.mjj > 800.)))', 'Sum$(dijet.mjj > 500) != 0', (50, 0., 5.)),
            'mjj': ('m_{jj} (GeV)', 'Max$(TMath::Abs(dijet.mjj * (TMath::Abs(dijet.dEtajj) > 3.2)))', 'Sum$(TMath::Abs(dijet.dEtajj) > 3.2) != 0', (50, 0., 1000.))
        })
    }
}

# TTree output for fitting
fitconfs = {}
#fitconfs['photon'] = []
#fitconfs['electron'] = [
#    ('ptzoom', 'el27')
#]
#fitconfs['muon'] = []
#fitconfs['vbf'] = []
