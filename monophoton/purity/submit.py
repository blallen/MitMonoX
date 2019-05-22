#!/usr/bin/env python

import sys
import os
import shutil
from subprocess import Popen, PIPE
import tarfile
import time

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
import selections as s

scratchPath = s.versionDir

argFile = file('condorArgs.txt', 'w')

bases = s.bases 
mods = s.mods
PhotonIds = [base+mod for base in bases for mod in mods]
# PhotonIds.append('none')

for era in ['GJetsCWIso']:
    for loc in s.Locations[:1]:
        for pt in sorted(s.PhotonPtSels.keys())[3:]:
            for met in sorted(s.MetSels.keys())[1:2]:
                for sel in PhotonIds:
                    outDir = scratchPath + '/' + era + '_' + loc + '_' + sel + '_' + pt + '_' + met

                    if not os.path.exists(outDir):
                        os.makedirs(outDir)
                        
                    argFile.write(loc + ' ' + sel + ' ' + pt.replace('PhotonPt', '') + ' ' + met.replace('Met', '') + ' ' + era + ' \n')

argFile.close()
# sys.exit(0)
"""
mceff = Popen( ['/home/ballen/bin/condor-run', 'calcEfficiency.py', '-a', 'condorArgs.txt'], stdout = PIPE, stderr = PIPE )
for mout_line in iter(mceff.stdout.readline, ''):
     sys.stdout.write(mout_line)
     sys.stdout.flush()
return_code = mceff.wait()
(mout, merr) = mceff.communicate()
#print mout, '\n'
print merr, '\n'
"""
# sys.exit(0)

submit = Popen( ['/home/ballen/bin/condor-run', 'calcPurity.py', '-a', 'condorArgs.txt'], stdout = PIPE, stderr = PIPE )
for sout_line in iter(submit.stdout.readline, ''):
     sys.stdout.write(sout_line)
     sys.stdout.flush()
return_code = submit.wait()
(sout, serr) = submit.communicate()
# print sout, '\n'
print serr, '\n'
