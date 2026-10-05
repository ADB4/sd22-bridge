export const meta = {
  name: 'material-review-round',
  description: 'Lens reviewers critique a procedural material from exported maps, adversarial verifiers re-measure every finding (highs first), one re-verify agent takes the high and medium findings a verifier left without a verdict, a lead writes the fix plan, design calls and scorecard',
  whenToUse: 'sd-material-research stage 6: the default panel route (the Agent tool is the fallback)',
  phases: [
    { title: 'Review', detail: 'one reviewer per lens, time-boxed' },
    { title: 'Verify', detail: 'adversarial re-measurement of each lens\'s findings, highs, then mediums, then lows, time-boxed' },
    { title: 'Re-verify', detail: 'one agent for every high or medium finding left without a verdict' },
    { title: 'Synthesize', detail: 'lead: plan, design calls, scorecard, ledger targets' },
  ],
}

// args: pass round<N>/panel_args.json from scripts/make_brief.py (it checks keys, sections and ownership), plus any
// optional arg below.
//   review_dir   absolute path of <tools>/review  (REFERENCE.md lives here; round<N>/ holds the delta BRIEF.md,
//                previews, scorecards, ledger)
//   round        round number (1, 2, ...)
//   lenses       [{key, prompt, sections?, owns?}]   built from the spec (references/review.md §3); key: letters,
//                digits, _ or -, unique ignoring case (the Mac volume folds case, so G1 and g1 would share a file);
//                sections: the REFERENCE.md ids the lens reads besides R1, R5, R9 (all of it when absent or empty);
//                owns: the carried items it owns (ledger ids, last round's unverified/deferred, open questions)
//   max_findings optional, default 7 / 6 / 5 for rounds 1 / 2 / 3+
//   box_lens     optional {min, calls}, default {min: 15, calls: 35}   (RV-03 time boxes; widen box_verify when the
//   box_verify   optional {min, calls}, default {min: 12, calls: 25}    severity-change rate in stats falls)
//   python       optional, the venv python (default: output of setup_env.sh)
//   skill_dir    optional, default ~/.claude/skills/sd-material-research
// Every agent runs at xhigh (no effort tiers); concurrency is the runtime's cap, min(16, CPUs-2).
// Each agent stamps `date -u` first and last and writes one file in round<N>/: <lens>.json (findings),
// <lens>.verdicts.json, reverify.verdicts.json, lead.json. Main can read them while the panel runs.
// Finding status: confirmed; rejected (a verdict says real=false or severity none; `artifact` alone never rejects);
// unverified (no verdict: a high/medium that neither its verifier nor the re-verify agent checked, or a low its verifier
// did not reach; lows are not re-verified).
const A = args || {}
const R = A.round || 1
const DIR = A.review_dir
const MAXF = A.max_findings || (R === 1 ? 7 : R === 2 ? 6 : 5)
const SKILL = A.skill_dir || '~/.claude/skills/sd-material-research'
const PY = A.python || `$(bash ${SKILL}/scripts/setup_env.sh)`
const BOX_LENS = { min: 15, calls: 35, ...(A.box_lens || {}) }
const BOX_VERIFY = { min: 12, calls: 25, ...(A.box_verify || {}) }
const EFFORT = 'xhigh'
const RD = `${DIR}/round${R}`
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const HM = f => f.severity === 'high' || f.severity === 'medium'
const SEV = ['high', 'medium', 'low']
const RANK = f => { const r = SEV.indexOf(f.severity); return r < 0 ? SEV.length : r }

if (!DIR) throw new Error('args.review_dir is required')
const lenses = A.lenses || []
if (!Array.isArray(lenses) || lenses.length === 0) throw new Error('args.lenses must be a non-empty array of {key, prompt}')
const RESERVED = ['lead', 'reverify', 'ledger', 'review_result', 'lenses', 'panel_args']
const seenKeys = new Set()
for (const l of lenses) {
  const k = l && l.key
  const kk = String(k || '').toLowerCase()
  if (!/^[A-Za-z0-9_-]+$/.test(k || '') || RESERVED.includes(kk) || seenKeys.has(kk) || !l.prompt)
    throw new Error(`lens ${JSON.stringify(k)}: needs a prompt and a key of letters, digits, _ or -, unique ignoring case, not ${RESERVED.join(', ')} in any case`)
  seenKeys.add(kk)
  const sid = s => typeof s === 'string' && /^R[1-9][0-9]*$/.test(s)
  if (l.sections != null && (!Array.isArray(l.sections) || !l.sections.every(sid)))
    throw new Error(`lens ${JSON.stringify(k)}: sections must be an array of REFERENCE ids R1, R2, ...`)
  if (l.owns != null && (!Array.isArray(l.owns) || !l.owns.every(o => typeof o === 'string')))
    throw new Error(`lens ${JSON.stringify(k)}: owns must be an array of item ids`)
}

const STAMPS = {
  started: { type: 'string', description: `UTC, from \`${STAMP}\` as your first action` },
  ended: { type: 'string', description: `UTC, from \`${STAMP}\` just before you write your file` },
}

const FINDINGS = {
  type: 'object',
  properties: {
    ...STAMPS,
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
    owned: { type: 'array', description: 'one row per carried item YOU OWN that is not a ledger item', items: { type: 'object', properties: {
      id: { type: 'string' }, outcome: { type: 'string', enum: ['problem', 'resolved', 'not_checked'] },
      finding: { type: 'string', description: 'with outcome problem: the id of your finding on it' }, note: { type: 'string' },
    }, required: ['id', 'outcome', 'note'] } },
    strengths: { type: 'array', items: { type: 'string' } },
    box: { type: 'string', enum: ['not_hit', 'minutes', 'calls'], description: 'the time-box limit that stopped you, if any' },
    not_reached: { type: 'array', items: { type: 'string' }, description: 'parts of your lens brief (areas, cards, regions, variants) you did not review' },
  },
  required: ['started', 'ended', 'findings', 'fix_status', 'strengths', 'box', 'not_reached'],
}

const VERDICTS = {
  type: 'object',
  properties: {
    ...STAMPS,
    verdicts: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      real: { type: 'boolean' },
      reproduced: { type: 'boolean' },
      independent_numbers: { type: 'string', description: 'your own method, script path and numbers' },
      artifact: { type: 'string', enum: ['none', 'preview_shader', 'downsampling', 'metric', 'quantisation'], description: 'what inflated the reviewer\'s numbers, if anything. A finding that is entirely an artifact gets real=false; otherwise keep real=true, correct the numbers and set severity_adjusted. This field alone never rejects a finding' },
      basis: { type: 'string', enum: ['hard_requirement', 'invariant', 'spec_fact', 'realism', 'taste'] },
      premise_errors: { type: 'string' },
      severity_adjusted: { type: 'string', enum: ['high', 'medium', 'low', 'none'] },
      fix_assessment: { type: 'string', enum: ['right', 'partial', 'wrong', 'harmful'] },
      better_fix: { type: 'string' },
      acceptance_fixed: { type: 'string', description: 'reachable target checked against a baseline' },
      reasoning: { type: 'string' },
    }, required: ['id', 'real', 'reproduced', 'independent_numbers', 'artifact', 'basis', 'premise_errors', 'severity_adjusted', 'fix_assessment', 'better_fix', 'acceptance_fixed', 'reasoning'] } },
    not_checked: { type: 'array', items: { type: 'string' }, description: 'ids of findings you did not re-measure with your own script; they get no verdict' },
  },
  required: ['started', 'ended', 'verdicts', 'not_checked'],
}

const PLAN = {
  type: 'object',
  properties: {
    ...STAMPS,
    fixes: { type: 'array', items: { type: 'object', properties: {
      priority: { type: 'integer' }, title: { type: 'string' }, why: { type: 'string' }, change: { type: 'string' },
      variants: { type: 'array', items: { type: 'string' } }, source_ids: { type: 'array', items: { type: 'string' } },
      depends_on: { type: 'array', items: { type: 'integer' } }, acceptance: { type: 'string' }, guard_rails: { type: 'string' },
    }, required: ['priority', 'title', 'why', 'change', 'variants', 'source_ids', 'depends_on', 'acceptance', 'guard_rails'] } },
    design_calls: { type: 'array', description: 'every choice only the user can make; the plan gate asks them in one batch', items: { type: 'object', properties: {
      question: { type: 'string' },
      options: { type: 'array', minItems: 2, maxItems: 4, items: { type: 'object', properties: {
        label: { type: 'string' }, consequence: { type: 'string', description: 'what the material looks or measures like with this option' },
      }, required: ['label', 'consequence'] } },
      recommended: { type: 'string', description: 'label of the recommended option, which is listed first' },
      affects: { type: 'string', description: 'fix priorities, R-ids and variants the answer changes' },
    }, required: ['question', 'options', 'recommended', 'affects'] } },
    spot_checks: { type: 'array', description: 'one row per UNVERIFIED high or medium finding, and per FIX STATUS row marked not_checked (id = its fix)', items: { type: 'object', properties: {
      id: { type: 'string' }, lens: { type: 'string' },
      outcome: { type: 'string', enum: ['confirmed', 'downgraded', 'rejected', 'not_measured', 'landed', 'partial', 'not_landed'] },
      numbers: { type: 'string', description: 'your script and numbers' },
    }, required: ['id', 'lens', 'outcome', 'numbers'] } },
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
  required: ['started', 'ended', 'fixes', 'design_calls', 'spot_checks', 'requirements_scorecard', 'invariants', 'keep_as_is', 'deferred', 'conflicts_resolved', 'premises_corrected', 'overall_assessment'],
}

// RV-05: every agent reads the round's delta brief (it carries REFERENCE R1, R5 and R9: requirements, node cheat sheet,
// rubric and verifier checklist), then the REFERENCE.md sections its REFERENCE SECTIONS line names.
const REF = `${DIR}/REFERENCE.md`
const COMMON = `Read ${RD}/BRIEF.md in full: the round's delta brief (rules; the requirements, node semantics cheat sheet,
severity rubric and verifier checklist, REFERENCE R1, R5 and R9; decisions; scorecard; ledger; carried items; lens table).
Then read the sections of ${REF} your REFERENCE SECTIONS line names (\`sed -n '/^## R4 /,/^## R5 /p'\` prints R4).
If ${RD}/BRIEF.md does not exist (a material reviewed before the delta brief), read ${DIR}/BRIEF.md completely instead
(all rounds up to ${R}; it lists the requirements, physics digest, scale, graph, node semantics, files, scorecard,
history, severity rubric and the verifier checklist) and skip the REFERENCE SECTIONS line.
Round files are in ${RD}/.
Never call substance-designer tools (Designer is single-threaded and reserved for the builder).
Read-only inputs. Helper scripts and images ONLY under ${DIR}/agents/round${R}/<your-label>/; your result file is the one other write.
Python: ${PY}  (numpy, scipy, Pillow, OpenCV). Import ${SKILL}/scripts/matcheck.py (load_image, Ctx, label_wrap)
instead of writing decoders; full-res 16-bit maps are listed in REFERENCE R7 (or the old brief).`
// Lenses read their own sections; verifiers, the re-verify agent and the lead read all of REFERENCE.md (the checklist's
// premise check needs the parameter values in R4).
const ALL_REF = `REFERENCE SECTIONS: all of ${REF}.`
const refLine = l => Array.isArray(l.sections) && l.sections.length
  ? `REFERENCE SECTIONS: ${l.sections.join(', ')} of ${REF} (R1, R5 and R9 are in the delta brief).`
  : ALL_REF
const ownLine = l => !Array.isArray(l.owns) ? '' : `
YOU OWN: ${l.owns.length ? l.owns.join(', ') : 'no carried items'}; carried items another lens owns are theirs: skip them.${l.owns.length ? `
Ledger items you own get a fix_status row; every other item you own gets one owned row: outcome problem (finding = the id
of your finding on it), resolved, or not_checked when you did not reach it.` : ''}`

const filing = file => `STAMPS AND RESULT FILE: your first action is \`${STAMP}\`; that is "started". Your last actions: run it
again for "ended", then write "${file}" as one JSON object, "started" and "ended" first, then every other field you
return. Return that same object.`

const boxed = (b, spent) => `TIME BOX: ${b.min} min and ${b.calls} tool calls from "started". Check \`${STAMP}\` before each new
finding; once the box is spent, ${spent}`

// The verifiers' own method; the re-verify agent uses the same text.
const METHOD = `Apply the verifier checklist in the brief to EACH finding: reproduce at
least one key number with your own script on full-res maps; refute claim by claim (visible? preview shader? downsampling?
metric artifact? wrong premise? basis? controls for statistical claims? does the consequence follow?). Correct overstated
numbers and downgrade rather than reject; real=false only when the core is unsupported. Review each fix (does it create a
singular feature or lattice, a bevel, break an invariant or registration, conflict with a requirement?) and the acceptance
target (reachable on current data, checked against a baseline?). Never guess a verdict: a finding you did not re-measure
with your own script gets no verdict and goes in not_checked.`

phase('Review')
const results = await pipeline(lenses,
  l => agent(`${COMMON}
${refLine(l)}${ownLine(l)}
Be concrete and critical, like a senior material artist reviewing for production. Every finding cites files, coordinates
and numbers, names its cause in the graph, proposes a node/parameter-level fix and an acceptance check. Only report problems
that map to a requirement id, an invariant id or a cited spec fact; say "taste" otherwise. Do not re-report items the brief
lists as rejected or keep-as-is unless they regressed. Return 0-${MAXF} findings, most severe first, with ids ${l.key}-1,
${l.key}-2, ...; fill fix_status for the ledger items your lens covers if the brief has a ledger for this round (else leave it empty);
leave out items outside your lens.
${boxed(BOX_LENS, 'stop measuring and report what you have, most severe first; set box to the limit you hit and list in not_reached every part of your lens brief you did not review; a ledger item of your lens you did not reach gets fix_status not_checked. Inside the box: box not_hit, not_reached empty.')}
${filing(`${RD}/${l.key}.json`)}

LENS ${l.key}: ${l.prompt}`, { label: `review:${l.key}`, phase: 'Review', schema: FINDINGS, effort: EFFORT }),
  async (rev, l) => {
    if (!rev) { log(`lens ${l.key}: returned nothing`); return { rev: null, v: null, sent: [] } }
    const fs = rev.findings || []
    // Verdicts match by id: make ids unique within the lens (keep them when they already are).
    const seen = new Set()
    for (const f of fs) {
      if (seen.has(f.id) || !f.id) {
        const old = f.id; let n = 2
        while (seen.has(`${old || l.key}~${n}`)) n++
        f.id = `${old || l.key}~${n}`
        log(`lens ${l.key}: duplicate or empty id ${JSON.stringify(old)} re-keyed to ${f.id}`)
      }
      seen.add(f.id)
    }
    // Every finding goes to the verifier: highs, then mediums, then lows (stable sort), so the box cuts lows first.
    const sent = [...fs].sort((a, b) => RANK(a) - RANK(b))
    log(`lens ${l.key}: ${fs.length} findings (${fs.filter(HM).length} high/medium) in ${RD}/${l.key}.json`)
    if (sent.length === 0) return { rev, v: null, sent }
    const v = await agent(`${COMMON}
${ALL_REF}
You are the adversarial verifier for lens ${l.key}. Below are all its findings: highs, then mediums, then lows. Work
through them in that order. ${METHOD}
${boxed(BOX_VERIFY, 'stop and return: every finding you did not re-measure goes in not_checked.')}
${filing(`${RD}/${l.key}.verdicts.json`)}

FINDINGS:
${JSON.stringify(sent, null, 1)}`, { label: `verify:${l.key}`, phase: 'Verify', schema: VERDICTS, effort: EFFORT })
    return { rev, v, sent }
  })

// Merge. A finding without a verdict is 'unverified', never 'rejected'.
const merged = [], strengths = [], fixStatus = [], owned = [], dead = [], redo = [], cut = []
lenses.forEach((l, i) => {
  const r = results[i]
  if (!r || !r.rev) { dead.push(`review:${l.key}`); return }
  if (r.sent.length && !r.v) dead.push(`verify:${l.key}`)
  const nr = r.rev.not_reached || []
  if ((r.rev.box && r.rev.box !== 'not_hit') || nr.length) {
    cut.push({ lens: l.key, box: r.rev.box || null, not_reached: nr })
    log(`lens ${l.key}: box ${r.rev.box || '?'}; not reached: ${nr.length ? nr.join('; ') : 'none listed'}`)
  }
  strengths.push(...(r.rev.strengths || []).map(s => `[${l.key}] ${s}`))
  fixStatus.push(...(r.rev.fix_status || []).map(s => ({ lens: l.key, ...s })))
  owned.push(...(r.rev.owned || []).map(s => ({ lens: l.key, ...s })))
  const skipped = new Set((r.v && r.v.not_checked) || [])
  for (const f of r.rev.findings || []) {
    const m = { lens: l.key, ...f, status: 'unverified', verdict: null }
    const v = r.v ? (r.v.verdicts || []).find(x => x.id === f.id) : null
    if (v && !skipped.has(f.id)) { m.verdict = v; m.verified_by = 'verifier' }
    else {
      m.why_unverified = !r.v ? 'verifier died' : skipped.has(f.id) ? 'verifier not_checked (box)' : 'verifier gave no verdict'
      if (v) m.partial_verdict = v
      // SH-01 takes the high and medium ones; a low without a verdict goes to the lead unverified.
      if (HM(f)) redo.push(m)
      else m.why_unverified += '; lows are not re-verified'
    }
    merged.push(m)
  }
})
const lowsLeft = merged.filter(m => !HM(m) && !m.verdict).length
log(`round ${R}: ${merged.length} findings from ${lenses.length - dead.filter(d => d.startsWith('review:')).length} of ${lenses.length} lenses; ${redo.length} high/medium without a verdict go to re-verify; ${lowsLeft} lows without a verdict go to the lead unverified`)

// SH-01: every high/medium a verifier left without a verdict goes to one re-verify agent before the lead.
let reverify = null
if (redo.length) {
  phase('Re-verify')
  const qid = m => `${m.lens}/${m.id}`
  const items = redo.map(m => {
    const { status, verdict, why_unverified, partial_verdict, verified_by, ...f } = m
    return { ...f, id: qid(m) }
  })
  reverify = await agent(`${COMMON}
${ALL_REF}
You are the re-verify agent for round ${R}. Each finding below is high or medium and has no verdict: its lens verifier ran
out of its time box, died, or skipped it. Verify each one as its lens verifier would, and use the ids exactly as given.
${METHOD} There is no time box: re-measure every finding; put one in not_checked only when you cannot measure it at all.
${filing(`${RD}/reverify.verdicts.json`)}

FINDINGS:
${JSON.stringify(items, null, 1)}`, { label: 'reverify', phase: 'Re-verify', schema: VERDICTS, effort: EFFORT })
  if (!reverify) dead.push('reverify')
  // Match by "<lens>/<id>", or by the bare id when it names exactly one finding sent here (and no other one's
  // qualified id); a bare id shared across lenses matches neither.
  const bareOk = m => redo.filter(o => o.id === m.id).length === 1 && !redo.some(o => qid(o) === m.id)
  const names = m => bareOk(m) ? [qid(m), m.id] : [qid(m)]
  const skipped = new Set((reverify && reverify.not_checked) || [])
  for (const m of redo) {
    const vs = reverify ? reverify.verdicts || [] : []
    const v = names(m).map(n => vs.find(x => x.id === n)).find(Boolean) || null
    if (v && !names(m).some(n => skipped.has(n))) {
      m.verdict = { ...v, id: m.id }; m.verified_by = 'reverify'
      delete m.why_unverified; delete m.partial_verdict
    } else m.why_unverified += !reverify ? '; re-verify died' : '; re-verify did not check it'
  }
  log(`re-verify: ${redo.filter(m => m.verdict).length} of ${redo.length} got a verdict`)
}

// `artifact` alone does not reject: verifiers use it to say what inflated a real finding's numbers.
const isRejected = v => v.real === false || v.severity_adjusted === 'none'
for (const m of merged) if (m.verdict) m.status = isRejected(m.verdict) ? 'rejected' : 'confirmed'
const confirmed = merged.filter(m => m.status === 'confirmed')
const unverified = merged.filter(m => m.status === 'unverified')
const rejected = merged.filter(m => m.status === 'rejected').map(m => ({ id: m.id, lens: m.lens, title: m.title, why: m.verdict.reasoning }))
const verifiedHM = merged.filter(m => HM(m) && m.verdict)
const unverifiedHM = unverified.filter(HM)
const stats = {
  findings: merged.length, high_medium: merged.filter(HM).length,
  confirmed: confirmed.length, rejected: rejected.length, unverified: unverified.length,
  unverified_high_medium: unverifiedHM.length, sent_to_reverify: redo.length,
  reverified: merged.filter(m => m.verified_by === 'reverify').length,
  verified_high_medium: verifiedHM.length,
  severity_changed: verifiedHM.filter(m => m.verdict.severity_adjusted !== m.severity).length,
  lenses_boxed: cut.length,
}
log(`round ${R}: ${stats.confirmed} confirmed, ${stats.rejected} rejected, ${stats.unverified} unverified (${stats.unverified_high_medium} high/medium); severity changed on ${stats.severity_changed} of ${stats.verified_high_medium} verified high/medium`)
if (unverifiedHM.length) log(`SIGNAL (RV-03): ${unverifiedHM.length} high/medium reach the lead unverified: ${unverifiedHM.map(m => `${m.lens}/${m.id}`).join(', ')}`)
const deadLenses = dead.filter(d => d.startsWith('review:')).map(d => d.slice(7))

phase('Synthesize')
const plan = await agent(`${COMMON}
${ALL_REF}
You are the lead material artist for round ${R}. Merge duplicates (keep source ids; agreement across lenses = confidence),
re-measure any disputed number yourself, correct wrong premises (Histogram Scan centre = 1 - Position; Blend divide = dst/src),
resolve conflicts with the user's requirements in writing, and order fixes by dependency (layout -> height/structure ->
process masks -> colour -> micro-detail). At most ${R === 1 ? 10 : R === 2 ? 8 : 5} fixes, each with acceptance checks and
guard rails. Fill the requirements scorecard (one row per requirement per variant) and the invariants table from the
current scorecards in the round folder. List keep-as-is, deferred items, conflicts resolved, premises corrected.
UNVERIFIED findings are lens claims that no verifier re-measured: re-measure every high or medium among them yourself
before planning it (one spot_checks row each); plan a low only on numbers you reproduced, else defer it.
REJECTED findings got a verdict of real=false or severity none (why = the verifier's reasoning). Leave them out of the
plan, unless you re-measure one and find the rejection wrong: then plan it and say so in premises_corrected.
A FIX STATUS row marked not_checked is one a boxed lens never reached: unless another lens reported that fix, read its
measured after value in ${RD}/ledger.json (or re-measure it) and add a spot_checks row (id = its fix, outcome landed,
partial or not_landed).
Every carried item in the brief that is not a ledger item (last round's deferred and unverified items, open questions)
gets one outcome: planned (its id in a fix's source_ids), re-deferred (a deferred entry that starts with its id, e.g.
"r2:deferred:2: ...") or closed (a keep_as_is or conflicts_resolved entry that starts with its id and gives the reason).
Spot-check an OWNED ITEM REPORTS row marked not_checked before you close its item.
Every choice only the user can make (between looks, a requirement trade, a deviation) goes in design_calls: the question,
2-4 options with the recommended one first, and what the answer changes. Write each fix a call touches for the recommended
option. The plan gate asks every call in one batch; nothing is asked during the apply.
${filing(`${RD}/lead.json`)}

CONFIRMED FINDINGS (with verifier notes):
${JSON.stringify(confirmed, null, 1)}

UNVERIFIED FINDINGS (reason in why_unverified):
${JSON.stringify(unverified, null, 1)}

REJECTED FINDINGS (id, lens, title, why):
${JSON.stringify(rejected, null, 1)}
${deadLenses.length ? `
LENSES THAT RETURNED NOTHING (their areas are unreviewed this round; say so in the overall assessment): ${deadLenses.join(', ')}
` : ''}${cut.length ? `
LENSES CUT BY THE TIME BOX (not_reached areas are unreviewed this round; say so in the overall assessment and do not score them as reviewed):
${JSON.stringify(cut, null, 1)}
` : ''}
FIX STATUS REPORTS:
${JSON.stringify(fixStatus, null, 1)}

OWNED ITEM REPORTS:
${JSON.stringify(owned, null, 1)}

STRENGTHS:
${JSON.stringify(strengths, null, 1)}`, { label: 'synthesize', phase: 'Synthesize', schema: PLAN, effort: EFFORT })
if (!plan) { dead.push('synthesize'); log(`lead returned nothing; the agents' files are in ${RD}`) }
// RV-05 signal: premises the lead had to correct; a rise round over round means a lens's REFERENCE sections were
// cut too far.
stats.premises_corrected = plan && Array.isArray(plan.premises_corrected) ? plan.premises_corrected.length : 0
log(`premises corrected by the lead: ${stats.premises_corrected} (RV-05 signal: compare round over round)`)

// GAP-1: per-agent timing from each agent's own stamps (the same values it wrote into its file).
const parse = s => { try { const t = Date.parse(s); return isFinite(t) ? t : null } catch (e) { return null } }
const timing = []
const row = (agentLabel, o, extra) => {
  const t0 = parse(o && o.started), t1 = parse(o && o.ended)
  timing.push({ agent: agentLabel, started: (o && o.started) || null, ended: (o && o.ended) || null,
    min: t0 !== null && t1 !== null ? Math.round((t1 - t0) / 6000) / 10 : null, ...extra })
}
lenses.forEach((l, i) => {
  const r = results[i]
  row(`review:${l.key}`, r && r.rev, { box: (r && r.rev && r.rev.box) || null })
  if (r && r.sent && r.sent.length) row(`verify:${l.key}`, r.v)
})
if (redo.length) row('reverify', reverify)
row('synthesize', plan)
const starts = timing.map(t => parse(t.started)).filter(t => t !== null)
const ends = timing.map(t => parse(t.ended)).filter(t => t !== null)
const panel_min = starts.length && ends.length ? Math.round((Math.max(...ends) - Math.min(...starts)) / 6000) / 10 : null
log(`timing: ${timing.filter(t => t.min !== null).length} of ${timing.length} agents stamped; panel ${panel_min === null ? '?' : panel_min} min${dead.length ? `; returned nothing: ${dead.join(', ')}` : ''}`)

return { round: R, plan, confirmed, unverified, rejected, fixStatus, owned, stats, timing, panel_min, dead }
