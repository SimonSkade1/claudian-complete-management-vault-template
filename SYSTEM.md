# The system

How this vault template is organized. The structure is plain Obsidian — markdown files, a little frontmatter, [Bases](https://help.obsidian.md/bases) dashboards — and works without Claude; the [Claude layer](#the-claude-layer) adds delegation and scheduled maintenance on top. This page is the map; per-folder detail lives in [INDEX_workspace.md](INDEX_workspace.md) and each folder's own `INDEX_*.md`. Setup: [README.md](README.md) (your phase) → [SETUP.md](SETUP.md) (Claude's phase).

## Folders

1. `tasks-and-notes/` — one-off tasks and notes, one file each, flat; frontmatter drives the root dashboards (see [Tasks](#tasks)).
2. `projects/` — the goal tree: goal and knowledge notes (see [File conventions](#file-conventions)); dashboard `projects/overview.md`.
3. `posts/` — drafts, published posts, dropped posts.
4. `auto-review/` — generated review notes: daily git-diff summaries, condensed weekly/monthly/quarterly/yearly.
5. `handoffs/` — session-handoff notes; handoffs serving a single goal live in that goal's folder instead.
6. `external-projects/` — code repos beside the vault; each keeps its own git history, auto-ignored by the vault repo.
7. `non-markdown/` — automation wrapper scripts, per-job settings profiles, systemd units, media.
8. `archive/` — frozen reference material, not active work.
9. `templates/` — Templater folder templates; they auto-fill frontmatter on notes click-created in `tasks-and-notes/` and `projects/`.
10. `optional-extensions/` — opt-in add-ons ([index](optional-extensions/INDEX_optional-extensions.md)).
11. `.claude/` — CLAUDE.md, skills, scripts, workflows, settings.
12. Vault root — the dashboards `me.base` (your queue), `claude.base` (delegated queue), `recent.base` (recently modified files), plus README / SETUP / this file.

## File conventions

1. In `projects/`, the filename marker sets the note type: `,` = goal note (e.g. `,create X.md`; a question is just a goal aimed at an answer), `-` = knowledge/reference note (e.g. `-atlas.md`), no marker = other/misc.
2. Goal notes carry `status` + `parent` frontmatter (`parent` wikilinks the parent goal) and `# Goal clarification` / `# Subtasks` / `# Notes` sections; a goal with subgoals gets its own folder. Full conventions: [INDEX_projects.md](projects/INDEX_projects.md).
3. Subtask lines carry state marks — `[x]` done, `[!]` finished but unconfirmed, `[?]` on hold, `[f]` failed, `[-]` cancelled — specified with the rest of the task-file format in [-VNA task-file structure.md](projects/-VNA%20task-file%20structure.md).
4. `projects/overview.md` embeds every top-level goal's `# Subtasks` — one dashboard over everything active.

## Tasks

1. Every task or note in `tasks-and-notes/` is one file; the frontmatter is the whole schema: `status` (empty, `in-progress`, `inbox`, `review`, `note`, `note-archived`, `done`, `archived`), `owner` and `next_action_by` (`me` = you), `priority` (1–10; empty sorts as 5), `not_before` (defer until a date), `project`, `subscribers`. Click-created notes get it auto-inserted by `templates/task.md`.
2. `me.base` groups everything actionable by you into sections — In Progress, Inbox, Review, Do, Wait & Subscribed, Later, Notes, and more.
3. The flow follows Getting Things Done: capture into the inbox, process into the actionable sections; a set `not_before` date corresponds to GTD's waiting-for — the task sits in Later until the date passes.
4. Tasks can be connected to projects via the `project` property, though the reference workflow tracks projects as goal files in `projects/` instead. Projects have no `not_before` equivalent (a `[b]` checkbox mark plus a wait-for status would be the mechanism; not implemented).

## The Claude layer

Claudian embeds Claude Code as a panel inside Obsidian — convenient mainly for quickly having Claude look at (and edit) whatever you're working on. `.claude/` holds its configuration: `CLAUDE.md` (the conventions above, as loaded instructions), 16 skills, scripts, workflows, and least-privilege settings profiles for the scheduled jobs. Beyond chat:

1. **Delegated tasks** — set a task's `next_action_by:` to a model name (`opus`, `fable`, `sonnet`, `haiku`, or `claude` for the CLI default); `claude.base` is that queue, and an hourly headless runner (opt-in at setup) processes it: one Claude instance per task, result written into the note, handed back as `status: review` into me.base's Review section. An empty queue costs zero tokens. Doc: [claude-task-runner.md](tasks-and-notes/claude-task-runner.md).
2. **Goal orchestration** — for multi-step goals, tell Claude to load the `vna-controller` skill on a goal note: planning agents decompose it into child task files, fresh-context agents execute and then review each one, and `checkpoint:` lines stop the run for your answer.
3. **Scheduled maintenance** — a nightly job (23:00) commits one git snapshot and writes the daily review note (the vault's git repo is this pipeline's; you normally never commit); every 2nd day a cleanup pass first restores the `projects/` tree from `parent` properties, moves handoff notes, and refreshes INDEX files and `overview.md`. Ops docs: [claude-task-runner.md](tasks-and-notes/claude-task-runner.md), [vault-cleanup routine.md](tasks-and-notes/vault-cleanup%20routine.md); scheduling is set up in [SETUP.md](SETUP.md).
4. **Handoffs** — the `handoff` skill distills a session's state into a note a fresh session resumes from; relay mode chains background successor sessions.
5. **Extensions** — install an add-on by telling Claude "set up the `<name>` extension"; shipped: `spare-usage-burner` ([index](optional-extensions/INDEX_optional-extensions.md)).

License: MIT; the `create-or-edit-skills` skill keeps its upstream Apache-2.0 license in its folder.
