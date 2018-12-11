import array
import copy
import re
import collections
import ROOT

from datasets import allsamples

class GroupSpec(object):
    def __init__(self, name, title, samples = [], region = '', count = 0., color = ROOT.kBlack, altbaseline = '', cut = '', scale = 1., reweight = '', norm = -1.):
        self.name = name
        self.title = title
        self.samples = samples
        self.region = region
        self.count = count
        self.color = color
        self.scale = scale # use for ad-hoc scaling of histograms
        self.reweight = reweight # use for ad-hoc reweighting
        self.cut = cut # additional cut (if samples are looser than the nominal region, e.g. to allow variations)
        self.altbaseline = altbaseline # use to replace baseline cut (hack for using lowdphi gjets shape in SR)
        self.norm = norm # use to normalize histograms post-fill. Set to the expected number of events after full selection
        self.variations = []

    def addVariation(self, name, **kwd):
        self.variations.append(Variation(name, **kwd))


class SampleSpec(object):
    # use for signal point spec

    def __init__(self, name, title, group, color = ROOT.kBlack):
        self.name = name
        self.sample = allsamples[self.name]
        self.title = title
        self.group = group
        self.color = color


class PlotDef(object):
    def __init__(self, name, title, expr, binning, unit = '', cutName = 'baseline', reweight = '', blind = None, sensitive = False, overflow = False, mcOnly = False, logy = None, ymax = -1., ymin = 0.):
        self.name = name
        self.title = title
        self.unit = unit
        self.expr = expr # expression to plot
        self.cutName = cutName # Name of the cut the plot belongs to
        self.reweight = reweight
        self.binning = binning
        self.blind = blind # 'full' or a range in 2-tuple. Always takes effect if set.
        self.sensitive = sensitive # whether to add signal distributions + prescale observed
        self.overflow = overflow # add overflow bin
        self.mcOnly = mcOnly # plotting MC-only quantity
        self.logy = logy
        self.ymax = ymax
        self.ymin = ymin

    def clone(self, name, **keywords):
        for vname in ['title', 'unit', 'expr', 'cutName', 'binning', 'blind', 'overflow', 'logy', 'ymax', 'sensitive']:
            if vname not in keywords:
                keywords[vname] = copy.copy(getattr(self, vname))

        vardef = PlotDef(name, **keywords)

        return vardef

    def ndim(self):
        if type(self.expr) is tuple:
            return len(self.expr)
        else:
            return 1

    def xlimits(self):
        if self.ndim() == 1:
            binning = self.binning
        else:
            binning = self.binning[0]

        if type(binning) is list:
            return binning[0], binning[-1]
        elif type(binning) is tuple:
            return binning[1], binning[2]
    
    def fullyBlinded(self):
        if not self.blind:
            return False

        if self.blind == 'full':
            return True

        xlow, xhigh = self.xlimits()
        return self.blind[0] <= xlow and self.blind[1] >= xhigh

    def makeHist(self, hname, outDir = None):
        """
        Make an empty histogram from the specifications.
        """

        gd = ROOT.gDirectory    
        if outDir:
            outDir.cd()
        else:
            ROOT.gROOT.cd()

        ndim = self.ndim()

        if ndim == 1:
            if type(self.binning) is list:
                nbins = len(self.binning) - 1
                arr = array.array('d', self.binning)
    
            elif type(self.binning) is tuple:
                nbins = self.binning[0]
                arr = array.array('d', [self.binning[1] + (self.binning[2] - self.binning[1]) / nbins * i for i in range(nbins + 1)])
    
            # we decided to merge the overflow into the last bin content
            #if self.overflow:
            #    lastbinWidth = (arr[-1] - arr[0]) / 30.
            #    arr += array.array('d', [self.binning[-1] + lastbinWidth])
            #    nbins += 1
    
            hist = ROOT.TH1D(hname, '', nbins, arr)
    
        else:
            args = []
    
            for binning in self.binning:
                if type(binning) is list:
                    nbins = len(binning) - 1
                    arr = array.array('d', binning)
    
                elif type(binning) is tuple:
                    nbins = binning[0]
                    arr = array.array('d', [binning[1] + (binning[2] - binning[1]) / nbins * i for i in range(nbins + 1)])
                    
                args += [nbins, arr]
    
            if self.ndim() == 2:
                hist = ROOT.TH2D(hname, '', *tuple(args))
            elif self.ndim() == 3:
                # who would do this??
                hist = ROOT.TH3D(hname, '', *tuple(args))
            else:
                # I appreciate this error message
                raise RuntimeError('What are you thinking')
            
        gd.cd()

        hist.Sumw2()
        return hist

    def makeTree(self, tname, outDir = None):
        outDir.cd()
        tree = ROOT.TTree(tname, '')

        return tree

    def binWidth(self, bin):
        if self.ndim() != 1:
            return 0.

        if type(self.binning) is list:
            return self.binning[bin] - self.binning[bin - 1]
    
        elif type(self.binning) is tuple:
            return (self.binning[2] - self.binning[1]) / self.binning[0]

    def xtitle(self):
        if self.ndim() == 1:
            title = self.title
            if self.unit:
                title += ' (%s)' % self.unit
            return title
        else:
            return self.title[0]

    def ytitle(self, binNorm = True):
        if self.ndim() == 1:
            title = 'Events'
            if binNorm and self.binWidth(1) != 1.:
                title += ' / '
                if self.unit:
                    title += self.unit
                else:
                    title += '%.2f' % self.binWidth(1)
            return title
        else:
            return self.title[1]

    def formExpression(self, replacements = None):
        if self.ndim() == 1:
            expr = self.expr
        elif self.ndim() == 2:
            expr = self.expr[1]+':'+self.expr[0]
        else:
            expr = ':'.join(self.expr)

        if replacements is not None:
            for repl in replacements:
                # replace the variable names given in repl = ('original', 'new')
                # enclose the original variable name with characters that would not be a part of the variable
                expr = re.sub(r'([^_a-zA-Z]?)' + repl[0] + r'([^_0-9a-zA-Z]?)', r'\1' + repl[1] + r'\2', expr)

        return expr


class PlotConfig(object):
    def __init__(self):
        self.name = '' # name serves as the default region selection (e.g. monoph)
        self.baseline = ''
        self.fullSelection = ''
        self.obs = GroupSpec('data_obs', 'Observed')
        self.prescales = {}
        self.sigGroups = []
        self.signalPoints = []
        self.bkgGroups = []
        self.cuts = {}
        self.aliases = collections.OrderedDict()
        self.plots = []
        self.treeMaker = ''

        self.plots.append(PlotDef('count', '', '0.5', (1, 0., 1.), cutName = 'fullSelection'))

    def addObs(self, snames, prescale = 1):
        samples = allsamples.getmany(snames)
        for sample in samples:
            self.obs.samples.append(sample)
            self.prescales[sample] = prescale

    def addSig(self, *args, **kwd):
        if len(args) > 2:
            args = args[0:2] + (allsamples.getmany(args[2]),) + args[3:]
        elif 'samples' in kwd:
            kwd['samples'] = allsamples.getmany(kwd['samples'])

        self.sigGroups.append(GroupSpec(*args, **kwd))

    def addSigPoint(self, *args, **kwd):
        for sig in self.sigGroups:
            for sample in sig.samples:
                if sample.name == args[0]:
                    kwd['group'] = sig
                    self.signalPoints.append(SampleSpec(*args, **kwd))
                    return

        raise RuntimeError('Signal sample ' + args[0] + ' not found in any of the signal groups')

    def addBkg(self, *args, **kwd):
        if len(args) > 2:
            args = args[0:2] + allsamples.getmany(args[2]) + args[3:]
        elif 'samples' in kwd:
            if type(kwd['samples'][0]) == tuple:
                kwd['samples'] = [ allsamples.get(sname) for (sname, _) in kwd['samples'] ]
            else:
                kwd['samples'] = allsamples.getmany(kwd['samples'])
            
        self.bkgGroups.append(GroupSpec(*args, **kwd))

    def addPlot(self, *args, **kwd):
        self.plots.append(PlotDef(*args, **kwd))

    def getPlot(self, name):
        return next(plot for plot in self.plots if plot.name == name)

    def getPlots(self, names = []):
        # reverse so that count comes at last

        if len(names) != 0:
            plots = []
            for plot in reversed(self.plots):
                if plot.name in names:
                    plots.append(plot)

        else:
            plots = list(reversed(self.plots))

        return plots

    def findGroup(self, name):
        return next(g for g in self.sigGroups + self.bkgGroups if g.name == name)

    def fullLumi(self):
        return sum(s.lumi for s in self.obs.samples)

    def effLumi(self):
        return sum(s.lumi / self.prescales[s] for s in self.obs.samples)


class Variation(object):
    """
    Specifies alternative samples and cuts for systematic variation.
    Must specify either region or replacements or both as a two-component tuple corresponding to up and down variations.
    Alternatively reweight can be specified as a string or a value. See comments below.
    """

    def __init__(self, name, normalize = False, cuts = None, replacements = None, regions = None, reweight = None):
        self.name = name
        # normalize:
        #  set integral of the variation to the integral of nominal
        self.normalize = normalize
        # cuts:
        #  a 2-tuple (Up & Down) of cuts to be applied
        self.cuts = cuts
        # replacements:
        #  a 2-tuple (Up & Down) of list of 2-tuples (variable replacements (original, replaced))
        self.replacements = replacements
        # regions:
        #  a 2-tuple (Up & Down) of strings (region names)
        self.regions = regions
        # reweight:
        #  single float -> scale up and down uniformly.
        #  string -> use branches 'reweight_%sUp' & 'reweight_%sDown'. Output suffix _{name}Up & _{name}Down
        self.reweight = reweight


# Variables to be set by plotconfig.py
confName = ''
plotConfig = PlotConfig()
