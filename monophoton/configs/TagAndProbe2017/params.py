import os

_localdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(os.path.dirname(_localdir))

lumilist = basedir + '/data/Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt'
datasetlist = basedir + '/data/datasets17.csv'

pureweight = basedir + '/data/pileup17.root'
