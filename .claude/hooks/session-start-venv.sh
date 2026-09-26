#!/bin/bash
# SessionStart ritual: point Claude at this repo's virtualenv.
#
# NOTE: the Bash tool's shell state does not persist between commands, so a
# plain `source venv/bin/activate` here would have zero effect on later
# commands. Instead we inject a reminder telling Claude to use the venv's
# binaries directly (or chain activation within a single command).

cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Session ritual: this repo has a virtualenv at ./venv (installed from requirements.txt). The Bash tool's shell state does not persist between commands, so `source venv/bin/activate` alone will NOT carry over to later commands. For python/pip work this session, either chain it in one call (`source venv/bin/activate && <cmd>`) or invoke the venv binaries directly: ./venv/bin/python, ./venv/bin/pip."
  }
}
JSON
