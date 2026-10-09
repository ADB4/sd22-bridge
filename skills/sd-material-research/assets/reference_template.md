# <Material>: review reference

Valid for: <variant> <exported_at>, ... (from each variant's `<prefix>manifest.json`); spec version <n>.
Changed in the last update: created

Written in round 1, before the first delta brief. At the end of each apply, rewrite the sections the apply changed and
any section one of the last lead's `premises_corrected` entries contradicts (a corrected node-semantics premise also
goes into R5 and into the hand-off notes for the skill's `sd_craft.md` §5), then `Changed in the last update:` (the
section ids, or `none`). Set `Valid for:` in each preflight, after its export (`references/review.md` §1 step 5). Keep
every heading `## R<k> <title>` and use `###` inside a section: `scripts/make_brief.py` cuts sections by those
headings. `make_brief.py` copies R1, R5 and R9 into every delta brief (`review/round<N>/BRIEF.md`). Each lens also
reads the sections its row in `review/round<N>/lenses.json` names (all of this file when it names none); verifiers,
the re-verify agent and the lead read all of it.

Default sections per lens family, besides R1, R5 and R9 (the round's `lenses.json` names the real ones):

| lens family | sections |
|---|---|
| G1 requirements and invariants | R2 |
| G2 scale, proportion and layout | R3 R4 R6 |
| G3 process semantics | R2 R4 |
| G4 surface, edges and signal | R3 R7 R8 |
| G5 large surface and tiling | R7 |
| G6 colour, PBR and variants | R2 R6 R7 |
| fixcheck | R2 R4 R6 R7 |
| regressions | R4 R7 R8 |
| check audit | R2 R7 R8 |
| verifiers, re-verify agent, lead | all (the runner sets it) |

## R1 Requirements
The user's requirements from spec §1, verbatim, with ids R1..Rn, each marked hard or soft. Then the interview
answers, the defaults applied (and that they were applied, not chosen), and the intentional deviations, each with the
invariant it relaxes.

## R2 Physics digest
From the spec:
- the layer model and its ASCII cross-section (spec §4)
- the process cards: acts on, reveals, **Never**, where, shape and scale (spec §5)
- the invariants INV-1..k, each with its check ids (spec §6)
- the sheet's common-mistakes table, as the watch list

## R3 Scale
Tile m, px, mm/px, height depth per variant, normal format, and the viewing distance of each view.

## R4 Graph architecture
The sections in build order, with node names, current parameters and the stage script (`build/NN_*.py`) that sets
them; the composition (max/min/lerp); which masks come from the layout only.

## R5 Node semantics cheat sheet
Replace this line with `references/sd_craft.md` §5, verbatim (`make_brief.py` exits 2 until it has the cheat sheet's
`| Histogram Scan |` row). Histogram Scan direction and Blend divide order have caused wrong fixes.

## R6 Variant presets
The presets table (spec §7) with the current values, in physical units.

## R7 Files
- maps per variant (2048, 16-bit) and their `nowear` renders, with purpose
- how to load them: `matcheck.Ctx` on `checks/<variant>.json`, the loader snippet and its verified output
- region names (from the checks configs)
- previews (`review/round<N>/views_index.md`) and the preview shader: one light, height-field shadows on the raking
  views only, no IBL; judge colour from albedo-only views
- side reports

## R8 Metric caveats and deprecations
Metrics that mislead here (threshold choice, a reference window that includes the feature, circular masks), retired
check ids and what replaced them.

## R9 Severity rubric, acceptance-target rules and verifier checklist
Replace this line with `references/review.md` §2 (the severity rubric and the acceptance-target rules) and §4 (the
verifier checklist, items 1-5), verbatim (`make_brief.py` exits 2 until it has the rubric and the checklist).
