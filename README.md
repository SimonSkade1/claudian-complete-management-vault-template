# Claudian complete-management vault template

An Obsidian vault template for running your work — goals, tasks, notes, and automation — with Claude Code inside Obsidian (via [Claudian](https://github.com/YishenTu/claudian)). You capture and decide; Claude plans, executes, reviews, and maintains the vault. Clone it, open it as a vault, follow [Setup](#setup) — the last setup step is telling Claude to finish the setup itself.

What you get:

1. **A goal tree with an orchestration system** (`projects/` + the VNA skills) — Claude decomposes goals into task files, executes them with fresh-context subagents, reviews every result, and keeps all program state in the notes themselves.
2. **Task management as Obsidian Bases** — `me.base` (your queue) and `claude.base` (tasks you delegate by setting one frontmatter property; a scheduled headless runner processes them hourly at zero idle cost).
3. **Automated reviews** — nightly git-snapshot commits plus a summary note of everything that changed, distilled weekly/monthly/quarterly/yearly (`auto-review/`).
4. **Automated vault cleanup** — every 2nd day Claude restores the folder structure from the goal tree, patches path references the moves break, and refreshes the INDEX files.
5. **A `.claude/` layer that makes it work** — CLAUDE.md conventions, 16 skills, workflows, scripts, and least-privilege permission profiles for the headless runs.

## Design principles

The reasons behind the structure — worth reading first, because every part below is an instance of one of these:

1. **Notes are the shared memory.** Everything both you and Claude need — goals, task state, decisions, review verdicts, open questions — lives in plain markdown files, never only in chat history. Chat context is disposable; any session (interactive or scheduled, today or next month) can pick up any thread by reading files. This is the load-bearing principle: it's what lets scheduled headless sessions, subagents, and you all work on the same state.
2. **Just enough machine-readable structure.** Two filename markers (`,` = goal, `-` = knowledge) and a handful of frontmatter properties (`status`, `parent`, `next_action_by`, `priority`, …) are the entire schema. That's enough for Bases to render live dashboards and for scripts to query the vault (`query-base.py`) — with no database, no sync, nothing that can drift from the notes.
3. **You capture, Claude maintains.** You create notes wherever convenient and never do folder structuring by hand; the scheduled cleanup rebuilds the `projects/` tree from `parent` properties, and templates auto-fill frontmatter on click-created notes. Frictionless capture beats discipline that decays.
4. **Delegation is a dial, not a switch.** Ask in chat (seconds) → write a task file and set `next_action_by:` to a model name (the hourly runner does it and hands the result back for review) → point the VNA controller at a whole goal (it plans, executes, and reviews a subtree for hours, stopping at checkpoints for your sign-off). Each notch up trades your attention for trust in review machinery.
5. **Automation is plain headless Claude, fenced in.** Every scheduled job is `claude -p` plus a wrapper script: a least-privilege settings profile per job, cheap no-token gates so idle fires cost nothing, plan-usage gates that keep the delegated-work runs inside your limits, locks against overlap, and git as the audit trail.
6. **Reviews turn git history into memory.** The nightly job commits one snapshot and writes a summary of the diff; weekly notes condense the dailies, monthly the weeklies, and so on. Both you and Claude can answer "what happened around X?" without scrolling raw history.

## The map

Top-level layout (fuller descriptions in `INDEX_workspace.md`; most folders have their own `INDEX_*.md`):

1. `projects/` — the goal tree: goal notes (`,` filename marker), knowledge notes (`-`), dashboard `overview.md`. Conventions: `projects/INDEX_projects.md`; VNA file format: `projects/-VNA task-file structure.md`.
2. `tasks-and-notes/` — flat one-off tasks and notes; their frontmatter drives the bases.
3. `me.base` / `claude.base` / `recent.base` — root dashboards: your queue, the delegated-to-Claude queue, recently modified files.
4. `posts/` — drafts, published posts, dropped posts.
5. `auto-review/` — the generated review notes (`YYYY/Qn/MM-Month/CW-ww/daily-DATE.md`, higher layers one level up each).
6. `handoffs/` — vault-general session-handoff notes; handoffs serving one goal live in that goal folder's own `handoffs/`.
7. `external-projects/` — code repos that live beside the vault but keep their own git history (auto-gitignored from the vault repo).
8. `non-markdown/` — the automation: wrapper scripts, per-job Claude settings profiles, systemd units, `logs/`.
9. `archive/` — frozen reference material, not active work.
10. `templates/` — Templater folder templates that auto-fill frontmatter (see Setup).
11. `optional-extensions/` — opt-in add-ons, each a `SETUP.md` + assets that Claude installs on request.
12. `.claude/` — CLAUDE.md, skills, scripts, workflows, references, settings (browsable inside Obsidian via the Hidden Folders Access plugin).

## The parts

### Tasks: `tasks-and-notes/` + the bases

Reason: a task system you and Claude share has to be queryable by both — so tasks are just notes with frontmatter, and the "system" is two Bases files reading it.

1. Every task/note is one file. Properties: `status` (empty, `in-progress`, `inbox`, `review`, `note`, `note-archived`, `done`, `archived`), `owner` and `next_action_by` (`me` = you; a model name = delegated), `priority` (1–10, empty sorts as 5), `not_before` (defer until a date), `project`, `subscribers`. Click-created notes get the frontmatter auto-inserted by the `templates/task.md` folder template.
2. `me.base` groups everything actionable-by-you into sections (In Progress, Inbox, Review, Do, Wait, Later, Notes …). The Review section is where delegated work comes back for your check.
3. `claude.base` lists tasks whose `next_action_by` is a model name (`opus`, `fable`, `sonnet`, `haiku`, or `claude` for the CLI default). The hourly runner (`non-markdown/run-claude-tasks.sh`) queries it in pure Python — an empty queue costs zero tokens — and otherwise launches one headless Claude per task, which writes results into the note and hands it back (`status: review`, `next_action_by: me`). Full behavior, gates, and operate commands: `tasks-and-notes/claude-task-runner.md`.

### Goals: `projects/` and the VNA orchestration

Reason: chat-sized delegation caps out fast; running a multi-day goal needs task files as durable program state, fresh-context agents per step, and reviews between steps — that's the VNA system ("von Neumann architecture": program and data live in the same medium, the notes).

1. A goal is a `,` note with `# Goal clarification` / `# Subtasks` / `# Notes` sections; subgoals link their parent via the `parent` property, and a goal with subgoals gets its own folder. `projects/overview.md` embeds every top-level goal's `# Subtasks` — one dashboard for all active frontiers.
2. To run a goal: tell Claude in a Claudian chat to load the `vna-controller` skill on the goal note. The controller decomposes it via planning workflows, spawns one executor + one reviewer per task (`.claude/workflows/vna-execute-review.mjs`), applies all state updates centrally (checkbox marks in `# Subtasks`, `status` frontmatter), and relays anything that needs you into the chat.
3. Control stays with you by construction: planners insert `checkpoint:` lines before outward-facing or hard-to-reverse steps, and the program stops there until you answer; only work independent of the answer proceeds meanwhile. Every task gets a fresh-context review; uncertain results are marked for your eyes rather than silently accepted.
4. The file format (marks like `[x]`/`[!]`/`[?]`, exceptions, verdicts) is specified in `projects/-VNA task-file structure.md` — the skills all read/write exactly that.

### Nightly reviews: `auto-review/`

Reason: with Claude editing files around the clock you need a cheap answer to "what changed and why" — so the vault's git repo exists purely for automated snapshots, and every commit gets summarized.

1. `non-markdown/run-daily-review.sh` (23:00 systemd user timer, catch-up after suspend/off days) commits one snapshot and has Claude write `auto-review/.../daily-DATE.md` from the diff; when a week/month/quarter/year just ended, the higher layer runs too, each reading only the layer below.
2. The vault git repo is the review pipeline's — the automation commits; you normally never do. Code lives in `external-projects/` precisely so its history stays out of this repo.
3. Idempotent and self-healing: a layer is skipped iff its note is already committed; killed runs are resumed by session id.

### Vault cleanup

Reason: principle 3 — you capture anywhere, structure is restored afterwards.

1. Every 2nd day (chained before the nightly snapshot), Claude rebuilds the `projects/` folder tree from the goal tree, moves handoff notes to the goal folders they serve, patches path-style references that moves break, and refreshes INDEX files and `overview.md`. Procedure: `.claude/references/vault-cleanup.md`; ops doc: `tasks-and-notes/vault-cleanup routine.md`.
2. Safe to run unattended because it's conservative: touches only parts that changed since the last run, skips files open in Obsidian or edited in the last 30 minutes, never deletes, never commits, and logs genuine ambiguities to `tasks-and-notes/vault-cleanup log.md` instead of guessing.

### Handoffs: surviving context limits

Reason: sessions die (context fills, laptops sleep); work shouldn't. The `handoff` skill has a session distill its state into a note a zero-context successor can resume from — goals and constraints quoted verbatim, current state, next steps, open questions.

1. Manual mode: Claude writes the handoff note, you start a fresh chat and point it there.
2. Relay mode: the session hands off to a fresh background session of itself (`.claude/scripts/handoff_respawn.sh`) with a hop budget, letting long autonomous work continue past any single context window. The most machine-specific part of the template — treat your first relay as a shakedown run.

### The `.claude/` layer

1. `CLAUDE.md` — the conventions above, as instructions Claude actually loads; its `## User` section is a placeholder you fill (that's part of Setup).
2. `settings.json` — fork-subagent env, `bgIsolation: none` (background sessions edit the vault in place instead of a worktree), a SessionStart hook that tells each session whether it runs on your primary machine or a server replica (`session-start-location.sh`), and a small allowlist (`read_obsidian.py`, `check-claude-usage.sh`, `handoff_respawn.sh`) so routine calls and relays don't permission-prompt.
3. Skills (16): the seven `vna-*` roles, `auto-review`, `handoff`, `obsidian-bases` (query/edit `.base` files, incl. headless via `query-base.py`), `create-or-edit-skills`, `document-chat`, `review-conversation`, `webresearch-format`, `about-me` (durable facts about you), and `secondary-skill-index` (rarely-needed procedures indexed instead of loaded — a context-cost pattern: each active skill's description costs context every message, so `.claude/references/` holds procedures and `.claude/skills-disabled/` parks whole skills).
4. `non-markdown/*-settings.json` — one least-privilege permission profile per scheduled job (review, cleanup, task runner): the cleanup profile can `mv` but not `rm` or commit; the task-runner profile keeps hard denies (sudo, credentials, …) that apply even under `--dangerously-skip-permissions`.

### Optional extensions

`optional-extensions/` holds opt-in add-ons — a `SETUP.md` (steps written for Claude to execute) plus assets each. Install one by telling Claude "set up the <name> extension". Shipped: `spare-usage-burner` — scheduled sessions that spend Claude-plan usage which would otherwise expire before the weekly reset on a `projects-claude/` tree of side-projects delegated entirely to Claude.

## A typical day

1. You jot tasks and ideas into `tasks-and-notes/` as they come up (template fills the frontmatter; set `status: inbox` or a priority if you care). You work out of `me.base`'s Do and In Progress sections.
2. Anything Claude-shaped you either ask in a Claudian chat or delegate by setting `next_action_by:` to a model name; results come back in `me.base`'s Review section.
3. Bigger goals go into `projects/` as `,` notes; when one is ripe you point the VNA controller at it and answer its checkpoints/questions when convenient — progress is visible in `projects/overview.md` and relayed in the chat.
4. At night the pipeline commits the snapshot and writes the daily review; every 2nd day cleanup restores structure first. You skim the daily/weekly notes to stay oriented.
5. When a chat gets long or you stop mid-task, you say "handoff" and continue in a fresh session from the note.

## Setup

Phase 1 is yours (installs and logins Claude can't do); phase 2 is one instruction.

1. Get the files: "Use this template" on GitHub (then clone your copy), or clone/download directly. The folder itself becomes your vault. Any location works; `~/workspace` matches the shipped scheduling units (anywhere else is a one-line path edit, see `SETUP.md`).
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and log in — Claudian requires a working local Claude Code installation. The scheduled automation assumes a subscription (Pro/Max) login: its usage gates read the plan-usage API.
3. Open the folder as a vault in Obsidian (a current version — Bases needs ≥1.9, Claudian ≥1.13) and install the **Claudian** community plugin. Recommended now, required during phase 2: also install **Templater** and **Hidden Folders Access** (Claude configures them but can't install them).
4. Open a Claudian chat and say: **"Read SETUP.md and finish the setup."** Claude then works through `SETUP.md`: git init + initial commit, plugin configuration (Templater folder templates, Bases check, `.claude/` visibility), scheduling (systemd on Linux — `non-markdown/systemd/install.sh` enables the nightly review; the hourly task runner is opt-in via two commented lines; on macOS/Windows it sets up launchd / Task Scheduler equivalents), and personalization (your `## User` section in CLAUDE.md).

## Adapting it

1. Start by filling `.claude/CLAUDE.md`'s `## User` section and pruning its communication preferences to taste — everything else works unmodified.
2. Skills you don't want: move their folder to `.claude/skills-disabled/` (keeps them out of the per-message listing) rather than deleting. New skills: the `create-or-edit-skills` skill carries the protocol.
3. Model names drift with releases: `claude.base`'s filter and the `next_action_by` values in the docs name current models (`opus`, `fable`, `sonnet`, `haiku`) — update them as generations ship.
4. The literal `me` is the hand-back owner value the system pivots on (`me.base` filters, `claude-task-helper.py`, `process-tasks.md`, `claude-task-runner.md`, the VNA structure doc) — keep it, or change all five files together.
5. This template is a snapshot (September 2026) of a live, evolving system — treat it as a starting point to reshape with your own Claude, not as an upstream that syncs.

License: MIT (the `create-or-edit-skills` skill keeps its upstream Apache-2.0 license in-folder).
