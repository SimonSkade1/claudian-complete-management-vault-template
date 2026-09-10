---
name: vna-planning-shared
description: Shared context of the von Neumann Architecture (VNA) planning workflow stages — preloaded by the vna-plan/-review/-write agent types. Will only be explicitly invoked.
---

# VNA planning workflow — shared context

Preloaded first by every planning-stage agent type (vna-plan-agent / vna-plan-review-agent / vna-plan-write-agent); your stage skill (vna-plan / vna-plan-review / vna-plan-write) follows with your stage spec. You are one stage of the **planning workflow** (orchestrated by `.claude/workflows/vna-planning.mjs`) that executes a VNA planning task. Your spawn prompt names your stage, the planning file's vault-relative path, and the trigger. The goal you are planning is the planning file's frontmatter `parent`: the **planned goal**, your main task. Everything here serves one outcome: the planned goal's queue continues with work a fresh, zero-context executor can succeed at.

Two hard rules:

1. **A planning task never fails and never excepts itself.** The workflow must end in a decision how to continue — the fixed decision space below. Missing information is handled by deciding to raise an exception **for the planned goal**, never for the planning task. Planning files are never marked `[!]`/`[f]` and get no separate review-result — the in-workflow plan-review is their review — and they always end `[x]`/`done`, exception-decisions included: the decision is the deliverable.
2. **Program state belongs to the controller — except the write agent's sanctioned surface** (plan install + own bookkeeping + excepted-line dispositions; defined in the vna-plan-write skill). Plan and plan-review agents write only into the planning file. Embeds stay the controller's everywhere; it applies everything else from the stages' return values.

## The VNA system in brief

A controller session walks a goal-file tree in projects/ (one file per goal/task), spawns one executor per task file, has every result reviewed, and applies the remaining state updates. When it judges a goal too big for one executor run, it creates a **planning task** as the goal's first loaded subtask — a bare file (frontmatter + empty sections, no clarification content), named `,planning task N for {goal name}` (braces literal; goal name without the `,` marker; N = next unused number for that goal — when creating one, match the pattern and numbering of the goal's existing planning tasks) — and runs this workflow on it. Every VNA file:

```
,example goal.md:
---
status:
parent: "[[,parent goal]]"
---

# Goal clarification

[task definition + success criteria — content spec below]

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

[considerations, uncertain judgment calls, continuation reasoning]
```

1. Marks: `[x]` done-confirmed · `[!]` probably ok, unconfirmed (status `review` — **finished**, only the user's review outstanding; never blocking, always History) · `[f]` failed (terminal) · `[-]` cancelled (terminal) · `[?]` on hold (status `on-hold` — **unfinished**, waiting on out-of-system input: exception / blocking user-step / checkpoint; stays in Loaded) · `[ ]` open. The reviewer decides `[x]`/`[!]`/`[f]`/`[?]`; terminated lines live in Subtask History, order preserved.
2. **Loaded** is the approved queue in execution order — **loading = being sorted into Loaded**, and a loaded item normally has its own file. ("Active" refers to the current descent/embed chain, never to Loaded membership.) **Possible next steps** is staging: coarse later plan parts, items demoted from Loaded during a re-plan (they sit at the front — plan input, not commitments), loose ideas; never executed directly.
3. Checkbox lines link only `,` goal files; knowledge notes (`-`) are linked in body text. Small steps that need no own file — `write output`, `review-result`, `checkpoint: …` — are plain-text link-less checkbox lines (write-output/review-result may get own files on really large goals — Plan-ending contract pt 2).
4. Sections inserted at the top of files as work happens: `# Verdict` (reviewer) · `# Executive summary` + `# Report` (on completion) · `# Exception` (escalation). Terminated files carry their results there — read siblings' tops when their outcomes matter.
5. New leaf files carry `# Subtasks`/`# Notes` as bare empty headers (the ` ^loaded` anchor and subsections appear only when a file is itself decomposed). Embeds (`![[child#^loaded]]`) are the controller's business, not yours.
6. Wikilinks resolve by basename — every new filename must be vault-unique.
7. Full conventions, rarely needed: `projects/-VNA task-file structure.md` (the structure doc; canonical on drift).

## Workflow & decision space

1. Stages: **plan** → **plan-review** → (revise ↔ review, at most 3 review rounds total, a further round only when the found issues are worth it; the last round may not request revision) → **write**. A revision is a fresh plan-stage agent working from the reviews in the file.
2. Working sections in the planning file, between `# Goal clarification` and `# Subtasks`: `# Plan` — the current draft, revised **in place**; `# Plan reviews` — `## Review N — <decision>` appended per round, never edited later. The file is the audit trail; your session is disposable.
3. The plan-review's **final** decision (a revision request is intra-workflow, never final), exactly one of:
	1. **accept** — the write agent installs the plan. A plan that should wait on the user's sign-off before running (early meta-level plans; taste-, values-, or stakes-heavy calls) is still an accept: it leads Loaded with a `checkpoint:` line (vna-plan skill), and the controller pauses there.
	2. **exception for the planned goal** — planning cannot responsibly draft a plan without a missing input: no plan is installed; the write agent puts `# Exception` at the top of the planned goal (setting it `status: on-hold`) and re-loads the truly independent items the exception draft frontloads — tasks doable without drawback whatever the answer (independence rule, vna-plan skill; may be none). The blocker escalates exactly one level up once those drain (the parent level gets its own planning chance first; at the goal the controller was launched on it becomes user-facing questions). Reserve exceptions for genuine blockers — ordinary uncertainty is better handled by deciding, recording the call, and letting review catch it; a drafted plan that merely needs the user's review takes the accept-with-checkpoint route.

## Context assembly

1. `python3 .claude/scripts/read_obsidian.py "<planning file>"`, then the planned goal, then the planned goal's parent (the why above the why). Grandparent and terminated siblings' verdicts/summaries (tops of their files) when they matter.
2. Plan input inside the planned goal: front-of-Possible-next-steps demoted items, `# Notes`, Subtask History with its marks.
3. On special-case triggers: the triggering `# Verdict`/`# Exception` and flagged file, plus the matching reference file (Special cases below) — all stages read it.

## Plan-ending contract

The controller treats an exhausted Loaded as goal completion, so a queue that runs dry without a final step breaks the program. The proposed Loaded must end with either:

1. `[ ] [[,planning task N+1 for {goal name}]]` — the next planning round, or
2. `[ ] ,write output` then `[ ] ,review-result` (canonical line texts) — normally link-less lines executed directly in the goal's file: compile the goal's `# Executive summary` + `# Report` from the subtask results; then a fresh reviewer grades the goal against its clarification (`# Verdict` + the goal's own mark; it may reuse the subtask verdicts, so often quick). On really large goals, either may instead be an own goal file (`,write output for {goal name}` / `,review-result for {goal name}`, with goal clarification) when it looks like it may itself need decomposing — the compiled output/verdict still lands in the goal's own file.

## Goal clarifications — for each new subtask file

Clarify-goal happens at plan time, because the planner holds context a fresh agent can't reconstruct; it is written FOR that fresh executor — zero context, full effort. Artifact quality dominates system performance, and these paragraphs are the highest-leverage artifact.

1. **Why** — 1–3 sentences: the planned goal's intent and how this subtask serves it. Distilled, not a link trail.
2. **What** — the task itself; scope boundaries, especially against sibling subtasks (who owns what).
3. **Success criteria** — an explicitly labeled list, concrete and checkable (exact paths, behaviors, numbers): the executor's target and the reviewer's bar. Name what failure looks like when that sharpens the bar.
4. **Context pointers** — only the non-obvious: specific notes/verdicts/files worth reading and why, one line each. (Task file, parent, grandparent the executor reads anyway.)
5. **Decisions & freedoms** — choices already made upstream (not to be re-litigated), and what is deliberately left open.

Usually 5–20 lines. Quote the user's instructions and constraints verbatim where they exist — paraphrase keeps the what and drops the why and the bar. Don't assume the executor can spawn agents or workflows (it runs as a workflow subagent and can't). Give goal + bar, not a procedure — over-specification wastes the executor's intelligence, and an executor hitting a real blocker raises its own exception; the plan doesn't need to pre-handle everything.

## Special cases

1. Re-plan after a `[f]` verdict, or a `[!]` escalated to re-planning → `.claude/skills/vna-planning-shared/references/replan-after-verdict.md`.
2. Exception resolution (a child sits `[?]` with an `# Exception`) → `.claude/skills/vna-planning-shared/references/replan-after-exception.md`.
3. Wait on the user (trigger `wait on <path>` — a child sits `[?]` with no `# Exception`: checkpoint wait or reviewer-flagged blocking step) → the same exception reference, its Waits section.

All short; every stage reads the matching one before its work.

## Spawn prompt

The workflow fills this template from the controller's args:

```
Stage: plan | plan (revision, round N) | plan-review (round N) | plan-review (round 3, final) | write (decision: <decision>)
Planning file: <vault-relative path>
Planned goal: <vault-relative path>
Trigger: scheduled | re-plan after [f] verdict on <path> | re-plan after escalated [!] on <path> | exception on <path> | wait on <path>
Extra pointers: <optional — sibling verdicts, knowledge notes, recent user input>
```

`scheduled` = the planning task was reached as a planned step in Loaded — the goal's first decomposition and planned re-planning rounds alike (the planning file's number and the goal's Subtask History tell which); the other triggers are the special cases.
