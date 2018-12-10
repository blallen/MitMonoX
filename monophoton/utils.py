import os
import config

def getSkimPath(sample, skim, primary = config.skimDir, alternative = config.localSkimDir):
    # Return merged skim file name
    sourceName = os.path.join(primary, sample + '_' + skim + '.root')
    if alternative:
        altName = os.path.join(alternative, sample + '_' + skim + '.root')
        if os.path.exists(altName) and os.stat(altName).st_mtime > os.stat(sourceName).st_mtime:
            sourceName = altName

    return sourceName

def getSkimPaths(sample, skim, primary = config.skimDir, alternative = config.localSkimDir):
    # Return pre-merge skim file names
    paths = {}

    if alternative:
        altDir = os.path.join(alternative, sample)
        if os.path.isdir(altDir):
            for fname in os.listdir(altDir):
                if fname.startswith(sample) and fname.endswith('_' + skim + '.root'):
                    altName = os.path.join(altDir, fname)
                    paths[fname] = (altName, os.stat(altName).st_mtime)

    primDir = os.path.join(primary, sample)
    for fname in os.listdir(primDir):
        if fname.startswith(sample) and fname.endswith('_' + skim + '.root'):
            primName = os.path.join(primDir, fname)
            mtime = os.stat(primName).st_mtime
            if fname in paths:
                if mtime > paths[fname][1]:
                    paths[fname] = (primName, mtime)
            else:
                paths[fname] = (primName, mtime)

    return [p[0] for p in paths.itervalues()]
