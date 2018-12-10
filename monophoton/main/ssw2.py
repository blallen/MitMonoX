#!/usr/bin/env python

import sys
import os
import subprocess
import collections
import importlib

from batch import BatchManager
# from hashlib import md5hash
from time import time
import requests

## load condor-run
sys.path.append('/home/yiiyama/lib')
from condor_run import CondorRun

logger = None

padd = os.environ['CMSSW_BASE'] + '/bin/' + os.environ['SCRAM_ARCH'] + '/padd'

HOST = ''

def create_payload(done = False):
    payload = {}

    if done:
        payload['timestamp'] = int(time()),
    else:
        payload['starttime'] = int(time()),

    
    payload['task'] = taskname + '_' + os.environ['USER']
    payload['job_id'] = job_id
    payload['args'] = [md5hash(x) for x in []]
    payload['host'] = hostname

    return payload

def report_start():
    for _ in xrange(5):
        try:
            payload = create_payload(done = False)
            r = requests.post(HOST + '/condor/start', json = payload)

            if r.status_code == 200:
                return
            else:
                sleep(10)
        except requests.ConnectionError:
            print "couldn't report start @", int(time())

def report_done():
    while True:
        try:
            payload = create_payload(done = True)
            r = requests.post(HOST + '/condor/done', json = payload)
            
            if r.status_code == 200:
                return
            else:
                sleep(10)
        except requests.ConnectionError:
            print "couldn't report done @", int(time())

class SkimSlimWeight(object):

    config = {}

    def __init__(self, sample, selectors, flist, files = False):
        self.sample = sample
        self.selectors = selectors
        if files:
            self.manual = True
            self.filesets = ['manual']
            self.files = flist
        else:
            self.manual = False
            self.filesets = flist
            self.files = []

        if os.path.isdir('/local/' + os.environ['USER']):
            self.tmpDir = '/local/' + os.environ['USER'] + '/ssw2'
        else:
            self.tmpDir = '/tmp/' + os.environ['USER'] + '/ssw2'

        if self.manual or len(sample.filesets()) == 1:
            self.outDir = SkimSlimWeight.config['skimDir']
        else:
            self.outDir = SkimSlimWeight.config['skimDir'] + '/' + sample.name

    def getOutNameBase(self, fileset):
        if self.manual:
            return self.sample.name + '_manual'
        elif SkimSlimWeight.config['outSuffix']:
            return self.sample.name + '_' + SkimSlimWeight.config['outSuffix']
        else:
            if len(self.sample.filesets()) > 1:
                return self.sample.name + '_' + fileset
            else:
                return self.sample.name

    def setupSkim(self):
        """
        Set up the skimmer, clean up the destination, request T2->T3 downloads if necessary.
        """
        
        tmpOutDir = self.tmpDir + '/' + self.sample.name
        if not os.path.exists(tmpOutDir):
            try:
                os.makedirs(tmpOutDir)
            except OSError:
                # did someone running on this machine beat this job and made the directory?
                if not os.path.exists(tmpOutDir):
                    raise
    
        if not os.path.exists(self.outDir):
            try:
                os.makedirs(self.outDir)
            except OSError:
                if not os.path.exists(self.outDir):
                    raise
    
        logger.debug('getting all input files')

        if not SkimSlimWeight.config['readRemote'] and not self.manual:
            # check for missing local copies and issue a smartcache download request
            self.sample.download()

        if SkimSlimWeight.config['skipExisting']:
            logger.info('Checking for existing files.')
        else:
            logger.info('Removing existing files.')
    
        # abort if any one of the selector output exists
        for fileset in list(self.filesets):
            outNameBase = self.getOutNameBase(fileset)

            for rname in self.selectors:
                outName = outNameBase + '_' + rname + '.root'
                outPath = self.outDir + '/' + outName
                logger.debug(outPath)
    
                if SkimSlimWeight.config['skipExisting']:
                    if os.path.exists(outPath) and os.stat(outPath).st_size != 0:
                        logger.info('Output files for %s already exist. Skipping skim.', outNameBase)
                        self.filesets.remove(fileset)
                        break

                elif not SkimSlimWeight.config['testRun']:
                    try:
                        os.remove(outPath)
                    except:
                        pass
    
        return True

    def executeSkim(self):
        """
        Execute the skim.
        """

        skimmer = ROOT.Skimmer()
    
        skimmer.setPrintEvery(SkimSlimWeight.config['printEvery'])
        skimmer.setPrintLevel(SkimSlimWeight.config['printLevel'])
        skimmer.setNThreads(SkimSlimWeight.config['nThreads'])
        skimmer.setSkipMissingFiles(SkimSlimWeight.config['skipMissing'])

        if SkimSlimWeight.config['openTimeout'] is not None:
            ROOT.TIMEOUT = SkimSlimWeight.config['openTimeout']
           
        # temporary - backward compatibility issue 004 -> 005/006/007
        # if self.sample.book != 'pandaf/004':
        #    skimmer.setCompatibilityMode(True)

        # can eventually think of submitting jobs separately for different preskims
        bypreskim = collections.defaultdict(list)
        for rname, selgen in self.selectors.items():
            selector = selgen(self.sample, rname)

            selector.setUseTimers(SkimSlimWeight.config['timer'])
            skimmer.addSelector(selector)

            bypreskim[selector.getPreskim()].append(selector)

        if len(bypreskim) > 1:
            print 'Selectors with different preskims mixed. Aborting.'
            for preskim, selectors in bypreskim.iteritems():
                print preskim
                print ' ' + ' '.join(str(s.name()) for s in selectors)

            raise RuntimeError('invalid configuration')

        if self.sample.data:
            # lumilist set globally in CONFIGDIR/params.py
            logger.info('Good lumi filter: %s', params.lumilist)
            skimmer.setGoodLumiFilter(makeGoodLumiFilter(params.lumilist))

        paths = {} # {filset: list of paths}
    
        if self.manual:
            paths['manual'] = []
            for path in self.files:
                paths['manual'].append(path)

        else:
            for fileset in self.filesets:
                paths[fileset] = []
                for path in self.sample.files([fileset]):
                    if SkimSlimWeight.config['readRemote']:
                        if not os.path.exists(path) or os.stat(path).st_size == 0:
                            path = path.replace('/mnt/hadoop/cms', 'root://xrootd.cmsaf.mit.edu/')
        
                    logger.debug('Add input: %s %s', fileset, path)
                    paths[fileset].append(path)

        tmpOutDir = self.tmpDir + '/' + self.sample.name
    
        for fileset, fnames in paths.items():
            print 'Fileset', fileset

            skimmer.clearPaths()
            for fname in fnames:
                skimmer.addPath(fname)

            outNameBase = self.getOutNameBase(fileset)
            nentries = SkimSlimWeight.config['nentries']
            firstEntry = SkimSlimWeight.config['firstEntry']
    
            logger.debug('Skimmer.run(%s, %s, %s, %d, %d)', tmpOutDir, outNameBase, self.sample.data, nentries, firstEntry)
            skimmer.run(tmpOutDir, outNameBase, self.sample.data, nentries, firstEntry)
    
            for rname in self.selectors:
                outName = outNameBase + '_' + rname + '.root'
        
                if SkimSlimWeight.config['testRun']:
                    logger.info('Output at %s/%s', tmpOutDir, outName)
                else:
                    logger.info('Copying output to %s/%s', self.outDir, outName)
                    shutil.copy(tmpOutDir + '/' + outName, self.outDir)
                    logger.info('Removing %s/%s', tmpOutDir, outName)
                    os.remove(tmpOutDir + '/' + outName)

    def setupMerge(self):
        if not os.path.exists(self.tmpDir):
            try:
                os.makedirs(self.tmpDir)
            except OSError:
                # did someone beat this job and made the directory?
                if not os.path.exists(self.tmpDir):
                    raise

        for rname in list(self.selectors):
            outNameBase = self.sample.name + '_' + rname
            outName = outNameBase + '.root'
            outPath = SkimSlimWeight.config['skimDir'] + '/' + outName
        
            if SkimSlimWeight.config['skipExisting']:
                if os.path.exists(outPath) and os.stat(outPath).st_size != 0:
                    logger.info('Output files for %s already exist. Skipping merge.', outNameBase)
                    self.selectors.pop(rname)

            elif not SkimSlimWeight.config['testRun']:
                try:
                    os.remove(outPath)
                except:
                    pass
    
        return True

    def executeMerge(self):
        inDir = SkimSlimWeight.config['skimDir'] + '/' + self.sample.name

        for rname in self.selectors:
            for fileset in list(self.filesets):
                fname = inDir + '/' + self.sample.name + '_' + fileset + '_' + rname + '.root'
	        if ( (not os.path.exists(fname)) or (os.stat(fname).st_size == 0) ):
                    if SkimSlimWeight.config['skipMissing']:
                        print 'Skipping fileset ' + fileset + ' in order to complete merge.'
			self.filesets.remove(fileset)
		    else:
                    	raise RuntimeError('Missing input file', fname)
        
            outNameBase = self.sample.name + '_' + rname
            outName = outNameBase + '.root'
        
            mergePath = self.tmpDir + '/' + outName
            outPath = SkimSlimWeight.config['skimDir'] + '/' + outName
        
            logger.debug('%s %s %s', padd, mergePath, ' '.join(inDir + '/' + self.sample.name + '_' + fileset + '_' + rname + '.root' for fileset in self.filesets))
            proc = subprocess.Popen([padd, mergePath] + [inDir + '/' + self.sample.name + '_' + fileset + '_' + rname + '.root' for fileset in self.filesets], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            out, err = proc.communicate()
            print out.strip()
            print err.strip()
        
            if SkimSlimWeight.config['testRun']:
                logger.info('Output at %s', mergePath)
            else:
                logger.info('Copying output to %s', outPath)
                shutil.copy(mergePath, SkimSlimWeight.config['skimDir'])
                logger.info('Removing %s', mergePath)
                os.remove(mergePath)


class SSWBatchManager(BatchManager):
    def __init__(self, ssws):
        BatchManager.__init__(self, 'ssw2')

        self.ssws = ssws # list of SlimSkimWeight objects to manage

    def submitMerge(self, args):
        submitter = CondorRun(os.path.realpath(__file__))
        submitter.requirements = 'UidDomain == "mit.edu"'

        arguments = []

        for ssw in self.ssws:
            # Collect arguments and remove output
            for rname in ssw.selectors:
                arguments.append((ssw.sample.name, rname))
    
                # clean up old .log files
                path = '/local/' + os.environ['USER'] + '/ssw2/' + ssw.sample.name + '_' + rname + '.0.log'
                logger.debug('Removing %s', path)
                try:
                    os.remove(path)
                except:
                    pass
    
        argTemplate = '-M %s -s %s'

        submitter.job_args = [argTemplate % arg for arg in arguments]
        submitter.job_names = ['%s_%s' % arg for arg in arguments]

        self._submit(submitter, 'merge', argTemplate, args.noWait, args.autoResubmit)

    def submitSkim(self, args):
        submitter = CondorRun(os.path.realpath(__file__))
        submitter.requirements = 'UidDomain == "mit.edu"'

        argTemplate = '%s -f %s'
    
        if args.skipMissing:
            argTemplate += ' -K'

        if args.readRemote:
            argTemplate += ' -R'
            try:
                x509Proxy = os.environ['X509_USER_PROXY']
            except KeyError:
                x509Proxy = '/tmp/x509up_u%d' % os.getuid()

            submitter.aux_input.append(x509Proxy)
            submitter.env['X509_USER_PROXY'] = os.path.basename(x509Proxy)

        if args.openTimeout is not None:
            argTemplate += ' -m ' + str(args.openTimeout)

        for ssw in self.ssws:
            for fileset in ssw.filesets:
                submitter.job_args.append(argTemplate % (ssw.sample.name, fileset) + ' -s ' + ' '.join(ssw.selectors.keys()))
                submitter.job_names.append('%s_%s' % (ssw.sample.name, fileset))
    
                # clean up old .log files
                logpath = '/local/' + os.environ['USER'] + '/ssw2/' + ssw.sample.name + '_' + fileset + '.0.log'
                logger.debug('Removing %s', logpath)
                try:
                    os.remove(logpath)
                except:
                    pass

        self._submit(submitter, 'skim', argTemplate, args.noWait, args.autoResubmit)
    

if __name__ == '__main__':

    import sys
    import socket
    import time
    import shutil
    import collections
    import logging
    from argparse import ArgumentParser
    
    argParser = ArgumentParser(description = 'Plot and count')
    argParser.add_argument('snames', metavar = 'SAMPLE', nargs = '*', help = 'Sample names to skim.')
    argParser.add_argument('--list', '-L', action = 'store_true', dest = 'list', help = 'List of samples.')
    argParser.add_argument('--nentries', '-N', metavar = 'N', dest = 'nentries', type = int, default = -1, help = 'Maximum number of entries.')
    argParser.add_argument('--timer', '-T', action = 'store_true', dest = 'timer', help = 'Turn on timers on Selectors.')
    argParser.add_argument('--compile-only', '-C', action = 'store_true', dest = 'compileOnly', help = 'Compile and exit.')
    argParser.add_argument('--filesets', '-f', metavar = 'ID', dest = 'filesets', nargs = '+', default = [], help = 'Fileset id to run on.')
    argParser.add_argument('--files', '-i', metavar = 'PATH', dest = 'files', nargs = '+', default = [], help = 'Directly run on files.')
    argParser.add_argument('--first-entry', '-t', metavar = 'ENTRY', dest = 'firstEntry', type = int, default = 0, help = 'First entry number to process.')
    argParser.add_argument('--suffix', '-x', metavar = 'SUFFIX', dest = 'outSuffix', default = '', help = 'Output file suffix.')
    argParser.add_argument('--batch', '-B', action = 'store_true', dest = 'batch', help = 'Use condor-run to run.')
    argParser.add_argument('--skip-existing', '-X', action = 'store_true', dest = 'skipExisting', help = 'Do not run skims on files that already exist.')
    argParser.add_argument('--merge', '-M', action = 'store_true', dest = 'merge', help = 'Merge the fragments without running any skim jobs.')
    argParser.add_argument('--selectors', '-s', metavar = 'SELNAME', dest = 'selnames', nargs = '*', default = [], help = 'Selectors to process. With --list, print the selectors configured with the samples.')
    argParser.add_argument('--printlevel', '-p', metavar = 'LEVEL', dest = 'printLevel', default = 'WARNING', help = 'Override config.printLevel.')
    argParser.add_argument('--print-every', '-e', metavar = 'NEVENTS', dest = 'printEvery', type = int, default = 10000, help = 'Print frequency.')
    argParser.add_argument('--no-wait', '-W', action = 'store_true', dest = 'noWait', help = '(With batch option) Don\'t wait for job completion.')
    argParser.add_argument('--read-remote', '-R', action = 'store_true', dest = 'readRemote', help = 'Read from root://xrootd.cmsaf.mit.edu if a local copy of the file does not exist.')
    argParser.add_argument('--resubmit', '-S', action = 'store_true', dest = 'autoResubmit', help = '(Without no-wait option) Automatically release held jobs.')
    argParser.add_argument('--skip-missing', '-K', action = 'store_true', dest = 'skipMissing', help = 'Skip missing files in skim.')
    argParser.add_argument('--num-threads', '-j', metavar = 'N', dest = 'nThreads', type = int, default = 1, help = 'Number of threads to use. Each selector is run in a separate thread.')
    argParser.add_argument('--open-timeout', '-m', metavar = 'SECONDS', dest = 'openTimeout', type = int, help = 'Timeout for opening input files. Open is attempted every 30 seconds.')
    argParser.add_argument('--test-run', '-E', action = 'store_true', dest = 'testRun', help = 'Don\'t copy the output files to the production area. Sets --filesets to 0000 by default.')
    
    args = argParser.parse_args()
    sys.argv = []

    ## option conflicts
    if len(args.files) != 0:
        if len(args.filesets) != 0:
            logger.error('Cannot set filesets and files simultaneously.')
            sys.exit(1)

        if args.batch:
            logger.error('Cannot use batch mode with individual files.')
            sys.exit(1)

    if args.readRemote:
        try:
            x509Proxy = os.environ['X509_USER_PROXY']
        except KeyError:
            x509Proxy = '/tmp/x509up_u%d' % os.getuid()

        if not os.path.exists(x509Proxy):
            raise RuntimeError('X509 proxy file does not exist')

        if not x509Proxy.startswith('/'):
            os.environ['X509_USER_PROXY'] = os.path.realpath(x509Proxy)

    ## import the global config
    import config

    ## directories to include
    monoxdir = os.path.dirname(config.baseDir)

    ## source the analysis config
    params = importlib.import_module('configs.' + config.config + '.params')

    ## set up logger
    printLevel = getattr(logging, args.printLevel.upper())
    args.printLevel = printLevel # gets passed to SkimSlimWeight.config

    logging.basicConfig(level = printLevel)
    logger = logging.getLogger(__name__)

    logger.debug('Running at %s', socket.gethostname())

    ## set up global configurations with args and config
    for key in dir(args):
        if not key.startswith('_'):
            SkimSlimWeight.config[key] = getattr(args, key)

    for key in dir(config):
        if not key.startswith('_'):
            SkimSlimWeight.config[key] = getattr(config, key)

    ## set up samples and selectors
    import datasets

    ## load ROOT and panda before they are possibly used by selectors.py
    import ROOT

    ROOT.gSystem.Load(config.libobjs)

    # if the objects library is compiled with CLING dictionaries, ROOT must load the
    # full library first before compiling the macros.
    try:
        e = ROOT.panda.Event
    except AttributeError:
        pass

    skimconfig = importlib.import_module('configs.' + config.config + '.skimconfig')

    allselectors = {}
    for pat, sels in skimconfig.skimconfig.items():
        samples = datasets.allsamples.getmany(pat)
        for sample in samples:
            if sample in allselectors:
                raise RuntimeError('Duplicate skim config for ' + sample.name)

            # sels = [(name, selection function), ...]
            allselectors[sample] = dict(sels)

    ## filter out the selectors

    # list of (sample, {rname: selgen})
    sampleList = []
    
    for ss in args.snames:
        # ss can be given in format sname=selector1,selector2,.. or sname_region
        if '=' in ss:
            spattern, rn = ss.split('=')
            rnames = rn.split(',')
        elif '_' in ss:
            spattern = ss.split('_')[0]
            rnames = [ss.split('_')[1]]
        else:
            spattern = ss
            rnames = []

        samples = datasets.allsamples.getmany(spattern)
        for sample in samples:
            selectors = {}

            if sample not in allselectors:
                raise RuntimeError('Sample ' + sample.name + ' not defined in skimconfig')

            if len(rnames) == 0:
                # fill in the selectors for samples with no selector specification
                if len(args.selnames) != 0:
                    for rname in args.selnames:
                        try:
                            selectors[rname] = allselectors[sample][rname]
                        except KeyError:
                            print 'Selector', sample.name, sel, 'not defined'
                            raise

                else:
                    for rname, selector in allselectors[sample].iteritems():
                        selectors[rname] = selector

            else:
                for rname in rnames:
                    try:
                        selectors[rname] = allselectors[sample][rname]
                    except KeyError:
                        print 'Selector', sample.name, rname, 'not defined'
                        raise

            sampleList.append((sample, selectors))

    if args.list:
        if len(args.selnames) != 0:
            for sample, selectors in sampleList:
                print sample.name + ' (' + ' '.join(selectors.keys()) + ')'
        else:
            print ' '.join(sorted(s.name for s, _ in sampleList))

        sys.exit(0)

    ## compile and load the Skimmer
    ROOT.gSystem.Load('libfastjet.so')

    ROOT.gROOT.LoadMacro(config.baseDir + '/main/operators.cc+')
    try:
        o = ROOT.Operator
    except:
        logger.error("Couldn't compile operators.cc. Quitting.")
        sys.exit(1)

    ROOT.gROOT.LoadMacro(config.baseDir + '/main/selectors.cc+')
    try:
        o = ROOT.EventSelectorBase
    except:
        logger.error("Couldn't compile selectors.cc. Quitting.")
        sys.exit(1)
    
    ROOT.gSystem.AddIncludePath('-I' + monoxdir + '/common')
    ROOT.gROOT.LoadMacro(config.baseDir + '/main/Skimmer.cc+')
    
    try:
        s = ROOT.Skimmer
    except:
        logger.error("Couldn't compile Skimmer.cc. Quitting.")
        sys.exit(1)
    
    if args.compileOnly:
        sys.exit(0)

    ## load good lumi filter
    sys.path.append(monoxdir + '/common')
    from goodlumi import makeGoodLumiFilter

    ## construct and run SkimSlimWeight objects
    ssws = []
    for sample, selectors in sampleList:
        if len(args.files) != 0:
            files = True
            flist = args.files
        else:
            files = False
            if len(args.filesets) == 0 and args.testRun:
                flist = ['0000']
            else:
                flist = args.filesets

        if len(flist) == 0:
            flist = sample.filesets()

        ssw = SkimSlimWeight(sample, selectors, flist, files)

        if args.merge:
            if not ssw.setupMerge():
                logger.warning('Failed to set up merge job for %s', sample.name)
                continue
        else:
            if not ssw.setupSkim():
                logger.warning('Failed to set up skim job for %s', sample.name)
                continue

        ssws.append(ssw)

    if args.batch:
        ## job submission only
        print 'Submitting jobs.'
       
        batchManager = SSWBatchManager(ssws)

        if args.merge:
            batchManager.submitMerge(args)
        else:
            batchManager.submitSkim(args)

        if args.noWait:
            print 'Jobs have been submitted.'
        else:
            print 'All jobs finished.'

    else:
        if args.merge:
            print 'Merging.'
            for ssw in ssws:
                ssw.executeMerge()

        else:
            print 'Skimming.'
            for ssw in ssws:
                ssw.executeSkim()
