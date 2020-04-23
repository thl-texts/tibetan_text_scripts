"""
A chunk of pages in vol 14 are reversed 505 through 550 got fed into the OCR scanner backwards
So scan 506.tif is page 550 and the proceed downard until 551.tif is page 505.
This script is an attempt to reverse the OCR so that the text properly convert

Date: 4/24/20
"""

inpath = 'workspace/in/kama-vol-014-rev-505-550.txt'
outpath = 'workspace/out/kama-vol-014-fixed-505-550.txt'
headlines = []
pages = []
pg = []
with open(inpath, 'r') as txtin:
    for ln in txtin:
        if ln.startswith('tbocrtifs'):
            if pg:
                pages.append(pg)
                pg = []
            headlines.append(ln)
        else:
            pg.append(ln)
    if pg:
        pages.append(pg)

pages = [pg for pg in reversed(pages)]

with open(outpath, 'w') as txtout:
    pgnum = 0
    for hl in headlines:
        txtout.write(hl)
        if len(pages) > pgnum:
            for ln in pages[pgnum]:
                txtout.write(ln)
        else:
            print("pgnum {} higher than pages {}".format(pgnum, len(pages)))
            break
        pgnum += 1

print("Done. \nTotal pages in array: {}\nTotal pages out: {}".format(len(pages), (pgnum+1)))
