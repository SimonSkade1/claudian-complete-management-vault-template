---
status: note
tags:
  - automation
  - vault-infra
  - tasks
---

# Claude task runner (headless)

Tasks in `tasks-and-notes/` delegated by setting frontmatter `next_action_by` to a model name get processed autonomously: **one claude instance per task**, **model chosen per task** from `next_action_by`, and **zero-cost idle runs** (the queue is checked in Python; claude only launches when there is work). Runs on the machine of your choice via a systemd user timer (or any scheduler) — usually your own machine; a server replica of the vault works too.

## Delegating a task

1. Set `next_action_by:` to `opus`, `fable`, `sonnet`, `haiku` (model choice), or `claude` (CLI default model). These are the model names current as of September 2026 — they drift with releases; when a new generation ships, update both the values you use and the filter list in [[claude.base]].
2. Status must be empty, `active`, or `inbox`; `not_before` empty or ≤ today.
3. Instructions go in the note body; the filename alone is often enough.
4. Claude writes results into the note, adds a `## Done by claude (<model>, date)` summary, sets `status: review` + `next_action_by: me`. The hand-back lands in me.base's Review section.

## Components

1. [[claude.base]] — queue definition + dashboard (views: Do, Later). Single source of truth for what's eligible.
2. `.claude/references/process-tasks.md` — the per-task protocol (a plain reference file rather than a skill, to keep the skill listing lean). Manual: tell Claude to read it and process the queue (or one task path).
3. `.claude/scripts/query-base.py` — `--paths` flag prints a view's file paths without needing the Obsidian app running.
4. `.claude/scripts/claude-task-helper.py` — `gate` (plan-usage check via OAuth usage API, fails closed), `get` (frontmatter read), `mark-failed` (hand-back on failed runs).
5. `non-markdown/run-claude-tasks.sh` — the runner loop (flock, queue, gate, launch, failure guard).
6. `non-markdown/headless-task-settings.json` — deny rules that still apply under `--dangerously-skip-permissions` (sudo, shutdown, mkfs, dd, crontab, reading credentials).
7. `non-markdown/systemd/workspace-process-tasks.{service,timer}` — hourly at :15, `Persistent=true`. Linked into `~/.config/systemd/user/` via `systemctl --user link`, so the vault copies stay the source of truth and edits only need `systemctl --user daemon-reload`.

## Behavior

1. Hourly, the runner queries the Do queue (pure Python — no tokens). Empty queue → exits silently, no log.
2. Per task, serially: usage gate → launch `claude -p --dangerously-skip-permissions --model <next_action_by> --effort max "Read .claude/references/process-tasks.md and follow it for exactly this task: <path>"` (no `--effort` for haiku; no `--model` for `claude`), 60 min timeout.
3. **Usage gate** (before every task, model-aware): blocks when 5h window ≥ 70%, 7d ≥ 85%, or the model's 7d bucket ≥ 80%. Gate failure stops the whole run; next hourly fire retries. Thresholds: env vars `MAX_5H`, `MAX_7D`, `MAX_7D_MODEL`.
4. **Failure guard:** if a task is still in the queue after its run (crash, timeout, usage cutoff mid-run), the runner sets `status: review`, `next_action_by: me` and inserts a warning callout — no infinite retries.
5. Logs: `~/.local/state/claude-task-runner/` (`run-*.log` + one `task-*.log` per task).
6. Overlap-safe: flock + systemd oneshot (a still-running run makes the next timer fire a no-op).

## Operate

1. Enable: uncomment the task-runner lines in `non-markdown/systemd/install.sh` and run it (Linux). On macOS/Windows: no systemd — ask Claude to set up a launchd / Task Scheduler equivalent invoking `non-markdown/run-claude-tasks.sh`.
2. Manual run: `MAX_TASKS_PER_RUN=1 bash non-markdown/run-claude-tasks.sh`
3. Status: `systemctl --user list-timers workspace-process-tasks.timer`; logs: `ls -t ~/.local/state/claude-task-runner/ | head`
4. Pause: `systemctl --user stop workspace-process-tasks.timer` (disable/enable for permanent).
5. Cadence/thresholds: edit the timer unit / the env defaults in `run-claude-tasks.sh`, then `systemctl --user daemon-reload`.
6. Dependency: a Claude Code login on the machine that runs it (`~/.claude/.credentials.json`). `claude -p` is plan-billed; the usage gate keeps scheduled runs within plan limits.
7. If the runner machine is a vault replica missing some resources (the vault `.git`, `external-projects/` repos), the protocol tells Claude to hand such tasks back with a note instead of half-doing them.
