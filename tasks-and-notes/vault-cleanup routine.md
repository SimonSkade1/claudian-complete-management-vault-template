---
status: note
---
# Vault cleanup routine

Restores vault navigation: rebuilds the `projects/` folder tree from the goal tree (`parent` properties), moves handoffs to the goal folder they serve, patches path-style references the moves break, and refreshes the INDEX files and [[overview]]. The user does no folder structuring by hand — this is what puts it back.

## Where things are

1. **Procedure** — `.claude/references/vault-cleanup.md`. A plain reference file rather than a skill, so it costs no context until something reads it. Point a session at it to run a cleanup by hand. Also indexed in the `secondary-skill-index` skill, which is how Claude finds it unprompted.
2. **Conventions it enforces** — [[INDEX_projects]] (folder-structure rule, note types, frontmatter) and [[INDEX_workspace]] (recursive INDEX policy). These are the spec and yours to change; the skill reads them at each run.
3. **Wrapper** — `non-markdown/run-vault-cleanup.sh`. Headless runner: cadence gate, lock, retry-by-resume.
4. **Permissions** — `non-markdown/cleanup-settings.json`. Least-privilege set for scheduled runs: adds `mv`/`rmdir` to the standard scheduled allowlist, denies `rm` and all committing git subcommands.
5. **Open ambiguities** — [[vault-cleanup log]]. Also carries `last_run` in frontmatter, which is the cadence gate's state.
6. **Raw run output** — `non-markdown/logs/vault-cleanup-*.log` (gitignored).

## How it runs

Chained from `run-daily-review.sh` immediately before that script stages the nightly snapshot, so any moves land in the same commit and the daily review note describes them. Fires at most every 2 days, gated on `last_run` in the log note's frontmatter rather than day-parity — self-healing after the laptop is off, and it can't double-run. A failed cleanup is non-fatal; the review proceeds.

It never commits (the daily review owns the commit cadence) and never deletes.

Two guards keep it from clobbering live work: it skips notes open in an Obsidian tab (`.obsidian/workspace.json`) or touched in the last 30 minutes, and it leaves code/model directories alone. Anything it can't resolve — a `parent` that contradicts its folder, a note that could serve several goals — becomes a log entry instead of a guess.

## Manual use

```bash
VC_FORCE=1 non-markdown/run-vault-cleanup.sh    # ignore the cadence gate
VC_GATE_ONLY=1 non-markdown/run-vault-cleanup.sh # report the gate decision, run nothing
CADENCE_DAYS=4 non-markdown/run-vault-cleanup.sh # override the interval
```

Or in a session: "clean up the vault" — or point at `.claude/references/vault-cleanup.md` directly. Same procedure, with you watching.

Run it on the machine where the vault's git history and the Obsidian app live — it needs `.git` for its scope signal and `.obsidian/workspace.json` for the open-file guard. If you mirror the vault to other machines (where those are typically absent), schedule it only on the primary one.
