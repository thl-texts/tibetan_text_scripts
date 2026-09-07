# Session Log

Running log of notable Claude Code sessions in this repo, so context carries over
between machines. Newest entries first. Add a new entry when a session makes a
substantive fix, decision, or leaves something in-progress worth knowing about;
skip trivial sessions.

## 2026-09-07 — Dedris (Sambhota) → Unicode converter: built, validated, needs vowel fixes

Built a pure-Python replacement for the Windows/`udp.exe` leg of the Sambhota
conversion pipeline, targeting the "Dedris" font family (Nitartha
International, 1999) used by `KAMA-084-{e,f}.doc` (not yet converted). Full
design doc, kept up to date with everything below:
[`DEDRIS_CONVERSION_PLAN.md`](DEDRIS_CONVERSION_PLAN.md) — **read its "STATUS"
section first when resuming this work**, it has the fullest detail.

**What's built and committed** (`a754dbd`, `dd5b13e`, `4f1ff22`):
- `tibtexts/fodtdoc.py` (`FodtDoc`) — extracts a per-character `(font_name,
  char)` stream from a legacy `.doc` via LibreOffice headless flat-ODT export
  (`soffice --headless --convert-to fodt`). Required because `textutil`/Word
  silently substitutes a generic font for anything not installed locally,
  destroying the font-switch signal the whole approach depends on. Fixed one
  real bug this session: the scratch LibreOffice profile/output dir must use
  **absolute paths**, or a bad `file://` URI makes `soffice` hang forever
  rather than error (only showed up converting a larger file).
- `tibtexts/dedrismap.py` (`DedrisMap`, `tokenize_unicode`) — the persisted
  lookup table (font/char → Unicode string) plus a regex tokenizer that
  segments already-Unicode Tibetan text into STACK/VOWEL/OTHER tokens
  comparable to a Dedris keystroke.
- `build_dedris_map.py` — trains the table. `convert_dedris.py` — applies it,
  marking unresolved keystrokes inline (`<<font:char>>`) rather than guessing.

**Major discovery that changed the approach mid-session**: the original plan
assumed `workspace/in/sambhota/KAMA-084-{a,b,c,d}.doc` (Sambhota originals)
line up 1:1 by letter with `workspace/in/KAMA-084-{a,b,c,d}.docx` (already
converted) — a ready-made parallel corpus for positional alignment. Measuring
actual character/tsek counts showed this is **false** (e.g. `-a.doc` has
~35,700 raw keystrokes vs. `-a.docx`'s ~114,000 Unicode chars — the converted
set was evidently re-chunked by text/title boundaries, not the typist's file
split), though the *aggregate* totals across the whole corpus line up well
(~8% expansion, right where real conversion should land). Pivoted to
**frequency-rank matching** instead (classic substitution-cipher approach):
match raw `(font, char)` keystroke counts against Unicode token counts by
rank/nearest-expected-count, anchored on tsek, rather than positionally
aligning specific documents.

**Encoding model correction** (from the user, who designed this font family):
a single Dedris keystroke represents a whole pre-rendered consonant stack (2+
Tibetan letters as one glyph), not one letter — so conversion is resolve-each-
keystroke-independently-then-concatenate, no generic base/subjoined/vowel
reordering assembler needed. Simpler than originally planned.

**Held-out validation result (train on Unicode={a,b,c}, convert held-out
`d.doc`, diff against real `d.docx`): the frequency-only table is not accurate
enough alone** — individual high-confidence entries looked like plausible
Tibetan consonant clusters (`སྐྱ`, `རྒྱ`, `སྦྱ`, etc. all correct), but the full
converted text came out garbled. Manually decoding a raw sample through the
table suggested consonant-stack entries are largely right, but `Dedris-vowa`
(vowel) entries are the weak point — small vocabulary (~29 keys) but lower
confidence, and a vowel appears in nearly every syllable so a few wrong
entries corrupt most of the output.

**Vowel corrections confirmed with the user this session** (also caught one
purely structural error myself: exactly 4 basic Tibetan vowels should occupy
the 4 highest-frequency `Dedris-vowa` keys, and the trained table only had 3
right):
- Key `'J'`: trained as literal space (wrong) → **confirmed: short-i, U+0F72
  (ི)**.
- Key `'R'`: trained as plain short-u (wrong) → **confirmed: long-u, achung +
  zhabkyu, U+0F71 U+0F75 (ཱུ, e.g. ཀཱུ)** — some vowel keys are
  achung-prefixed compounds, not bare single codepoints.
- Keys `'A'` (guessed plain-o) and `','` (guessed plain-e) — **not yet
  confirmed**; given the long-u pattern just found, check whether these are
  also achung-prefixed long forms rather than the plain short forms guessed.
- The other ~25 low-frequency `Dedris-vowa` entries haven't been reviewed at
  all.

**User feedback on review format (apply going forward)**: the terminal's
multiple-choice question UI garbles/overwrites itself when the choices
contain Tibetan text. For any future review-with-the-user step involving
Tibetan strings, **create an RTF or LibreOffice/Word document with a table**
(one column showing the Dedris key + current guess, one blank column for the
user to type the correct Tibetan into) instead of using inline chat questions
or the multiple-choice question tool.

**Next steps for a resumed session** (see the plan doc's STATUS section for
the fuller list): get the user's confirmation on the remaining `Dedris-vowa`
entries (ideally via the table-document format above, not chat); patch or
override the trained table with confirmed values; actually write the trained
table to the real `resources/dedris-map.json` (every run so far used `/tmp`
test paths — nothing has been written to that path for real yet); re-run the
held-out validation and this time compute an actual accuracy number
(`python-Levenshtein`-based, as originally planned — not implemented yet);
only then retrain on the full `a-d` set and convert `e`/`f`.

**Cleanup**: `workspace/in/sambhota-train/` and `workspace/in/train-unicode/`
(gitignored copies made for the held-out test) can be deleted; `/tmp/dedris-*`
paths used during testing are ephemeral and won't survive a restart.

## 2026-08-17 — ocrfolder finalized, SESSION_LOG.md added, clear_all.py covers stage/

Follow-on to the session below, same day.

- **`insert_milestones.py`**: `ocrfolder` settled on a relative path,
  `./tibetan_text_scripts/workspace/ocr`, matching the `workspace =
  './tibetan_text_scripts/workspace'` convention right above it (superseding
  the absolute-path version from the prior entry). Committed as `ff07857`.

- Added this file (`SESSION_LOG.md`) and pointed to it from `CLAUDE.md`, so a
  Claude session on another of the user's machines can pick up prior-session
  context. Committed as `8ad8b17`.

- **`clear_all.py`** only cleared `workspace/in` and `workspace/out`, missing
  `workspace/stage` — the directory `process_volume.py` uses to stage
  milestoned `*-pgd.txt` files between its two pipeline steps (see
  `CLAUDE.md`'s description of `process_volume.py`). A fresh-volume clear was
  leaving stale `stage/bak` files behind from the previous volume. Updated
  `delete_files_in`/`clear_all()` to also recurse into `stage`, and updated the
  docstring, confirmation prompt, and `CLAUDE.md`'s description to match.
  Verified with a live run (cleared 12 leftover files from vol-068's stage/bak).
  Committed as `2d4f54f`.

- All three pushed to `origin/master`.

## 2026-08-17 — Hidden page milestones, Jomolhari-ID font leak, ocrfolder path

Working volume: `kama-vol-068`, run via `process_volume.py` for the first time on
this machine (previously only run manually step-by-step / by Claude on another
computer).

- **`insert_milestones.py`**: updated the hard-coded `ocrfolder` path (see
  `CLAUDE.md` "Important quirks") from the original author's old machine
  (`/Users/ndg8f/...`) to this machine's actual path
  (`/Users/thangrove/Documents/thl/catalogs/tibetan_text_scripts/workspace/ocr`).
  Still a hard-coded absolute path — expect to redo this on any new machine.

- **Bug: page-number milestones (`[23]`) appeared missing from styled docx
  output.** Root cause was *not* in `insert_milestones.py` or
  `add_styles2docx.py` — both were correctly inserting `[pg][pg.line]` and
  applying the `Page Number Print Edition` / `Line Number Print` styles. The
  template's `Page Number Print Edition` character style had **hidden text**
  turned on (`font.hidden = True`), so Word just didn't display it. Fixed by
  clearing the hidden flag on that style in
  `resources/tibtext-styled-tpl-2023-09-26.docx` (all other formatting on the
  style, e.g. purple color, left untouched).

- **Bug: Tibetan text still rendered in Jomolhari-ID instead of Jomolhari**,
  even after a prior session's template edit that set the `Paragraph` style's
  `cs` (complex-script) font to Jomolhari. Root cause: `set_tib_font()` in
  `add_styles2docx.py` set `r.font.name = "Jomolhari"`, but python-docx's
  `Font.name` setter only writes `rFonts@ascii`/`@hAnsi` — never `@cs`. Word
  renders Tibetan from the complex-script (`cs`) font slot, so runs kept
  falling back to whatever `cs` was inherited (previously `Jomolhari-ID` from
  docDefaults/style). Fixed by explicitly setting `w:rFonts/@w:cs="Jomolhari"`
  on every run via direct XML manipulation, so it no longer depends on style
  inheritance.

- Regenerated `workspace/out/KAMA-068-*.docx` from the staged `-pgd.txt` files
  (in `workspace/stage/bak`, gitignored) using the fixed template/script and
  spot-verified both fixes in the actual run XML.

- Committed as `237f27c` (ocrfolder path) and `84a5531` (hidden style + font
  fix), pushed to `origin/master`.

**Takeaway for next session**: when a styled-docx output looks wrong (missing
element, wrong font), check whether the *template* or *script* is at fault
before assuming insertion logic is broken — both bugs this session were
template/styling issues, not the milestone-insertion logic itself. Also
remember that already-generated `.docx` files embed their own copy of the
template's styles at creation time, so fixing the template doesn't retroactively
fix docs already produced — they need regenerating.
