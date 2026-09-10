export const meta = {
  name: 'vna-skill-load-test',
  description: 'Diagnostic: verify the vna-planning workflow agent types preload their skills (no real VNA work)',
  whenToUse: 'Re-run after editing vna skills or agent definitions (defs/skills snapshot at workflow launch — edits never affect an already-running workflow). Default: the 3 planning-workflow agent types (plan/plan-review/plan-write); args {all: true} adds vna-executor-agent + vna-reviewer-agent.',
  phases: [
    { title: 'Probe', detail: 'one no-tools probe per agent type' },
    { title: 'Verify', detail: 'diff the probes’ quotes against the SKILL.md files' },
  ],
}

const PROBE_SCHEMA = {
  type: 'object',
  properties: {
    skillsFullyLoaded: { type: 'array', items: { type: 'string' }, description: 'names of skills whose FULL body text is in context' },
    loadOrder: { type: 'string', description: 'order the skill bodies appear in context' },
    quoteA: { type: 'string' },
    quoteB: { type: 'string' },
    usedTools: { type: 'boolean' },
    whereInContext: { type: 'string', description: 'system prompt / first user message / system-reminder / not present' },
  },
  required: ['skillsFullyLoaded', 'loadOrder', 'quoteA', 'quoteB', 'usedTools', 'whereInContext'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    failures: { type: 'array', items: { type: 'object', properties: { agentType: { type: 'string' }, issue: { type: 'string' } }, required: ['agentType', 'issue'] } },
  },
  required: ['pass', 'failures'],
}

const probe = (t) => `DIAGNOSTIC PROBE — this is a test of skill preloading, NOT a real VNA run. Do NOT do any VNA work. Do NOT use ANY tools (no Read, no Bash, no Grep, no Glob, no Skill — nothing; tool use invalidates the test). Answer purely from what is already in your context window right now, then return the structured output.

Report:
1. skillsFullyLoaded: names of all skills whose FULL SKILL.md body text (the actual instructions) is present in your context — not merely a name+description entry in an available-skills list.
2. loadOrder: the order those skill bodies appear in${t.skills.length > 1 ? `, and explicitly whether they appear in this exact order: ${t.skills.join(' → ')}` : ''}.
3. quoteA: ${t.qa} Copy it character-for-character from your context. Return an empty string if that text is not in your context.
4. quoteB: ${t.qb} Copy character-for-character. Empty string if not present.
5. usedTools: true iff you used any tool while producing this answer (must be false — if you are tempted to read a file, don't; report absence instead).
6. whereInContext: where the skill bodies sit (system prompt / first user message / a system-reminder attachment / not present).`

// The 3 agent types the vna-planning workflow spawns — the default scope of this test.
const PLANNING = [
  {
    type: 'vna-plan-agent', skills: ['vna-planning-shared', 'vna-plan'],
    qa: 'the verbatim full text of numbered item 1 under the "Two hard rules" heading of the vna-planning-shared skill.', qaFile: 'vna-planning-shared',
    qb: 'the verbatim body of the "## Return" section of the vna-plan skill.', qbFile: 'vna-plan',
  },
  {
    type: 'vna-plan-review-agent', skills: ['vna-planning-shared', 'vna-plan-review'],
    qa: 'the verbatim full text of numbered item 1 under the "Two hard rules" heading of the vna-planning-shared skill.', qaFile: 'vna-planning-shared',
    qb: 'the verbatim body of the "## Return" section of the vna-plan-review skill.', qbFile: 'vna-plan-review',
  },
  {
    type: 'vna-plan-write-agent', skills: ['vna-planning-shared', 'vna-plan-write'],
    qa: 'the verbatim full text of numbered item 1 under the "Two hard rules" heading of the vna-planning-shared skill.', qaFile: 'vna-planning-shared',
    qb: 'the verbatim body of the "## Return" section of the vna-plan-write skill.', qbFile: 'vna-plan-write',
  },
]
// Not part of the planning workflow — probed only with args {all: true}.
const EXTRAS = [
  {
    type: 'vna-executor-agent', skills: ['vna-executor'],
    qa: 'the verbatim first paragraph immediately after the top-level "# " title heading of the vna-executor skill body.', qaFile: 'vna-executor',
    qb: 'the verbatim full text of numbered item 1 under the "## Exceptions" heading of the vna-executor skill.', qbFile: 'vna-executor',
  },
  {
    type: 'vna-reviewer-agent', skills: ['vna-reviewer'],
    qa: 'the verbatim first paragraph immediately after the top-level "# " title heading of the vna-reviewer skill body.', qaFile: 'vna-reviewer',
    qb: 'the verbatim body of the "## Return" section of the vna-reviewer skill.', qbFile: 'vna-reviewer',
  },
]

const ARGS = typeof args === 'string' ? JSON.parse(args) : (args || {})   // args may arrive object OR JSON string
const targets = ARGS.all ? PLANNING.concat(EXTRAS) : PLANNING

phase('Probe')
// Barrier justified: the single verifier needs all probe results together.
const probes = await parallel(targets.map(t => () =>
  agent(probe(t), { agentType: t.type, label: `probe:${t.type}`, phase: 'Probe', schema: PROBE_SCHEMA, effort: 'low' })
    .then(r => ({ agentType: t.type, expectedSkills: t.skills, quoteAFile: t.qaFile, quoteBFile: t.qbFile, result: r }))
))

phase('Verify')
const verdict = await agent(`Verify skill-preloading probe results against the actual skill files (ground truth).

Probe results (one per agent type):
${JSON.stringify(probes, null, 2)}

For each probe (skip null entries, but report a failure "probe returned null" for them — count nulls by comparing against the expected agent types listed above):
1. result.skillsFullyLoaded must include every name in expectedSkills.
2. result.usedTools must be false.
3. result.quoteA must appear as a contiguous substring of .claude/skills/<quoteAFile>/SKILL.md, and result.quoteB of .claude/skills/<quoteBFile>/SKILL.md — read the files and check; whitespace-normalize both sides (collapse runs of whitespace to single spaces) before matching. Empty quotes are failures.
4. Where expectedSkills has more than 1 entry, result.loadOrder must affirm the bodies appear in exactly the expectedSkills order.
5. result.whereInContext must not be "not present".

Return pass=true only if every check passes for every probe; list each failed check in failures with its agentType and a one-line issue.`,
  { label: 'verify', phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'low' })

if (!verdict) throw new Error('verifier returned no result')
return { pass: verdict.pass, failures: verdict.failures, probes }
