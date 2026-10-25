---
name: feedback-memory-location
description: Store this project's memories in the repo's .claude/memory/, not ~/.claude/projects/.../memory/ (travels across machines)
metadata:
  type: feedback
---

Write and update memories (and the `MEMORY.md` index) in `<repo>/.claude/memory/`, not in
`~/.claude/projects/<mangled-path>/memory/`.

**Why:** Than works on several computers against this repo and wants memory to travel with it. On
2026-10-25 he asked that everything relevant be in the repo so any machine is up to date; the 8
memories that had only existed in `~/.claude/projects/-Users-ndg8f-Sandbox-THL-Scripts-tibetan-text-scripts/memory/`
were ported here and brought current. That local folder is now stale and can be ignored.

**How to apply:** read/write `.claude/memory/` for this repo, and mirror notable session outcomes
into `SESSION_LOG.md`. He commits `.claude/` himself (see [[git-workflow-env]]).
