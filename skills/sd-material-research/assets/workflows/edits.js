export const meta = {
  name: 'material-apply-edits',
  description: 'Apply batch of a material review: one writer per plan item rewrites its stage scripts from the checked draft into copies beside the build, one reviewer per item checks fidelity and sdkit use, one cross-check compares all items; nothing is copied into build/',
  whenToUse: 'sd-material-research stage 7: per graph batch of the apply, once the batch\'s drafts are checked',
  phases: [
    { title: 'Edit', detail: 'one writer per item (items sharing a stage script run in apply order), each followed at once by its reviewer' },
    { title: 'Cross-check', detail: 'after every writer: conflicts between items, undone edits, names read across files' },
  ],
}

// Purpose: write the stage-script edits of one graph batch of the apply (SKILL.md stage 7) off the main session's
// critical path. The main session keeps Designer: per item, on its <id>.done, in apply order, it snaps, copies the
// item's files into build/, patches and rebuilds, while the reviewers read.
// Launched by the skill, in the background, once the batch's drafts carry their .checked files.
//
// args (all required; a missing or wrong-typed one returns {error} before any agent runs):
//   tools   absolute path of the tools folder (build/, review/ live here)
//   skill   absolute real path of the skill folder (scripts/sdkit.py, references/sd_craft.md)
//   python  literal path of the numpy python (never a scratchpad file, no shell substitution)
//   round   N+1, the apply's ledger round (integer >= 1); everything is written under review/round<N+1>/apply/edits/
//   items   [{id, draft, files}] in apply order. id: letters, digits, _ or -, unique ignoring case, not "cross";
//           draft: path relative to tools (the checked draft); files: the stage scripts the item changes, relative to
//           tools, .py, e.g. "build/05_height.py", no ".", ".." or empty segments, no duplicates inside an item
//           (ignoring case)
//
// Per item (OUT = <tools>/review/round<N+1>/apply/edits):
//   writer    follows the draft and writes full new copies of its files to OUT/<id>/<same relative path>, never into
//             build/, plus OUT/<id>/edit.json {files, summary, new_nodes, removed_nodes, rebuild_from, placeholders,
//             open_questions}; py_compiles each copy; writes OUT/<id>.done (a `date -u` stamp) as its last act, and
//             only when it finished and every copy compiled. An item whose files overlap an earlier item's waits for
//             that writer and starts each shared file from the latest earlier item's output copy; the others run at
//             once. An earlier writer that returned nothing or no .done leaves its dependents unstarted
//             (done false, "blocked by"): the main session repairs the earlier item first.
//   reviewer  starts when its writer returns, no barrier: fidelity to the draft and code (sdkit calls against their
//             definitions, Blend/Levels/Histogram Scan semantics of sd_craft.md section 5, names other stages read are
//             still produced). Writes OUT/<id>.review.json {verdict: "go"|"blocker", issues: [{severity, file, line,
//             problem, fix}]}.
// After every writer (the one barrier, justified: it compares all items): the cross-check writes OUT/cross.review.json
// (same shape). There is no fix stage: the main session repairs blockers.
// Progress files: OUT/<id>.progress.md, OUT/<id>.review.progress.md, OUT/cross.progress.md (a `date -u` line and what
// it showed after every script run). Boxes (minutes): edit writer 25, edit reviewer 15, cross-check 15.
// Agents inherit the session's model and effort. Returns {round, items: [{id, done, verdict, issues, blockers,
// files, blocked_by?}], cross: {verdict, issues, blockers} | null, dead}, issues being counts.
// `done` is the writer's own report (complete, and every copy compiled); this script cannot see the files. The main
// session checks that OUT/<id>.done exists before it copies an item's files into build/; the reviewer checks it too,
// but a reviewer that returned nothing leaves it unchecked.
// Paths: tools, skill, python, draft and files are put inside double quotes in the prompts, so they may not contain
// a double quote, a backtick or $ (rejected). Files are compared ignoring case (the Mac volume folds case): items
// that list the same file in different case are chained, and one item may not list a file twice in any case.
const A = (typeof args === 'object' && args !== null && !Array.isArray(args)) ? args : {}
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const BOX = { writer: 25, reviewer: 15, cross: 15 }

const UNSAFE = /["`$\n\r]/   // would break the double-quoted paths in the prompts
const isAbs = s => typeof s === 'string' && /^(\/|[A-Za-z]:[\\/])/.test(s) && !UNSAFE.test(s)
const relOk = s => typeof s === 'string' && s.length > 0 && !/^([\\/]|[A-Za-z]:)/.test(s) && !UNSAFE.test(s) && !/\\/.test(s)
  && s.split('/').every(seg => seg !== '' && seg !== '.' && seg !== '..')
const bad = []
if (!isAbs(A.tools)) bad.push('tools must be an absolute path string without a double quote, backtick or $')
if (!isAbs(A.skill)) bad.push('skill must be an absolute path string without a double quote, backtick or $')
if (!isAbs(A.python) || /scratchpad/.test(A.python)) bad.push('python must be an absolute literal path (no double quote, backtick, $ or shell substitution; not a scratchpad file)')
if (!Number.isInteger(A.round) || A.round < 1) bad.push('round must be an integer >= 1 (the apply\'s ledger round, N+1)')
const seenIds = new Set()
if (!Array.isArray(A.items) || A.items.length === 0) bad.push('items must be a non-empty array of {id, draft, files}')
else A.items.forEach((it, i) => {
  const w = `items[${i}]`
  if (!it || typeof it !== 'object' || Array.isArray(it)) { bad.push(`${w} must be an object {id, draft, files}`); return }
  const idl = typeof it.id === 'string' ? it.id.toLowerCase() : ''
  if (typeof it.id !== 'string' || !/^[A-Za-z0-9_-]+$/.test(it.id)) bad.push(`${w}.id must be a string of letters, digits, _ or -`)
  else if (idl === 'cross') bad.push(`${w}.id "cross" is reserved (cross.review.json)`)
  else if (seenIds.has(idl)) bad.push(`${w}.id ${JSON.stringify(it.id)} repeats an earlier id (compared ignoring case)`)
  else seenIds.add(idl)
  if (!relOk(it.draft)) bad.push(`${w}.draft must be a path relative to tools (no "..", no leading slash, no double quote, backtick or $)`)
  if (!Array.isArray(it.files) || it.files.length === 0) bad.push(`${w}.files must be a non-empty array of relative .py paths`)
  else {
    if (!it.files.every(f => relOk(f) && /\.py$/.test(f))) bad.push(`${w}.files entries must be relative .py paths without ".", ".." or empty segments`)
    else if (new Set(it.files.map(f => f.toLowerCase())).size !== it.files.length) bad.push(`${w}.files lists a file twice (compared ignoring case)`)
  }
})
if (bad.length) return { error: `edits.js: ${bad.join('; ')}` }

const T = A.tools, SK = A.skill, PY = A.python, R = A.round
const items = A.items.map(it => ({ id: it.id, draft: it.draft, files: [...it.files] }))
const OUT = `${T}/review/round${R}/apply/edits`
const REL_OUT = `review/round${R}/apply/edits`

// Chaining, decided before any agent runs. deps[i]: earlier items sharing a file. src[i][file]: where item i starts
// the file from (the latest earlier item's output copy that has it, else the build's own script).
// Files are compared ignoring case; an earlier item's copy is named with that item's own spelling.
const lc = f => f.toLowerCase()
const own = (it, f) => it.files.find(g => lc(g) === lc(f))
const deps = items.map((it, i) => items.slice(0, i).map((o, j) => j).filter(j => items[j].files.some(f => own(it, f))))
const src = items.map((it, i) => Object.fromEntries(it.files.map(f => {
  let from = `${T}/${f}`
  for (let j = 0; j < i; j++) { const g = own(items[j], f); if (g) from = `${OUT}/${items[j].id}/${g}` }
  return [f, from]
})))
// Final state of each file after the whole batch: the copy of the last item whose writer finished (known only once
// the writers have returned). A file no finished item wrote stays as build/ has it.
const finalCopies = (written) => {
  const fin = {}
  items.forEach((it, i) => it.files.forEach(f => {
    const k = lc(f)
    if (!fin[k]) fin[k] = { file: f, copy: null, by: null }
    if (written[i].ok) { fin[k].copy = `${OUT}/${it.id}/${f}`; fin[k].by = it.id }
  }))
  return Object.values(fin)
}
// A report shortened for a prompt: every cut says so and points at edit.json, never a silent slice.
const cap = (s, n) => s.length > n ? `${s.slice(0, n)}...[cut, read edit.json]` : s
const capVal = v => Array.isArray(v)
  ? [...v.slice(0, 15).map(x => typeof x === 'string' ? cap(x, 160) : x), ...(v.length > 15 ? [`...${v.length - 15} more, read edit.json`] : [])]
  : typeof v === 'string' ? cap(v, 800) : v
const capReport = r => r && typeof r === 'object' ? Object.fromEntries(Object.entries(r).map(([k, v]) => [k, capVal(v)])) : r

const STAMPS = {
  started: { type: 'string', description: `UTC, from \`${STAMP}\` as your first action` },
  ended: { type: 'string', description: `UTC, from \`${STAMP}\` just before your last write` },
}
const strs = { type: 'array', items: { type: 'string' } }
const WRITE_SCHEMA = {
  type: 'object',
  properties: {
    ...STAMPS,
    complete: { type: 'boolean', description: 'true only when every draft change for your files is written and every copy compiled; false when the box stopped you or a compile failed' },
    files: { ...strs, description: 'the files written, relative to the tools folder' },
    summary: { type: 'string' },
    new_nodes: strs,
    removed_nodes: strs,
    rebuild_from: { type: 'string', description: 'the stage script (or stage number) the rebuild after this edit must start from' },
    placeholders: { ...strs, description: 'constants a later probe fits, each with its placeholder value and the script and line' },
    open_questions: strs,
    compile: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, ok: { type: 'boolean' } }, required: ['file', 'ok'] } },
    left: { ...strs, description: 'what is left when the box stopped you; [] when complete' },
  },
  required: ['started', 'ended', 'complete', 'files', 'summary', 'new_nodes', 'removed_nodes', 'rebuild_from', 'placeholders', 'open_questions', 'compile', 'left'],
}
const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    ...STAMPS,
    verdict: { type: 'string', enum: ['go', 'blocker'] },
    issues: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
      file: { type: 'string' }, line: { type: 'string' },
      problem: { type: 'string' }, fix: { type: 'string' },
    }, required: ['severity', 'file', 'line', 'problem', 'fix'] } },
  },
  required: ['started', 'ended', 'verdict', 'issues'],
}

// Rules every agent gets.
const common = (label, minutes) => `Tools folder: "${T}" (cd there). Skill folder: "${SK}". Python for numpy checks: ${PY}
HARD RULES: never call substance-designer tools (only the main session calls Designer); never edit anything but your named output files; never commit or touch git; never write into build/.
Run \`${STAMP}\` first. After every script run, append a \`date -u\` line and what it showed to ${OUT}/${label}.progress.md (create ${OUT} if it is missing).
Box: ${minutes} minutes; at the box, stop, write what is left in the progress file and return what you have.`

const compileLine = `Compile with \`PYTHONPYCACHEPREFIX="${OUT}/.pycache" python3 -m py_compile <copy>\` (the prefix keeps __pycache__ out of the item folder).`

const writerPrompt = (it, i) => `${common(it.id, BOX.writer)}

You are the edit writer for plan item ${it.id}. The checked draft is "${T}/${it.draft}" (read all of it; start with its CHANGE sections, probes, the guard rows, order notes and its Premise check).
Your files, with the copy each one starts from:
${it.files.map(f => `- ${f}: start from "${src[i][f]}"${src[i][f].startsWith(OUT) ? ' (an earlier item\'s output; keep its edits)' : ''}`).join('\n')}
${deps[i].length ? `Earlier items that touch the same files and already wrote their copies: ${deps[i].map(j => `${items[j].id} (${OUT}/${items[j].id}/edit.json)`).join(', ')}. Read their edit.json first; their node names and constants are now part of your source.\n` : ''}Do:
1. Apply every change the draft lists for your files, and nothing else. A change the draft puts in a file you do not own goes in open_questions, not in that file. Match on quoted text, not line numbers (line numbers in a draft predate other edits).
2. Follow the sdkit signatures (${SK}/scripts/sdkit.py: grep each function you call) and ${SK}/references/sd_craft.md sections 2 and 5 (Blend argument order, Levels arguments, Histogram Scan direction). Keep the file's idiom, comment density and node-name prefixes. Mark each constant a later probe or fit sets with a comment saying which step fits it, and list it in placeholders.
3. Write the full new copy of each file to ${OUT}/${it.id}/<same relative path> (for build/x.py: ${OUT}/${it.id}/build/x.py). ${compileLine}
4. Write ${OUT}/${it.id}/edit.json: {"files", "summary", "new_nodes", "removed_nodes", "rebuild_from", "placeholders", "open_questions"} (rebuild_from: the first stage script a rebuild must run so every changed node is recreated).
5. Last act, only when every draft change is written and every copy compiled: run \`${STAMP}\` and write that one line to ${OUT}/${it.id}.done. Without it the main session does not treat the item as done.
Return the same fields as edit.json plus started, ended, complete, compile and left.`

const reviewerPrompt = (it, i, w) => `${common(`${it.id}.review`, BOX.reviewer)}

You are the edit reviewer for plan item ${it.id}: read-only, adversarial, specific. The checked draft is "${T}/${it.draft}". The writer's copies are in ${OUT}/${it.id}/ (edit.json beside them); the writer reported:
${JSON.stringify(capReport(w))}
(fields cut with "[cut" or "more" are complete in ${OUT}/${it.id}/edit.json)
Each copy started from:
${it.files.map(f => `- ${f}: "${src[i][f]}"`).join('\n')}
Check first that ${OUT}/${it.id}.done exists; if it does not, say so as a blocker. Then diff each copy against its starting file and check:
1. FIDELITY: every change the draft lists for these files is present; nothing extra changed; the node names, files and registry entries that other stage scripts (build/*.py as they are now, the other items' copies in ${OUT}/), the export scripts (export*.py) and registry.json read are still produced, with the same names.
2. CODE: every sdkit call matches its definition in ${SK}/scripts/sdkit.py (argument count and order; Blend (name, mode, source, destination); Levels arguments; parameter ids); Histogram Scan direction and Blend/divide semantics as in ${SK}/references/sd_craft.md section 5; unique node names; every node read exists upstream in stage order. ${compileLine}
Each issue: severity blocker (the build breaks or a draft change is missing or wrong), major (wrong but the build runs), or minor; file, line, the problem and the exact fix. verdict is "blocker" if any issue is a blocker, else "go". Do not fix anything.
Write ${OUT}/${it.id}.review.json as {"verdict", "issues": [{"severity", "file", "line", "problem", "fix"}]}, then run \`${STAMP}\` for "ended". Return that object plus started and ended.`

const crossPrompt = (rows, finals) => `${common('cross', BOX.cross)}

You are the cross-checker for this apply batch: read-only. Every item's writer has returned; reviewers may still be running. The items, in apply order, with their writers' reports:
${JSON.stringify(rows, null, 1)}
Fields cut with "[cut" or "more" are complete in each item's edit.json: ${rows.map(r => `${r.id}: ${OUT}/${r.id}/edit.json${r.done ? '' : ' (not finished: the file may be missing or partial)'}`).join('; ')}. Items with "done": false have no finished copy; judge only what their report and any partial copy show, and say so in the issue.
The file each item rewrote ends in this state (the copy of the last item whose writer finished; nothing is in build/ yet):
${finals.map(x => x.copy ? `- ${x.file}: "${x.copy}" (item ${x.by})` : `- ${x.file}: no finished copy; build/ keeps its own "${T}/${x.file}"`).join('\n')}
Check across the items and the unchanged build/*.py:
1. conflicts between items: two items editing the same node, constant or parameter to different values; a later item undoing or overwriting an earlier item's change;
2. names read across files: every node name, registry key, preset or constant that one stage script (changed or unchanged) reads from another is still produced by the final copy of the other, in stage order; no node name is created twice in one graph; reset() prefixes of each stage still cover its new nodes;
3. rebuild order: each item's rebuild_from is early enough for every node the batch changes.
Each issue: severity blocker, major or minor; file, line, the problem and the exact fix. verdict "blocker" if any issue is a blocker, else "go". Do not fix anything.
Write ${OUT}/cross.review.json as {"verdict", "issues": [{"severity", "file", "line", "problem", "fix"}]}, then run \`${STAMP}\` for "ended". Return that object plus started and ended.`

const counts = r => r && Array.isArray(r.issues)
  ? { blocker: r.issues.filter(x => x.severity === 'blocker').length, major: r.issues.filter(x => x.severity === 'major').length, minor: r.issues.filter(x => x.severity === 'minor').length }
  : { blocker: 0, major: 0, minor: 0 }
const total = c => c.blocker + c.major + c.minor
// A blocker issue makes the verdict "blocker" even when the reviewer wrote "go"; a "blocker" verdict stands.
const verdictOf = r => {
  if (!r) return null
  const n = counts(r).blocker
  const v = n > 0 || r.verdict === 'blocker' ? 'blocker' : 'go'
  if (v !== r.verdict) log(`review verdict corrected to ${v}: it said ${r.verdict} with ${n} blocker issue(s)`)
  return v
}
const short = r => (r && r.issues ? r.issues.filter(x => x.severity === 'blocker').map(x => `${x.file}:${x.line} ${x.problem}`.slice(0, 200)) : [])

log(`edits: ${items.length} item(s), round ${R}; chaining: ${items.map((it, i) => `${it.id}${deps[i].length ? ' after ' + deps[i].map(j => items[j].id).join('+') : ''}`).join(', ')}`)

phase('Edit')
// Writers: an item waits only for the earlier writers it shares a file with. Reviewers start from their own writer.
const writerP = []
items.forEach((it, i) => {
  writerP[i] = (async () => {
    const before = await Promise.all(deps[i].map(j => writerP[j]))
    const blockers = deps[i].filter((j, k) => !before[k] || !before[k].ok)
    if (blockers.length) {
      log(`writer ${it.id} not started: ${blockers.map(j => items[j].id).join(', ')} did not finish`)
      return { ok: false, w: null, blocked_by: blockers.map(j => items[j].id) }
    }
    const w = await agent(writerPrompt(it, i), { label: `edit:${it.id}`, phase: 'Edit', schema: WRITE_SCHEMA })
    const ok = !!w && w.complete === true && Array.isArray(w.compile) && w.compile.length > 0 && w.compile.every(c => c.ok)
    if (!w) log(`writer ${it.id} returned nothing`)
    else if (!ok) log(`writer ${it.id} incomplete: ${(w.left || []).join('; ') || 'compile failed or no compile result'}`)
    return { ok, w, blocked_by: [] }
  })()
})
const reviewP = items.map((it, i) => writerP[i].then(async res => {
  if (!res.w) return null
  const r = await agent(reviewerPrompt(it, i, res.w), { label: `review:${it.id}`, phase: 'Edit', schema: REVIEW_SCHEMA })
  if (!r) log(`reviewer ${it.id} returned nothing`)
  return r
}))

// The cross-check waits for every writer, not for the reviewers.
const written = await Promise.all(writerP)
phase('Cross-check')
const crossRows = items.map((it, i) => ({ id: it.id, files: it.files, done: written[i].ok, report: written[i].w ? capReport({ summary: written[i].w.summary, new_nodes: written[i].w.new_nodes, removed_nodes: written[i].w.removed_nodes, rebuild_from: written[i].w.rebuild_from, placeholders: written[i].w.placeholders, open_questions: written[i].w.open_questions }) : null }))
const crossP = written.some(x => x.w)
  ? agent(crossPrompt(crossRows, finalCopies(written)), { label: 'cross-check', phase: 'Cross-check', schema: REVIEW_SCHEMA })
  : Promise.resolve(null)
const [reviews, cross] = await Promise.all([Promise.all(reviewP), crossP])

const dead = []
const out = items.map((it, i) => {
  const res = written[i], r = reviews[i]
  if (!res.w && !res.blocked_by.length) dead.push(`edit:${it.id}`)
  if (res.w && !r) dead.push(`review:${it.id}`)
  const c = counts(r)
  const row = { id: it.id, done: res.ok, verdict: verdictOf(r), issues: total(c), blockers: short(r), files: res.w ? res.w.files : [] }
  if (res.blocked_by.length) row.blocked_by = res.blocked_by
  return row
})
if (written.some(x => x.w) && !cross) dead.push('cross-check')
const cc = counts(cross)
const crossOut = cross ? { verdict: verdictOf(cross), issues: total(cc), blockers: short(cross) } : null
log(`edits done: ${out.filter(o => o.done).length} of ${out.length} items done, ${out.filter(o => o.verdict === 'blocker').length} review blocker(s), cross-check ${crossOut ? crossOut.verdict : 'missing'}${dead.length ? `; returned nothing: ${dead.join(', ')}` : ''}`)

return { round: R, items: out, cross: crossOut, dead }
