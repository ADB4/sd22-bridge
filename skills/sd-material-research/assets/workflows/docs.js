export const meta = {
  name: 'material-docs',
  description: 'Bring REFERENCE.md and spec.md up to the final build once: a drafter and an adversarial verifier per section group write verified JSON, then one agent splices it all-or-nothing and sets the REFERENCE header',
  whenToUse: 'sd-material-research stop point: the last final gate is green (SKILL.md stage 7, references/review.md §2)',
  phases: [
    { title: 'Draft', detail: 'one drafter per key, time-boxed 25 min' },
    { title: 'Verify', detail: 'one adversarial verifier per key, re-derives every value from build/, dry-runs docsplice.py, 15 min' },
    { title: 'Apply', detail: 'one agent (barrier): docsplice.py --apply, then the REFERENCE header' },
  ],
}

// Purpose: the REFERENCE.md written in round 1 is frozen (references/review.md §2) and its R4 goes stale; spec.md keeps
// the values the run changed. This workflow rewrites both once, after the last final gate, from what is BUILT.
//
// Launched by the skill at the stop point (SKILL.md "Stop point" and stage 7), in the background, once the last final
// gate is green. Run it once per material; it writes into <tools>/review/docs and the documents it splices.
//
// args (all required unless marked optional; a missing or wrong-typed one returns {error} before any agent):
//   round     N+1, the number of the last final gate's folder (<tools>/review/round<round>/ holds its scorecards and
//             suite.json; the ledger of the last apply is <tools>/review/round<round>/ledger.json); integer >= 1
//   tools     absolute path of the material's tools folder (agents cd there); no quote, $ or backtick in it
//   skill     absolute real path of the skill folder (scripts/docsplice.py, references/)
//   python    the numpy python, a literal absolute path (never a command substitution or a file to read)
//   sections  optional [{key, scope}] (default: r4, r2_r6_r7_r8, spec). key: letters, digits, _ or -, unique ignoring
//             case (the Mac volume folds case; a key names two files). scope: what the key rewrites, in words. Keys
//             must own disjoint headings and passages: they are applied in order, each against the text before it.
//   keys      optional ['r4', ...]: runs only those default keys, by name, with their default scope text and in the
//             default order (a name that is not a default key: error). Use it to rerun one default key without
//             retyping its scope. `sections` and `keys` together: error.
// Per key, pipeline (no barrier): drafter -> verifier. The drafter writes <tools>/review/docs/<key>.draft.json, the
// verifier <key>.verified.json, both {key, started, ended, replace_sections: [{file, heading, text}], edits: [{file,
// old, new}], claims: [{claim, source}], corrections, open_questions}; the verifier first runs
// `python3 <skill>/scripts/docsplice.py --tools <tools> --dir review/docs --dry <key>` until it exits 0. Then one apply
// agent (barrier: it needs every verified key) runs `docsplice.py --apply`, which applies nothing on any problem, and
// edits the REFERENCE header: `Valid for:` (the final gate's manifests' exported_at), the Frozen line and `Changed in
// the last update:`. It writes <tools>/review/docs/apply.json {utc, applied, skipped, files, backup, header} as its
// last act.
// Partial apply (a deliberate deviation from "apply every verified key"): when the dry run of all keys together fails,
// the apply agent applies only the keys whose own dry run is clean and lists every other key in `skipped` with its
// problem lines; it never repairs a verified file. The skipped keys are rerun by hand (fix the file, `--apply <key>`).
// Outputs: review/docs/<key>.draft.json, <key>.verified.json, <label>.progress.md per agent (labels draft-<key>,
// verify-<key>, apply), apply.json, backup/<utc>/ (docsplice's copies of the files it changed), the changed documents.
// R4 is a description of the build as it is now. The change history stays in review/round*/ledger.json, review/patches/
// order.jsonl and review/decisions.json; the text gives the current state and one pointer line to them, in the
// "## R4" intro.
// Boxes (minutes, stated in each prompt with the progress-file rule): drafter 25, verifier 15, apply 10. Agents inherit
// the session's model and effort. Helper scripts go only in review/docs/scratch/ (created if missing, listed in the
// progress files; the folder is left for the main session to delete).
// Returns {round, keys: [{key, status, n_sections, n_edits, corrections, draft_corrections, dry_exit, n_dry_problems,
// open_questions, box, left, draft_box, draft_left}], apply, held}. status: verified | verified_box_hit |
// box_hit_dry_failed | dry_failed | dead_draft | dead_verify | dead. corrections (the verifier's changes to the draft)
// and draft_corrections (the drafter's build-vs-old-text findings) are arrays of strings, capped by this script to 20
// items of 200 chars each; the schema states the limits in its description but does not enforce them, so an oversize
// list is cut here and never makes an agent's whole summary invalid (a null return is only for a dead agent). box is
// 'not_hit' or 'hit'; when either agent reports hit the key is verified_box_hit (box_hit_dry_failed when its dry run
// also failed or never ran clean) with the progress file's `left` note, and the apply agent does NOT
// apply it unreviewed: it is listed in `held` and the main session reads the key's progress files and verified file,
// finishes or accepts it, and applies it with `docsplice.py --apply <key>`. dry_failed (no box hit) is passed to the
// apply agent, which re-checks it and skips it when the dry run still fails.

const BOX = { draft: 25, verify: 15, apply: 10 }
const STAMP = 'date -u +%Y-%m-%dT%H:%M:%SZ'
const defaultSections = round => [
  { key: 'r4', scope: `REFERENCE.md section "## R4" (Graph architecture), all of it. Replace each "###" subsection whole, one replace_sections entry per subsection with its heading copied exactly (the heading's node count included), as the graph is built now: the stages in build order, node names with their current parameter values, the composition with its operand order, the calibration tables used, which masks come from the layout only. Use edits for the lines of the "## R4" intro. The frozen REFERENCE is stale here (it was written in round 1): compare its text with the stage scripts value by value, keep every still-valid fact, and drop or correct only what the build contradicts. Count nodes from registry.json or the graph's export manifest, never from memory. Scripts: for every script the text tells the reader to run, grep the node names it reads in registry.json; when one is missing the script is stale: say so in the text ("stale: do not run", with the missing name) and never tell the reader to run it. Readers: for every node you name, find the stage script that reads it (grep the build for its name); say plainly which nodes feed no output (probes, unused randoms) with their count. History: this section is the build as it is now; the change history stays in the ledgers (review/round*/ledger.json), review/patches/order.jsonl and review/decisions.json. Drop sentences that only retell what past rounds changed (keep the facts they state about the build as it is now), and put a single one-line pointer to those three files at the end of the "## R4" intro, as an edit; no pointer per subsection.` },
  { key: 'r2_r6_r7_r8', scope: `REFERENCE.md sections "## R2" (physics digest), "## R6" (variant presets), "## R7" (files) and "## R8" (metric caveats and deprecations). R2: the process cards and invariant text the run changed, and every check id they name (a retired id gets its successor; mark hard or soft as checks/*.json has it), as edits. R6: the presets table and the PBR keys as the presets file and the shading stage scripts hold them now, as edits. R7: the files, folders and scripts the run added, renamed or retired (review/round<n>/ folders, measure scripts, scorecards, previews, ledgers, patches), as edits or one replace. R8: ONE replace_sections entry for the whole "## R8" section: keep every caveat that still holds; add the final gate's soft misses each with its cause and whether it is accepted or carried, the retired checks with their successors, the run's deviations from the plan (review/decisions.json rows of kind deviation_from_user_answer, requirement_trade, technical and look_trade, the ledgers' notes), and the custom measures. Do not touch R1, R3, R5 or R9.` },
  { key: 'spec', scope: `spec.md, edits only: the values the run changed (the variants and presets section and the PBR targets, as the build and review/decisions.json now have them), the invariants' check ids and the acceptance table where the run renamed or retired a check (checks/*.json, checks/gen_checks.py), the graph architecture section (node counts, stage structure as built), and a risk or open question the run settled. Bump the version line (see the shape of the existing one) to the next minor version with the UTC date of your date -u and ", round ${round} docs pass". NEVER change the user requirements section (section 1), and never a value the user gave verbatim (section 1 and the interview answers in REFERENCE R1 quote them; a value the run changed through a recorded design call with changes_spec true is the exception, and you cite the decisions.json row id).` },
]

// ----- arg validation: returns {error} before any agent
const A = args !== null && typeof args === 'object' && !Array.isArray(args) ? args : null
const err = m => ({ error: `docs.js: ${m}` })
const DEFAULT_KEYS = defaultSections(1).map(s => s.key)
const goodPath = s => typeof s === 'string' && s.startsWith('/') && s.length > 1 && !/["$`\\\n\r\0]/.test(s)
const isKey = k => typeof k === 'string' && /^[A-Za-z0-9_-]+$/.test(k) && k.length <= 40
let SECTIONS = null
let bad = null
if (!A) bad = err('args must be an object {round, tools, skill, python, sections?, keys?}')
else if (!Number.isInteger(A.round) || A.round < 1) bad = err('args.round must be an integer >= 1 (the last final gate\'s round, N+1)')
else if (!goodPath(A.tools)) bad = err('args.tools must be an absolute path string (no quote, $, backtick or backslash)')
else if (!goodPath(A.skill)) bad = err('args.skill must be an absolute path string (no quote, $, backtick or backslash)')
else if (!goodPath(A.python) || /\$\(|\n/.test(A.python)) bad = err('args.python must be a literal absolute path string')
else if (A.sections != null && A.keys != null) bad = err('args.sections and args.keys together: pass one (keys selects default keys, sections replaces them)')
else if (A.keys != null && (!Array.isArray(A.keys) || A.keys.length === 0 || A.keys.some(k => typeof k !== 'string'))) bad = err('args.keys must be a non-empty array of default key names (' + DEFAULT_KEYS.join(', ') + ')')
else if (A.keys != null && A.keys.some(k => !DEFAULT_KEYS.includes(k))) bad = err(`args.keys: ${JSON.stringify(A.keys.find(k => !DEFAULT_KEYS.includes(k)))} is not a default key (${DEFAULT_KEYS.join(', ')}); use args.sections for a key of your own`)
else if (A.keys != null && new Set(A.keys).size !== A.keys.length) bad = err('args.keys lists a key twice')
else if (A.sections !== undefined && A.sections !== null) {
  if (!Array.isArray(A.sections) || A.sections.length === 0) bad = err('args.sections must be a non-empty array of {key, scope}')
  else {
    const seen = new Set()
    for (const s of A.sections) {
      const k = s && s.key
      if (!s || typeof s !== 'object' || !isKey(k) || typeof s.scope !== 'string' || !s.scope.trim()) {
        bad = err(`section ${JSON.stringify(k)}: needs a key of letters, digits, _ or - (40 at most) and a non-empty scope string`)
        break
      }
      const kk = k.toLowerCase()
      if (seen.has(kk) || kk === 'apply' || kk === 'backup') { bad = err(`section key ${JSON.stringify(k)} is duplicated ignoring case or reserved (apply, backup)`); break }
      seen.add(kk)
    }
    if (!bad) SECTIONS = A.sections
  }
}
if (bad) return bad

const R = A.round
if (!SECTIONS) SECTIONS = defaultSections(R).filter(s => !A.keys || A.keys.includes(s.key))
const T = A.tools
const SKILL = A.skill
const PY = A.python
const FINAL = `review/round${R}`
const OUT = `${T}/review/docs`
const SPLICE = `python3 "${SKILL}/scripts/docsplice.py" --tools "${T}" --dir review/docs`

// The box and progress-file rule every agent prompt carries (the shipped workflows' common rule).
const boxRule = (label, min, canReport = true) => `Run \`${STAMP}\` first. After every script run, append a \`date -u\` line and what it showed to \`${OUT}/${label}.progress.md\`. Box: ${min} minutes; at the box, stop, write what is left in the progress file and return what you have.${canReport ? ' If the box stopped you, write that note as a line starting "left:", return box "hit" and the same text in "left"; otherwise box "not_hit".' : ' If the box stopped you, write that note as a line starting "left:" and put it in "notes".'}`

const COMMON = `You are helping close a procedural material built with the sd-material-research skill (Adobe Substance Designer). The last final gate is green; your job is documentation only: REFERENCE.md and spec.md describe the build as it was in round 1 or at the last docs pass, and are brought up to the final build once, now.
Tools folder: ${T} (cd there; paths below are relative to it unless absolute). Skill folder: ${SKILL}. numpy python: ${PY}.
HARD RULES: never call substance-designer tools; never edit anything but the output files named in your task (not build/, checks/, registry.json, review/REFERENCE.md, spec.md, ledgers or decisions), plus helper scripts, which go only in ${OUT}/scratch/ (create it if missing; list every file you put there in your progress file), except the apply agent, which edits REFERENCE.md and spec.md only through docsplice.py and the REFERENCE header lines named in its task; never commit; heavy numpy jobs are not needed (reading files, grep and small python one-liners are enough).

WHAT IS BUILT is the authority. Where a ledger, a draft, a plan or the old documents differ from the build, the build wins, and you say so in "corrections". Sources, newest knowledge first:
- build/*.py (the stage scripts: node names, parameters, composition and operand order) and the json files beside them (tune, calibration, presets and the like); the *.py and *.json files at the tools folder root (composition, measure and config files; \`ls\` the root); any file or script named in a backticked path of the text you replace (run \`ls\` on it; a missing one goes to open_questions with the ls output); registry.json (node names and counts); the graph's export manifests (their paths come from the maps.dir and maps.prefix of checks/*.json: <prefix>manifest.json);
- checks/*.json (check ids, hard or soft, targets), checks/gen_checks.py, checks/ladder.py, checks/wrong_build_cases.py;
- ${FINAL}/ (the final gate): scorecard_<variant>.json and .md, suite.json, ledger.json (the last apply: items, decisions, apply), fixcheck output; the earlier review/round*/ folders (lead.json premises_corrected, ledger.json, findings.md); review/decisions.json (every call the run settled, with its row id); review/patches/order.jsonl (the edits in application order); CONTEXT_PROMPT.md;
- the documents being updated: review/REFERENCE.md (sections "## R<k> <title>", "###" inside; its first lines before the first "##" are the apply agent's header, never yours) and spec.md; node semantics: ${SKILL}/references/sd_craft.md section 5 and ${SKILL}/scripts/sdkit.py (check a composition's argument order there before describing it).
NAMED THINGS: every script, file or command the text you write names must exist (ls it) and be usable against the current build; a name you cannot find is not written as fact (open_questions, with the ls or grep output).
STYLE: match the documents as written: terse technical English, bullets, \`code\` for node, file, check and parameter names, numbers with units, lines wrapped at 120 characters (table rows excepted), no marketing, no dashes as sentence connectors (use commas, colons, parentheses). Keep every still-valid fact. Every number you write is traceable to a source above; mark anything estimated "(est.)".
FORMAT of your JSON file (paths relative to the tools folder): {"key": "<key>", "started": "<date -u>", "ended": "<date -u>", "replace_sections": [{"file", "heading", "text"}], "edits": [{"file", "old", "new"}], "claims": [{"claim", "source"}], "corrections": [str], "open_questions": [str]}. A replace_sections "heading" is an existing heading line copied exactly (it must occur exactly once as a whole line of the file); the section it names runs to the next heading of the same or a higher level; "text" is the whole replacement, starting with a heading of the SAME level (its wording may change, a node count does) and holding no other heading of that level or higher. An edits "old" is copied from the CURRENT file (no line-number prefixes, mind the line breaks), must occur exactly once, and is replaced by "new"; prefer whole bullets or paragraphs. "claims" lists each specific value or name you wrote with its source (file:line or file and key).
`

const SUMMARY = {
  type: 'object',
  properties: {
    key: { type: 'string' },
    started: { type: 'string', description: `UTC, from \`${STAMP}\` as your first action` },
    ended: { type: 'string', description: `UTC, from \`${STAMP}\` just before you write your file` },
    file: { type: 'string', description: 'the JSON file you wrote' },
    n_sections: { type: 'integer' },
    n_edits: { type: 'integer' },
    corrections: { type: 'array', items: { type: 'string' }, description: 'drafter: places where the build differed from a ledger, draft or old text; verifier: changes you made to the draft. One string each (200 characters at most, the 20 most important; longer is cut by the workflow), empty when none' },
    open_questions: { type: 'array', items: { type: 'string' } },
    dry_exit: { type: 'integer', description: 'verifier only: the exit code of the last docsplice.py --dry run on your verified file (0 = clean)' },
    dry_problems: { type: 'array', items: { type: 'string' }, description: 'verifier only: the problem lines of that run, empty when clean' },
    box: { type: 'string', enum: ['not_hit', 'hit'], description: 'hit when the time box stopped you before the work was done' },
    left: { type: 'string', description: 'when box is hit: the "left" note you wrote in your progress file (what is not done); otherwise empty' },
  },
  required: ['key', 'started', 'ended', 'file', 'n_sections', 'n_edits', 'corrections', 'open_questions', 'box'],
}

const APPLY = {
  type: 'object',
  properties: {
    started: { type: 'string' },
    ended: { type: 'string' },
    applied: { type: 'array', items: { type: 'string' }, description: 'keys docsplice.py --apply applied' },
    skipped: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, problems: { type: 'array', items: { type: 'string' } } }, required: ['key', 'problems'] }, description: 'keys left out (no verified file, or problems in a dry run) with the problem lines' },
    files: { type: 'array', items: { type: 'string' }, description: 'files docsplice.py changed' },
    backup: { type: 'string' },
    apply_exit: { type: 'integer', description: 'exit code of the docsplice.py --apply run, -1 when none ran' },
    header: {
      type: 'object',
      properties: { valid_for: { type: 'string' }, frozen: { type: 'string' }, changed: { type: 'string' } },
      required: ['valid_for', 'frozen', 'changed'],
    },
    notes: { type: 'array', items: { type: 'string' } },
  },
  required: ['started', 'ended', 'applied', 'skipped', 'files', 'backup', 'apply_exit', 'header', 'notes'],
}

const draftPrompt = s => `${COMMON}
YOUR TASK: drafter for key "${s.key}" (round ${R} final gate, folder ${FINAL}/).
SCOPE: ${s.scope}
Read the sources your scope needs in full, then write your JSON to ${OUT}/${s.key}.draft.json (create the folder if it is missing) and return the compact summary (counts, not the document). Before you write, check each "old" with python (open(f).read().count(old) == 1) and each heading (exactly one whole-line match).
${boxRule(`draft-${s.key}`, BOX.draft)}`

const verifyPrompt = s => `${COMMON}
YOUR TASK: adversarial verifier for key "${s.key}". The drafter's brief was:
---
${s.scope}
---
The drafter's output is ${OUT}/${s.key}.draft.json: read it from the file, it is the authority over any summary. Assume the drafter made mistakes: wrong operand order in a composition, a stale value copied from the old text or a plan draft that the build changed, a check marked hard that is soft, a retired check id, an invented node count.
Method, in this order:
1. Values: re-derive EVERY number, node name, key, parameter and check id in the new text from the sources yourself, and correct each error in the text. \`ls\` every script, file and command the new text names (a missing one is a correction or an open question with the ls output), and for each script the text tells the reader to run, grep the node names it reads in registry.json: a stale one is never recommended.
2. Coverage: is anything the scope requires missing? Consistency inside the key: every output, port, node and file name in one replaced subsection must appear identically in the other subsections and edits of this key (grep each backticked name of the new text against registry.json and the Outputs bullet); each mismatch is a correction. Is a still-valid fact of the old text dropped without reason? Does a new sentence contradict another section of the documents that this key does not change? Does anything change the user requirements section of spec.md, a value the user gave verbatim, or an R1, R3, R5 or R9 section of REFERENCE.md? Undo it.
3. Mechanics: write the corrected JSON (same format; "corrections" lists each change you made and why, empty when none) to ${OUT}/${s.key}.verified.json, then run \`${SPLICE} --dry ${s.key}\` from the tools folder. It prints every problem (a heading not found exactly once, an "old" not found exactly once, a replacement that starts at the wrong heading level or holds a heading that would end the section early, a path outside the tools folder) and exits 1; fix the file and rerun until it exits 0. Long-line warnings: wrap them.
4. Style as above.
Return the compact summary with dry_exit and dry_problems from your last run.
${boxRule(`verify-${s.key}`, BOX.verify)}`

const applyPrompt = keys => `${COMMON}
YOUR TASK: the apply agent. Verified files: ${keys.map(k => `${OUT}/${k}.verified.json`).join(', ')}. You are the one agent allowed to change the documents, through docsplice.py and the REFERENCE header lines below.
1. Dry run: \`${SPLICE} --dry ${keys.join(' ')}\`. Exit 0: go to 2. Exit 1: run \`${SPLICE} --dry <key>\` for each key to find the keys with problems, then \`--dry\` on the clean keys together; apply only a clean set (and list every other key in "skipped" with its problem lines). A key whose verified file is missing is skipped. Do not repair a verified file yourself.
2. \`${SPLICE} --apply <clean keys>\` (it applies nothing on any problem and prints the backup folder, OUT/backup/<utc>). Record its exit code, files and backup in apply.json.
3. Edit the header of review/REFERENCE.md (the lines before its first "## " heading), nothing else in that file, whatever the splice did:
   - "Valid for:" field: one entry "<variant> <exported_at>" per variant, comma separated, the exported_at read from each variant's manifest of the final gate (checks/*.json: maps.dir and maps.prefix, relative to the config's folder, + manifest.json), in the shape the line has now, ending "; spec version <n>." with the version now in spec.md's header. A variant whose manifest is missing keeps its old entry, and you say so in notes.
   - the Frozen line: exactly "Frozen at round ${R}; current parameters are in build/ and the ledger." (replace the existing "Frozen at round" line; insert it under "Valid for:" when there is none).
   - "Changed in the last update:" field (write it as one line): the REFERENCE section ids the applied keys rewrote or edited (R2, R4, ...; read the "## R<k>" a replaced heading or an edit's old text falls under) and "spec.md" when the spec key applied, then " (round ${R} docs pass)"; "none" when nothing was applied.
   Each of these three fields is the whole paragraph from its label to the next blank line or the next label, not just the first line: replace every continuation line with the new value (a field that runs over several lines becomes the new text, however many lines it had), and leave no line of the old value behind. Check afterwards with grep that each label occurs exactly once and that no old continuation line remains (print the header and read it).
4. Last act: write ${OUT}/apply.json {utc (from date -u), applied, skipped, files, backup, header: {valid_for, frozen, changed}} and return the summary.
${boxRule('apply', BOX.apply, false)}`

const cap = c => (Array.isArray(c) ? c : []).filter(x => typeof x === 'string').slice(0, 20).map(x => (x.length > 200 ? x.slice(0, 197) + '...' : x))
const trim = r => r ? { key: r.key, n_sections: r.n_sections, n_edits: r.n_edits, corrections: cap(r.corrections), dry_exit: r.dry_exit === undefined ? null : r.dry_exit, n_dry_problems: (r.dry_problems || []).length, open_questions: r.open_questions, box: r.box, left: r.left || '' } : null

phase('Draft')
log(`docs pass for round ${R}: keys ${SECTIONS.map(s => s.key).join(', ')}; drafter ${BOX.draft} min, verifier ${BOX.verify} min, apply ${BOX.apply} min`)
const res = await pipeline(SECTIONS,
  s => agent(draftPrompt(s), { label: `draft:${s.key}`, phase: 'Draft', schema: SUMMARY }),
  async (dr, s) => {
    if (!dr) { log(`key ${s.key}: the drafter returned nothing`); return { key: s.key, status: 'dead_draft' } }
    const v = await agent(verifyPrompt(s), { label: `verify:${s.key}`, phase: 'Verify', schema: SUMMARY })
    if (!v) { log(`key ${s.key}: the verifier returned nothing; the draft is not applied`); return { key: s.key, status: 'dead_verify', draft: trim(dr) } }
    const hit = dr.box === 'hit' || v.box === 'hit'
    if (hit) log(`key ${s.key}: the time box was hit (${dr.box === 'hit' ? 'drafter' : ''}${dr.box === 'hit' && v.box === 'hit' ? ', ' : ''}${v.box === 'hit' ? 'verifier' : ''}); read review/docs/*-${s.key}.progress.md before applying`)
    // a key with a hit box is never passed to the apply agent, whatever its dry run did (it would re-run the dry check
    // and could apply the key unreviewed)
    const dryOk = v.dry_exit === 0
    const status = hit ? (dryOk ? 'verified_box_hit' : 'box_hit_dry_failed') : dryOk ? 'verified' : 'dry_failed'
    return { key: s.key, status, ...trim(v), draft_corrections: cap(dr.corrections), draft_box: dr.box, draft_left: dr.left || '' }
  })

const rows = SECTIONS.map((s, i) => res[i] || { key: s.key, status: 'dead' })
const ok = rows.filter(r => r.status === 'verified' || r.status === 'dry_failed')
const held = rows.filter(r => r.status === 'verified_box_hit' || r.status === 'box_hit_dry_failed').map(r => r.key)
if (held.length) log(`held, not applied (a time box was hit): ${held.join(', ')}; review them, then run docsplice.py --apply <key>`)
let apply = null
if (ok.length === 0) log('no key is ready to apply: nothing to apply')
else {
  phase('Apply')
  const dry = ok.filter(r => r.status !== 'verified').map(r => r.key)
  if (dry.length) log(`dry run still failing for ${dry.join(', ')}: the apply agent re-checks and skips them`)
  apply = await agent(applyPrompt(ok.map(r => r.key)), { label: 'apply', phase: 'Apply', schema: APPLY })
  if (!apply) log('the apply agent returned nothing; check review/docs/apply.json and the documents before rerunning')
}
log(`docs pass: ${rows.map(r => `${r.key} ${r.status}`).join(', ')}; applied ${apply ? apply.applied.join(', ') || 'none' : 'nothing'}`)
return { round: R, keys: rows, apply, held }
