#!/bin/bash
# Stop ritual: nudge Claude to write memories and refresh CLAUDE.md.
#
# Stop fires after every assistant turn, not just at "true" session end, so
# this debounces with a marker file: only fires if it's been more than 4
# hours since the last reminder, which approximates a new session/work block
# without nagging on every single turn of one continuous session.

marker="$HOME/.claude/state/tibetan-text-scripts-memory-reminder"
mkdir -p "$(dirname "$marker")"

now=$(date +%s)
last=0
[ -f "$marker" ] && last=$(cat "$marker" 2>/dev/null || echo 0)
case "$last" in ''|*[!0-9]*) last=0 ;; esac

if [ $(( now - last )) -gt 14400 ]; then
  echo "$now" > "$marker"
  cat <<'JSON'
{
  "decision": "block",
  "reason": "Session ritual: before finishing up, write any memory updates (feedback/project/user memories, per the auto-memory system) and refresh this repo's CLAUDE.md with anything learned or changed this session. Skip if nothing session-worthy happened.",
  "systemMessage": "Reminder: write memory updates + refresh CLAUDE.md before wrapping up."
}
JSON
fi
