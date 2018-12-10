#!/usr/bin/env python

import re
import os
import math
import fnmatch
import subprocess
import importlib

import config

def expandBrace(pattern):
    """Expand a string with a brace-enclosed substitution pattern."""

    op = pattern.find('{')
    if op < 0:
        return

    cl = pattern.find('}', op + 1)
    if cl < 0:
        raise RuntimeError('Invalid dataset name ' + pattern)

    sublist = pattern[op + 1:cl].split(',')

    template = pattern[:op] + '%s' + pattern[cl + 1:]

    strings = []
    for sub in sublist:
        strings.append(template % sub)

    return strings

def strDiff(base, target):
    """
    Extract the difference between base and target. Return (begin, end, b, t)
    where begin is the start position of the difference, end is the position from
    the end (negative) of the first post-difference character, and end are the
    positions in the string, b and t are the portions of the base and target
    strings that differ from each other.
    """

    begin = 0
    while True:
        if target[begin] != base[begin]:
            break
        begin += 1

    end = -1
    while True:
        if target[end] != base[end]:
            break
        end -= 1

    # end cannot be -1 - don't mix data from different tiers!
    if end == -1:
        raise RuntimeError('Two strings are different all the way to the end!')

    end += 1

    b = base[begin:end]
    t = target[begin:end]

    return (begin, end, b, t)

def braceContract(strings):
    """Reverse operation of expandBrace."""

    if len(strings) == 1:
        return strings[0]

    base = strings[0]
    
    start = len(base)
    end = -len(base)

    for target in strings[1:]:
        s, e, _, _ = strDiff(base, target)

        if s < start:
            start = s

        if e > end:
            end = e

    diffs = [s[start:end] for s in strings]

    return base[:start] + '{' + ','.join(diffs) + '}' + base[end:]


class SampleDef(object):
    def __init__(self, name, title = '', catalog = ('', ''), book = '', fullname = '', additionalDatasets = [], crosssection = 0., nevents = 0, sumw = 0., lumi = 0., generator = '', comments = '', custom = {}):
        self.name = name
        self.title = title
        self.catalog = catalog
        self.book = book
        self.fullname = fullname
        self.crosssection = crosssection
        self.nevents = nevents
        if sumw == 0.:
            self.sumw = float(nevents)
        else:
            self.sumw = sumw
        self.lumi = lumi
        self.generator = generator
        self.data = (generator == 'lhc')
        self.comments = comments
        self.custom = custom

        self.datasetNames = [self.fullname]
        self.datasetSuffices = ['']

        for name in additionalDatasets:
            self.addDataset(name)

        self._sumw2 = 0. # will be > 0 at the first call to _updateSumw

        # loaded from catalog only on demand
        self._directories = {} # {dataset: directory}
        self._basenames = {} # {dataset: {fileset: [basename]}}
        self._downloadable = {}

    def clone(self):
        return SampleDef(self.name, title = self.title, catalog = self.catalog, book = self.book, fullname = self.fullname,
            additionalDatasets = self.datasetNames, crosssection = self.crosssection, nevents = self.nevents,
            sumw = self.sumw, lumi = self.lumi, generator = self.generator, comments = self.comments, custom = dict(self.custom.items()))

    def addDataset(self, name):
        if name in self.datasetNames:
            return

        # extract a suffix from the additional dataset name
        _, _, _, suffix = strDiff(self.fullname, name)

        self.datasetNames.append(name)
        self.datasetSuffices.append(suffix)

        # invalidate cached information
        self._sumw2 = 0.

    def dump(self, effectiveLumi = False):
        print 'name =', self.name
        print 'title =', self.title
        print 'catalog = %s (%s)' % self.catalog
        print 'book =', self.book
        print 'fullname =', self.fullname
        print 'datasetNames =', self.datasetNames
        print 'datasetSuffices =', self.datasetSuffices
        print 'crosssection =', self.crosssection
        print 'nevents =', self.nevents
        print 'sumw =', self.sumw
        if self.lumi > 0. or effectiveLumi:
            print 'lumi =', self.effectiveLumi(), 'pb'
        print 'generator =', self.generator
        print 'comments = "' + self.comments + '"'
        print 'filesets =', self.filesets()

    def linedump(self):
        title = '"%s"' % self.title

        if self.data:
            crosssection = self.lumi
            ndec = 1
            sumwstr = '-'
        else:
            crosssection = self.crosssection
            ndec = 0
            while crosssection < math.pow(10., 3 - ndec):
                ndec += 1

            if int(self.sumw) == self.nevents:
                sumwstr = '%.1f' % self.sumw
            else:
                sumwstr = '%.11e' % self.sumw

        if ndec >= 6:
            xsecstr = '%.{ndec}e'.format(ndec = 3) % crosssection
        else:
            xsecstr = '%.{ndec}f'.format(ndec = ndec) % crosssection

        fullnames = braceContract(self.datasetNames)

        if self.comments != '':
            comments = " # " + self.comments
        else:
            comments = ''
            
        lineTuple = (self.name, title, xsecstr, self.nevents, sumwstr, self.generator, self.catalog[0], self.book, fullnames, comments)
        return '%-16s %-35s %-16s %-10d %-20s %-9s %-8s %-12s %s%s' % lineTuple

    def _updateSumw(self):
        if self._sumw2 > 0.:
            return

        import ROOT

        self.download()

        self.nevents = 0
        self.sumw = 0.

        error = False
        for dataset in self.datasetNames:
            if self.generator in ('amcatnlo', 'sherpa', 'powheg'):
                for fileset, basenames in self._basenames[dataset].items():
                    for basename in basenames:
                        path = self._directories[dataset] + '/' + basename
                        if os.path.exists(path):
                            source = ROOT.TFile.Open(path)
                        else:
                            path = path.replace('/mnt/hadoop/cms', 'root://xrootd.cmsaf.mit.edu/')
                            source = ROOT.TFile.Open(path)

                        if not source:
                            error = True
                            continue

                        try:
                            counter = source.Get('eventcounter')
                            self.nevents += counter.GetBinContent(1)
                            if not self.data:
                                sumw = source.Get('hSumW')
                                self.sumw += sumw.GetBinContent(1)
                                self._sumw2 += math.pow(sumw.GetBinError(1), 2.)

                        except:
                            print path, 'corrupt'
                            error = True

                        source.Close()
            else:
                # Originally we were reading the ROOT files to get the actual event count
                # If we want to instead rely on numbers from production, we can simply
                # read the catalog
                with open(self.catalog[1] + '/' + self.book + '/' + dataset + '/Files') as fileList:
                    for line in fileList:
                        nevents = int(line.strip().split()[2])
                        self.nevents += nevents
                        self.sumw += nevents
                        self._sumw2 += math.pow(nevents, 2.)

        if error:
            raise RuntimeError('Corrupt input')

    def _readCatalogs(self):
        # Loop over dataset names of the sample
        for dsuffix, dataset in zip(self.datasetSuffices, self.datasetNames):
            if dataset in self._basenames:
                continue

            self._basenames[dataset] = {}

            with open(self.catalog[1] + '/' + self.book + '/' + dataset + '/Filesets') as filesetList:
                for line in filesetList:
                    fileset, xrdpath = line.split()[:2]
                    fileset += dsuffix

                    self._basenames[dataset][fileset] = []

                    if dataset not in self._directories:
                        self._directories[dataset] = xrdpath.replace('root://xrootd.cmsaf.mit.edu/', '/mnt/hadoop/cms').replace('root://t3serv006.mit.edu/', '/mnt/hadoop')
                        self._downloadable[dataset] = self._directories[dataset].startswith('/mnt/hadoop/cms/store/user/paus')
    
            with open(self.catalog[1] + '/' + self.book + '/' + dataset + '/Files') as fileList:
                for line in fileList:
                    fileset, fname = line.split()[:2]
                    fileset += dsuffix
    
                    self._basenames[dataset][fileset].append(fname)
    
    def recomputeWeight(self):
        self._sumw2 = 0.

        self._updateSumw()

        if self._sumw2 == 0.:
            print 'Failed at counting sample. Not changing anything!!!.'
            return

    def effectiveLumi(self):
        if self.lumi > 0.:
            return self.lumi
        else:
            self._updateSumw()
            sumw2 = self._sumw2
            if sumw2 > 0.:
                return math.pow(self.sumw, 2.) / sumw2 / self.crosssection
            else:
                print 'sumw2 is zero'
                return 0.

    def checkT2(self, dataset):
        filesT2 = set()

        listT2 = subprocess.Popen(
            ['gfal-ls', 'gsiftp://se01.cmsaf.mit.edu:2811/cms/store/user/paus/' + self.book + '/' + dataset],
            stdout = subprocess.PIPE, stderr = subprocess.PIPE
            )
        rawT2 = listT2.communicate()[0].strip()

        for line in rawT2.split("\n"):
            if not '.root' in line:
                continue

            filename = dataset + '/' + os.path.basename(line)
            filesT2.add(filename)

        return filesT2

    def checkT3(self, dataset):
        filesT3 = set()

        if not os.path.isdir(self._directories[dataset]):
            return filesT3

        for fname in os.listdir(self._directories[dataset]):
            if not fname.endswith('.root'):
                continue

            path = self._directories[dataset] + '/' + fname
            if os.stat(path).st_size == 0:
                continue

            filesT3.add(dataset + '/' + fname)

        return filesT3

    def download(self, filesets = []):
        self._readCatalogs()

        for dataset in self.datasetNames:
            if not self._downloadable[dataset]:
                continue

            filesT3 = self.checkT3(dataset)
            filesT2 = self.checkT2(dataset)

            nTotal = 0
            nMissing = 0
            missingFiles = set()
            for fileT2 in filesT2:
                if fileT2 in filesT3:
                    nTotal += 1
                else:
                    missingFiles.add(fileT2)
                    nMissing +=1

            if nMissing == nTotal:
                print 'No files present on T3. Requesting entire dataset.'
                proc = subprocess.Popen(
                    ['python2.6', '/usr/bin/dynamo-request', '--panda', self.book[self.book.find('/') + 1:], '--sample', dataset],
                    stdout = subprocess.PIPE, stderr = subprocess.PIPE
                    )
                print proc.communicate()[0].strip()

            elif nMissing > 0:
                print 'Files partially available on T3. Requesting missing or corrupted blocks.'
                ### eventually replace with block level requests
                proc = subprocess.Popen(
                    ['python2.6', '/usr/bin/dynamo-request', '--panda', self.book[self.book.find('/') + 1:], '--sample', dataset],
                    stdout = subprocess.PIPE, stderr = subprocess.PIPE
                    )
                print proc.communicate()[0].strip()

            else:
                print self.book + '/' + dataset + ' is already on disk at T3.'

    def filesets(self, datasetNames = []):
        self._readCatalogs()

        if len(datasetNames) == 0:
            datasetNames = self.datasetNames

        return sum([sorted(self._basenames[d].keys()) for d in datasetNames], [])

    def files(self, filesets = []):
        self._readCatalogs()

        if len(filesets) == 0:
            filesets = self.filesets()

        paths = []

        for dataset in self.datasetNames:
            directory = self._directories[dataset]

            basenames = sum((bs for f, bs in self._basenames[dataset].items() if f in filesets), [])
            for basename in basenames:
                paths.append(directory + '/' + basename)

        return paths


class SampleDefList(object):
    def __init__(self, samples = [], listpath = ''):
        self.samples = list(samples)
        self._catalogs = {} # {name: path}
        self._lineInsertions = {} # {path: [(dataset before, comment)]} to reproduce comment lines from the source
        self._sample_source = {} # {path: set(sample name)}

        if listpath:
            self._load(listpath)

    def __iter__(self):
        return iter(self.samples)

    def __reversed__(self):
        return reversed(self.samples)

    def __getitem__(self, key):
        try:
            return self.get(key)
        except RuntimeError:
            raise KeyError(key + ' not defined')

    def _load(self, listpath):
        self._lineInsertions[listpath] = []
        self._sample_source[listpath] = set()

        with open(listpath) as dsSource:
            name = ''
            for line in dsSource:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    self._lineInsertions[listpath].append((name, line))
                    continue

                if line.startswith('%'):
                    self._lineInsertions[listpath].append((name, line))
                    words = line[1:].split()

                    if words[0] == 'catalog':
                        cname = words[1]
                        path = words[2]
                        if path[0] != '/':
                            path = os.path.dirname(os.path.realpath(listpath)) + '/' + path

                        self._catalogs[cname] = path

                    elif words[0] == 'import':
                        path = words[1]
                        if path[0] != '/':
                            path = os.path.dirname(os.path.realpath(listpath)) + '/' + path
                    
                        self._load(path)

                    continue

                #                   name       title    xsec           nevt       sumw           generator  catalog    book       fullnames        comments
                matches = re.match('([^\s]+)\s+"(.*)"\s+([0-9e.+-]+)\s+([0-9]+)\s+([0-9e.+-]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+((?:[^\s#]+\s*)+)(#.*|)$', line)
                if not matches:
                    print 'Ill-formed line in ' + listpath
                    print line
                    continue
        
                name, title, crosssection, nevents, sumw, generator, catalog, book, fullnames, comments = [matches.group(i) for i in range(1, 11)]
                fullnames = fullnames.split()

                self._sample_source[listpath].add(name)

                for pattern in fullnames:
                    if '{' in pattern: # bash-like substitution pattern delimited by ','
                        fullnames.remove(pattern)
                        fullnames.extend(expandBrace(pattern))

                catarg = (catalog, self._catalogs[catalog])

                kwd = {'title': title, 'generator': generator, 'catalog': catarg, 'book': book, 'fullname': fullnames[0], 'additionalDatasets': fullnames[1:], 'nevents': int(nevents), 'comments': comments.lstrip(' #')}

                if sumw == '-':
                    kwd.update({'lumi': float(crosssection)})
                else:
                    kwd.update({'crosssection': float(crosssection), 'sumw': float(sumw)})

                self.samples.append(SampleDef(name, **kwd))

    def save(self, listpath):
        insertions = self._lineInsertions[listpath]

        def insert_comment(out, iC, name):
            while iC != len(insertions) and insertions[iC][0] == name:
                line = insertions[iC][1]
                out.write(line + '\n')
                if line.startswith('<'):
                    path = line[1:-1]
                    if path[0] != '/':
                        path = os.path.dirname(listpath) + '/' + path
    
                    self.save(path)
                    
                iC += 1

            return iC

        with open(listpath, 'w') as out:
            iC = insert_comment(out, 0, '')

            for sample in self.samples:
                if sample.name not in self._sample_source[listpath]:
                    continue

                out.write(sample.linedump() + '\n')

                iC = insert_comment(out, iC, sample.name)

    def names(self):
        return [s.name for s in self.samples]

    def get(self, name):
        try:
            return next(s for s in self.samples if s.name == name)
        except StopIteration:
            raise RuntimeError('Sample ' + name + ' not found')

    def getmany(self, names):
        if type(names) is str:
            names = [names]
        else:
            names = list(names) # make a copy

        samples = []
        iname = 0
        while iname != len(names): # iterate by len because the length can change
            name = names[iname]
            iname += 1

            match = True
            if name.startswith('!'):
                name = name[1:]
                match = False

            if '{' in name:
                expanded = expandBrace(name)
                name = expanded[0]
                names.extend(expanded[1:]) # add to the end of list
            
            if '*' in name:
                matching = [s for s in self.samples if fnmatch.fnmatch(s.name, name)]
            else:
                matching = [self.get(name)]

            if match:
                samples += matching
            else:
                for s in matching:
                    try:
                        samples.remove(s)
                    except:
                        pass

        return sorted(list(set(samples)), key = lambda s: s.name)

params = importlib.import_module('configs.' + config.config + '.params')

if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser

    argParser = ArgumentParser(description = 'Dataset information management')
    commandHelp = '''list [DATASETS]: List datasets with nevents > 0 (no argument) or datasets with names matching to the argument.
print DATASET: Print information of DATASET.
dump DATASETS: Dump information of DATASETS in CSV form.
recalculate DATASETS: Recalculate nentries and sumw for DATASETS.
add INFO: Add a new dataset.'''
    argParser.add_argument('command', nargs = '+', help = commandHelp)
    argParser.add_argument('--list-path', '-s', metavar = 'PATH', dest = 'listPath', default = params.datasetlist, help = 'CSV file to load data from.')
    argParser.add_argument('--save', '-o', metavar = 'PATH', dest = 'outPath', nargs = '?', const = '', help = 'Save updated content to CSV file (no argument: save to original CSV).')

    args = argParser.parse_args()
    sys.argv = []

    import ROOT

    samples = SampleDefList(listpath = args.listPath)

    command = args.command[0]
    arguments = args.command[1:]

    if command == 'list':
        if len(arguments) > 0:
            matches = samples.getmany(arguments)
        else:
            matches = samples.getmany(['*'])

        print ' '.join([sample.name for sample in matches])

    elif command == 'print':
        try:
            sample = samples[arguments[0]]
        except:
            print 'No sample', arguments[0]
            sys.exit(1)

        sample.dump()

    elif command == 'filesets':
        try:
            sample = samples[arguments[0]]
        except:
            print 'No sample', arguments[0]
            sys.exit(1)

        print ' '.join(sample.filesets())

    elif command == 'dump':
        if len(arguments) == 0:
            arguments = samples.names()

        for name in arguments:
            try:
                sample = samples[name]
            except:
                print 'No sample', name
                sys.exit(1)

            print sample.linedump()

    elif command == 'recalculate':
        targets = []
        for name in arguments:
            targets.extend(samples.getmany(name))

        for sample in targets:
            sample.recomputeWeight()
            print sample.linedump()

    elif command == 'add':
        name, title, crosssection, nevents, sumw, book, fullname = arguments[:7]
        additionalDatasets = []
        comments = ''

        iarg = 7
        while iarg < len(arguments):
            if arguments[iarg].startswith('#'):
                comments = ' '.join(arguments[iarg:])
                break
            else:
                additionalDatasets.append(arguments[iarg])

            iarg += 1

        kwd = {'title': title, 'book': book, 'fullname': fullname, 'additionalDatasets': additionalDatasets, 'nevents': int(nevents), 'comments': comments.lstrip('#')}

        if sumw == '-':
            kwd.update({'lumi': float(crosssection), 'data': True})
        else:
            kwd.update({'crosssection': float(crosssection), 'sumw': float(sumw)})

        samples.samples.append(SampleDef(name, **kwd))
        # add to the main file
        samples._sample_source[args.listPath].add(name)

    elif command == 'lumi':
        source = samples.getmany(arguments)
        print ' '.join(s.name for s in source)
        print sum(s.lumi for s in source)

    elif command == 'download':
        for sample in samples.getmany(arguments):
            sample.download()

    elif command == 'check':
        for sample in samples.getmany(arguments):
            paths = sample.files()
            for path in paths:
                if not os.path.exists(path):
                    print sample.name, '[NG] does not have all files'
                    break
            else:
                print sample.name, '[OK] has all files'

    else:
        print 'Unknown command', command
        sys.exit(1)
    
    if args.outPath is not None:
        if args.outPath == '':
            args.outPath = args.listPath

        samples.save(args.outPath)

else: # when importing from another python script
    allsamples = SampleDefList(listpath = params.datasetlist)
