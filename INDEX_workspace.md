# Vault Structure Notes

Each folder that contains subfolders should have an INDEX_[folder-name] file which briefly explains the content of those folders. This applies recursively. Exceptions:
1. The auto-review folder needs none.
2. For the external-projects folder it does not apply recursively (only on the level of the folder itself).
3. Only subfolders where purpose is clear by name or the name is sth like "archived" or "old".

Please flag violations of this policy or directly update index files.
# Index

- tasks-and-notes — one-off tasks and notes, one file each, flat. Frontmatter drives the two root bases: `status` (empty, `in-progress`, `inbox`, `review`, `note`, `note-archived`, `done`, `archived`), `owner`/`next_action_by` (`me` = the user; a model name delegates to the headless runner — [[claude-task-runner]]), `priority` 1–10 (empty sorts as 5), `not_before` (defer until date), `project`, `subscribers`. Views: [[me.base]] (the user's queue, grouped by section), [[claude.base]] (the delegated queue). Click-created notes get the frontmatter auto-inserted ([[task]] template).
- projects — goal and knowledge notes (plus misc "other" files). Filename marker sets the type: `,` = goal (a question is just a goal), `-` = knowledge, none = other. Frontmatter: only `status` + `parent`. A goal with ≥1 subgoal gets its own folder (named without the marker), recursively; goal folders need no INDEX — the goal note's `# Subtasks` is the index. Terminal-status top-level projects move to `projects/archived/`; `on-hold` ones to `projects/on-hold/`. Dashboard: [[overview]] (embeds top-level goals' `# Subtasks`); full scheme: [[INDEX_projects]].
- external-projects — code projects and other repos that live beside the vault but keep their own git history; every subfolder containing a `.git` is auto-ignored by the vault repo (managed `.gitignore` block, regenerated nightly). Conventions + project list: [[INDEX_external-projects]].
- posts — drafts, published posts, and dropped posts.
- handoffs — vault-general session-handoff notes (working docs one Claude session writes for its successor — `handoff` skill); handoffs serving a single goal live in that goal folder's own `handoffs/` subfolder instead ([[INDEX_projects]], folder-structure rule 4).
- archive — frozen/reference-only material, not active work. Contents need no INDEX (folder name signals purpose, per policy above).
- auto-review — auto-generated review notes: daily git-diff summaries plus weekly/monthly/quarterly/yearly distillations (each layer condenses the one below); structure `YYYY/Qn/MM-Month/CW-ww/daily-DATE.md`, higher-layer notes one level up each.
- non-markdown — scripts and non-markdown assets: review-pipeline wrapper + settings, task-runner wrapper + settings ([[claude-task-runner]]), vault-cleanup wrapper + settings (`run-vault-cleanup.sh`, chained from the review wrapper every 2nd day — see [[vault-cleanup routine]]), systemd units, update-external-ignores.sh; `logs/` is gitignored.
- optional-extensions — opt-in add-ons, one subfolder each (setup doc + assets); install by pointing Claude at the subfolder's SETUP.md. See [[INDEX_optional-extensions]].
- templates — Templater folder templates, auto-applied only to notes created empty via the Obsidian UI (files created with content — by Claude, scripts, or sync — are never touched): [[project]] (for `projects/` — `status`/`parent` frontmatter, plus the VNA sections on goal notes), [[task]] (for `tasks-and-notes/` — the task frontmatter). [[subtasks]] is a manual snippet for the `# Subtasks` skeleton. Mappings live in Templater's plugin settings (SETUP.md step 8).
