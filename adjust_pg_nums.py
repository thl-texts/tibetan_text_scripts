"""
A script to adjust page numbers by a certain augment starting at a certain point
Works on Word Docs with milestones inserted and changes both page and line milestones in selected range
"""

import os
import argparse
import shutil
from docx import Document
import re


parser = argparse.ArgumentParser(description='Augment milestone numbers in a certain range')
parser.add_argument('-d', '--delta', default=1, type=int,
                    help='The change in the page number')
parser.add_argument('-s', '--start', default=1, type=int,
                    help='The page to start at')
parser.add_argument('-e', '--end', type=int,
                    help='The page to end at, if any')
parser.add_argument('-nb', '--no-backup', action='store_true',
                    help='Do not make a backup file')
parser.add_argument('-p', '--path', default='workspace/out',
                    help='Path to document')
parser.add_argument('doc', help="File name of the document")
args = parser.parse_args()


if __name__ == "__main__":
    mspattern = re.compile('\[(\d+)(\.?\d*)\]')
    kwargs = vars(args)
    filenm = kwargs['doc']
    filepath = kwargs['path']
    docpath = os.path.join(filepath, filenm)
    if not kwargs['no_backup']:
        bknm = filenm.replace('.doc', '-bak.doc')
        bkpath = os.path.join(filepath, bknm)
        shutil.copy(docpath, bkpath)
        print("Backup at: {}".format(bkpath))
    stnum = kwargs['start']
    endnum = kwargs['end']
    delta = int(kwargs['delta'])
    chngct = 0

    print("Updating document: {} \n"
          "{} {} "
          "starting at page {} and "
          "ending at {}".format(
                filenm,
                "Adding" if delta > 0 else "Subtracting",
                delta,
                stnum,
                endnum if endnum is not None else "the end of the document"
            ))

    doc = Document(docpath)
    for p in doc.paragraphs:
        for r in p.runs:
            mtchs = re.search(mspattern, r.text)
            if mtchs:
                pgnum = int(mtchs.group(1))
                lnstr = mtchs.group(2)
                if pgnum >= stnum and (endnum is None or pgnum <= endnum):
                    r.text = "[{}{}]".format(pgnum + delta, lnstr)
                    chngct += 1

    doc.save(docpath)
    print("{} milestones changed!".format(chngct))

