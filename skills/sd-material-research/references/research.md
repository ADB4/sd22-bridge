# Research

Research turns "make a weathered X" into facts the graph can obey: dimensions, layers, processes, invariants and PBR
values, each with a source. Its output feeds the spec. The goal is better decisions, not a long bibliography.

## A. Material with a bundled sheet

Bundled sheets: `references/materials/*.md` (brick, asphalt, concrete, wood_planks, and any added later).

1. Read the sheet in full. Note its date and its stated scope.
2. List what this request needs that the sheet doesn't settle: a regional standard, a sub-type, a process the user
   emphasised, a colour family, a finish.
3. Close those gaps with targeted searches, usually 5-15 (WebSearch/WebFetch; load them with ToolSearch
   `select:WebSearch,WebFetch`).
4. Re-verify any number that a **hard** check will depend on, unless the sheet already cites a primary source for it.
5. Write `<tools>/research/notes.md`:
   - the facts specific to this request, with sources
   - which sheet values you are using, by section
   - decisions the user should own (ask them in a short follow-up interview round)
6. If you found something that's wrong or missing in the sheet itself, fix the sheet. Add a line to its header saying
   what changed and when. The sheet is shared knowledge, and the next material benefits.

## B. Material without a sheet

Create one from `references/materials/_TEMPLATE.md`. It becomes a bundled sheet for next time.

**Team** (the same shape that produced the bundled sheets):
1. **Researcher(s).** For a broad material, split the work by area: (a) construction, layout, dimensions and layers;
   (b) aging and wear processes; (c) damage and deposition processes, plus PBR values. One researcher is enough for a
   narrow material. Each one writes its sections into the sheet file, or into section files you merge.
2. **Two auditors, working independently.**
   - *Physics:* an expert in the material who also knows procedural materials. Checks mechanisms, which layer each
     process acts on, what it reveals, the invariants and the common-mistakes table.
   - *Citations:* opens every cited source and confirms each number, its units and its context. Also checks PBR values
     against measured data.
3. **Reviser.** Verifies each audit finding before applying it, since auditors can be wrong too. Fills the gaps the
   auditors flagged, and makes sections 2, 4, 7 and 9 agree with each other.

**How to run it**
- If the user has opted into workflows (ultracode is on, or they asked for a workflow or multi-agent run), run
  `assets/workflows/research_sheet.js` with the Workflow tool (`scriptPath`). Its args are documented at the top of
  the file.
- Otherwise, spawn the same roles with the Agent tool: the researchers in one message, then the auditors in one
  message, then the reviser. The prompts in the workflow file work as Agent prompts too.
- If neither is available, do the three roles yourself in sequence, and do the audit as a separate, deliberately
  adversarial pass.

## Source rules

- Prefer, in order:
  1. standards and government manuals (ASTM, BS EN, FHWA/LTPP, USDA FPL Wood Handbook, ...)
  2. industry associations (BIA, Asphalt Institute, PCA/ACI, TRADA, ...)
  3. peer-reviewed papers
  4. conservation guidance (Historic England, NPS Preservation Briefs, ...)
  5. measured PBR datasets
- Use forums and blogs for visual examples only.
- Cite only what you have read. Every number carries `[n]` or `(est.)` with a reason.
- Watch out for these:
  - Solar reflectance (whole spectrum, often 0.05-0.40 for pavements) is not visible albedo.
  - Lab values are not field values.
  - "Typical" is not a range.
- Give ranges, and say which variant or region each applies to.

## Reference photos

- **User-supplied photos are the best reference.** Read them, then:
  - Measure proportions using a known size, e.g. brick height 65 mm → joint width.
  - Note which processes are visible, and where they sit relative to their drivers.
  - Note colour relationships: face vs revealed layer, wet vs dry.
  - Treat colours in photos as relative. White balance and exposure are unknown, so take absolute albedo from the PBR
    table.
- If web photos would help, give the user the search terms from the sheet's section 11, or ask before downloading
  anything.

## Done when

- Every process in the planned spec has a card: acts on, removes/adds, reveals, never, where, scale, progression.
- Every dimension and PBR value the spec will use has a source or an explicit estimate.
- The decisions that belong to the user are listed for them.
