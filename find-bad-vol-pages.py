from os.path import join
import argparse
from tibtexts.ocrvol import OCRVol

parser = argparse.ArgumentParser(description='Insert Milestones from OCR in Unicode Docs')
parser.add_argument('-v', '--vol', required=True,
                    help='The Volume Number')
args = parser.parse_args()


if __name__ == "__main__":
    kwargs = vars(args)
    volnum = kwargs['vol']
    volfilenm = "kama-ocr-vol-{}.txt".format(str(volnum).zfill(3))
    volpath = join('resources', 'ocr', volfilenm)
    volobj = OCRVol(volpath)
    volobj.print_stats()
