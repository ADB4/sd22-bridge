export const meta = {
  name: 'material-fix-drafts',
  description: 'One drafter per plan item writes the fix draft from lead.json, the round ledger, the verdicts and the build scripts; one checker per draft verifies it against the files and fixes it in place; items that depend on others wait for their .checked results; nothing is applied',
  whenToUse: 'sd-material-research: at lead.json (references/review.md section 6 item 4), the plan items\' drafts',
  phases: [
    { title: 'Draft', detail: 'one drafter per plan item, 25 min box; a dependent item starts once the items it depends on are checked' },
    { title: 'Check', detail: 'one checker per draft, 15 min box, pipelined behind its drafter' },
  ],
}

// Purpose: turns the panel's fix plan into one draft per plan item (what to change in which stage script, the probes,
// the acceptance rows, the risks). A draft changes nothing: the main session applies it later, through edits.js or by hand.
// Launched by the skill: at lead.json, in the background (SKILL.md stage 6 and "Delegating while you own Designer").
//
// args (all required; a missing or wrong-typed one returns {error} before any agent):
//   round   the panel round N (positive integer); the plan is <tools>/review/round<N>/lead.json
//   items   the plan items, unique ids ignoring case. Each entry is a `P<priority>` string (P1, P2, ...: no
//           dependencies, so old args still work) or {id: "P<priority>", depends_on: ["P<priority>", ...]}. P<k> is the
//           lead.json `fixes` entry whose `priority` is k (the script cannot read files, so the main session lists them).
//           An item's drafter starts once each item it depends on (when that item is in this run) has its .checked
//           result, and reads that item's draft to reuse its row ids and shared-file line ranges; an item with no
//           dependencies starts at once. A dependency that is not in this run is allowed: its draft is read when the
//           file exists, else its ids are listed as NEW. Error before any agent: a dependency cycle, a depends_on entry
//           that is not a `P<priority>` id, an item depending on itself.
//   tools   absolute path of the material's tools folder
//   skill   absolute path of the real skill folder (the realpath, as RUN.json `workflows` was set from)
//   python  absolute path of the numpy python, a literal path (no $ or backticks)
// Outputs, in <tools>/review/drafts/round<N>/: <id>.md (the draft; the checker corrects it in place and appends a
//   "## Checked" section of at most 12 lines), <id>.checked (one line, a `date -u` stamp, the checker's last act; absent
//   when the checker's box ran out first), and a progress file per agent, draft-<id>.progress.md and check-<id>.progress.md
//   (the agent label draft:<id> with the colon replaced by a hyphen; they carry each MEASURED number with the
//   one-line command that gave it).
// Returns {round, items: [{id, depends_on, status, draft, checked, corrections, n_corrections, issues, lines, over_aim}], dead}:
//   status is checked (the checker finished: it named its .checked file and returned its stamp, which parses and is later
//   than the drafter's `ended`, and the .checked path is the expected one; the drafter and the checker return started/ended as
//   the exact `date -u` stamp), boxed (draft written, check unfinished or unconfirmed), blocked (no draft) or dead.
//   corrections = the checker's strings (at most 8), n_corrections their number; issues = the drafter's and the checker's
//   open_questions, deduplicated; lines = wc -l of the draft at the end of the check (the drafter's count unless the check finished: dead, boxed
//   and unconfirmed rows use it); over_aim = lines > 330 (the limit is 300 lines excluding quoted code blocks, plus the Checked section).
// Boxes: drafter 25 min, checker 15 min. Agents inherit the session's model and effort. They never call substance-designer
// tools, never edit anything outside their named files and never commit.
const A = args || {}
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const BOX = { draft: 25, check: 15 }
const STAMP_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/
// a stamp is YYYY-MM-DDTHH:MM:SSZ and a real date: 2026-02-30 and T24:00:00 parse in V8 but do not round-trip
const stampMs = s => {
  if (typeof s !== 'string' || !STAMP_RE.test(s.trim())) return NaN
  const t = s.trim(), ms = Date.parse(t)
  return Number.isNaN(ms) || new Date(ms).toISOString().slice(0, 19) + 'Z' !== t ? NaN : ms
}

const absPath = v => typeof v === 'string' && /^\/[^\n\r$`'"\\]*[^\n\r$`'"\\/]$/.test(v) && !v.includes('//') && !/\/\.\.(\/|$)/.test(v)
const PLAN_ID = /^P[1-9][0-9]*$/
const problems = []
const ITEMS = []   // normalised {id, depends_on}
if (!Array.isArray(A.items) || A.items.length === 0) problems.push('items must be a non-empty array of plan ids "P<priority>" (P1, P2, ...) or {id, depends_on: [ids]}')
else {
  let shapeOk = true
  for (const e of A.items) {
    const id = typeof e === 'string' ? e : e && typeof e === 'object' && !Array.isArray(e) ? e.id : undefined
    const deps = typeof e === 'string' ? [] : e && typeof e === 'object' && e.depends_on !== undefined ? e.depends_on : []
    if (typeof id !== 'string' || !PLAN_ID.test(id)) { shapeOk = false; problems.push('items must be a non-empty array of plan ids "P<priority>" (P1, P2, ...) or {id, depends_on: [ids]}'); break }
    if (!Array.isArray(deps) || !deps.every(d => typeof d === 'string' && PLAN_ID.test(d))) { shapeOk = false; problems.push(`item ${id}: depends_on must be an array of plan ids "P<priority>"`); break }
    if (deps.some(d => d.toLowerCase() === id.toLowerCase())) { shapeOk = false; problems.push(`item ${id}: depends_on names the item itself`); break }
    ITEMS.push({ id, depends_on: [...new Set(deps)] })
  }
  if (shapeOk) {
    if (new Set(ITEMS.map(i => i.id.toLowerCase())).size !== ITEMS.length) problems.push('items must be unique')
    else {
      // dependency cycle among the items in this run: Kahn's algorithm
      const inRun = new Set(ITEMS.map(i => i.id))
      const left = new Map(ITEMS.map(i => [i.id, new Set(i.depends_on.filter(d => inRun.has(d)))]))
      for (let moved = true; moved && left.size;) {
        moved = false
        for (const [id, ds] of [...left]) if (ds.size === 0) { left.delete(id); for (const o of left.values()) o.delete(id); moved = true }
      }
      if (left.size) problems.push(`items: dependency cycle among ${[...left.keys()].join(', ')}`)
    }
  }
}
if (!Number.isSafeInteger(A.round) || A.round < 1) problems.push('round must be a positive integer')
for (const k of ['tools', 'skill', 'python'])
  if (!absPath(A[k])) problems.push(`${k} must be an absolute literal path (no $, quotes or backticks, no trailing slash, no // or .. segment)`)
if (problems.length) return { error: `drafts.js: ${problems.join('; ')}` }

const R = A.round
const TOOLS = A.tools, SKILL = A.skill, PY = A.python
const RD = `${TOOLS}/review/round${R}`
const DD = `${TOOLS}/review/drafts/round${R}`
const prog = (kind, id) => `${DD}/${kind}-${id}.progress.md`
const IDS = ITEMS.map(i => i.id)

// roots first (stable). Only the agent start order changes: a dependent waits on a promise, not on an agent slot, so
// the sort cannot deadlock a capped pipeline and is not needed for correctness
const ORDER = []
{
  const placed = new Set()
  while (ORDER.length < ITEMS.length)
    for (const it of ITEMS)
      if (!placed.has(it.id) && it.depends_on.every(d => placed.has(d) || !IDS.includes(d))) { placed.add(it.id); ORDER.push(it) }
}

const COMMON = (kind, id) => `Procedural material project (Substance Designer). Tools folder '${TOOLS}': cd there first. Skill folder '${SKILL}'. Numpy python: '${PY}' (read-only measuring only; small scripts that read JSON are fine). Never call substance-designer tools. Never edit anything except your named output files below. Never commit or touch git.
Run \`${STAMP}\` first. After every script run, append a \`date -u\` line and what the run showed to ${prog(kind, id)}; for every number you measure, append a line \`MEASURED <number> <what> :: <the one-line command that gave it>\`. Box: ${BOX[kind]} minutes; at the box, stop, write what is left in the progress file and return what you have.
Round ${R}'s panel (${RD}: BRIEF.md, the lens files <lens>.json and <lens>.verdicts.json, reverify.verdicts.json when present, lead.json, ledger.json when present) produced a plan, lead.json "fixes" (plan item P<k> is the fix whose "priority" is k) and "design_calls". Drafts stay drafts: they describe the change, they do not apply it, and nothing is copied into build/.
Nobody is asked anything in an unattended run: where a design call decides the item's form (lead.json design_calls whose "affects" names this item's priority, stage or variants), the main path of the draft is the call's "settled" option, else its "recommended" option; the heading of the "Design-call branches" section names the key used (for example "Design-call branches (main path = settled)"), and each other option gets its delta in that short section.
Truth: build/*.py is the only truth for what exists and for every quote. When REFERENCE.md, registry.json or a job_*.py names a node, constant or file that build/ lacks, write one line under PREMISE CHECK, and never copy its fitted values into the draft as measured results.
The draft format (limit: 300 lines excluding quoted code blocks, counted with \`awk '/^\`\`\`/{f=!f;next} !f' <draft> | wc -l\` (lines outside \`\`\` fences); over it, move option detail to a one-line pointer), in this order: line 1 "# <id>: <title>"; line 2 "Files: <the build/ stage scripts the change edits, comma-separated, relative to the tools folder>"; WHY (the merged findings with ids, the verdicts' corrected numbers); CHANGE as exact edits per stage script (file, the node names and parameters as they exist in build/ today: quote the current lines you would change, then the new text or the new node chain; a quoted block is contiguous lines copied from \`sed -n a,bp\` with its range written as file:a-b, never a "..." inside a block (quote each run separately), and a block to replace is quoted in full); probes and fits it needs (probe-then-choose steps and their rule); rebuild FROM and the exports; ACCEPTANCE (the lead's acceptance mapped to check ids in checks/<config>.json, or to named script rows, or a new soft check with its target and the wrong build that proves it); GUARD ROWS (the fix's lead.json "guards" as {check, variant, bound}; when the fix has none, one line per row of its "guard_rails", at most 15; and intended_lowfreq only if that key exists); TELL (only when the fix has a "tell"; otherwise omit the section); RISKS (hard checks, wrong-build cases, registration, other plan items); ORDER inside the apply (depends_on, shared files with other items); PREMISE CHECK (every place the lead's change text does not match the build as it exists: names, parameters, line quotes).`

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
    design_calls_used: { type: 'array', items: { type: 'string' }, description: 'the settled (else recommended) labels the main path follows' },
    open_questions: { type: 'array', items: { type: 'string' } },
    lines: { type: 'integer', description: 'wc -l of the draft written (0 when blocked)' },
    started: { type: 'string', description: 'the exact output of the date -u stamp command (YYYY-MM-DDTHH:MM:SSZ), your first run' },
    ended: { type: 'string', description: 'the exact output of the date -u stamp command (YYYY-MM-DDTHH:MM:SSZ), a fresh stamp run immediately before returning' },
  },
  required: ['id', 'status', 'file', 'title', 'stages_touched', 'rebuild_from', 'acceptance_rows', 'open_questions', 'lines', 'started', 'ended'],
}

const CHECK_OUT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    corrections: { type: 'array', items: { type: 'string' }, description: 'one line per change made to the draft' },
    open_questions: { type: 'array', items: { type: 'string' } },
    boxed: { type: 'boolean', description: 'the box ran out before the check finished; no .checked file written' },
    checked_file: { type: 'string', description: 'absolute path of the .checked file written, "" when none' },
    checked_stamp: { type: 'string', description: 'the date -u line written to the .checked file (YYYY-MM-DDTHH:MM:SSZ), "" when none' },
    lines: { type: 'integer', description: 'wc -l of the draft after the check' },
    started: { type: 'string', description: 'the exact output of the date -u stamp command (YYYY-MM-DDTHH:MM:SSZ), your first run' },
    ended: { type: 'string', description: 'the exact output of the date -u stamp command (YYYY-MM-DDTHH:MM:SSZ), a fresh stamp run immediately before returning' },
  },
  required: ['id', 'corrections', 'open_questions', 'boxed', 'checked_file', 'checked_stamp', 'lines', 'started', 'ended'],
}

const depBlock = (id, dstat) => {
  const ds = Object.keys(dstat)
  if (!ds.length) return ''
  return `\nDependencies: item ${id} depends on ${ds.map(d => `${d} (${dstat[d]})`).join(', ')}. Read ${ds.map(d => `${DD}/${d}.md`).join(', ')} for each dependency (a file that is absent: say so in the progress file); reuse its row ids and shared-file line ranges, and list the ones it does not define as NEW. A dependency whose status is not checked may be unreliable: say which of its rows you relied on.`
}

const draftPrompt = (id, dstat) => `${COMMON('draft', id)}

You are the drafter for plan item ${id} (lead.json fixes entry with priority ${id.slice(1)}). Your one output file: ${DD}/${id}.md (create the folder if needed; an earlier run's file of that name is overwritten, and so is its stale ${DD}/${id}.checked, which you delete first with \`rm -f ${DD}/${id}.checked\`; your progress file is ${prog('draft', id)}).
Read, in this order: ${RD}/lead.json (this item's fix: change, why, acceptance, guard_rails, tell, guards, intended_lowfreq, depends_on, source_ids; and conflicts_resolved, premises_corrected, spot_checks and design_calls that name it); the round ledger ${RD}/ledger.json when it exists (rows, notes and CORRECTION lines for this item and its source ids: a CORRECTION overrides lead.json and the verdicts, and you quote its stamp when you rely on it); the source findings' entries in the lens files ${RD}/<lens>.json and their verdict entries in ${RD}/<lens>.verdicts.json and reverify.verdicts.json (better_fix, acceptance_fixed, premise_errors, the corrected numbers); any panel-time pre-draft ${DD}/<lens>-<finding id>.md whose finding is among this item's source_ids (reuse its text where it still holds; it is not yours to edit); ${RD}/BRIEF.md (its "Changed since REFERENCE" section, when it has one, lists the build scripts newer than REFERENCE); ${TOOLS}/review/REFERENCE.md (may be stale: the build scripts win; registry.json is good for node counts only); ${TOOLS}/build/ (the stage scripts, read in full where you quote them) and the checks configs ${TOOLS}/checks/*.json. For the sdkit signatures and Designer node semantics see ${SKILL}/scripts/sdkit.py and ${SKILL}/references/sd_craft.md.
Do not add an edit the lead did not ask for: a defect you find outside the item goes in open_questions.${depBlock(id, dstat)}
Quote current lines from the files as they are now, not from the lead's text. If this item has no fix with that priority in lead.json, write nothing and return status blocked.
Before you return, run \`wc -l ${DD}/${id}.md\` and return that count as lines. Then run \`${STAMP}\` once more as the very last command and return its exact output as ended (started is the exact output of your first \`${STAMP}\`); both must be in the form YYYY-MM-DDTHH:MM:SSZ, copied from the command, never a local time, never the default \`date -u\` format, never a guess: the item is not shown as checked when ended does not parse.
Return the summary object only (title, stages touched, rebuild FROM, number of acceptance rows, open questions, lines, started, ended), never the draft.`

const checkPrompt = (id, sum, dstat) => {
  const n = Number.isInteger(sum.lines) ? sum.lines : null
  const grow = n === null ? 'the file grows by at most 20 lines (base: your own wc -l before the first edit)' : `the file grows by at most 20 lines (the drafter reports ${n} lines when drafted, so it ends at ${n + 20} or fewer; the drafter's count is self-reported, so run \`wc -l ${DD}/${id}.md\` before your first edit and use that count as the base)`
  return `${COMMON('check', id)}

You are the checker for the draft ${DD}/${id}.md (drafter summary: ${JSON.stringify(sum)}). You may edit that one file, write ${prog('check', id)} and, as your last act, ${DD}/${id}.checked. Check it against ${RD}/lead.json (the fixes entry with priority ${id.slice(1)}), ${RD}/ledger.json when it exists (a CORRECTION line overrides lead.json), the verdicts and the build scripts:
- existence: every node name and parameter it says exists today must exist in ${TOOLS}/build/*.py (grep it); registry.json confirms node counts only, and a registry/build mismatch is one line in Checked;
- quotes: for each quoted block run \`sed -n a,bp\` on its range and diff it against the draft; a mismatch is fixed, a "..." inside a block is an error to fix (quote each run separately), and a block to replace is quoted in full;
- every file on the "Files:" line is the set of build/ scripts the change edits, and nothing is edited that the lead did not ask for;
- every acceptance check id must exist in its config ${TOOLS}/checks/<config>.json (or be marked new with a target);
- the lead's guards (else the guard_rails rows, at most 15) and intended_lowfreq (only if the key exists) are listed as guard rows, and a TELL section exists only when the fix has a tell;
- the design-call main path is the "settled" option, else the "recommended" one, the heading of the Design-call branches section names the key used, and each other option has its delta;
- the draft's sdkit calls match ${SKILL}/scripts/sdkit.py; nothing in it applies changes;
- claims: for every sentence with never, only, none, all or every about build/ or the jobs, run the grep that tests it and fix or soften the sentence;
- numbers: for every number the drafter says it measured (the MEASURED lines of ${prog('draft', id)}), re-run the command, or mark the number unverified in Checked;${Object.keys(dstat).length ? `
- dependencies (${Object.keys(dstat).map(d => `${d}: ${dstat[d]}`).join(', ')}): the row ids and shared-file line ranges the draft takes from ${Object.keys(dstat).map(d => `${DD}/${d}.md`).join(', ')} match that file, and the ones it does not find there are marked NEW;` : ''}
- size: the draft stays within 300 lines excluding quoted code blocks (count them as the drafter does: \`awk '/^\`\`\`/{f=!f;next} !f' ${DD}/${id}.md | wc -l\`; the returned lines is the plain wc -l, quoted code included); the "## Checked" section is at most 12 lines and ${grow}.
Start by deleting any stale ${DD}/${id}.checked from an earlier run (\`rm -f ${DD}/${id}.checked\`), so that the file exists only when this check finished. Fix errors in place in the draft and append a "## Checked" section listing what you changed (and "nothing" when you changed nothing). Then, once the draft is final, run \`wc -l ${DD}/${id}.md\` (that is the lines you return) and append its progress line. Then, as your last act that changes the draft or writes a file, run \`${STAMP} > ${DD}/${id}.checked\` and \`cat\` it (these last two commands need no progress line; return the stamp \`cat\` showed as checked_stamp). If your box runs out before the check is complete, do not write the .checked file: say in the progress file what is unchecked and return boxed true.
Return the object only: the corrections you made (one line each), open questions, boxed, the .checked path, checked_stamp (the exact line in the .checked file, "" when none), lines (the wc -l count), started and ended (the exact output of \`${STAMP}\`, YYYY-MM-DDTHH:MM:SSZ; ended is the stamp you returned as checked_stamp).`
}

phase('Draft')
// fin[id] settles with the item's final status once it is out of the pipeline, so a dependent's drafter can start
const fin = {}, finRes = {}
for (const id of IDS) fin[id] = new Promise(r => { finRes[id] = r })
const drafted = {}, checkedBy = {}, finishedBy = {}, depStat = {}
const finishCheck = (id, d, o) => {
  if (!o) return { ok: false, why: 'checker returned nothing' }
  if (o.boxed) return { ok: false, why: 'checker box ran out: no .checked file' }
  if (typeof o.checked_file !== 'string' || o.checked_file === '') return { ok: false, why: 'checker reported no .checked file: the check is not confirmed finished' }
  if (o.checked_file !== `${DD}/${id}.checked`) return { ok: false, why: `checked_file "${o.checked_file}" is not the expected ${DD}/${id}.checked: the check is not confirmed finished` }
  const s = stampMs(o.checked_stamp)
  if (Number.isNaN(s)) return { ok: false, why: `checked_stamp "${o.checked_stamp}" does not parse as YYYY-MM-DDTHH:MM:SSZ: the check is not confirmed finished` }
  const e = stampMs(d && d.ended)
  if (Number.isNaN(e)) return { ok: false, why: `drafter's ended "${d && d.ended}" does not parse: the check cannot be shown to follow the draft` }
  if (!(s > e)) return { ok: false, why: `checked_stamp ${o.checked_stamp} is not later than the drafter's ended ${d.ended}: the check is not confirmed finished` }
  return { ok: true }
}

await pipeline(ORDER,
  async it => {
    const id = it.id
    try {
      const dstat = {}
      for (const d of it.depends_on) dstat[d] = IDS.includes(d) ? await fin[d] : 'not in this run'
      depStat[id] = dstat
      drafted[id] = await agent(draftPrompt(id, dstat), { label: `draft:${id}`, phase: 'Draft', schema: DRAFT_OUT })
    } catch (e) { drafted[id] = null }
    const d = drafted[id]
    if (!d || d.status !== 'drafted') { finRes[id](d ? 'blocked' : 'dead'); return null }
    return d
  },
  async (sum, it) => {
    const id = it.id
    if (!sum || sum.status !== 'drafted') return null
    let status = 'dead'   // settles fin[id] whatever happens below, so a dependent never hangs
    try {
      try { checkedBy[id] = await agent(checkPrompt(id, sum, depStat[id] || {}), { label: `check:${id}`, phase: 'Check', schema: CHECK_OUT }) }
      catch (e) { checkedBy[id] = null }
      finishedBy[id] = finishCheck(id, sum, checkedBy[id])
      status = finishedBy[id].ok ? 'checked' : checkedBy[id] ? 'boxed' : 'dead'
    } catch (e) {
      checkedBy[id] = checkedBy[id] || null
      finishedBy[id] = { ok: false, why: 'the check result could not be read' }
    } finally { finRes[id](status) }
    return checkedBy[id]
  })

const dead = []
const dedupe = xs => [...new Set(xs.filter(x => typeof x === 'string' && x !== ''))]
const items = ITEMS.map(it => {
  const id = it.id
  const o = checkedBy[id]
  const d = drafted[id]
  const base = { id, depends_on: it.depends_on }
  if (d && d.status === 'blocked') return { ...base, status: 'blocked', draft: null, checked: null, corrections: null, n_corrections: null,
    issues: dedupe(['no such plan item or lead.json unreadable', ...(d.open_questions || [])]), lines: null, over_aim: null }
  if (!o) {
    dead.push(id)
    const lines = d && Number.isInteger(d.lines) ? d.lines : null
    return { ...base, status: 'dead', draft: d ? `${DD}/${id}.md` : null, checked: null, corrections: null, n_corrections: null,
      issues: dedupe([d ? 'checker returned nothing: the draft stands unchecked' : 'drafter returned nothing', ...(d ? d.open_questions || [] : [])]),
      lines, over_aim: lines === null ? null : lines > 330 }
  }
  const f = finishedBy[id] || { ok: false, why: 'the check result could not be read' }
  const issues = dedupe([...(d.open_questions || []), ...(o.open_questions || []), ...(f.ok ? [] : [f.why])])
  // the checker's count is trusted only when its check finished; a boxed checker may return 0 or an estimate
  const lines = f.ok && Number.isInteger(o.lines) ? o.lines : Number.isInteger(d.lines) ? d.lines : null
  const corr = (o.corrections || []).filter(s => typeof s === 'string')
  return { ...base, status: f.ok ? 'checked' : 'boxed', draft: `${DD}/${id}.md`, checked: f.ok ? o.checked_file : null,
    corrections: corr.slice(0, 8), n_corrections: corr.length, issues, lines, over_aim: lines === null ? null : lines > 330 }
})
const nOver = items.filter(x => x.over_aim).length
log(`drafts round ${R}: ${items.filter(x => x.status === 'checked').length} of ${items.length} checked${nOver ? `; over the line aim: ${items.filter(x => x.over_aim).map(x => `${x.id} (${x.lines})`).join(', ')}` : ''}${dead.length ? `; no result: ${dead.join(', ')} (progress files in ${DD})` : ''}`)
return { round: R, items, dead }
