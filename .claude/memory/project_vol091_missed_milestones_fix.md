---
name: project-vol091-missed-milestones-fix
description: CLOSED 2026-10-25 — vol 091 missed milestones (combining marks U+0F35/U+0F37) fixed in PR #9, vol re-run and posted to Teams
metadata:
  type: project
---

**Status: closed.** Vol 091 and vol 122 were re-run correctly and their files are on Teams
(confirmed by the user 2026-10-25). Nothing pending here.

**Cause (2026-10-03 run, 110 misses, no single failure region):** Unicode docs carry combining
marks U+0F37/U+0F35 after most syllables (~25% of chars in refrain passages). They (1) consume
the fuzzy `ldist=5` budget and (2) inflate raw length so the `avg_ln_len*factor` window covers too
few real chars; after a few misses the index lags and the target lies beyond the chunk.

**Fix (PR #9, merged 2026-10-04):** `UniVol.get_search_chunk` builds the chunk from raw text with
U+0F35/U+0F37 stripped, sized in stripped chars, and keeps `chunk_map` (stripped idx → raw offset);
`find_insertion_point` maps the match back via `UniVol.raw_offset`, so milestones still land at the
right raw position. Vol 091 (`-v 91 -s 3 -c -d`): 110 → 32 misses; the old [155.1]–[155.4] region
(KAMA-091-b) and scattered leftovers were handled in the final accepted run.

**How to apply:** if another volume shows 100+ *scattered* misses (no single region in
`diagnose_log.py`), suspect combining marks / window sizing first, not OCR drift. Untried ideas
are in [[project-improvement-backlog]]. Related: [[project-kama-pipeline-state]].
