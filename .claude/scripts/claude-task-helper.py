#!/usr/bin/env python3
"""Helpers for the headless Claude task runner (non-markdown/run-claude-tasks.sh).

Subcommands:
    gate <model> [--max-5h N] [--max-7d N] [--max-7d-model N]
        Check Claude plan usage (OAuth usage API, credentials from
        ~/.claude/.credentials.json). Prints "OK ..." and exits 0 if there is
        headroom to launch a task on <model>; prints "BLOCK <reason>" and
        exits 1 otherwise. Fails closed (BLOCK) on API/credential errors.

    get <task-path> <frontmatter-key>
        Print the frontmatter value (lowercased, trimmed) or "".

    mark-failed <task-path> <detail>
        Hand a task back to the user after a failed headless run: set
        status: review, next_action_by: me, and insert a warning line
        below the frontmatter. Prevents infinite retry loops.
"""

import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

CREDS = Path.home() / ".claude" / ".credentials.json"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"


def read_frontmatter(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    return text, m


def cmd_get(path, key):
    _, m = read_frontmatter(path)
    if m:
        fm = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", m.group(1), re.M)
        if fm:
            print(fm.group(1).strip().strip("\"'").lower())
            return
    print("")


def cmd_gate(argv):
    model = argv[0]
    opts = {"--max-5h": 70.0, "--max-7d": 85.0, "--max-7d-model": 80.0}
    for i, a in enumerate(argv):
        if a in opts and i + 1 < len(argv):
            opts[a] = float(argv[i + 1])
    try:
        token = json.loads(CREDS.read_text())["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request(USAGE_URL, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "anthropic-beta": "oauth-2025-04-20",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except Exception as e:  # fail closed
        print(f"BLOCK usage check failed: {e}")
        sys.exit(1)

    def util(key):
        return (d.get(key) or {}).get("utilization")

    checks = [
        ("five_hour", util("five_hour"), opts["--max-5h"]),
        ("seven_day", util("seven_day"), opts["--max-7d"]),
    ]
    if model == "opus":
        checks.append(("seven_day_opus", util("seven_day_opus"), opts["--max-7d-model"]))
    if model == "sonnet":
        checks.append(("seven_day_sonnet", util("seven_day_sonnet"), opts["--max-7d-model"]))

    for name, v, cap in checks:
        if v is not None and v >= cap:
            print(f"BLOCK {name} at {v:.1f}% >= {cap:.0f}%")
            sys.exit(1)
    print("OK " + ", ".join(
        f"{n}={'n/a' if v is None else f'{v:.1f}%'}" for n, v, _ in checks))


def set_fm_value(fm_text, key, value):
    """Set key: value in a frontmatter block, appending the key if absent."""
    pattern = rf"^{re.escape(key)}:[ \t]*.*$"
    if re.search(pattern, fm_text, re.M):
        return re.sub(pattern, f"{key}: {value}", fm_text, count=1, flags=re.M)
    return fm_text + f"\n{key}: {value}"


def cmd_mark_failed(path, detail):
    text, m = read_frontmatter(path)
    warning = (f"> [!warning] Headless run did not complete this task "
               f"({date.today().isoformat()}, {detail}). Handed back unprocessed.\n")
    if m:
        fm = m.group(1)
        fm = set_fm_value(fm, "status", "review")
        fm = set_fm_value(fm, "next_action_by", "me")
        new = f"---\n{fm}\n---\n{warning}" + text[m.end():]
    else:
        new = f"---\nstatus: review\nnext_action_by: me\n---\n{warning}" + text
    Path(path).write_text(new, encoding="utf-8")
    print(f"marked failed: {path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "get" and len(rest) == 2:
        cmd_get(*rest)
    elif cmd == "gate" and rest:
        cmd_gate(rest)
    elif cmd == "mark-failed" and len(rest) == 2:
        cmd_mark_failed(*rest)
    else:
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
