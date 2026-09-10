export const meta = {
  name: 'build-eval-fix',
  description: 'Build an artifact, score it with independent rubric judges + a holistic judge, fix, re-evaluate',
  phases: [
    { title: 'Build', detail: 'one builder agent writes the artifact' },
    { title: 'Evaluate', detail: 'per-dimension rubric judges (multi-trial, median-aggregated) + one holistic judge' },
    { title: 'Fix', detail: 'fixer snapshots, verifies findings by execution, applies its own fixes' },
    { title: 'Finalize', detail: 'restore snapshot if the fix regressed scores; clean up' },
  ],
}

// ============================= CONFIG =============================
// The build-eval-fix-composer agent edits ONLY this block. Harness below is fixed.
// Strings may be template literals; escape literal ` and ${ inside them.
const CONFIG = {
  // 1-2 sentence statement of the goal. Shown to every agent.
  goal: '',

  // Self-contained brief for the builder AND the fixer. Assume the reader has
  // zero conversation context. Must fully convey what success looks like
  // (requirements, constraints, audience, quality bar, expected depth/effort,
  // deliverable format, non-goals) in prose - but not the rubric's scoring
  // mechanics (anchors, weights, check IDs).
  builderBrief: ``,

  // Files agents should read for context/sources (vault-relative or absolute).
  contextPaths: [],

  // Files the builder writes the artifact to. Never empty: every deliverable
  // lives in files (even a "text answer" gets a note), so judge/fixer prompts
  // stay small and results survive the run.
  deliverablePaths: [],

  // Rubric: 3-6 dimensions, each 2-6 checks. A check asserts exactly ONE
  // observable predicate (never "A and B" - split compounds), decidable as
  // pass/fail. Include at least one absence-based check per dimension
  // (penalizing a failure mode: unsupported claims, padding, decorative
  // citations, template-filling). `exec` is an optional shell command that
  // decides or aids the check - set it whenever one can.
  rubric: [
    // {
    //   key: 'accuracy', name: 'Factual accuracy', weight: 2,
    //   anchors: { 1: 'multiple claims wrong or unsupported', 3: 'core claims correct, minor errors', 5: 'all claims verified against sources' },
    //   checks: [
    //     { id: 'A1', desc: 'Every number matches its cited source', exec: null },
    //     { id: 'A2', desc: 'No citation is decorative: each cited source actually supports the sentence it is attached to', exec: null },
    //     { id: 'A3', desc: 'All links resolve', exec: 'grep -oE "https?://[^ )]+" <file>' },
    //   ],
    // },
  ],

  // Brief for the non-rubric common-sense judge: purpose, audience, context.
  // Must NOT restate the rubric dimensions - its value is catching what the
  // rubric misses (and rubric-gaming the rubric judges reward).
  holisticBrief: ``,

  maxFixRounds: 1, // fix->re-evaluate cycles; refinement gains plateau fast, keep <=3
  passScore: 4,    // every dimension AND holistic must reach this (1-5)
  judgeTrials: 1,  // samples per judge per round; >1 = lower-median score + worst-case
                   // check verdicts (single-trial scores are noisy, so pass/revert
                   // gating is less reliable at 1). Set 3 for important runs.
}
// ======================= HARNESS (do not edit) =======================

const CHECK_SCHEMA = {
  type: 'object',
  properties: {
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['pass', 'fail', 'not-checkable'] },
          evidence: { type: 'string', maxLength: 500, description: 'For fail: file + location + what is wrong. For not-checkable: what you tried. For pass: one line on how verified.' },
        },
        required: ['id', 'verdict', 'evidence'],
        additionalProperties: false,
      },
    },
    summary: { type: 'string', maxLength: 600 },
    dimScore: { type: 'integer', minimum: 1, maximum: 5, description: 'Set AFTER completing all check verdicts; must be consistent with them and with the anchors.' },
  },
  required: ['checks', 'summary', 'dimScore'],
  additionalProperties: false,
}

const HOLISTIC_SCHEMA = {
  type: 'object',
  properties: {
    topIssues: {
      type: 'array',
      maxItems: 8,
      items: {
        type: 'object',
        properties: {
          what: { type: 'string', maxLength: 300 },
          where: { type: 'string', maxLength: 120 },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['what', 'where', 'severity'],
        additionalProperties: false,
      },
    },
    summary: { type: 'string', maxLength: 600 },
    dimScore: { type: 'integer', minimum: 1, maximum: 5, description: 'Set AFTER listing issues; must be consistent with them.' },
  },
  required: ['topIssues', 'summary', 'dimScore'],
  additionalProperties: false,
}

const ctx = CONFIG.contextPaths.length
  ? `Context/source files (read as needed): ${CONFIG.contextPaths.join(', ')}`
  : ''

function builderPrompt() {
  return [
    'You are the builder. Your final text is machine-read by an orchestration script - return a compact report, not prose for a human.',
    `GOAL: ${CONFIG.goal}`,
    `BRIEF:\n${CONFIG.builderBrief}`,
    ctx,
    `Write the deliverable to: ${CONFIG.deliverablePaths.join(', ')}`,
    'Then return a build report (<=250 words): key decisions, deviations from the brief and why, known weaknesses or open uncertainties.',
  ].filter(Boolean).join('\n\n')
}

function judgePrompt(dim) {
  return [
    'You are an independent evaluator scoring ONE dimension of an artifact. You have no other context - trust only what you verify yourself.',
    `GOAL of the artifact: ${CONFIG.goal}`,
    `ARTIFACT (read fully): ${CONFIG.deliverablePaths.join(', ')}`,
    ctx,
    `DIMENSION: ${dim.name}\nScore anchors: 1 = ${dim.anchors[1]} | 3 = ${dim.anchors[3]} | 5 = ${dim.anchors[5]}`,
    `CHECKS:\n${dim.checks.map(c => `- [${c.id}] ${c.desc}${c.exec ? ` (verify by running: ${c.exec})` : ''}`).join('\n')}`,
    [
      'Rules:',
      '1. Work check-by-check FIRST: verdict + evidence for every check, THEN set dimScore consistent with those verdicts and the anchors.',
      '2. Any check that can be decided by executing something (run code, resolve links, recompute numbers, count words, compare against sources) MUST be verified that way, never by impression. Use the exec command when given.',
      '3. Verdicts are pass/fail only. If you cannot verify a check either way, use "not-checkable" and say what you tried. If after trying you remain genuinely uncertain, the verdict is fail, not pass.',
      '4. For every non-pass verdict cite concrete evidence: file + location + what is wrong.',
      '5. Do NOT reward length, formatting polish, confident tone, or agreement with the goal framing. Judge substance only - a longer or more assertive artifact is not better.',
      '6. Report defects only - do NOT suggest fixes.',
      '7. Score this dimension only; ignore unrelated flaws.',
    ].join('\n'),
  ].filter(Boolean).join('\n\n')
}

function holisticPrompt() {
  return [
    'You are an independent common-sense judge. You have no rubric and no other context - judge the artifact as a demanding expert reviewer would.',
    `GOAL of the artifact: ${CONFIG.goal}`,
    `ARTIFACT (read fully): ${CONFIG.deliverablePaths.join(', ')}`,
    ctx,
    CONFIG.holisticBrief,
    'Hunt explicitly for: requirements implied by the goal but not obviously covered; missing content; wrong emphasis; whether the artifact is actually usable for its purpose; signs of box-ticking (content that formally satisfies plausible criteria without real substance); anything a thoughtful human reviewer would flag.',
    'Do NOT reward length, formatting polish, or confident tone; judge substance and fitness for purpose only.',
    'List issues FIRST, then score 1-5 consistent with them (5 = a demanding expert would accept it as-is). Cite evidence; do NOT suggest fixes.',
  ].filter(Boolean).join('\n\n')
}

function fixerPrompt(judged, round, priorFixReports) {
  const checkDesc = new Map(CONFIG.rubric.flatMap(d => d.checks.map(c => [c.id, c.desc])))
  const failed = []
  const passing = []
  for (const j of judged) {
    for (const c of j.checks || []) {
      if (c.verdict === 'pass') passing.push(`[${c.id}] ${checkDesc.get(c.id) || ''}`)
      else failed.push({ dim: j.name, id: c.id, check: checkDesc.get(c.id) || '', verdict: c.verdict, evidence: c.evidence })
    }
    for (const t of j.topIssues || []) {
      failed.push({ dim: 'holistic', severity: t.severity, evidence: `${t.where}: ${t.what}` })
    }
  }
  return [
    `You are the fixer (round ${round}). Your final text is machine-read - return a compact report.`,
    `GOAL: ${CONFIG.goal}`,
    `BRIEF:\n${CONFIG.builderBrief}`,
    `ARTIFACT to improve in place: ${CONFIG.deliverablePaths.join(', ')}`,
    ctx,
    `Independent judges found these defects (localized evidence, no scores - they are deliberately withheld):\n${JSON.stringify(failed, null, 1)}`,
    passing.length ? `Checks currently passing - do NOT regress these:\n${passing.join('\n')}` : '',
    priorFixReports && priorFixReports.length
      ? `Reports from earlier fix rounds (you are a fresh agent - use these to avoid re-litigating findings already refuted or re-trying failed approaches):\n${priorFixReports.join('\n---\n')}`
      : '',
    [
      'Rules:',
      `1. FIRST, before any edit, snapshot every deliverable file: cp <file> <file>.r${round}.bak`,
      '2. Verify each finding by execution where possible (run the code, resolve the link, recompute, re-read the cited source) - judges can be wrong. Do NOT act on a finding you cannot independently confirm; list it as unconfirmed instead.',
      '3. Plan your own fixes; the judges deliberately gave no suggestions.',
      '4. Prefer targeted edits over rewrites; do not regress passing checks.',
      '5. Return a change report (<=250 words): findings addressed, findings refuted (and why), findings unconfirmed, remaining known gaps.',
    ].join('\n'),
  ].filter(Boolean).join('\n\n')
}

function lowerMedian(nums) {
  const s = [...nums].sort((a, b) => a - b)
  return s[Math.floor((s.length - 1) / 2)]
}

// Aggregate multiple trials of the same judge: lower-median score,
// worst-case verdict per check (fail > not-checkable > pass).
function aggregateTrials(trials) {
  const score = lowerMedian(trials.map(t => t.dimScore))
  const rank = { pass: 0, 'not-checkable': 1, fail: 2 }
  const byId = new Map()
  for (const t of trials) {
    for (const c of t.checks || []) {
      const cur = byId.get(c.id)
      if (!cur || rank[c.verdict] > rank[cur.verdict]) byId.set(c.id, c)
    }
  }
  const median = trials.find(t => t.dimScore === score) || trials[0]
  return {
    dimScore: score,
    summary: median.summary,
    checks: [...byId.values()],
    topIssues: trials.flatMap(t => t.topIssues || []).slice(0, 8),
  }
}

async function evaluate(round) {
  const ph = `Evaluate r${round}`
  const T = Math.max(1, CONFIG.judgeTrials | 0)
  const units = [
    ...CONFIG.rubric.map(dim => ({ prompt: judgePrompt(dim), schema: CHECK_SCHEMA, key: dim.key, name: dim.name, weight: dim.weight ?? 1 })),
    { prompt: holisticPrompt(), schema: HOLISTIC_SCHEMA, key: 'holistic', name: 'Holistic', weight: 1 },
  ]
  const results = await parallel(units.flatMap((u, i) =>
    Array.from({ length: T }, (_, t) => () =>
      agent(u.prompt, { label: `judge:${u.key} r${round} t${t + 1}`, phase: ph, schema: u.schema })
        .then(r => r && { i, r }))
  ))
  const byUnit = new Map()
  for (const x of results.filter(Boolean)) {
    if (!byUnit.has(x.i)) byUnit.set(x.i, [])
    byUnit.get(x.i).push(x.r)
  }
  const judged = []
  let droppedTrials = 0
  units.forEach((u, i) => {
    const trials = byUnit.get(i) || []
    droppedTrials += T - trials.length
    if (!trials.length) {
      log(`WARNING: all ${T} trial(s) of judge ${u.key} failed - dimension dropped in round ${round}`)
      return
    }
    judged.push({ ...aggregateTrials(trials), key: u.key, name: u.name, weight: u.weight })
  })
  if (droppedTrials > 0) log(`WARNING: ${droppedTrials} judge trial(s) failed in round ${round} - aggregates use surviving trials`)
  return judged
}

const expectedJudges = CONFIG.rubric.length + 1
const passed = judged => judged.length === expectedJudges && judged.every(j => j.dimScore >= CONFIG.passScore)
const total = judged => judged.reduce((s, j) => s + j.dimScore * (j.weight ?? 1), 0)
const scoreTable = judged => judged.map(j => ({ dim: j.key, score: j.dimScore, summary: j.summary }))

// ----- Run -----
if (!CONFIG.goal || !CONFIG.deliverablePaths.length || !CONFIG.rubric.length) {
  throw new Error('CONFIG incomplete: goal, deliverablePaths and rubric are required (this skeleton must be filled by the build-eval-fix-composer agent)')
}

phase('Build')
const buildReport = await agent(builderPrompt(), { label: 'builder', phase: 'Build' })
if (buildReport == null) throw new Error('Builder agent failed - aborting before evaluation')
log('Build complete, starting evaluation')

const roundLog = []
let judged = await evaluate(1)
roundLog.push({ round: 1, total: total(judged), scores: scoreTable(judged) })

let revertedFixRound = null
let fixRoundsRan = 0

for (let r = 1; r <= CONFIG.maxFixRounds; r++) {
  if (passed(judged)) { log('All dimensions at pass threshold - no fix round needed'); break }
  if (budget.total && budget.remaining() < 60_000) { log('Token budget nearly exhausted - stopping fix loop'); break }

  const priorFixReports = roundLog.filter(e => e.fixReport).map(e => e.fixReport)
  const fixReport = await agent(fixerPrompt(judged, r, priorFixReports), { label: `fixer r${r}`, phase: `Fix r${r}` })
  if (fixReport == null) { log(`Fixer round ${r} failed - stopping with last evaluation`); break }
  fixRoundsRan = r

  const next = await evaluate(r + 1)
  // Keep-best acceptance: adopt the revision only if it strictly improves the
  // weighted total (or newly clears the pass bar). Otherwise revert - revisions
  // that don't measurably improve tend to degrade.
  const adopt = total(next) > total(judged) || (passed(next) && !passed(judged))
  roundLog.push({ round: r + 1, total: total(next), scores: scoreTable(next), adopted: adopt, fixReport: String(fixReport).slice(0, 1200) })
  if (!adopt) {
    revertedFixRound = r
    log(`Fix round ${r} did not strictly improve (${total(judged)} -> ${total(next)}) - reverting to pre-fix snapshot`)
    break
  }
  judged = next
}

if (fixRoundsRan > 0) {
  const files = CONFIG.deliverablePaths.join(', ')
  const inst = revertedFixRound
    ? `A fix attempt was rejected by evaluation. For each of these files: ${files} - restore it from its snapshot <file>.r${revertedFixRound}.bak (overwrite the current version), then delete ALL <file>.r*.bak snapshots for these files. Return one line per action taken.`
    : `Fix rounds were accepted. Delete ALL <file>.r*.bak snapshot files belonging to these files: ${files}. Do NOT modify the deliverables themselves. Return one line per deletion.`
  await agent(inst, { label: 'finalize snapshots', phase: 'Finalize', effort: 'low' })
}

const openIssues = judged
  .flatMap(j => [
    ...(j.checks || []).filter(c => c.verdict !== 'pass')
      .map(c => ({ dim: j.key, id: c.id, verdict: c.verdict, evidence: c.evidence })),
    ...(j.topIssues || []).map(t => ({ dim: 'holistic', severity: t.severity, evidence: `${t.where}: ${t.what}` })),
  ])
const shownIssues = openIssues.slice(0, 20)

return {
  deliverable: CONFIG.deliverablePaths,
  passed: passed(judged),
  passScore: CONFIG.passScore,
  rounds: roundLog,
  revertedFixRound,
  buildReport: String(buildReport).slice(0, 1200),
  openIssues: shownIssues,
  openIssuesTruncated: openIssues.length - shownIssues.length,
}
