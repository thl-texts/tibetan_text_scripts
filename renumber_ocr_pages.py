"""
Renumber the page headers in a plain-text OCR volume sequentially.

OCR volumes are plain text where each scanned page begins with a header line like

    tbocrtifs/kama_vol_067/out_0071.tif

followed by that page's lines. When scans go missing, get repeated, or land out
of order, the page numbers in these headers stop matching the actual sequence,
which throws off milestone insertion (insert_milestones keys milestone numbers
off the OCR page numbers).

The usual fix: hand-edit the affected stretch -- splice in any missing pages'
text marking each with a placeholder header ("first page", "second page", ...),
delete a repeated page -- then run this script to renumber every header from a
known-good starting point straight through to the end. It treats both real
``...out_NNNN.tif`` headers and the placeholder marker lines as headers and
rewrites them all to a clean, contiguous ``out_NNNN.tif`` sequence.

The header prefix, suffix, and zero-pad width are copied from the first real tif
header in the file, so this is not hard-coded to any one volume. Reads the input
read-only and writes a new file (``-fixed`` appended to the name by default).

Usage:
    python renumber_ocr_pages.py kama-vol-067.txt
    python renumber_ocr_pages.py kama-vol-067.txt -s 71
    python renumber_ocr_pages.py vol.txt -m "first page" -m "second page" -m "extra"
    python renumber_ocr_pages.py vol.txt -n          # dry run, just report
"""
import argparse
import os
import re
import sys

DEFAULT_MARKERS = ["first page", "second page"]
# Capture the prefix (through out_), the digits, and the suffix of a tif header.
TIF_RE = re.compile(r'^(.*out_)(\d+)(\.tif)\s*$')


def main():
    parser = argparse.ArgumentParser(
        description="Renumber OCR page headers sequentially from a starting page.")
    parser.add_argument('infile', help='Plain-text OCR volume to renumber')
    parser.add_argument('-o', '--output',
                        help='Output path (default: input name with -fixed before the extension)')
    parser.add_argument('-s', '--start', type=int,
                        help='Page number for the first header (default: keep the first header as is)')
    parser.add_argument('-m', '--marker', action='append', dest='markers',
                        help='A placeholder header line to treat as a page break and renumber. '
                             'Repeatable. Default: "first page" and "second page".')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Report what would change without writing the output file')
    args = parser.parse_args()

    markers = set(args.markers if args.markers else DEFAULT_MARKERS)

    with open(args.infile, encoding='utf-8') as f:
        lines = f.readlines()

    def header_kind(line):
        if TIF_RE.match(line):
            return 'tif'
        if line.strip() in markers:
            return 'marker'
        return None

    # Use the first real tif header as the template for prefix / suffix / pad width.
    template = None
    for line in lines:
        m = TIF_RE.match(line)
        if m:
            template = m
            break
    if template is None:
        sys.exit("No 'out_NNNN.tif' header found in {}".format(args.infile))
    prefix, first_num, suffix = template.group(1), template.group(2), template.group(3)
    width = len(first_num)

    def make_header(n):
        return "{}{:0{w}d}{}\n".format(prefix, n, suffix, w=width)

    start = args.start if args.start is not None else int(first_num)
    counter = start
    headers = 0
    changes = []
    for i, line in enumerate(lines):
        if header_kind(line) is None:
            continue
        new_line = make_header(counter)
        if new_line != line:
            changes.append((i + 1, line.strip(), new_line.strip()))
        lines[i] = new_line
        headers += 1
        counter += 1

    last = counter - 1
    print("Headers found: {}".format(headers))
    print("Renumbered {} -> {} (contiguous), {} line(s) changed".format(start, last, len(changes)))
    for ln, old, new in changes[:8]:
        print("  line {}: {!r} -> {!r}".format(ln, old, new))
    if len(changes) > 8:
        print("  ... and {} more".format(len(changes) - 8))

    if args.dry_run:
        print("Dry run -- no file written.")
        return

    out = args.output
    if not out:
        root, ext = os.path.splitext(args.infile)
        out = root + "-fixed" + ext
    with open(out, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Wrote: {}".format(out))


if __name__ == "__main__":
    main()
