#! /bin/bash

indir=$1
outdir=$2
echo $indir, $outdir
for doc in $indir/*.doc
do
   dnm=$(basename $doc .doc)
   echo textutil -convert rtf -output $outdir/$dnm.rtf $doc
   textutil -convert rtf -output $outdir/$dnm.rtf $doc

done

