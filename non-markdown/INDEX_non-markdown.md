# Index — non-markdown

Scripts and non-markdown assets that don't belong to a specific project (project-specific artifacts live in the project's own folder).

Loose files at this level — only active automation plus its config:

1. Wrapper scripts (run by systemd timers or chained): `run-daily-review.sh` (nightly review; chains `run-vault-cleanup.sh` every 2nd day and `update-external-ignores.sh`), `run-claude-tasks.sh` (hourly task runner).
2. Their Claude settings: `scheduled-settings.json` (daily review), `cleanup-settings.json` (vault cleanup), `headless-task-settings.json` (task runner).

Subfolders:

3. `systemd` — user systemd units + `install.sh` for the review pipeline and the task runner (see [[claude-task-runner]], [[vault-cleanup routine]]). Linux-only; on macOS/Windows ask Claude to set up launchd / Task Scheduler equivalents for the wrappers.
4. `logs` — run logs of those timers (gitignored; created on first run).
5. `images` — loose images embedded in notes that have no project folder.
6. `audio` — loose audio, e.g. voice memos.
7. `inactive-scripts` — retired non-project scripts, kept for reference.
