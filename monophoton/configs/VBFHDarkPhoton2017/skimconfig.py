import main.skimutils as su
import selectors as s

makeSel = su.MakeSelectors(s)

data_sph = [
    'vbfg', 'vbfem', 'vbfgEfake', 'vbfgHfake', 'vbfgCtrl', 'vbfgHfakeCtrl', 'ph75', 'vbfgLJCtrl',
    'vbfzee', 'vbfzeeEfake'
]

data_smu = [
    'vbfm', 'vbfmm'
]

data_sel = [
    'vbfe', 'vbfee'
]

mc_cand = ['vbfg', 'vbfgCtrl', 'vbfgLJCtrl']
mc_sig = ['vbfg', 'signalRaw']
mc_lep = ['vbfe', 'vbfm']
mc_dilep = ['vbfee', 'vbfmm']

skimconfig = {
    # Data
    'sph-16*': makeSel(data_sph),
    'smu-16*': makeSel(data_smu),
    'sel-16*': makeSel(data_sel),
    # MC
    'gj{,04}-*': makeSel(mc_cand + ['vbfem', 'ph75'], s.addKfactor),
    'gjn*': makeSel(mc_cand + ['vbfem', 'ph75']),
    'dy-50': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'dy-50@': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto, su.htTruncator(maximum = 100.)),
    'dy-50-*': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'dyn-50': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'dyn-50@': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto, su.genBosonPtTruncator(maximum = 50.)),
    'dyn-50-*': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'zewk': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'w{m,p}lnuewk': makeSel(mc_lep),
    'tt': makeSel(mc_cand + mc_lep + mc_dilep),
    'st*': makeSel(mc_lep),
    'ttg': makeSel(mc_cand + mc_lep + mc_dilep + ['vbfzee']),
    'tg': makeSel(mc_cand + mc_lep + ['vbfzee']),
    'ww': makeSel(mc_cand + mc_lep + mc_dilep),
    'wz': makeSel(mc_cand + mc_lep + mc_dilep),
    'zz': makeSel(mc_cand + mc_lep + mc_dilep),
    'znng': makeSel(mc_sig),
    'wglo': makeSel(mc_cand + mc_lep + ['vbfgWHadCtrl', 'vbfzee'], s.addKfactor),
    'wlnu': makeSel(mc_lep, su.htTruncator(maximum = 70.)),
    'wlnu{,n}-*': makeSel(mc_lep),
    # Signal MC
    'dph*': makeSel(mc_sig)
}
