# Plan: Dedris (Sambhota-family) → Unicode Tibetan Converter

## Context

The repo's only existing "Sambhota → Unicode" conversion path is external and non-Python: a
multi-machine pipeline (`doc2rtf.sh` → transfer to a Windows VM → the proprietary `udp.exe`
tool → transfer back → `rtf2docx.sh` → `add_styles2docx.py`). This works, but requires a
Windows machine and a GUI tool that isn't scriptable or vendored.

The user downloaded the actual Dedris font files (`Dedris-a`, `Dedris-a1`, `Dedris-vowa`)
from fontsgeek.com into `resources/fonts/` and asked whether we have enough information to
write a pure-Python converter for documents in these Sambhota-family "Dedris" fonts (Nitartha
International, 1999), used for the Peltsek Kama collection.

**Key discovery driving this plan**: `workspace/in/sambhota/KAMA-084-{a,b,c,d}.doc` (the
original Sambhota-encoded files) and `workspace/in/KAMA-084-{a,b,c,d}.docx` (the same content,
already correctly converted to Unicode, evidently via the existing UDP pipeline) sit side by
side in the workspace. This is a ready-made parallel corpus. `KAMA-084-e.doc`/`f.doc` are the
actual unconverted targets. This means the conversion table doesn't need to be sourced from
font/vendor documentation (none exists) — it can be **learned empirically** by aligning the
Sambhota originals against their known-correct Unicode counterparts, then validated on
held-out data before being trusted on `e`/`f`.

A second discovery changes scope from the original 2-font assumption: LibreOffice-based
inspection shows `KAMA-084-a.doc` alone uses at least 8 distinct font names in its body text
(`Dedris-a`, `-a1`, `-b`, `-b1`, `-c`, `-d`, `-e`, `-vowa`), and `KAMA-084-e.doc`'s style
catalog references `-a2`, `-a3`, `-f` as well (need to confirm those are actually used in
body text, not just declared/unused). Only `Dedris-a`, `-a1`, `-vowa` have `.ttf` files
currently in `resources/fonts/`. Per the user: proceed without acquiring the missing font
files for now (the alignment method doesn't strictly need them), but track which font names
are actually encountered so the user can pull them from fontsgeek later if needed for
resolving rare/ambiguous tokens.

**Intended outcome**: a set of scripts that (1) train a Dedris→Unicode mapping table from the
`a`–`d` ground truth, (2) validate it on held-out data, and (3) convert `e`/`f` (and future
Dedris-encoded volumes) without needing Windows/`udp.exe`, flagging any untranslatable tokens
for human review rather than guessing silently.

## Encoding model (confirmed this session)

- Dedris is a classic Sambhota-style multi-font input scheme: many font families are mapped
  onto the same small printable-ASCII keystroke alphabet; the *font active at each keystroke*
  determines whether a key produces a base consonant, a subjoined/stacked form, a vowel sign,
  etc. Confirmed the document text is 100% within 7-bit ASCII (no high-bit/hex-escaped chars).
- Characters are typed as **one single interleaved stream in ordinary reading order**,
  with fonts switching character-by-character — visual stacking comes from each font's glyph
  design, not from document-level layering or manual cursor positioning. This was confirmed by
  inspecting raw ODT markup showing font switches at single-character granularity within
  continuous runs.
- **Corrected encoding model (per the user, who designed/knows this font family directly)**:
  each single Dedris keystroke doesn't represent one Tibetan letter — **it represents an
  entire pre-rendered consonant stack** (2 or more Tibetan letters glued into one glyph in the
  font), which is why a font like Dedris-a needs so many distinct byte values: one per
  distinct stack combination the typist might need, not one per letter. Converting one such
  keystroke therefore expands to a *set* of 2+ Unicode codepoints (the stack's base consonant
  plus its subjoined-form codepoint(s)), not just 1. Vowel signs are a separate keystroke
  (Dedris-vowa) applied per syllable on top of/after the stack. **This means the
  "composition/assembly" step (§4 below) is simpler than originally framed**: no generic
  Tibetan base→subjoined→vowel reordering state machine is needed — each keystroke resolves
  independently (via the flat per-font lookup table trained in §3) to its correct, *already
  correctly-ordered* Unicode string (1, 2, or more codepoints), and assembly is just
  concatenating those resolved strings in keystroke order, inserting tsek at syllable
  boundaries. This also means the alignment DP in §3 step 4 must allow a Dedris token to map
  to more than 2 Unicode codepoints (3+ for bigger stacks), not just 0/1/2 as originally
  scoped.
- `textutil` (already used by `doc2rtf.sh`) is **not usable for extraction** — since the real
  Dedris fonts aren't installed on macOS, Word's own `.doc` reader silently collapses runs into
  substitute fonts (`Times`/`Times New Roman`), destroying the font-switch signal this whole
  approach depends on. **LibreOffice's headless flat-ODT export** (`soffice --headless
  --convert-to fodt`) must be used instead, since it preserves real font-table names from the
  legacy `.doc` regardless of what's installed. LibreOffice is already installed on this
  machine (`/Applications/LibreOffice.app`). Always invoke it with an isolated
  `-env:UserInstallation=file://<scratch-dir>` profile (e.g. under `workspace/temp/`) — a
  stray running `soffice` process can otherwise hang a naive headless call waiting on the
  default profile lock.

## Module/script organization

New code, following the repo's existing `tibtexts/` (reusable classes) + top-level
`argparse` runner + `workspace/in→out`/`bak`/`temp` + `workspace/logs/` conventions:

- **`tibtexts/fodtdoc.py`** — `FodtDoc` class. `FodtDoc.from_doc(path, workdir)` shells out to
  `soffice --headless -env:UserInstallation=... --convert-to fodt`, then parses the resulting
  flat-XML file with `lxml` (already a dependency): resolves `office:automatic-styles`/
  `office:styles` (`style:font-name`/`fo:font-family`/`style:font-family`, following
  `style:parent-style-name` chains) into a `style-name → font-name` map, then walks
  `office:text` paragraphs and their `text:span` runs (plus bare text inheriting the
  paragraph's own style) to yield, per paragraph, an ordered `[(font_name, char), ...]`
  sequence at single-character granularity — mirroring `OCRVol`'s per-line iterator shape.
- **`tibtexts/dedrismap.py`** — `DedrisMap` class: loads the persisted mapping table (JSON),
  exposes `resolve(font_name, char) -> (unicode_unit, confidence)`, and records/reports misses
  (unknown `(font, char)` pairs) plus **every distinct font name it's asked to resolve**, so
  a per-volume "fonts encountered" list can be reported (this is the tracking the user asked
  for re: fontsgeek downloads).
- **`tibtexts/dedrissyllable.py`** — syllable buffering/assembly: consumes a paragraph's
  `[(font, char)]` stream plus a `DedrisMap`, groups into tsek-delimited syllables, emits
  assembled Unicode paragraph text plus a list of untranslatable spots (paragraph/char
  position). Reuses `UniVol.normalize_pairs`-style punctuation cleanup as a post-pass (e.g.
  collapsing doubled tsek) rather than reimplementing it.
> **CORRECTION (2026-09-07, during implementation)**: step 2 below ("paragraph-aligns
> directly by index... same source document") turned out to be **false**. Measured
> character/tsek counts show `KAMA-084-{a,b,c,d}.doc` do NOT correspond 1:1 by letter to
> `KAMA-084-{a,b,c,d}.docx` — e.g. `a.doc` has ~35,700 raw keystrokes but `a.docx` has
> ~114,000 Unicode chars (3.2x, far more than stacking expansion explains), and paragraph
> structure differs (`b.docx` bundles two separate titled texts; `b.doc` doesn't). But the
> **aggregate** totals line up well: all six `.doc` originals (a-f) sum to 593,175 raw
> keystrokes; a+b+c+d alone sum to 405,929; the four converted `.docx` (a-d) sum to 439,001
> Unicode chars — only 8% expansion, exactly what real conversion should produce. Conclusion:
> the "already converted" docx set was re-chunked by actual text/title boundaries (this is a
> multi-text Kama collection), not by the typist's arbitrary a-f file split. **Fix**:
> concatenate all six `.doc` streams (a-f, in order) into one stream, and all four `.docx`
> texts (a-d, in order) into another, and align those two globally (anchor-based, à la
> `insert_milestones.py`'s existing `fuzzysearch`-based OCR-vs-Unicode matching) rather than
> pairing per letter. Steps 1-2 below are superseded by this; steps 3-7 still apply, just
> operating on the two concatenated streams instead of per-letter pairs.

- **`build_dedris_map.py`** (top-level, run rarely/offline) — the **trainer**:
  1. Extracts `(font, char)` streams from `workspace/in/sambhota/KAMA-084-{a,b,c}.doc` via
     `FodtDoc`, and clean Unicode paragraph text from `workspace/in/KAMA-084-{a,b,c}.docx`
     via `python-docx`.
  2. Paragraph-aligns directly by index (same source document, should line up 1:1; log/skip
     any length mismatch rather than force-align).
  3. Anchors on tsek/shad via frequency correlation to fix the highest-confidence tokens
     first, then segments both sides into tsek-delimited syllable blocks using those anchors.
  4. Aligns within each syllable pair with a small custom DP (Needleman-Wunsch-style,
     allowing one Dedris token → 0 to ~4 Unicode codepoints, since one keystroke can be an
     entire pre-rendered multi-letter consonant stack, not just a single letter) — not
     `difflib`, which isn't built for cross-alphabet alignment.
  5. Aggregates per-token votes across the corpus; a token is "confident" above a vote
     threshold (start at ≥95% agreement), otherwise flagged for manual review.
  6. Writes the table to **`resources/dedris-map.json`** (committed to the repo like other
     reference data, e.g. `resources/tibtext-styled-tpl-2023-09-26.docx` — not workspace
     scratch, since it's expensive to derive and should be diffable/reviewable/correctable by
     hand over time, not silently regenerated).
  7. Writes a human-readable alignment report to `workspace/logs/` (ambiguous tokens,
     low-occurrence tokens, any paragraph-alignment mismatches) for manual review, following
     `insert_milestones.py`'s logging convention.
- **`convert_dedris.py`** (top-level, run repeatedly) — the **converter**: `argparse`-driven,
  reads `.doc` files from `workspace/in/sambhota/` (or wherever pointed), runs
  `FodtDoc` → `DedrisMap.resolve` → `dedrissyllable` assembly per paragraph, writes one plain
  `.docx` per input to `workspace/out` via `python-docx` (one `Document()`, `add_paragraph()`
  per source paragraph) — this output is designed to feed unchanged into the existing
  `add_styles2docx.py` step, so nothing downstream of conversion needs to change. Any
  untranslatable/low-confidence token gets an inline marker in the output text (e.g.
  `⟦?font:char?⟧`, echoing `UniVol`'s existing use of `*` to mark uncertain milestone spots)
  plus a per-run log entry (paragraph/char position) under `workspace/logs/`, and the script
  also prints/logs the full set of distinct font names it encountered per input file.

## Validation plan

1. Train on `KAMA-084-{a,b,c}` only; hold out `KAMA-084-d` entirely.
2. Run `convert_dedris.py` on `KAMA-084-d.doc`; diff its output against the existing
   `KAMA-084-d.docx` ground truth — character-level accuracy (edit distance via the
   already-installed `python-Levenshtein`) and syllable-level exact-match rate, with a
   `diagnose_log.py`-style report localizing *where* and on *which token* any drift occurs.
3. Once `-d` validation is acceptable, retrain the mapping on the full `a`–`d` set (more data)
   before using it on `e`/`f`.
4. For `e`/`f` (no ground truth exists): treat the untranslatable/low-confidence-token log as
   the primary QA artifact — a short, greppable list of exact spots for human proofreading —
   rather than claiming automatic correctness. Also surface the "fonts encountered" list so
   the user can see whether any of the not-yet-downloaded fontsgeek fonts (`Dedris-b`, `-b1`,
   `-c`, `-d`, `-e`, `-f`, possibly `-a2`/`-a3`) are actually needed.

## STATUS as of 2026-09-07 end of session (superseded — see "RESOLVED" section at the end)

> **This section is history, not current guidance.** The statistical approach described below
> was abandoned the next session once the real UDP `.fuf` ground-truth tables were found. Jump
> to "RESOLVED — 2026-09-08" at the bottom of this file if you're resuming this work.

**Built and committed** (commits `a754dbd`, `dd5b13e`, `4f1ff22`):
- `tibtexts/fodtdoc.py` (`FodtDoc`) — extraction via LibreOffice headless flat-ODT export.
  Working and validated against all six `KAMA-084-{a..f}.doc`. Fixed one real bug during this
  session: `FodtDoc.from_doc`'s scratch profile/output dir must use **absolute paths** — a
  relative path produced an invalid `file://` URI and caused `soffice` to hang indefinitely
  (600s timeout) instead of erroring, only surfaced when converting a larger file (`d.doc`).
- `tibtexts/dedrismap.py` (`DedrisMap`, `tokenize_unicode`) — table load/save/resolve, and a
  regex-based Unicode Tibetan tokenizer (STACK = consonant + subjoined run, VOWEL = vowel-sign
  run, OTHER = everything else) used to build comparable tokens on the Unicode side.
- `build_dedris_map.py` — trainer. **Superseded the plan's positional-alignment design
  entirely** with **frequency-rank matching** (see next section) once the per-letter
  file-correspondence assumption was found false (see the CORRECTION note above). Anchors on
  tsek (the single most frequent keystroke in the dominant stack font), derives an expected
  unicode/raw count ratio from it, then greedily matches every other raw token to its
  nearest-expected-count unclaimed Unicode candidate token — leaving a poor fit (relative
  error > 35%) unresolved rather than force-matching it.
- `convert_dedris.py` — converter. Resolves each keystroke via `DedrisMap`, concatenates,
  marks unresolved keystrokes inline as `<<font:char>>` plus logs them.

**Why frequency-rank matching instead of positional alignment (§3 as originally written)**:
once `FodtDoc` was working, checking actual character/tsek counts showed
`KAMA-084-{a,b,c,d}.doc` do **not** correspond 1:1 by letter to `KAMA-084-{a,b,c,d}.docx` (see
the CORRECTION note earlier in this doc) — so there's no reliable positional pairing to run a
sequence-alignment DP against. But Tibetan Buddhist commentarial text has a stable enough
letter-frequency distribution that matching by rank/expected-count works for an initial pass,
without needing to know which specific raw file corresponds to which specific converted file.

**Held-out validation result: the frequency-only table is NOT accurate enough on its own.**
Trained on Unicode side = `{a,b,c}.docx` (raw side = all six `.doc`, held out `d`'s Unicode
text only), then ran `convert_dedris.py` on `KAMA-084-d.doc` and compared to the real
`KAMA-084-d.docx`. Result: **garbled, not real Tibetan**, despite individual high-confidence
table entries looking like plausible Tibetan letter clusters in isolation (e.g. `སྐྱ`, `རྒྱ`,
`སྦྱ` all decoded correctly for the dominant font `Dedris-a`). Manually decoding a raw sample
by hand through the trained table suggested why: the **consonant-stack entries are largely
right** (e.g. the sequence decoded to real words like `ཕན` "benefit"), but the **`Dedris-vowa`
(vowel-sign) entries are the weak point** — smaller vocabulary (~29 distinct keys) but lower
confidence scores (0.85–0.92 for the four most common, vs. 0.94–1.00 for common consonants),
and since a vowel appears in nearly every syllable, a handful of wrong vowel entries garble a
huge fraction of all output.

**Vowel corrections confirmed with the user so far** (via manual review, not automatable from
frequency alone — this is the "make a list and ask" collaboration the user proposed):
- Key `'J'` (11,544 occurrences, 4th-most-frequent Dedris-vowa key): trained table had this
  wrong as literal space (0.85 confidence); **confirmed correct value is short-i, U+0F72
  (ི)**. Spotted by noticing exactly 4 basic Tibetan vowels (i/u/e/o) should occupy the 4
  highest-frequency Dedris-vowa keys, and the table only had 3 of them right.
- Key `'R'` (14,362 occurrences, 2nd-most-frequent): trained table had this wrong as plain
  short-u, U+0F75 (ུ); **confirmed correct value is long-u — achung + zhabkyu, U+0F71 U+0F75
  (ཱུ, e.g. ཀཱུ)**. Important pattern: some of these aren't single Unicode codepoints but
  achung-prefixed compounds — don't assume every vowel key is a bare single vowel-sign
  codepoint.
- Keys `'A'` (17,729 occurrences, trained guess: plain o, U+0F7C) and `','` (13,469
  occurrences, trained guess: plain e, U+0F7A) — **NOT YET CONFIRMED**. Given the long-u
  pattern just found for `'R'`, check whether these are also achung-prefixed long forms
  (U+0F71 U+0F7C / U+0F71 U+0F7A) rather than the plain short forms currently guessed, using
  the same "ཀ + this key" question format that worked for R.
- The remaining ~25 low-frequency `Dedris-vowa` entries (each seen ≤255 times; these are
  visible in the training report / `resources/dedris-map.json` once regenerated) have not been
  reviewed at all yet and are exactly the kind of list the user offered to check by hand.

**Review tooling built this session**: `make_review_doc.py` generates a Word table document
(one row per keystroke: current guess + codepoints + a blank "Correct Tibetan" column) for the
user to fill in by hand — built because the terminal's multiple-choice question UI garbles
Tibetan text (see [[feedback-tibetan-review-format]] / SESSION_LOG.md). A first review doc for
all `Dedris-vowa` entries (from the `/tmp` test table, since nothing's been written to the real
`resources/dedris-map.json` yet) is at `workspace/review/dedris-vowa-review.docx` (gitignored —
regenerate with `python make_review_doc.py --map <table.json> --font Dedris-vowa -o
workspace/review/dedris-vowa-review.docx` if it's missing). `build_dedris_map.py` now has a
`KNOWN_ENTRIES` dict (currently holding the J and R corrections) applied after the statistical
pass, so confirmed corrections survive a retrain — add newly-confirmed entries there as the
user fills in more of the review doc.

**Immediate next steps for a resumed session**:
1. Have the user fill in `workspace/review/dedris-vowa-review.docx` (or regenerate it first if
   missing/stale), then transcribe their answers into `build_dedris_map.py`'s `KNOWN_ENTRIES`.
2. Re-run `build_dedris_map.py` for real (no run has yet written to the actual
   `resources/dedris-map.json` default path — all runs so far used `/tmp` test paths and
   scratch copies in gitignored `workspace/in/sambhota-train`, `workspace/in/train-unicode`,
   which can be deleted).
3. Re-run the held-out validation (`convert_dedris.py` on `d.doc`, diff against real
   `d.docx`) and actually check whether accuracy is now acceptable — no accuracy number has
   been computed yet (only qualitative "garbled" vs. "looks plausible" judgment so far); the
   plan's original idea of a `python-Levenshtein`-based character accuracy score, plus a
   `diagnose_log.py`-style localized diff report, still hasn't been implemented.
4. Given vowels are clearly the highest-leverage thing to get right, the review doc above
   already covers all of `Dedris-vowa` — don't spend more time on the long tail of rare
   consonant-stack fonts (`Dedris-c/d/e/f/g/a2/a3/b2` etc., each seen only a handful of times
   in the whole corpus) — those rare fonts will very rarely get hit in practice and are already
   correctly handled by being left unresolved/flagged rather than guessed.
5. Only once `d` validates well should the table be retrained with Unicode side = full
   `{a,b,c,d}.docx` (more data) and then applied to `e`/`f`.

**Loose ends / cleanup**: `workspace/in/sambhota-train/` and `workspace/in/train-unicode/`
(gitignored copies made for the held-out test) can be deleted once no longer needed;
`/tmp/dedris-fonts-check/`, `/tmp/dedris-map-test.json`, `/tmp/dedris-validate/` are ephemeral
and will not persist across machine restarts — regenerate via `build_dedris_map.py`/
`convert_dedris.py` rather than looking for them.

## Open items to settle during implementation (not blocking, but worth surfacing as they arise)

- Confirm whether `Dedris-a2`/`-a3`/`-f` (declared in `e`'s style catalog) are actually used in
  body text there, and do the same font-name check for `b`/`c` (only `a` has been directly
  confirmed as an 8-font document so far).
- Pick a concrete accuracy/confidence threshold for "trust this without a human check" —
  propose starting the conversation from `process_volume.py`'s existing configurable
  `--threshold` pattern rather than inventing a new one.

## Verification

- Run `build_dedris_map.py` then `convert_dedris.py -d` (held-out) and confirm the accuracy
  report; inspect flagged low-confidence tokens by hand.
- Run `convert_dedris.py` on `KAMA-084-e.doc`/`f.doc`, open the resulting `.docx` and visually
  spot-check rendered Tibetan text (with a proper Tibetan Unicode font) against a few pages,
  and review the untranslatable-token log.
- Confirm `add_styles2docx.py` runs cleanly on the converter's `.docx` output with no
  unexpected style/structure issues.

## RESOLVED — 2026-09-08: ground-truth tables found, `e`/`f` converted successfully

Everything above this section is the design history of the **statistical (frequency-rank
matching)** approach, which was abandoned mid-session once it became clear it could not
resolve the `Dedris-a` consonant-stack table accurately enough (see `SESSION_LOG.md`'s
2026-09-08 entry for the full narrative). It's kept here for the record, not as current
guidance — **for how the converter actually works and how to run it now, see the README's
"Converting Dedris-Family Sambhota Files" section**, not the sections above.

**What actually solved it**: the user installed the real `udp2302.exe` (via CrossOver on this
Mac, sidestepping the need for a Windows machine) and copied its installed program directory
out to `resources/fonts/UnicDocP/`. That directory contains one `.fuf` plain-text file per
font UDP knows how to convert — its **real, authoritative keystroke→Unicode tables**, not a
guess. `build_dedris_map_from_fuf.py` parses these directly into `resources/dedris-map.json`,
completely replacing `build_dedris_map.py`'s statistical approach (deleted, along with
`make_review_doc.py` which only existed to hand-review the statistical guesses).

Two follow-up bugs found and fixed after the initial `.fuf` table build:
1. `apply_known_entries()` (from the statistical-era `KNOWN_ENTRIES` mechanism) was defined
   but never called from `main()` — a genuine bug caught mid-session, now moot since that
   whole mechanism was removed along with `build_dedris_map.py`.
2. A `.fuf` codepoints value of `FFFF` (seen exactly once, on the space keystroke in
   `Dedris-a.fuf`) means "no substitution — pass the keystroke through unchanged," not "delete
   it" — initially misread as the latter, which silently ate the conventional space that
   follows a shad (`།`) in these documents. Fixed in `build_dedris_map_from_fuf.py` (pass
   space through as itself) and in `convert_dedris.py` (a post-processing rule keeps a space
   only when it immediately follows `།` or `༈`, dropping the typist's other, purely
   decorative space keystrokes between syllables — spot-checked against the real
   `KAMA-084-a.docx` where 96%+ of real spaces follow one of those two marks).

`KAMA-084-e.doc` and `KAMA-084-f.doc` — the actual conversion targets — are now converted
cleanly with no unresolved keystrokes and correct shad-spacing, at
`workspace/fixes/kama-084-ef/out/KAMA-084-{e,f}.docx` (gitignored `workspace/`, so not in the
repo; regenerate via `convert_dedris.py` per the README if needed). Milestone insertion and
THL-style conversion for these two files are being handled separately (not by this plan/script
chain).
