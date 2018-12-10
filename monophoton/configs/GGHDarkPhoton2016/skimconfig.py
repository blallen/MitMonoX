import main.skimutils as su
import selectors as s

makeSel = su.MakeSelectors(s)

data_sph = [
    'gghg', 'gghEfake', 'gghHfake', 
    'gghe', 'ggheEfake', 'ggheHfake', 'gghm', 'gghmEfake', 'gghmHfake', 
    'gghee', 'gghmm',
    'fakeMetRandom', 'fakeMet25', 'fakeMet50', 'fakeMet75',
    'gghgNoGSFix'
]

mc_cand = ['gghg']
mc_qcd = ['fakeMetRandom', 'fakeMet25', 'fakeMet50', 'fakeMet75']
mc_sig = ['signalRaw', 'gghg']
mc_lep = ['gghe', 'gghm']
mc_dilep = ['gghee', 'gghmm']

mc_wlnu = makeSel(makeSel(['gghg'], s.gghgNoE) + ['gghe', 'gghm'], s.addGenPhotonVeto)

skimconfig = {
    # Data
    'sph-16*': makeSel(data_sph),
    # MC
    'gj{,04}-*': makeSel(mc_qcd + mc_cand, s.addKfactor),
    'dyn-50': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'dyn-50@': makeSel(makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto), su.genBosonPtTruncator(maximum = 50.)),
    'dyn-50-*': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'tt': makeSel(mc_cand + mc_lep + mc_dilep, s.addGenPhotonVeto),
    'ttg': makeSel(mc_cand + mc_lep + mc_dilep),
    'tg': makeSel(mc_cand + mc_lep),
    'znng-130-o': makeSel(mc_sig, s.addKfactor),
    'zllg-130-o': makeSel(makeSel(mc_sig + mc_lep + mc_dilep, s.addKfactor), su.ptTruncator(maximum = 300.)),
    'zllg-300-o': makeSel(mc_sig + mc_lep + mc_dilep, s.addKfactor),
    'wnlg-130-o': makeSel(mc_sig + mc_lep, s.addKfactor),
    'wnlg-130-p': makeSel(mc_sig + mc_lep, s.addKfactor),
    'ww': makeSel(mc_cand + mc_lep + mc_dilep),
    'wz': makeSel(mc_cand + mc_lep + mc_dilep),
    'zz': makeSel(mc_cand + mc_lep + mc_dilep),
    # Signal MC
    'dph*': makeSel(mc_sig)
}
