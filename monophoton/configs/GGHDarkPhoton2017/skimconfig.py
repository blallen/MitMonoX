import main.skimutils as su
import configs.common.selectors_gen as sg
import configs.common.selectors_photon as sp
import selectors as s

makeSel = su.MakeSelectors(s)

data_sph = [
    'gghg', 'gghEfake', 'gghHfake', 
    'gghe', 'ggheEfake', 'ggheHfake', 'gghm', 'gghmEfake', 'gghmHfake', 
    'gghee', 'gghmm',
    'fakeMetRandom', 'fakeMet25', 'fakeMet50', 'fakeMet75',
    'gghgLowPt'
]

mc_cand = ['gghg']
mc_qcd = ['fakeMetRandom', 'fakeMet25', 'fakeMet50', 'fakeMet75']
#mc_sig = ['signalRaw', 'gghg']
mc_sig = ['gghg']
mc_lep = ['gghe', 'gghm']
mc_dilep = ['gghee', 'gghmm']

mc_wlnu = makeSel(makeSel(['gghg'], s.gghgNoE) + ['gghe', 'gghm'], sg.addGenPhotonVeto)

skimconfig = {
    # Data
    'sph-17*': makeSel(data_sph),
#    # MC
    'gj{,04}-*': makeSel(mc_qcd + mc_cand + ['gghgLowPt'], sp.addKfactor),
    'gju': makeSel(mc_qcd + mc_cand + ['gghgLowPt']),
#    'dyn-50': makeSel(mc_cand + mc_lep + mc_dilep, sg.addGenPhotonVeto),
#    'dyn-50@': makeSel(makeSel(mc_cand + mc_lep + mc_dilep, sg.addGenPhotonVeto), sg.genBosonPtTruncator(maximum = 50.)),
#    'dyn-50-*': makeSel(mc_cand + mc_lep + mc_dilep, sg.addGenPhotonVeto),
#    'tt': makeSel(mc_cand + mc_lep + mc_dilep, sg.addGenPhotonVeto),
    'ttg': makeSel(mc_cand + mc_lep + mc_dilep),
#    'tg': makeSel(mc_cand + mc_lep),
    'znng-130-o': makeSel(mc_cand, sp.addKfactor),
    'zllg-130-o': makeSel(makeSel(mc_cand + mc_lep + mc_dilep, sp.addKfactor), sg.ptTruncator(maximum = 300.)),
    'zllg-300-o': makeSel(mc_cand + mc_lep + mc_dilep, sp.addKfactor),
    'wnlg-130-o': makeSel(mc_cand + mc_lep, sp.addKfactor),
#    'wnlg-130-p': makeSel(mc_cand + mc_lep, sp.addKfactor),
    'ww': makeSel(mc_cand + mc_lep + mc_dilep),
    'wz': makeSel(mc_cand + mc_lep + mc_dilep),
    'zz': makeSel(mc_cand + mc_lep + mc_dilep),
    'wwg': makeSel(mc_cand + mc_lep + mc_dilep),
    'wzg': makeSel(mc_cand + mc_lep + mc_dilep),
#    # Signal MC
    'dph*': makeSel(mc_sig)
}
