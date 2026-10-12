export const meta = {
  name: 'material-apply-edits',
  description: 'Apply batch of a material review: one writer per plan item rewrites its stage scripts (and sets keys in its json files, and starts its new scripts) from the checked draft into copies beside the build, one reviewer per item checks fidelity, sdkit use and json overrides, one cross-check compares all items; nothing is copied into build/',
  whenToUse: 'sd-material-research stage 7: per graph batch of the apply, once the batch\'s drafts are checked',
  phases: [
    { title: 'Edit', detail: 'one writer per item (items sharing a stage script run in apply order), each followed at once by its reviewer' },
    { title: 'Cross-check', detail: 'after every writer: conflicts between items, undone edits, names read across files, json overrides' },
  ],
}

// Purpose: write the stage-script edits of one graph batch of the apply (SKILL.md stage 7) off the main session's
// critical path. The main session keeps Designer: per item, on its <id>.done, in apply order, it snaps, copies the
// item's files into build/, patches and rebuilds, while the reviewers read.
// Launched by the skill, in the background, once the batch's drafts carry their .checked files.
//
// args (tools, skill, python, round, items required; a missing or wrong-typed one returns {error} before any agent runs):
//   tools   absolute path of the tools folder (build/, review/ live here)
//   skill   absolute real path of the skill folder (scripts/sdkit.py, references/sd_craft.md)
//   python  literal path of the numpy python (never a scratchpad file, no shell substitution)
//   round   N+1, the apply's ledger round (integer >= 1); everything is written under review/round<N+1>/apply/edits/
//   items   [{id, draft, files, json?, new?, notes?}] in apply order.
//           id: letters, digits, _ or -, unique ignoring case, not "cross";
//           draft: path relative to tools (the checked draft);
//           files: the stage scripts the item changes, relative to tools, under build/, .py, e.g. "build/05_height.py",
//             no ".", ".." or empty segments; an array, empty only when the item has json or new (json and new are under
//             build/ too: nothing outside build/ is edited);
//           json (optional): [{file, set: {key: value}}], file = "build/<name>.json" (e.g. build/tune.json,
//             build/calibration.json) that exists; the writer copies it to OUT/<id>/<file> and sets those top-level
//             keys to those values, nothing else changed; values are JSON (finite numbers, strings, booleans, null,
//             arrays, plain objects);
//           new (optional): ["build/<name>.py", ...] scripts that do not exist yet; they start empty in OUT/<id>/ and
//             are compiled like the others;
//           notes (optional): [string], the apply-order rows for this item (e.g. a docstring sentence to add), shown
//             to the writer and the reviewer.
//           No path (files, json file, new) may repeat inside an item (ignoring case); a path in new may not appear
//           in an earlier item. This script cannot read the disk: "json files exist" and "new files do not exist yet"
//           are checked by the writer first, which stops without a .done and says so when they do not hold.
//
// Per item (OUT = <tools>/review/round<N+1>/apply/edits):
//   writer    follows the draft and writes full new copies of its files to OUT/<id>/<same relative path>, never into
//             build/, plus OUT/<id>/edit.json {files, summary, new_nodes, removed_nodes, rebuild_from, placeholders,
//             open_questions}; py_compiles each script copy and parses each json copy; writes OUT/<id>.done (a
//             `date -u` stamp) as its last act, and only when it finished and every copy compiled. Comments only on
//             lines it changes, plus the docstring sentences in the item's notes. An item whose paths overlap an
//             earlier item's waits for that writer and starts each shared file from the latest earlier item's output
//             copy; the others run at once. An earlier writer that returned nothing or no .done leaves its dependents
//             unstarted (done false, "blocked by"): the main session repairs the earlier item first.
//   reviewer  starts when its writer returns, no barrier: fidelity to the draft and code (sdkit calls against their
//             definitions, Blend/Levels/Histogram Scan semantics of sd_craft.md section 5, names other stages read are
//             still produced; registry.json lists names that exist today and proves nothing about the copies), the
//             json copies differ from their sources in the listed keys only, overrides (a TUNE / CAL key or constant
//             the item changes against build/tune.json, build/calibration.json and the `**` merge in the stage
//             script), scope (a changed line that is neither a draft change nor a notes row is a minor). Writes
//             OUT/<id>.review.json {verdict: "go"|"fix"|"blocker", issues: [{severity, file, line, problem, fix}]}.
//             Severities by what the rebuild produces: blocker = it fails or does not produce what the draft specifies
//             (a draft change missing or not applied); major = it runs and produces the draft's changes, but wrongly
//             (a json key that shadows a new default is a major by rule); minor = no effect on the result (comment,
//             style, an extra change outside the draft). The verdict is derived from the issues only: "blocker" when
//             any issue is a blocker, "fix" when none is but one is a major (the main session repairs it before the
//             rebuild), else "go"; a written verdict that disagrees is corrected, logged and kept as verdict_said.
//   After every writer (the one barrier, justified: it compares all items): the cross-check writes
//   OUT/cross.review.json (same shape, same severity definitions): conflicts between items, names read across files,
//   rebuild order, and overrides across the final copies. There is no fix stage: the main session repairs blockers
//   and majors. It reads every OUT/<id>.review.json major (and the cross one) before it rebuilds the item; the
//   returned majors are one-line texts, not the issues.
// Progress files: OUT/<id>.progress.md, OUT/<id>.review.progress.md, OUT/cross.progress.md (a `date -u` line and what
// it showed after every script run). Boxes (minutes): edit writer 25, edit reviewer 15, cross-check 15.
// Rule for every agent: read only inside the tools folder, the skill folder and the files named; never another tools
// folder or a later round's files; if it did, it says so in its progress file.
// Agents inherit the session's model and effort.
// Returns {round, items: [{id, done, verdict (go|fix|blocker|null), verdict_said?, issues, counts: {blocker, major, minor}, blockers, majors, files, aux,
// files_reported, open_questions, n_open_questions, blocked_by?}], cross: {verdict, verdict_said?, issues, counts, blockers, majors} |
// null, dead}. issues is the total; blockers and majors are one-line texts "file:line problem" (cut at 200 characters
// with "..."; the full text is in the review.json). files is [{build, copy}] built from the item's own list (files,
// then json files, then new), copy = review/round<N+1>/apply/edits/<id>/<file> relative to tools, [] unless the item
// is done; aux = [edit.json, <id>.done] under the same folder (never copy those into build/); files_reported is the
// writer's own list (a warning is logged when it differs from the item's); open_questions is the writer's, at most 8.
// `done` is the writer's own report (complete, every copy compiled and reported written, every file of the item
// covered; a reported name counts only as the item's path or that path inside this item's own output folder, ignoring
// case, and any other difference from the item's list is logged); this script cannot see the files. The main session checks that OUT/<id>.done exists before it copies an
// item's files into build/; the reviewer checks it too, but a reviewer that returned nothing leaves it unchecked.
// Paths: tools, skill, python, draft and files are put inside double quotes in the prompts, so they may not contain
// a double quote, a backtick or $ (rejected). Files are compared ignoring case (the Mac volume folds case): items
// that list the same file in different case are chained, and one item may not list a file twice in any case.
const A = (typeof args === 'object' && args !== null && !Array.isArray(args)) ? args : {}
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const BOX = { writer: 25, reviewer: 15, cross: 15 }
const lc = f => f.toLowerCase()

const UNSAFE = /["`$\n\r]/   // would break the double-quoted paths in the prompts
const isAbs = s => typeof s === 'string' && /^(\/|[A-Za-z]:[\\/])/.test(s) && !UNSAFE.test(s)
const relOk = s => typeof s === 'string' && s.length > 0 && !/^([\\/]|[A-Za-z]:)/.test(s) && !UNSAFE.test(s) && !/\\/.test(s)
  && s.split('/').every(seg => seg !== '' && seg !== '.' && seg !== '..')
const inBuild = s => relOk(s) && s.startsWith('build/')
const isObj = v => Object.prototype.toString.call(v) === '[object Object]'
// Array.from turns a hole into undefined, which every check below rejects (every/forEach would skip it).
const every = (a, f) => Array.from(a).every(f)
const jsonVal = (v, d = 0) => d < 12 && (v === null || typeof v === 'boolean' || typeof v === 'string' || (typeof v === 'number' && Number.isFinite(v))
  || (Array.isArray(v) && every(v, x => jsonVal(x, d + 1))) || (isObj(v) && Object.values(v).every(x => jsonVal(x, d + 1))))
const bad = []
if (!isAbs(A.tools)) bad.push('tools must be an absolute path string without a double quote, backtick or $')
if (!isAbs(A.skill)) bad.push('skill must be an absolute path string without a double quote, backtick or $')
if (!isAbs(A.python) || /scratchpad/.test(A.python)) bad.push('python must be an absolute literal path (no double quote, backtick, $ or shell substitution; not a scratchpad file)')
if (!Number.isInteger(A.round) || A.round < 1) bad.push('round must be an integer >= 1 (the apply\'s ledger round, N+1)')
const seenIds = new Set()
const allPaths = o => [...(Array.isArray(o.files) ? o.files : []), ...(Array.isArray(o.json) ? o.json.map(j => j && j.file) : []), ...(Array.isArray(o.new) ? o.new : [])].filter(f => typeof f === 'string')
if (!Array.isArray(A.items) || A.items.length === 0) bad.push('items must be a non-empty array of {id, draft, files, json?, new?, notes?}')
else A.items.forEach((it, i) => {
  const w = `items[${i}]`
  if (!it || typeof it !== 'object' || Array.isArray(it)) { bad.push(`${w} must be an object {id, draft, files, json?, new?, notes?}`); return }
  const idl = typeof it.id === 'string' ? lc(it.id) : ''
  if (typeof it.id !== 'string' || !/^[A-Za-z0-9_-]+$/.test(it.id)) bad.push(`${w}.id must be a string of letters, digits, _ or -`)
  else if (idl === 'cross') bad.push(`${w}.id "cross" is reserved (cross.review.json)`)
  else if (seenIds.has(idl)) bad.push(`${w}.id ${JSON.stringify(it.id)} repeats an earlier id (compared ignoring case)`)
  else seenIds.add(idl)
  if (!relOk(it.draft)) bad.push(`${w}.draft must be a path relative to tools (no "..", no leading slash, no double quote, backtick or $)`)
  const paths = []
  if (!Array.isArray(it.files)) bad.push(`${w}.files must be an array of relative build/ .py paths (empty only when the item has json or new)`)
  else if (!every(it.files, f => inBuild(f) && /\.py$/.test(f))) bad.push(`${w}.files entries must be relative .py paths under build/ without ".", ".." or empty segments`)
  else paths.push(...it.files)
  if (it.json !== undefined) {
    if (!Array.isArray(it.json)) bad.push(`${w}.json must be an array of {file, set: {key: value}}`)
    else Array.from(it.json).forEach((j, k) => {
      const x = `${w}.json[${k}]`
      if (!isObj(j)) { bad.push(`${x} must be an object {file, set: {key: value}}`); return }
      if (!inBuild(j.file) || !/\.json$/.test(j.file)) bad.push(`${x}.file must be a relative path under build/ ending in .json (and existing: the writer checks)`)
      else paths.push(j.file)
      if (!isObj(j.set) || Object.keys(j.set).length === 0) bad.push(`${x}.set must be a non-empty object {key: value}`)
      else Object.entries(j.set).forEach(([key, v]) => {
        if (key === '') bad.push(`${x}.set has an empty key`)
        if (!jsonVal(v)) bad.push(`${x}.set[${JSON.stringify(key)}] must be JSON (finite number, string, boolean, null, array or plain object)`)
      })
    })
  }
  if (it.new !== undefined) {
    if (!Array.isArray(it.new)) bad.push(`${w}.new must be an array of relative build/ .py paths that do not exist yet`)
    else if (!every(it.new, f => inBuild(f) && /\.py$/.test(f))) bad.push(`${w}.new entries must be relative .py paths under build/ without ".", ".." or empty segments (not existing yet: the writer checks)`)
    else paths.push(...it.new)
  }
  if (it.notes !== undefined && !(Array.isArray(it.notes) && every(it.notes, n => typeof n === 'string' && n.trim().length > 0))) bad.push(`${w}.notes must be an array of non-empty strings`)
  if (new Set(paths.map(lc)).size !== paths.length) bad.push(`${w} lists a file twice across files, json and new (compared ignoring case)`)
  if (Array.isArray(it.files) && paths.length === 0 && !bad.some(b => b.startsWith(w))) bad.push(`${w} lists no file: files is empty and there is no json or new`)
})
if (!bad.length) A.items.forEach((it, i) => (it.new || []).forEach(n => {
  const j = A.items.findIndex((o, k) => k < i && allPaths(o).some(f => lc(f) === lc(n)))
  if (j >= 0) bad.push(`items[${i}].new ${JSON.stringify(n)} is listed by earlier item ${A.items[j].id}: list it under files (it exists in that item's output copy)`)
}))
if (bad.length) return { error: `edits.js: ${bad.join('; ')}` }

const T = A.tools, SK = A.skill, PY = A.python, R = A.round
const items = A.items.map(it => {
  const json = Array.isArray(it.json) ? it.json.map(j => ({ file: j.file, set: j.set })) : []
  const files = [...it.files], neu = Array.isArray(it.new) ? [...it.new] : []
  return { id: it.id, draft: it.draft, files, json, neu, notes: Array.isArray(it.notes) ? [...it.notes] : [], paths: [...files, ...json.map(j => j.file), ...neu] }
})
const OUT = `${T}/review/round${R}/apply/edits`
const REL_OUT = `review/round${R}/apply/edits`

// Chaining, decided before any agent runs. deps[i]: earlier items sharing a path (script, json or new).
// src[i][path]: where item i starts the file from (the latest earlier item's output copy that has it, else the build's
// own file; null for a new file nobody wrote yet). Files are compared ignoring case; an earlier item's copy is named
// with that item's own spelling.
const own = (it, f) => it.paths.find(g => lc(g) === lc(f))
const kindOf = (it, p) => it.neu.some(g => lc(g) === lc(p)) ? 'new' : it.json.some(j => lc(j.file) === lc(p)) ? 'json' : 'py'
const deps = items.map((it, i) => items.slice(0, i).map((o, j) => j).filter(j => items[j].paths.some(f => own(it, f))))
const src = items.map((it, i) => Object.fromEntries(it.paths.map(f => {
  let from = kindOf(it, f) === 'new' ? null : `${T}/${f}`
  for (let j = 0; j < i; j++) { const g = own(items[j], f); if (g) from = `${OUT}/${items[j].id}/${g}` }
  return [f, from]
})))
// Final state of each file after the whole batch: the copy of the last item whose writer finished (known only once
// the writers have returned). A file no finished item wrote stays as build/ has it (a new file: stays absent).
const finalCopies = (written) => {
  const fin = {}
  items.forEach((it, i) => it.paths.forEach(f => {
    const k = lc(f)
    if (!fin[k]) fin[k] = { file: f, copy: null, by: null, isNew: kindOf(it, f) === 'new' }
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
// A reported name matches an item path when it is that path or that path inside this item's own output folder (the
// absolute or the tools-relative copy path), ignoring case. A suffix match would let another folder's or another item's
// file stand in for this item's. A name that matches but is not spelled as listed is "respelled" and still warned.
const nameIs = (it, g, f) => typeof g === 'string' && [f, `${OUT}/${it.id}/${f}`, `${REL_OUT}/${it.id}/${f}`].some(x => lc(x) === lc(g))
const gaps = (it, w) => {
  const rep = Array.isArray(w.files) ? w.files : []
  return {
    compiled: it.paths.filter(p => !(Array.isArray(w.compile) && w.compile.some(c => c && c.ok && nameIs(it, c.file, p)))),
    reported: it.paths.filter(p => !rep.some(g => nameIs(it, g, p))),
    extra: rep.filter(g => !it.paths.some(p => nameIs(it, g, p))),
    respelled: rep.filter(g => it.paths.some(p => nameIs(it, g, p) && g !== p)),
  }
}

const STAMPS = {
  started: { type: 'string', description: `UTC, from \`${STAMP}\` as your first action` },
  ended: { type: 'string', description: `UTC, from \`${STAMP}\` just before your last write` },
}
const strs = { type: 'array', items: { type: 'string' } }
const WRITE_SCHEMA = {
  type: 'object',
  properties: {
    ...STAMPS,
    complete: { type: 'boolean', description: 'true only when every draft change for your files is written and every copy compiled (scripts) or parsed (json); false when the box stopped you, an input was not as stated or a compile failed' },
    files: { ...strs, description: 'the item\'s paths you wrote, relative to the tools folder, spelled as listed in the prompt (build/x.py), never the copies, edit.json or progress files' },
    summary: { type: 'string' },
    new_nodes: strs,
    removed_nodes: strs,
    rebuild_from: { type: 'string', description: 'the stage script (or stage number) the rebuild after this edit must start from' },
    placeholders: { ...strs, description: 'constants a later probe fits, each with its placeholder value and the script and line' },
    open_questions: strs,
    compile: { type: 'array', description: 'one entry per file of the item, json files included', items: { type: 'object', properties: { file: { type: 'string' }, ok: { type: 'boolean' } }, required: ['file', 'ok'] } },
    left: { ...strs, description: 'what is left when the box stopped you; [] when complete' },
  },
  required: ['started', 'ended', 'complete', 'files', 'summary', 'new_nodes', 'removed_nodes', 'rebuild_from', 'placeholders', 'open_questions', 'compile', 'left'],
}
const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    ...STAMPS,
    verdict: { type: 'string', enum: ['go', 'fix', 'blocker'] },
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
Read only inside the tools folder, the skill folder and the files named here; never open another tools folder or a later round's files (anything for a round after ${R}); if you did, say so in the progress file.
Run \`${STAMP}\` first. After every script run, append a \`date -u\` line and what it showed to ${OUT}/${label}.progress.md (create ${OUT} if it is missing).
Box: ${minutes} minutes; at the box, stop, write what is left in the progress file and return what you have.`

const compileLine = `Compile each script copy with \`PYTHONPYCACHEPREFIX="${OUT}/.pycache" python3 -m py_compile <copy>\` (the prefix keeps __pycache__ out of the item folder) and parse each json copy with \`python3 -m json.tool <copy> > /dev/null\`.`

// One definition of the severities and the verdict, shared by the reviewer and the cross-check.
const SEVERITY = 'Each issue: severity blocker (the rebuild fails or does not produce what the draft specifies: a draft change is missing or not applied), major (the rebuild runs and produces the draft\'s changes, but wrongly), or minor (no effect on the result: a comment, style, an extra change outside the draft); file, line, the problem and the exact fix. A rule that names a severity (a shadowing json key is a major) wins over these definitions.'
const VERDICT = 'verdict is "blocker" if any issue is a blocker, else "fix" if any issue is a major (the main session repairs it before the rebuild), else "go".'
const OVERRIDES = (what) => `every TUNE / CAL key or constant ${what} changes (a json key it sets counts) is checked against ${T}/build/tune.json, ${T}/build/calibration.json (a json copy of the batch where one finished) and the \`**\` merge in the stage script that reads them; a key that shadows the new default is a major by rule (never a blocker), naming the file and the key.`

// How each path of an item starts (writer and reviewer).
const startLine = (it, i, p) => {
  const k = kindOf(it, p), s = src[i][p]
  if (k === 'new') return `- ${p}: start empty (a new file: "${T}/${p}" must not exist yet)`
  const j = k === 'json' ? it.json.find(x => lc(x.file) === lc(p)) : null
  return `- ${p}: start from "${s}"${s.startsWith(`${OUT}/`) ? ' (an earlier item\'s output; keep its edits)' : ''}${j ? ` (a JSON file: set only these top-level keys, nothing else: ${JSON.stringify(j.set)})` : ''}`
}
const notesBlock = (it) => it.notes.length ? `Apply-order notes for this item (rows the main session assigned to it):\n${it.notes.map(n => `- ${n}`).join('\n')}\n` : ''

const writerPrompt = (it, i) => `${common(it.id, BOX.writer)}

You are the edit writer for plan item ${it.id}. The checked draft is "${T}/${it.draft}" (read all of it; start with its CHANGE sections, probes, the guard rows, order notes and its Premise check).
${notesBlock(it)}Your files, with the copy each one starts from:
${it.paths.map(f => startLine(it, i, f)).join('\n')}
${deps[i].length ? `Earlier items that touch the same files and already wrote their copies: ${deps[i].map(j => `${items[j].id} (${OUT}/${items[j].id}/edit.json)`).join(', ')}. Read their edit.json first; their node names and constants are now part of your source.\n` : ''}Do:
1. First check the inputs: every "start from" path exists and every "start empty" path is absent from build/ (ls). If one is not as stated, write nothing, write no .done, name the path in open_questions and left, and return complete false. Then apply every change the draft lists for your files, and nothing else. A change the draft puts in a file you do not own (or a json key you were not given) goes in open_questions, not in that file. Match on quoted text, not line numbers (line numbers in a draft predate other edits). Comments: only on the lines you change, plus the docstring sentences the notes name; do not reword a comment on a line you leave as it is.
2. Follow the sdkit signatures (${SK}/scripts/sdkit.py: grep each function you call) and ${SK}/references/sd_craft.md sections 2 and 5 (Blend argument order, Levels arguments, Histogram Scan direction). Keep the file's idiom and node-name prefixes. Mark each constant a later probe or fit sets with a comment saying which step fits it (that comment is on a changed line), and list it in placeholders.
3. Write the full new copy of each file to ${OUT}/${it.id}/<same relative path> (for build/x.py: ${OUT}/${it.id}/build/x.py). A JSON file: copy its source, set only the listed top-level keys to the listed values (a key the source lacks is added at the end and named in open_questions), keep everything else as it was (indent, key order, number formatting; edit the text of those values rather than re-dumping the file when a dump would change its layout), then diff the copy against its source: only those keys differ. A new file starts empty and gets the draft's content. ${compileLine}
4. Write ${OUT}/${it.id}/edit.json: {"files", "summary", "new_nodes", "removed_nodes", "rebuild_from", "placeholders", "open_questions"} (files: exactly the paths listed above, spelled as above; rebuild_from: the first stage script a rebuild must run so every changed node is recreated).
5. Last act, only when every draft change is written and every copy compiled or parsed: run \`${STAMP}\` and write that one line to ${OUT}/${it.id}.done. Without it the main session does not treat the item as done.
Return the same fields as edit.json plus started, ended, complete, compile (one entry per file above, json included) and left.`

const reviewerPrompt = (it, i, w) => `${common(`${it.id}.review`, BOX.reviewer)}

You are the edit reviewer for plan item ${it.id}: read-only, adversarial, specific. The checked draft is "${T}/${it.draft}". The writer's copies are in ${OUT}/${it.id}/ (edit.json beside them); the writer reported:
${JSON.stringify(capReport(w))}
(fields cut with "[cut" or "more" are complete in ${OUT}/${it.id}/edit.json)
${notesBlock(it)}Each copy started from:
${it.paths.map(f => startLine(it, i, f)).join('\n')}
Check first that ${OUT}/${it.id}.done exists; if it does not, say so as a blocker. Then diff each copy against its starting file and check:
1. FIDELITY: every change the draft lists for these files is present (an extra change is judged under SCOPE); each json copy differs from its source in the listed keys only; the node names, files and registry entries that other stage scripts (build/*.py as they are now, the other items' copies in ${OUT}/), the export scripts (export*.py) and registry.json read are still produced, with the same names. registry.json lists names that exist today; it proves nothing about the copies, so read the copies' own code for every new name.
2. CODE: every sdkit call matches its definition in ${SK}/scripts/sdkit.py (argument count and order; Blend (name, mode, source, destination); Levels arguments; parameter ids); Histogram Scan direction and Blend/divide semantics as in ${SK}/references/sd_craft.md section 5; unique node names; every node read exists upstream in stage order. ${compileLine}
3. OVERRIDES: ${OVERRIDES('this item')}
4. SCOPE: list any changed line that is neither a draft change nor a notes row as a minor issue; a notes row that was not carried out is an issue too (a minor when it is a docstring or comment sentence).
${SEVERITY} ${VERDICT} Do not fix anything.
Write ${OUT}/${it.id}.review.json as {"verdict", "issues": [{"severity", "file", "line", "problem", "fix"}]}, then run \`${STAMP}\` for "ended". Return that object plus started and ended.`

const crossPrompt = (rows, finals) => `${common('cross', BOX.cross)}

You are the cross-checker for this apply batch: read-only. Every item's writer has returned; reviewers may still be running. The items, in apply order, with their writers' reports:
${JSON.stringify(rows, null, 1)}
Fields cut with "[cut" or "more" are complete in each item's edit.json: ${rows.map(r => `${r.id}: ${OUT}/${r.id}/edit.json${r.done ? '' : ' (not finished: the file may be missing or partial)'}`).join('; ')}. Items with "done": false have no finished copy; judge only what their report and any partial copy show, and say so in the issue.
The file each item rewrote ends in this state (the copy of the last item whose writer finished; nothing is in build/ yet):
${finals.map(x => x.copy ? `- ${x.file}: "${x.copy}" (item ${x.by})` : x.isNew ? `- ${x.file}: no finished copy; build/ has no such file (a new file nobody finished)` : `- ${x.file}: no finished copy; build/ keeps its own "${T}/${x.file}"`).join('\n')}
Check across the items and the unchanged build/*.py:
1. conflicts between items: two items editing the same node, constant, parameter or json key to different values; a later item undoing or overwriting an earlier item's change;
2. names read across files: every node name, registry key, preset or constant that one stage script (changed or unchanged) reads from another is still produced by the final copy of the other, in stage order; no node name is created twice in one graph; reset() prefixes of each stage still cover its new nodes;
3. rebuild order: each item's rebuild_from is early enough for every node the batch changes;
4. overrides: ${OVERRIDES('an item')}
${SEVERITY} ${VERDICT} Do not fix anything.
Write ${OUT}/cross.review.json as {"verdict", "issues": [{"severity", "file", "line", "problem", "fix"}]}, then run \`${STAMP}\` for "ended". Return that object plus started and ended.`

const counts = r => r && Array.isArray(r.issues)
  ? { blocker: r.issues.filter(x => x.severity === 'blocker').length, major: r.issues.filter(x => x.severity === 'major').length, minor: r.issues.filter(x => x.severity === 'minor').length }
  : { blocker: 0, major: 0, minor: 0 }
const total = c => c.blocker + c.major + c.minor
// The verdict comes from the issue counts only: a blocker issue gives "blocker", else a major gives "fix" (the main
// session repairs before the rebuild), else "go". A written verdict that disagrees (a "fix" or "blocker" with no such
// issue, or a "go" with issues) is logged and returned as verdict_said, so a stronger claim is never dropped silently.
const verdictOf = r => {
  if (!r) return null
  const c = counts(r)
  const v = c.blocker > 0 ? 'blocker' : c.major > 0 ? 'fix' : 'go'
  if (v !== r.verdict) log(`review verdict corrected to ${v}: it said ${r.verdict} with ${c.blocker} blocker and ${c.major} major issue(s)`)
  return v
}
const judged = r => { const verdict = verdictOf(r); return verdict !== null && verdict !== r.verdict ? { verdict, verdict_said: r.verdict } : { verdict } }
const oneLine = x => { const t = `${x.file}:${x.line} ${x.problem}`; return t.length > 200 ? `${t.slice(0, 197)}...` : t }
const short = (r, sev) => (r && Array.isArray(r.issues) ? r.issues.filter(x => x.severity === sev).map(oneLine) : [])

log(`edits: ${items.length} item(s), round ${R}; chaining: ${items.map((it, i) => `${it.id}${deps[i].length ? ' after ' + deps[i].map(j => items[j].id).join('+') : ''}`).join(', ')}`)

phase('Edit')
// Writers: an item waits only for the earlier writers it shares a path with. Reviewers start from their own writer.
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
    if (!w) { log(`writer ${it.id} returned nothing`); return { ok: false, w: null, blocked_by: [] } }
    const g = gaps(it, w)
    const ok = w.complete === true && Array.isArray(w.compile) && w.compile.length > 0 && w.compile.every(c => c && c.ok) && g.compiled.length === 0 && g.reported.length === 0
    if (g.reported.length || g.extra.length || g.respelled.length) log(`writer ${it.id} reported files differ from the item's list (the row uses the item's list): ${[g.reported.length ? `not reported ${g.reported.join(', ')}` : '', g.extra.length ? `not in the list ${g.extra.join(', ')}` : '', g.respelled.length ? `not spelled as listed ${g.respelled.join(', ')}` : ''].filter(Boolean).join('; ')}`)
    if (!ok) log(`writer ${it.id} incomplete: ${[(w.left || []).join('; '), w.complete !== true || !Array.isArray(w.compile) || !w.compile.length || !w.compile.every(c => c && c.ok) ? 'compile failed or no compile result' : '', g.compiled.length ? `not compiled ok: ${g.compiled.join(', ')}` : '', g.reported.length ? `not reported written: ${g.reported.join(', ')}` : ''].filter(Boolean).join('; ')}`)
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
const crossRows = items.map((it, i) => ({
  id: it.id, files: it.paths, done: written[i].ok,
  // the json sets and notes come from args, are not in edit.json, and the overrides check works from them: never cut
  ...(it.json.length ? { json: it.json.map(j => `${j.file} set ${JSON.stringify(j.set)}`) } : {}),
  ...(it.notes.length ? { notes: it.notes } : {}),
  report: written[i].w ? capReport({ summary: written[i].w.summary, new_nodes: written[i].w.new_nodes, removed_nodes: written[i].w.removed_nodes, rebuild_from: written[i].w.rebuild_from, placeholders: written[i].w.placeholders, open_questions: written[i].w.open_questions }) : null,
}))
const crossP = written.some(x => x.w)
  ? agent(crossPrompt(crossRows, finalCopies(written)), { label: 'cross-check', phase: 'Cross-check', schema: REVIEW_SCHEMA })
  : Promise.resolve(null)
const [reviews, cross] = await Promise.all([Promise.all(reviewP), crossP])

const dead = []
const out = items.map((it, i) => {
  const res = written[i], r = reviews[i], w = res.w
  if (!w && !res.blocked_by.length) dead.push(`edit:${it.id}`)
  if (w && !r) dead.push(`review:${it.id}`)
  const c = counts(r)
  const oq = w && Array.isArray(w.open_questions) ? w.open_questions.filter(x => typeof x === 'string') : []
  const row = {
    id: it.id, done: res.ok, ...judged(r), issues: total(c), counts: c, blockers: short(r, 'blocker'), majors: short(r, 'major'),
    files: res.ok ? it.paths.map(p => ({ build: p, copy: `${REL_OUT}/${it.id}/${p}` })) : [],
    aux: res.ok ? [`${REL_OUT}/${it.id}/edit.json`, `${REL_OUT}/${it.id}.done`] : [],
    files_reported: w && Array.isArray(w.files) ? w.files : [],
    open_questions: oq.slice(0, 8).map(x => cap(x, 300)), n_open_questions: oq.length,
  }
  if (res.blocked_by.length) row.blocked_by = res.blocked_by
  return row
})
if (written.some(x => x.w) && !cross) dead.push('cross-check')
const cc = counts(cross)
const crossOut = cross ? { ...judged(cross), issues: total(cc), counts: cc, blockers: short(cross, 'blocker'), majors: short(cross, 'major') } : null
const nItemMajor = out.reduce((n, o) => n + o.counts.major, 0), nItemsMajor = out.filter(o => o.counts.major > 0).length
const readIn = [nItemMajor > 0 ? '<id>.review.json' : '', cc.major > 0 ? 'cross.review.json' : ''].filter(Boolean).join(' and ')
const majorPart = `${nItemMajor + cc.major} major(s)${nItemsMajor ? ` in ${nItemsMajor} item(s)` : ''}${cc.major ? `${nItemsMajor ? ' +' : ' in'} cross-check` : ''}${readIn ? ` to read in ${readIn} before the rebuild` : ''}`
log(`edits done: ${out.filter(o => o.done).length} of ${out.length} items done, ${out.filter(o => o.verdict === 'blocker').length} review blocker(s), ${majorPart}, cross-check ${crossOut ? crossOut.verdict : 'missing'}${dead.length ? `; returned nothing: ${dead.join(', ')}` : ''}`)

return { round: R, items: out, cross: crossOut, dead }
