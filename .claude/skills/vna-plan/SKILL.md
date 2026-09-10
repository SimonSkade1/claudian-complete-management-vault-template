---
name: vna-plan
description: Plan stage of the von Neumann Architecture (VNA) planning workflow. Will only be explicitly invoked.
---

# VNA plan stage

You draft — or, on a `plan (revision, round N)` spawn, revise — the plan for a VNA planning task. Your agent type preloads the **vna-planning-shared** skill ahead of this one (system, hard rules, decision space, context assembly, plan-ending contract, goal-clarification spec, special-case references); if it's not in your context, read `.claude/skills/vna-planning-shared/SKILL.md` before anything else.

Boundaries: you write only into the planning file — `# Plan` (the draft, revised **in place**) and the planning file's `# Notes` (longer reasoning). No program state, no other files. On a revision you are a fresh agent: read `# Plan` and all `# Plan reviews`, apply the reviews' concrete fixes, don't re-litigate what they settled.

## Heuristics

Lean heuristics (GTD natural planning) — skip steps that are already settled:

1. Understand the **why**: purpose of the planned goal, and of its parent.
2. Clarify the **what**: what properties would a good solution have? Usually mostly given in the goal clarification — sharpen, don't restate.
3. Brainstorm **approaches or subproblems** — one lens at a time, whichever fits the goal: approaches = competing ways to achieve it; subproblems = parts that compose it.
4. Organize: what are the key underlying approaches, which ideas combine?
5. Decide.

## Plan shape

6. **Lazy decomposition.** Break only the frontier into executor-sized subtasks — default ~2 plus a trailing planning task; grain ≈ one focused effort-max executor run per subtask. Lay the full remaining course out only when it is small and clear — then end with the output lines instead (Plan-ending contract in the shared reference). Coarse later parts become Possible-next-steps suggestions; continuation reasoning goes to the planned goal's `# Notes`.
7. **Checkpoints** — ask-the-user steps, link-less: `[ ] checkpoint: <what the user signs off / decides>`. Place one before outward-facing, hard-to-reverse, or costly-if-wrong steps. Don't scatter them; each blocks its branch until the user answers (the controller relays the questions in chat, the user often reads much later, and only truly independent work proceeds meanwhile; a goal blocked at a checkpoint goes `status: on-hold` and sits `[?]` in its parent — levels above get their own frontloading chance through wait-triggered planning rounds). A plan that should itself wait on the user's review before running (early meta-level plans, stakes-heavy calls) leads with one, e.g. `[ ] checkpoint: the user signs off on the plan`. **Independence rule**: when the plan waits at a checkpoint — including a re-plan that decides to wait for the user's review instead of fixing a blocker now — frontload the truly independent tasks before the blocker; only steps unaffected by any plausible answer go ahead of it, the rest queue behind. In doubt, behind: wasted work costs more than idling.
8. **Check-ins**: after a step expected to produce plan-relevant information, prefer ending the frontier there (trailing planning task) over planning past it — reconsider the plan whenever new information about what plan would be good arrives.
9. Order for information: steps that reduce the biggest uncertainty come early.
10. A goal that turns out one-run-sized: one subtask + the output lines is a fine plan; don't force decomposition, don't except over the do-vs-decompose call. Plans in general can be short when the continuation is straightforward — re-plans especially are often just a brief memo + queue edits.

## Draft format in `# Plan`

Review and write consume this — keep the structure:

11. **Approach** — a few lines: the chosen approach and the alternatives rejected, with why (longer reasoning → planning file `# Notes`).
12. **Frontier subtasks**, in execution order, each: proposed filename (`,verb phrase`, vault-unique), a one-line grain judgment, and the full draft goal clarification (spec in the shared reference).
13. **Queue tail & extras**: the trailing element (contract pt 1 or 2), checkpoints/check-ins at their positions, Possible-next-steps additions, planned-goal `# Notes` additions.
14. On re-plans: an explicit disposition for **every** demoted item — re-load / keep staged / drop (with reason).
15. If your considered conclusion is escalation, draft the `# Exception` text in `# Plan` instead of a plan and say so — the reviewer judges it like a plan. Add a frontload list (may be empty): the demoted/queued items truly independent of the exception — doable without drawback whatever the answer — that keep running ahead of the `[?]` meanwhile (independence rule, pt 7).

## Return

`{status: 'drafted', note}` — note is one line; everything of substance is in the file.
