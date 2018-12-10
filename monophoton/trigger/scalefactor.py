# Trigger efficiency scale factors
#   scalefactor.py object mname1 mname2

import sys
import os
import ROOT
ROOT.gROOT.SetBatch(True)

from plotstyle import SimpleCanvas
import config

tconf = importlib.import_module('configs.' + config.config + '.trigger')
measurements = tconf.measurements
confs = tconf.confs
fitconfs = tconf.fitconfs

oname, mname1, mname2 = sys.argv[1:4]
if len(sys.argv) > 4:
    fit_targ = sys.argv[4]
    formula = sys.argv[5]
    fit_range = tuple(map(float, sys.argv[6].split(',')))
    params = tuple(map(float, sys.argv[7].split(',')))
else:
    fit_targ = None

outName = 'trigger'
outDir = config.histDir + '/trigger'

if (oname, mname1) not in measurements or (oname, mname2) not in measurements:
    print 'Invalid object or measurement name'
    sys.exit(1)

canvas = SimpleCanvas()
canvas.legend.setPosition(0.7, 0.3, 0.9, 0.5)

numerSource = ROOT.TFile.Open(outDir + '/trigger_efficiency_%s_%s.root' % (oname, mname1))
denomSource = ROOT.TFile.Open(outDir + '/trigger_efficiency_%s_%s.root' % (oname, mname2))

outputFile = ROOT.TFile.Open(outDir + '/scalefactor_%s_%s_%s.root' % (oname, mname1, mname2), 'recreate')

for tname, (_, _, title, variables) in confs[oname].items():
    for vname, (vtitle, _, _, binning) in variables.items():
        npass = numerSource.Get(tname + '/' + vname + '_pass')
        nbase = numerSource.Get(tname + '/' + vname + '_base')
        dpass = denomSource.Get(tname + '/' + vname + '_pass')
        dbase = denomSource.Get(tname + '/' + vname + '_base')
        
        if not npass or not nbase or not dpass or not dbase:
            print tname, vname, 'not in source'
            continue
    
        sf = ROOT.TGraphErrors(npass.GetNbinsX())

        iP = 0
        for iX in range(1, npass.GetNbinsX() + 1):
            np = npass.GetBinContent(iX)
            nb = nbase.GetBinContent(iX)
            dp = dpass.GetBinContent(iX)
            db = dbase.GetBinContent(iX)

            x = npass.GetXaxis().GetBinCenter(iX)

            if nb > 0.:
                ncent = np / nb
                nerr = ncent - ROOT.TEfficiency.ClopperPearson(int(nb), int(np), 0.6827, False)
            else:
                ncent = 0.
                nerr = 0.

            if db > 0. and dp > 0.:
                dcent = dp / db
                # denom is typically MC - not using stat error
                #derr = dcent - ROOT.TEfficiency.ClopperPearson(nb, np, 0.6827, False)
                sf.SetPoint(iP, x, ncent / dcent)
                sf.SetPointError(iP, 0., nerr / dcent)
                iP += 1

        sf.Set(iP)

        outputFile.cd()
        sf.Write(tname + '_'+ vname)

        # PLOT

        canvas.Clear()
        canvas.SetGrid()
        
        canvas.legend.Clear()
        if title:
            canvas.legend.add('sf', title = title, opt = 'LP', color = ROOT.kBlack, mstyle = 8)
            canvas.legend.apply('sf', sf)
        else:
            sf.SetMarkerColor(ROOT.kBlack)
            sf.SetMarkerStyle(8)
        
        canvas.addHistogram(sf, drawOpt = 'EP')

        if tname + '_' + vname == fit_targ:
            func = ROOT.TF1('fitfunc', formula, *fit_range)
            if len(params) > 1:
                func.SetParameters(*params)
            else:
                func.SetParameter(0, params[0])
            sf.Fit(func, "", "", *fit_range)
            canvas.addHistogram(func, drawOpt = '')
        
        canvas.xtitle = vtitle
        canvas.ylimits = (0.8, 1.2)
        
        canvas.Update()
        
        if type(binning) is tuple:
            canvas.addLine(binning[0], 1., binning[2], 1., style = ROOT.kDashed)
            sf.GetXaxis().SetLimits(binning[1], binning[2])
        else:
            canvas.addLine(binning[0], 1., binning[-1], 1., style = ROOT.kDashed)
            sf.GetXaxis().SetLimits(binning[0], binning[-1])
        
        sf.GetYaxis().SetRangeUser(0.8, 1.2)
        
        canvas.printWeb(outName, 'sf_' + oname + '_' + mname1 + '_' + mname2 + '_' + tname + '_' + vname, logy = False)
