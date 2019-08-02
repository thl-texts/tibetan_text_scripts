from os import listdir, path
from docx import Document
from docx.shared import Pt


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


def copy_doc_to_template(infnm, outfnm):
    '''
    Copies unstyled word document paragraphs to a "template" document which is a Word docx with the correct styles

    :param doc: docx.document.Document
    :param tmpl:
    :return: docx.document.Document
    '''
    indoc = read_in_doc(infnm)
    outdoc = get_template_doc(outfnm)
    pstyl = get_style(outdoc)
    for ind, p in enumerate(indoc.paragraphs):
        outpara = outdoc.add_paragraph(p.text, pstyl)
        do_annotations(outpara, outdoc)

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


def get_template_doc(fnm):
    '''
    Get the template document that has all the styles in it
    :param fnm:
    :return: docx.document.Document
    '''
    folder = 'resources'
    tplnm = 'tibtext-styled-tpl.docx'
    tplpath = path.join(folder, tplnm)
    doc = Document(tplpath)
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


if __name__ == "__main__":
    '''
    The main routine that runs the conversion. Is there any reason to document this?
    '''
    indir = 'in'
    outdir = 'out'
    ct = 0
    for fnm in [f for f in listdir(indir) if not f.startswith('.')]:
        print("Processing {}".format(fnm))
        inf = path.join(indir, fnm)
        outf = path.join(outdir, fnm)
        newdoc = copy_doc_to_template(inf, outf)
        ct += 1

    print("{} documents done!".format(ct))

