import re

class OCRVol:
    """
        A class to handle OCR Tibetan volumes
        Iterator that goes through lines
    """
    LINE_FRAG_SYLLABLES = 5
    lines = []

    def __init__(self, path, startat=0, skips=[], translen=10, maxskips=10, badblanks=[]):
        self.inpath = path
        # print(path)
        vnmtc = re.search(r'vol[\-\_](\d+)', self.inpath)
        self.volnum = vnmtc.group(1) if vnmtc else "unknown"
        self.startat = startat
        self.skips = skips  # array of page numbers to skip. Skipped pages do not increment milestone counter
        # but startat becomes one lower for ever page skipped
        self.pgsskipped = set()  # Keep track of number of pages already skipped to subtract from MS counter
        self.badblanks = badblanks
        self.maxskips = maxskips * 7  # maxskips given is number of pages, multiply by 7 to get rough number of lines
        self.translen = translen
        pgnm = '0'
        lnnm = 0
        self.startn = -1
        self.length = 0
        self.line_count = 0
        self.adj = 0
        in_intro = True
        with open(self.inpath, 'r') as fin:
            for ln in fin:
                ln = ln.strip()
                if '.tif' in ln or '.jpg' in ln:
                    in_intro = False
                    mtch = re.search(r'kama[\-_]vol[\-_]\d+/out_+(\d+)', ln)
                    if mtch:
                        pgnm = mtch.group(1)
                        if int(pgnm) == int(self.startat):
                            self.startn = self.line_count - 1
                        lnnm = 0
                        continue
                elif ln.strip('༌་༴།༏༐༑༄༅') == '' or in_intro:
                    continue
                lnnm += 1
                self.length += len(ln)
                self.line_count += 1

                self.lines.append((int(pgnm), lnnm, ln))

        self.avg_line_length = int(self.length / self.line_count)
        self.max = len(self.lines) - 1
        self.isfirst = True

    def __iter__(self):
        self.n = self.startn
        return self

    def __next__(self):
        if self.n < self.max:
            self.n += 1
            skct = 0
            pgnum = self.get_current_page(as_int=True)
            while pgnum in self.skips:
                self.pgsskipped.add(pgnum)  # add to set, only unique values get added
                skct += 1
                if skct > self.maxskips:
                    print("\nWARNING!!!!!! Maximum pages skipped {} at page {}. \n".format(self.maxskips, self.n))
                    break
                self.n += 1
                pgnum = self.get_current_page(as_int=True)

            ln = self.get_line()
            ln = ln.strip('༄༅།་ ')
            # Clean up OCR line
            ln = ln.replace('་་', '་').replace('།་', '།').replace(' ་', ' ')  # remove extra tseks
            ln = ln.replace('༷', '').replace('༵', '')  # Removing the nges bzung (emphasis) marks
            lnpts = ln.split('་')
            ln = '་'.join(lnpts[0:self.LINE_FRAG_SYLLABLES])
            ln = ln.strip('༄༅།་ ')
            return ln

        else:
            raise StopIteration

    def get_line(self, lnnm=False):
        if not lnnm:
            lnnm = self.n
        return self.lines[lnnm][2] if len(self.lines[lnnm]) == 3 else None

    def get_line_length(self, lnnm=False):
        if lnnm == 'prev':
            lnnm = self.n - 1
        elif lnnm == 'next':
            lnnm = self.n + 1
        elif not lnnm:
            lnnm = self.n
        return len(self.lines[lnnm][2]) if len(self.lines[lnnm]) == 3 else -1

    def print_stats(self):
        import pandas as pd
        lns_per_pg = {}
        for item in self.lines:
            pgnm = item[0]
            if pgnm in lns_per_pg:
                lns_per_pg[pgnm] += 1
            else:
                lns_per_pg[pgnm] = 1
        totalpgs = len(lns_per_pg.keys())
        totallns = sum(lns_per_pg.values())
        summarylns = {}
        for val in lns_per_pg.values():
            val = str(val)
            if val in summarylns:
                summarylns[val] += 1
            else:
                summarylns[val] = 1

        print("Statistics for Volume {}".format(self.volnum))
        print("Total pages: {}".format(totalpgs))
        print("Total lines: {}".format(totallns))
        print("Average number of lines per page: {}".format("%.2f" % (totallns / totalpgs)))
        print("Lines per page spread:")
        sumkeys = list(summarylns.keys())
        sumkeys.sort()
        print("Lines per page: \t", end='')
        print("\t".join(sumkeys))
        print("Number of pages: \t", end='')
        for ky in sumkeys:
            print("{}\t".format(summarylns[ky]), end='')

        print("")

    def get_transition(self):
        """
        Returns the transition text from the previous page to the current one, including the given number of syllables
        :param numofsyls: int
        :return:
        """
        currln = self.get_line(self.n).split('་')
        trans = '་'.join(currln[:self.translen])
        if self.n > 0:
            prevln = self.get_line(self.n - 1).split('་')
            templst = prevln[(-1 * self.translen):]
            templst.append(trans)
            trans = '་'.join(templst)

        return trans

    def get_milestone(self):
        pg, lnnm, lnstr = self.lines[self.n]
        # Adjust page number for milestone based on start page
        # if it starts at 7, it means milestone page 1 is in the OCR labeled as:
        #           "tbocrtifs/kama-vol-002/out__0007.tif"
        pg = pg - self.startat - len(self.pgsskipped) + 1 + self.adj
        pgstr = str(pg)
        mspref = ""  # Prefix for the blank page milestone. Usually empty.
        if pgstr in self.badblanks:
            mspref = "[{}]".format(pg)
            pg = pg + 1
            self.adj += 1
            self.badblanks.remove(pgstr)
        # flgstr = "*" if flag else ""
        ms = "[{}.{}]".format(pg, lnnm)
        if lnnm == 1:
            ms = mspref + "[{}]".format(pg) + ms
        return ms

    def get_page_num(self, with_line=False, as_int=False):
        pg, lnnm, lnstr = self.lines[self.n]
        pg = int(pg) if as_int else pg
        if with_line:
            return "{}.{}".format(pg, lnnm)
        else:
            return pg

    def get_line_num(self, sequential=False):
        pg, lnnm, lnstr = self.lines[self.n]
        if sequential:
            return self.n + 1
        else:
            return lnnm

    def get_current_page(self, as_int=False):
        pg, lnnm, ln = self.lines[self.n]
        pg = int(pg) if as_int else pg
        return pg

    def next_is_page(self):
        '''
        Determine if next line is beginning of a page
        :return: boolean
        '''
        nextpg, nextln, nexttext = self.lines[self.n + 1]
        if nextln == 1:
            return True
        else:
            return False

    def nextpage(self):
        currpg = self.get_page_num()
        msg = "Skipping rest of page {}".format(currpg)
        nextpg, nextln, nexttext = self.lines[self.n + 1]
        ct = 0
        while nextpg == currpg:
            ct += 1
            self.n += 1
            nextpg, nextln, nexttext = self.lines[self.n + 1]
            if ct > 6:
                msg += "\nTried to skip more than 3 lines. Stopping!"
        if ct < 7:
            msg += "\nFound next page {}".format(nextpg)
        return msg
