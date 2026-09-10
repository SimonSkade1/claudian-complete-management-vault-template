---
name: secondary-skill-index
description: Index of rarely-needed skills/scripts — vault-cleanup (restore the projects/ folder tree, move handoffs, refresh INDEX files), check-claude-usage (Claude plan usage: 5-hour / 7-day / per-model / extra-credit utilization), and read_obsidian (read a note with `![[embeds]]` expanded).
---

# Secondary Skill Index

Procedures and scripts deliberately kept out of `.claude/skills/` so the per-message skill listing stays lean. When one matches the task, read the referenced file and follow it.

## vault-cleanup

`.claude/references/vault-cleanup.md`

Restores vault navigation: rebuilds the `projects/` folder tree from the goal tree (`parent` properties), moves handoffs into the goal folder they serve, patches path-style references the moves break, and refreshes the INDEX files and `projects/overview.md`. Read it and follow it end to end when the user asks to clean up the vault, tidy or reorganize `projects/`, fix the folder structure, or update INDEX files.

Normally runs itself: `non-markdown/run-vault-cleanup.sh`, chained from the nightly review wrapper every 2nd day. Setup docs and manual invocations: [[vault-cleanup routine]]; open ambiguities: [[vault-cleanup log]].

## check-claude-usage

`.claude/scripts/check-claude-usage.sh`

Prints Claude plan usage from the OAuth usage API (`api.anthropic.com/api/oauth/usage`): 5-hour window %, 7-day window %, per-model 7-day windows (whatever the API reports), and extra-usage credits, each with reset times. Pass `--raw` for the raw JSON.

On accounts whose setup-tokens lack the `user:profile` scope, the OAuth endpoint 403s and the script falls back to reading `anthropic-ratelimit-unified-*` headers off a 1-token haiku call — 5h/7d % + overage status only, no per-model/credit breakdown (unreachable for such tokens), costs ~1 token of that account's quota.

Per-model rows are read from `limits[]` (`kind: "weekly_scoped"`, name from `scope.model.display_name`), so new models appear without a script change; the old top-level `seven_day_opus`/`seven_day_sonnet` fields are now null and only used as a fallback. Money fields are minor units — divide by 10^`exponent`.

Run: `bash .claude/scripts/check-claude-usage.sh`. Token source priority: `$CLAUDE_CODE_OAUTH_TOKEN` env var, then `$CLAUDE_CONFIG_DIR/.credentials.json`, then `$CLAUDE_CONFIG_DIR/.oauth-token` (alt-account dirs; Claudian doesn't export the token env var to subshells), then `~/.claude/.credentials.json` (needs an active Claude Code login). Triggers: "plan usage", "how much have I used", "usage limit", "am I near my limit", "5-hour/7-day window".

## read_obsidian (expand embeds)

`python3 .claude/scripts/read_obsidian.py "<note>[#subpath]"` reads a note with `![[embeds]]` expanded. Use only when a note has embeds you need expanded, or when instructed.
