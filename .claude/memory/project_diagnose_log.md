---
name: project-diagnose-log
description: diagnose_log.py finds where a milestone run began consistently missing; auto-runs in process_volume's over-threshold path
metadata:
  type: project
---

`diagnose_log.py` (added 2026-06-29, merged in PR #6) is a **read-only** analyzer for a milestone
run that went over `--threshold`. It parses the timestamped run log
`workspace/logs/kama-vol-NNN-<datetime>.log` (not the `-missed-ms.log` summary) and reports where
insertion went off the rails.

**Why it matters:** in `insert_milestones.py`, when `find_insertion_point` fails and the Unicode
doc isn't near its end, it logs a warning and continues without advancing the doc index, so one
bad anchor can cascade into thousands of misses. The tool separates a recovered "wobble" from the
real sustained collapse (gap-tolerant region grouping) and reports the onset: milestone, scan
page, Word doc, OCR line sought, where the Unicode doc was stuck, last good placement.

Keys on: header `Milestone: [p.l] (Curr pg: N, Curr Doc: doc)` (debug on, the default here), hit
`Text chunk: …#$#$#$#…`, miss `!!! Milestone … not found (scanpg.ln) for: … !!!`.
Standalone: `python diagnose_log.py -v 67` or pass a log path. Validated on KAMA-067 (3107 misses →
collapse at [74.1]/scan 77.1; root cause was a duplicate scan, see [[project-ocr-page-fix-workflow]]).

Note: it shows *scattered* misses poorly (vol 091's 110 misses had no single region); that case
was a matcher problem, see [[project-vol091-missed-milestones-fix]].
