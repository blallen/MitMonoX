#!/usr/bin/env python

import os
import sys
import shutil
import importlib

import ROOT

from datasets import allsamples
import config

os.environ['X509_USER_PROXY'] = os.getcwd() + '/x509up_u51268'

sname = sys.argv[1]

sample = allsamples[sname]

for dataset in sample.datasetNames:
    out = ROOT.TFile.Open(dataset + '.root', 'recreate')
    htrue = None
    hreco = None
    for fname in sample.files(sample.filesets([dataset])):
        source = ROOT.TFile.Open(fname.replace('/mnt/hadoop/cms', 'root://xrootd.cmsaf.mit.edu/'))
        if htrue is None:
            out.cd()
            htrue = source.Get('hNPVTrue').Clone()
            hreco = source.Get('hNPVReco').Clone()
        else:
            htrue.Add(source.Get('hNPVTrue'))
            hreco.Add(source.Get('hNPVReco'))

        source.Close()

    out.cd()
    out.Write()
    out.Close()

    shutil.copyfile(dataset + '.root', config.baseDir + '/data/pileup/' + dataset + '.root')
