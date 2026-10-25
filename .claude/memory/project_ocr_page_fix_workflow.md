---
name: project-ocr-page-fix-workflow
description: Fixing OCR page-number drift (missing/repeated scans) with renumber_ocr_pages.py / adjust_ocr_pgnums.py, then rerunning via -c
metadata:
  type: project
---

When a volume fails with a huge missed-milestone count, the usual root cause is the **OCR file**,
not the matcher: a scan went missing, repeated, or out of order, so the `out_NNNN.tif` headers no
longer line up. `insert_milestones` derives milestone numbers from them, so everything after the
slip drifts ([[project-diagnose-log]] locates it).

**Workflow (validated on KAMA-067):**
1. `diagnose_log.py` points at the collapse.
2. Fix the OCR stretch by hand: splice missing pages in (placeholder header lines like
   `first page`, or `out_XXXX.tif`/`out_0999.tif`), delete repeats.
3. Renumber: `renumber_ocr_pages.py` = *absolute* (stamp a fresh contiguous run from `-s` to EOF,
   writes a `-fixed` copy); `adjust_ocr_pgnums.py` = *relative* (`-d` delta on headers in `[-s,-e]`,
   in place, backs up to `-bak`, `-n` dry-run; non-numeric placeholder headers are skipped and
   reported).
4. Put the corrected text in the OCR file `insert_milestones` reads:
   `./tibetan_text_scripts/resources/ocr/kama-vol-NNN.txt` (`ocrfolder`, `insert_milestones.py:25`;
   it was an absolute `ocr-plain` path in June, changed to `resources/ocr` in commit 2951d4a). That
   dir is gitignored, so its location and contents differ per computer: verify where the OCR files
   actually are on the current machine before editing or rerunning.
5. Rerun from the repo's PARENT dir with `-c` forwarded (restores originals from `workspace/in/bak`):
   `python tibetan_text_scripts/process_volume.py -v 67 --threshold 25 -a -m -- -s 4 -c`
   (answer `Y` to the reset prompt). KAMA-067 start page is `-s 4`.

KAMA-067 had a duplicate scan (`out_0078`/`0079`) that caused the [74.1] collapse; fixed, and the
rerun missed only 5. Related: [[project-process-volume-orchestrator]].
