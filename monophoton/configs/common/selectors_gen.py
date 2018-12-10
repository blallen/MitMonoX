import os
import importlib
import logging
import ROOT

import config

logger = logging.getLogger(__name__)

params = importlib.import_module('configs.' + config.config + '.params')

###############
## Modifiers ##
###############
_garbage = []

def addPDFVariation(sample, selector):
    if sample.generator in ('mg5', 'amcatnlo'):
        logger.info('Adding PDF variation for %s', sample.name)
        if 'znng' in sample.name or 'zllg' in sample.name:
            pdf = ROOT.NNPDFVariation()
            pdf.setRescale(0.0420942143487 / 0.0769709934685)
            selector.addOperator(pdf)
        elif 'wnlg' in sample.name or 'wglo' in sample.name:
            pdf = ROOT.NNPDFVariation()
            pdf.setRescale(0.0453828335472 / 0.0933792628506)
            selector.addOperator(pdf)
        else:
            selector.addOperator(ROOT.NNPDFVariation())

def addGenPhotonVeto(sample, selector):
    veto = ROOT.GenPhotonVeto()
    veto.setMinPt(130.)
    veto.setMinPartonDR(0.5)

    selector.addOperator(veto, 0)

def addPUWeight(sample, selector):
    pudir = ROOT.gROOT.GetDirectory('puweight')

    if not pudir:
        pudir = ROOT.gROOT.mkdir('puweight')

        f = ROOT.TFile.Open(params.pureweight)
        for k in f.GetListOfKeys():
            if k.GetName().startswith('puweight_'):
                logger.info('Saving PU weights %s into ROOT/%s', k.GetName(), 'puweight')
                pudir.cd()
                obj = k.ReadObj().Clone(k.GetName().replace('puweight_', ''))
                _garbage.append(obj)

        pudir.cd()
        hdata = f.Get('data').Clone('data')
        _garbage.append(hdata)

        f.Close()

    # Check if we have the sample-specific PU profile here
    hist = pudir.Get(sample.name)

    if not hist:
        # Saved in file?
        pudir.cd()
        # Grab the data histogram and divide by the sample distribution later
        hist = pudir.Get('data').Clone(sample.name)
        mcHist = None

        for dataset in sample.datasetNames:
            if os.path.exists(params.basedir + '/data/pileup/' + dataset + '.root'):
                f = ROOT.TFile.Open(params.basedir + '/data/pileup/' + dataset + '.root')
                h = f.Get('hNPVTrue')
                if mcHist is None:
                    pudir.cd()
                    mcHist = h.Clone(sample.name)
                else:
                    mcHist.Add(h)
    
                f.Close()
                
            elif mcHist is not None:
                raise RuntimeError('Part of sample ' + sample.name + ' has dataset-specific PU profile but not all')

        if mcHist is None:
            hist.Delete()
            hist = None
        else:
            mcHist.Scale(1. / mcHist.GetSumOfWeights())
            hist.Divide(mcHist)
            mcHist.Delete()

    if hist is not None:
        logger.info('Sample-specific PU distribution found for %s', sample.name)
    else:
        for hist in pudir.GetList():
            if hist.GetName() in sample.fullname:
                logger.info('Using PU weights %s/%s for %s', 'puweight', hist.GetName(), sample.name)
                break
        else:
            raise RuntimeError('Pileup profile for ' + sample.name + ' not defined')

    selector.addOperator(ROOT.PUWeight(hist))


#########################
## Modifier generators ##
#########################

def ptTruncator(minimum = 0., maximum = -1.):
    def addPtCut(sample, selector):
        truncator = ROOT.PhotonPtTruncator()
        truncator.setPtMin(minimum)
        if maximum > 0.:
            truncator.setPtMax(maximum)

        selector.addOperator(truncator, 0)

    return addPtCut

def htTruncator(minimum = 0., maximum = -1.):
    def addHtCut(sample, selector):
        truncator = ROOT.HtTruncator()
        truncator.setHtMin(minimum)
        if maximum > 0.:
            truncator.setHtMax(maximum)

        selector.addOperator(truncator, 0)

    return addHtCut

def genBosonPtTruncator(minimum = 0., maximum = -1.):
    def addGenBosonPtCut(sample, selector):
        truncator = ROOT.GenBosonPtTruncator()
        truncator.setPtMin(minimum)
        if maximum > 0.:
            truncator.setPtMax(maximum)

        selector.addOperator(truncator, 0)

    return addGenBosonPtCut

