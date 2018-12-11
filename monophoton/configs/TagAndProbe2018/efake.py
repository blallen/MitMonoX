import os
import importlib
import config

tpconf = importlib.import_module('configs.' + config.config + '.tpconf')

sampleGroups = tpconf.sampleGroups
getBinning = tpconf.getBinning
fitBinningT = tpconf.fitBinningT

def mmtConf(target):
    if target.startswith('monoph'):
        outputName = 'efrate_monoph'
        dataSource = 'sph'
        probeSel = 'probes.scRawPt > 220.'
        itune = 2
        probeSel += ' && probes.mediumX[][%d] && probes.mipEnergy < 4.9 && TMath::Abs(probes.time) < 3. && probes.sieie > 0.001 && probes.sipip > 0.001' % itune
        vetoCut = 'probes.pixelVeto'
        labels = ['ee', 'eg']

    elif target.startswith('gghg'):
        outputName = 'efrate_gghg'
        dataSource = 'sph'
        probeSel = 'probes.scRawPt > 220.'
        probeSel += ' && probes.medium'
        vetoCut = 'probes.pixelVeto && probes.chargedPFVeto'
        labels = ['ee', 'eg']

    elif target == 'vbfg':
        outputName = 'efrate_vbfg'
        dataSource = 'sel'
        probeSel = 'probes.scRawPt > 25.'
        probeSel += ' && probes.medium'
        vetoCut = 'probes.pixelVeto && probes.chargedPFVeto'
        labels = ['ee', 'eg']

    if target.endswith('B'):
        dataSource += 'B'
    if target.endswith('CDE'):
        dataSource += 'CDE'
    elif target.endswith('F'):
        dataSource += 'F'

    outputDir = config.histDir + '/' + outputName

    return outputDir, dataSource, probeSel, vetoCut, labels
