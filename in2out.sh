#! /bin/bash

indir="in"
outdir="out"
inform=$1
outform=$2
echo $indir, $outdir
for indoc in $indir/*.$inform
do
   dnm=$(basename $indoc .$inform)
   echo textutil -convert $outform -output "$outdir/$dnm.$outform" "$indoc"
   textutil -convert $outform -output "$outdir/$dnm.$outform" "$indoc"

done

