export const meta = {
  name: 'material-fix-drafts',
  description: 'One drafter per plan item writes the fix draft from lead.json, the verdicts and the build scripts; one checker per draft verifies it against the files and fixes it in place; nothing is applied',
  whenToUse: 'sd-material-research: at lead.json (references/review.md section 6 item 4), the plan items\' drafts',
  phases: [
    { title: 'Draft', detail: 'one drafter per plan item, 25 min box' },
    { title: 'Check', detail: 'one checker per draft, 15 min box, pipelined behind its drafter' },
  ],
}

// Purpose: turns the panel's fix plan into one draft per plan item (what to change in which stage script, the probes,
// the acceptance rows, the risks). A draft changes nothing: the main session applies it later, through edits.js or by hand.
// Launched by the skill: at lead.json, in the background (SKILL.md stage 6 and "Delegating while you own Designer").
//
// args (all required; a missing or wrong-typed one returns {error} before any agent):
//   round   the panel round N (positive integer); the plan is <tools>/review/round<N>/lead.json
//   items   the plan item ids, an array of `P<priority>` strings (P1, P2, ...), unique; P<k> is the lead.json `fixes`
//           entry whose `priority` is k (the script cannot read files, so the main session lists them)
//   tools   absolute path of the material's tools folder
//   skill   absolute path of the real skill folder (the realpath, as RUN.json `workflows` was set from)
//   python  absolute path of the numpy python, a literal path (no $ or backticks)
// Outputs, in <tools>/review/drafts/round<N>/: <id>.md (the draft; the checker corrects it in place and appends a
//   "## Checked" section), <id>.checked (one line, a `date -u` stamp, the checker's last act; absent when the checker's
//   box ran out first), and a progress file per agent, draft-<id>.progress.md and check-<id>.progress.md (the agent label
//   draft:<id> with the colon replaced by a hyphen). Returns {round, items: [{id, status, draft, checked, corrections,
//   issues}], dead}: status is checked (the checker finished and named its .checked file), boxed (draft written, check unfinished or unconfirmed), blocked (no draft) or dead.
// Boxes: drafter 25 min, checker 15 min. Agents inherit the session's model and effort. They never call substance-designer
// tools, never edit anything outside their named files and never commit.
const A = args || {}
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const BOX = { draft: 25, check: 15 }

const absPath = v => typeof v === 'string' && /^\/[^\n\r$`'"\\]*[^\n\r$`'"\\/]$/.test(v) && !v.includes('//') && !/\/\.\.(\/|$)/.test(v)
const problems = []
if (!Number.isSafeInteger(A.round) || A.round < 1) problems.push('round must be a positive integer')
if (!Array.isArray(A.items) || A.items.length === 0 || !A.items.every(i => typeof i === 'string' && /^P[1-9][0-9]*$/.test(i)))
  problems.push('items must be a non-empty array of plan ids "P<priority>" (P1, P2, ...)')
else if (new Set(A.items.map(i => i.toLowerCase())).size !== A.items.length) problems.push('items must be unique')
for (const k of ['tools', 'skill', 'python'])
  if (!absPath(A[k])) problems.push(`${k} must be an absolute literal path (no $, quotes or backticks, no trailing slash, no // or .. segment)`)
if (problems.length) return { error: `drafts.js: ${problems.join('; ')}` }

const R = A.round
const TOOLS = A.tools, SKILL = A.skill, PY = A.python
const RD = `${TOOLS}/review/round${R}`
const DD = `${TOOLS}/review/drafts/round${R}`
const prog = (kind, id) => `${DD}/${kind}-${id}.progress.md`

const COMMON = (kind, id) => `Procedural material project (Substance Designer). Tools folder '${TOOLS}': cd there first. Skill folder '${SKILL}'. Numpy python: '${PY}' (read-only measuring only; small scripts that read JSON are fine). Never call substance-designer tools. Never edit anything except your named output files below. Never commit or touch git.
Run \`${STAMP}\` first. After every script run, append a \`date -u\` line and what the run showed to ${prog(kind, id)}. Box: ${BOX[kind]} minutes; at the box, stop, write what is left in the progress file and return what you have.
Round ${R}'s panel (${RD}: BRIEF.md, the lens files <lens>.json and <lens>.verdicts.json, reverify.verdicts.json when present, lead.json) produced a plan, lead.json "fixes" (plan item P<k> is the fix whose "priority" is k) and "design_calls". Drafts stay drafts: they describe the change, they do not apply it, and nothing is copied into build/.
Nobody is asked anything in an unattended run: where a design call decides the item's form (lead.json design_calls whose "affects" names this item's priority, stage or variants), the main path of the draft is the call's "settled" option, and each other option gets its delta in a short "Design-call branches" section.
The draft format (aim at 300 lines or fewer), in this order: line 1 "# <id>: <title>"; line 2 "Files: <the build/ stage scripts the change edits, comma-separated, relative to the tools folder>"; WHY (the merged findings with ids, the verdicts' corrected numbers); CHANGE as exact edits per stage script (file, the node names and parameters as they exist in build/ today: quote the current lines you would change, then the new text or the new node chain); probes and fits it needs (probe-then-choose steps and their rule); rebuild FROM and the exports; ACCEPTANCE (the lead's acceptance mapped to check ids in checks/<config>.json, or to named script rows, or a new soft check with its target and the wrong build that proves it); GUARD ROWS (the fix's lead.json "guards" as {check, variant, bound}, plus intended_lowfreq); TELL (the fix's "tell"); RISKS (hard checks, wrong-build cases, registration, other plan items); ORDER inside the apply (depends_on, shared files with other items); PREMISE CHECK (every place the lead's change text does not match the build as it exists: names, parameters, line quotes).`

const DRAFT_OUT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    status: { type: 'string', enum: ['drafted', 'blocked'], description: 'blocked: no such plan item, or lead.json unreadable; nothing written' },
    file: { type: 'string', description: 'absolute path of the draft written' },
    title: { type: 'string' },
    stages_touched: { type: 'array', items: { type: 'string' } },
    rebuild_from: { type: 'string' },
    acceptance_rows: { type: 'integer' },
    design_calls_used: { type: 'array', items: { type: 'string' }, description: 'the settled labels the main path follows' },
    open_questions: { type: 'array', items: { type: 'string' } },
    started: { type: 'string' },
    ended: { type: 'string' },
  },
  required: ['id', 'status', 'file', 'title', 'stages_touched', 'rebuild_from', 'acceptance_rows', 'open_questions', 'started', 'ended'],
}

const CHECK_OUT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    corrections: { type: 'array', items: { type: 'string' }, description: 'one line per change made to the draft' },
    open_questions: { type: 'array', items: { type: 'string' } },
    boxed: { type: 'boolean', description: 'the box ran out before the check finished; no .checked file written' },
    checked_file: { type: 'string', description: 'absolute path of the .checked file written, "" when none' },
    started: { type: 'string' },
    ended: { type: 'string' },
  },
  required: ['id', 'corrections', 'open_questions', 'boxed', 'checked_file', 'started', 'ended'],
}

const draftPrompt = id => `${COMMON('draft', id)}

You are the drafter for plan item ${id} (lead.json fixes entry with priority ${id.slice(1)}). Your one output file: ${DD}/${id}.md (create the folder if needed; an earlier run's file of that name is overwritten, and so is its stale ${DD}/${id}.checked, which you delete first with \`rm -f ${DD}/${id}.checked\`; your progress file is ${prog('draft', id)}).
Read, in this order: ${RD}/lead.json (this item's fix: change, why, acceptance, guard_rails, tell, guards, intended_lowfreq, depends_on, source_ids; and conflicts_resolved, premises_corrected, spot_checks and design_calls that name it); the source findings' entries in the lens files ${RD}/<lens>.json and their verdict entries in ${RD}/<lens>.verdicts.json and reverify.verdicts.json (better_fix, acceptance_fixed, premise_errors, the corrected numbers); any panel-time pre-draft ${DD}/<lens>-<finding id>.md whose finding is among this item's source_ids (reuse its text where it still holds; it is not yours to edit); ${RD}/BRIEF.md (its "Changed since REFERENCE" section, when it has one, lists the build scripts newer than REFERENCE); ${TOOLS}/review/REFERENCE.md (R4 may be stale: the build scripts and registry.json win); ${TOOLS}/build/ (the stage scripts, read in full where you quote them) and the checks configs ${TOOLS}/checks/*.json. For the sdkit signatures and Designer node semantics see ${SKILL}/scripts/sdkit.py and ${SKILL}/references/sd_craft.md.
Quote current lines from the files as they are now, not from the lead's text. If this item has no fix with that priority in lead.json, write nothing and return status blocked.
Return the summary object only (title, stages touched, rebuild FROM, number of acceptance rows, open questions), never the draft.`

const checkPrompt = (id, sum) => `${COMMON('check', id)}

You are the checker for the draft ${DD}/${id}.md (drafter summary: ${JSON.stringify(sum)}). You may edit that one file, write ${prog('check', id)} and, as your last act, ${DD}/${id}.checked. Check it against ${RD}/lead.json (the fixes entry with priority ${id.slice(1)}), the verdicts and the build scripts: every node name and parameter it says exists today must exist (grep ${TOOLS}/build/ and registry.json); every quoted current line must match the file; every file on the "Files:" line is the set of build/ scripts the change edits; every acceptance check id must exist in its config ${TOOLS}/checks/<config>.json (or be marked new with a target); the lead's guards and intended_lowfreq are listed as guard rows; the design-call "settled" option is the main path and each other option has its delta; the draft's sdkit calls match ${SKILL}/scripts/sdkit.py; nothing in it applies changes.
Start by deleting any stale ${DD}/${id}.checked from an earlier run (\`rm -f ${DD}/${id}.checked\`), so that the file exists only when this check finished. Fix errors in place in the draft and append a "## Checked" section listing what you changed (and "nothing" when you changed nothing). Then, as your last act (after the draft is final), run \`${STAMP} > ${DD}/${id}.checked\`. If your box runs out before the check is complete, do not write the .checked file: say in the progress file what is unchecked and return boxed true.
Return the object only: the corrections you made (one line each), open questions, boxed, the .checked path.`

phase('Draft')
const drafted = {}
const out = await pipeline(A.items,
  async id => { drafted[id] = await agent(draftPrompt(id), { label: `draft:${id}`, phase: 'Draft', schema: DRAFT_OUT }); return drafted[id] },
  (sum, id) => !sum || sum.status !== 'drafted' ? null
    : agent(checkPrompt(id, sum), { label: `check:${id}`, phase: 'Check', schema: CHECK_OUT }))

const dead = []
const items = A.items.map((id, i) => {
  const o = out[i]
  const d = drafted[id]
  if (d && d.status === 'blocked') return { id, status: 'blocked', draft: null, checked: null, corrections: null, issues: ['no such plan item or lead.json unreadable', ...(d.open_questions || [])] }
  if (!o) {
    dead.push(id)
    return { id, status: 'dead', draft: d ? `${DD}/${id}.md` : null, checked: null, corrections: null,
      issues: [d ? 'checker returned nothing: the draft stands unchecked' : 'drafter returned nothing'] }
  }
  const issues = [...(o.open_questions || [])]
  const finished = !o.boxed && typeof o.checked_file === 'string' && o.checked_file !== ''
  if (o.boxed) issues.push('checker box ran out: no .checked file')
  else if (!finished) issues.push('checker reported no .checked file: the check is not confirmed finished')
  return { id, status: finished ? 'checked' : 'boxed', draft: `${DD}/${id}.md`, checked: finished ? o.checked_file : null,
    corrections: (o.corrections || []).length, issues }
})
log(`drafts round ${R}: ${items.filter(x => x.status === 'checked').length} of ${items.length} checked${dead.length ? `; no result: ${dead.join(', ')} (progress files in ${DD})` : ''}`)
return { round: R, items, dead }
