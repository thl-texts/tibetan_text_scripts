"""
Script created to rename and reorganize files. Originally created for Taranatha but could be modified for other uses
"""
import os
from os.path import isdir, join
import re
import shutil

# Taranatha File Renaming
# rootdir = '/Users/thangrove/Documents/Sandbox/THL/Taranatha/Originals'
# pdfdir = '/Users/thangrove/Documents/Sandbox/THL/Taranatha/Renamed/pdfs'
# textdir = '/Users/thangrove/Documents/Sandbox/THL/Taranatha/Renamed/texts'
# miscdir = '/Users/thangrove/Documents/Sandbox/THL/Taranatha/Renamed/misc'
# filepat = r'^\[?\(?(\d+)\)?\]?\.doc'
# fileprefix = 'tn-pk'

# Dolpopa File Renaming
rootdir = '/Users/thangrove/Documents/Sandbox/THL/Dolpopa/Originals'
pdfdir = '/Users/thangrove/Documents/Sandbox/THL/Dolpopa/Renamed/pdfs'
textdir = '/Users/thangrove/Documents/Sandbox/THL/Dolpopa/Renamed/texts'
miscdir = '/Users/thangrove/Documents/Sandbox/THL/Dolpopa/Renamed/misc'
filepat = r'^\[?(\d+)[^\.]*\.+doc'
# find files that optionally start with [, then a number followed by any number of non-period characters, followed by
# one or many periods followed by "doc" (Need to ignore case because some have DOC)
fileprefix = 'dpp'

# Get list of all dirs in root folders
dirs = [d for d in os.listdir(rootdir) if isdir(join(rootdir, d))]
dirs.sort()

# Make a dictionary keyed on the vol number (as string) determined from regular expression on dir name
dirlist = {}
for dnm in dirs:
    mtch = re.match(r'^\[(\d+)', dnm)
    if mtch:
        vnm = mtch.group(1)
        dirlist[vnm] = dnm

# Get the dictionary keys and sort as integers
dkeys = [int(k) for k in dirlist.keys()]
dkeys.sort()

# Iterate through dictionary of dirs with integer-sorted keys converted back to strings
c = 0
for dnum in dkeys:
    c += 1
    dk = str(dnum)
    print("Doing Volume {} --> Directory: {}".format(dk, dirlist[dk]))
    currdir = join(rootdir, dirlist[dk])
    for flnm in os.listdir(currdir):
        if flnm.startswith('~') or flnm.startswith('.') or flnm.endswith('.tmp'):
            continue
        src = join(currdir, flnm)
        mtch = re.match(filepat, flnm, re.I)
        if ".pdf" in flnm:
            dest = join(pdfdir, "{}-v{}-{}".format(fileprefix, dk.zfill(2), flnm))
            # print("moving {} to {}".format(src, dest))
            shutil.copy(src, dest)

        elif mtch:
            dest = join(textdir, "{}-v{}-t{}.doc".format(fileprefix, dk.zfill(2), mtch.group(1).zfill(2)))
            # print("moving {} to {}".format(src, dest))
            shutil.copy(src, dest)

        else:
            dest = join(miscdir, "{}-v{}-{}".format(fileprefix, dk.zfill(2), flnm))
            # print("moving {} to {}".format(src, dest))
            shutil.copy(src, dest)




