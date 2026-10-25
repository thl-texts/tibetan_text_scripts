---
name: project-kama-pipeline-state
description: "Where the Kama pipeline stands (as of 2026-10-25): tooling merged to master, vols 066/067/084/091/122 done; nothing open"
metadata:
  type: project
---

Than Grove ([[user-than-grove]]) is building a toolkit for converting and milestoning Peltsek Kama
volumes for THL. Per volume: insert OCR-based milestones (`insert_milestones.py`) → apply THL
docx styles (`add_styles2docx.py`), or both via `process_volume.py`
([[project-process-volume-orchestrator]]). Finished styled files are posted to **Teams**.

**State as of 2026-10-25 — `master` clean and in sync with `origin/master`; no open branches/PRs:**
- Tooling merged: orchestrator, `diagnose_log.py`, OCR page tools, `clear_all.py`, Dedris converter
  ([[project-dedris-conversion]], PR #8), vol-091 combining-marks fix (PR #9), graceful exit when
  `in/` has no chunk files (PR #10).
- Volumes done and posted to Teams: 066, 067 (after OCR fix, 5 missed), 084 (a–e, 12 missed),
  **091 and 122 (re-run correctly, confirmed 2026-10-25)**.
- Open items: none for specific volumes. Only the unscheduled [[project-improvement-backlog]].

**Config facts:** `insert_milestones.py` `ocrfolder = './tibetan_text_scripts/resources/ocr'`
(commit 2951d4a). Scripts expect to run from the repo's *parent* dir.

**Gitignored folders are NOT portable.** `workspace/`, `resources/ocr/`, `resources/worddocs/`,
`test/` and the Teams output folder are excluded from the repo, so where they live (and whether
they exist or hold the same volumes) differs from computer to computer (Than's instruction,
2026-10-25). Never assume a path or file from an earlier session or another machine exists here:
check the actual directory first, and if the OCR/workspace data is elsewhere, adjust `ocrfolder`
locally (or pass paths) rather than committing a machine-specific path.

**Lessons:** when a styled docx looks wrong, check the template/styling layer before the matching
logic (the 2026-08-17 bugs were a hidden-text flag on "Page Number Print Edition" and a missing
complex-script `cs` font slot for Jomolhari — fixed in `84a5531`). Docx files embed their own copy
of the template styles, so fixing the template doesn't fix already-generated docs; regenerate.
Huge miss count → OCR drift ([[project-ocr-page-fix-workflow]]); scattered misses → matcher
([[project-vol091-missed-milestones-fix]]).

Full narrative history is in `SESSION_LOG.md` ([[session-log-convention]]).
