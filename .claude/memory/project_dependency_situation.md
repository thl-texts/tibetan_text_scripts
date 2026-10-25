---
name: project-dependency-situation
description: Old pinned deps don't build on Python 3.14; requirements.txt loosened, requirements-lock.txt has known-good versions
metadata:
  type: project
---

On Python 3.14 the original exact pins (`lxml==4.9.2`, `Levenshtein==0.20.9`) fail to compile. Since
2026-06-27 `requirements.txt` uses `>=` floors and `requirements-lock.txt` records known-working
versions (lxml 6.1.1, Levenshtein 0.27.3, python-docx 1.2.0, fuzzysearch 0.8.1, rapidfuzz 3.14.5);
`six` was dropped. `venv/` is gitignored; a SessionStart hook (`.claude/hooks/session-start-venv.sh`)
sets up the venv ritual.

The full pipeline has since run on real volumes (066, 067, 084, 091, 122) with no regression from
the python-docx 0.8→1.2 upgrade, so the new versions are validated for this workflow.
