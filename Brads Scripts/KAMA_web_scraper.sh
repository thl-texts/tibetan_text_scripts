#!/usr/bin/env bash
# Created by Tom Sharp, June 2019

# For volumes 100-109 you need to run this script without
# the final 'rm' commands because those volumes do not have
# the same dedication and the rm command will delete the
# actual text. You will have to change the {1..133} below to 
# {100..109}, supress rm KMG*/KMG*ad by making it a comment below, 
# and then delete the already-downloaded KMG100-109
# directories and run the script again.  

# For each volume...
for i in {1..133}; do
  # Get the volume name with leading zeros, e.g. KMG005
  name=KMG`printf %03d $i`;
  echo "Preparing to operate on $name";
  # Make a new directory to put the volume's texts in.
  mkdir $name;
  cd $name;
  # Download the volume's print view and split texts into
  # separate files on the assumption that the h2 HTML tag
  # delimits a text.
  curl "http://nitarthadigitallibrary.org/xtf/view?docId=tei/$name/$name.xml&doc.view=print;chunk.id=0" | split -p h2 - $name;
  # Find the name of the last file in the directory.
  fname=`/bin/ls | tail -n 1`;
  echo "Preparing to strip last line from $fname"
  # Strip off the last line of the last file, to remove
  # HTML footers.
  sed '$d' $fname > tmp;
  # Move the temporary file back to the original place.
  mv tmp $fname
  cd ..;
done

# Delete the front matter, including various bits of
# HTML junk and the dedications.
rm KMG*/KMG*aa;
rm KMG*/KMG*ab;
rm KMG*/KMG*ac;
rm KMG*/KMG*ad;

