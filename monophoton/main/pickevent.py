#!/usr/bin/env python

import sys
import os
import re
import tempfile

from batch import BatchManager

## load condor-run
sys.path.append('/home/yiiyama/lib')
from condor_run import CondorRun

logger = None

class PickEvent(object):

    config = {}

    def __init__(self, sample, flist, files):
        self.sample = sample
        self.flist = flist
        if files:
            self.manual = True
            self.filesets = ['manual']
            self.files = flist
        else:
            self.manual = False
            self.filesets = flist
            self.files = []

        self.outDir = PickEvent.config['outDir'] + '/' + sample.name

        self.eventIds = []

    def setupSkim(self):
        """
        Set up the skimmer, clean up the destination, request T2->T3 downloads if necessary.
        """
        
        if not os.path.exists(self.outDir):
            try:
                os.makedirs(self.outDir)
            except OSError:
                if not os.path.exists(self.outDir):
                    raise
    
        logger.debug('getting all input files')

        if not PickEvent.config['readRemote'] and not self.manual:
            # check for missing local copies and issue a smartcache download request
            self.sample.download()

        return True

    def readEventList(self, path, uwFormat):
        """
        Read the list of events to pick from a file.
        """

        with open(path) as source:
            for line in source:
                matches = re.match('([0-9]+):([0-9]+):([0-9]+)', line.strip())
                if matches:
                    if uwFormat:
                        self.eventIds.append((int(matches.group(1)), int(matches.group(3)), int(matches.group(2))))
                    else:
                        self.eventIds.append((int(matches.group(1)), int(matches.group(2)), int(matches.group(3))))

    def executeSkim(self):
        """
        Execute the skim.
        """

        skimmer = ROOT.EventPicker()
    
        skimmer.setPrintEvery(PickEvent.config['printEvery'])
        skimmer.setPrintLevel(PickEvent.config['printLevel'])
    
        if self.manual:
            for path in self.files:
                skimmer.addPath(path)
        else:
            for fileset in self.filesets:
                for path in self.sample.files([fileset]):
                    if PickEvent.config['readRemote']:
                        if not os.path.exists(path) or os.stat(path).st_size == 0:
                            path = path.replace('/mnt/hadoop/cms', 'root://xrootd.cmsaf.mit.edu/')
        
                    logger.debug('Add input: %s %s', fileset, path)
                    skimmer.addPath(path)

        for eventId in self.eventIds:
            skimmer.addEvent(*eventId)

        tmpDir = tempfile.mkdtemp()

        logger.debug('Skimmer.run(%s, %d)', tmpDir, PickEvent.config['nentries'])
        skimmer.run(tmpDir, PickEvent.config['nentries'])

        for eventId in self.eventIds:
            tmpName = tmpDir + ('/%d_%d_%d.root' % eventId)
            logger.debug('Checking output ' + tmpName)
            if not os.path.exists(tmpName):
                continue

            outName = self.outDir + ('/%d_%d_%d.root' % eventId)

            logger.info('Copying output to %s', outName)
            shutil.copy(tmpName, outName)

        logger.info('Removing %s', tmpDir)
        shutil.rmtree(tmpDir)


class PickEventBatchManager(BatchManager):
    def __init__(self, pickers, skipMissing, readRemote):
        BatchManager.__init__(self, 'pickevent')

        self.pickers = pickers # list of SlimSkimWeight objects to manage
        self.skipMissing = skipMissing
        self.readRemote = readRemote

    def submitSkim(self, noWait, autoResubmit = False):
        submitter = CondorRun(os.path.realpath(__file__))

        argTemplate = '%s -f %s'
    
        if self.skipMissing:
            argTemplate += ' -K'

        if self.readRemote:
            argTemplate += ' -R'

        for picker in self.pickers:
            eventList = tempfile.NamedTemporaryFile(delete = False)
            for eventId in picker.eventIds:
                eventList.write('%d:%d:%d\n' % eventId)

            eventList.close()
            listName = eventList.name
            os.chmod(listName, 0644)
            # event list will appear in the pwd of the job
            argTemp = argTemplate + ' -l ' + os.path.basename(listName)

            submitter.aux_input.append(listName)

            for fileset in picker.filesets:
                submitter.job_args.append(argTemp % (picker.sample.name, fileset))
                submitter.job_names.append('%s_%s' % (picker.sample.name, fileset))
    
                # clean up old .log files
                logpath = '/local/' + os.environ['USER'] + '/ssw2/' + picker.sample.name + '_' + fileset + '.0.log'
                logger.debug('Removing %s', logpath)
                try:
                    os.remove(logpath)
                except:
                    pass

        self._submit(submitter, 'skim', argTemplate, noWait, autoResubmit)


if __name__ == '__main__':
    import sys
    import socket
    import time
    import shutil
    import collections
    import logging
    from argparse import ArgumentParser
    
    argParser = ArgumentParser(description = 'Plot and count')
    argParser.add_argument('args', metavar = 'ARGS', nargs = '+', help = 'List of samples followed by list of events.')
    argParser.add_argument('--event-list', '-l', metavar = 'PATH', dest = 'eventLists', nargs = '+', default = [], help = 'List events in a file instaed of passing in command line.')
    argParser.add_argument('--filesets', '-f', metavar = 'ID', dest = 'filesets', nargs = '+', default = [], help = 'Fileset id to run on.')
    argParser.add_argument('--files', '-i', metavar = 'PATH', dest = 'files', nargs = '+', default = [], help = 'Directly run on files.')
    argParser.add_argument('--batch', '-B', action = 'store_true', dest = 'batch', help = 'Use condor-run to run.')
    argParser.add_argument('--nentries', '-N', metavar = 'N', dest = 'nentries', type = int, default = -1, help = 'Maximum number of entries.')
    argParser.add_argument('--no-wait', '-W', action = 'store_true', dest = 'noWait', help = '(With batch option) Don\'t wait for job completion.')
    argParser.add_argument('--print-every', '-e', metavar = 'NEVENTS', dest = 'printEvery', type = int, default = 10000, help = 'Print frequency.')
    argParser.add_argument('--printlevel', '-p', metavar = 'LEVEL', dest = 'printLevel', default = 'WARNING', help = 'Override config.printLevel.')
    argParser.add_argument('--read-remote', '-R', action = 'store_true', dest = 'readRemote', help = 'Read from root://xrootd.cmsaf.mit.edu if a local copy of the file does not exist.')
    argParser.add_argument('--resubmit', '-S', action = 'store_true', dest = 'autoResubmit', help = '(Without no-wait option) Automatically release held jobs.')
    argParser.add_argument('--skip-missing', '-K', action = 'store_true', dest = 'skipMissing', help = 'Skip missing files in skim.')
    argParser.add_argument('--uw-format', '-U', action = 'store_true', dest = 'uwFormat', help = 'Print event list in run:event:lumi format.')
    
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

    snames = []
    eventIds = []
    for arg in args.args:
        matches = re.match('([0-9]+):([0-9]+):([0-9]+)', arg)
        if matches:
            if args.uwFormat:
                eventIds.append((int(matches.group(1)), int(matches.group(3)), int(matches.group(2))))
            else:
                eventIds.append((int(matches.group(1)), int(matches.group(2)), int(matches.group(3))))
        else:
            snames.append(arg)

    if len(eventIds) == 0 and len(args.eventLists) == 0:
        logger.error('No events specified to pick.')
        sys.exit(1)

    ## directories to include
    thisdir = os.path.dirname(os.path.realpath(__file__))
    basedir = os.path.dirname(thisdir)
    monoxdir = os.path.dirname(basedir)
    
    ## import the monophoton config
    sys.path.append(basedir)
    import config

    ## set up logger
    printLevel = getattr(logging, args.printLevel.upper())
    args.printLevel = printLevel # gets passed to SkimSlimWeight.config

    logging.basicConfig(level = printLevel)
    logger = logging.getLogger(__name__)

    logger.debug('Running at %s', socket.gethostname())

    ## set up global configurations with args and config
    for key in dir(args):
        if not key.startswith('_'):
            PickEvent.config[key] = getattr(args, key)

    for key in dir(config):
        if not key.startswith('_'):
            PickEvent.config[key] = getattr(config, key)

    PickEvent.config['outDir'] = os.path.dirname(config.skimDir) + '/pickevent'

    ## set up samples and selectors
    import datasets

    samples = datasets.allsamples.getmany(snames)

    ## compile and load the event picker
    import ROOT
    ROOT.gSystem.Load('libPandaTreeObjects.so')

    ## need to instantiate ROOT.panda (otherwise CLING segfaults)
    e = ROOT.panda.Event

    ROOT.gROOT.LoadMacro(os.path.dirname(os.path.realpath(__file__)) + '/EventPicker.cc+')

    try:
        p = ROOT.EventPicker
    except:
        logger.error("Couldn't compile EventPicker.cc. Quitting.")
        sys.exit(1)

    ## construct and run PickEvent objects
    pickers = []
    for sample in samples:
        if len(args.files) != 0:
            files = True
            flist = args.files
        else:
            files = False
            flist = args.filesets

        if len(flist) == 0:
            flist = sample.filesets()

        picker = PickEvent(sample, flist, files)

        if not picker.setupSkim():
            logger.warning('Failed to set up skim job for %s', sample.name)
            continue

        picker.eventIds = eventIds
        for eventList in args.eventLists:
            picker.readEventList(eventList, args.uwFormat)

        pickers.append(picker)

    if args.batch:
        ## job submission only
        print 'Submitting jobs.'

        ## load condor-run
        sys.path.append('/home/yiiyama/lib')
        from condor_run import CondorRun

        batchManager = PickEventBatchManager(pickers, args.skipMissing, args.readRemote)
        batchManager.submitSkim(args.noWait, args.autoResubmit)

        if args.noWait:
            print 'Jobs have been submitted.'
        else:
            print 'All jobs finished.'

    else:
        print 'Picking events.'
        for picker in pickers:
            picker.executeSkim()
