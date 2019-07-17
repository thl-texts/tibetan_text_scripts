#! /bin/bash

indir=$1
outdir=$2
echo $indir, $outdir
for rtfdoc in $indir/*.rtf
do
   dnm=$(basename $rtfdoc .rtf)
   echo textutil -convert docx -output $outdir/$dnm.docx $rtfdoc
   textutil -convert docx -output $outdir/$dnm.docx $rtfdoc

done

