#!/bin/bash

TEST=$1

CWD=$(pwd)

cd $(dirname $(cd $(dirname $0); pwd))
SKIMDIR=$(python -c "import config; print config.skimDir")
LOCALDIR=$(python -c "import config; print config.localSkimDir")

for FILE in $(rsync -nuv $SKIMDIR/*.root $LOCALDIR/ | grep .root)
do
  echo $FILE
  if [ $TEST ]
  then
    echo rm $LOCALDIR/$FILE
    echo hdfs dfs -fs hdfs://t3serv002.mit.edu:9000 -get $(echo $SKIMDIR | sed 's|/mnt/hadoop||')/$FILE $LOCALDIR/$FILE
  else
    rm $LOCALDIR/$FILE 2> /dev/null
    hdfs dfs -fs hdfs://t3serv002.mit.edu:9000 -get $(echo $SKIMDIR | sed 's|/mnt/hadoop||')/$FILE $LOCALDIR/$FILE
  fi
done
