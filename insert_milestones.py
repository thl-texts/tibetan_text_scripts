"""
A script to insert milestones into Unicode volumes of Kama Gyeba converted from Sambhota by matching lines with the
OCR volumes read in by Zach. Using fuzzy search it finds the line breaks as delineated in the OCR within the converted
Sambhota files. It uses two custom classes: OCRVol and UniVol

Date: 9/5/2019
"""
from tibtexts.ocrvol import OCRVol
from tibtexts.univol import UniVol
from fuzzysearch import find_near_matches
from os import getcwd, listdir, remove, system
from os.path import join
import datetime
from math import ceil
import logging

debugon = True
unidocs = []
avg_ln_len = 0

def set_unidocs(pth):
    '''
    If files in the In folder are Word docx, then convert them to .txt files

    :param pth:
    :return: List of txt Files to which to add milestones
    '''
    global unidocs
    isok = False
    for f in listdir(inpath):
        if not f.startswith('.'):
            if f.endswith('.docx'):
                if not isok:
                    answer = input("Some of the files in the In folder are Word docs. May I convert them to text files? "
                                   "(The Word docs in the In folder will be replaced): y/n? ")
                    if answer == 'y' or answer == 'yes':
                        isok = True
                    else:
                        print("Aborting Milestone insertion!")
                        exit(0)
                filepth = join(pth, f)
                cmd = 'textutil -convert txt -output "{}" "{}"'.format(filepth.replace('.docx', '.txt'), filepth)
                system(cmd)
                remove(filepth)
    fileslist = [f for f in listdir(inpath) if f.endswith('.txt')]
    fileslist.sort()
    unidocs = [join(inpath, f) for f in fileslist]


def get_next_unidoc():
    global unidocs, avg_ln_len
    if len(unidocs) == 0:
        return None
    return UniVol(unidocs.pop(0), vol.avg_line_length)


def find_insertion_point(doc, linebeg, lines_skipped):
    '''
    Find the index for the beginning of the line in the current unicode document, where the milestone should be
    inserted
    :param doc: UniVol
        The Unicode document wrapped in the custom class UniVol
    :param linebeg: str
        The fragment from the beginning of the line from the OCR volume
    :param lines_skipped: int
        Count of lines skipped in previous iteraction for determining the chunk
    :return: int
        The index in the current chunk where the milestone should be inserted. The index of the beginning of the chunk
        is added later to get the absolute index where the mileston is to be inserted.
    '''
    ldist = 5
    chunk = doc.get_search_chunk(skipped=lines_skipped)
    tries = 0
    insind = False
    while tries < 3:
        tries += 1

        logging.debug("Try {} Looking for: {}".format(tries, linebeg))
        logging.debug("In: {} (ind: {})".format(chunk, doc.index))

        mtc = find_near_matches(linebeg, chunk, max_l_dist=ldist)  # Call fuzzy search to find the match point
        logging.debug("match: {}".format(mtc))
        if len(mtc) == 0:
            # If there's no match, call the narrow_search function to change the parameters
            linebeg, chunk, ldist = narrow_search(linebeg, chunk, ldist, doc, tries)
        else:
            # If there is a match use the start point of the first match for this
            # TODO: Check that the first match is always the one with the list l_dist or is it the first
            best_match = -1
            for n, m in enumerate(mtc):
                if n == 0:
                    best_match = 0
                elif m.dist < mtc[best_match].dist:
                    best_match = n

            insind = mtc[best_match].start
            break

    return insind


def narrow_search(srchtxt, chunk, ldist, udoc, tries):
    '''
    Attempt different ways to narrow (or generalize) the search to find the hit for the line break
    Need to achieve 95+% accuracy.
    :param srchtxt: str
        The line beginning fragment from the OCR vol we are looking for
    :param chunk:
        The chunk of the Unicode document we are searching in
    :param ldist: int
        The maximum Levenshtein distance (number of edits required to achieve a match)
    :param udoc:
        The original Unicode document. Needed to get a bigger chunk
    :param tries:
        The number of tries we are currently on
    :return: tuple
        srchtxt - the updated search text, the beginning of the line where the milestone goes from OCR doc
        chunk - the updated chunk to look in from the Unicode document
        ldist - the new maximum Levenshtein distance
    '''

    if tries == 1:
        # First double the chunk
        chunk = udoc.get_search_chunk(2)
        print("Narrowing search....", end='')   # Only print it the first time. Other times, it's already there.

    elif tries == 2:
        # Second try upping ldist from 5 to 8
        ldist = 8

    # elif tries == 3:
    #   chunk = chunk.replace(' ', '')   # remove spaces

    return srchtxt, chunk, ldist


def clean_ocr_line(txt):
    '''
    Clean the line from the OCR volume
    :param txt:
    :return:
    '''

    # Remove leading punctuation and other non-characters
    while txt[0] in ('་', '༅', '༄', '།', ' '):
        txt = txt[1:]
    # Remove double tseks and other ocr anomalies
    txt = txt.replace('།་', '།').replace('།', '། ').replace('  ', ' ').replace('་་', '་')
    # Split on tsek and trim to seven syllables (roughly) if greater than that.
    txt = txt.split('་')
    if len(txt) > 7:
        txt = '་'.join(txt[:7])
    elif len(txt) == 1:
        txt = txt[0]
    else:
        txt = '་'.join(txt)
    return txt


if __name__ == "__main__":

    # Load the OCR Volume used to determine page and line breaks into the custom OCRVol class
    volnum = input("Enter volume number: ")
    if not volnum.isnumeric():
        print("{} is not a number. Bye!".format(volnum))
        exit(0)
    volnum = str(int(volnum)).zfill(3)
    volflnm = 'kama-ocr-vol-{}'.format(volnum)
    startsat = input("Enter scan page the volume starts at: ")
    # startsat = 4    # This is the ocr page number that should be labeled as milestone 1
    if not startsat.isnumeric():
        print("{} is not a number. Bye!".format(startsat))
        exit(0)
    else:
        startsat = int(startsat)
    # OCR usually seem to start on pg 7, vol 1 starts at 167
    skippgs = list()  # Skippgs are pages in the OCR vol to be skipped without incrementing the milestone number
    # for vol 1 use range(171, 177) vols 2 & 3 skip nothing

    # Set up the logging
    currdt = datetime.datetime.now()
    currdt = currdt.strftime("%Y-%m-%d_%H-%M")
    logging.basicConfig(filename='workspace/logs/{}-{}.log'.format(volflnm, currdt), filemode='w',
                        format='(%(levelname)s) %(message)s', level=logging.DEBUG)

    vol = OCRVol('resources/ocr/{}.txt'.format(volflnm), startat=startsat, skips=skippgs)
    avg_ln_len = vol.avg_line_length
    logging.info("Vol has {} lines and is {} characters long".format(vol.line_count, vol.length))
    logging.info("Vol average line length: {}".format(avg_ln_len))

    # Load the Unicode document into which the milestones will be inserted into the custom UniVol class
    inpath = join(getcwd(), 'workspace/in')
    set_unidocs(inpath)
    unidoc = get_next_unidoc()
    logging.info("Doing file: {}".format(unidoc.filename))

    # Iterate through the lines in the OCR Volume with the custom iterater that returns just the beginning of the line
    missed_ms = []
    skipped_lines = []
    skipped = 0
    for lnbeg in vol:
        if lnbeg is None or len(lnbeg) == 0:
            continue
        if len(lnbeg) < 10:
            logging.info("Skipping too-short line {}: {}".format(vol.get_page_num(True), lnbeg))
            skipped += 1
            skipped_lines.append(vol.get_page_num(True))
            continue

        ms = vol.get_milestone()  # Get the current milestone string, e.g. [12.4] or [51][51.1]
        if debugon:
            logging.debug("\n===========================================\n")
            logging.debug("Milestone: {} (Curr pg: {})".format(ms, vol.get_current_page()))

        ind = find_insertion_point(unidoc, lnbeg, skipped)  # Call function to find the insertion point in the unidoc for ms

        if ind is False and unidoc.get_length() - unidoc.index < 200 and len(unidocs) > 0:
            unidoc = get_next_unidoc()
            logging.info("\n**********************\nDoing file: {}\n**********************\n".format(unidoc.filename))
            ind = find_insertion_point(unidoc, lnbeg, skipped)

        if ind is False:
            # If not found, do not insert milestone.
            logging.warning("!!!!!!! Milestone {} not found !!!!!!!!!!".format(ms))
            logging.warning("Current index: {}, Full Length: {}".format(unidoc.index, len(unidoc.text)))
            print("\rMilestone {} not found!                                       ".format(ms), end='')
            missed_ms.append(ms.replace('][', '/').strip('[]'))
            skipped += 1
            continue

        ind += unidoc.index

        if debugon:
            logging.debug("Line beg: {}".format(lnbeg))
            lbln = len(lnbeg)
            logging.debug("Text chunk: {}#$#$#$#{}".format(unidoc.text[ind - lbln:ind], unidoc.text[ind:ind + lbln]))
        print("\rInserting: {}                                             ".format(ms), end='')
        unidoc.insert_milestone(ms, ind, vol.get_line_length())
        skipped = 0  # Reset skipped lines

        # Test if end of unidoc. Added "+ 25" for vol. 2 but didn't have it for vol. 1
        if len(unidoc.text) - unidoc.index < vol.avg_line_length - 25:
            # If we are at the end of a chunk document ...
            print("")
            unidoc.writedoc('workspace/out')  # Write it and
            if len(unidocs) > 0:
                # If there are more documents, open the next one (popping it off the top of the list)
                unidoc = get_next_unidoc()
                logging.info("\n**********************\nDoing file: {}\n**********************\n".format(unidoc.filename))
            elif vol.get_line_num(True) < vol.line_count:
                # If no more chunk docs left, but still lines in the OCR volume, then notify
                logging.warning("Reached end of unicode Docs but volume at line {} of {}".format(vol.get_line_num(True),
                                                                                       vol.line_count))
                break

    if isinstance(unidoc, UniVol) and not unidoc.is_written():
        print("\nWriting last file")
        unidoc.writedoc('workspace/out')


    with open('workspace/logs/{}-missed-ms.log'.format(volflnm), 'w') as msout:
        msout.write("****** {} Milestones not inserted for {} ******\n".format(len(missed_ms), volflnm))
        for mms in missed_ms:
            msout.write("{}\n".format(mms))
        if len(skipped_lines) > 0:
            msout.write("\n\n****** {} Lines Skipped ******\n".format(len(skipped_lines)))
            for skl in skipped_lines:
                msout.write("{}\n".format(skl))
    print("Done!")

