---
status: note
---
# projects/ — index & conventions

Home of the user's **goal** notes and the **knowledge** notes that serve them, plus misc **other** files. Dashboard: [[overview]] (embeds every top-level goal's `# Subtasks`; there is no base over this folder). New-note template: [[project]] (auto-applied by Templater, but only to files created **empty** — i.e. Obsidian UI click-create — in `projects/` and its subfolders). It inserts the `status`/`parent` frontmatter (for goal and knowledge files `parent:` is pre-filled with the previously open note, if that is a goal note) and appends empty `# Goal clarification` / `# Subtasks` / `# Notes` sections to **goal** files. Files created with any content (Claude/scripts/sync) are left completely untouched — Claude writes complete files itself, incl. frontmatter and sections.

There is no top-level wikis folder — knowledge notes live inside the goal folder they serve.

## Note types (inferred from the filename's `,` / `-` marker)

1. **Goal note** — marker `,` (e.g. `,create a good setup for this workspace vault`). A *question* is just a goal whose aim is finding a good answer — same `,` marker, not a separate type.
2. **Knowledge note** — marker `-` (e.g. `-AI agent orchestration system - components atlas`). Reference/wiki material.
3. **Other** — no `,`/`-` marker (e.g. `overview`). Uncategorized / misc files.

Don't start an unmarked note's filename with a digit directly before `,`/`-` (e.g. `7-day…`, `3,000…`) — the note template's marker regex would read it as a goal/knowledge note.

## Frontmatter

Exactly two properties — the `tasks-and-notes` task properties (`owner`, `next_action_by`, `priority`, `not_before`, `subscribers`, `project`) are **not** used in `projects/`:

1. **`status`** — *(empty = active)*, `active`, `in-progress`, `review`, `done`, `archived`, plus the VNA statuses `failed`, `on-hold`, `cancelled` (see [[-VNA task-file structure]]; `review` = finished, awaiting the user's review only · `on-hold` = unfinished, waiting on an out-of-system input). No `note`/`note-archived` values — the goal/knowledge/other distinction comes from the filename. (Meta-files like this INDEX and [[overview]] use `status: note`.)
2. **`parent`** — wikilink to the **single** parent goal, e.g. `parent: "[[,supergoal]]"`. On goal notes: empty only for top-level (root) goals; a goal serving several goals keeps one parent for the hierarchy edge and lists the others in a "serves also: [[…]]" line at the file bottom. On knowledge/other notes: set it when the note clearly serves one goal, leave empty otherwise.

## Overview file

[[overview]] is the dashboard: one section per **top-level goal** — every goal note lying directly in `projects/`, plus for every folder lying directly in `projects/` its main goal note (the note named like the folder + marker); `archived/` and `on-hold/` and their contents are excluded from embeds, but on-hold main goal notes are listed as plain wikilinks under an "On hold" section — embedding that note's `# Subtasks` section. The `^loaded` embeds inside those sections (structure doc) unfold the active frontier of deeper levels automatically. Cleanup keeps it in sync as top-level goals appear/disappear.

## Folder-structure rule (soft invariant — for cleanup)

The folder tree mirrors the goal tree. The user does **no** folder structuring by hand — Claude restores this structure during cleanup, per `.claude/references/vault-cleanup.md`. Concretely:

1. **A goal gets its own folder as soon as it has ≥1 subgoal** (a `,` note with it as `parent`). The folder is named like the note **without** the `,` marker (e.g. goal `,build X.md` → folder `build X/`), with the note itself inside as the folder's main note, and its subgoal notes (recursively: subgoal folders) inside.
2. A goal with no subgoals stays a flat file. Folders are **not** collapsed back when subgoals terminate — finished/cancelled subgoal files remain in the folder as history.
3. **Knowledge/other notes** live in the folder of the innermost goal they are *specific to* (= exist only to serve that goal). A note relevant to several goals — or consumed vault-wide via fixed paths in skills/scripts (e.g. [[-VNA task-file structure]], [[VNA-exceptions-log]]) — sits at the nearest common ancestor folder or the `projects/` root. A note specific to a folder-less goal stays flat next to it.
4. **`handoffs/` subfolders**: session-handoff notes (working docs one Claude instance writes for its successor; see the `handoff` skill) live in a `handoffs/` subfolder of the goal folder they serve (vault-general ones fall back to a root-level `handoffs/` folder; never under `.claude/` — permission-gated for headless successors). They are operational artifacts, not goal/knowledge notes; the name is either plain (`YYYY-MM-DD HHMM topic.md`) or carries the `,HANDOFF ` prefix (`,HANDOFF YYYY-MM-DD HHMM topic.md`) — the prefix is the majority convention in practice and is fine, but never use a bare `,`/`-` marker. During cleanup, a `handoffs/` folder moves together with its goal folder.
5. Goal folders get **no INDEX file** of their own — the main goal note's `# Subtasks` section *is* the index (satisfies the [[INDEX_workspace]] policy via its purpose-clear-by-name exception). Non-goal subfolders (if any ever exist) still need one.
6. **`archived/` subfolder** — **top-level** projects with terminal status (`done`/`archived`/`cancelled`/`failed`) move into `projects/archived/`: a goal folder moves whole (incl. its `handoffs/`); a flat goal moves together with the knowledge/other notes specific to it, its handoffs going to `archived/handoffs/`. Status `review` or empty stays at top level. Terminated subgoals *inside* active projects stay put as history (rule 2). `archived/` is a plain container, not a goal folder: excluded from [[overview]], and needs no INDEX ([[INDEX_workspace]] purpose-clear-by-name exception).
7. **`on-hold/` subfolder** — **top-level** projects with `status: on-hold` (on the main goal note) move into `projects/on-hold/`, same mechanics as rule 6. Excluded from [[overview]]'s embeds but listed there as plain wikilinks under "On hold"; when a project resumes (status cleared/`active`), it moves back to the `projects/` root. Like `archived/`, a plain container — no INDEX needed.

This is **not enforced at all times** — it's the target state cleanup restores.

### Cleanup procedure (automated every 2nd day; also runnable by hand)

`.claude/references/vault-cleanup.md` carries the full procedure — scoping a run by git recency, skipping notes the user has open, patching references, and logging. The rules below are the part that belongs to `projects/` and is the user's to change; the procedure reads them at each run.

1. Build the goal tree from `parent` properties + `# Subtasks` links + judgment; decide for each knowledge/other note which goal it is specific to. Conflicts between folder structure and `parent` properties with no obvious right answer: don't guess — flag them to the user.
2. For every goal with ≥1 subgoal, ensure its folder exists (named per rule 1), the goal note is inside as the folder's main note, and subgoal notes/subfolders + specific knowledge/other notes are inside. Fill in missing `parent` properties and `# Subtasks` sections where the tree is evident.
3. Move shared/general knowledge up to the nearest common ancestor folder or the `projects/` root.
4. Move top-level projects whose status has turned terminal into `archived/`, and those turned `on-hold` into `on-hold/` — moving resumed ones back to the root (rules 6–7 above).
5. Wikilinks are basename-based and survive scripted `mv`; **path-style references do not** — after moves, grep the vault and `.claude/` for the old `projects/...` paths and patch (skills, scripts, INDEX files, CLAUDE.md).
6. Update [[overview]] (the top-level goal set may have changed) and this INDEX if conventions drifted.
7. Don't move files the user might be editing right now — skip them and note the skip.

How the routine runs: [[vault-cleanup routine]]. Conflicts it flagged rather than guessed at: [[vault-cleanup log]].
