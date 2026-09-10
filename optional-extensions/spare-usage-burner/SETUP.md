# Spare-usage burner — setup

Spends Claude-plan usage that would otherwise expire: in the last ~18h before the weekly usage limit resets, scheduled headless sessions run the vna-controller protocol over a `projects-claude/` folder — lower-relevance side-projects the user delegates entirely to Claude. Usage-ceiling-gated via `.claude/scripts/check-claude-usage.sh`, so idle fires cost ~0 tokens and it stops at the configured targets.

Not installed by default. Tell Claude in this vault to "set up the spare-usage-burner extension" — the steps below are written for Claude to execute.

## What gets installed (assets/ → target)

1. `INDEX_projects-claude.md` → `projects-claude/INDEX_projects-claude.md` — folder conventions (deltas from `projects/`).
2. `projects-claude-overview.md` → `projects-claude/projects-claude-overview.md` — the priority-list dashboard sessions work from.
3. `run-projects-claude.sh` → `non-markdown/run-projects-claude.sh` — wrapper: slot detection, usage pre-check, budget target, launch. Keep it executable (`chmod +x`).
4. `projects-claude-session-prompt.md` → `non-markdown/projects-claude-session-prompt.md` — the session policy prompt (edit there, not in the wrapper).
5. `projects-claude routine.md` → `tasks-and-notes/projects-claude routine.md` — ops documentation (schedule, budget formula, operate commands).
6. `workspace-projects-claude.service` + `workspace-projects-claude.timer` → `non-markdown/systemd/` — scheduling units (Linux; see step 12).

## Install steps (for Claude)

7. Create `projects-claude/` and `projects-claude/archived/`; copy the assets to their targets as listed above.
8. Add a `projects-claude` folder line to `.claude/CLAUDE.md`'s Vault folder list and to `INDEX_workspace.md`'s Index — mirroring the `projects` lines, one sentence each: "similar to projects but lower-relevance side-projects worked mostly by Claude; conventions: `projects-claude/INDEX_projects-claude.md`, dashboard: `projects-claude-overview.md`". (This SETUP.md is the explicit instruction that CLAUDE.md's "never edit uninstructed" rule requires.)
9. If Templater folder templates are configured (core setup), add the mapping `projects-claude` → `templates/project.md` alongside the `projects` one.
10. Optional: add a gitignored free-play folder — uncomment the `projects-claude/do whatever you want …` example line in `.gitignore` and create the folder (see rule 5 in the INDEX asset).
11. Review the schedule: the shipped example values assume a weekly reset at **Wed 08:00 Europe/Berlin**, with slots Tue 12:00 / Tue 18:00 / Wed 00:00 / Wed 06:00 Europe/Berlin. Check the actual weekly reset time (`bash .claude/scripts/check-claude-usage.sh` prints it) and shift the `OnCalendar=` lines in the timer plus the slot-window logic and `Europe/Berlin` occurrences in `run-projects-claude.sh` accordingly.
12. Enable (Linux): add link/enable lines for `workspace-projects-claude.{service,timer}` to `non-markdown/systemd/install.sh` (mirroring the commented task-runner block) and run it. Non-Linux: set up a launchd / Task Scheduler equivalent invoking `non-markdown/run-projects-claude.sh` at the slot times.
13. Seed `projects-claude/projects-claude-overview.md` with 1–3 starter goals from the user (ask), or leave the list empty — sessions then wind down cheaply.

## Notes

14. Sessions run as fable, effort max, `--permission-mode auto`, constrained by the deny rules in `non-markdown/headless-task-settings.json`; budget formula and all knobs: the routine doc (asset 5).
15. Requires: a Claude Code login on the machine that runs it (plan-billed `claude -p`), the vna-controller + handoff skills (core), and `check-claude-usage.sh` (core).
