export const meta = {
  name: 'material-review-round',
  description: 'Lens reviewers critique a procedural material from exported maps, adversarial verifiers re-measure each list, a lead writes the fix plan and scorecard',
  whenToUse: 'sd-material-research stage 6, when the user has opted into workflows',
  phases: [
    { title: 'Review', detail: 'one reviewer per lens' },
    { title: 'Verify', detail: 'adversarial re-measurement per lens' },
    { title: 'Synthesize', detail: 'lead: plan, scorecard, ledger targets' },
  ],
}

// args:
//   review_dir   absolute path of <tools>/review  (BRIEF.md lives here; round<N>/ holds previews, scorecards, ledger)
//   round        round number (1, 2, ...)
//   lenses       [{key, prompt}]   built from the spec (references/review.md §3)
//   max_findings optional, default 7 / 6 / 5 for rounds 1 / 2 / 3+
//   python       optional, the venv python (default: output of setup_env.sh)
//   skill_dir    optional, default ~/.claude/skills/sd-material-research
const A = args
const R = A.round || 1
const DIR = A.review_dir
const MAXF = A.max_findings || (R === 1 ? 7 : R === 2 ? 6 : 5)
const SKILL = A.skill_dir || '~/.claude/skills/sd-material-research'
const PY = A.python || `$(bash ${SKILL}/scripts/setup_env.sh)`

const FINDINGS = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      title: { type: 'string' },
      severity: { type: 'string', enum: ['high', 'medium', 'low'] },
      category: { type: 'string', description: 'fin_or_moat, registration, aliasing, shape_vocabulary, false_correlation, decal_albedo, deposit_band, tiling_landmark, uniform_statistics, wrong_scale, cad_layout, step_discontinuity, calibration, variant_collapse, pbr_range, invariant_breach, other' },
      requirement_ids: { type: 'array', items: { type: 'string' } },
      invariant_ids: { type: 'array', items: { type: 'string' } },
      variants: { type: 'array', items: { type: 'string' } },
      visible_at: { type: 'string', enum: ['zoom', '1:1', 'tile', 'tiled'] },
      evidence: { type: 'string', description: 'files, coordinates, and numbers with the script that produced them' },
      cause: { type: 'string', description: 'graph nodes / parameters that cause it' },
      proposed_fix: { type: 'string', description: 'node/parameter-level change' },
      acceptance: { type: 'string', description: 'check id or script + target that proves the fix' },
    }, required: ['id', 'title', 'severity', 'category', 'requirement_ids', 'invariant_ids', 'variants', 'visible_at', 'evidence', 'cause', 'proposed_fix', 'acceptance'] } },
    fix_status: { type: 'array', items: { type: 'object', properties: {
      fix: { type: 'string' }, status: { type: 'string', enum: ['landed', 'partial', 'not_landed', 'regressed', 'not_checked'] }, note: { type: 'string' },
    }, required: ['fix', 'status', 'note'] } },
    strengths: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'fix_status', 'strengths'],
}

const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      real: { type: 'boolean' },
      reproduced: { type: 'boolean' },
      independent_numbers: { type: 'string', description: 'your own method, script path and numbers' },
      artifact: { type: 'string', enum: ['none', 'preview_shader', 'downsampling', 'metric', 'quantisation'] },
      basis: { type: 'string', enum: ['hard_requirement', 'invariant', 'spec_fact', 'realism', 'taste'] },
      premise_errors: { type: 'string' },
      severity_adjusted: { type: 'string', enum: ['high', 'medium', 'low', 'none'] },
      fix_assessment: { type: 'string', enum: ['right', 'partial', 'wrong', 'harmful'] },
      better_fix: { type: 'string' },
      acceptance_fixed: { type: 'string', description: 'reachable target checked against a baseline' },
      reasoning: { type: 'string' },
    }, required: ['id', 'real', 'reproduced', 'independent_numbers', 'artifact', 'basis', 'premise_errors', 'severity_adjusted', 'fix_assessment', 'better_fix', 'acceptance_fixed', 'reasoning'] } },
  },
  required: ['verdicts'],
}

const PLAN = {
  type: 'object',
  properties: {
    fixes: { type: 'array', items: { type: 'object', properties: {
      priority: { type: 'integer' }, title: { type: 'string' }, why: { type: 'string' }, change: { type: 'string' },
      variants: { type: 'array', items: { type: 'string' } }, source_ids: { type: 'array', items: { type: 'string' } },
      depends_on: { type: 'array', items: { type: 'integer' } }, acceptance: { type: 'string' }, guard_rails: { type: 'string' },
    }, required: ['priority', 'title', 'why', 'change', 'variants', 'source_ids', 'depends_on', 'acceptance', 'guard_rails'] } },
    requirements_scorecard: { type: 'array', items: { type: 'object', properties: {
      requirement: { type: 'string' }, variant: { type: 'string' }, verdict: { type: 'string', enum: ['met', 'mostly_met', 'not_met'] }, evidence: { type: 'string' },
    }, required: ['requirement', 'variant', 'verdict', 'evidence'] } },
    invariants: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, variant: { type: 'string' }, pass: { type: 'boolean' }, value: { type: 'string' },
    }, required: ['id', 'variant', 'pass', 'value'] } },
    keep_as_is: { type: 'array', items: { type: 'string' } },
    deferred: { type: 'array', items: { type: 'string' } },
    conflicts_resolved: { type: 'array', items: { type: 'string' } },
    premises_corrected: { type: 'array', items: { type: 'string' } },
    overall_assessment: { type: 'string' },
  },
  required: ['fixes', 'requirements_scorecard', 'invariants', 'keep_as_is', 'deferred', 'conflicts_resolved', 'premises_corrected', 'overall_assessment'],
}

const COMMON = `Read ${DIR}/BRIEF.md completely (all rounds up to ${R}); it lists the requirements, physics digest, scale, graph,
node semantics, files, scorecard, history, severity rubric and the verifier checklist. Round files are in ${DIR}/round${R}/.
Never call substance-designer tools (Designer is single-threaded and reserved for the builder).
Read-only inputs. Helper scripts and images ONLY under ${DIR}/agents/round${R}/<your-label>/.
Python: ${PY}  (numpy, scipy, Pillow, OpenCV). Import ${SKILL}/scripts/matcheck.py (load_image, Ctx, label_wrap)
instead of writing decoders; full-res 16-bit maps are listed in the brief.`

const lenses = A.lenses || []
phase('Review')
const results = await pipeline(lenses,
  l => agent(`${COMMON}
Be concrete and critical, like a senior material artist reviewing for production. Every finding cites files, coordinates
and numbers, names its cause in the graph, proposes a node/parameter-level fix and an acceptance check. Only report problems
that map to a requirement id, an invariant id or a cited spec fact; say "taste" otherwise. Do not re-report items the brief
lists as rejected or keep-as-is unless they regressed. Return 0-${MAXF} findings, most severe first; fill fix_status for
every ledger item if the brief has a ledger for this round (else leave it empty).

LENS ${l.key}: ${l.prompt}`, { label: `review:${l.key}`, phase: 'Review', schema: FINDINGS }),
  (rev, l) => {
    if (!rev || !rev.findings || rev.findings.length === 0) return { lens: l.key, rev, verdicts: [] }
    return agent(`${COMMON}
You are the adversarial verifier for lens ${l.key}. Apply the verifier checklist in the brief to EACH finding: reproduce at
least one key number with your own script on full-res maps; refute claim by claim (visible? preview shader? downsampling?
metric artifact? wrong premise? basis? controls for statistical claims? does the consequence follow?). Correct overstated
numbers and downgrade rather than reject; real=false only when the core is unsupported. Review each fix (does it create a
singular feature or lattice, a bevel, break an invariant or registration, conflict with a requirement?) and the acceptance
target (reachable on current data, checked against a baseline?).

FINDINGS:
${JSON.stringify(rev.findings, null, 1)}`, { label: `verify:${l.key}`, phase: 'Verify', schema: VERDICTS })
      .then(v => ({ lens: l.key, rev, verdicts: v ? v.verdicts : [] }))
  })

const merged = [], strengths = [], fixStatus = []
for (const r of results.filter(Boolean)) {
  if (!r.rev) continue
  strengths.push(...(r.rev.strengths || []).map(s => `[${r.lens}] ${s}`))
  fixStatus.push(...(r.rev.fix_status || []).map(s => ({ lens: r.lens, ...s })))
  for (const f of r.rev.findings || []) {
    const v = (r.verdicts || []).find(x => x.id === f.id)
    merged.push({ lens: r.lens, ...f, verdict: v || null })
  }
}
const confirmed = merged.filter(f => f.verdict && f.verdict.real && f.verdict.artifact === 'none' && f.verdict.severity_adjusted !== 'none')
const rejected = merged.filter(f => !confirmed.includes(f)).map(f => ({ id: f.id, lens: f.lens, title: f.title, why: f.verdict ? f.verdict.reasoning : 'no verdict' }))
log(`round ${R}: ${merged.length} findings, ${confirmed.length} confirmed, ${rejected.length} rejected`)

phase('Synthesize')
const plan = await agent(`${COMMON}
You are the lead material artist for round ${R}. Merge duplicates (keep source ids; agreement across lenses = confidence),
re-measure any disputed number yourself, correct wrong premises (Histogram Scan centre = 1 - Position; Blend divide = dst/src),
resolve conflicts with the user's requirements in writing, and order fixes by dependency (layout -> height/structure ->
process masks -> colour -> micro-detail). At most ${R === 1 ? 10 : R === 2 ? 8 : 5} fixes, each with acceptance checks and
guard rails. Fill the requirements scorecard (one row per requirement per variant) and the invariants table from the
current scorecards in the round folder. List keep-as-is, deferred items, conflicts resolved, premises corrected.

CONFIRMED FINDINGS (with verifier notes):
${JSON.stringify(confirmed, null, 1)}

FIX STATUS REPORTS:
${JSON.stringify(fixStatus, null, 1)}

STRENGTHS:
${JSON.stringify(strengths, null, 1)}`, { label: 'synthesize', phase: 'Synthesize', schema: PLAN })

return { round: R, plan, confirmed, rejected, fixStatus }
