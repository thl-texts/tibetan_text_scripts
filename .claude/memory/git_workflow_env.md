---
name: git-workflow-env
description: Git/gh auth state, whether Claude may push, and the auto-mode block on committing .claude/ config in this repo
metadata:
  type: reference
---

- Remote: `git@github.com:thl-texts/tibetan_text_scripts.git` (SSH), default branch `master`. PRs
  are opened with `gh pr create` (`gh` logged in as ThanGrove; if not, ask for `! gh auth login`).
- **Pushing is machine-dependent.** On Than's main Mac (set up 2026-07-16, see his global
  `~/.claude/CLAUDE.md`) Claude can `git push` via the launchd ssh-agent once he has opened one
  Terminal after a reboot. On other machines, or if `ssh-add -l` shows no identities, a
  non-interactive shell can't answer the key passphrase: don't hang on it, give him the exact
  `! git push ...` line instead. Earlier (June) he preferred pushing himself; when unsure, ask or
  hand him the command. Don't push unless asked.
- Claude Code's auto-mode classifier refuses to let Claude commit changes to `.claude/`
  (settings, hooks, memory), flagging it as "Self-Modification". Don't retry; commit other
  changes and give him the line: `! git add .claude SESSION_LOG.md CLAUDE.md && git commit && git push`.

Related: [[project-dedris-conversion]], [[feedback-memory-location]]
