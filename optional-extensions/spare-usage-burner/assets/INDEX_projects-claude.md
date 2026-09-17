---
status: note
---
# projects-claude/ — index & conventions

**Lower-relevance projects executed mostly by Claude.** The user delegates rather than works here: a scheduled routine launches headless vna-controller sessions over this folder in the last ~18h before the weekly usage limit resets, spending capacity that would otherwise expire — usage-ceiling-gated via the `check-claude-usage` script. Setup, schedule, and budget formula: [[projects-claude routine]].

## Conventions — identical to [[INDEX_projects]] except

1. **Dashboard**: [[projects-claude-overview]] — a priority-sorted (descending) checklist of top-level goals; work top-down, only continue to lower entries when blocked or finished. (Deliberate format choice — not the embed-dashboard format of projects/' [[overview]].) Archived projects move out of the main list into an `## Archived` section at the bottom (ticked, with archive date).
2. **`projects-claude/archived/`** takes top-level projects with terminal status (`done`/`archived`/`cancelled`/`failed`), same mechanics as `projects/archived/`.
3. **Templater**: the same [[project]] folder template applies here as in `projects/` (empty click-created files only) — mostly irrelevant in practice since Claude writes complete files itself: `status`/`parent` frontmatter, and `# Goal clarification` / `# Subtasks` / `# Notes` sections on goal notes.
4. Everything else — note types (`,` goal / `-` knowledge / unmarked other), frontmatter (`status` + `parent` only), the folder-structure rule (goal folders once ≥1 subgoal, knowledge placement, `handoffs/`, no per-goal INDEX files) — as specified in [[INDEX_projects]]. The cleanup routine (`.claude/references/vault-cleanup.md`) maintains this folder the same way, independently of `projects/`.

5. **Gitignored folder** (optional pattern): a free-play folder like `do whatever you want (as long as it doesn't harm my goals)/` can be excluded from the vault git repo — Claude's free-play output, kept out of history and daily-review diffs (a commented example line ships in `.gitignore`). Cleanup must not move or archive it out of that path without re-checking `.gitignore`.

## Working mode

6. Since work here runs with little supervision: when finishing a goal prefer `status: review` over `done` unless the result is trivially verifiable, and keep goal notes' `# Notes` current enough that a fresh session (or the user skimming) can resume from the note alone. Mid-task stops get a handoff (handoff skill).
