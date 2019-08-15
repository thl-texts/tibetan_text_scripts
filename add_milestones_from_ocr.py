"""
This script adds milestones from OCR volume files into converted Sambhota files

"""
import re
import os
import glob
import math
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def read_in_ocr(inpath):
    """
    Takes a volume ocr doc from Zach and reads it into a dictionary keyed by pgnum strings "0001" etc. with values
    of a list of lines. To reference a page you need a zero-filled string of the page num. This gives you a list of
    lines where pagevar[0] is the first line pagevar[1] is the second, etc.

    :param inpath:
    :return:
    """
    outdoc = {}
    pagelns = []
    firstpg = 0
    pgnm = '0'
    with open(inpath, 'r') as fin:
        for ln in fin:
            ln = ln.strip()
            if '.tif' in ln:
                mtch = re.search(r'kama-vol-\d+/out__(\d+)', ln)
                if mtch:
                    if len(pagelns) > 0:
                        outdoc[pgnm] = pagelns.copy()
                        pagelns = []
                    pgnm = mtch.group(1)
                    if firstpg == 0:
                        firstpg = int(pgnm)
                    continue
            ln = ln.replace('༄༅། ', '')
            if len(ln) > 0:
                pagelns.append(ln)
        if len(pagelns) > 0 and pgnm not in outdoc:
            outdoc[pgnm] = pagelns.copy()
    return firstpg, outdoc


def read_in_chunk(cpath):
    intxt = ''
    with open(cpath, 'r') as fin:
        for ln in fin:
            ln = ln.strip()
            intxt += ln
    return intxt


def find_pages(unidocin, last_index, pagedref, firstpg):
    pagepos = {}
    numpgs = len(pagedref.keys())
    endpg = firstpg + numpgs - 1
    for n in range(firstpg, endpg + 1):
        pgkey = str(n).zfill(4)
        if pgkey not in pagedref:
            continue
        pglines = pagedref[pgkey]
        for x, ln in enumerate(pglines):
            # print("doing {}.{}".format(n, x + 1))
            tmpln = ln.lstrip('༄༅། ')
            foundpos = unidocin.find(tmpln, last_index)
            ct = 0
            while foundpos == -1:
                ct += 1
                tmpln = tmpln.split('་')
                tmpln.pop()
                if len(tmpln) == 1:
                    foundpos = unidocin.find(tmpln[0], last_index)
                    break
                elif len(tmpln) == 0:
                    break

                tmpln = '་'.join(tmpln)
                foundpos = unidocin.find(tmpln, last_index)
                if ct > 200:
                    print("Stuck in a line... {}")
                    break

            if foundpos > -1:
                # print("Found with {} characters".format(len(tmpln)))
                linekey = "{}.{}".format(n, x + 1)
                pagepos[foundpos] = linekey
                last_index += len(ln)

            if last_index > len(unidocin) - 20:
                break
        if last_index > len(unidocin) - 20:
            break

    poses = list(pagepos.keys())
    poses.sort(reverse=True)
    for ps in poses:
        ms = '{}'.format(pagepos[ps])
        pms = '[{}]'.format(ms.replace('.1', '')) if '.1' in ms else ''
        ms = pms + '[{}]'.format(ms)
        # print(ms)
        unidocin = unidocin[:ps] + ms + unidocin[ps:]
    return last_index, unidocin


def do_milestones(file_list, paged_doc, first_pg):
    pagepos = {}
    current_doc_num = 0
    current_doc_path = file_list[current_doc_num]
    current_doc = read_in_chunk(current_doc_path)
    current_index = 0
    current_vol_pos = 0
    pgnms = list(paged_doc.keys())
    for pgkey in pgnms:
        pglines = paged_doc[pgkey]
        for lnnm, ln in enumerate(pglines):
            milestone = "{}.{}".format(int(pgkey), lnnm + 1)
            tmpln = ln.lstrip('༄༅། ')
            ind = find_line_in_doc(tmpln, current_doc, current_index)
            if ind == -1:
                print("{} not found".format(milestone))
            else:
                pagepos[ind] = milestone
                current_index = ind + len(ln) - 1
            if current_index > current_vol_pos + len(current_doc) - 25:
                break

        if current_index > current_vol_pos + len(current_doc) - 25:
            print("End of doc {} reached".format(current_doc_path))
            add_milestones(current_doc_path, current_doc, pagepos)
            current_vol_pos = current_index
            current_doc_num += 1
            if current_doc_num < len(file_list):
                current_doc_path = file_list[current_doc_num]
                current_doc = read_in_chunk(current_doc_path)
                pagepos = {}
            else:
                break


def find_line_in_doc(linein, current_doc, current_index):
    pos = -1
    # Start at end and slowly shrink search string to 1/2 length until found
    for n in range(0, math.floor(len(linein) / 2)):
        tmpln = linein[:n]
        pos = current_doc.find(tmpln, current_index)
        if pos > -1:
            break

    # Do the same kind of truncation from beginning
    if pos == -1:
        for n in range(0, math.floor(len(linein) / 2)):
            tmpln = linein[n:]
            pos = current_doc.find(tmpln, current_index)
            if pos > -1:
                pos += n
                break

    return pos


def add_milestones(current_doc_path, out_doc, pagepos):
    outpath = current_doc_path.replace('in/', 'out/')
    indexes = list(pagepos.keys())
    indexes.sort(reverse=True)
    for ind in indexes:
        msstr = pagepos[ind]
        pgstr = "[{}]".format(msstr.replace('.1','')) if '.1' in msstr else ''
        out_doc = out_doc[:ind] + "{}[{}]".format(pgstr, msstr) + out_doc[ind:]
    with open(outpath, 'w') as fout:
        fout.write(out_doc)


def update_volume(ocrfl, docmatch):
    # Read in ocred volume
    fpg, ocrdoc = read_in_ocr(ocrfl)
    # Get all the volume chunks where milestones will go
    docpath = os.path.join('in', docmatch)
    print(os.getcwd())
    print(docpath)
    fls = glob.glob(docpath)
    fls.sort()
    if len(fls) > 0:
        do_milestones(fls, ocrdoc, fpg)
    else:
        print("No files globbed! Check your pattern!")


if __name__ == '__main__':
    ocrpath = 'test/kama-ocr-v2-in.txt'
    update_volume(ocrpath, "KAMA-002-*.txt")
    print("Done")

