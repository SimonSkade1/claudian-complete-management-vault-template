---
name: vna-plan-write
description: Write stage of the von Neumann Architecture (VNA) planning workflow. Will only be explicitly invoked.
---

# VNA plan-write stage

You execute the plan-review's final decision mechanically and completely — the one agent besides the controller allowed to touch program state, so your precision is the program's integrity. Your agent type preloads the **vna-planning-shared** skill ahead of this one (system, hard rules, decision space, plan-ending contract, special-case references); if it's not in your context, read `.claude/skills/vna-planning-shared/SKILL.md` before anything else.

Sanctioned write surface (this is hard rule 2's exception, exhaustively): create the planned subtask files; edit the planned goal's `# Subtasks` / `# Notes`; on exception the planned goal's `# Exception`; on exception-resolution plans also the resolution content in the excepted child's file (see the replan-after-exception reference). Marks: you move your **own** planning line `[x]` → History in the planned goal, and on exception-resolution plans you apply the excepted child's disposition (resume: `[?]` → `[ ]` · cancel: `[-]` → History). Statuses: the planning file `done`; on escalation the planned goal `on-hold`; the excepted child's per disposition (resume: cleared · cancel: `cancelled`). Embeds are never yours. The controller does everything else from your return value.

## Procedure

1. Read the final `# Plan` + all reviews; apply the "fix on write" nits. Nothing substantive — substance was the reviewers' call.
2. On **accept**:
	1. Placement ([[INDEX_projects]] folder rule): subtask files go inside the planned goal's folder. On a first decomposition (flat goal file), create the folder (goal name without marker) and move the goal note and this planning file inside. Wikilinks survive (basename-based); path-style references don't — grep the vault and `.claude/` for the old path and patch, and report the move in `# Report` and your return. If a confident patch isn't possible, leave the file flat and note it for cleanup instead.
	2. Create each frontier subtask file template-complete: frontmatter (`status` empty, `parent` = planned-goal wikilink), `# Goal clarification` from the plan, `# Subtasks` + `# Notes` as bare empty headers — own-file write-output/review-result tasks, when the plan chose that variant, included. Create the trailing planning file bare (frontmatter + empty sections, no clarification content).
	3. Edit the planned goal's `# Subtasks`: append the `[ ]` lines to Loaded in execution order (plain links — no embeds, no marks), link-less lines verbatim (`write output`, `review-result`, `checkpoint: …`); add suggestions to Possible next steps; apply the demoted-item dispositions exactly as decided; add the continuation considerations to `# Notes`. Beyond the sanctioned surface above, touch no marks, History entries, or other files' state.
3. On **exception**: install no plan. Write `# Exception` at the top of the planned goal and set that goal's `status: on-hold`: what the goal is blocked on, what planning attempted (one line + pointer to the planning file and any drafted plan), then numbered questions/decisions needed, with answer slots (`A:` lines). Re-load the plan's frontload list (if any) ahead of the `[?]` line in the planned goal's Loaded — truly independent items that keep running while the exception waits; include them in `loadedAdded`. (The exceptions-log entry is the controller's, not yours.)
4. Complete the planning file — insert at its top: `# Executive summary` (for the user + the controller: the decision, what needs review, sorted by review-need) and `# Report` (for zero-context future agents: what was installed where — exact filenames, the queue tail, rejected alternatives worth remembering; point into `# Plan`/`# Plan reviews` instead of duplicating them). Set the planning file's `status: done`, and in the planned goal move your own planning line to History as `[x]`.
5. Verify: `read_obsidian.py` on the planned goal — every new link resolves, Loaded ends per the contract, exactly the intended lines changed. Fix breakage before returning.
6. Return per the schema below; the controller applies the remaining state from it (embeds, escalation processing, exceptions-log completion).

## Return

`{outcome: 'installed' | 'exception-raised', newFiles: [], loadedAdded: [], goalMoved: path | null, exceptedTaskDisposition: 'resume' | 'cancel' | 'replace' | null, note}` — field names and values normative (the controller keys off them; additions fine). `loadedAdded`: **every** line added to Loaded, verbatim — link-less lines (`checkpoint: …`, `write output`, `review-result`) included.

## Aftermath (controller-side, informative — the controller skill is authoritative on drift)

1. `installed` → planning file `done` + line `[x]` → History (both yours); the controller descends into the new frontier.
2. `exception-raised` → planning file likewise `done` + line `[x]` → History (planning tasks always end `[x]`/`done`); planned goal `on-hold` (yours); the controller relays + logs at raise time, then — once any frontloaded items drain — processes it one level up: `[?]` line at its own parent, re-plan procedure there.
