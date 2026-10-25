---
name: project-process-volume-orchestrator
description: process_volume.py chains insert_milestones -> add_styles2docx with a missed-milestone gate; design decisions not to undo
metadata:
  type: project
---

`process_volume.py` (added 2026-06-28; merged to master 2026-06-30 in PR #6) automates the
hand-off between the two pipeline stages. Verified on KAMA-066, later used on 067, 084, 091, 122.

**What it does:** runs `insert_milestones.py`, parses the missed-milestone count from the first
line of `workspace/logs/kama-vol-NNN-missed-ms.log`, and only proceeds to styling if
`N <= --threshold` (default 50). On pass it clears `workspace/stage`, copies `out/*-pgd.txt` into
it and into `out/bak`, then runs `add_styles2docx.py -i workspace/stage`. Only the final
`*-pgd.docx` remain in `out/`. Over threshold, it prints a `diagnose_log.py` report and stops
(see [[project-diagnose-log]]). Prints a summary line: "Milestones inserted and styles added to N
document(s). P total pages. M out of a total of T milestones missed."

**Design decisions (don't undo without asking):**
- Shells out to both scripts via `subprocess` so they stay untouched (avoids their import-time
  argparse). Children run with `cwd=PARENT_DIR` so their `./tibetan_text_scripts/...` paths
  resolve; the orchestrator anchors its own paths on `__file__`.
- **Hybrid args:** owns `-v`, `--threshold`, `-a/-m/-t`, `-n/--dry-run`; everything after `--` is
  forwarded to `insert_milestones.py`. `-v` is zero-padded to 3 digits. Never put `-v` after `--`.
- **Uses `workspace/stage`, not `workspace/in`.** `add_styles`' `standardize_in_files` moves its
  input `.txt` into `<in>/bak`; reusing `in/` would pollute `in/bak`, which is the pristine
  restore set for `-c` reruns.
- Total-page count is taken *before* styling (afterwards the `-pgd.txt` have moved to `stage/bak`
  and it printed 0 — fixed in PR #7).

Typical run (from the repo's PARENT dir):
`python tibetan_text_scripts/process_volume.py -v 67 --threshold 25 -a -m -- -s 4 -c`
