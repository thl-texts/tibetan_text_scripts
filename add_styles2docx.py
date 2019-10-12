from os import listdir, mkdir, path, system, getcwd, chdir, remove
import shutil
from docx import Document
from docx.shared import Pt
import argparse


def summarize_args(kws):
    print("----------- Parameters   ---------")
    print("In directory: {}".format(kws['in']))
    print("Out directory: {}".format(kws['out']))
    print("Options:")
    print("\tAdd metadata table: {}".format("yes" if kws['table'] else "no"))
    print("\tDo annotations: {}".format("yes" if kws['annotations'] else "no"))
    print("\tDo Milestones: {}".format("yes" if kws['milestones'] else "no"))


def stardardize_in_files(infld):
    '''
    Standardize the files in the in folder converting them to docx

    :param infld:
    :return:
    '''
    bakfld = path.join(infld, 'bak')
    if not path.exists(bakfld):
        mkdir(bakfld)
    cwd = getcwd()
    for f in listdir(infld):
        if f.endswith('.txt') or f.endswith('.rtf'):
            newf = f.replace('.txt', '-temp.docx').replace('.rtf', '-temp.docx')
            chdir(infld)
            system('textutil -convert docx -output "{}" "{}"'.format(newf, f))
            chdir(cwd)
            shutil.move(path.join(infld, f), path.join(bakfld, f))
        elif f.endswith('.docx') and not f.endswith('-temp.docx'):
            newf = f.replace('.docx', '-temp.docx')
            shutil.move(path.join(infld, f), path.join(infld, newf))


def clean_out_folder(outd):
    for f in listdir(outd):
        if f.endswith('-temp.docx'):
            remove(path.join(outd, f))


def read_in_text(dir, fnm):
    '''
    Reads in plain text to put in Word doc. Original idea, maybe deprecated
    :param dir: String
    :param fnm: String
    :return: List
    '''
    try:
        with open("{}/{}".format(dir, fnm), 'r') as infl:
            alltxt = infl.readlines()
    except FileNotFoundError as fnfe:
        print(fnfe)
        alltxt = False

    return alltxt


def read_in_doc(fnm):
    '''
    Read in a Word docx with file name

    :param fnm: String
    :return: docx.document.Document
    '''
    doc = Document(fnm)
    return doc


def copy_doc_to_template(infnm, outfnm, include_table=True, do_annots=False, mark_miles=True):
    """
    Copies unstyled word document paragraphs to a "template" document which is a Word docx with the correct styles

    :param infnm:
    :param outfnm:
    :param include_table:
    :param do_annots:
    :param mark_miles:
    :return: docx.document.Document
    """

    indoc = read_in_doc(infnm)
    outdoc = get_template_doc(outfnm, include_table)
    pstyl = get_style(outdoc)
    for ind, p in enumerate(indoc.paragraphs):
        outpara = outdoc.add_paragraph(p.text, pstyl)
        if do_annots:
            do_annotations(outpara, outdoc)
        if mark_miles:
            mark_milestones(outpara, outdoc)
    set_tib_font(outdoc)
    outdoc.save(outfnm)
    return outdoc


def do_annotations(p, mydoc):
    '''
    Finds text betwee « and » and applies the Annotations style

    :param p:
    :param mydoc:
    :return: Null (manipulation done by reference)
    '''
    annotstyl = get_style(mydoc, "Annotations")
    # ptxt = p.text
    # for dolpopa
    ptxt = p.text.replace("«", "").replace("»", "")  # Ignore the smaller font
    pts = ptxt.split("<")  # for dolpopa was «
    if len(pts) > 1:
        p.clear()
        p.add_run(pts[0])
        for rn in pts[1:]:
            rnpts = rn.split(">")  # for dolpopa was »
            if len(rnpts) == 1:
                print("No closing annotation marker")
                p.add_run(rn, annotstyl)
            else:
                p.add_run(rnpts[0], annotstyl)
                runtxt = rnpts[1]
                if len(rnpts) > 2:
                    print("more than two closing annotation markers!")
                    runtxt = ''.join(rnpts[1:])
                p.add_run(runtxt)


def mark_milestones(p, mydoc):
    pgstyl = get_style(mydoc, 'Page Number Print Edition')
    lnstyl = get_style(mydoc, 'Line Number Print')
    # parastyl = get_style(mydoc, 'Default Character Font')
    ptxt = p.text
    pts = ptxt.split('[')
    if len(pts) > 1:
        p.clear()
        for rn in pts:
            if ']' in rn:
                rnpts = rn.split(']')
                rn = '[' + rnpts[0] + ']'
                sty = lnstyl if '.' in rn else pgstyl
                p.add_run(rn, sty)
                if len(rnpts) > 1:
                    p.add_run(rnpts[1])
            else:
                p.add_run(rn)


def get_template_doc(fnm, with_table=True):
    '''
    Get the template document that has all the styles in it
    :param fnm:
    :param with_table:
    :return: docx.document.Document
    '''
    folder = 'resources'
    tplnm = 'tibtext-styled-tpl.docx'
    # print("Template: {}".format(tplnm))
    tplpath = path.join(folder, tplnm)
    doc = Document(tplpath)
    parastyl = get_style(doc)
    if not with_table:
        for tbl in doc.tables:
            tbl._element.getparent().remove(tbl._element)
        for p in doc.paragraphs:
            p._element.getparent().remove(p._element)

    doc.save(fnm)
    return doc


def get_style(doc, stynm="Paragraph"):
    '''
    Find a style in the doc by name, defaults to paragraph

    :param doc:
    :param stynm: The name of the style to find, defaults to paragraph
    :return: docx.styles.styles.Styles
    '''
    for st in doc.styles:
        if st.name == stynm:
            return st


def get_title_p(tmpldoc):
    '''
    Returns the paragraph with the text "TITLE HERE" from template

    :param tmpldoc: docx.Document
    :return: docx.text.paragraph.Paragraph
    '''
    for p in tmpldoc.paragraphs:
        ptxt = p.text
        ptxt = ptxt.strip()
        if ptxt == 'TITLE HERE':
            return p
    print("Title paragraph not found!")
    return False


def set_tib_font(doc):
    '''
    Set the font in the document to Jomolhari

    :param doc:
    :return: Null (manipulation by reference)
    '''
    for p in doc.paragraphs:
        for r in p.runs:
            r.font.complex_script = True
            r.font.name = "Jomolhari"
            r.font.size = Pt(16)


def convert_files(ind, outd, table, annots, milestones):
    ct = 0
    for fnm in [f for f in listdir(ind) if f.endswith('.docx')]:
        print("Processing {}".format(fnm))
        inf = path.join(ind, fnm)
        outf = path.join(outd, fnm.replace('-temp', ''))
        newdoc = copy_doc_to_template(inf, outf, table, annots, milestones)
        ct += 1

    print("{} documents done!".format(ct))


parser = argparse.ArgumentParser(description='Add convert text files to Word docs with THL Styles')
parser.add_argument('-i', '--in', required=True,
                    help='Where are the documents to convert?')
parser.add_argument('-o', '--out',
                    help='Where to save the converted documents')
parser.add_argument('-t', '--table', action='store_true',
                    help='Add metadata tables to documents')
parser.add_argument('-a', '--annotations', action='store_true',
                    help='Convert << and >> into annotation style')
parser.add_argument('-m', '--milestones', action='store_true',
                    help='Add styles to page and line milestones')
args = parser.parse_args()

if __name__ == "__main__":
    '''
    The main routine that runs the conversion. 
    '''
    kwargs = vars(args)
    if not kwargs['out']:
        kwargs['out'] = kwargs['in']
    indir = kwargs['in']
    if not path.isdir(indir):
        print("The In directory setting, {}, is not a directory".format(indir))
        exit(0)
    outdir = kwargs['out']
    if not path.isdir(outdir):
        print("The Out directory setting, {}, is not a directory".format(outdir))
        exit(0)

    summarize_args(kwargs)
    stardardize_in_files(indir)
    print("Files converted to docx!")
    convert_files(indir, outdir, kwargs['table'], kwargs['annotations'], kwargs['milestones'])
    print("Removing temp files ...")
    clean_out_folder(outdir)
    print("Done")
