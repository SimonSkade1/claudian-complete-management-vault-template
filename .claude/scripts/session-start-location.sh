#!/usr/bin/env bash
# SessionStart hook: tell the model which machine it is running on (the
# primary machine vs a secondary/server replica of the vault) and the key
# practical implication. Registered in .claude/settings.json under
# hooks.SessionStart; the injected text lands in the session's startup context.
#
# Single-machine setups need no changes — everything detects as "primary".
# If you mirror the vault to a server (e.g. to host the headless task runner
# there), fill in the hostname below so sessions on it know what is NOT
# available there (typically the vault's .git and external-projects/, if you
# exclude those from sync). A username fallback is included so a later
# hostname rename can't silently flip detection back to "primary".
#
# The hook command in settings.json invokes this via $CLAUDE_PROJECT_DIR —
# never an absolute path — so the same synced script serves every machine
# even when home directories differ.

set -uo pipefail

host="$(hostname 2>/dev/null || echo unknown)"
user="$(whoami 2>/dev/null || echo unknown)"

case "$host" in
  your-server-hostname) role="server" ;;   # <- replace / extend for your machines
  *) role="primary" ;;
esac
if [ "$role" = "primary" ] && [ "$user" = "your-server-username" ]; then
  role="server"
fi

# Build the JSON with python3 so escaping is always valid (jq may not be
# installed everywhere). Backticks are literal characters inside the strings.
python3 - "$role" "$host" "$user" <<'PY'
import json, sys

role, host, user = sys.argv[1], sys.argv[2], sys.argv[3]

if role == "server":
    msg = (
        f"You are running on the vault owner's server replica (host `{host}`, "
        f"user `{user}`) — almost certainly headless via automation such as the "
        "Claude task runner. If the vault's `.git` history and the "
        "`external-projects/` repos are excluded from sync to this machine, "
        "work needing them cannot be done here and must be handed back to the "
        "primary machine rather than attempted."
    )
else:
    msg = (
        f"You are running on the vault owner's primary machine (host `{host}`, "
        f"user `{user}`) — the full vault, its git history, and the "
        "`external-projects/` repos are available."
    )

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": msg,
    }
}))
PY
