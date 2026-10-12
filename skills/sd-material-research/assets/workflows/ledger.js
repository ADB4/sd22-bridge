export const meta = {
  name: 'material-ledger-rows',
  description: 'Write each apply item\'s ledger row (change, note, misses, status) from the measured numbers, verify every number and the status rule against the scorecards, then merge the verified rows into ledger.json',
  whenToUse: 'sd-material-research stage 7: after the last batch\'s targeted set and fixcheck --fill after; ends before the final fixcheck',
  phases: [
    { title: 'Write', detail: 'one writer per item, 20 min box' },
    { title: 'Verify', detail: 'one verifier per row, 15 min box, pipelined behind its writer' },
    { title: 'Merge', detail: 'one agent replaces the rows in ledger.json and runs fixcheck, 10 min box' },
  ],
}

// Purpose: turns the numbers `fixcheck.py --fill` wrote into finished ledger rows. Precondition the main session meets:
// <tools>/review/round<N+1>/ledger.json has every item's rows (acceptance and guard rows) with before, after, target and
// the `fill` provenance from `fixcheck.py --fill before` and `--fill after`. The writers add the prose and the status;
// the verifiers re-read every number; one merge agent (a barrier: one atomic write of one file) puts the verified rows in.
// Launched by the skill: after the last batch's `--fill after`, in the background. The merge agent runs fixcheck against
// the scorecards: if the final gate's export writes scorecards into this same round folder, either start this workflow
// after that export has landed or have the export write elsewhere (a half-written scorecard would be read, and a stale one
// re-measured). The merge agent passes `--scorecards` the folder of the rows' `fill.after` provenance (the scorecards the
// last `--fill after` read) and reports it when a scorecard there is newer than the newest `fill.utc`.
//
// args (all required; a missing or wrong-typed one returns {error} before any agent):
//   round   the apply's ledger round N+1 (integer, 2 or more); the ledger is <tools>/review/round<N+1>/ledger.json
//   items   the ledger item ids to write (strings of letters, digits, _ or -, unique ignoring case, e.g. P3, P3r)
//   tools   absolute path of the material's tools folder
//   skill   absolute path of the real skill folder
//   python  absolute path of the numpy python, a literal path (no $ or backticks)
// Each writer reads the ledger row, the item's draft (<tools>/review/drafts/round<N>/<id>.md; a repair id such as P3r
// uses P3's), the decisions.json rows naming the item, the apply's progress files (review/round<N+1>/apply/**/*.progress.md,
// edit.json beside each item's edits) and the plan (review/round<N>/lead.json). It keeps id, title and every number --fill
// wrote; it writes `change` (nodes, parameters, script as built), `note` (every miss with its cause in one clause, a row two
// items move attributed to both, a reverted item's note starts "reverted:"), `misses` and `status` (done only when every
// target row holds; a user_edit status stays). The verifier re-reads each number from the scorecards named by the row's
// `fill` provenance and the configs, checks the status rule, and writes the corrected row.
// Outputs: <tools>/review/round<N+1>/ledger_rows/<id>.json (the verified row plus `corrections` [strings] and `verified_at`),
//   <label>.progress.md beside them (write-<id>, verify-<id>, merge; the label with the colon replaced by a hyphen), then
//   ledger.json merged structurally: from each verified row only `change`, `status`, `note`, `misses` and, per acceptance
//   row (matched by position, with the same check and variant), a `before`/`after` that the verifier corrected; every
//   other key of the item (title, intended_lowfreq, trades, ...) and of each acceptance row (target, role, bound, tolerance,
//   promote_hard, target_from, fill, ...), `apply`, `decisions`, every other key and every item not in `items` stay as they
//   are, a user_edit status stays; an item whose rows do not line up is skipped with a reason. Written atomically through
//   fixcheck's own ledger reader and writer (number text and layout kept) after a copy to ledger.json.premerge (an existing
//   copy is kept: .premerge.2, ...).
//   The merge agent runs `<python> <skill>/scripts/fixcheck.py --ledger <ledger>` last (it writes the ledger folder's
//   fixcheck/, which the final fixcheck replaces) and reports its exit code and flags.
// An item is merged only when its writer finished (not boxed) with a row of its own id and its verifier finished, named the
// same id and wrote the expected row file; any other outcome lands in `dead` with the reason in the item's issues.
// Returns {round, items: [{id, status, corrections, verified, issues}], dead, merge: {merged, skipped, written, fixcheck_exit, flags}}.
// Boxes: writer 20 min, verifier 15, merge agent 10. Agents inherit the session's model and effort. They never call
// substance-designer tools, never edit anything but the files named for them and never commit.
const A = args || {}
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const BOX = { write: 20, verify: 15, merge: 10 }

const absPath = v => typeof v === 'string' && /^\/[^\n\r$`'"\\]*[^\n\r$`'"\\/]$/.test(v) && !v.includes('//') && !/\/\.\.(\/|$)/.test(v)
const problems = []
if (!Number.isSafeInteger(A.round) || A.round < 2) problems.push('round must be an integer, 2 or more (the apply\'s ledger round N+1)')
if (!Array.isArray(A.items) || A.items.length === 0 || !A.items.every(i => typeof i === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(i)))
  problems.push('items must be a non-empty array of item ids (letters, digits, _ or -)')
else if (new Set(A.items.map(i => i.toLowerCase())).size !== A.items.length) problems.push('items must be unique ignoring case')
for (const k of ['tools', 'skill', 'python'])
  if (!absPath(A[k])) problems.push(`${k} must be an absolute literal path (no $, quotes or backticks, no trailing slash, no // or .. segment)`)
if (problems.length) return { error: `ledger.js: ${problems.join('; ')}` }

const R = A.round
const TOOLS = A.tools, SKILL = A.skill, PY = A.python
const RD = `${TOOLS}/review/round${R}`
const LEDGER = `${RD}/ledger.json`
const ROWS = `${RD}/ledger_rows`
const PLAN = `${TOOLS}/review/round${R - 1}`
const DRAFTS = `${TOOLS}/review/drafts/round${R - 1}`
const prog = label => `${ROWS}/${label}.progress.md`

const COMMON = (kind, label) => `Procedural material project (Substance Designer). Tools folder '${TOOLS}': cd there first. Skill folder '${SKILL}'. Numpy python: '${PY}'. Never call substance-designer tools. Never edit anything except your named output files below. Never commit or touch git. Never run an export or a suite.
Run \`${STAMP}\` first (create ${ROWS} if it does not exist). After every script run, append a \`date -u\` line and what the run showed to ${prog(label)}. Box: ${BOX[kind]} minutes; at the box, stop, write what is left in the progress file and return what you have.
The ledger is ${LEDGER} (references ${SKILL}/references/review.md section 1 step 4; the fields are in the docstring of ${SKILL}/scripts/fixcheck.py). Its items[] rows carry id, title, change, status (done, partial, not_done, or user_edit), note, misses [strings], acceptance [{check, variant, target [lo, hi] (null = open end), before, after, role (target by default, or guard with a "bound"), tolerance, promote_hard, target_from, fill}], and the item-level lists intended_lowfreq and trades (declared exemptions that fixcheck reads). \`fixcheck.py --fill\` wrote the before and after numbers and the \`fill\` provenance on each row: {before: the scorecard folder relative to the tools folder, after: the scorecard path relative to the tools folder, utc, plus target_from "config" on a row whose target the fill took from the config}. Those numbers come from scorecards: scorecard_<variant>.json (results[] with the check id and its value) in that folder, and from the check configs ${TOOLS}/checks/<config>.json.
Row rules:
- Never change a row's check, variant, role, bound, promote_hard, tolerance, target_from or fill, nor the item's id, title, intended_lowfreq or trades, and never add, remove or reorder an acceptance row. Carry every one of those keys through unchanged in the row you return (the merge takes only change, status, note, misses and each row's before and after from it, and skips an item whose rows do not line up with the ledger's). A target or number is changed only by a verifier who finds it differs from the file it names (a correction, listed).
- status: done only when every target row (role absent or "target") meets its target (after inside [lo, hi], null = open end); partial when some do and some do not; not_done when none does. A guard row is not a target: a guard outside its bound goes in the note. A user_edit status stays user_edit. A reverted item is not_done with a note that starts "reverted:".
- note: keep every existing history sentence of the row; add, for each target row that misses, "<check> <variant> <before> -> <after> [<target>]" and its cause in one clause (a predicted miss in the item's draft or the apply order says so); a row that two items move (the same check and variant in another item's acceptance, or named in a draft's conflict list) is attributed to both items; for a status other than done the miss and its cause stand in the note.
- misses: one string per target row that misses, same text as in the note.
- Numbers keep 4 significant digits as --fill wrote them.`

const ROW = {
  type: 'object',
  properties: {
    id: { type: 'string' }, title: { type: 'string' }, change: { type: 'string' },
    status: { type: 'string', enum: ['done', 'partial', 'not_done', 'user_edit'] },
    note: { type: 'string' },
    acceptance: { type: 'array', items: { type: 'object', properties: {
      check: { type: 'string' }, variant: { type: 'string' }, target: {}, before: {}, after: {},
      role: { type: 'string', enum: ['target', 'guard'] }, bound: {}, tolerance: {}, promote_hard: { type: 'boolean' },
      target_from: { type: 'string' }, fill: { type: 'object' } },
      required: ['check', 'variant'] } },
    misses: { type: 'array', items: { type: 'string' } },
    intended_lowfreq: { type: 'array', items: { type: 'string' } },
    trades: { type: 'array', items: { type: 'string' } },
  },
  required: ['id', 'title', 'change', 'status', 'note', 'acceptance', 'misses'],
}
const STAMPS = { started: { type: 'string' }, ended: { type: 'string' } }
const WRITE_OUT = {
  type: 'object',
  properties: { ...STAMPS, row: ROW, boxed: { type: 'boolean' } },
  required: ['started', 'ended', 'row', 'boxed'],
}
const VERIFY_OUT = {
  type: 'object',
  properties: {
    ...STAMPS, id: { type: 'string' },
    corrections: { type: 'array', items: { type: 'string' }, description: 'one line per change to the writer\'s row (number, status, note, attribution); [] if none' },
    status: { type: 'string', enum: ['done', 'partial', 'not_done', 'user_edit'] },
    file: { type: 'string', description: 'the row file written' },
    verified_at: { type: 'string', description: 'the `date -u` stamp written into the row file as verified_at' },
    boxed: { type: 'boolean' },
  },
  required: ['started', 'ended', 'id', 'corrections', 'status', 'file', 'verified_at', 'boxed'],
}
const MERGE_OUT = {
  type: 'object',
  properties: {
    ...STAMPS,
    merged: { type: 'array', items: { type: 'string' } },
    skipped: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, why: { type: 'string' } }, required: ['id', 'why'] } },
    written: { type: 'boolean' },
    fixcheck_exit: { type: 'integer', description: '-1 when fixcheck was not run' },
    flags: { type: 'array', items: { type: 'string' }, description: 'fixcheck\'s flags and its printed summary line' },
  },
  required: ['started', 'ended', 'merged', 'skipped', 'written', 'fixcheck_exit', 'flags'],
}

const writePrompt = id => `${COMMON('write', `write-${id}`)}

You are the ledger writer for item ${id}. Write no file but ${prog(`write-${id}`)} (create ${ROWS} first if it is missing); return the full row.
Read: the ledger row (items[] id ${id}) and its neighbours (other items' rows, to find rows two items move), the ledger's "apply" and "decisions" keys, the item's draft ${DRAFTS}/${id}.md (a repair id such as <id>r uses the draft of <id>; read the lead's fix for it in ${PLAN}/lead.json: fixes entry whose priority matches a P<k> id), ${TOOLS}/review/decisions.json (rows whose "items" include ${id}; skip it when the file does not exist), the apply's progress files and notes under ${RD}/apply/ (*.progress.md, and edits/${id}/edit.json when it exists), and, for the numbers' source, the scorecards the row's fill provenance names and the configs. Write "change": the nodes, parameters and script edits as built (from the build/ scripts and edit.json, not only the draft); where the build differs from the draft, say so. Then note, misses and status by the row rules.
Return {started, ended, row, boxed}: row is the full row JSON (every key of the ledger item including intended_lowfreq and trades, every acceptance row with all its keys, unchanged except as the rules allow). boxed true only when your box ran out before the row was finished.`

const verifyPrompt = (id, w) => `${COMMON('verify', `verify-${id}`)}

You are the ledger verifier for item ${id}. A writer produced the row below. Re-read every acceptance row's number from the scorecard its fill provenance names: \`after\` from the scorecard file given by fill.after, \`before\` from the scorecard folder given by fill.before (scorecard_<variant>.json there); a row with no fill.before (its before was set by \`guards.py rows\`) keeps its before, which is not corrected, and the same holds for a missing fill.after. A mismatch in the last digit that is only rounding is no correction. Check each row's target against the config (target_from "config" means the check's own target), check every check id exists in its variant's config, check the status rule and the attribution rule above, that no history sentence of the existing note was dropped, that every miss is in both note and misses with its cause, and that nothing else changed (id, title, check, variant, role, bound, tolerance, promote_hard, target_from, fill on every acceptance row, the order and number of the acceptance rows, and the item's intended_lowfreq and trades: restore any the writer dropped or altered, listing each in corrections). The merge takes only change, status, note, misses and each row's before and after from your row. Your row replaces the writer's.
Write the corrected full row to ${ROWS}/${id}.json (create the folder if needed), the row's own fields plus "corrections" (an array of strings, [] if none) and "verified_at" (the \`${STAMP}\` stamp you run just before you write). Write nothing else but ${prog(`verify-${id}`)}.
Return {started, ended, id, corrections, status, file, verified_at, boxed}.

ROW:
${JSON.stringify(w.row, null, 1)}`

const mergePrompt = (ready, wanted) => `${COMMON('merge', 'merge')}

You are the merge agent. Verified rows are in ${ROWS}/<id>.json for: ${JSON.stringify(ready)} (each with the verified_at stamp given here; a file whose verified_at differs, or whose "id" is not the file's id, is stale and is skipped, reported in "skipped"). Items asked for in this run: ${JSON.stringify(wanted)}.
The merge is structural, not a replacement of the item by the row: the rows come from language-model writers and may have dropped keys, so only the fields below are taken from a row.
Do:
(1) Copy ${LEDGER} to ${LEDGER}.premerge. Never overwrite an existing .premerge (an earlier merge's pre-merge state): use ${LEDGER}.premerge.2, .3, ... for the first name that is free.
(2) Merge with a short Python script (not by retyping JSON). Read the ledger with fixcheck's reader so that number text and the file's layout survive: sys.path.insert(0, '${SKILL}/scripts'); import fixcheck; led, lay, raw = fixcheck.read_ledger(path, fill=True). Read each row file with json. For each ready item:
  - skip it, with the reason in "skipped", when the ledger has no item with that id (never add one), when the row's "id" or "verified_at" is wrong, or when the row's acceptance list does not line up with the ledger item's: the same number of rows and, at each position, the same check and variant (the sequence of (check, variant) pairs must be equal; a user's reorder or a dropped or added row is a skip, not a repair);
  - otherwise set, on the ledger item, only: change, note, misses (from the row), status (from the row, except that an item whose ledger status is user_edit keeps it), and, for each acceptance position, before and after from the row's row, but only where the row's value differs from the ledger's (compare as numbers; null equals null) so that an unchanged number keeps its original text, e.g. 0.1230. Every other key of the item (id, title, intended_lowfreq, trades, anything else) and of each acceptance row (target, role, bound, tolerance, promote_hard, target_from, fill, anything else) stays exactly as the ledger has it, whatever the row says;
  - never copy "corrections" or "verified_at"; keep the item's position; keep "apply", "decisions", every other top-level key and every item not listed unchanged.
(3) Write the ledger with fixcheck.write_ledger(path, led, lay, raw) (a temp file in the same folder, then os.replace; it keeps the indentation, the line ends, the number text and the trailing newline, and leaves ${LEDGER}.bak). If nothing was merged, write nothing.
(4) Run \`'${PY}' '${SKILL}/scripts/fixcheck.py' --ledger '${LEDGER}' --scorecards <F>\` where <F> is the absolute folder of the scorecards the rows' fill.after provenance names (the folder part of fill.after, relative to '${TOOLS}'; all the rows should share one; when they do not, use the one most rows name and say so in "flags"). Do not pass --rerun. If a scorecard_*.json in <F> is newer than the newest fill.utc in the ledger, add the line "scorecards newer than the last fill: <names>" to "flags" (a final-gate export may be writing there; fixcheck's own freshness rule decides what it re-measures). Report fixcheck's exit code and its flags (read fixcheck/fixcheck.json in the ledger folder: done_not_landed, claim_contradicted, measure_failed, promotion_missing, regression_counts, and the printed summary). Exit 1 is a finding for the main session, not yours to fix: you edit nothing but the ledger, its .premerge copy and ${prog('merge')} (fixcheck writes its own fixcheck/ folder and the ledger.json.bak).
Return {started, ended, merged, skipped, written, fixcheck_exit, flags}.
READY (id: verified_at):
${JSON.stringify(ready)}`

phase('Write')
const rows = {}
const writerOk = (w, id) => !!(w && w.row && w.row.id === id && !w.boxed)
const out = await pipeline(A.items,
  async id => { rows[id] = await agent(writePrompt(id), { label: `write:${id}`, phase: 'Write', schema: WRITE_OUT }); return rows[id] },
  (w, id) => writerOk(w, id) ? agent(verifyPrompt(id, w), { label: `verify:${id}`, phase: 'Verify', schema: VERIFY_OUT }) : null)

const dead = [], ready = {}
const items = A.items.map((id, i) => {
  const w = rows[id], v = out[i]
  let why = null
  if (!w || !w.row) why = 'writer returned nothing'
  else if (w.row.id !== id) why = `writer returned a row for id ${JSON.stringify(w.row.id)}: not verified, not merged`
  else if (w.boxed) why = 'writer box ran out: the partial row is not verified and not merged (run the item again)'
  else if (!v || !v.verified_at) why = 'verifier returned nothing: the writer\'s row is unverified and is not merged'
  else if (v.id !== id || v.file !== `${ROWS}/${id}.json`) why = `verifier returned id ${JSON.stringify(v.id)} and file ${JSON.stringify(v.file)}, expected ${id} and ${ROWS}/${id}.json: the row is not merged`
  else if (v.boxed) why = 'verifier box ran out: the row is not merged'
  if (why) {
    dead.push(id)
    return { id, status: v && v.status ? v.status : null, corrections: v && v.corrections ? v.corrections.length : null, verified: false, issues: [why] }
  }
  ready[id] = v.verified_at
  return { id, status: v.status, corrections: (v.corrections || []).length, verified: true, issues: [] }
})

let merge = null
if (Object.keys(ready).length) {
  phase('Merge')
  merge = await agent(mergePrompt(ready, A.items), { label: 'merge', phase: 'Merge', schema: MERGE_OUT })
  if (!merge) dead.push('merge')
} else log('ledger: no verified row, nothing to merge')
log(`ledger round ${R}: ${Object.keys(ready).length} of ${items.length} rows verified${dead.length ? `; not merged or dead: ${dead.join(', ')}` : ''}${merge ? `; fixcheck exit ${merge.fixcheck_exit}` : ''}`)
return { round: R, items, dead, merge: merge ? { merged: merge.merged, skipped: merge.skipped, written: merge.written, fixcheck_exit: merge.fixcheck_exit, flags: merge.flags } : null }
