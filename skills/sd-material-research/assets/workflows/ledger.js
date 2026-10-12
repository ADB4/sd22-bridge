export const meta = {
  name: 'material-ledger-rows',
  description: 'Write each apply item\'s ledger row text (change, note, misses, script_misses, status) from the measured numbers and verify it against the scorecards, one row file per item; the main session merges the verified rows with fixcheck.py --merge-rows',
  whenToUse: 'sd-material-research stage 7: after the last batch\'s targeted set and fixcheck --fill after; ends before the final fixcheck',
  phases: [
    { title: 'Write', detail: 'one writer per item, 20 min box' },
    { title: 'Verify', detail: 'one verifier per row, 15 min box, pipelined behind its writer' },
  ],
}

// Purpose: turns the numbers `fixcheck.py --fill` wrote into the prose of finished ledger rows. Precondition the main
// session meets: <tools>/review/round<N+1>/ledger.json has every item's rows (acceptance and guard rows) with before,
// after, target and the `fill` provenance from `fixcheck.py --fill before` and `--fill after`. The writers add the prose
// and the status; the verifiers re-read every number and write one small row file per item. There is no merge agent: the
// main session runs the returned merge_command (`fixcheck.py --merge-rows`, deterministic, idempotent, a copy to
// ledger.json.premerge first) and then `fixcheck.py --ledger <ledger> --scorecards <the folder of the rows' fill.after
// provenance>` (if the final gate's export writes scorecards into this same round folder, start this workflow after that
// export has landed: a half-written scorecard would be read, and a stale one re-measured).
// Launched by the skill: after the last batch's `--fill after`, in the background.
//
// args (all required; a missing or wrong-typed one returns {error} before any agent):
//   round   the apply's ledger round N+1 (integer, 2 or more); the ledger is <tools>/review/round<N+1>/ledger.json
//   items   the ledger item ids to write (strings of letters, digits, _ or -, unique ignoring case, e.g. P3, P3r)
//   tools   absolute path of the material's tools folder
//   skill   absolute path of the real skill folder
//   python  absolute path of the numpy python, a literal path (no $ or backticks)
// Each writer reads the ledger row, the item's draft (<tools>/review/drafts/round<N>/<id>.md; a repair id such as P3r
// uses P3's), the decisions.json rows naming the item, the apply's progress files (review/round<N+1>/apply/**/*.progress.md,
// edit.json beside each item's edits) and the plan (review/round<N>/lead.json). It returns only the fields it owns, never
// an acceptance row: `change` (nodes, parameters, script as built), `note`, `misses`, `script_misses` and `status`.
//   misses         every existing entry that does not name a (check, variant) of an acceptance row of this item, as
//                  written (except one that is also a script_misses entry and was re-measured: it carries the measured
//                  text, or is dropped from misses when it now holds); plus one entry per acceptance target row that
//                  misses (an existing entry for it is replaced)
//   script_misses  the script-row and ladder misses the note names (suite script rows, ladder rows, watches), each
//                  re-measured from the scorecards or ladder the note names or kept with "not re-measured"; an entry that
//                  holds now stays here with its measured number and leaves misses
//   note           every existing history sentence stays; a miss sentence is added only when the note does not already
//                  carry that (check, variant) with its numbers and cause; at most one paragraph per run, starting
//                  `Ledger pass <stamp>:` with the run's `date -u` stamp; a paragraph that starts `Ledger pass ` plus any
//                  stamp and a colon is an earlier one: it is replaced, not kept beside the new one; no description of the
//                  checking itself
//   status         done only when every acceptance target row holds and script_misses is empty or each entry was
//                  re-measured as holding; not_done when no target row holds (as `fixcheck.py --fill after` sets it);
//                  else partial; user_edit stays; a reverted item is not_done with a note that starts "reverted:"; an item
//                  with no target row, or a target row whose after is null, keeps its status as the ledger has it
// The verifier reads the ledger row itself (every number from the scorecards the row's `fill` provenance names, targets from
// the configs), checks the writer's fields against the same rules and writes the corrected values. A number it finds wrong in
// the ledger is a correction reported, never merged (numbers come from `fixcheck.py --fill`); a target row whose check has no
// target in the current config keeps its target and status and goes to target_mismatches, not into the note.
// Outputs (the verifier deletes an old <id>.json before it writes the new one, so a file that is there was written by this
// run; the status in it is the status it returns): <tools>/review/round<N+1>/ledger_rows/<id>.json = {id, verified_at, change, note, misses, script_misses, status,
//   corrections: [{field, old, new, why}], additions: [string], target_mismatches: [{check, variant, row_target,
//   config_target}]} and <label>.progress.md beside them (write-<id>, verify-<id>; the label with the colon replaced by a
//   hyphen). The ledger itself is not touched by this workflow. `fixcheck.py --merge-rows` sets from a row file only change,
//   note, status, misses and script_misses on the item with that id (a user_edit status stays) and skips an item whose row
//   file is wrong, with the reason; every other key and row of the ledger stays as the ledger has it.
// An item is mergeable only when its writer finished (not boxed) and its verifier finished, named the same id and the
// expected row file; any other outcome lands in `dead` with the reason in the item's issues.
// Returns {round, items: [{id, status, corrections, additions, verified, issues, row_file}], dead, merge_command}:
//   corrections and additions are counts (a correction is a writer value changed, an addition is text the verifier added);
//   a verified item with target_mismatches carries one issues line naming their number and the row file; row_file is
//   the row file (null when not verified); merge_command is the exact `fixcheck.py --ledger L --merge-rows DIR --item ID ...`
//   line for the verified items (null when none), which the main session runs, reading its exit code and its skipped lines,
//   then `fixcheck.py --ledger <ledger> --scorecards <the fill.after folder>`.
// Boxes: writer 20 min, verifier 15. Agents inherit the session's model and effort. They never call substance-designer
// tools, never edit anything but the files named for them and never commit.
const A = args || {}
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const BOX = { write: 20, verify: 15 }

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
Run \`${STAMP}\` first (create ${ROWS} if it does not exist). After every script run, append a \`date -u\` line and what the run showed to ${prog(label)}. Append to a progress file only by its full absolute path, never a relative one: printf '%s\\n' "<line>" >> '${prog(label)}'. Box: ${BOX[kind]} minutes; at the box, stop, write what is left in the progress file and return what you have.
The ledger is ${LEDGER} (references ${SKILL}/references/review.md section 1 step 4; the fields are in the docstring of ${SKILL}/scripts/fixcheck.py). Its items[] rows carry id, title, change, status (done, partial, not_done, or user_edit), note, misses [strings], optionally script_misses [strings], acceptance [{check, variant, target [lo, hi] (null = open end), before, after, role (target by default, or guard with a "bound"), tolerance, promote_hard, target_from, fill}], and the item-level lists intended_lowfreq and trades (declared exemptions that fixcheck reads). \`fixcheck.py --fill\` wrote the before and after numbers and the \`fill\` provenance on each row: {before: the scorecard folder relative to the tools folder, after: the scorecard path relative to the tools folder, utc, plus target_from "config" on a row whose target the fill took from the config}. Those numbers come from scorecards: scorecard_<variant>.json (results[] with the check id and its value) in that folder, and from the check configs ${TOOLS}/checks/<config>.json.
You write text fields only: change, note, misses, script_misses and status. You never write an acceptance row and never retype a number into the ledger; a number is read from a scorecard and quoted. The main session merges your row file with fixcheck.py --merge-rows, which sets only those five fields on the item with your id.
Row rules:
- status: done only when every target row (role absent or "target") meets its target (after inside [lo, hi], null = open end) and script_misses is empty or each of its entries was re-measured and holds; not_done when no target row meets its target (the rule of \`fixcheck.py --fill after\`); else partial. A guard row is not a target: a guard outside its bound goes in the note. An item with no target row, or with a target row whose after is null, keeps the status the ledger has (as --fill does); you do not guess one. A user_edit status stays user_edit. A reverted item is not_done with a note that starts "reverted:".
- misses: keep every existing entry that does not name a (check, variant) of an acceptance row of this item, exactly as written, except an entry that is also a script_misses entry (see below): once re-measured, a script miss that still misses has the same measured text in misses and in script_misses, and one that now holds is dropped from misses (it stays in script_misses with its measured number). For each target row that misses, add one entry "<check> <variant> <before> -> <after> [<target>]: <cause in one clause>", or replace the existing entry that names that (check, variant).
- script_misses: the script-row and ladder misses the note names (suite script rows, ladder rows, watches: misses that are not acceptance rows). Start from the row's existing script_misses when it has the key, else from its existing misses entries that name no acceptance row. Re-measure each from the scorecards or the ladder the note names and write the measured number; one you cannot re-measure stays as written with the words "not re-measured". Drop none: an entry that now holds stays with its measured number (status reads that as holding) and only leaves misses.
- note: keep every existing history sentence. Add a miss sentence only when the note does not already carry that (check, variant) with its numbers and cause; the sentence has "<check> <variant> <before> -> <after> [<target>]" and its cause in one clause (a predicted miss in the item's draft or the apply order says so); a row that two items move (the same check and variant in another item's acceptance, or named in a draft's conflict list) is attributed to both items. Everything you add to the note is one paragraph per run that starts with "Ledger pass <stamp>:", where <stamp> is replaced by the \`date -u\` stamp of this run (for example "Ledger pass 2026-10-12T03:00:00Z:"; never the text "<stamp>"); if the note already has a paragraph that starts "Ledger pass " plus any stamp and a colon, edit that paragraph instead of adding another, and give it this run's stamp. Do not describe your own checking in the note (no "re-read", "matched", "verified"): that goes in the progress file and in corrections. For a status other than done the miss and its cause stand in the note.
- Numbers keep 4 significant digits as --fill wrote them.`

const WRITE_OUT = {
  type: 'object',
  properties: {
    started: { type: 'string' }, ended: { type: 'string' },
    change: { type: 'string', description: 'nodes, parameters and script edits as built' },
    note: { type: 'string', description: 'the full note: every existing history sentence plus at most one "Ledger pass <stamp>:" paragraph' },
    misses: { type: 'array', items: { type: 'string' } },
    script_misses: { type: 'array', items: { type: 'string' } },
    status: { type: 'string', enum: ['done', 'partial', 'not_done', 'user_edit'] },
    boxed: { type: 'boolean' },
  },
  required: ['started', 'ended', 'change', 'note', 'misses', 'script_misses', 'status', 'boxed'],
}
const VERIFY_OUT = {
  type: 'object',
  properties: {
    started: { type: 'string' }, ended: { type: 'string' }, id: { type: 'string' },
    corrections: { type: 'array', description: 'one object per writer value you changed, or per ledger number you found wrong (reported, never merged); [] if none',
      items: { type: 'object', properties: { field: { type: 'string' }, old: {}, new: {}, why: { type: 'string' } }, required: ['field', 'old', 'new', 'why'] } },
    additions: { type: 'array', items: { type: 'string' }, description: 'text you added that the writer did not write; [] if none' },
    target_mismatches: { type: 'array', description: 'rows whose target differs from the config or whose check has no target there; [] if none',
      items: { type: 'object', properties: { check: { type: 'string' }, variant: { type: 'string' }, row_target: {}, config_target: {} }, required: ['check', 'variant', 'row_target', 'config_target'] } },
    status: { type: 'string', enum: ['done', 'partial', 'not_done', 'user_edit'] },
    file: { type: 'string', description: 'the row file written' },
    verified_at: { type: 'string', description: 'the `date -u` stamp written into the row file as verified_at' },
    boxed: { type: 'boolean' },
  },
  required: ['started', 'ended', 'id', 'corrections', 'additions', 'target_mismatches', 'status', 'file', 'verified_at', 'boxed'],
}

const writePrompt = id => `${COMMON('write', `write-${id}`)}

You are the ledger writer for item ${id}. Write no file but ${prog(`write-${id}`)} (create ${ROWS} first if it is missing).
Read: the ledger row (items[] id ${id}) and its neighbours (other items' rows, to find rows two items move), the ledger's "apply" and "decisions" keys, the item's draft ${DRAFTS}/${id}.md (a repair id such as <id>r uses the draft of <id>; read the lead's fix for it in ${PLAN}/lead.json: fixes entry whose priority matches a P<k> id), ${TOOLS}/review/decisions.json (rows whose "items" include ${id}; skip it when the file does not exist), the apply's progress files and notes under ${RD}/apply/ (*.progress.md, and edits/${id}/edit.json when it exists), and, for the numbers' source, the scorecards the row's fill provenance names and the configs. Write "change": the nodes, parameters and script edits as built (from the build/ scripts and edit.json, not only the draft); where the build differs from the draft, say so. Then note, misses, script_misses and status by the row rules.
Return {started, ended, change, note, misses, script_misses, status, boxed}: note is the full note text (the existing note with your one paragraph), misses and script_misses the full lists. No acceptance rows. boxed true only when your box ran out before the fields were finished.`

const verifyPrompt = (id, w) => `${COMMON('verify', `verify-${id}`)}

You are the ledger verifier for item ${id}. A writer produced the fields below. Read the ledger row (items[] id ${id}) yourself. Re-read every acceptance row's number from the scorecard its fill provenance names: \`after\` from the scorecard file given by fill.after, \`before\` from the scorecard folder given by fill.before (scorecard_<variant>.json there); a row with no fill.before (its before was set by \`guards.py rows\`) keeps its before, which is not checked, and the same holds for a missing fill.after. A mismatch in the last digit that is only rounding is no correction. A number you find wrong in the ledger is reported in corrections (field "<check>@<variant>.before" or ".after", old = the ledger's, new = the scorecard's) and is never put in the row file: numbers come from fixcheck.py --fill, which the main session re-runs.
Check: each row's target against the config (target_from "config" means the check's own target) and that every check id exists in its variant's config; a target row whose check carries no target in the current config (or whose target differs from the config's) keeps its target and its status, you never edit it, and it is listed in target_mismatches {check, variant, row_target, config_target}, not in the note; the writer's status by the status rule (from the ledger's target rows as they stand, and script_misses); the misses rule (no existing entry dropped that names no acceptance row; one entry per missing target row); the script_misses rule (none dropped, each re-measured or marked "not re-measured"); the note rule (no history sentence of the existing note dropped, a miss sentence only if the note did not already carry it, at most one "Ledger pass <stamp>:" paragraph (any stamp) in total: edit the writer's paragraph, or start it if the writer wrote none, never add a second; no sentence describing checking). Never touch an acceptance row, id, title, intended_lowfreq or trades. Each change you make to a writer value is one corrections entry {field, old, new, why}; each piece of text you add is one entry of additions.
First delete ${ROWS}/${id}.json if it exists (it is from an earlier run). Write the corrected values to ${ROWS}/${id}.json (create the folder if needed; the file must exist when you return, written by you even when every value equals the writer's) as {id, verified_at, change, note, misses, script_misses, status, corrections, additions, target_mismatches}: "verified_at" is the \`${STAMP}\` stamp you run just before you write; id is ${id}, "status" is the status you return, and "verified_at" is the stamp you return. Write nothing else but ${prog(`verify-${id}`)}.
Return {started, ended, id, corrections, additions, target_mismatches, status, file, verified_at, boxed}.

WRITER FIELDS:
${JSON.stringify({ change: w.change, note: w.note, misses: w.misses, script_misses: w.script_misses, status: w.status }, null, 1)}`

phase('Write')
const rows = {}
const writerOk = w => !!(w && !w.boxed && typeof w.change === 'string' && typeof w.note === 'string')
const out = await pipeline(A.items,
  async id => { const w = await agent(writePrompt(id), { label: `write:${id}`, phase: 'Write', schema: WRITE_OUT }); rows[id] = w; return { id, w } },
  x => writerOk(x.w) ? agent(verifyPrompt(x.id, x.w), { label: `verify:${x.id}`, phase: 'Verify', schema: VERIFY_OUT }) : null)

const dead = [], ready = []
const items = A.items.map((id, i) => {
  const w = rows[id], v = out[i]
  let why = null
  if (!w) why = 'writer returned nothing'
  else if (w.boxed) why = 'writer box ran out: the partial row is not verified and not merged (run the item again)'
  else if (!writerOk(w)) why = 'writer returned no change or note text: not verified, not merged'
  else if (!v || !v.verified_at) why = 'verifier returned nothing: the writer\'s fields are unverified and are not merged'
  else if (v.id !== id || v.file !== `${ROWS}/${id}.json`) why = `verifier returned id ${JSON.stringify(v.id)} and file ${JSON.stringify(v.file)}, expected ${id} and ${ROWS}/${id}.json: the row is not merged`
  else if (v.boxed) why = 'verifier box ran out: the row is not merged'
  if (why) {
    dead.push(id)
    return { id, status: v && v.status ? v.status : null, corrections: v && v.corrections ? v.corrections.length : null, additions: v && v.additions ? v.additions.length : null, verified: false, issues: [why], row_file: null }
  }
  ready.push(id)
  const tm = (v.target_mismatches || []).length
  return { id, status: v.status, corrections: (v.corrections || []).length, additions: (v.additions || []).length, verified: true,
    issues: tm ? [`${tm} target_mismatches (a target row whose check has no target or another target in the current config): see ${v.file}`] : [], row_file: v.file }
})

const merge_command = ready.length ? `'${PY}' '${SKILL}/scripts/fixcheck.py' --ledger '${LEDGER}' --merge-rows '${ROWS}' --item ${ready.join(' ')}` : null
log(`ledger round ${R}: ${ready.length} of ${items.length} rows verified${dead.length ? `; not merged or dead: ${dead.join(', ')}` : ''}${merge_command ? '; run merge_command, then fixcheck --ledger with --scorecards the fill.after folder' : '; nothing to merge'}`)
return { round: R, items, dead, merge_command }
