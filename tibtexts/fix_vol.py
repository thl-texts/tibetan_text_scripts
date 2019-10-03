import re

def getvol(pth):
    with open(pth, 'r') as volstream:
        lines = volstream.readlines()
    return lines


def renumberpgs(vol, startat, diff=0, renumfrom=-1):
    '''
    Takes an ocrvol and renumber pages beginning at a certain point
    :param vol:
    :param startat:
    :param diff:
    :param renumfrom:
    :return:  OCRVol
    '''
    outvol = []
    renumbering = False
    renumfrom = int(renumfrom) if renumfrom > -1 else False
    for ln in vol:
        mtch = re.search(r'/out_(\d+)\.tif', ln)
        if mtch:
            nm = int(mtch.group(1))
            if nm == startat:
                renumbering = True
            if renumbering:
                newnum = str(renumfrom).zfill(4)
                ln = ln.replace(mtch.group(1), newnum)
                renumfrom += 1
            elif nm >= startat:
                nm += diff
                nm = str(nm).zfill(4)
                ln = ln.replace(mtch.group(1), nm)
        outvol.append(ln)
    return outvol


if __name__ == '__main__':
    volnm = 'resources/kama-ocr-vol-107.txt'
    volin = getvol(volnm)
    volout = renumberpgs(volin, 449, renumfrom=445)
    voloutnm = 'out/kama-ocr-vol-107-renum.txt'
    with open(voloutnm, 'w') as outf:
        outf.writelines(volout)
