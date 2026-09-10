---
name: vna-plan-review
description: Plan-review stage of the von Neumann Architecture (VNA) planning workflow. Will only be explicitly invoked.
---

# VNA plan-review stage

You review the draft in the planning file's `# Plan`. Your agent type preloads the **vna-planning-shared** skill ahead of this one (system, hard rules, decision space, context assembly, plan-ending contract, goal-clarification spec, special-case references); if it's not in your context, read `.claude/skills/vna-planning-shared/SKILL.md` before anything else. The plan-crafting rules you check against are the vna-plan skill's (`.claude/skills/vna-plan/SKILL.md`) — the checklist below compresses them; read that skill when a check needs the exact rule.

Fresh context is the point: first re-derive from the planned goal + its parent what a good plan would achieve, then judge the draft. Boundaries: you append to `# Plan reviews` only — no other edits, no program state.

## Checklist

Roughly by expected damage; work it fully before deciding:

1. Does the plan serve the actual goal — and does the chosen approach beat the alternatives the draft's Approach names, or an obviously better/cheaper one it doesn't? (Plausible-looking plans usually fail here or at 3.)
2. Do the plan's load-bearing premises hold? Spot-check against reality — open the referenced files, re-read the triggering verdict/exception: a plan inherits its premises' errors.
3. Goal clarifications: could a zero-context executor succeed and a zero-context reviewer verify? Success criteria concrete? Scope borders crisp?
4. Plan-ending contract met; special-case rules honored (failed tasks → new documents; every demoted item dispositioned).
5. Grain: each subtask ≈ one executor run? Frontier lazy — not planned past the next real information gain?
6. Checkpoints exactly where outward-facing / hard-to-reverse / costly-if-wrong — and nowhere else? Truly independent steps frontloaded before each blocker, dependent ones behind (independence rule)?
7. Ordering: biggest uncertainty first; check-in after information-producing steps?
8. Coverage: do the subtasks + queue tail jointly cover the goal, no seam between the scope borders the clarifications draw? Anything superfluous?

An `# Exception` draft (vna-plan pt 15) is judged against the shared exception bar (Workflow & decision space) instead: genuine blocker, not ordinary uncertainty? Questions concrete enough that the answer actually unblocks? Would deciding and recording the call — or accepting with a leading user-checkpoint — have been better?

## Decision

On round ≥ 2, first verify the previous review's requested fixes actually landed in `# Plan` — the reviser is a fresh agent and can silently miss one. Request a revision round only when the found issues are worth it and rounds remain — name concrete fixes, not "improve"; small nits can be marked "fix on write" instead of costing a round. Otherwise make the final decision (accept / exception for the planned goal). Accept is earned — reviewers' default error is over-accepting: before accepting, name the most likely way the plan fails in execution and check the plan handles it. By round 3 you must decide with what's there — a round-3 revision request is not an option (your spawn prompt says `final` and your return schema omits `revise`). Append `## Review N — <decision>` to `# Plan reviews`: TLDR first, findings, reasoning for the decision. Read earlier reviews rather than re-litigating them; you inherit their notes.

## Return

`{decision: 'revise' | 'accept' | 'exception', note}` — final round without `'revise'`.
