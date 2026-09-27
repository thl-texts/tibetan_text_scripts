# Session Log

Running log of notable Claude Code sessions in this repo, so context carries over
between machines. Newest entries first. Add a new entry when a session makes a
substantive fix, decision, or leaves something in-progress worth knowing about;
skip trivial sessions.

## 2026-09-27 — kama-vol-084 done and posted; Dedris converter merged to master

`kama-vol-084` is finished: all five texts (`a`–`e`) run through `process_volume.py`
(`insert_milestones.py` + `add_styles2docx.py`) and posted to Teams, in the folder where
paged/styled files are stored. `KAMA-084-e.docx` had gone missing from the source input at
some point and was recreated from the OCR before this run. The run's
`kama-vol-084-missed-ms.log` shows 12 milestones not auto-inserted (`74.4`, `160.5`, `167.2`,
`293.5`, `293.6`, `334/334.1`, `406.2`, `406.5`, `406.6`, `407/407.1`, `428.2`, `429.3`) —
under the usual threshold, output was accepted without a `diagnose_log.py` deep-dive.

Also: the Dedris (Sambhota→Unicode) converter and its other accumulated updates (see
2026-09-08 entry below) are now merged to `master` via PR #8 (`4adf2ab`); the
`dedris-converter` branch is deleted, both locally and on `origin`.

## 2026-09-08 — Dedris converter: abandoned statistical guessing, found real UDP tables, `e`/`f` done

Continuation of 2026-09-07's session. Short version: the statistical (frequency-rank matching)
approach described in the next log entry down was a dead end, and got replaced entirely by
using UDP's own real conversion tables — `KAMA-084-e.doc`/`f.doc` (the actual targets) are now
converted cleanly. See `DEDRIS_CONVERSION_PLAN.md`'s "RESOLVED — 2026-09-08" section for the
technical detail; this entry is the narrative.

**The vowel-table hand-review (from the prior session) turned out not to be the real
bottleneck.** The user filled in `workspace/fixes/kama-084-ef/review/dedris-vowa-review.docx`
by eye (comparing each keystroke rendered in the actual installed `Dedris-vowa` font glyph
against the trained guess — noted several raw keys collapse to the same Unicode vowel because
Dedris drew visually distinct glyph variants for the same vowel depending on the root
consonant). Transcribing those corrections into `build_dedris_map.py`'s `KNOWN_ENTRIES` and
retraining still produced garbled, non-real Tibetan on held-out validation — because the much
bigger `Dedris-a` consonant-stack table (80.8% of every keystroke in the corpus; `Dedris-vowa`
is only 15.6%) was still just a frequency-rank guess, and that guess wasn't good enough at
that scale even though individual high-confidence entries looked plausible in isolation.
(Also found and fixed a real bug in passing: `build_dedris_map.py`'s `apply_known_entries()`
was defined but never called from `main()`, so the hand-confirmed vowel corrections weren't
actually reaching the output table at all — now moot, see below.)

**Tried OCR-based glyph recognition next** (installed `tesseract` + `tesseract-lang` via
Homebrew, rendered individual Dedris keystrokes as images with the real installed fonts, ran
Tibetan-model OCR on them). Mixed results — got structural pieces right (e.g. correctly read a
subjoined consonant) but confused visually-similar base consonants, and was size-sensitive
(different image sizes gave different answers for the same glyph), since Tesseract's Tibetan
model expects normal text lines, not isolated jumbo single glyphs. Concluded it wasn't worth
pursuing further without much more engineering (e.g. closed-set image-similarity matching
against rendered Unicode candidates, rather than open-vocabulary OCR).

**What actually worked**: the user asked about running the real `udp.exe` (the tool this whole
converter was meant to replace) on the Mac directly. Homebrew's Wine casks (`wine-stable`,
`wine@staging`, `wine@devel`) are all currently disabled (blocked 2026-09-01, fail Gatekeeper).
[CrossOver](https://www.codeweavers.com/crossover)'s free trial worked instead — the user
installed `udp2302.exe` into a CrossOver bottle, then copied the installed program directory
out to `resources/fonts/UnicDocP/`. That directory turned out to contain one `.fuf` plain-text
file per font UDP converts (`Dedris-a.fuf`, `Dedris-vowa.fuf`, etc.) — **UDP's own real
keystroke→Unicode tables**, not something to reverse-engineer or guess. Spot-checked against
every entry the user had hand-confirmed the hard way and they matched exactly.

Wrote `build_dedris_map_from_fuf.py` to parse these directly into `resources/dedris-map.json`,
completely obsoleting the statistical approach. Deleted `build_dedris_map.py` and
`make_review_doc.py` (only existed to train/review the statistical guess) and stripped the
now-unused Unicode tokenizer out of `tibtexts/dedrismap.py`. Converting `KAMA-084-d.doc`
(held out) with the new table produced genuine, grammatical Tibetan for the first time all
session — it didn't textually match the real `d.docx` verbatim, but that's expected and
explains an earlier mystery: the raw `.doc` files and their converted `.docx` counterparts
were already known not to correspond 1:1 (the `.docx` set was evidently re-chunked by title
boundaries), so `d.doc`/`d.docx` are almost certainly just different texts within the volume,
not a mismatch.

Two more real bugs found and fixed while converting the actual `e`/`f` targets: (1) a `.fuf`
codepoints value of `FFFF` (seen once, on `Dedris-a`'s space keystroke) means "pass this
keystroke through unchanged," not "delete it" — misread as the latter at first, which silently
dropped the space that conventionally follows a shad (`།`) in these documents; (2) even after
fixing that, *every* space was being kept (including the typist's purely decorative spaces
between syllables), because the raw docs use the same space keystroke for both purposes.
Fixed with a post-processing rule in `convert_dedris.py`: keep a space only when it
immediately follows `།` or `༈`, drop it otherwise — spot-checked against the real
`KAMA-084-a.docx`, where 96%+ of actual spaces there follow one of those two marks.

**End state**: `KAMA-084-e.doc`/`f.doc` converted cleanly, no unresolved keystrokes, correct
shad-spacing, at `workspace/fixes/kama-084-ef/out/KAMA-084-{e,f}.docx` (gitignored, not in the
repo). `resources/fonts/` and `resources/old/` added to `.gitignore` and untracked from git
(third-party/legacy files, not meant to be redistributed in this repo) — `resources/fonts/`
specifically now holds `udp2302.exe` and the unpacked `UnicDocP/` directory needed to
regenerate `resources/dedris-map.json` from scratch on a new machine (see README for the
regeneration steps, since these files aren't in the repo). The user is handling milestone
insertion and THL-style conversion for `e`/`f` separately. New README section: "Converting
Dedris-Family Sambhota Files (Pure-Python, No Windows Needed)".

**Takeaway for next session**: when a from-scratch reverse-engineering effort (statistical
guessing, then OCR) is fighting hard for marginal accuracy gains, it's worth checking whether
the *original* proprietary tool can just be run directly (even via a compatibility layer like
CrossOver) before investing further in the from-scratch approach — the real tables were sitting
in a plain-text, trivially-parseable format the whole time, just inside a Windows install we
hadn't run yet.

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
