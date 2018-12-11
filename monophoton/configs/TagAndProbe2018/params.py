import os

_localdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(os.path.dirname(_localdir))

lumilist = basedir + '/data/Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt'
datasetlist = basedir + '/data/datasets18.csv'

pureweight = basedir + '/data/pileup18.root' #needs to be made
