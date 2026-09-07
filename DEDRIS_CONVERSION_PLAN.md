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
