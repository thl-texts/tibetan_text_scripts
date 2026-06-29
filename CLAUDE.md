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
- `adjust_pg_nums.py` — shifts page/line milestone numbers in a range within a doc.
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
