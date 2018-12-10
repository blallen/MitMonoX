photonData = ['sph-17b', 'sph-17c', 'sph-17d', 'sph-17e', 'sph-17f']
muonData = ['smu-17b', 'smu-17c', 'smu-17d', 'smu-17e', 'smu-17f']
electronData = ['sel-17b', 'sel-17c', 'sel-17d', 'sel-17e', 'sel-17f']

#gj = ['gj-100', 'gj-200', 'gj-400', 'gj-600']
gj = ['gj-100', 'gj-200', 'gj04-400', 'gj-600']
#gje = ['gje-100', 'gje-200', 'gje-400', 'gje-600']
#gj04 = ['gj04-100', 'gj04-200', 'gj04-400', 'gj04-600']
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
