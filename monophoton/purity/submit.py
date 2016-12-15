#!/usr/bin/env python

import sys
import os
import shutil
from subprocess import Popen, PIPE

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
import selections as s

scratchPath = '/data/t3home000/ballen/hist/purity/'+s.Version

argFile = file('condorArgs.txt', 'w')

PhotonIds = [ 'none' ]
for base in ['loose', 'medium', 'tight', 'highpt']:
     PhotonIds += [ base, base+'-pixel', base+'-pixel-monoph' ]

#print sorted(s.PhotonPtSels.keys())
#print sorted(s.MetSels.keys())
#sys.exit(0)

for era in s.Eras:
    for loc in s.Locations[:1]:
        for pt in sorted(s.PhotonPtSels.keys())[:]:
            for met in sorted(s.MetSels.keys())[:1]:
                for sel in PhotonIds:
                    outDir = scratchPath + '/' + era + '_' + loc + '_' + sel + '_' + pt + '_' + met

                    if not os.path.exists(outDir):
                        os.makedirs(outDir)

                    argFile.write(loc + ' ' + sel + ' ' + pt.replace('PhotonPt', '') + ' ' + met.replace('Met', '') + ' ' + era + ' \n')

argFile.close()

mceff = Popen( ['/home/ballen/bin/condor-run', 'calcMcEff.py', '-a', 'condorArgs.txt', '-c', '10'], stdout = PIPE, stderr = PIPE )
for mout_line in iter(mceff.stdout.readline, ''):
     sys.stdout.write(mout_line)
     sys.stdout.flush()
return_code = mceff.wait()
(mout, merr) = mceff.communicate()
#print mout, '\n'
print merr, '\n'

submit = Popen( ['/home/ballen/bin/condor-run', 'bkgdstats.py', '-a', 'condorArgs.txt', '-c', '6'], stdout = PIPE, stderr = PIPE )
for sout_line in iter(submit.stdout.readline, ''):
     sys.stdout.write(sout_line)
     sys.stdout.flush()
return_code = submit.wait()
(sout, serr) = submit.communicate()
# print sout, '\n'
print serr, '\n'
