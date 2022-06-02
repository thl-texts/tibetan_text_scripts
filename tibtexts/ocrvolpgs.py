import re
from os.path import join

class OCRVol:
    """
        A class to handle OCR Tibetan volumes for looking up and retrieving pages
        Used to get chunks of texts with milestones from OCR, for missing or corrupted sections
    """

    def __init__(self, volnum, offset=0,
                 folder="/Users/thangrove/Documents/Sandbox/THL/XML/TibetanTextScripts/resources/ocr",
                 fileprefix="kama-ocr-vol-",
                 pgpattern=r'[_\-\.](\d{4})[_\-\.]'):
        # Volume text file path
        self.volnum = volnum
        self.offset = int(offset)
        self.folder = folder
        self.fileprefix = fileprefix
        self.filename = f"{self.fileprefix}{str(self.volnum).zfill(3)}.txt"
        self.file = join(self.folder, self.filename)
        self.pgpattern = pgpattern
        self.pages = []
        self.filelines = []

    def load_pages(self):
        with open(self.file, 'r') as filein:
            self.filelines = filein.readlines()
        pglns = []
        # ocrpgnum is the number of the image file listed in the OCR. This is stored in the page object
        ocrpgnum = 0  # any prefatory lines with a ocr page num are considered page 0
        for ln in self.filelines:
            ln = ln.strip()
            match = re.search(self.pgpattern, ln)
            if match:
                pgobj = {
                    "lines": pglns,
                    "ocrnum": int(ocrpgnum)
                }
                self.pages.append(pgobj)
                ocrpgnum = match.group(1)
                pglns = []

            elif len(ln) > 0:
                pglns.append(ln)

    def get_page(self, pgnum):
        try:
            pgnum = int(pgnum)
            ocrpg = pgnum + self.offset
            print("ocrpg: " + str(ocrpg))
            pgobj = self.pages[ocrpg]
            if ocrpg != pgobj['ocrnum']:
                print("ocr page numbers do not match. calculated: {}, pageobj: {}".format(ocrpg, pgobj['ocrnum']))
            return pgobj['lines']
        except ValueError as ve:
            print("Page num must be an integer in OCRVol.get_page. {} given: ‘{}’".format(type(pgnum), pgnum))
        except IndexError as ie:
            print("Page {} does not exist".format(pgnum))

    def get_last(self):
        return len(self.pages) - self.offset


if __name__ == "__main__":
    vnum = 20
    myvol = OCRVol(vnum, 4)
    myvol.load_pages()
    print("There are {} lines".format(len(myvol.filelines)))
    pg1 = myvol.get_page(5)
    print(pg1)
