# Grouping of samples for convenience.
# Argument targets can be individual sample names or the config names (eldata/mudata/mc).
# Samples in the same data are skimmed for skimTypes (second parameters of the tuples) in the group.
dy50 = ['dy-50@', 'dy-50-100', 'dy-50-200', 'dy-50-400', 'dy-50-600', 'dy-50-800', 'dy-50-1200', 'dy-50-2500']
# dy50 = ['dyn-50@', 'dyn-50-50', 'dyn-50-100', 'dyn-50-250', 'dyn-50-400', 'dyn-50-650']
sampleGroups = {
    'sph': (['sph-17b', 'sph-17c', 'sph-17d', 'sph-17e', 'sph-17f'], ['kEG', 'kMG']),
    'sel': (['sel-17b', 'sel-17c', 'sel-17d', 'sel-17e', 'sel-17f'], ['kEG']),
    'smu': (['smu-17b', 'smu-17c', 'smu-17d', 'smu-17e', 'smu-17f'], ['kMG']),
    'sphB': (['sph-17b'], ['kEG', 'kMG']),
    'selB': (['sel-17b'], ['kEG']),
    'smuB': (['smu-17b'], ['kMG']),
    'selCDE': (['sph-17c', 'sph-17d', 'sph-17e'], ['kEG', 'kMG']),
    'selCDE': (['sel-17c', 'sel-17d', 'sel-17e'], ['kEG']),
    'smuCDE': (['smu-17c', 'smu-17d', 'smu-17e'], ['kMG']),
    'sphF': (['sph-17f'], ['kEG', 'kMG']),
    'selF': (['sel-17f'], ['kEG']),
    'smuF': (['smu-17f'], ['kMG']),
    'mc': (dy50 + ['wglo', 'tt'], ['kEG', 'kMG', 'kMMG']),
    'mcmu': (dy50, ['kEG', 'kMG', 'kMMG']),
    'mcgg': (['gg-80'], ['kEG'])
}

fitBinningT = (120, 60., 120.)

def getBinning(binningName):
    if binningName == 'inclusive':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [175., 6500.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

        binning.pop()
        binning.append(500.)

    elif binningName in ['pt', 'ptnlo', 'ptnloalt']:
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [175., 200., 250., 6500.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

        binning.pop()
        binning.append(500.)

    elif binningName == 'ptalt':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [175., 200., 250., 300., 350., 400., 6500.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

        # hack to elimiate one large-weight event
        fitBins[-1] = (fitBins[-1][0], fitBins[-1][1] + ' && (weight == 1 || weight < 0.0001)')

        binning.pop()
        binning.append(500.)

    elif binningName == 'ptalt2':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [175., 200., 250., 6500.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

        # hack to elimiate one large-weight event
        fitBins[-1] = (fitBins[-1][0], fitBins[-1][1] + ' && (weight == 1 || weight < 0.0001)')

        binning.pop()
        binning.append(500.)

    elif binningName == 'highpt':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [175., 200., 225., 250., 275., 300., 350., 400., 6500.] 
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

        binning.pop()
        binning.append(500.)

    elif binningName == 'lowpt':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [24., 28., 32., 35., 38., 40., 42., 44., 46., 48., 50., 54., 58., 62., 66., 70., 75., 80., 85., 90., 100., 120., 140., 160.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

    elif binningName in ['pogpt', 'pogptalt']:
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [20., 35., 50., 90., 150., 6500.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

        binning.pop()
        binning.append(200.)

    elif binningName == 'pteta':
        binningTitle = 'p_{T}^{probe} (GeV)'
        
        ptBinning = [175., 200., 250., 300., 350., 400., 6500.]
        etaBinning = [-1.5, -0.8, 0., 0.8, 1.5]

        fitBins = []
        for iBin in range(len(etaBinning) - 1):
            etaRepl = {'low': etaBinning[iBin], 'high': etaBinning[iBin + 1]}
            etaName = 'eta_{low:.0f}_{high:.0f}'.format(**etaRepl)
            etaCut = 'probes.scEta > {low:.2f} && probes.scEta < {high:.2f}'.format(**etaRepl)

            for jBin in range(len(ptBinning) - 1):
                ptRepl = {'low': ptBinning[jBin], 'high': ptBinning[jBin + 1]}
                ptName = 'pt_{low:.0f}_{high:.0f}'.format(**ptRepl)
                ptCut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**ptRepl)

                name = etaName + '_' + ptName
                cut = etaCut + ' && ' + ptCut
                fitBins.append((name, cut))

        binning = range(len(fitBins) + 1)

    elif binningName in ['ht', 'htalt']:
        binningTitle = 'H_{T} (GeV)'
        binning = [0., 100., 200., 400., 600., 800., 1200., 13000.]

        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'ht_{low:.0f}_{high:.0f}'.format(**repl)
            # ht = 'Sum$(partons.pt_ * (TMath::Abs(partons.pdgid) < 6 || TMath::Abs(partons.pdgid) == 21))'
            ht = 'Sum$(jets.pt_)'
            cut = ht + ' > {low:.0f} && ' + ht + ' < {high:.0f}'
            cut = cut.format(**repl)
            fitBins.append((name, cut))

        binning.pop()
        binning.append(1500.)


    elif binningName in ['ptht', 'pthtalt']:
        binningTitle = 'p_{T}^{probe} (GeV)'
        
        ptBinning = [20., 35., 50., 90., 150., 6500.] # [175., 200., 250., 6500.]
        htBinning = [0., 200., 400., 600., 800., 13000.]

        fitBins = []
        for iBin in range(len(htBinning) - 1):
            htRepl = {'low': htBinning[iBin], 'high': htBinning[iBin + 1]}
            htName = 'ht_{low:.0f}_{high:.0f}'.format(**htRepl)
            ht = 'Sum$(jets.pt_)'
            htCut = ht + ' > {low:.0f} && ' + ht + ' < {high:.0f}'
            htCut = htCut.format(**htRepl)

            for jBin in range(len(ptBinning) - 1):
                ptRepl = {'low': ptBinning[jBin], 'high': ptBinning[jBin + 1]}
                ptName = 'pt_{low:.0f}_{high:.0f}'.format(**ptRepl)
                ptCut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**ptRepl)

                name = htName + '_' + ptName
                cut = htCut + ' && ' + ptCut
                fitBins.append((name, cut))

        binning = range(len(fitBins) + 1)

    elif binningName == 'test':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [28., 32.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.scRawPt > {low:.0f} && probes.scRawPt < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))

    elif binningName == 'mutest':
        binningTitle = 'p_{T}^{probe} (GeV)'
        binning = [24., 28.]
        
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'pt_{low:.0f}_{high:.0f}'.format(**repl)
            cut = 'probes.pt_ > {low:.0f} && probes.pt_ < {high:.0f}'.format(**repl)
            fitBins.append((name, cut))
    
    elif binningName == 'eta':
        binningTitle = '|#eta^{probe}| (GeV)'
        binning = [0., 0.2, 0.4, 0.6, 1., 1.5]
    
        fitBins = []
        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'eta_{low:.1f}_{high:.1f}'.format(**repl)
            cut = 'probes.scRawPt > 40. && TMath::Abs(probes.eta_) > {low:.1f} && TMath::Abs(probes.eta_) < {high:.1f}'.format(**repl)
            fitBins.append((name, cut))
    
    elif binningName == 'njet':
        binningTitle = 'N^{jet}'
        binning = [0., 1., 2., 3., 4., 10.]
    
        fitBins = []
        for low, high in [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 10)]:
            repl = {'low': low, 'high': high}
            name = 'njet_{low}_{high}'.format(**repl)
            if low == high:
                cut = 'probes.scRawPt > 40. && TMath::Max(0, jets.size - 2) == {low}'.format(**repl)
            else:
                cut = 'probes.scRawPt > 40. && TMath::Max(0, jets.size - 2) >= {low} && TMath::Max(0, jets.size - 2) <= {high}'.format(**repl)
    
            fitBins.append((name, cut))
    
    elif binningName == 'npv':
        binningTitle = 'N^{PV}'
        binning = [0., 10., 20., 30.]
    
        fitBins = []
        for low, high in [(0, 9), (10, 19), (20, 29)]:
            repl = {'low': low, 'high': high}
            name = 'npv_{low}_{high}'.format(**repl)
            if low == high:
                cut = 'probes.scRawPt > 175. && npv == {low}'.format(**repl)
            else:
                cut = 'probes.scRawPt > 175. && npv >= {low} && npv <= {high}'.format(**repl)
    
            fitBins.append((name, cut))

    elif binningName == 'npvh':
        binningTitle = 'N^{PV}'
        binning = [0., 10., 20., 30.]
    
        fitBins = []
        for low, high in [(0, 9), (10, 19), (20, 29)]:
            repl = {'low': low, 'high': high}
            name = 'npvh_{low}_{high}'.format(**repl)
            if low == high:
                cut = 'probes.scRawPt > 175. && npv == {low} && runNumber >= 280919 && runNumber <= 284044'.format(**repl)
            else:
                cut = 'probes.scRawPt > 175. && npv >= {low} && npv <= {high} && runNumber >= 280919 && runNumber <= 284044'.format(**repl)
    
            fitBins.append((name, cut))

    elif binningName == 'npvbg':
        binningTitle = 'N^{PV}'
        binning = [0., 10., 20., 30.]
    
        fitBins = []
        for low, high in [(0, 9), (10, 19), (20, 29)]:
            repl = {'low': low, 'high': high}
            name = 'npvh_{low}_{high}'.format(**repl)
            if low == high:
                cut = 'probes.scRawPt > 175. && npv == {low} && runNumber >= 272007 && runNumber <= 280385'.format(**repl)
            else:
                cut = 'probes.scRawPt > 175. && npv >= {low} && npv <= {high} && runNumber >= 272007 && runNumber <= 280385'.format(**repl)
    
            fitBins.append((name, cut))

    elif binningName == 'chiso':
        binningTitle = 'chiso'
        binning = [0., 0.01, 0.5, 1., 1.37]

        fitBins = []

        for iBin in range(len(binning) - 1):
            repl = {'low': binning[iBin], 'high': binning[iBin + 1]}
            name = 'chiso_{low:.2f}_{high:.2f}'.format(**repl)
            cut = 'probes.scRawPt > 175. && probes.chIso >= {low:.2f} && probes.chIso < {high:.2f}'.format(**repl)
            fitBins.append((name, cut))

    return binningTitle, binning, fitBins
