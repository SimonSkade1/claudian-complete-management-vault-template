# Setup

Finishing the vault setup after the user has done the manual phase (README → Setup): cloned the template as their vault, installed Claude Code + logged in, opened the vault in Obsidian, installed the Claudian plugin (plus, ideally, Templater and Hidden Folders Access). The user triggers this by telling Claude in a Claudian chat: **"Read SETUP.md and finish the setup."** The steps below are written for Claude to execute; do them in order, report what you did, what you skipped, and anything that failed. Ask instead of improvising when a check fails.

## Preflight

1. Confirm the working directory is the vault root: `README.md`, `SETUP.md`, and `.claude/` are present here.
2. Check the dependencies the automation needs, and report any that are missing (with the install command for the user's platform):
   1. `git --version`
   2. `python3 --version` (3.8+) and `python3 -c "import yaml"` — PyYAML is needed by `.claude/scripts/query-base.py`; if missing: `pip3 install --user pyyaml` or the distro package (e.g. `python3-yaml`).
   3. `uuidgen` and `flock` (used by the wrapper scripts; part of util-linux on Linux — on macOS `flock` may be absent, note it: the wrappers then need a small edit or a `flock` port before scheduling them).
3. `ls .obsidian/ 2>/dev/null` — if `.obsidian/` doesn't exist, the folder hasn't been opened in Obsidian yet; plugin steps 7–10 will have nothing to configure. Do the git steps, then ask the user to do the Obsidian part of phase 1 first and re-invoke this doc.

## Git — the review pipeline's backbone

The nightly review pipeline snapshots the vault as git commits and refuses to run without a repo; cleanup uses git history to scope its runs. This git repo is the automation's — after setup, the nightly job commits; the user normally never does.

4. If `git rev-parse --git-dir` fails: `git init -b main`.
5. Ensure a commit identity exists (`git config user.name` and `git config user.email`, local or global). If either is empty, ask the user what to set and set it repo-locally. Note to the user: the email lands in every commit of this (local, private) repo; a GitHub noreply address is fine if they might ever publish it.
6. Initial commit if the repo has no commits yet: `git add -A && git commit -m "Initial vault snapshot"`.

## Obsidian plugins — config Claude writes, installs the user does

Claude cannot install community plugins (Obsidian downloads them), but their settings are plain JSON files Claude can write. Plugin configs are read at plugin load, so a reload (step 10) applies them.

7. Check installs: `.obsidian/community-plugins.json` should list `templater-obsidian` and `hidden-folders-access` (and Claudian, or this chat wouldn't exist). For any missing one, ask the user to install + enable it (Settings → Community plugins) and continue with the rest meanwhile.
8. Templater — this is what auto-fills frontmatter on notes created empty in the two task folders. Merge into `.obsidian/plugins/templater-obsidian/data.json` (create the file if absent; preserve any existing keys):
   ```json
   {
     "templates_folder": "templates",
     "trigger_on_file_creation": true,
     "folder_templates": [
       { "folder": "tasks-and-notes", "template": "templates/task.md" },
       { "folder": "projects", "template": "templates/project.md" }
     ]
   }
   ```
9. Hidden Folders Access — makes `.claude/` browsable inside Obsidian. Merge into `.obsidian/plugins/hidden-folders-access/data.json`:
   ```json
   {
     "enabledFolders": [".claude"],
     "allowedExtensions": ["md", "py", "sh", "js", "mjs", "json", "yaml", "yml", "txt", "html", "css", "base"]
   }
   ```
10. Core **Bases** plugin (renders the three root `.base` dashboards): if `.obsidian/core-plugins.json` exists and contains `"bases": false`, set it to `true`. If the file is absent or lacks the key, change nothing — current Obsidian ships Bases enabled by default; just have the user confirm under Settings → Core plugins in step 11.
11. Ask the user to reload Obsidian (command palette → "Reload app without saving") and confirm: `me.base` renders as a table, and `.claude/` shows in the file explorer.

## Scheduling — laptop-local

Two scheduled jobs ship: the nightly review pipeline (23:00, self-catching-up after suspend/off days; runs cleanup every 2nd day) and the optional hourly task runner. Both are wrapper scripts in `non-markdown/`; scheduling is just invoking them.

12. Linux (systemd user units, the shipped path): the units in `non-markdown/systemd/` point at `%h/workspace` — if the vault root is not `~/workspace`, first edit every `%h/workspace` path in both `.service` files — `ExecStart=` in each, plus `WorkingDirectory=` in `workspace-process-tasks.service` (a header comment marks the lines; edit the vault copies — they stay the single source of truth, `install.sh` links them). Then run `bash non-markdown/systemd/install.sh`. It enables only the nightly review; the hourly task runner is opt-in — uncomment its two lines in `install.sh` and rerun once the user wants delegated-task processing.
13. macOS / Windows: no systemd — set up the equivalent for the user's platform (launchd plist / Task Scheduler job): nightly `non-markdown/run-daily-review.sh`, hourly `non-markdown/run-claude-tasks.sh` (optional, see step 12). Same opt-in logic: skip the task runner until asked.
14. Verify without spending tokens (if any command prints "this workspace has not been trusted", Claude Code's trust dialog hasn't been accepted for this folder yet — permission allowlists are ignored until then; run `claude` once interactively in the vault root and accept it, then re-check):
   1. `DR_COMPUTE_ONLY=1 bash non-markdown/run-daily-review.sh` — prints the computed review-period ends.
   2. `VC_GATE_ONLY=1 bash non-markdown/run-vault-cleanup.sh` — prints the cleanup cadence-gate decision (first run: `LAST_RUN=none`).
   3. `bash .claude/scripts/check-claude-usage.sh` — prints plan usage (needs the subscription login; this is the gate that keeps scheduled runs inside plan limits).
   4. On systemd: `systemctl --user list-timers daily-review.timer` shows the next fire time.

## Personalize

15. Ask the user for a few lines about themselves — name, what they're working toward, background per field (so Claude can skip basics) — and replace the placeholder `## User` section in `.claude/CLAUDE.md` with it. (CLAUDE.md's never-edit-uninstructed rule is satisfied: this step is the explicit instruction.) Longer-lived setup facts (machine, sync, plan tier) go into `.claude/skills/about-me/SKILL.md` — seed it with whatever came up during this setup.
16. Smoke-test the capture flow with the user: create a new note in `tasks-and-notes/` via Obsidian (click-create) and confirm the frontmatter appears; set `status: inbox` and watch it show up in `me.base`'s Inbox view; delete the test note.

## Wrap up

17. Final checks, report pass/fail per line:
   1. `python3 .claude/scripts/read_obsidian.py "projects/overview.md"` — embed expansion works.
   2. `python3 .claude/scripts/query-base.py me.base` — base parsing works (lists the views).
   3. `bash .claude/scripts/session-start-location.sh` — emits valid JSON (the SessionStart hook; says which machine role this session runs under).
18. Commit the setup: `git add -A && git commit -m "Vault setup"`.
19. Tell the user where to go next: `SYSTEM.md` for how the system is organized; `optional-extensions/` for add-ons (installed the same way: "set up the <name> extension"); delegation needs the task runner enabled (step 12/13). If they later mirror the vault to a server, `.claude/scripts/session-start-location.sh` has the hostname slots to fill.
