"""
Shift the page-header image numbers in a plain-text OCR volume by a fixed delta
over a range of pages. The OCR-header analog of ``adjust_pg_nums.py`` (which does
the same thing to ``[p.l]`` milestones inside a styled Word doc).

OCR volumes are plain text where each scanned page begins with a header line like

    tbocrtifs/kama_vol_067/out_0601.tif

followed by that page's lines. When a scan is spliced in or removed upstream, every
header from that point on ends up off by a constant amount. This script adds ``--delta``
(which may be negative) to the image number of every ``out_NNNN.tif`` header whose
current number falls in the ``[--start, --end]`` range, rewriting the file in place.

It keys the range on the headers' *existing* numbers (not their position), so ``-s 601``
means "start at the header currently numbered ``out_0601.tif``". Omit ``--start`` to begin
at the first page and ``--end`` to run through the last. Unlike ``renumber_ocr_pages.py``
-- which discards the old numbers and stamps a fresh contiguous sequence -- this preserves
the existing numbers and only slides the selected window, so any intentional gaps outside
the range are left untouched.

The volume file name is built from the volume number (``kama-vol-NNN.txt``) and looked up
in the OCR directory. The original is backed up (``-bak`` before the extension) before any
change, in case something goes wrong.

Usage:
    python adjust_ocr_pgnums.py -v 67 -d 1 -s 601        # +1 to out_0601.tif .. end
    python adjust_ocr_pgnums.py -v 67 -d -2 -s 601 -e 650
    python adjust_ocr_pgnums.py -v 67 -d 1               # +1 to every header
    python adjust_ocr_pgnums.py -v 67 -d 1 -s 601 -n     # dry run, just report
"""
import argparse
import datetime
import os
import re
import shutil
import sys

# Where the plain-text OCR volumes live (matches insert_milestones.py's ocrfolder).
DEFAULT_OCR_DIR = '/Users/ndg8f/Sandbox/THL/Catalogs/Kama/ocr-plain'
# Capture the prefix (through out_), the digits, and the suffix of a tif header.
TIF_RE = re.compile(r'^(.*out_)(\d+)(\.tif)\s*$')
# A header line whose number part isn't all digits (e.g. out_XXXX.tif) -- a hand
# placeholder for a page still awaiting its real number. Ignored by the shift (no
# --end needed to protect it) but reported so it isn't forgotten.
PLACEHOLDER_RE = re.compile(r'^.*out_\S*\.tif\s*$')


def backup_path(filepath):
    """Return a ``-bak`` path for filepath, timestamped if a backup already exists
    so a rerun never clobbers an earlier good backup."""
    root, ext = os.path.splitext(filepath)
    bak = root + '-bak' + ext
    if os.path.exists(bak):
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        bak = "{}-bak-{}{}".format(root, stamp, ext)
    return bak


def main():
    parser = argparse.ArgumentParser(
        description='Shift OCR page-header image numbers by a delta over a range.')
    parser.add_argument('-v', '--vol', required=True,
                        help='Volume number; the file kama-vol-NNN.txt is built from it')
    parser.add_argument('-d', '--delta', required=True, type=int,
                        help='Amount to add to each header number in range (may be negative)')
    parser.add_argument('-s', '--start', type=int,
                        help='First header image number to shift (default: the first page)')
    parser.add_argument('-e', '--end', type=int,
                        help='Last header image number to shift (default: the last page)')
    parser.add_argument('-p', '--path', default=DEFAULT_OCR_DIR,
                        help='Directory holding the OCR volume files')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Report what would change without writing anything')
    args = parser.parse_args()

    if not str(args.vol).isnumeric():
        sys.exit("Volume '{}' is not numeric.".format(args.vol))
    if args.delta == 0:
        sys.exit("Delta is 0; nothing to do.")

    filename = 'kama-vol-{}.txt'.format(str(int(args.vol)).zfill(3))
    filepath = os.path.join(args.path, filename)
    if not os.path.isfile(filepath):
        sys.exit("OCR file not found: {}".format(filepath))

    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()

    # Use the first tif header as the template for prefix / suffix / pad width.
    template = next((TIF_RE.match(ln) for ln in lines if TIF_RE.match(ln)), None)
    if template is None:
        sys.exit("No 'out_NNNN.tif' header found in {}".format(filepath))
    prefix, suffix = template.group(1), template.group(3)
    width = len(template.group(2))

    def make_header(n):
        return "{}{:0{w}d}{}\n".format(prefix, n, suffix, w=width)

    lo = args.start if args.start is not None else float('-inf')
    hi = args.end if args.end is not None else float('inf')
    if args.start is not None and args.end is not None and args.start > args.end:
        sys.exit("--start {} is greater than --end {}.".format(args.start, args.end))

    changes = []
    new_nums = []          # every header's resulting number, for the collision check
    placeholders = []      # non-numeric out_*.tif headers, left untouched
    in_range = 0
    for i, line in enumerate(lines):
        m = TIF_RE.match(line)
        if not m:
            if PLACEHOLDER_RE.match(line):
                placeholders.append((i + 1, line.strip()))
            continue
        num = int(m.group(2))
        if lo <= num <= hi:
            in_range += 1
            newnum = num + args.delta
            if newnum < 0:
                sys.exit("Delta {} would make header out_{:0{w}d}.tif negative ({}).".format(
                    args.delta, num, newnum, w=width))
            new_line = make_header(newnum)
            if new_line != line:
                changes.append((i + 1, line.strip(), new_line.strip()))
            lines[i] = new_line
            new_nums.append(newnum)
        else:
            new_nums.append(num)

    print("File: {}".format(filepath))
    print("{} {} to headers {}..{}: {} header(s) in range, {} changed.".format(
        "Adding" if args.delta > 0 else "Subtracting", abs(args.delta),
        args.start if args.start is not None else "first",
        args.end if args.end is not None else "last",
        in_range, len(changes)))
    for ln, old, new in changes[:8]:
        print("  line {}: {!r} -> {!r}".format(ln, old, new))
    if len(changes) > 8:
        print("  ... and {} more".format(len(changes) - 8))

    # Placeholders (out_XXXX.tif) are skipped automatically -- remind so the
    # still-unnumbered page doesn't get forgotten.
    for ln, text in placeholders:
        print("  (ignored placeholder on line {}: {!r} -- rename it by hand)".format(ln, text))

    # Warn (don't block) if the shift leaves duplicate header numbers -- a sign the
    # range boundary overlaps the untouched pages and needs a second look.
    dupes = sorted({n for n in new_nums if new_nums.count(n) > 1})
    if dupes:
        print("WARNING: resulting headers contain duplicate number(s): {}".format(
            ", ".join(str(d) for d in dupes)))

    if not changes:
        print("Nothing to change.")
        return
    if args.dry_run:
        print("Dry run -- no file written.")
        return

    bak = backup_path(filepath)
    shutil.copy(filepath, bak)
    print("Backup at: {}".format(bak))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Wrote: {}".format(filepath))


if __name__ == "__main__":
    main()
