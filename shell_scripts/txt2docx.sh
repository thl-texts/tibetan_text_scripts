#! /bin/bash

indir=$1
outdir=$2
echo "$indir", "$outdir"
for txtdoc in "$indir"/*.txt
do
   dnm=$(basename "$txtdoc" .txt)
   echo textutil -convert docx -output "$outdir/$dnm.docx" "$txtdoc"
   textutil -convert docx -output "$outdir/$dnm.docx" "$txtdoc"

done

