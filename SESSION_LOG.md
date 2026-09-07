# Session Log

Running log of notable Claude Code sessions in this repo, so context carries over
between machines. Newest entries first. Add a new entry when a session makes a
substantive fix, decision, or leaves something in-progress worth knowing about;
skip trivial sessions.

## 2026-09-07 — Dedris (Sambhota) → Unicode converter: design plan

Assessed and designed a pure-Python replacement for the Windows/`udp.exe` leg of
the Sambhota conversion pipeline, targeting the "Dedris" font family (Nitartha
International, 1999) used by `KAMA-084-{e,f}.doc` (not yet converted). Full
design doc: [`DEDRIS_CONVERSION_PLAN.md`](DEDRIS_CONVERSION_PLAN.md).

Key findings: (1) `workspace/in/sambhota/KAMA-084-{a,b,c,d}.doc` (Sambhota
originals) and `workspace/in/KAMA-084-{a,b,c,d}.docx` (already UDP-converted)
form a ready-made parallel corpus — the byte→Unicode mapping can be learned
empirically instead of sourced from documentation (none exists for Dedris).
(2) The scheme uses at least 8 font names (not the 2 originally assumed),
confirmed via LibreOffice headless flat-ODT export — `textutil`/Word silently
substitutes Times New Roman for uninstalled fonts and is unusable for
extraction; `soffice --headless --convert-to fodt` preserves the real
per-character font-table names. (3) Characters are typed as one interleaved
stream in reading order (base→subjoined→vowel), so this reduces to sequential
token-substitution + syllable composition, closer to a Wylie/EWTS converter
than a 2-D glyph-overlay problem.

Plan: train a mapping table on `a`–`c`, validate against held-out `d`, then
convert `e`/`f` — flagging any untranslatable token rather than guessing.
User confirmed: proceed without the missing Dedris font files for now (only
`Dedris-a`/`-a1`/`-vowa` are in `resources/fonts/`; the rest are on fontsgeek
if needed later), and build the full general tool (not just a one-off for
KAMA-084). Implementation not yet started as of this entry.

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
