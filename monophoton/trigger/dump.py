"""
Fill a histogram of triggers (passes per path).
"""

import os
import sys
import ROOT

from datasets import allsamples
import config

sname = sys.argv[1]
sample = allsamples[sname]

ROOT.gSystem.Load(config.libobjs)
e = ROOT.panda.Event

ROOT.gROOT.LoadMacro('Dumper.cc+')

tree = ROOT.TChain('events')
for fname in sample.files():
    tree.Add(fname)

ROOT.triggerRates(tree, 'test.root', 10000)
