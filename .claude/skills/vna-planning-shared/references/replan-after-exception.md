# Exception-resolution planning

Covers two triggers: `exception on <path>` (the main body below) and `wait on <path>` (the Waits section at the end).

A child of the planned goal raised `# Exception` — its line sits `[?]` in Loaded — and the controller front-queued this planning task to deal with it. Exceptions are resolved **through planning**, not user-review, by default: the first duty is to genuinely try to resolve it at this level. The workflow runs normally (plan → plan-review → write); the "plan" is often a short resolution memo plus the restored queue.

Extra inputs: the excepted file's `# Exception` and partial work (its state is described there), its `# Goal clarification`, the planned goal's parent (the answer often sits one level up), the [[VNA-exceptions-log]] entry.

## Resolution moves — try hard before escalating

1. **Answer it**: the missing information exists in the tree/vault or is derivable — derive it, record the rationale.
2. **Make the call**: the needed decision lies within this goal's authority — make it and record why. Ordinary uncertainty is decided and recorded, not escalated.
3. **Fix the task setup**: the task was ill-posed → correct its `# Goal clarification` in place (the task resumes in the same document), add missing pointers, adjust scope.
4. **Restructure around it**: the exception rightly showed the task was misguided → plan a different continuation; the task gets cancelled. A differently-framed replacement counts as a retry → **new document**, old one cancelled as superseded.

## Install shape (write agent)

5. Append `## Resolution` under the excepted file's `# Exception`: the answer/decision, rationale, date, and what was changed where. Adjust its `# Goal clarification` if the fix reframed the task (move 3). (Writing into the excepted child is part of the sanctioned write surface on this trigger — vna-plan-write skill.)
6. Queue order: the resumed task runs first — flip its `[?]` line back to `[ ]` yourself and clear its file's `status`; then re-loaded demoted items per disposition; then the contract-mandated queue tail. The resumed task runs again and ends in whatever state its reviewer then assigns.
7. Apply the disposition yourself — resume: the flip in pt 6 · cancel: `[-]` → History + status `cancelled` · replace: new document, old one cancelled as superseded — and still return `exceptedTaskDisposition`: `resume` | `cancel` | `replace` (name the replacement file in `newFiles`); the controller completes the exceptions-log entry.

## Escalation

8. Only when the resolution needs information or a decision this level genuinely cannot produce: decision = exception **for the planned goal** — `# Exception` at its top, referencing the child's exception, with numbered questions and answer slots, plus a frontload list (may be empty): truly independent items — doable without drawback whatever the answer (independence rule) — that keep running ahead of the `[?]` meanwhile. It moves exactly **one level up** once those drain (that level gets its own planning chance; never jump straight to the user — at the controller's launch goal it becomes user-facing questions on its own). The child's `[?]` line stays in Loaded meanwhile.
9. Never except the planning task itself: by the final review round the decision must be one of moves 1–4 or 8.

## Waits without `# Exception` (trigger `wait on <path>`)

10. The `[?]` child carries no `# Exception`: it is **on hold waiting on the user** — blocked at an unanswered `checkpoint:` line (first open item in its Loaded), or a reviewer's blocking-step verdict (`# Verdict → ## Blocking step`: only a genuine user-step remains). Read that checkpoint line / verdict as your trigger input instead.
11. The resolution moves don't apply — nothing is resolvable at any level: the user must answer or act. Never answer a checkpoint yourself (checkpoints exist precisely because the call is the user's); on their answer the controller restores the held line itself — return `exceptedTaskDisposition: null`, write nothing into the held child.
12. The plan's job is purely queue shape (independence rule): frontload the truly independent items — doable without drawback whatever the user's answer — ahead of the `[?]`; disposition every demoted item (re-load behind the `[?]` / keep staged / drop, with reason); contract tail applies. Install nothing you can't justify as independent — in doubt, behind the `[?]`. Frontloading nothing is a legitimate outcome: the level then drains and the controller escalates the wait one level up (no log entry).
