import os
import importlib
import config

tpconf = importlib.import_module('configs.' + config.config + '.tpconf')

skimConfig = tpconf.skimConfig
getBinning = tpconf.getBinning
fitBinningT = tpconf.fitBinningT

def mmtConf(target, dataSource):
    if target == 'monoph':
        outputName = 'ideff_monoph'
        dataSource = 'sph'
        probeSel = 'probes.scRawPt > 220.'
        itune = 2
        probeSel += ' && probes.mediumX[][%d] && probes.mipEnergy < 4.9 && TMath::Abs(probes.time) < 3. && probes.sieie > 0.001 && probes.sipip > 0.001' % itune
        vetoCut = 'probes.pixelVeto'
        labels = ['pass', 'fail']

    elif target == 'gghg':
        outputName = 'ideff_gghg'
        dataSource = 'sph'
        probeSel = 'probes.scRawPt > 220.'
        probeSel += ' && probes.medium'
        vetoCut = 'probes.pixelVeto && probes.chargedPFVeto'
        labels = ['pass', 'fail']

    elif target == 'vbfg':
        outputName = 'ideff_vbfg'
        dataSource = 'sel'
        probeSel = 'probes.scRawPt > 25.'
        probeSel += ' && probes.medium'
        vetoCut = 'probes.pixelVeto && probes.chargedPFVeto'
        labels = ['pass', 'fail']

    outputDir = config.histDir + '/' + outputName

    return outputDir, dataSource, probeSel, vetoCut, labels
