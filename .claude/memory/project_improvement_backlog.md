---
name: project-improvement-backlog
description: Remaining code-quality fixes identified but not scheduled (suggestions, not approved work)
metadata:
  type: project
---

From a code review on 2026-06-27. The `OCRVol` shared-`lines` bug and the broken `clear_files` are
fixed; the no-input-files crash was fixed 2026-10-11 (PR #10); `ocrfolder` is now repo-relative.
Still open, rough priority:

- **Mutable default args** in `OCRVol.__init__` (`skips=[]`, `badblanks=[]`); `badblanks` is mutated.
- **Hard-coded paths**: `HOMEDIR`/`workspace` prefixes (`./tibetan_text_scripts/...`) assume the
  script runs from the repo's *parent* dir; `ocrfolder` still isn't a CLI arg (leftover `TODO`).
- **argparse at import time** in every script — modules can't be imported for tests/reuse.
- **No tests** — the fuzzy matching is the riskiest part; highest-value long-term addition.
- **Duplicated helpers** across `add_styles2docx.py` and `split_into_texts_delim.py`.
- **Dead/commented code** in `insert_milestones.py`.
- Ideas never tried for missed milestones: advance `index` on a miss; tighten `ldist` now that
  combining marks no longer eat the budget (see [[project-vol091-missed-milestones-fix]]).

These are suggestions the user found useful but hasn't scheduled — confirm before doing any.
