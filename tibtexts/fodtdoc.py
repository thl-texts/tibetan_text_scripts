"""
Extracts a per-character (font_name, char) stream from a legacy Word .doc file, by shelling
out to LibreOffice's headless flat-ODT ("fodt") export and parsing the result.

Why fodt and not textutil/.rtf: on a Mac without the original Sambhota-family fonts (e.g.
Dedris-a, Dedris-vowa) installed, textutil/Word's own .doc reader silently substitutes a
generic font (Times/Times New Roman) for every run, destroying the font-switch information
this whole conversion approach depends on. LibreOffice's ODF export preserves the real
font-table names from the legacy .doc regardless of what's installed locally.
"""
import os
import subprocess
import uuid
from os.path import join, basename, splitext
from lxml import etree

SOFFICE_PATHS = (
    '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
    'soffice',  # assume on PATH (Linux/other)
)

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
}


def _q(prefix, local):
    return '{{{}}}{}'.format(NS[prefix], local)


def find_soffice():
    for path in SOFFICE_PATHS:
        if path.startswith('/'):
            if os.path.exists(path):
                return path
        else:
            from shutil import which
            found = which(path)
            if found:
                return found
    raise FileNotFoundError(
        "Could not find the LibreOffice 'soffice' binary. Install LibreOffice, or add its "
        "location to tibtexts.fodtdoc.SOFFICE_PATHS."
    )


class FodtDoc:
    """
    Per-paragraph, per-character (font_name, char) sequence extracted from a .doc/.fodt file.

    self.paragraphs is a list of paragraphs; each paragraph is a list of (font_name, char)
    tuples in reading order. font_name is None for text with no resolvable font (rare; the
    doc's own default is used when nothing better is found).
    """

    def __init__(self, fodt_path):
        self.fodt_path = fodt_path
        tree = etree.parse(fodt_path)
        root = tree.getroot()
        self._style_font, self._style_parent = self._build_style_maps(root)
        self.paragraphs = self._extract_paragraphs(root)

    @classmethod
    def from_doc(cls, doc_path, workdir):
        """
        Convert doc_path (a legacy .doc file) to flat ODT via headless LibreOffice, using a
        scratch profile under workdir so concurrent/leftover soffice instances can't hang this
        conversion waiting on a shared user-profile lock. Returns a FodtDoc wrapping the result.
        """
        soffice = find_soffice()
        scratch = join(workdir, 'lo-profile-{}'.format(uuid.uuid4().hex))
        outdir = join(workdir, 'fodt-out-{}'.format(uuid.uuid4().hex))
        os.makedirs(outdir, exist_ok=True)
        cmd = [
            soffice, '--headless',
            '-env:UserInstallation=file://{}'.format(scratch),
            '--convert-to', 'fodt',
            '--outdir', outdir,
            doc_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        stem = splitext(basename(doc_path))[0]
        fodt_path = join(outdir, stem + '.fodt')
        if not os.path.exists(fodt_path):
            raise RuntimeError(
                "LibreOffice did not produce {} from {}.\nstdout: {}\nstderr: {}".format(
                    fodt_path, doc_path, result.stdout, result.stderr)
            )
        return cls(fodt_path)

    @staticmethod
    def _build_style_maps(root):
        """
        Map style-name -> font-name (resolving style:font-name directly, or falling back to
        fo:font-family when a style only records the font that way), and style-name ->
        parent-style-name, so resolve_font() can walk the inheritance chain.
        """
        style_font = {}
        style_parent = {}
        for st in root.iter(_q('style', 'style')):
            name = st.get(_q('style', 'name'))
            if name is None:
                continue
            parent = st.get(_q('style', 'parent-style-name'))
            if parent:
                style_parent[name] = parent
            tp = st.find(_q('style', 'text-properties'))
            if tp is not None:
                font_name = tp.get(_q('style', 'font-name'))
                font_family = tp.get(_q('fo', 'font-family'))
                if font_name:
                    style_font[name] = font_name
                elif font_family:
                    style_font[name] = font_family.strip("'")
        return style_font, style_parent

    def resolve_font(self, style_name, _seen=None):
        if style_name is None:
            return None
        seen = _seen or set()
        if style_name in seen:
            return None
        seen.add(style_name)
        if style_name in self._style_font:
            return self._style_font[style_name]
        if style_name in self._style_parent:
            return self.resolve_font(self._style_parent[style_name], seen)
        return None

    def _extract_paragraphs(self, root):
        body = root.find('.//' + _q('office', 'text'))
        paragraphs = []
        if body is None:
            return paragraphs
        for p in body.iter(_q('text', 'p')):
            default_font = self.resolve_font(p.get(_q('text', 'style-name')))
            paragraphs.append(self._extract_run(p, default_font))
        return paragraphs

    def _extract_run(self, elem, default_font):
        """
        Walk elem's children in document order, emitting (font_name, char) for every character:
        text nodes directly under elem use default_font; text:span children resolve their own
        style (falling back to default_font); text:line-break/text:tab/text:s become a single
        space character in the current font.
        """
        chars = []
        span_tag = _q('text', 'span')
        linebreak_tag = _q('text', 'line-break')
        tab_tag = _q('text', 'tab')
        space_tag = _q('text', 's')

        def emit_text(txt, font):
            if txt:
                for ch in txt:
                    chars.append((font, ch))

        emit_text(elem.text, default_font)
        for child in elem:
            if child.tag == span_tag:
                span_font = self.resolve_font(child.get(_q('text', 'style-name'))) or default_font
                emit_text(child.text, span_font)
                for grandchild in child:
                    # Nested spans/breaks inside a span are rare but handled the same way.
                    if grandchild.tag == span_tag:
                        gf = self.resolve_font(grandchild.get(_q('text', 'style-name'))) or span_font
                        emit_text(grandchild.text, gf)
                    elif grandchild.tag in (linebreak_tag, tab_tag, space_tag):
                        chars.append((span_font, ' '))
                    emit_text(grandchild.tail, span_font)
            elif child.tag in (linebreak_tag, tab_tag, space_tag):
                chars.append((default_font, ' '))
            emit_text(child.tail, default_font)
        return chars

    def font_counts(self):
        """Total character count per font name across the whole document (diagnostic)."""
        counts = {}
        for para in self.paragraphs:
            for font, _ch in para:
                counts[font] = counts.get(font, 0) + 1
        return counts
