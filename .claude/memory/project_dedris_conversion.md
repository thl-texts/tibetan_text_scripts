---
name: project-dedris-conversion
description: "Status of the Dedris (Sambhota font) -> Unicode Python converter, replacing udp.exe"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9ea9e228-eb1f-4f7a-aada-2d55d6901962
  modified: 2026-09-08T15:35:35.259Z
---

RESOLVED as of 2026-09-08: the Dedris (Sambhota font family, Nitartha International 1999)
keystroke -> Unicode converter is done and working, converting the actual targets
(`KAMA-084-e.doc`/`f.doc`) cleanly. Full detail: `DEDRIS_CONVERSION_PLAN.md`'s "RESOLVED —
2026-09-08" section (bottom of file) and `SESSION_LOG.md`'s 2026-09-08 entry — read those
before assuming anything below is still accurate, this is a condensed pointer.

MERGED to `master` 2026-09-27 via PR #8; the `dedris-converter` branch is deleted (local and remote).

**How it actually got solved**, after two abandoned approaches (statistical frequency-rank
matching, then OCR-based glyph recognition — both described in earlier sessions/plan sections
and not worth resuming): the user ran the real `udp2302.exe` (the Windows tool this whole
converter was meant to replace) via CrossOver on the Mac, then copied its installed program
directory (containing real `.fuf` keystroke->Unicode tables per font) out to
`resources/fonts/UnicDocP/`. `build_dedris_map_from_fuf.py` parses those directly into
`resources/dedris-map.json` — no more guessing needed. `build_dedris_map.py` and
`make_review_doc.py` (the statistical-era trainer/reviewer) were deleted as obsolete.

**Why:** THL wants a scriptable, Mac-only replacement for the pipeline that previously needed
a Windows VM and the proprietary `udp.exe` GUI tool.

**How to apply:** this specific plan (`e`/`f` conversion) is done — don't resume it. If asked
to convert *another* Dedris-encoded volume in the future: just run `convert_dedris.py` per the
README's "Converting Dedris-Family Sambhota Files" section; `resources/dedris-map.json` already
has the ground-truth table for every Dedris sub-font (Dedris-a through -g, -a1/-a2/-a3, -vowa,
-syma — 2600+ entries). Only regenerate the table (needs `resources/fonts/UnicDocP/`, which is
gitignored and not in the repo — see README for how to get it again via CrossOver) if the map
file is missing or a newer UDP version surfaces.

**Non-obvious things worth remembering if similar work comes up again**:
- `resources/fonts/` and `resources/old/` are now gitignored (third-party/legacy files not
  meant to be redistributed) — don't expect font/UDP files to show up in `git status` on a
  fresh clone; they have to be re-fetched per the README.
- A `.fuf` codepoints value of `FFFF` means "pass the keystroke through unchanged" (seen only
  on the space keystroke), not "delete it."
- Not every literal space keystroke in these documents is meaningful — the typist used the
  same space key both for the real, conventional space after a shad (`།`)/sbrul-shad (`༈`) and
  for purely decorative padding between every other syllable. `convert_dedris.py` now strips
  the latter and keeps only the former.
- Homebrew's Wine casks (`wine-stable`/`@staging`/`@devel`) are disabled as of 2026-09-01
  (fail Gatekeeper) — CrossOver's free trial is the working alternative for running old
  Windows `.exe` tools on this Mac when that's ever needed again.

[[feedback-tibetan-review-format]] (the fill-in-table review-doc technique) is now moot for
this specific project since ground truth replaced hand-review, but the technique itself is
still valid guidance for any *future* situation needing the user to correct Tibetan Unicode
text by hand.
