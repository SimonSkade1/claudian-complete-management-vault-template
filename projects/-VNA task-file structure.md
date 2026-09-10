---
status:
parent:
---

Canonical reference for how VNA goal/task files are structured; consumed by the planner/controller/executor/reviewer skills. These conventions + `read_obsidian.py` + the `parent` property make a context-assembly script unnecessary. Vault-general conventions (`,`/`-` filename markers, status lifecycle, [[INDEX_projects]]) still apply; this adds the VNA specifics.

## Template

One template for **every** VNA task. All sections exist from file creation on; `# Subtasks` and `# Notes` start **empty**. The three subtask subsections are filled in only when the controller decides the task gets decomposed / a planner is called (a decomposed task is expected to span multiple executor runs). A leaf executor may or may not use its native Claude task list; if it does, it copies the completed list into `# Subtasks` on completion.

```
,example goal.md:
---
status:
parent: "[[,parent goal]]"
---

# Goal clarification

[written by the planner from the parent goal; content spec is the vna-plan skill's job]

# Subtasks

1. Subtask History
	1. [x] [[,planning task 1 for {example goal}]]
	2. [x] [[,finished subtask]]
	3. [!] [[,probably-ok subtask]] — key uncertainty in one line
	4. [f] [[,failed subtask]] — what fell short in one line
	5. [-] [[,dropped subtask]] — why dropped
2. Loaded ^loaded
	1. [ ] ![[,currently active subtask#^loaded]]
	2. [?] [[,on-hold subtask]] — waiting, see its # Exception
	3. [ ] [[,queued subtask]]
	4. [ ] [[,planning task 2 for {example goal}]]
3. Possible next steps
	1. [ ] [[,demoted subtask]] — moved back from Loaded while re-planning
	2. ,subtask proposed by the planner
	3. ,loose idea

# Notes

[space for Claude to put useful information and considerations]
```

1. Sections inserted at the **top** of the file later, in this order when several exist: `# Verdict` (reviewer), `# Executive summary` + `# Report` (executor, on completion), `# Exception` (the working agent, when raising one). Execute↔review fix rounds (vna-reviewer skill) stack `# Verdict round N` (reviewer's interim fix requests, no status change) and `# Key updates round N` + `# Report about updates round N` (executor) on top the same way; a plain `# Verdict` is always the final one.
2. The ` ^loaded` block anchor is required verbatim (with the preceding space) — embeds and `read_obsidian.py` resolve it.
3. Empty sections stay as bare headers (never deleted); empty subtask subsections may be omitted.

## Subtask sections

1. **Subtask History** — all terminated lines (`[x]`/`[!]`/`[f]`/`[-]`) in one section, sub-distinguished only by their marks. **Order is preserved**: lines keep the order in which the subtasks were planned/executed; never regroup by outcome. One exception: `[?]` lines never move to History — they stay in Loaded until resolved.
2. **Loaded** — the approved queue in intended execution order: `[ ]` lines (plus `[?]` lines awaiting resolution).
3. **Possible next steps** — staging area: coarse later parts of a plan (lazy decomposition — the planning workflow loads only the frontier into Loaded), items demoted from Loaded during re-planning, and loose ideas. Input to later planning, never executed directly.

## Checkbox marks

The **reviewer** decides between `[x]`/`[!]`/`[f]`/`[?]` and itself sets the reviewed file's `status`; an agent raising an exception sets its own `status: on-hold`; `[-]` follows from controller/planner decisions. The controller performs the checkbox-mark and move edits, except the planning write agent's own bookkeeping and excepted-line dispositions (see State updates).

1. `[ ]` **open** — queued in Loaded. *(file status: empty/active, in-progress while running)*
2. `[x]` **done and confirmed** — reviewer verdict: meets the bar. → History. *(status: done)*
3. `[!]` **probably ok, not confirmed** — the work is **finished**; the reviewer wasn't sure everything meets the bar, or key implementation choices deserve the user's review (which may trigger minor adjustments). Never a blocker: the line always moves to History with the `[!]` kept; flips to `[x]` once confirmed. The controller/planner still decides — a real judgment call — whether to also front-queue a planning round about the flagged uncertainty. *(status: review)*
4. `[f]` **failed** — reviewer verdict: doesn't meet the bar. → History; triggers the re-plan procedure. *(status: failed)*
5. `[?]` **on hold** — the task is **unfinished** and waiting on an out-of-system input: a raised `# Exception`, a reviewer-flagged blocking user-step (Review pt 3), or a checkpoint wait (Descent pt 6). Stays in Loaded until resolved (the task is usually resumed afterwards); triggers the re-plan procedure / wait escalation. Never terminal, never History as `[?]`. *(status: on-hold)*
6. `[-]` **cancelled** — deliberately dropped, nothing further needed. → History. *(status: cancelled)*

File-level `status` and mark mirror each other as noted — status set at the source, parent-side mark by the controller. The sharp divide: `review` = **finished**, only the user's review outstanding — never blocking, line always in History; `on-hold` = **unfinished**, non-terminal, waiting on out-of-system input — line stays in Loaded. Exceptions are resolved through planning, not user-review; `failed`/`cancelled` are terminal like `archived`. `projects/` has no base — waiting `[?]` and unconfirmed `[!]` lines surface through [[overview]]'s embedded `# Subtasks`. In the tasks-and-notes bases ([[me.base]], [[claude.base]]): `on-hold` → Review section, `failed`/`cancelled` → Done & Archived, all three excluded from Claude's Do queue.

## Loading & edges

1. **Loading = being sorted into Loaded.** That is the deciding factor — not whether a link, checkbox, or file exists. ("Active"/"activate" instead always refers to the current descent/embed chain, never to Loaded membership.) Loading normally comes with: own file created (frontmatter `parent` set, `# Goal clarification` written by the planner; controller-created planning files are the exception — no clarification content, see Descent pt 2) + a `[ ]` checkbox link placed in Loaded at its execution-order position.
2. Demotion (Loaded → **front** of Possible next steps — during re-planning): keep the checkbox + file link if the file already exists (the usual case); strip to plain text only if no file was created yet (unlikely). A demoted item counts as **not loaded** despite its link.
3. Checkbox lines link **only `,` goal files**. Knowledge notes (`-`) and other references are linked in body text, never after checkboxes. Small planner-added steps that need no own file (e.g. a "compile output" step) may be plain-text checkbox lines without a link.
4. `parent`: wikilink to the **single** parent goal; empty only for root goals. A task serving several goals: one parent owns the hierarchy edge; the others get a plain "serves also: [[…]]" line at the file bottom.
5. Frontmatter carries nothing beyond `status` + `parent` (projects/-wide rule, [[INDEX_projects]]): model choice is the controller's call at spawn time. *(The earlier planner-sets-`next_action_by` design was dropped 2026-07-10 together with the extra properties.)*
6. **Embed rule**: the first open `[ ]` item in Loaded — the active descent path — is an embed `![[child#^loaded]]` instead of a plain link, *iff* the child is itself decomposed. At most one embed per file; collapse to a plain link when the line leaves Loaded or the descent moves elsewhere.

## Context assembly (no script)

1. `python3 .claude/scripts/read_obsidian.py "<task>"` — the `^loaded` embed chain expands the active frontier inline (default `--max-depth 4`; raise for deeper trees).
2. Read the parent via `parent` (gives goal context + siblings + order); the grandparent too when it seems useful.
3. Verdicts/executive summaries of terminated children/siblings sit at the top of their files — read on demand.

## Descent & flow control

1. Next task = first `[ ]` item in Loaded, depth-first through the embed/link chain.
2. Active leaf (empty `# Subtasks` — a never-decomposed goal; an *exhausted* Loaded is instead completion, see Completion): the controller decides — small enough → launch a do-task agent on the task directly; needs decomposition → create a **planning subtask** (own new document, front of Loaded). The controller creates that file **bare** — frontmatter + the standard empty sections, no goal-clarification content: the planning agents read the planned leaf's own goal clarification (and, on re-plans, the triggering `# Exception`/`# Verdict`) plus the planning-stage skills. Planning tasks are always executed directly, never themselves planned (no meta-planning). A pending planning subtask in Loaded always takes precedence: never judge the goal directly do-able past it — run the planner on it.
3. On `[!]`: the line moves to History (`[!]` kept) either way — review never blocks. The controller (or planner) still decides, a real judgment call with no default: continue, or additionally front-queue a planning round about the flagged uncertainty (re-plan procedure).
4. **Re-plan procedure** (on `[f]`; on `[?]` — exceptions and waits alike, re-fired at each level as they escalate; or on `[!]` if so decided):
	1. Front-queue a **planning task** (its own new document) into the Loaded holding the blocking line — it becomes the first open item, so execution continues with the planner.
	2. Move the remaining loaded items to the **front of Possible next steps** — they are input to the new plan.
	3. The blocking line itself is not demoted: `[f]` and a re-plan-triggering `[!]` move to History (marks kept), `[?]` stays in Loaded.
	4. Failed tasks are never re-run in place: a retry, if the new plan decides on one, happens in a **new document** (the old file keeps its terminal status). Excepted tasks are instead usually **resumed in the same document** (the resolution plan's write agent flips the line back to `[ ]`) once the blocker is resolved (see Exceptions).
5. **Independence rule**: while something waits on the user or another out-of-system input (an unanswered `checkpoint:`, an unresolved `[?]`), only tasks **truly independent of it — doable without drawback whatever the answer** — may proceed: the planner frontloads those tasks before the blocker; everything else waits behind it or stays demoted. In doubt, wait: wasted work costs more than idling. The rule is **planner-owned** — applied whenever a plan waits on the user instead of fixing a blocker now: ordering steps ahead of a `checkpoint:`, frontloading independents when raising an exception (vna-plan skill), and in the wait-triggered planning rounds at each level as a wait escalates (Exceptions pts 3/6). The controller makes no independence judgments itself.
6. **Checkpoint wait** — the next open item is a link-less `checkpoint: …` line: it's the user's to answer (e.g. a plan sign-off; planners lead a plan with one when it should wait on the user's review before running). The controller relays the question in chat and sets the goal's `status: on-hold` — unfinished, waiting, not complete or dry. The goal is drained by construction (nothing workable ahead of the checkpoint), so the wait escalates per the drain rule (Exceptions pt 6): its line in the parent stays in Loaded flipped to `[?]`, and the parent gets a wait-triggered planning round (re-plan procedure, trigger `wait on <goal path>`) whose planner frontloads truly independent parent-level items ahead of the `[?]` — at the goal the controller was launched on, instead stop cleanly. On the user's answer: checkpoint line `[x]` → History, status cleared, the `[?]` line back to `[ ]`, execution continues.

## Review

1. A review-result step is part of executing every loaded task (inline for cheap tasks; separate reviewer agent / rubric workflow for harder ones — cf. parent note → Review & evaluation). Exception: planning tasks — the plan-review inside the planning workflow is their review; no review-result step follows, and planning files are never marked `[!]`/`[f]` — they end `[x]`/`done`, also when their decision was raising an exception for the planned goal.
2. The reviewer **always adds a `# Verdict` section at the top** of the reviewed file, starting with a TLDR unless the verdict is very short. In multi-round execute↔review runs it may first request fix rounds (`# Verdict round N`, no status/mark); only the final review produces `# Verdict`, the mark, and the status — decision rules and verdict format: the vna-reviewer skill.
3. Verdict → mark: meets the bar `[x]` · probably ok but not sure `[!]` · doesn't meet the bar `[f]` · complete except a last genuine user-step `[?]` (`status: on-hold` — **there are no blocking review tasks**: `review` is reserved for finished work; when a blocking step the user must do remains, the reviewer marks on-hold instead and names the step in the verdict's `## Blocking step`, plus what the status becomes once the user has done it).
4. An agent that makes significant judgment calls without excepting should record those key uncertainties in `# Notes`, so review can surface them later.

## Exceptions

1. **When to raise**: it seems sorta likely that proceeding would be wasted effort or actively confusing (ill-posed task, wrong approach, missing key information). If the agent thinks it can resolve the uncertainties well through its own considerations, it should instead just do the task and record the key uncertain decisions in `# Notes` (surfaced later through review). Self-clarify via parent (+ grandparent) before raising. Should fire rarely.
2. **Raise**: the agent writes `# Exception` at the top of its task file (what's wrong; what decision/information is needed), sets its own file `status: on-hold`, and reports back. The controller sets the parent line to `[?]` and runs the re-plan procedure.
3. **Resolve — through planning**: the front-queued planning task tries to resolve the exception itself (answer the question, fix the task setup). Planning agents never except their own planning task — they must come to a decision; if the decision is that the exception cannot be resolved (specifically for lack of information/a needed call), they raise the exception **for the goal being planned** (the write agent puts `# Exception` on that goal, sets its `status: on-hold`, and re-loads the plan's frontloaded truly independent items ahead of the `[?]` — Independence rule) — no planning retry at that level. The controller relays the questions into chat at raise time (the user typically reads much later) and works the frontloaded tasks; the exception escalates **one level up only when they drain** (no open item left ahead of the `[?]`): the planned goal's line goes `[?]` and the normal Raise/re-plan procedure runs at the parent level. This recurses; a drained exception at the goal the controller was launched on ends in stopping cleanly on the already-relayed questions. Exceptions are not resolved by user-review by default.
4. **Afterwards**: the excepted task is usually **resumed in the same document** (the resolution plan's write agent flips its `[?]` line back to `[ ]` and clears its status; cancels are likewise the write agent's edit), runs again, and ends in whatever state the reviewer assigns (`[x]`/`[!]`/`[f]`/`[?]` — completion included). If the exception rightly showed the task was misguided, it is cancelled (`[-]`) instead; a differently-framed replacement counts as a retry → new document, old one cancelled as superseded. While unresolved, the `[?]` line stays in Loaded (never History); after resumption it follows the normal rules with its final mark.
5. **Log**: every exception gets a reasonably detailed entry in [[VNA-exceptions-log]] — date, task + parent, what was attempted, why blocked / what's needed, resolution (resumed / cancelled / replaced / escalated, with links). Once per exception, at raise time — not again on escalation.
6. **Waits without an exception share the machinery**: a goal on hold at an unanswered `checkpoint:` (Descent pt 6) or a task the reviewer put on hold over a blocking user-step (Review pt 3) likewise sits `[?]` in its parent's Loaded. The same drain rule applies at every level: a goal with no open item left ahead of its wait (`[?]` line or first-open `checkpoint:`) is **drained** — the controller flips its line to `[?]` at the parent (setting `status: on-hold` there if not already set at the source) and runs the re-plan procedure there, trigger `exception on <path>` if an `# Exception` sits on the drained file, else `wait on <path>`. Each level's planning round frontloads its truly independent items (Independence rule) or installs nothing, in which case that level drains too and the wait escalates further — at the launch goal it ends in stopping cleanly on the already-relayed blocker. Waits carry no `# Exception` and get no log entry; the blocker text lives in the checkpoint line or the verdict's `## Blocking step`, and resolution is the user's answer, not planning: on it the controller itself restores state (`[?]` → `[ ]` and status cleared for checkpoints; the verdict's stated final status/mark for blocking steps).

## State updates

1. `status` is set at the source: the **reviewer** sets the reviewed file to `done`/`review`/`failed`/`on-hold` per its verdict; an agent **raising an exception** sets its own file to `on-hold`; the **planning write agent** sets the planning file to `done` (on escalation also the planned goal to `on-hold`; on exception-resolution plans the excepted child's status per disposition); the **controller** sets `on-hold` at checkpoint waits and when flipping a drained goal's line to `[?]` (Exceptions pt 6).
2. Controller: everything else — checkbox marks, moves between sections, front-queuing and demotions, embed promotion/collapse, `in-progress`/`cancelled` and any status repairs. Exception: the **planning workflow's write agent** — it writes an accepted plan in (creates the subtask files incl. `# Goal clarification`, adds their `[ ]` lines to the planned file's Loaded — frontier only; coarse later parts → Possible next steps; on a first decomposition it also creates the goal's folder and moves the goal file and planning file inside), moves its own planning line `[x]` → History in the planned goal, and applies excepted-line dispositions (resume: `[?]` → `[ ]` · cancel: `[-]` → History).
3. Beyond that, agents write only **content**: executor inside its own task file (work, `# Notes`, `# Executive summary`/`# Report`, `# Exception`); reviewer its `# Verdict` into the reviewed file.

## Completion

1. Executor inserts `# Executive summary` + `# Report` at the top; an executor that used the native task list copies the completed list into `# Subtasks`. (Audiences + writing bar for the inserted sections: specified in each role skill.)
2. Reviewer adds `# Verdict`, decides `[x]`/`[!]`/`[f]`/`[?]`, and sets the file `status` accordingly (`done`/`review`/`failed`/`on-hold`).
3. Controller: moves the parent line to History with its verdict mark (a `[!]` keeps its mark until confirmed), collapses the embed to a plain link, embeds/starts the next open item. (Planning lines: the write agent moves its own.)
4. **Goal completion**: a goal is complete exactly when its Loaded is exhausted — no separate complete-vs-continue decision. Planners always end Loaded with either another planning task or write-output + review-result checkbox lines (normally link-less, executed directly in the goal's own file; on really large goals either may instead be an own goal file when it may itself need decomposing — the compiled output/verdict still lands in the goal's own file); that final review-result grades the goal's output and yields the goal's own mark. Loaded run dry without such a final step = planner-contract breach → the controller front-queues a planning task.
