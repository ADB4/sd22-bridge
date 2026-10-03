export const meta = {
  name: 'material-reference-sheet',
  description: 'Research one material reference sheet with sources, audit it through two independent lenses, then revise it',
  whenToUse: 'sd-material-research stage 2, for a material without a bundled sheet, when the user has opted into workflows',
  phases: [
    { title: 'Research', detail: 'web research into the template' },
    { title: 'Audit', detail: 'physics lens + citation lens, adversarial' },
    { title: 'Revise', detail: 'verify audit findings and apply' },
  ],
}

// args:
//   key        short id, e.g. "slate_roof"          file  sheet file name, e.g. "slate_roof.md"
//   material   what is researched, e.g. "natural slate roofing"
//   scope      what the sheet covers and what it doesn't
//   expert     who the physics auditor should be, e.g. "a roofing surveyor and slate geologist"
//   hints      bullet list of topics that must be covered (processes, dimensions, PBR, layout rules)
//   context    optional extra context (user request, reference photos already read, related project files)
//   skill_dir  absolute path of the skill (sheets go to <skill_dir>/references/materials/)
//   out_dir    absolute folder for audit changelogs (e.g. <tools>/research)
const A = args
const SHEET = `${A.skill_dir}/references/materials/${A.file}`
const TEMPLATE = `${A.skill_dir}/references/materials/_TEMPLATE.md`
const CHECKS = `${A.skill_dir}/references/checks.md`

const RESEARCH_OUT = {
  type: 'object',
  properties: {
    path: { type: 'string' },
    n_sources: { type: 'integer' },
    key_invariants: { type: 'array', items: { type: 'string' } },
    uncertainties: { type: 'array', items: { type: 'string' } },
  },
  required: ['path', 'n_sources', 'key_invariants', 'uncertainties'],
}

const AUDIT_OUT = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          section: { type: 'string' },
          claim: { type: 'string', description: 'the sheet text or number being challenged, quoted briefly' },
          problem: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          evidence: { type: 'string', description: 'URLs you opened and what they say, or the physical argument' },
          correction: { type: 'string', description: 'exact replacement text or value, with source' },
        },
        required: ['id', 'section', 'claim', 'problem', 'severity', 'evidence', 'correction'],
      },
    },
    missing: { type: 'array', items: { type: 'string' }, description: 'visually significant topics the sheet omits' },
    overall: { type: 'string' },
  },
  required: ['findings', 'missing', 'overall'],
}

const REVISE_OUT = {
  type: 'object',
  properties: {
    path: { type: 'string' },
    applied: { type: 'array', items: { type: 'string' } },
    rejected: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, why: { type: 'string' } }, required: ['id', 'why'] } },
    added: { type: 'array', items: { type: 'string' } },
    n_sources: { type: 'integer' },
    summary: { type: 'string' },
  },
  required: ['path', 'applied', 'rejected', 'added', 'n_sources', 'summary'],
}

const PRINCIPLE = `The skill this sheet belongs to builds physically plausible procedural materials in Adobe Substance 3D Designer
(default use: real-time tiling surfaces, 2048 px, DirectX normals). Before designing a ${A.material} material, Claude reads this sheet,
so it must be accurate, specific, quantitative and sourced.

The principle the skill is built on comes from a brick material the user made. Erosion of a brick removes brick: it rounds the
arrises and spalls the face, which reveals more brick underneath. It never reveals more mortar, and the joint keeps its width,
because mortar sits beside the brick face, not beneath it. Generalise that reasoning to ${A.material}. For every process, work out:
- which layer it acts on
- whether it removes or adds material
- what lies beneath, in the same component
- where it happens, and why
- at what scale
- how it progresses
These become invariants the graph must obey, and numeric checks (the check vocabulary is in ${CHECKS}).`

phase('Research')
const research = await agent(`${PRINCIPLE}

TASK: write the reference sheet for: ${A.material}
SCOPE: ${A.scope}

Read first:
- ${TEMPLATE}: follow its section order and its source rules exactly.
- ${CHECKS}: the check types to reference in sections 5 and 9.
${A.context ? `\nCONTEXT:\n${A.context}\n` : ''}
Topics that must be covered, plus anything else visually significant you find:
${A.hints}

METHOD
- Load the web tools with ToolSearch, query "select:WebSearch,WebFetch".
- Run many searches (aim for 30-50). Use mode "extended" for niche or numeric questions.
- Prefer primary sources: standards, government and agency manuals, industry associations, peer-reviewed papers,
  conservation guidance, and measured PBR datasets such as physicallybased.info.
- Open and read the pages you cite. Never cite a page you have not read.
- Every number gets [n] or "(est.)" with a reason. Give ranges, and say which variant or region each applies to.
- Focus on what changes appearance at tile scale (0.5-5 m) and close up (cm). Skip chemistry with no visual consequence.
- Where procedural materials commonly fake something wrongly, say so explicitly in section 6.
- Recommended tile sizes must hold whole layout repeats, and the smallest important features must stay at least 2-3 px wide at 2048.

OUTPUT
- Write the sheet to ${SHEET}, in Markdown, about 450-750 lines. Write it section by section as you go so nothing is lost.
- Use plain, direct English and dense content, without padding.
- Do not touch any other file in ${A.skill_dir}. Never call substance-designer tools.
- Return the path, the number of sources, the most important invariants, and open uncertainties.`,
  { label: `research:${A.key}`, phase: 'Research', schema: RESEARCH_OUT })

if (!research) return { error: 'research agent failed' }
log(`${A.key}: sheet written with ${research.n_sources} sources`)

phase('Audit')
const LENSES = [
  {
    key: 'physics',
    prompt: `LENS: physics and procedural translation. Act as ${A.expert}, who also knows how procedural materials are built.
Audit the sheet's physics: mechanisms, which layer each process acts on, what it reveals, spatial drivers, progression,
interactions, the layer model and envelope, and above all the invariants (section 5) and the common-mistakes table (section 6).
Look for:
- wrong mechanisms
- processes that add where they should remove, or the reverse
- a process that reveals the wrong layer
- missing processes that are visually significant
- invariants that are false in some common real case (name the case)
- oversimplifications that would mislead a material artist
- contradictions between sections
Also check:
- section 9: targets consistent with sections 2 and 4
- section 10: build notes that would actually enforce the invariants
- whether each invariant's check is measurable with ${CHECKS}
Use web searches to confirm your objections. Do not object on taste; object only on physics or usability.`,
  },
  {
    key: 'citations',
    prompt: `LENS: numbers and citations. Act as an adversarial citation auditor.
For every number and every sourced claim:
- Open the cited source with WebFetch and confirm it says that: value, units and context.
- Flag misquotes, wrong units or conversions, and values taken out of context
  (e.g. solar reflectance presented as visible albedo, lab values presented as field values).
- Flag unsourced numbers that are not marked (est.), implausible estimates, and dead or irrelevant sources.
- Cross-check every PBR value against at least one independent measured source.
- Check that the recommended tile sizes hold whole layout repeats.
- Check that the key feature sizes stay at least 2-3 px wide at the stated mm/px.
Sample broadly: at least 25 claims. Report only real problems; confirmed claims need no entry.`,
  },
]

const audits = await parallel(LENSES.map(l => () => agent(`${PRINCIPLE}

You are auditing the reference sheet at ${SHEET} (material: ${A.material}; scope: ${A.scope}).
Read it fully, plus ${TEMPLATE} and ${CHECKS}.
Load the web tools with ToolSearch "select:WebSearch,WebFetch".

${l.prompt}

Be adversarial: the sheet's author may be confidently wrong. But only report what you can support.
Each correction must be exact enough to paste in. Do not edit the sheet yourself.
Also list visually significant topics the sheet omits.`,
  { label: `audit:${A.key}:${l.key}`, phase: 'Audit', schema: AUDIT_OUT }).then(r => r ? { lens: l.key, ...r } : null)))

const found = audits.filter(Boolean)
const nFind = found.reduce((s, a) => s + a.findings.length, 0)
log(`${A.key}: ${nFind} audit findings, ${found.reduce((s, a) => s + a.missing.length, 0)} gaps`)

phase('Revise')
const revised = await agent(`${PRINCIPLE}

You are revising the reference sheet at ${SHEET} (material: ${A.material}; scope: ${A.scope}).
Read it fully, plus ${TEMPLATE} and ${CHECKS}.
Load the web tools with ToolSearch "select:WebSearch,WebFetch".

Two independent auditors reviewed it. Their findings are below.
1. Verify each finding yourself before applying it. Auditors can be wrong too: open the sources.
2. Apply the corrections you confirm.
3. Reject the rest, with a reason.
4. Research and add the omitted topics that are visually significant, with sources.
5. Keep the template's structure.
6. Make the sheet self-consistent: numbers in sections 2, 4, 7 and 9 must agree, and every invariant must have an Enforce line and a Check line.
7. Remove or mark (est.) any claim you cannot support.
8. Finally, read the whole sheet once more, looking for contradictions and padding.

Edit ${SHEET} in place. Write a short changelog to ${A.out_dir}/${A.key}_changelog.md.

AUDITS:
${JSON.stringify(found, null, 1)}`,
  { label: `revise:${A.key}`, phase: 'Revise', schema: REVISE_OUT })

return { material: A.key, research, audits: found, revised }
