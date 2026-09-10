# Re-plan after a verdict — `[f]`, or `[!]` escalated to re-planning

The controller front-queued this planning task because a reviewer's `# Verdict` found work below the bar (`[f]`), or found a `[!]` whose uncertainty it decided not to wave through. The workflow runs normally (plan → plan-review → write); this file adds the case-specific rules. The verdict may sit on a subtask of the planned goal or on the planned goal's own final review-result.

Extra inputs: the flagged file's `# Verdict` (+ `# Executive summary`/`# Report` and the work itself), its `# Goal clarification` (was the bar wrong, or the work?), the demoted items at the front of Possible next steps.

## Decision guidance — smallest sufficient continuation first

1. **Improve the imperfections**: one subtask that fixes the verdict's concrete gaps, whose success criteria re-state the *original* bar (its review-result then re-checks the whole artifact, not just the delta). Typical for near-misses.
2. **Plan the improvement**: the gap is larger → decompose the fix like any goal (the improvement subtask may itself carry a planning task).
3. **Change course**: the verdict shows the approach — or the plan around it — was wrong → re-plan the remaining course; document the dead branch in the planned goal's `# Notes` so no future planner retries it blind.
4. **Accept and continue** (only for `[!]`): the flagged uncertainty is tolerable → re-load the demoted items and continue; the `[!]` stays in History for the user's eventual confirmation. An `[f]` always demands 1–3 or 5.
5. **Escalate**: a genuinely missing input this level cannot produce → exception for the planned goal (escalates one level up, reaching the user at the launch goal). A call that is genuinely the user's (taste, values, outward-facing/irreversible consequences) but doesn't block drafting the plan → accept, with a `checkpoint:` line in front of the affected steps instead — truly independent steps frontloaded before it (independence rule, vna-plan skill).

## Hard rules

6. **A failed task is never re-run in place.** A retry runs in a **new document** (new name or "… v2"); the old file keeps its `[f]`/failed status forever, as history.
7. Building on a `[!]` task's output is fine; flipping its mark is not yours — that's the user's confirmation via the controller.
8. Disposition every demoted item explicitly (re-load / keep staged / drop with reason); the plan-ending contract applies unchanged.
9. Diagnose before prescribing: read the failed work itself, not only the verdict. The cheapest real fix is often a corrected goal clarification (wrong bar, missing pointer, wrong scope) — that insight belongs in the retry's clarification and the planned goal's `# Notes`.
