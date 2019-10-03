from os import listdir, mkdir, path
import shutil
import re

indir = 'in/kama-vol-chunks'
outdir = 'out/kama-vol-chunks-renum'
pattern = re.compile('KAMA-(\d+)-(\d?)-?')

for fl in listdir(indir):
    if fl.endswith('.docx'):
        mtch = pattern.match(fl)
        if mtch:
            src = path.join(indir, fl)
            volnum = int(mtch.group(1))

            if volnum == 40:
                # If it's 40-1, then renumber as 40
                if int(mtch.group(2)) == 1:
                    outfl = fl.replace('KAMA-040-1', 'KAMA-040')
                    dest = path.join(destpath, outfl)
                else:
                    # If it's 40-2, then renumber as 41
                    volnum = 41
                    outfl = fl.replace('KAMA-040-2', 'KAMA-041')
                    dest = path.join(destpath, outfl)
            elif volnum > 40:
                # everything over 40 is off by one, so add one.
                oldvnum = str(volnum).zfill(3)
                volnum += 1
                newvnum = str(volnum).zfill(3)
                outfl = fl.replace('KAMA-{}-'.format(oldvnum), 'KAMA-{}-'.format(newvnum))

            else:
                # Before 40, just use the volnum as is
                outfl = fl
                dest = path.join(destpath, fl)

            destpath = path.join(outdir, 'kama-v{}'.format(str(volnum).zfill(3)))
            if not path.exists(destpath):
                mkdir(destpath)
            dest = path.join(destpath, outfl)
            shutil.copy(src, dest)

print("Done!")
