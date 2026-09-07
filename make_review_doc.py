"""
Generates a Word table document for the user to review/correct Dedris keystroke mappings by
hand, filling in a blank column -- used instead of chat-based questions because the terminal's
multiple-choice question UI garbles Tibetan text (see SESSION_LOG.md, 2026-09-07).

Usage:
    python make_review_doc.py --map /path/to/dedris-map.json --font Dedris-vowa \
        -o workspace/review/dedris-vowa-review.docx

Columns: Font, Key, Times seen, Current guess (Unicode + codepoints), Confirmed?,
Correct Tibetan (blank for the user to fill in). Already manually-confirmed entries (those
present in build_dedris_map.py's KNOWN_ENTRIES) are marked so the user can skip them.
"""
import argparse
import json
from os import makedirs
from os.path import dirname, abspath, join

import docx

from build_dedris_map import KNOWN_ENTRIES


def codepoints_of(s):
    return ' '.join('U+{:04X}'.format(ord(ch)) for ch in s)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--map', required=True, help='Path to a trained dedris-map.json')
    parser.add_argument('--font', required=True, help='Font name to generate a review table for (e.g. Dedris-vowa)')
    parser.add_argument('-o', '--out', required=True, help='Output .docx path')
    parser.add_argument('--limit', type=int, default=None, help='Only include the top N entries by frequency')
    args = parser.parse_args()

    table = json.load(open(args.map, encoding='utf-8'))
    entries = table.get(args.font, {})
    rows = sorted(entries.items(), key=lambda kv: -kv[1].get('count', 0))
    if args.limit:
        rows = rows[:args.limit]

    d = docx.Document()
    d.add_heading('Dedris keystroke review: {}'.format(args.font), level=1)
    d.add_paragraph(
        'For each row, type the correct Tibetan Unicode text into the "Correct Tibetan" '
        'column. Leave it blank if the current guess is already right; write "?" if you are '
        'not sure. Rows marked CONFIRMED already have a manually-verified answer -- only '
        'change those if you spot an error.'
    )
    table_doc = d.add_table(rows=1, cols=6)
    table_doc.style = 'Table Grid'
    hdr = table_doc.rows[0].cells
    hdr[0].text = 'Key'
    hdr[1].text = 'Times seen'
    hdr[2].text = 'Current guess'
    hdr[3].text = 'Guess codepoints'
    hdr[4].text = 'Status'
    hdr[5].text = 'Correct Tibetan'

    for ch, entry in rows:
        confirmed = (args.font, ch) in KNOWN_ENTRIES
        row = table_doc.add_row().cells
        row[0].text = repr(ch)
        row[1].text = str(entry.get('count', ''))
        row[2].text = entry.get('unicode', '')
        row[3].text = codepoints_of(entry.get('unicode', ''))
        row[4].text = 'CONFIRMED' if confirmed else '(confidence {:.2f})'.format(entry.get('confidence', 0))
        row[5].text = ''

    makedirs(dirname(abspath(args.out)), exist_ok=True)
    d.save(args.out)
    print('Wrote {} rows to {}'.format(len(rows), args.out))


if __name__ == '__main__':
    main()
