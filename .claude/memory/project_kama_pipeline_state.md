---
name: project-kama-pipeline-state
description: "Current working state of the Tibetan Text Scripts repo — active volume-processing pipeline, developer identity, recent template/font bug fixes."
metadata: 
  node_type: memory
  type: project
  originSessionId: c8459d9a-31eb-4f32-8138-25b8a76019b4
  modified: 2026-09-27T13:12:32.796Z
---

The user (Than Grove) is the original developer of this repo (created 2019-07-31), building
a toolkit for converting and milestoning Peltsek Kama volumes for THL (Tibetan & Himalayan
Library). The active workflow per volume is: insert OCR-based milestones
(`insert_milestones.py`) → apply THL docx styles (`add_styles2docx.py`), or both via
`process_volume.py`.

`insert_milestones.py`'s `ocrfolder` is set to a relative path,
`./tibetan_text_scripts/workspace/ocr` (matching the `workspace = './tibetan_text_scripts/workspace'`
convention right above it), settled and committed as of `ff07857` (2026-08-17). It went
through an absolute-path version first (`237f27c`) before the user confirmed the relative
form is what they want.

On 2026-08-17 a session diagnosed and fixed two docx-output bugs for kama-vol-068: page
milestones invisible due to a hidden-text flag on the template's "Page Number Print Edition"
style, and Tibetan text rendering as Jomolhari-ID instead of Jomolhari because
`set_tib_font()` only set the ascii/hAnsi font slots, never the complex-script (`cs`) slot
Word actually uses for Tibetan. Both fixed and pushed (`84a5531`). Full writeup lives in
[[session-log-convention]] under `SESSION_LOG.md`.

`kama-vol-084` (texts a–e) finished and posted to Teams as of 2026-09-27 — that's where the
user stores paged/styled output files. `KAMA-084-e.docx` had gone missing from the source
input at some point and was recreated from OCR before that run; the run logged 12
unmatched milestones (under threshold, accepted without a `diagnose_log.py` deep-dive). Also
as of 2026-09-27, [[project-dedris-conversion]]'s converter and other accumulated updates are
merged to `master` (PR #8, `4adf2ab`); `dedris-converter` branch deleted both locally and on
`origin`. Full detail in `SESSION_LOG.md`'s 2026-09-27 entry.

**Why:** These aren't structural changes — they're incremental fixes/tuning as the user
runs the pipeline for the first time on this machine.

**How to apply:** Don't assume `insert_milestones.py`/template state is final; check current
git diff and `SESSION_LOG.md` for the latest before making further changes. When a styled
docx output looks wrong, check the template/styling layer before assuming the
milestone-insertion logic is broken — both bugs found this session were template/styling
issues.
