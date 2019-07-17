#!/bin/env bash
# Created by Bradley Aaron, July 8, 2019

# Before executing this script, first run the KAMA_web_scraper.sh script.

# You must install pandoc and create the templates directory and copy the 
# default.docx file provided with this script into the ~/.pandoc/templates directory.

# Find all files in a folder that are NOT a script or DS Store file and then
# set them up to be processed.
for i in $(find . \! -name "*.sh" \! -name ".DS_Store" -type f); do
  # run pandoc to create html files on each file in the directory
  echo "$i" && pandoc +RTS -K100000000 -RTS --standalone $i --output $i.html --quiet;
  echo "Converting $i to HTML..."; 		
done

# Find all html files in a folder and convert them into docx files.
for f in $(find . -name "*.html"); do
  echo "$f" && pandoc +RTS -K100000000 -RTS --reference-doc ~/.pandoc/templates/default.docx --standalone $f --output $f.docx;
  echo "Converting $f to DOCX...";
done

# Remove all html files after conversion to docx.
echo "Removing all HTML files...";
find . -type f -name '*.html' -delete;

# Remove the ".html" from the filename to leave only "*.docx".
echo "Renaming files..."; 
mmv ';*.html.docx' '#1#2.docx';

# Remove all files that aren't *.docx.
echo "Cleaning everything up...";
find . -type f ! -name '*.docx' ! -name '.DS_Store' ! -name '*.sh' -delete;

