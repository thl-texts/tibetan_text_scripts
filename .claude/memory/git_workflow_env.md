---
name: git-workflow-env
description: gh CLI auth state and the auto-mode block on committing .claude/ config in this repo
metadata:
  type: reference
---

- `gh` CLI was logged in (account ThanGrove, keyring) on 2026-09-26, so `gh pr create` works from Bash. If it says "gh auth login", ask the user to run `! gh auth login`.
- Repo remote: github.com:thl-texts/tibetan_text_scripts, default branch `master`.
- Claude Code's auto-mode classifier refuses to let Claude commit changes to `.claude/` (settings.json, hooks), flagging it as "Self-Modification". **How to apply:** don't retry. Commit the other changes and give the user the exact `! git add .claude/... && git commit && git push` line to run themselves. They did this on 2026-09-26, and `.claude/settings.json` and the hooks are now tracked on master.

Related: [[project-dedris-conversion]]
