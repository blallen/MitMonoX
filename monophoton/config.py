import os

config = 'GGHDarkPhoton2017'
#config = 'TagAndProbe2017'

# this installation
baseDir = os.path.dirname(os.path.realpath(__file__))

# location of skim output from ssw2
skimDir = '/mnt/hadoop/scratch/' + os.environ['USER'] + '/' + config + '/skim'

# optionally copy to a local disk to speed up
localSkimDir = '/local/' + os.environ['USER'] + '/' + config + '/skim'

# where the various output plots and text files
histDir = '/data/t3home000/' + os.environ['USER'] + '/' + config

# subdirectory of cmsplots.php
plotDir = config

# panda library
libobjs = 'libPandaTreeObjects.so'

# MultiDraw library
libmultidraw = '/home/yiiyama/cms/tools/multidraw/libmultidraw.so'
