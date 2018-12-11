#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True
import os
import math
import re
import collections
import shutil
import tempfile
import importlib

import ROOT

def makePlotter(plotConfig, group, sample, region, sourceDir, altSourceDir, lumi, printLevel, inputMux):
    plotter = ROOT.multidraw.MultiDraw()
    plotter.setInputMultiplexing(inputMux)
    plotter.setAbortOnReadError(True)

    sourceName = utils.getSkimPath(sample.name, region, sourceDir, altSourceDir)

    if os.path.exists(sourceName):
        plotter.addInputPath(sourceName)
    else:
        sourceNames = utils.getSkimPaths(sample.name, region, sourceDir, altSourceDir)

        if len(sourceNames) == 0:
            sys.stderr.write('File ' + sourceName + ' does not exist.\n')
            raise RuntimeError('InvalidSource')
        elif len(sourceNames) != len(sample.filesets()):
            sys.stderr.write('Not enough skim files for %s_%s.\n' % (sample.name, region))
            raise RuntimeError('InvalidSource')

        for nm in sourceNames:
            plotter.addInputPath(nm)

    # define expression aliases
    for name, expr in plotConfig.aliases.iteritems():
        plotter.addVariable(name, expr)

    # group-wide cut set as base filter
    if group.cut.strip():
        plotter.setFilter(group.cut.strip())

    cuts = []

    if group.altbaseline.strip():
        cuts.append('(' + group.altbaseline.strip() + ')')
    elif plotConfig.baseline.strip():
        cuts.append('(' + plotConfig.baseline.strip() + ')')

    baseSel = ' && '.join(cuts)

    if plotConfig.fullSelection.strip():
        cuts.append(plotConfig.fullSelection.strip())

    fullSel = ' && '.join(cuts)

    if printLevel > 0:
        print '      Baseline selection:', baseSel
        print '      Full selection:', fullSel

    if baseSel:
        plotter.addVariable('__baseline__', baseSel)
        plotter.addCut('baseline', '__baseline__[0]')
    else:
        plotter.addCut('baseline', '1.')

    if fullSel:
        plotter.addVariable('__fullSelection__', fullSel)
        plotter.addCut('fullSelection', '__fullSelection__[0]')
    else:
        plotter.addCut('fullSelection', '1.')

    for name, expr in plotConfig.cuts.iteritems():
        plotter.addCut(name, expr)

    if not sample.data:
        plotter.setConstantWeight(lumi)

    if group == plotConfig.obs:
        plotter.setPrescale(plotConfig.prescales[sample])

    if group.reweight:
        plotter.setReweight(group.reweight)

    plotter.setPrintLevel(printLevel)

    return plotter
    

def fillPlots(plotConfig, group, plotdefs, sourceDir, outFile, lumi = 0., postscale = 1., printLevel = 0, altSourceDir = '', inputMux = 1):
    if group.region:
        region = group.region
    else:
        region = plotConfig.name

    histograms = collections.OrderedDict() # {(sample, plotdef, variation, direction): histogram}

    # run the Plotter for each sample
    for sample in group.samples:
        dname = sample.name + '_' + region

        print '   ', dname

        plotter = makePlotter(plotConfig, group, sample, region, sourceDir, altSourceDir, lumi, printLevel, inputMux)
        varPlotters = {} # additional plotters for variations of sample type

        for plotdef in plotdefs:
            if not outFile.GetDirectory(plotdef.name):
                outFile.mkdir(plotdef.name)

            outDir = outFile.GetDirectory(plotdef.name + '/samples')
            if not outDir:
                outDir = outFile.GetDirectory(plotdef.name).mkdir('samples')

            hist = plotdef.makeHist(dname, outDir = outDir)
            histograms[(sample, plotdef, None, None)] = hist

            if group == plotConfig.obs and plotdef.fullyBlinded():
                continue

            if sample.data and plotdef.mcOnly:
                continue

            if plotdef.overflow:
                overflowMode = ROOT.multidraw.Plot1DFiller.kMergeLast
            else:
                overflowMode = ROOT.multidraw.Plot1DFiller.kDefault

            # nominal distribution
            plotter.addPlot(
                hist,
                plotdef.formExpression(),
                plotdef.cutName,
                plotdef.reweight,
                overflowMode
            )

            # systematic variations
            for variation in group.variations:
                for iv, direction in [(0, 'Up'), (1, 'Down')]:
                    hist = plotdef.makeHist(dname + '_' + variation.name + direction, outDir = outDir)
                    histograms[(sample, plotdef, variation, direction)] = hist
    
                    if type(variation.reweight) is str:
                        reweight = 'reweight_' + variation.reweight + direction
                    elif type(variation.reweight) is float:
                        reweight = str(1. + variation.reweight * (1. - 2. * iv))
                    else:
                        reweight = ''

                    if plotdef.reweight:
                        if reweight:
                            reweight = '(%s) * (%s)' % (reweight, plotdef.reweight)
                        else:
                            reweight = plotdef.reweight

                    if variation.cuts is not None:
                        reweight = ' && '.join(['(%s)' % s for s in (reweight, variation.cuts[iv].strip())])

                    if variation.replacements is not None:
                        expr = plotdef.formExpression(variation.replacements[iv])
                    else:
                        expr = plotdef.formExpression()

                    if variation.regions is not None:
                        try:
                            varPlotter = varPlotters[hist.GetName()]
                        except KeyError:
                            varPlotter = makePlotter(plotConfig, group, sample, variation.regions[iv], sourceDir, altSourceDir, lumi, printLevel, inputMux)
                            varPlotters[hist.GetName()] = varPlotter
                    else:
                        varPlotter = plotter

                    varPlotter.addPlot(
                        hist,
                        expr,
                        plotdef.cutName,
                        reweight,
                        overflowMode
                    )

        # setup complete. Fill all plots in one go
        if plotter.numObjs() != 0:
            plotter.execute()

        for varname, varPlotter in varPlotters.items():
            if varPlotter.numObjs() != 0:
                varPlotter.execute()

    if group.norm >= 0.:
        normalization = sum(hist.GetBinContent(1) for (_, plotdef, variation, direction), hist in histograms.items() if plotdef.name == 'count' and variation is None)

    for (sample, plotdef, variation, _), hist in histograms.items():
        # ad-hoc scaling
        if group.scale != 'data':
            hist.Scale(group.scale)

        if group.norm >= 0.:
            hist.Scale(group.norm / normalization)

        if sample.data and group != plotConfig.obs:
            # this is a data-driven background sample
            hist.Scale(postscale)

        # histograms is an ordered dict -> nominal histogram always comes before the variations
        if variation and variation.normalize and hist.GetSumOfWeights() > 0.:
            nominal = histograms[(sample, plotdef, None, None)]
            hist.Scale(nominal.GetSumOfWeights() / hist.GetSumOfWeights())

        # zero out negative bins
        hist, horig = cleanHist(hist)

        writeHist(hist)

        if horig is not None:
            horig.SetDirectory(hist.GetDirectory())
            writeHist(horig)

    # aggregate group plots

    # not for signal
    if group in plotConfig.sigGroups:
        return

    for plotdef in plotdefs:
        outDir = outFile.GetDirectory(plotdef.name)

        # simple sum of samples
        ghist = plotdef.makeHist(group.name, outDir = outDir)

        for sample in group.samples:
            shist = outDir.Get('samples/' + sample.name + '_' + region)
            ghist.Add(shist)

        if group == plotConfig.obs and plotdef.blind is not None:
            # take care of masking
            for iBin in range(1, ghist.GetNbinsX() + 1):
                binCenter = ghist.GetBinCenter(iBin)
                if (binCenter > plotdef.blind[0] and (plotdef.blind[1] == 'inf' or binCenter < plotdef.blind[1])):
                    ghist.SetBinContent(iBin, 0.)
                    ghist.SetBinError(iBin, 0.)

        writeHist(ghist)

        if group != plotConfig.obs:
            # write a group total histogram with systematic uncertainties added in quadrature (for display purpose only)
            outDir.cd()
            ghistSyst = ghist.Clone(group.name + '_syst')
    
            # variation Ups and Downs
            for variation in group.variations:
                uphist = plotdef.makeHist(group.name + '_' + variation.name + 'Up', outDir = outDir)
                downhist = plotdef.makeHist(group.name + '_' + variation.name + 'Down', outDir = outDir)
    
                for sample in group.samples:
                    if sample.data and plotdef.mcOnly:
                        continue

                    suphist = outDir.Get('samples/' + sample.name + '_' + region + '_' + variation.name + 'Up')
                    sdownhist = outDir.Get('samples/' + sample.name + '_' + region + '_' + variation.name + 'Down')
                    uphist.Add(suphist)
                    downhist.Add(sdownhist)

                if variation.normalize:
                    # individual sample variation plots are normalized to corresponding sample nominal already
                    # in the fringe case where sample variation has SumWeight of 0, the sample-level normalization
                    # does not work, leading to sum of SumWeights of variation samples not being equal to nominal
                    # total. We therefore re-normalize the variation at group level here.
                    if uphist.GetSumOfWeights() > 0.:
                        uphist.Scale(ghist.GetSumOfWeights() / uphist.GetSumOfWeights())
                    if downhist.GetSumOfWeights() > 0.:
                        downhist.Scale(ghist.GetSumOfWeights() / downhist.GetSumOfWeights())

                writeHist(uphist)
                writeHist(downhist)
                
                # add the average variation as systematics
                uphist.Add(downhist, -1.)
                uphist.Scale(0.5)
    
                for iX in range(1, ghist.GetNbinsX() + 1):
                    err = math.sqrt(math.pow(ghistSyst.GetBinError(iX), 2.) + math.pow(uphist.GetBinContent(iX), 2.))
                    if err > ghistSyst.GetBinContent(iX):
                        err = ghistSyst.GetBinContent(iX)

                    ghistSyst.SetBinError(iX, err)
    
            writeHist(ghistSyst)


# zero out negative bins (save the original as _orig)
def cleanHist(hist):
    horig = None
    for iX in range(1, hist.GetNbinsX() + 1):
        if hist.GetBinContent(iX) < 0.:
            if horig is None:
                # print '      Adjusting bin contents of', plotdef.name, hist.GetName(), 'to be non-negative'
                horig = hist.Clone(hist.GetName() + '_original')

            hist.SetBinContent(iX, 0.)
            hist.SetBinError(iX, 0.)

        elif hist.GetBinContent(iX) - hist.GetBinError(iX) < 0.:
            if horig is None:
                # print '      Adjusting bin errors of', plotdef.name, hist.GetName(), 'to be non-negative'
                horig = hist.Clone(hist.GetName() + '_original')

            hist.SetBinError(iX, hist.GetBinContent(iX))

    return hist, horig

# python deletes histograms when variables are overwritten unless someone references the object
objectstore = []
def writeHist(hist):
    global ROOT
    if not hist.GetDirectory() or not hist.GetDirectory().GetFile():
        # we don't have a persistent storage
        objectstore.append(hist)
        return

    gd = ROOT.gDirectory
    hist.GetDirectory().cd()
    hist.Write()
    gd.cd()


def formatHist(hist, plotdef):
    # Label the axes and normalize bin contents by width
    if plotdef.ndim() == 1:
        # we decided to merge the overflow into last bin content
        # if plotdef.overflow:
        #     nbins = hist.GetNbinsX() - 1
        # else:
        #     nbins = hist.GetNbinsX()

        nbins = hist.GetNbinsX()

        for iX in range(1, nbins + 1):
            cont = hist.GetBinContent(iX)
            err = hist.GetBinError(iX)
            w = hist.GetXaxis().GetBinWidth(iX)
            if plotdef.unit:
                hist.SetBinContent(iX, cont / w)
                hist.SetBinError(iX, err / w)
            else:
                if iX == 1:
                    wnorm = w

                hist.SetBinContent(iX, cont / (w / wnorm))
                hist.SetBinError(iX, err / (w / wnorm))

    hist.GetXaxis().SetTitle(plotdef.xtitle())
    hist.GetYaxis().SetTitle(plotdef.ytitle(binNorm = True))

    if plotdef.ndim() != 1:
        hist.GetZaxis().SetTitle('Events')
        hist.SetMinimum(0.)


def printCounts(counters, plotConfig):
    prec = '%.2f'

    # Print out the predictions and yield
    bkgTotal = 0.
    bkgTotalErr2 = 0.

    selection = plotConfig.baseline
    if plotConfig.fullSelection:
        if selection:
            selection += ' && ' + plotConfig.fullSelection
        else:
            selection = plotConfig.fullSelection

    print 'Yields for ' + selection

    for group in reversed(plotConfig.bkgGroups):
        counter = counters[group.name]
        count = counter.GetBinContent(1)
        err = counter.GetBinError(1)

        bkgTotal += count
        bkgTotalErr2 += math.pow(err, 2.)

        print ('%+12s  ' + prec + ' +- ' + prec) % (group.name, count, err)
    
    print '---------------------'
    print ('%+12s  ' + prec + ' +- ' + prec) % ('bkg', bkgTotal, math.sqrt(bkgTotalErr2))
    
    print '====================='
    
    for sspec in plotConfig.signalPoints:
        counter = counters[sspec.name]
        print ('%+12s  ' + prec + ' +- ' + prec) % (sspec.name, counter.GetBinContent(1), counter.GetBinError(1))
        # print ('%+12s  ' + prec + ' +- ' + prec + '  S/sqrt(B): ' + prec) % (sspec.name, counter.GetBinContent(1), counter.GetBinError(1), counter.GetBinContent(1) / math.sqrt(bkgTotal) )

    if 'data_obs' in counters:
        print '====================='
        print '%+12s  %d' % ('data_obs', int(counters['data_obs'].GetBinContent(1)))
    

def printBinByBin(stack, plotdef, plotConfig, precision = '.2f'):
    obs = stack['data_obs']
    nBins = obs.GetNbinsX()

    boundaries = []
    for iX in range(1, nBins + 1):
        boundaries.append('%12s' % ('[%.1f, %.1f]' % (obs.GetXaxis().GetBinLowEdge(iX), obs.GetXaxis().GetBinUpEdge(iX))))
    boundaries.append('%12s' % 'total')

    print 'Bin-by-bin yield for plot', plotdef.name
    print '           ' + ' '.join(boundaries)
    print '===================================================================================='

    bkgTotal = [0.] * nBins

    for group in reversed(plotConfig.bkgGroups):
        yields = []
        for iX in range(1, nBins + 1):
            cont = stack[group.name].GetBinContent(iX)
            yields.append(cont)
            bkgTotal[iX - 1] += cont

        print ('%+12s' % group.name), ' '.join([('%12' + precision) % y for y in yields]), (('%12' + precision) % sum(yields))

    print '------------------------------------------------------------------------------------'
    print ('%+12s' % 'total'), ' '.join([('%12' + precision) % b for b in bkgTotal]), (('%12' + precision) % sum(bkgTotal))
    print '===================================================================================='

    yields = []
    for iX in range(1, nBins + 1):
        cont = obs.GetBinContent(iX)
        yields.append(int(round(cont)))

    print ('%+12s' % 'data_obs'), ' '.join(['%12d' % y for y in yields]), ('%12d' % sum(yields))


def printChi2(stack, plotdef, plotConfig, precision = '.2f'):
    obs = stack['data_obs']
    nBins = obs.GetNbinsX()

    residuals = [0.] * nBins
    err2s = [0.] * nBins
    for iX in range(1, nBins + 1):
        o = obs.GetBinContent(iX) * obs.GetXaxis().GetBinWidth(iX)
        residuals[iX - 1] = o
        err2s[iX - 1] = o
        
        for group in plotConfig.bkgGroups:
            x = stack[group.name].GetBinContent(iX) * obs.GetXaxis().GetBinWidth(iX)
            e = stack[group.name].GetBinError(iX) * obs.GetXaxis().GetBinWidth(iX)

            residuals[iX - 1] -= x
            err2s[iX - 1] += e * e

    chi2 = 0.
    for iR, res in enumerate(residuals):
        if err2s[iR] == 0.:
            continue

        chi2 += res * res / err2s[iR]

    print 'Chi2 for plot ' + plotdef.name + ': ' + str(chi2 / (nBins - 1))


def printCanvas(canvas, plotdef, plotConfig, plotDir):
    """
    Print the canvas content as pdf and png.
    """

    eil = ROOT.gErrorIgnoreLevel
    ROOT.gErrorIgnoreLevel = ROOT.kWarning

    canvas.xtitle = plotdef.xtitle()
    canvas.ytitle = plotdef.ytitle(binNorm = True)

    canvas.selection = plotdef.cutName

    if plotdef.logy is None:
        logy = True
        addLinear = True
    else:
        logy = plotdef.logy
        addLinear = False

    canvas.ylimits = (plotdef.ymin, plotdef.ymax)
    canvas.Update(logy = logy)

    if plotdef.fullyBlinded():
        # remove ratio pad. Hack to use SimpleCanvas interface
        simple = SimpleCanvas(lumi = canvas.lumi)

        garbage = []
        cnv = ROOT.TCanvas('tmp', 'tmp', 600, 600)
        cnv.cd()

        plotPad = canvas.plotPad.DrawClone()
        garbage.append(plotPad)
        plotPad.SetTopMargin(simple.canvas.GetTopMargin())
        plotPad.SetRightMargin(simple.canvas.GetRightMargin())
        plotPad.SetBottomMargin(simple.canvas.GetBottomMargin())
        plotPad.SetLeftMargin(simple.canvas.GetLeftMargin())

        xaxis = canvas.xaxis.DrawClone()
        garbage.append(xaxis)
        xaxis.SetX1(simple.canvas.GetLeftMargin())
        xaxis.SetX2(1. - simple.canvas.GetRightMargin())
        xaxis.SetY1(simple.canvas.GetBottomMargin())
        xaxis.SetY2(simple.canvas.GetBottomMargin())

        yaxis = canvas.yaxis.DrawClone()
        garbage.append(yaxis)
        yaxis.SetX1(simple.canvas.GetLeftMargin())
        yaxis.SetX2(simple.canvas.GetLeftMargin())
        yaxis.SetY1(simple.canvas.GetBottomMargin())
        yaxis.SetY2(1. - simple.canvas.GetTopMargin())

        simple.canvas.IsA().Destructor(simple.canvas)
        simple.canvas = cnv
        simple._needUpdate = False
        simple.printWeb(plotDir, plotdef.name)

        sys.stdout.write('    main')
        if logy:
            sys.stdout.write(' (log)')
        else:
            sys.stdout.write(' (lin)')

        if addLinear:
            plotPad.SetLogy(False)
            plotPad.Update()
            yaxis.SetOption('')
            yaxis.SetWmin(plotPad.GetUymin())
            yaxis.SetWmax(plotPad.GetUymax())
            simple.printWeb(plotDir, plotdef.name + 'Linear', logy = False)

            sys.stdout.write(' (lin)')

        sys.stdout.write('\n')
        sys.stdout.flush()

        # cleanup the mess
        for obj in garbage:
            obj.IsA().Destructor(obj)

        cnv.IsA().Destructor(cnv)

    else:
        # normal, (partially) unblinded distributions
        canvas.printWeb(plotDir, plotdef.name, drawLegend = False)

        sys.stdout.write('    main')
        if logy:
            sys.stdout.write(' (log)')
        else:
            sys.stdout.write(' (lin)')

        if addLinear:
            canvas.ylimits = (0., -1.)
            canvas.minimum = -1.
            plotdef.ymax = -1.
            plotdef.ymin = 0.
            canvas._needUpdate = True
            canvas.printWeb(plotDir, plotdef.name + 'Linear', logy = False)

            sys.stdout.write(' (lin)')

        sys.stdout.write('\n')
        sys.stdout.flush()

    ROOT.gErrorIgnoreLevel = eil


def removeBaskets(dir_in, dir_out):
    # Use of alias leaves orphan baskets in the output file
    for key in dir_in.GetListOfKeys():
        if key.GetClassName() == 'TDirectoryFile':
            removeBaskets(dir_in.GetDirectory(key.GetName()), dir_out.mkdir(key.GetName()))
            continue

        obj = key.ReadObj()
        if obj.InheritsFrom(ROOT.TH1.Class()):
            dir_out.cd()
            clone = obj.Clone()
            clone.Write()


if __name__ == '__main__':

    from argparse import ArgumentParser
    
    argParser = ArgumentParser(description = 'Plot and count')
    argParser.add_argument('config', metavar = 'CONFIG', help = 'Plot config name.')
    argParser.add_argument('--all-signal', '-S', action = 'store_true', dest = 'allSignal', help = 'Write histogram for all signal points.')
    argParser.add_argument('--asimov', '-v', metavar = '(background|<signal>)', dest = 'asimov', help = 'Plot the total background or signal + background as the observed distribution. For signal + background, give the signal point name.')
    argParser.add_argument('--use-variation', '-z', metavar = 'GROUP:VARIATION', dest = 'asimov_variation', nargs = '+', default = [], help = 'Use with --asimov option to inject variation of the group to the pseudo-data instead of nominal.')
    argParser.add_argument('--bin-by-bin', '-y', metavar = 'PLOT', dest = 'bbb', default = '', help = 'Print out bin-by-bin breakdown of the backgrounds and observation.')
    argParser.add_argument('--blind', '-B', action = 'store_true', dest = 'blind', help = 'Do not plot the observed distribution at all.')
    argParser.add_argument('--unblind', '-U', action = 'store_true', dest = 'unblind', help = 'Ignore the blind option of plot configs.')
    argParser.add_argument('--chi2', '-x', metavar = 'PLOT', dest = 'chi2', default = '', help = 'Compute the chi2 for the plot.')
    argParser.add_argument('--clear-dir', '-R', action = 'store_true', dest = 'clearDir', help = 'Clear the plot directory first.')
    argParser.add_argument('--hist-file', '-o', metavar = 'PATH', dest = 'histFile', default = '', help = 'Histogram output file.')
    argParser.add_argument('--list-samples', '-L', action = 'store_true', dest = 'listSamples', help = 'List the samples in the given plot config and exit.')
    argParser.add_argument('--plot', '-p', metavar = 'NAME', dest = 'plots', nargs = '+', default = [], help = 'Limit plotting to specified set of plots.')
    argParser.add_argument('--plot-dir', '-d', metavar = 'PATH', dest = 'plotDir', default = '', help = 'Specify a directory under {webdir} to save images. Use "-" for no output.')
    argParser.add_argument('--print-level', '-m', metavar = 'LEVEL', dest = 'printLevel', type = int, default = 0, help = 'Verbosity of the script.')
    argParser.add_argument('--replot', '-P', action = 'store_true', dest = 'replot', default = '', help = 'Do not fill histograms. Need --hist-file.')
    argParser.add_argument('--skim-dir', '-i', metavar = 'PATH', dest = 'skimDir', help = 'Input skim directory.')
    argParser.add_argument('--multiplex', '-j', metavar = 'N', dest = 'inputMux', type = int, default = 1, help = 'Run MultiDraw with input multiplexing.')
    
    args = argParser.parse_args()
    sys.argv = []

    import ROOT
    ROOT.gROOT.SetBatch(True)

    from plotstyle import WEBDIR, SimpleCanvas, DataMCCanvas
    import config
    import utils
    import main.plotutil as plotutil
    plotutil.confName = args.config

    # Fill plotConfig parameters based on plotutil.confName
    importlib.import_module('configs.' + config.config + '.plotconfig')

    ##################################
    ## PARSE COMMAND-LINE ARGUMENTS ##
    ##################################

    if args.skimDir:
        localSkimDir = ''
    else:
        args.skimDir = config.skimDir
        localSkimDir = config.localSkimDir

    plotConfig = plotutil.plotConfig

    if args.listSamples:
        print 'Obs:', ' '.join('%s_%s' % (s.name, plotConfig.name) for s in plotConfig.obs.samples)
        bkg = []
        for group in plotConfig.bkgGroups:
            if group.region:
                bkg += ['%s_%s' % (s.name, group.region) for s in group.samples]
            else:
                bkg += ['%s_%s' % (s.name, plotConfig.name) for s in group.samples]
        print 'Bkg:', ' '.join(bkg)

        if args.allSignal:
            sig = []
            for group in plotConfig.sigGroups:
                if group.region:
                    sig += ['%s_%s' % (s.name, group.region) for s in group.samples]
                else:
                    sig += ['%s_%s' % (s.name, plotConfig.name) for s in group.samples]
        else:
            sig = ['%s_%s' % (sdef.sample.name, plotConfig.name) for sdef in plotConfig.signalPoints]
        print 'Sig:', ' '.join(sig)

        sys.exit(0)

    if args.bbb:
        plotdefs = [plotConfig.getPlot(args.bbb)]
    elif args.chi2:
        plotdefs = [plotConfig.getPlot(args.chi2)]
    elif len(args.plots) != 0:
        plotdefs = set()
        if 'sensitive' in args.plots:
            plotdefs.update([plot for plot in plotConfig.getPlots() if plot.sensitive])
            args.plots.remove('sensitive')

        if 'insensitive' in args.plots:
            plotdefs.update([plot for plot in plotConfig.getPlots() if not plot.sensitive])
            plotConfig.getPlot('count').blind = 'full'
            args.plots.remove('insensitive')

        if len(args.plots) != 0:
            plotdefs.update(plotConfig.getPlots(args.plots))

        plotdefs = list(plotdefs)
    else:
        plotdefs = plotConfig.getPlots()

    if plotConfig.getPlot('count') not in plotdefs:
        plotdefs.append(plotConfig.getPlot('count'))

    plotNames = [p.name for p in plotdefs]

    for plotdef in plotdefs:
        if plotdef.sensitive and plotdef.blind is None:
            plotdef.blind = 'full'

    if args.unblind:
        for plotdef in plotdefs:
            plotdef.blind = None

    if args.blind:
        for plotdef in plotdefs:
            plotdef.blind = 'full'

    if args.histFile:
        if args.replot:
            histFile = ROOT.TFile.Open(args.histFile)
        else:
            histFile = ROOT.TFile.Open(args.histFile, 'recreate')

    else:
        if args.allSignal:
            print '--all-signal set but no output file is given.'
            sys.exit(1)

        if args.replot:
            print '--replot requires a --hist-file.'
            sys.exit(1)

        histFile = ROOT.gROOT

    if args.asimov:
        if args.asimov == 'background':
            pass
        elif args.asimov in [s.name for s in plotConfig.signalPoints]:
            pass
        else:
            print 'Invalid value for option --asimov.'
            sys.exit(1)

    ############################
    ## SET UP FROM PLOTCONFIG ##
    ############################

    fullLumi = plotConfig.fullLumi()
    effLumi = plotConfig.effLumi()

    #####################################
    ## FILL HISTOGRAMS FROM SKIM TREES ##
    #####################################

    if not args.replot:
        ROOT.gSystem.Load(config.libmultidraw)
    
        print 'Filling plots for %s..' % plotConfig.name

        # for data-driven background estimates under presence of prescales
        # multiply the yields by postscale
        postscale = effLumi / fullLumi
    
        groups = list(plotConfig.bkgGroups)
        if args.allSignal:
            groups += plotConfig.sigGroups
        else:
            for sspec in plotConfig.signalPoints:
                if sspec.group not in groups:
                    groups.append(sspec.group)
                    sspec.group.samples = []
    
                sspec.group.samples.append(sspec.sample)

        if not args.asimov:
            # if args.asimov, we'll make the data_obs plot below
            groups.append(plotConfig.obs)
    
        for group in groups:
            print ' ', group.name

            fillPlots(plotConfig, group, plotdefs, args.skimDir, histFile, lumi = effLumi, postscale = postscale, printLevel = args.printLevel, altSourceDir = localSkimDir, inputMux = args.inputMux)
   
        # Save a background total histogram (for display purpose) for each plotdef
        for plotdef in plotdefs:
            outDir = histFile.GetDirectory(plotdef.name)

            bkghist = plotdef.makeHist('bkgtotal', outDir = outDir)
            bkghistSyst = plotdef.makeHist('bkgtotal_syst', outDir = outDir)

            for group in plotConfig.bkgGroups:
                bkghist.Add(outDir.Get(group.name))
                bkghistSyst.Add(outDir.Get(group.name + '_syst'))
    
            writeHist(bkghist)
            writeHist(bkghistSyst)

            if args.asimov:
                asimov = bkghist.Clone('asimov')

                # generate the "observed" distribution from background total
                for varspec in args.asimov_variation:
                    # example: fakemet:fakemetShapeUp:5
                    words = varspec.split(':')
                    gname, varname = words[:2]
                    if len(words) > 2:
                        scale = float(words[2])
                    else:
                        scale = 1.

                    nominal = outDir.Get(gname)
                    if varname:
                        varhist = outDir.Get(gname + '_' + varname)
                    else:
                        varhist = nominal
                    
                    if not nominal or not varhist:
                        print 'Invalid variation specified for pseudo-data:', varspec
                        continue

                    asimov.Add(nominal, -1.)
                    asimov.Add(varhist, scale)

                if args.asimov != 'background':
                    sighist = outDir.Get('samples/' + args.asimov + '_' + plotConfig.name)
                    asimov.Add(sighist)

                # make data_obs here
                obshist = plotdef.makeHist('data_obs', outDir = outDir)

                for iBin in xrange(1, asimov.GetNbinsX() + 1):
                    x = asimov.GetXaxis().GetBinCenter(iBin)
                    for _ in xrange(int(round(asimov.GetBinContent(iBin)))):
                        obshist.Fill(x)

                writeHist(obshist)

        if args.histFile:
            # purge orphan baskets
            tmpPath = tempfile.mkdtemp()
            tmpout = ROOT.TFile.Open(tmpPath + '/hist.root', 'recreate')
            removeBaskets(histFile, tmpout)
            histFile.Close()
            tmpout.Close()
            os.unlink(args.histFile)
            shutil.copyfile(tmpPath + '/hist.root', args.histFile)
            shutil.rmtree(tmpPath)

            # reopen the output file
            histFile = ROOT.TFile.Open(args.histFile)

    # closes if not args.replot


    ####################
    ## DRAW / ANALYZE ##
    ####################

    if args.plotDir == '-' and not ('count' in plotNames or args.bbb or args.chi2):
        # nothing to do
        sys.exit(0)

    print 'Drawing plots..'

    canvas = DataMCCanvas()

    nentries = (1 + len(plotConfig.bkgGroups) + len(plotConfig.signalPoints))
    ncolumns = math.ceil(float(nentries) / 5.) 
    xmin = 0.35 if ncolumns > 2 else 0.55
    canvas.legend.setPosition(xmin, SimpleCanvas.YMAX - 0.01 - 0.035 * 5, 0.92, SimpleCanvas.YMAX - 0.01)

    if args.plotDir:
        if args.plotDir == '-':
            plotDir = ''
        else:
            plotDir = args.plotDir
            if plotDir.startswith(plotstyle.WEBDIR):
                plotDir = plotDir.replace(plotstyle.WEBDIR, '')
    else:
        plotDir = config.config + '/' + args.config

    if plotDir and args.clearDir:
        for plot in os.listdir(WEBDIR + '/' + plotDir):
            os.remove(WEBDIR + '/' + plotDir + '/' + plot)

    for plotdef in plotdefs:
        if plotdef.name != 'count' and plotdef.name != args.bbb and plotdef.name != args.chi2:
            graphic = True
        else:
            graphic = False

        if not plotDir and graphic:
            # nothing to do
            continue

        print ' ', plotdef.name

        if graphic:
            if plotdef.ndim() == 1:
                drawOpt = 'HIST'
            elif plotdef.ndim() == 2:
                drawOpt = 'LEGO4 F 0'

            # set up canvas
            canvas.Clear(full = True)

            isSensitive = plotdef.sensitive

        else:
            counters = {}
            isSensitive = True
    
        if isSensitive:
            canvas.lumi = effLumi
            # for data-driven background estimates under presence of prescales
            # multiply the yields by 1/postscale
            postscale = fullLumi / effLumi
        else:
            canvas.lumi = fullLumi
            postscale = 1.

        inDir = histFile.GetDirectory(plotdef.name)

        # observed distributions
        obshist = inDir.Get('data_obs')

        # deal with the special case of fill-to-data scaling
        fillToDataScale = 1.
        if obshist and not plotdef.mcOnly:
            othersTotal = 0.
            scaledTotal = 0.
            for group in plotConfig.bkgGroups:
                ghist = inDir.Get(group.name + '_syst')
    
                if group.scale == 'data':
                    scaledTotal += ghist.GetSumOfWeights()
                else:
                    othersTotal += ghist.GetSumOfWeights()
    
            if scaledTotal != 0.:
                fillToDataScale = (obshist.GetSumOfWeights() - othersTotal) / scaledTotal

        # fetch and format background groups
        for group in plotConfig.bkgGroups:
            ghist = inDir.Get(group.name + '_syst')

            if group.scale == 'data':
                # special case - scaling this group to data (for shape comparison)
                ghist.Scale(fillToDataScale)

            if graphic:
                formatHist(ghist, plotdef)
                title = group.title
                if group.scale == 'data':
                    title += ' (norm. to obs)'
                elif group.scale != 1.:
                    title += (' #times %.1f' % group.scale)
                canvas.addStacked(ghist, title = title, color = group.color, drawOpt = drawOpt)
            else:
                counters[group.name] = ghist

        # background total used for uncertainty display
        bkgTotal = inDir.Get('bkgtotal_syst')
        if graphic:
            formatHist(bkgTotal, plotdef)

        # plot signal distributions for sensitive plots
        if isSensitive:
            for sspec in plotConfig.signalPoints:
                shist = inDir.Get('samples/' + sspec.name + '_' + plotConfig.name)

                if graphic:
                    formatHist(shist, plotdef)
                    title = sspec.title
                    if sspec.group.scale != 1. and group.scale != 'data':
                        title += (' #times %.1f' % sspec.group.scale)
                    canvas.addSignal(shist, title = title, color = sspec.color, drawOpt = drawOpt)
                else:
                    counters[sspec.name] = shist

        if obshist:
            if graphic:
                formatHist(obshist, plotdef)
                canvas.addObs(obshist, title = plotConfig.obs.title)
            else:    
                counters['data_obs'] = obshist

        if plotdef.name == 'count':
            printCounts(counters, plotConfig)
        elif plotdef.name == args.bbb:
            printBinByBin(counters, plotdef, plotConfig)
        elif plotdef.name == args.chi2:
            printChi2(counters, plotdef, plotConfig)
        else:
            if args.asimov:
                plotdef.name += args.asimov.capitalize()

            printCanvas(canvas, plotdef, plotConfig, plotDir)
