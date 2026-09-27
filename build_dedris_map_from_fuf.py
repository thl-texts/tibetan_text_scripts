"""
Builds the authoritative Dedris keystroke -> Unicode lookup table directly from the real UDP
(Unicode Data Processor, https://leighb.com/udp/) .fuf mapping files, instead of statistically
guessing it (see build_dedris_map.py, superseded for the fonts covered here).

Where the data came from: the user installed udp2302.exe into a CrossOver bottle on this Mac,
then copied the installed program directory out to resources/fonts/UnicDocP/. That directory
contains one plain-text ".fuf" file per legacy font UDP knows how to convert (Dedris-a,
Dedris-a1, ..., Dedris-vowa, Dedris-syma, etc.) -- these are UDP's real, hand-built keystroke
tables, not a guess. Spot-checked against every entry the user hand-confirmed by eye in
workspace/fixes/kama-084-ef/review/dedris-vowa-review.docx (see build_dedris_map.py's
KNOWN_ENTRIES) and they match exactly.

.fuf format: tab-separated lines "0xHH\t0xHH\t0F.. or 0F..+0F..+...", CRLF-terminated. The
first two columns are always identical (the ASCII/ANSI byte value of the keystroke, in hex,
duplicated -- unclear why UDP stores it twice, but harmless). The third column is one or more
Unicode Tibetan-block codepoints (hex, no "U+" prefix) joined with "+", giving the Unicode
string that keystroke should resolve to. A value of literal "FFFF" means "no real Unicode
equivalent" (e.g. a typist's visual-spacing space) -- skipped, same as an unresolved entry in
the statistical table.

Usage:
    python build_dedris_map_from_fuf.py --fuf-dir resources/fonts/UnicDocP -o resources/dedris-map.json
"""
import argparse
import json
from glob import glob
from os.path import basename, join, splitext

DEFAULT_OUT = join('resources', 'dedris-map.json')


def parse_fuf(path):
    """
    Yields (char, unicode_str) for each line in a .fuf file. A codepoints value of "FFFF"
    appears exactly once across every Dedris .fuf file, on the space keystroke (0x20) in
    Dedris-a -- it means "no substitution, pass the keystroke through unchanged" (a literal
    space is already valid on its own), not "delete it". Confirmed by real converted text:
    a shad (།) is conventionally followed by a literal space in these documents (e.g. "། །"
    for what looks like a doubled shad), typed as a plain space keystroke -- dropping it
    silently ate meaningful punctuation spacing.
    """
    with open(path, 'r', encoding='ascii', errors='replace') as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) != 3:
                continue
            key_hex, _key_hex2, codepoints = parts
            ch = chr(int(key_hex, 16))
            if codepoints.strip().upper() == 'FFFF':
                yield ch, ch
                continue
            unicode_str = ''.join(chr(int(cp, 16)) for cp in codepoints.split('+'))
            yield ch, unicode_str


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--fuf-dir', required=True, help='Directory containing the UDP-installed Dedris-*.fuf files')
    parser.add_argument('-o', '--out', default=DEFAULT_OUT, help='Output path for the map JSON')
    args = parser.parse_args()

    table = {}
    for path in sorted(glob(join(args.fuf_dir, 'Dedris-*.fuf'))):
        font_name = splitext(basename(path))[0]
        entries = {}
        for ch, unicode_str in parse_fuf(path):
            entries[ch] = {'unicode': unicode_str, 'confidence': 1.0, 'count': 0, 'source': 'udp-fuf'}
        # Only Dedris-a.fuf has an explicit "0x20 -> FFFF" (pass-through) row; every other
        # font's table omits the space keystroke entirely rather than repeating it. Apply the
        # same pass-through fallback to every font so a bare space keystroke -- used, e.g., for
        # the conventional space after a shad (།) -- resolves to a literal space rather than
        # being reported as an unresolved/unknown keystroke.
        entries.setdefault(' ', {'unicode': ' ', 'confidence': 1.0, 'count': 0, 'source': 'udp-fuf-space-fallback'})
        table[font_name] = entries
        print('{}: {} entries'.format(font_name, len(entries)))

    with open(args.out, 'w', encoding='utf-8') as fout:
        json.dump(table, fout, ensure_ascii=False, indent=1, sort_keys=True)
    print('\nWrote {} font(s), {} entries to {}'.format(
        len(table), sum(len(c) for c in table.values()), args.out))


if __name__ == '__main__':
    main()
