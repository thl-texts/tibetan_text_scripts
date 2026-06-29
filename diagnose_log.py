"""
Diagnose a milestone-insertion run that went over the missed-milestone threshold.

For every milestone it tries to place, insert_milestones.py writes a block to the
timestamped run log (workspace/logs/kama-vol-NNN-<datetime>.log):

    (DEBUG) Milestone: [69.1] (Curr pg: 72, Curr Doc: KAMA-067-a.txt)
    (DEBUG) Try 1 Looking for: <ocr line beginning>
    ...
    (DEBUG) Text chunk: <before>#$#$#$#<after>          <- a HIT (insertion point)

or, when it cannot place the milestone:

    (WARNING) !!! Milestone [69.1] not found (72.1) for: <ocr line beginning> !!!
    (WARNING) Doc text area: <30 chars of the unicode doc at the stuck index>

When fuzzy matching drifts off the rails, insert_milestones keeps failing for the
rest of the document without advancing its read position, so a single bad anchor
can cost thousands of milestones downstream. This module finds the *onset* of that
consistent failure -- the first miss that begins a sustained run of misses -- and
reports the scan page, the milestone page number, the surrounding text, and the
Word doc involved, so you know where in the OCR / Unicode docs to look.

This module only READS the log; it never modifies it.

Usage:
    python diagnose_log.py -v 67                  # find newest log for the volume
    python diagnose_log.py path/to/run.log        # diagnose a specific log file
"""
import argparse
import glob
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOGDIR = os.path.join(SCRIPT_DIR, 'workspace', 'logs')

# The per-milestone header (only emitted when insert_milestones runs with debug on).
HEADER_RE = re.compile(r'Milestone:\s*(\S+)\s*\(Curr pg:\s*(.+?),\s*Curr Doc:\s*(.+?)\)')
# A miss -- always emitted, debug or not. Group 2 is the OCR scan page.line.
NOTFOUND_RE = re.compile(r'!!! Milestone\s*(\S+)\s*not found\s*\(([^)]*)\)\s*for:\s*(.*?)\s*!!!')
DOCAREA_RE = re.compile(r'Doc text area:\s*(.*)$')
LOOKING_RE = re.compile(r'Looking for:\s*(.*)$')
TEXTCHUNK_RE = re.compile(r'Text chunk:\s*(.*)$')


def find_main_log(logdir, volfile):
    """Return the path to the newest run log for volfile, or None.

    Excludes the -missed-ms.log summary and its -tmp companion so only the real
    timestamped run logs are considered.
    """
    candidates = [
        p for p in glob.glob(os.path.join(logdir, volfile + '-*.log'))
        if not p.endswith('-missed-ms.log') and not p.endswith('-missed-ms-tmp.log')
    ]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def parse_records(logpath):
    """Parse the run log into an ordered list of per-milestone records.

    Each record is a dict with keys: ms, scan_pg, doc, miss (bool), looking_for,
    text_chunk (hits), doc_area and miss_page (misses). Records are in the order
    insert_milestones attempted them.
    """
    records = []
    cur = None
    with open(logpath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            header = HEADER_RE.search(line)
            if header:
                if cur is not None:
                    records.append(cur)
                cur = {
                    'ms': header.group(1),
                    'scan_pg': header.group(2).strip(),
                    'doc': header.group(3).strip(),
                    'miss': False,
                    'looking_for': None,
                    'text_chunk': None,
                    'doc_area': None,
                    'miss_page': None,
                }
                continue

            notfound = NOTFOUND_RE.search(line)
            if notfound:
                # A miss can appear without a header if the run had debug off; start
                # a bare record so we still capture it.
                if cur is None:
                    cur = {'ms': notfound.group(1), 'scan_pg': None, 'doc': None,
                           'looking_for': None, 'text_chunk': None}
                cur['miss'] = True
                cur['miss_page'] = notfound.group(2).strip()
                cur['looking_for'] = cur.get('looking_for') or notfound.group(3).strip()
                continue

            if cur is None:
                continue

            looking = LOOKING_RE.search(line)
            if looking:
                cur['looking_for'] = looking.group(1).strip()
                continue
            docarea = DOCAREA_RE.search(line)
            if docarea:
                cur['doc_area'] = docarea.group(1).strip()
                continue
            chunk = TEXTCHUNK_RE.search(line)
            if chunk:
                cur['text_chunk'] = chunk.group(1).strip()
                continue

    if cur is not None:
        records.append(cur)
    return records


def find_failure_regions(records, max_gap=3):
    """Group misses into sustained failure regions, tolerating small recoveries.

    A region is a stretch of misses where no more than ``max_gap`` consecutive
    successful placements occur before the next miss. A single off-by-one anchor
    typically produces one large region that runs to the end of a document, while
    a brief wobble that the matcher recovers from stays a small, separate region.

    Returns a list of (start_idx, end_idx, miss_count), in document order.
    """
    regions = []
    start = None
    last_miss = None
    gap = 0
    for i, rec in enumerate(records):
        if rec['miss']:
            if start is None:
                start = i
            last_miss = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap > max_gap:
                regions.append((start, last_miss))
                start = None
                last_miss = None
                gap = 0
    if start is not None:
        regions.append((start, last_miss))
    return [(s, e, sum(1 for r in records[s:e + 1] if r['miss'])) for s, e in regions]


def last_hit_before(records, idx):
    """Return the last successfully-placed record before idx, or None."""
    for i in range(idx - 1, -1, -1):
        if not records[i]['miss']:
            return records[i]
    return None


def format_report(records, logpath):
    """Build a human-readable diagnosis string from parsed records."""
    total = len(records)
    total_misses = sum(1 for r in records if r['miss'])
    lines = []
    lines.append("Milestone-miss diagnosis")
    lines.append("  Log: {}".format(logpath))
    lines.append("  Milestones attempted: {}   Misses: {}".format(total, total_misses))

    if total == 0:
        lines.append("  No milestone records found in this log "
                     "(was insert_milestones run with debug on?).")
        return "\n".join(lines)
    if total_misses == 0:
        lines.append("  No misses recorded -- nothing to diagnose.")
        return "\n".join(lines)

    regions = find_failure_regions(records)
    if not regions:
        lines.append("  Could not locate a miss onset.")
        return "\n".join(lines)

    # The first symptom is the earliest miss; the main failure is the largest region.
    first_symptom = records[regions[0][0]]
    onset, end, region_misses = max(regions, key=lambda r: r[2])
    region_span = end - onset + 1
    rec = records[onset]
    end_rec = records[end]

    if regions[0][0] != onset:
        lines.append("")
        lines.append("First symptom (an earlier wobble it recovered from):")
        lines.append("  Milestone {} on scan page {} ({} miss(es))".format(
            first_symptom['ms'],
            first_symptom.get('miss_page') or first_symptom.get('scan_pg'),
            regions[0][2]))

    lines.append("")
    lines.append("Consistent misses begin here:")
    lines.append("  Milestone page number : {}".format(rec['ms']))
    lines.append("  Scan page             : {}".format(rec.get('miss_page') or rec.get('scan_pg')))
    lines.append("  Word doc              : {}".format(rec.get('doc') or '(unknown -- run had debug off)'))
    lines.append("  Failure region        : {} -> {}  ({} of {} milestones missed)".format(
        rec['ms'], end_rec['ms'], region_misses, region_span))
    if rec.get('looking_for'):
        lines.append("  OCR line it sought    : {}".format(rec['looking_for']))
    if rec.get('doc_area'):
        lines.append("  Unicode doc stuck at  : {}".format(rec['doc_area']))

    prev = last_hit_before(records, onset)
    if prev is not None:
        lines.append("")
        lines.append("Last milestone placed correctly before the drift:")
        lines.append("  Milestone page number : {}".format(prev['ms']))
        lines.append("  Scan page             : {}".format(prev.get('scan_pg')))
        lines.append("  Word doc              : {}".format(prev.get('doc')))
        if prev.get('text_chunk'):
            # #$#$#$# marks where the milestone was inserted (before#$#$#$#after).
            lines.append("  Inserted at           : {}".format(prev['text_chunk']))
    else:
        lines.append("")
        lines.append("  (No successful milestone before this point -- the drift starts at the top.)")

    return "\n".join(lines)


def diagnose(logpath):
    """Parse logpath and return a diagnosis report string."""
    records = parse_records(logpath)
    return format_report(records, logpath)


def main():
    parser = argparse.ArgumentParser(
        description="Find where milestone insertion started consistently missing.")
    parser.add_argument('log', nargs='?',
                        help='Path to a run log. If omitted, use -v to locate the newest one.')
    parser.add_argument('-v', '--vol', help='Volume number; finds newest kama-vol-NNN-*.log')
    parser.add_argument('-l', '--logdir', default=DEFAULT_LOGDIR,
                        help='Log directory (default: workspace/logs next to this script)')
    parser.add_argument('-w', '--window', type=int, default=12,
                        help='Look-ahead window for judging a consistent miss run (default: 12)')
    parser.add_argument('-r', '--ratio', type=float, default=0.7,
                        help='Miss fraction within the window that counts as consistent (default: 0.7)')
    args = parser.parse_args()

    logpath = args.log
    if logpath is None:
        if not args.vol or not args.vol.isnumeric():
            parser.error('Provide a log path or a numeric -v/--vol.')
        volfile = 'kama-vol-{}'.format(str(int(args.vol)).zfill(3))
        logpath = find_main_log(args.logdir, volfile)
        if logpath is None:
            print("No run log found for {} in {}".format(volfile, args.logdir))
            return 1
    if not os.path.exists(logpath):
        print("Log not found: {}".format(logpath))
        return 1

    records = parse_records(logpath)
    print(format_report(records, logpath))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
