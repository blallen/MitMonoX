#!/bin/bash

DIR=$1
FILESET_SIZE=$2

DATASET=$(basename $DIR)
VERSION=$(basename $(dirname $DIR))
BOOK=pandaf/$VERSION

MONOPHDIR=$(dirname $(cd $(dirname $0); pwd))

CATALOGDIR=$MONOPHDIR/data/catalog/$BOOK/$DATASET
mkdir -p $CATALOGDIR
rm -f $CATALOGDIR/*

i=0
ls $DIR | while read line
do
  N=$(root -b -q -l $MONOPHDIR/misc/num_events.C'("'$DIR/$line'")' | tail -n 1)
  if [ $? -ne 0 ]
  then
    echo "File $line corrupted"
    continue
  fi
  echo $(printf %04d $(($i/$FILESET_SIZE))) $line $N $N 1 1 1 1 >> $CATALOGDIR/Files
  i=$(($i+1))
done

MAXFS=$(tail -n 1 $CATALOGDIR/Files | sed 's/^0*\([0-9]*\) .*/\1/')
[ "$MAXFS" ] || MAXFS=0

URL=root://t3serv006.mit.edu/$(echo $DIR | sed 's|/mnt/hadoop||')

i=0
while [ $i -le $MAXFS ]
do
  echo $(printf %04d $i) $URL 1 1 1 1 1 1 >> $CATALOGDIR/Filesets
  i=$(($i+1))
done
