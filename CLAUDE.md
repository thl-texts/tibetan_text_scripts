# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A collection of standalone Python 3 scripts and shell scripts for processing Tibetan
texts for the Tibetan & Himalayan Library (THL). The original purpose was converting
Peltsek Kama volumes from the Sambhota font to Unicode; it has since grown into a
general toolkit. There is no single application or package entry point — each script is
run directly from the command line for a specific step of the workflow.

See `README.md` for the prose description of the conversion and milestone-insertion
processes; this file captures the things that aren't obvious from the README.

## Running scripts

Scripts use `argparse` and are run directly, e.g.:

```
python insert_milestones.py -v 96 -s 8
python add_styles2docx.py -i workspace/out -a -m
python adjust_pg_nums.py -d 1 -s 12 KAMA-066-a-pgd.txt
```

Set up the environment with the virtualenv described in `README.md`:

```
python -m virtualenv venv && source venv/bin/activate && pip install -r requirements.txt
```

Key dependencies: `python-docx` (Word `.docx` manipulation), `lxml`, and the fuzzy-match
stack (`fuzzysearch`, `fuzzywuzzy`, `rapidfuzz`, `Levenshtein`). There is no test suite,
linter config, or CI — verification is done by inspecting output `.docx`/`.txt` files and
the per-run logs in `workspace/logs/`.

## Important quirks (read before editing)

- **Hard-coded paths.** Several scripts assume a fixed layout. `insert_milestones.py` and
  `add_styles2docx.py` define `HOMEDIR`/`workspace` as `./tibetan_text_scripts/...`, i.e.
  they expect to be run from the *parent* of this repo directory, not from inside it.
  `insert_milestones.py` also has an absolute `ocrfolder` pointing at a user-specific
  path on the original author's machine. Expect to adjust these when running anywhere new;
  don't assume the defaults work.
- **macOS-only steps.** Conversion relies on the macOS `textutil` command (`.doc`↔`.rtf`↔
  `.docx`↔`.txt`) and the shell scripts in `shell_scripts/`. The Sambhota→Unicode step
  itself runs on Windows via `udp.exe` (`shell_scripts/convertSamRTF.bat`).
- **In/out folder convention.** Most scripts read from a `workspace/in` folder and write to
  `workspace/out`, moving originals into a `bak/` subfolder and using `temp/` for
  intermediates. The `workspace/` tree is gitignored, as are `resources/ocr/`,
  `resources/worddocs/`, and `test/`.
- **Tibetan-specific string handling.** Code splits and trims on the tsek (`་`) and shad
  (`།`) and normalizes OCR/Unicode punctuation anomalies (e.g. `OCRVol.normalize_pairs`,
  `clean_ocr_line`). Preserve these characters exactly when editing; they are easy to
  mangle. Milestones use the format `[23.4]` (page.line) and `[23]` (page start).

## Code layout

- `process_volume.py` — orchestrator that chains `insert_milestones.py` then
  `add_styles2docx.py` for one volume, gating on the missed-milestone count parsed from the
  run's `workspace/logs/kama-vol-NNN-missed-ms.log` summary line (proceeds only if
  `count <= --threshold`). Shells out to both scripts (so they stay untouched); owns `-v`,
  `--threshold`, `-a/-m/-t`, `-n/--dry-run`, and forwards everything after `--` to
  `insert_milestones.py`. Stages `*-pgd.txt` into `workspace/stage` (not `in/`) to keep
  `in/bak` pristine, backs them up to `out/bak`, and leaves only the final `.docx` in `out/`.
  When the missed count is over `--threshold` it prints a `diagnose_log.py` report (below)
  pointing at where the run started consistently missing, then stops.
- `diagnose_log.py` — read-only analyzer for a milestone run that went over threshold. Parses
  the timestamped run log (`workspace/logs/kama-vol-NNN-<datetime>.log`, *not* the
  `-missed-ms.log` summary) into per-milestone records — header `Milestone: [p.l] (Curr pg: N,
  Curr Doc: doc)`, plus the hit (`Text chunk: …#$#$#$#…`) or miss (`!!! Milestone … not found
  (scanpg.ln) for: … !!!` + `Doc text area:`) lines that follow. Groups misses into sustained
  failure regions (small-gap tolerant, so a recovered wobble stays separate), then reports the
  first symptom and the largest region's onset: milestone page number, scan page, Word doc, the
  OCR line it sought, where the Unicode doc was stuck, and the last milestone placed before the
  drift. Run standalone: `python diagnose_log.py -v 67` (or pass a log path). NB: the header
  line is only written when insert_milestones runs with debug on (it does by default here); the
  miss lines are always written. Never modifies the log.
- `insert_milestones.py` — fuzzy-matches OCR line beginnings against converted Unicode
  chunk files to insert `[page.line]` milestones. Core logic; uses the two classes below.
  Its `-c/--clear` flag resets the workspace for a *re-run* (recoverable): clears `out/`
  and `in/temp`, clears the top level of `in/`, then restores the originals from `in/bak`
  so the conversion can run again. (To wipe everything instead, use `clear_all.py`.)
- `clear_all.py` — standalone, destructive workspace reset for starting a fresh volume:
  recursively deletes all non-hidden files in `workspace/in` and `workspace/out` (incl.
  their `bak/` and `temp/`), leaving the folder structure and hidden files (`.DS_Store`).
  Resolves `workspace` relative to its own file, so it runs from any cwd (no parent-dir
  assumption). Prompts for a capital-`Y` confirmation; `-y/--yes` skips it, `-w/--workspace`
  overrides the path. Intentionally separate from `insert_milestones.py` because it reads
  nothing and is not recoverable, unlike `-c/--clear`.
- `tibtexts/ocrvol.py` (`OCRVol`) — iterator over an OCR volume's lines, yielding cleaned
  line-beginning fragments and computing milestone numbers (handles `startat`, skipped
  blank pages, bad blanks).
- `tibtexts/univol.py` (`UniVol`) — wraps a Unicode chunk document; finds insertion points
  and writes the milestoned output.
- `add_styles2docx.py` — copies paragraphs from plain `.docx` files into the THL styled
  template (`resources/tibtext-styled-tpl-2023-09-26.docx`), optionally applying
  Annotations style (text between `«` `»`), milestone styles, and the metadata table.
- `renumber_ocr_pages.py` — renumbers the `tbocrtifs/.../out_NNNN.tif` page headers in a
  plain-text OCR volume into a clean contiguous sequence. Used after hand-fixing a stretch of
  OCR where scans were missing/repeated/misordered (splice missing pages in as marker lines
  like `first page`/`second page`, delete repeats, then renumber from a known-good start to the
  end). Treats both real tif headers and the marker lines as headers; copies the prefix/suffix/
  pad-width from the first tif header so it isn't volume-specific. Reads input read-only, writes
  a `-fixed` copy. `-s` sets the start page, `-m` adds marker strings, `-n` dry-runs. Fixing the
  OCR page numbers is the upstream fix for the drift `diagnose_log.py` surfaces, since
  `insert_milestones` keys milestone numbers off the OCR page numbers. Use this for an
  *absolute* renumber (discard the old numbers, stamp a fresh contiguous run from `-s` to EOF);
  use `adjust_ocr_pgnums.py` (below) for a *relative* shift that keeps the old numbers.
- `adjust_ocr_pgnums.py` — the OCR-header analog of `adjust_pg_nums.py`: adds `-d/--delta`
  (may be negative) to the image number of every `out_NNNN.tif` header whose current number is
  in the `[-s, -e]` range, rewriting the volume in place. Builds the file name from `-v`
  (`kama-vol-NNN.txt`) and looks it up in the OCR dir (`-p` overrides; default matches
  `insert_milestones.py`'s `ocrfolder`). The range is keyed on the headers' *existing* numbers,
  not their position, so `-s 601` means "start at the header currently numbered `out_0601.tif`";
  omit `-s`/`-e` for first/last. Unlike `renumber_ocr_pages.py` it preserves the numbers and only
  slides the selected window (intentional gaps outside the range survive), so it's for "a splice
  upstream left everything from page N off by a constant". Backs up to `-bak` (timestamped if a
  backup already exists) before writing; `-n` dry-runs; warns (doesn't block) if the shift leaves
  duplicate header numbers, and refuses a delta that would make a number negative. A header whose
  number part isn't all digits (e.g. `out_XXXX.tif`) is treated as a *placeholder* for a page
  awaiting its real number: it's skipped by the shift (so an unbounded `-s N` won't disturb it —
  no need to bound with `-e`) and reported as a reminder to rename it by hand afterward.
- `adjust_pg_nums.py` — shifts page/line milestone numbers in a range within a styled `.docx`
  (the `[p.l]` milestones, not OCR headers; `adjust_ocr_pgnums.py` is the OCR-side counterpart).
- `split_into_texts_delim.py` / `split_into_text_spread.py` — split a volume into texts on
  a delimiter (the README notes this approach is unreliable).
- Other top-level scripts (`check_for_missing.py`, `find-bad-vol-pages.py`,
  `fix_first_pages.py`, `get_page_chunk.py`, `renamefiles.py`, `reorder_pages.py`,
  `renumKamaVols.py`, `replace_docstyles.py`) — one-off utilities for cleanup/QA.
- `shell_scripts/` — `textutil` format-conversion wrappers and the Windows `.bat` for the
  Sambhota conversion.
- `resources/` — Word templates (the `.docx` template is the source of THL styles), the
  Kama catalog, and gitignored input/OCR data.

## When the template styles change

The THL style names referenced in code (`Paragraph`, `Annotations`,
`Page Number Print Edition`, `Line Number Print`, plus the `TITLE HERE` placeholder and
`Jomolhari` font) must match the styles in the template `.docx`. If the template is
updated, keep these names in sync. `README.md` documents where the canonical template
lives in Google Drive.
