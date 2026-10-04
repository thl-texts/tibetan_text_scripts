---
name: project-vol091-missed-milestones-fix
description: Diagnosed cause of 100+ missed milestones in kama vol 091 (combining marks U+0F35/U+0F37 + undersized search window) and the fix, IMPLEMENTED 2026-10-04 (110 -> 32 misses).
metadata:
  type: project
---

Vol 091 (2026-10-03 run, log `kama-vol-091-2026-10-03_11-38.log`) missed 110 milestones with no single failure region. Text IS in the doc (user verified e.g. [266.1] in KAMA-091-c).

**Cause:** Unicode docs carry combining marks U+0F37/U+0F35 after most syllables (~25% of chars in refrain passages). They (1) consume the fuzzy `ldist=5` budget and (2) inflate raw length so the `avg_ln_len*factor` window covers too few real chars; after a few misses the index lags and the target lies beyond the chunk (~300 chars ahead for [266.1]).

**Fix to implement next:** search a mark-stripped copy of the chunk with an index map back to raw positions; size window in stripped chars; maybe advance index on a miss; optionally tighten ldist. Re-run vol 091 and compare missed count. Details in SESSION_LOG.md (2026-10-03 entry).

**Why:** user left mid-session and asked to remember the fix for next time. **How to apply:** when user resumes vol 091 / missed-milestone work, start from this fix instead of re-diagnosing. Related: [[project-kama-pipeline-state]].

**Status (2026-10-03):** branch `fix-vol091-combining-marks` is pushed (SESSION_LOG entry, ocrfolder change, .DS_Store untracked) but contains NO code fix yet. At the start of the next session, remind the user this fix is pending and offer to implement it on that branch.

**Update 2026-10-04:** fix implemented and pushed on `fix-vol091-combining-marks` (commit after 764e7b1); vol 091 re-run (`-v 91 -s 3 -c -d`) gives 32 misses. Remaining: region at [155.1]-[155.4] (KAMA-091-b) + scattered. Branch not yet merged to master / no PR. Ignore the 'pending' reminder above.
