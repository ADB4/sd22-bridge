---
name: sd-material-research
description: Research-driven pipeline for physically plausible procedural materials in Adobe Substance 3D Designer through the substance-designer MCP bridge. It interviews the user, researches how the real material is built and how it wears (layers, dimensions, aging and damage processes, PBR values, with sources), writes a spec of physical invariants and numeric targets, builds the graph with bundled Designer helpers, measures the exported maps with bundled numpy checks, and runs an adversarial reviewer panel. Bundled research covers brick, asphalt, concrete and wood planks; anything else is researched on the spot. Use it whenever the user wants to create, extend, fix or critique a realistic Substance Designer material (brick, pavement, concrete, wood, stone, tile, plaster, roofing, metal or anything else), asks for erosion, weathering, damage, wear or aging that should look physically right, or asks why a material looks fake or CG, even if they never say "research".
---

# Research-based materials in Substance Designer

A material is a set of components laid out at construction, each a stack of physical layers. Every aging process is a
physical event: it acts on one layer of one component, removes or adds material there, reveals what lies *beneath* it
in the same component, and happens where its drivers put it (edges, traffic, water, sun, gravity). Build the graph in
that order, enforce the consequences by structure, check them with numbers, and the result reads as real at any
distance.

The rule that started this came from the user's brick material. Erosion removes brick: it rounds the arrises and spalls
the face, showing more brick underneath. It never reveals more mortar, and the joint keeps its width, because mortar
sits *beside* the brick face, not beneath it. Read `references/method.md` before the spec stage. It turns that rule
into a method that works for any material.

## Stages

| # | Stage | Read | Produces | Gate |
|---|---|---|---|---|
| 0 | Orient | this file | tools folder, environment | — |
| 1 | Interview | `references/interview.md`, the sheet's §8 | answers | user answers |
| 2 | Research | `references/research.md`, `references/materials/<m>.md` | `research/notes.md`, or a new sheet | — |
| 3 | Spec | `references/method.md`, `assets/spec_template.md`, `references/checks.md` | `spec.md`, `checks/<variant>.json` | user approves |
| 4 | Build | `references/sd_craft.md` | graphs, `build/NN_*.py`, `registry.json` | stage checks pass |
| 5 | Measure | `references/checks.md` | scorecards, previews | hard checks pass |
| 6 | Review | `references/review.md` | `review/round<N>/findings.md` | — |
| 7 | Iterate, hand off | `assets/context_prompt_template.md` | fixes, `CONTEXT_PROMPT.md`, memory note | user is satisfied |

Other entry points:
- **Existing material** (critique, extend or fix it): research, then write a spec from the sheet plus the user's
  intent, then export (`sk.export_outputs`) and measure and review their graph, then propose fixes. Ask before editing
  their graph, and never save their package unasked.
- **Continuing a material**: read its `CONTEXT_PROMPT.md`, `spec.md` and the latest scorecards, then pick up at
  stage 7.

### 0. Orient
- Call `designer_status` and `list_packages`.
- Create the tools folder next to the package, `~/Documents/Allegorithmic/Substance Designer/<m>_tools/`, with
  `research/`, `checks/`, `build/`, `dump/` and `review/`. Keep everything there, not in a session scratchpad, so
  the work survives the session. A file that must go to a scratchpad goes in a subfolder named after the material and
  variant (`<scratchpad>/<m>_<variant>/`): parallel sessions and agents can share one scratchpad.
- Run `PY=$(bash <skill>/scripts/setup_env.sh)` (numpy, scipy, Pillow, OpenCV).

### 1. Interview
Ask before starting; the user wants to be asked. Follow `references/interview.md`:
- 4-8 questions in AskUserQuestion rounds.
- Recommended option first.
- Each option states its physical consequence.
- Defaults are stated, not asked.
- Ask what any wear words mean (rounding, chipping, spalling...) and how much damage each variant gets.

### 2. Research
- **With a bundled sheet:** read all of it, close the request's gaps with targeted searches, and re-verify the numbers
  that hard checks depend on.
- **Without one:** run the research team in `references/research.md`. It writes a new sheet for next time.
- The brick build skipped this stage, and its acceptance targets were invented reactively after reviews. Research
  first is the main fix.

### 3. Spec
Fill `assets/spec_template.md` into `<tools>/spec.md`:
- the user's requirements, verbatim
- scale (mm/px, height depth)
- layout
- the layer model with a cross-section
- the process plan
- invariants, each with **Enforce** and **Check**
- variant presets in physical units
- PBR targets
- acceptance targets
- graph architecture

Then generate `checks/<variant>.json` from the acceptance table. Include perceptual checks, such as the visible joint
at half depth, not only mask-level ones. Before the gate, put every hard check through `references/checks.md`, "Hard
checks that can fail": tiling is hard, a direction the physics fixes is hard, and each hard check reads the rendered
maps and names the wrong build it catches. In the dry runs, every spec's weakest hard checks proved only the mask
wiring.

**Gate:** show the user a short summary (scale, layer model, the 3-6 key invariants in plain words, the variant
ladder, what's estimated) and wait for the go-ahead. Skip this only if they said not to stop.

### 4. Build
Follow the skeleton in `references/sd_craft.md` §3, using `scripts/sdkit.py` (quick reference in §2):
- Script each stage as `build/NN_<stage>.py`. Run it with `run_python`; anything over ~45 s goes through
  `python3 <skill>/scripts/sdcall.py build/NN.py` (`py -3` on Windows) from a background shell.
- Make the graph 16-bit at creation. Use only cheap noises (`sk.lib` refuses the FX-map noises that stall the engine).
  Save right after creating the package and after each stage.
- **Render `nowear` from the first height stage on** (`sk.nowear`), and run `mask_invariance` and `envelope` after
  every change. The brick build never had this controlled render.
- After each stage, export at 1024 and run that stage's checks before moving on. Calibrate every Histogram Scan from
  measured quantiles (`scripts/calibrate.py`); never set Position by intuition.
- Keep one Flood Fill random per visual feature. Shared randoms made "hero bricks" that printed a lattice.

### 5. Measure
- Export every variant plus its `nowear` at 2048 (`sk.export_outputs` / `sk.nowear`; batch them through `sdcall.py`).
- Run `$PY <skill>/scripts/matcheck.py checks/<v>.json`, which writes scorecards.
- Run `$PY <skill>/scripts/previews.py checks/*.json --out review/round<N>`, which makes lit views with height
  shadows, a hillshade, tiling sheets, crops at typical and worst sites, and compare sheets.
- Look at the previews yourself with Read, but treat your own verdict as provisional. In the brick build it was
  optimistic three times.
- Fix every **hard** failure before any review.

### 6. Review
Follow `references/review.md`:
1. Preflight: scorecards, previews, the fix ledger.
2. Write `review/BRIEF.md`.
3. Run 4-6 lenses derived from the spec, each with an adversarial verifier.
4. A lead writes the plan and the scorecard.

Use a Workflow (`assets/workflows/review_round.js`) only when the user has opted into workflows (ultracode is on, or
they asked). Otherwise run the same agents with the Agent tool. Reviewers never call Designer. While the panel runs,
prepare the next fixes from the numbers.

### 7. Iterate and hand off
- Apply the plan in dependency order, fill the ledger with measured acceptance, re-measure, and review again with
  fewer lenses. Three rounds is typical. The stopping rule is in `references/review.md` §5.
- **Final gate:** the last change is followed by a full matcheck run on every variant. The report states what was
  verified after the last change, in physical terms ("joint 10.5 mm at half depth; 0 damaged pixels below the mortar;
  damage 4.3 %"). Send the comparison images (SendUserFile).
- Write `<tools>/CONTEXT_PROMPT.md` from the template: requirements, architecture, how to edit, a measured-state
  table, open items, and the invariants to re-check. Also save a project memory note with the requirements as
  acceptance criteria.

## Designer rules that save hours
- **One Designer call at a time.** Parallel agents never call substance-designer tools; they read exported files.
- **A timeout (~60 s) usually means Designer is still computing.** Don't retry. Wait (poll `designer_status`, or
  sample the process), then check. Long jobs go through `sdcall.py`.
- **Watch for FX-map noises at high scale.** They stall the GL engine for minutes (Gaussian above ~200, BnW Spots 3
  near 96, Cells 4 near 110). For fine detail, use Fractal Sum Base levels (`sk.fractal`, `sk.level_for`).
- **Histogram Scan centre = 1 − Position. Blend divide = destination ÷ source.** Both have caused wrong fixes; the
  full cheat sheet is in `sd_craft.md` §5.
- **Only touch the material's own package.** Never edit or save other packages, and save the material's own package
  after each completed stage.

## Bundled files
- `references/method.md`: the physical reasoning (layout, layers, envelope, process cards, invariants, scale).
- `references/interview.md`, `research.md`, `review.md`: how to run those stages.
- `references/checks.md`: the check vocabulary, matcheck and previews usage.
- `references/sd_craft.md`: bridge operation, sdkit, graph skeleton, recipes R1-R14, node cheat sheet, engine costs,
  transfer table.
- `references/materials/`: reference sheets (`_TEMPLATE.md` plus brick, asphalt, concrete, wood_planks, and any added
  later).
- `scripts/`:
  - `sdkit.py`: Designer-side helpers (run_python)
  - `sdcall.py`: long jobs without the 60 s limit
  - `matcheck.py`: checks → scorecard
  - `previews.py`: lit views and sheets
  - `calibrate.py`: Histogram Scan Position from quantiles
  - `setup_env.sh`
- `assets/`:
  - `spec_template.md`, `context_prompt_template.md`
  - `workflows/research_sheet.js`, `workflows/review_round.js`
- `evals/`: spec dry-run test cases (`evals.json`) and how to run them (`README.md`).
