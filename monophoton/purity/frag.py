import os, sys
import ROOT as r
from selections import Version

varName = 'sieie'
versDir = os.path.join('/scratch5/ballen/hist/purity',Version,varName)
skimDir  = os.path.join(versDir,'Skims')

fileName = os.path.join(skimDir, 'TempSignalGJets.root')
fileSignalGJets = r.TFile(fileName)
treeSignalGJets = fileSignalGJets.Get('skimmedEvents')

hDirect = r.TH1F("hdirect", "hdirect", 120, -2., 10.)
hFrag = r.TH1F("hfrag", "hfrag", 120, -2., 10.)

dR = 0.5
'''
baseSel = "weight * ( (selPhotons.isEB && selPhotons.medium && selPhotons.pt > 170)"+' &&  (TMath::Abs(selPhotons.matchedGen) == 22) && (!selPhotons.hadDecay)'
directSel =  baseSel+' && (selPhotons.drParton > '+str(dR)+') )'
fragSel =  baseSel+' && !(selPhotons.drParton > '+str(dR)+') && !(selPhotons.drParton < 0) )'
'''
baseSel = "weight * ( (selPhotons.isEB[0] && selPhotons.medium[0] && selPhotons.pt[0] > 170)"+' &&  (TMath::Abs(selPhotons.matchedGen[0]) == 22) && (!selPhotons.hadDecay[0])'
directSel = baseSel+' ) '
fragSel = baseSel+" && (selPhotons.isEB[1] && selPhotons.medium[1] && selPhotons.pt[1] > 30)"+' &&  (TMath::Abs(selPhotons.matchedGen[1]) == 22) && (!selPhotons.hadDecay[1]) )'
#directSel =  baseSel+' && (selPhotons[0].drParton > '+str(dR)+') )'
#fragSel =  baseSel+' && !(selPhotons[0].drParton > '+str(dR)+') && !(selPhotons[0].drParton < 0) )'


print "Selecting direct photons with selection:", directSel
treeSignalGJets.Draw("selPhotons.drParton>>hdirect",directSel)
print "Selecting fragmentation photons with selection:", fragSel
treeSignalGJets.Draw("selPhotons.drParton>>hfrag",fragSel)

nDirect = hDirect.Integral()
nFrag = hFrag.Integral()
nTotal = nDirect + nFrag
print "Number of direct photons:", nDirect
print "Number of fragmentation photons:", nFrag
print "Number of total photons:", nTotal

rDirect = nDirect / nTotal
rFrag = nFrag / nTotal
print "Fraction of direct photons:", rDirect
print "Fraction of fragmentation photons:", rFrag
