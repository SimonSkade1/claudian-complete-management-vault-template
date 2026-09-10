# Vault cleanup — procedure

Deliberately not a skill: it is needed every couple of days at most, so it stays out of the always-loaded context and is read only when pointed at. Follow it end to end when running a cleanup.

The user does no folder structuring by hand: they create notes wherever is convenient and let structure be restored afterwards. This routine is that restoration. It moves files, never rewrites their content beyond frontmatter and references.

Two things make it safe to run unattended: it only descends into parts of the vault that changed since the last run, and it refuses to touch files the user may have open. Everything it cannot decide becomes a flag rather than a guess.

The conventions being enforced live in `projects/INDEX_projects.md` (folder-structure rule + note types + frontmatter) and `INDEX_workspace.md` (the recursive INDEX policy). Read both at the start of each run — they are the user's to change, and the current file wins over anything remembered here. This file is the *procedure*; those are the *spec*. If the vault has a `projects-claude/` tree (optional extension, see `optional-extensions/spare-usage-burner/`), the same procedure applies to it equally and **independently** (spec deltas: `projects-claude/INDEX_projects-claude.md`; dashboard: `projects-claude/projects-claude-overview.md`, whose format is a priority list, not embeds) — read mentions of `projects/` below as covering both trees, without ever moving notes between the two.

Open ambiguities and the `last_run` stamp: `tasks-and-notes/vault-cleanup log.md`. Setup docs: `tasks-and-notes/vault-cleanup routine.md`.

Normally this runs headless every 2nd day, chained from `non-markdown/run-vault-cleanup.sh` just before the nightly review stages its snapshot — so moves land in that night's commit. The user can also point a session at this file directly. Two constraints follow from the scheduled context: shell `for`/`while` loops are not on that run's permission allowlist (batch moves as `mv a b c target/`, or one call per file), and the run must never commit.

## 1. Scope the run

Read the log note's last run date. Then find what changed since:

```bash
git log --since="<last run date>" --name-only --pretty=format: | sort -u
git status --porcelain
```

Never commit — the daily-review automation owns this repo's commit cadence.

Restrict work to the **working set**: changed files, plus every note one goal-tree edge away from them (a note's `parent`, and the notes naming it as `parent`). A change elsewhere can force a move here — a new subgoal means its parent now needs a folder — so neighbors matter even when untouched. Folders with no changed files and no changed neighbors are already in their target state; skip them and say so.

On the first run, or when the log is missing, treat everything as in scope.

## 2. Exclude files the user may be editing

Moving a file out from under an open editor loses work. Skip:

1. Notes open in an Obsidian tab, from `.obsidian/workspace.json` (`leaf` nodes → `state.state.file`; `lastOpenFiles` is history, not open tabs, and entries ending `.tmp.<digits>.<hex>` are sync artifacts to ignore).
2. Anything modified in the last 30 minutes (`find … -mmin -30`).

Skipped files stay put and are listed in the run log so the next run picks them up. Skipping is cheap; a lost edit is not.

## 3. Build the goal tree

Read `status` and `parent` frontmatter across `projects/`, and the `# Subtasks` sections of goal notes. The tree comes from `parent` properties; `# Subtasks` links and judgment fill gaps.

Where a note's `parent` is evident but missing, fill it in. Where `parent` and the existing folder placement disagree and neither is clearly right, **flag it — do not guess** (§7). Terminated goals (`done`/`cancelled`/`failed`/`archived`) stay in the tree as history; they never trigger moves on their own.

## 4. Restore the folder structure

Per the folder-structure rule in `INDEX_projects.md` — reread it rather than working from memory. In outline:

1. A goal with ≥1 subgoal gets a folder named like the note without its `,` marker, containing the goal note itself plus its subgoals (recursively). Folders are never collapsed back when subgoals terminate.
2. Knowledge/other notes go in the folder of the innermost goal they are specific to; notes serving several goals, or consumed vault-wide by fixed paths in skills and scripts, rise to the nearest common ancestor or the `projects/` root.
3. `handoffs/` subfolders move with their goal folder. A handoff whose goal has no folder (a goal with no subgoals) belongs in the nearest ancestor `handoffs/`, falling back to `projects/handoffs/`. A handoff sitting in the vault-root `handoffs/` that carries a `parent` into `projects/` belongs with that work — move it in.

Use `mv` (wikilinks are basename-based and survive it). Create folders as needed; `mkdir -p` the whole target path in one go.

**Non-note directories stay put.** Code, data, model, and build directories (`model/`, `scripts/`, `__pycache__/`, `example-graph/`, …) belong to whichever goal folder they already sit in — they are working material, not navigation. Move them only as passengers when their whole goal folder moves, and never reorganize their insides: relative imports and hardcoded paths break in ways a wikilink never does. They are also the likeliest sign of a session working right now, so treat a recently-touched one as a reason to skip that branch entirely this run.

## 5. Patch references the moves broke

Wikilinks survive moves; **path-style references do not**. After every batch of moves, grep the vault and `.claude/` for the old paths and fix them:

```bash
grep -rn "<old path fragment>" --include="*.md" --include="*.mjs" --include="*.sh" --include="*.json" . \
  | grep -v "^\./\.git/" | grep -v "^\./\.claude/projects/" | grep -v "^\./\.stversions/"
```

Two kinds, handled differently:

1. **Path-style wikilinks** (`[[projects/foo/bar.md]]`) — rewrite to basename form (`[[bar]]`), which survives all future moves.
2. **Code/backtick paths** (reading lists in handoffs, script constants, skill instructions) — rewrite to the new path. These stay paths because headless agents open them directly.

Leave `auto-review/` notes alone: they are dated records of what the vault looked like then, not live references.

Check skills and scripts specifically — `.claude/skills/`, `.claude/references/`, `.claude/scripts/`, `non-markdown/`, `CLAUDE.md`, `INDEX_*.md` — since a stale path there breaks automation rather than just a link.

## 6. Refresh the indexes

1. **`projects/overview.md`** — one `## [[goal]]` heading plus `![[goal#Subtasks]]` embed per top-level goal (goal notes directly in `projects/`, and each `projects/`-level folder's main goal note). Add and remove sections as the top-level set changes; a goal note without a `# Subtasks` section gets one rather than a broken embed. Same role for `projects-claude/projects-claude-overview.md` over its own tree, if that optional tree exists — but that file is a priority-sorted checklist: keep entries pointing at existing top-level goals, don't convert it to embeds, don't reorder (order = the user's priorities).
2. **INDEX files** — per `INDEX_workspace.md`, every folder with subfolders needs `INDEX_<folder-name>.md`, except where the folder name already makes the purpose clear (`archived`, `old`, …), `auto-review/`, and below the top level of `external-projects/`. Goal folders are exempt: the main goal note's `# Subtasks` is their index. So in practice `projects/` subfolders get no INDEX — only a non-goal subfolder would.
3. Update the INDEX text where conventions actually drifted; leave it alone otherwise.

## 7. Log the run and flag what needs the user

Set `last_run: <today>` in the frontmatter of `tasks-and-notes/vault-cleanup log.md`. That stamp is the cadence gate's state *and* the wrapper's success signal — a run that moved files without stamping is treated as failed and retried, so stamp it even on a run that changed nothing.

The note's body is **only genuine ambiguities** — things you refused to guess at. Append new ones to the top, one or two sentences each, dated `(MM-DD)`. Don't log what moved, what was skipped, or that a run happened: the git diff already shows the moves, and a routine narrating itself buries the few items that actually need the user. Delete entries they have resolved. Keep `status: note` — these are for reading, not a task queue.

Flag anything the routine cannot resolve on its own:

1. `parent` property and folder placement conflict with no obvious right answer.
2. A note that could belong to several goals.
3. A structural oddity worth a human decision — an unexpectedly deep nesting chain, a goal whose stated independence contradicts its `parent`, a broken reference to a note that no longer exists.

Write flags as questions with a concrete recommendation, so the user can answer in one line.

Finally, report in chat: what moved, what was skipped, what is flagged. Short — a few lines.
