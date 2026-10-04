---
name: session-log-convention
description: This repo now keeps a committed SESSION_LOG.md for cross-machine Claude session context — check and update it.
metadata: 
  node_type: memory
  type: project
  originSessionId: c8459d9a-31eb-4f32-8138-25b8a76019b4
  modified: 2026-08-17T22:18:08.025Z
---

As of 2026-08-17, the repo has a committed `SESSION_LOG.md` at its root: a running,
newest-first log of notable Claude Code sessions (fixes, decisions, in-progress work),
referenced from `CLAUDE.md`. Purpose: the user works across multiple computers, and this
file lets a Claude session on a different machine pick up context that plain git
history/diffs wouldn't carry (the "why", not just the "what").

**Why:** The user asked for a durable, repo-committed way to hand off session context
between machines, on top of (not instead of) this memory system — memory lives locally per
machine, `SESSION_LOG.md` travels with the repo.

**How to apply:** After a substantive session in this repo (a real fix, a decision, or
something left in-progress), add a dated entry to `SESSION_LOG.md` and commit it — mirror
what's saved to project memory, since the two serve different audiences (this file is
machine-local; `SESSION_LOG.md` is cross-machine/repo-visible). Skip it for trivial sessions.
See [[project-kama-pipeline-state]] for the first entry's content.
