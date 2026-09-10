export const meta = {
  name: 'vna-execute-review',
  description: 'VNA execute↔review: executor → fresh-context review, fix rounds until final verdict',
  whenToUse: 'Run by the VNA controller on one task file. args: {taskFile, parentGoal, maxRounds? (default 2), model?, extraPointers?}',
  phases: [
    { title: 'Execute', detail: 'executor works the task file; fix rounds land here too' },
    { title: 'Review', detail: 'fresh-context review each round; the final verdict sets mark decision + status' },
  ],
}

// Stage instructions live in the vna-executor / vna-reviewer skills, preloaded by the agent types.

let A = args
if (typeof A === 'string') {
  try { A = JSON.parse(A) } catch (e) { /* fall through to the guard below */ }
}
if (!A || !A.taskFile) {
  throw new Error(`args required: {taskFile, parentGoal?, maxRounds? (default 2), extraPointers?} — received (${typeof args}): ${String(JSON.stringify(args)).slice(0, 200)}`)
}
const MAX = Math.max(1, A.maxRounds ?? 2)
const parentGoal = A.parentGoal || 'none (root goal — derive context from the task file itself)'
const modelOpt = A.model ? { model: A.model } : {}
const ctx = `Task file: ${A.taskFile}
Parent goal: ${parentGoal}
Extra pointers: ${A.extraPointers || 'none'}`

const EXEC = {
  type: 'object',
  properties: {
    status: { enum: ['done', 'exception'] },
    note: { type: 'string', description: 'a few sentences of pointers; the substance lives in the task file' },
  },
  required: ['status', 'note'],
}
const REVIEW = {
  type: 'object',
  properties: {
    decision: { enum: ['fix-round', 'done', 'review', 'on-hold', 'failed'] },
    note: { type: 'string' },
  },
  required: ['decision', 'note'],
}
const REVIEW_FINAL = {
  type: 'object',
  properties: {
    decision: { enum: ['done', 'review', 'on-hold', 'failed'] },
    note: { type: 'string' },
  },
  required: ['decision', 'note'],
}

const first = await agent(ctx, {
  agentType: 'vna-executor-agent', effort: 'max', phase: 'Execute', label: 'execute', schema: EXEC, ...modelOpt,
})
if (!first) throw new Error('executor returned no result')
log(`execute: ${first.status} — ${first.note}`)
if (first.status === 'exception') return { outcome: 'exception', reviewRounds: 0, note: first.note }

for (let round = 1; round <= MAX; round++) {
  const final = round === MAX
  const r = await agent(
    `Review round ${round} of max_rounds ${MAX}${final ? ' — final round: requesting another fix round is not available; issue the final verdict' : ''}.
${ctx}`,
    { agentType: 'vna-reviewer-agent', effort: 'high', phase: 'Review', label: `review ${round}`, schema: final ? REVIEW_FINAL : REVIEW, ...modelOpt },
  )
  if (!r) throw new Error(`review round ${round} returned no result`)
  log(`review round ${round}: ${r.decision} — ${r.note}`)
  if (r.decision !== 'fix-round') return { outcome: r.decision, reviewRounds: round, note: r.note }
  const fix = await agent(
    `Fix round ${round + 1}: a reviewer requested fixes — see \`# Verdict round ${round}\` at the top of your task file.
${ctx}`,
    { agentType: 'vna-executor-agent', effort: 'max', phase: 'Execute', label: `fix ${round + 1}`, schema: EXEC, ...modelOpt },
  )
  if (!fix) throw new Error(`fix round ${round + 1} returned no result`)
  log(`fix round ${round + 1}: ${fix.status} — ${fix.note}`)
  if (fix.status === 'exception') return { outcome: 'exception', reviewRounds: round, note: fix.note }
}
throw new Error('unreachable: final review round must return a final verdict')
