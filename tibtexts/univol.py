import os
import os.path
import re
import logging


class UniVol:
    line_length_add = 30

    # Combining marks that follow many syllables in the Unicode docs. They eat the fuzzy-match
    # budget and inflate raw length, so searches run on a copy with them stripped.
    search_ignore = '\u0f35\u0f37'

    normalize_pairs = (
        ('༌', '་'),  # nb tsek to regular tsek
        ('༴', '།'),
        ('༏', '།'),
        ('༐', '།'),
        ('༑', '།'),
    )

    def __init__(self, fpath, avglnlen):
        self.text = ''
        self.path = fpath
        pthpts = fpath.split('/')
        self.filename = pthpts.pop()
        self.outname = self.filename.replace('.txt', '-pgd.txt')
        self.dir = '/'.join(pthpts)
        self.avglnlen = avglnlen
        self.index = 0
        self.chunk_map = []  # stripped-chunk index -> offset from self.index in the raw text
        with open(self.path, 'r') as fin:
            for ln in fin:
                ln = ln.strip()
                self.text += ln
        # remove the ྅྅྅྅྅PAGE # at end of Unicode Word docs
        self.text = re.sub(r'[྅྄]{4,}[\s\w]+$', '', self.text)
        if '྅྅྅྅྅྅྅྅྅྅྅྅྅' in self.text:
            pts = self.text.split('྅྅྅྅྅྅྅྅྅྅྅྅྅')
            self.text = pts[0]
        self.written = False

    def get_length(self):
        return len(self.text)

    def get_search_chunk(self, factor=2, skipped=0):
        """
        Get a chunk of text within which to search for a line beginning
        :param factor: The factor multiplied with the average line length to get the size of the chunk
        :param skipped: Previous number of lines skipped
        :return:
        """
        if skipped > 0:  # Some ocr lines don't come through and are just 2 or 3 characters long, these are skipped
            augment = int(self.avglnlen * skipped * 0.5)
            logging.debug("{} Lines skipped. Index is {}, Adding {}".format(skipped, self.index, augment))
            self.index += augment
            # self.index += int(self.avglnlen * skipped * 0.8) # old augment
            factor = skipped * 1.5
        chunk_start = self.index
        # Size the window in searchable chars (combining marks don't count), keeping a map back
        # to raw offsets so the match can be inserted at the right place in the raw text.
        max_chars = int(self.avglnlen * factor)
        chars = []
        self.chunk_map = []
        for off, ch in enumerate(self.text[chunk_start:chunk_start + max_chars * 2]):
            if ch in self.search_ignore:
                continue
            if len(chars) >= max_chars:
                break
            chars.append(ch)
            self.chunk_map.append(off)
        return self.clean_chunk(''.join(chars))

    def raw_offset(self, chunk_ind):
        """Convert an index in the last chunk from get_search_chunk to an offset from self.index"""
        if chunk_ind < len(self.chunk_map):
            return self.chunk_map[chunk_ind]
        return chunk_ind

    def clean_chunk(self, chnk):
        for pair in self.normalize_pairs:
            chnk = chnk.replace(pair[0], pair[1])
        return chnk

    def insert_milestone(self, ms, ind, line_len):
        pretext = self.text[:ind]
        posttext = self.text[ind:]
        # Check for various abnormal situations, when the preceding character is not a syllable break
        if len(pretext) > 1 and pretext[-1] not in '་། ':
            # if milestone is one character into a syllable, sift it over one
            if pretext[-2] in '་། ':
                posttext = pretext[-1] + posttext
                pretext = pretext[:-1]
            # else if milestone is before a tsek shift it back one
            elif posttext[0] == '་':
                pretext += posttext[0]
                posttext = posttext[1:]
            # else if there's only one letter after milestone move it over two
            elif posttext[1] == '་':
                pretext += posttext[0:2]
                posttext = posttext[2:]

        # if pretext[-1] not in " ་།༔༄༅" and "*" not in ms:
        #     bktind = ms.rfind(']')
        #     ms = ms[:bktind] + "*" + ms[bktind:]
        self.text = pretext + ms + posttext
        self.index = ind + len(ms) + int(line_len / 4)  # int(self.avglnlen / 2)
        self.written = False

    def is_written(self):
        return self.written

    def writedoc(self, outdir):
        print(".... Done!\nDocument {} written to {}".format(self.outname, outdir))
        with open(os.path.join(outdir, self.outname), 'w') as dout:
            dout.write(self.text)
            self.written = True


if __name__ == '__main__':
    from ocrvol import OCRVol
    vol = OCRVol('resources/kama-ocr-vol-001.txt', 167)  # Usually seem to start on pg 7, vol 1 starts at 167
    myunivol = UniVol('in/KAMA-001-b.txt', vol.avg_line_length)
    print("Done!")
