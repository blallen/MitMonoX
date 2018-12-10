import main.skimutils as su
import selectors as s

makeSel = su.MakeSelectors(s)

data_sph = [
    'monoph', 
    'efake', 'hfake', 'trivialShower', 'halo',
    'dimu', 'diel', 'monomu', 'monoel',
    'dimuHfake', 'dielHfake', 'monomuHfake', 'monomuEfake', 'monoelHfake', 'monoelEfake', 'monoelQCD',
    'tpeg', 'tpmg',
    'emjet',
    'dimuAllPhoton', 'dielAllPhoton', 'monomuAllPhoton', 
    'dijet',
    'monophNoGSFix'
]

data_smu = [
    'monomuLowPt'
]

mc_cand = ['monoph', 'emjet']
mc_qcd = ['hfake']
mc_sig = ['monoph', 'emjet']
mc_lep = ['monomu', 'monoel']
mc_dilep = ['dimu', 'dimuAllPhoton', 'diel', 'dielVertex', 'dimuVertex']

mc_ewk = ['monoph250', 'monoph300', 'monoph400', 'monoph500', 'monoph600']
mc_ewk_lep = ['monomu250', 'monomu300', 'monomu400', 'monomu500', 'monomu600', 'monoel250', 'monoel300', 'monoel400', 'monoel500', 'monoel600']
mc_ewk_dilep = ['dimu250', 'dimu300', 'dimu400', 'dimu500', 'dimu600', 'diel250', 'diel300', 'diel400', 'diel500', 'diel600']

mc_wlnu = ['wenu', 'monoelVertex', 'monomuVertex'] + makeSel(makeSel(['monoph'], s.monophNoE) + ['monomu', 'monoel', 'emjet'], s.addGenPhotonVeto)

skimconfig = {
    # Data
    'sph-16*': makeSel(data_sph),
    'smu-16*': makeSel(data_smu),
    # MC
    'gj{,04}-*': makeSel(mc_qcd + mc_cand + ['halo', 'monoel'], s.addKfactor),
    'tt': makeSel(mc_cand + mc_lep + mc_dilep),
    'znng-130-o': makeSel(makeSel(mc_sig + ['monophNoLVeto', 'trivialShower'], s.addKfactor) + mc_ewk),
    'zllg-130-o': makeSel(makeSel(mc_sig + mc_lep + mc_dilep, s.addKfactor, su.ptTruncator(maximum = 300.)) + mc_ewk + mc_ewk_lep + mc_ewk_dilep),
    'zllg-300-o': makeSel(makeSel(mc_sig + mc_lep + mc_dilep, s.addKfactor) + mc_ewk + mc_ewk_lep + mc_ewk_dilep),
    'wnlg-130-o': makeSel(makeSel(mc_sig + mc_lep, s.addKfactor) + mc_ewk + mc_ewk_lep),
    'wnlg-130-p': makeSel(makeSel(mc_sig + mc_lep, s.addKfactor) + mc_ewk + mc_ewk_lep),
    'gg-*': makeSel(mc_cand + mc_lep + mc_dilep),
    'ttg': makeSel(mc_cand + mc_lep + mc_dilep),
    'tg': makeSel(mc_cand + mc_lep),
    'ww': makeSel(mc_cand + mc_lep + mc_dilep),
    'wz': makeSel(mc_cand + mc_lep + mc_dilep),
    'zz': makeSel(mc_cand + mc_lep + mc_dilep),
    'wlnu{,n}-*': makeSel(mc_wlnu),
    # Signal MC
    'add-*': makeSel(mc_sig),
    'dm*': makeSel(mc_sig)
}
