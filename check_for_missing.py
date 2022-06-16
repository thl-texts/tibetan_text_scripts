from os import listdir, mkdir, path
from docx import Document
import shutil
import re

"""
Script to check for missing pages in a volume
"""

vnum = "002"
src_folder = "/Users/thangrove/Documents/Sandbox/THL/Projects/Kama/Kama-Unicode/Docx/Vol Chunks Paged/Kama-vols-001-020/KAMA-vol-002"
filelist = listdir(src_folder)
filelist = [f for f in filelist if f.endswith('.docx') and not f.startswith('~')]
filelist.sort()

pagenums = []
for fnm in filelist:
    print(f"\rDoing {fnm} ....", end="")
    fpth = path.join(src_folder, fnm)
    wdoc = Document(fpth)
    for p in wdoc.paragraphs:
        for r in p.runs:
            if r.style.name == 'Page Number Print Edition':
                pgtxt = r.text.strip(' []')
                pg = int(pgtxt) if pgtxt.isnumeric() else pgtxt
                pagenums.append(pg)
print("\n")
print(f"There are {len(pagenums)} pages. Last page: {pagenums[-1]}")

# Calculate missing pages
missing = []
lastpg = 0
for pgn in pagenums:
    if pgn > lastpg + 1:
        for n in range(lastpg + 1, pgn):
            missing.append(n)
    lastpg = pgn

# Print out file of missing pages
mpg_file = f'./workspace/out/pglist-km-v{vnum}.txt'
print(f"{len(missing)} Missing pages list recorded at {mpg_file}:")
with open(mpg_file, 'w') as pout:
    for mpg in missing:
        # print(f"{mpg}")
        pout.write(f"{mpg}\n")



