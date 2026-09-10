export const meta = {
  name: 'vna-planning',
  description: 'VNA planning workflow: plan → plan-review (≤3 rounds, revise↔review) → write',
  whenToUse: 'Run by the VNA controller on a planning task. args: {planningFile, plannedGoal, trigger, extraPointers?}',
  phases: [
    { title: 'Plan', detail: 'draft (and revise) the plan in the planning file' },
    { title: 'Review', detail: 'fresh-context plan review, up to 3 rounds; final decision: accept | exception' },
    { title: 'Write', detail: 'install the accepted plan / write the escalation' },
  ],
}

// Stage instructions: the vna-planning-shared skill (general context, preloaded first)
// + the matching stage skill (vna-plan / vna-plan-review / vna-plan-write), via the agent types below.

let A = args
if (typeof A === 'string') {
  try { A = JSON.parse(A) } catch (e) { /* fall through to the guard below */ }
}
if (!A || !A.planningFile || !A.plannedGoal || !A.trigger) {
  throw new Error('args required: {planningFile, plannedGoal, trigger, extraPointers?} — trigger ∈ "scheduled" (planned step reached in Loaded) | "re-plan after [f] verdict on <path>" | "re-plan after escalated [!] on <path>" | "exception on <path>" | "wait on <path>"')
}

const PLAN = {
  type: 'object',
  properties: {
    status: { const: 'drafted' },
    note: { type: 'string', description: 'one line; substance lives in the planning file' },
  },
  required: ['status', 'note'],
}
const REVIEW = {
  type: 'object',
  properties: {
    decision: { enum: ['revise', 'accept', 'exception'] },
    note: { type: 'string' },
  },
  required: ['decision', 'note'],
}
const REVIEW_FINAL = {
  type: 'object',
  properties: {
    decision: { enum: ['accept', 'exception'] },
    note: { type: 'string' },
  },
  required: ['decision', 'note'],
}
const WRITE = {
  type: 'object',
  properties: {
    outcome: { enum: ['installed', 'exception-raised'] },
    newFiles: { type: 'array', items: { type: 'string' } },
    loadedAdded: { type: 'array', items: { type: 'string' }, description: 'EVERY line added to Loaded, verbatim — link-less lines (checkpoint/write output/review-result) included' },
    goalMoved: { type: ['string', 'null'], description: 'new path if the goal file moved into its own folder, else null' },
    exceptedTaskDisposition: { enum: ['resume', 'cancel', 'replace', null] },
    note: { type: 'string' },
  },
  required: ['outcome', 'newFiles', 'loadedAdded', 'goalMoved', 'exceptedTaskDisposition', 'note'],
}

const stagePrompt = (stage) => `Stage: ${stage}
Planning file: ${A.planningFile}
Planned goal: ${A.plannedGoal}
Trigger: ${A.trigger}
Extra pointers: ${A.extraPointers || 'none'}`

const MAX_ROUNDS = 3

const p = await agent(stagePrompt('plan'), {
  agentType: 'vna-plan-agent', effort: 'max', phase: 'Plan', label: 'plan',
  schema: PLAN,
})
if (!p) throw new Error('plan stage returned no result')

let decision = null
let rounds = 0
for (let round = 1; round <= MAX_ROUNDS; round++) {
  const final = round === MAX_ROUNDS
  const r = await agent(stagePrompt(`plan-review (round ${round}${final ? ', final' : ''})`), {
    agentType: 'vna-plan-review-agent', effort: 'high', phase: 'Review', label: `review ${round}`,
    schema: final ? REVIEW_FINAL : REVIEW,
  })
  if (!r) throw new Error(`plan-review round ${round} returned no result`)
  rounds = round
  decision = r.decision
  log(`review round ${round}: ${decision} — ${r.note}`)
  if (decision !== 'revise') break
  const rev = await agent(stagePrompt(`plan (revision, round ${round})`), {
    agentType: 'vna-plan-agent', effort: 'max', phase: 'Plan', label: `revise ${round}`,
    schema: PLAN,
  })
  if (!rev) throw new Error(`plan revision after round ${round} returned no result`)
}

const w = await agent(stagePrompt(`write (decision: ${decision})`), {
  agentType: 'vna-plan-write-agent', effort: 'max', phase: 'Write', label: 'write',
  schema: WRITE,
})
if (!w) throw new Error('write stage returned no result')

return { decision, reviewRounds: rounds, ...w }
