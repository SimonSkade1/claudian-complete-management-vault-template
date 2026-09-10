---
status: note
tags:
  - automation
  - vault-infra
---
# projects-claude routine (spare weekly usage)

Spends Claude-plan usage that would otherwise expire: in the last ~18h before the weekly limit resets (shipped example values: **Wed 08:00 Europe/Berlin** — adjust to your account's reset time, see the extension's SETUP.md step 11), headless sessions work through [[projects-claude-overview]] via the vna-controller protocol. Each session runs as **fable, effort max, `--permission-mode auto`** (plus the task-runner deny rules in `non-markdown/headless-task-settings.json`).

## Schedule & budget formula

1. Four slots (example values, Europe/Berlin): **Tue 12:00, Tue 18:00, Wed 00:00, Wed 06:00** — 6h apart, last one 2h before reset.
2. Weekly-usage target per slot: `target = 99 − n·b`, n = launches still to come (3/2/1/0 → with b=12: **63 / 75 / 87 / 99%**). b = `B_5H_PCT`, the guessed weekly-% one 5h-window-limited session burns — a plain hand-tuned guess (default 12, no runtime estimation by design); adjust the env default in the wrapper as reality comes in.
3. Wrapper pre-checks usage (`check-claude-usage.sh`) and exits without launching when the 7d window is already ≥ target or the 5h window ≥ 99% — an idle fire costs ~0 tokens. A slot firing while the previous session still runs is **skipped** (flock + systemd oneshot), so after a long run the week can end below target.
4. **Session prompt** = a dynamic header (slot n, 7d usage target, 5h cap) + the template **`non-markdown/projects-claude-session-prompt.md`** sent verbatim — usage-check instructions, model policy (opus-should / fable-should / fable-must; fable-should flips to opus once fable's per-model weekly window reaches the target), wind-down rules, and the closing task sentence (*"please load the vna-controller skill and run the protocol with projects-claude-overview as your root"*). **Edit the prompt there**, not in the wrapper; this note is ops documentation only and is not read by sessions.

## Where things are

5. **Wrapper** — `non-markdown/run-projects-claude.sh` (slot detection from the configured timezone; off-window fires exit unless `TARGET_PCT` is set, so `Persistent=true` catch-ups after machine downtime can't burn to 99% mid-week; 18h `timeout` as runaway backstop; sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` — without it, headless `claude -p` kills the session after 600s of waiting on background subagent workflows, fatal for vna-controller runs).
6. **Prompt template** — `non-markdown/projects-claude-session-prompt.md` (see 4).
7. **Units** — `non-markdown/systemd/workspace-projects-claude.{service,timer}`, linked into `~/.config/systemd/user/` (the vault copies stay the source of truth; edits need `systemctl --user daemon-reload`).
8. **Logs** — `~/.local/state/projects-claude-runner/` (`run-*.log` wrapper-level, `session-*.log` full claude output) — deliberately not `non-markdown/logs/`, keeping session-log churn out of the vault and out of any sync.
9. **What it works on** — [[INDEX_projects-claude]] (conventions) + [[projects-claude-overview]] (priority list).

## Operate

10. Status: `systemctl --user list-timers workspace-projects-claude.timer`; logs: `ls -t ~/.local/state/projects-claude-runner/ | head`.
11. Dry-run (no launch, ~0 cost): `DRY_RUN=1 TARGET_PCT=63 bash non-markdown/run-projects-claude.sh` (`TARGET_PCT` needed outside the slot windows).
12. Manual real run: same without `DRY_RUN`, with an explicit `TARGET_PCT`.
13. Pause: `systemctl --user stop workspace-projects-claude.timer`; permanent: `disable`. Tune: `B_5H_PCT` / slot times in wrapper + timer, then daemon-reload.
14. Dependencies: a Claude Code login on the machine that runs it (`~/.claude/.credentials.json`), plan-billed `claude -p`; the vna-controller + handoff skills, `check-claude-usage.sh`, and the prompt template.
