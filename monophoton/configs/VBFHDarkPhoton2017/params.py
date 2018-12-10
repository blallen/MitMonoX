import os

_localdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(os.path.dirname(_localdir))

lumilist = basedir + '/data/lumis16_plain.txt'
datasetlist = basedir + '/data/datasets16.csv'

pureweight = ('puweight_vbf75', basedir + '/data/pileup16_vbf75.root')
