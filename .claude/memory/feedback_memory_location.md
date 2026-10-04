---
name: feedback-memory-location
description: Store this project's memories in the repo's .claude/memory/, not ~/.claude/projects/.../memory/.
metadata:
  type: feedback
---

Write and update memories (and MEMORY.md index) in `<repo>/.claude/memory/`, not in `~/.claude/projects/-Users-thangrove-Documents-thl-catalogs-tibetan-text-scripts/memory/`.

**Why:** the user said this project has its own .claude folder and wants memories kept there (travels with the repo / across machines).
**How to apply:** read and write `.claude/memory/` for this repo. The user commits `.claude/` themselves (see [[git-workflow-env]]), so don't commit it.
