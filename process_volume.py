"""
Orchestrate the milestone-insertion -> styling pipeline.

Runs ``insert_milestones.py`` with the milestone arguments you forward to it,
then reads the ``*-missed-ms.log`` summary line to count how many milestones
were not inserted. If that count is at or below ``--threshold`` the script
stages the milestoned ``*-pgd.txt`` files and runs ``add_styles2docx.py`` to
produce the THL-styled Word docs; otherwise it stops so you can fix the volume
and rerun.

Argument convention (hybrid): this script owns the few flags it must reason
about -- ``-v`` (to locate the log), ``--threshold`` (the gate), and the
add_styles styling flags (``-a``/``-m``/``-t``). Everything after a ``--``
separator is forwarded verbatim to ``insert_milestones.py``::

    python tibetan_text_scripts/process_volume.py -v 66 --threshold 50 -a -m \
        -- -s 8 -b 12,13 -br 40

Do NOT put ``-v`` in the forwarded section; this script supplies it to
``insert_milestones.py`` itself.

Staging uses a dedicated ``workspace/stage`` directory rather than
``workspace/in`` so that ``workspace/in/bak`` -- the pristine original Word
docs that insert_milestones backs up for reruns -- is never touched.
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

import diagnose_log

# Anchor every path on this script's own location so the orchestrator works
# regardless of the current working directory. The sibling scripts, however,
# use hard-coded ``./tibetan_text_scripts/...`` paths, so we launch them with
# cwd set to this repo's parent (PARENT_DIR) and reference them by absolute path.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.join(SCRIPT_DIR, 'workspace')
OUTDIR = os.path.join(WORKSPACE, 'out')
OUTBAK = os.path.join(OUTDIR, 'bak')
STAGEDIR = os.path.join(WORKSPACE, 'stage')
LOGDIR = os.path.join(WORKSPACE, 'logs')

INSERT_SCRIPT = os.path.join(SCRIPT_DIR, 'insert_milestones.py')
STYLES_SCRIPT = os.path.join(SCRIPT_DIR, 'add_styles2docx.py')

# Matches the summary line insert_milestones writes first in the missed-ms log,
# e.g. "****** 3 Milestones not inserted for kama-vol-066 ******".
SUMMARY_RE = re.compile(r'(\d+)\s+Milestones not inserted')


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Run insert_milestones, gate on the missed-milestone count, '
                    'then stage and run add_styles2docx.',
        epilog='Forward insert_milestones arguments after a "--" separator, '
               'e.g.: -v 66 --threshold 50 -a -m -- -s 8 -b 12,13')
    parser.add_argument('-v', '--vol', required=True,
                        help='Volume number (same value passed to insert_milestones); '
                             'used to locate the kama-vol-NNN-missed-ms.log')
    parser.add_argument('-th', '--threshold', type=int, default=50,
                        help='Proceed to styling only if missed milestones <= this (default: 50)')
    parser.add_argument('-a', '--annotations', action='store_true',
                        help='Pass -a to add_styles2docx (style « » annotations)')
    parser.add_argument('-m', '--milestones', action='store_true',
                        help='Pass -m to add_styles2docx (style page/line milestones)')
    parser.add_argument('-t', '--table', action='store_true',
                        help='Pass -t to add_styles2docx (add metadata table)')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Run insert_milestones and report the missed count, '
                             'but skip staging and styling')
    parser.add_argument('passthrough', nargs=argparse.REMAINDER,
                        help='Everything after "--" is forwarded to insert_milestones.py')
    return parser.parse_args(argv)


def run_subprocess(cmd, label):
    """Run a child script from PARENT_DIR so its relative paths resolve. Returns exit code."""
    print("\n=== {} ===".format(label))
    print("$ {}".format(' '.join(cmd)))
    return subprocess.run(cmd, cwd=PARENT_DIR).returncode


def read_missed_count(volfile):
    """Return the missed-milestone count from the log's summary line, or None if unreadable."""
    logpath = os.path.join(LOGDIR, volfile + '-missed-ms.log')
    if not os.path.exists(logpath):
        print("Missed-milestone log not found: {}".format(logpath))
        return None
    with open(logpath, 'r') as f:
        first_line = f.readline()
    match = SUMMARY_RE.search(first_line)
    if not match:
        print("Could not parse the missed-milestone summary line in {}".format(logpath))
        print("First line was: {!r}".format(first_line))
        return None
    return int(match.group(1))


def stage_milestoned_files():
    """Copy out/*-pgd.txt into a fresh workspace/stage and back them up to out/bak.

    Returns the number of files staged, or 0 if there were none to stage.
    """
    pgd_files = glob.glob(os.path.join(OUTDIR, '*-pgd.txt'))
    if not pgd_files:
        print("No *-pgd.txt files found in {} to stage.".format(OUTDIR))
        return 0

    # Recreate the staging dir from scratch so stale files from a previous
    # volume (and add_styles' own stage/bak churn) cannot leak into this run.
    if os.path.isdir(STAGEDIR):
        shutil.rmtree(STAGEDIR)
    os.makedirs(STAGEDIR)
    os.makedirs(OUTBAK, exist_ok=True)

    for f in pgd_files:
        shutil.copy(f, STAGEDIR)   # input for add_styles
        shutil.copy(f, OUTBAK)     # safekeeping copy
        os.remove(f)               # drop the .txt from out/ so only final .docx stay on top
    print("Staged {} file(s) into {}; moved originals to {}.".format(len(pgd_files), STAGEDIR, OUTBAK))
    return len(pgd_files)


def count_output_milestones():
    """Tally the milestoned output for the final summary.

    Reads the staged ``*-pgd.txt`` files and returns ``(inserted, pages)`` where
    ``inserted`` is the number of line milestones (``[p.l]``) actually placed --
    the same unit as the missed-milestone count -- and ``pages`` is the highest
    page number seen across page (``[p]``) and line (``[p.l]``) milestones, i.e.
    the volume's last/total page. Call this while the staged files are still in
    workspace/stage; add_styles moves them into stage/bak as it runs.
    """
    inserted = 0
    max_page = 0
    for f in glob.glob(os.path.join(STAGEDIR, '*-pgd.txt')):
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        inserted += len(re.findall(r'\[\d+\.\d+\]', text))
        for p in re.findall(r'\[(\d+)(?:\.\d+)?\]', text):
            max_page = max(max_page, int(p))
    return inserted, max_page


def main(argv):
    args = parse_args(argv)

    if not args.vol.isnumeric():
        print("Volume '{}' is not numeric. Bye!".format(args.vol))
        return 2
    volfile = 'kama-vol-{}'.format(str(int(args.vol)).zfill(3))

    # argparse.REMAINDER keeps the leading "--"; drop it before forwarding.
    forwarded = args.passthrough
    if forwarded and forwarded[0] == '--':
        forwarded = forwarded[1:]

    # --- Stage 1: insert milestones --------------------------------------
    insert_cmd = [sys.executable, INSERT_SCRIPT, '-v', args.vol] + forwarded
    if run_subprocess(insert_cmd, "insert_milestones.py") != 0:
        print("\ninsert_milestones.py failed; aborting before styling.")
        return 1

    # --- Gate: check the missed-milestone count --------------------------
    missed = read_missed_count(volfile)
    if missed is None:
        print("\nCannot determine missed-milestone count; aborting before styling.")
        return 1
    print("\nMissed milestones: {} (threshold: {})".format(missed, args.threshold))
    if missed > args.threshold:
        print("Over threshold -- stopping. Fix the volume and rerun; "
              "originals remain in workspace/in/bak.")
        print()
        logpath = diagnose_log.find_main_log(LOGDIR, volfile)
        if logpath is None:
            print("(No run log found to diagnose where the misses start.)")
        else:
            print(diagnose_log.diagnose(logpath))
        return 1

    if args.dry_run:
        print("Within threshold. Dry run -- skipping staging and styling.")
        return 0

    # --- Stage 2: stage files and run add_styles -------------------------
    staged = stage_milestoned_files()
    if staged == 0:
        print("Nothing to style; aborting.")
        return 1

    # Count now, while the staged *-pgd.txt files are still in workspace/stage;
    # add_styles moves them into stage/bak as it runs.
    inserted, pages = count_output_milestones()

    style_flags = []
    if args.annotations:
        style_flags.append('-a')
    if args.milestones:
        style_flags.append('-m')
    if args.table:
        style_flags.append('-t')
    styles_cmd = [sys.executable, STYLES_SCRIPT, '-i', 'workspace/stage'] + style_flags
    if run_subprocess(styles_cmd, "add_styles2docx.py") != 0:
        print("\nadd_styles2docx.py failed.")
        return 1

    print("\nMilestones inserted and styles added to {} document(s). "
          "{} total pages. {} out of a total of {} milestones missed.".format(
              staged, pages, missed, inserted))
    print("Styled documents are in {}.".format(OUTDIR))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
