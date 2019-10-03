'''
Testing the insertion of milestones
'''

from univol import UniVol
from fuzzysearch import find_near_matches
from os import getcwd, listdir
from os.path import join
import datetime
from math import ceil
import logging


def check_ms_in_dir(dirin):
    badplacements = []
    ct = 0
    for fl in listdir(dirin):
        ct += 1
        print("Doing {}".format(fl))
        badplacements += ["\n********* File {} ***********\n".format(fl)]
        badplacements += check_milestones(join(dirin, fl))
    badplacements.append(ct)
    return badplacements


def check_milestones(fl):
    with open(fl, 'r') as fin:
        chunktxt = fin.read()
    chunkpts = chunktxt.split('[')
    badplaces = []
    for n, pt in enumerate(chunkpts):
        if len(pt) > 0 and pt[-1] not in '་། []' and n < len(chunkpts) - 1:
            nextchunk = chunkpts[n + 1]
            ms = nextchunk[:nextchunk.find(']')]
            badplaces.append("{} not after tsek but after {}\n".format(ms, pt[-1]))
    return badplaces


if __name__ == '__main__':
    volnum = input("Enter the volume number: ")
    if volnum:
        indir = 'out'
        results = check_ms_in_dir(indir)
        filect = results.pop()
        badlinect = len(results) - filect
        lognm = 'logs/kama-vol-{}-bad-placement.log'.format(volnum)
        with open(lognm, 'w') as logout:
            logout.write("There were {} bad placements in volume {}\n------------------\n".format(badlinect, volnum))
            logout.writelines(results)

