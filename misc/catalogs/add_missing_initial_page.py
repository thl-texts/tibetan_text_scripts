"""
Script to go through a collection of texts and add the initial page milestone if the text starts on a line in the
middle of the page and there is not page milestone.
"""

from os import listdir
import os.path as osp
from lxml import etree
# from StringIO import StringIO
import re
import argparse


cathome = '/usr/local/projects/thlib-texts/thlib-texts-xml/catalogs/xml/'
log = None   # The Log writer for logging
out = None   # The outfile write for writing out data

# Set and initialize the arguments for the script
parser = argparse.ArgumentParser(description='Fix texts in a collection/edition that begin mid page')
parser.add_argument('-p', '--path', required=True,
                    help='Location of text folder')
parser.add_argument('-l', '--log', default='add_missing_initpg.log',
                    help='Name/location of log file to output for debugging etc')
parser.add_argument('-o', '--out',
                    help='Name/location of outfile listing texts that don’t start with a page MS')
args = parser.parse_args()


def process_text(fld, txtnum):
    """
    Function to process a text folder called from __main__

    :param fld:
    :param txtnum:
    :return:
    """
    # Use the log and out writers
    global log, out
    # Get all XML files in the folder
    txtdocs = [td for td in listdir(fld) if not td.startswith('.') and td.endswith('.xml')]
    txtdocs.sort() # Sort them
    if len(txtdocs) > 1:  # with peltsek don't have to worry about multi file texts
        # TODO: deal with multifile texts if ever necessary
        if out:
            out.write("{}, multiple files\n".format(fld))
        if log:
            log.write("{} has {} files. Skipping\n".format(fld, len(txtdocs)))
    else:
        # Single file texts
        txtdoc = txtdocs[0]
        docurl = osp.join(fld, txtdoc)  # The full URL to the document
        # Get the doctype declaration (dt) to preserve when writing out
        dt = ''
        with open(docurl, 'r') as docin:
            docstr = docin.read()
            mtchs = re.findall(r'<!DOCTYPE\s+[^\]]+\s+\]>', docstr)
            if len(mtchs) > 0:
                dt = mtchs[0]

        # Parse xml without resolving entities
        noent_parser = etree.XMLParser(resolve_entities=False)
        xmldoc = etree.parse(docurl, noent_parser)
        xmlroot = xmldoc.getroot()
        # Find the first milestone in the document and determine if it is a page or note
        #         Note: assuming body/div1 structure
        pel = xmlroot.xpath('//body/div1[1]/p[1]/milestone[1]')
        if len(pel) > 0:
            # If a first milestone is found, check its unit
            pel = pel[0]
            unit = pel.get('unit')
            if unit != 'page':
                # If it is not a page, then fix
                if out:
                    out.write("{}, {}\n".format(txtdoc, pel.get('n')))
                natt = pel.get('n')  # Get n attribute for line should be "123.4" etc.
                if natt:
                    lnnumpts = str(natt).split('.') # isolate the page number
                    pgnum = lnnumpts[0]
                    # Create page milestone
                    ms = etree.Element('milestone')
                    ms.set('unit', 'page')
                    ms.set('n', pgnum)
                    # Add it to xml doc etree and note in log
                    pel.addprevious(ms)
                    log.write("{}, Added page {} milestone\n".format(txtdoc, pgnum))
                    # Write over the old xml file with the new xml file adding the DTD decl back in
                    outdocurl = docurl  # or for testing docurl.replace(".xml", "-test.xml")
                    with open(outdocurl, 'wb') as xout:
                        print("\rWriting {}   ".format(outdocurl), end='')
                        xout.write(etree.tostring(xmlroot,
                                                  xml_declaration=True,
                                                  doctype=dt,
                                                  encoding="utf-8",
                                                  pretty_print=True))
                else:
                    log.write("{}, No n attribute on first milestone\n".format(txtdoc))
        else:
            if out:
                out.write("{}, No milestone found\n".format(txtdoc))


if __name__ == "__main__":
    kwargs = vars(args)
    loc = osp.join(cathome, kwargs['path'])
    logfile = kwargs['log']
    log = open(logfile, 'w')
    if kwargs['out']:
        outfile = kwargs['out']
        out = open(outfile, 'w')
    textfolders = listdir(loc)
    textfolders.sort()

    for txt in textfolders:
        if not txt.startswith('.'):
            txtfld = osp.join(loc, txt)
            if osp.isdir(txtfld):
                print("\rDoing folder {}        ".format(txtfld), end='')
                process_text(txtfld, txt)

