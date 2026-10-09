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

| # | Stage | Read | Produces | Gate | Effort | Target | Expect |
|---|---|---|---|---|---|---|---|
| 0 | Orient | this file | tools folder, environment | — | xhigh | 4 | 4 |
| 1 | Interview | `references/interview.md`, the sheet's §8 | answers | user answers | xhigh | 5 | 4 |
| 2 | Research | `references/research.md`, `references/materials/<m>.md` by section | `research/notes.md`, or a new sheet | — | xhigh | 22 | 24 |
| 3 | Spec | `references/method.md`, `assets/spec_template.md`, `references/checks.md` | `spec.md`, `checks/<variant>.json` | the go question | xhigh | 5 | 5 |
| 4 | Build | `references/sd_craft.md` | graphs, `build/NN_*.py`, `registry.json` | stage checks pass | xhigh | 45 | 55 |
| 5 | Measure | `references/checks.md` | scorecards, previews | suite green | xhigh | 3 | 2 |
| 6 | Review | `references/review.md` | `review/round<N>/findings.md` | auto gate | xhigh | R1 42, R2 42 | R1 47, R2 50 est |
| 7 | Iterate, hand off | `assets/context_prompt_template.md` | fixes, `CONTEXT_PROMPT.md`, memory note | stop point | xhigh | R1 85, R2 70 | R1 115 est, R2 130 est |

Target and Expect are minutes of wall time on the run's path. Expect comes from the concrete (M8) stamps; `est` marks a
value with no M8 stamp behind it. Steps between stages, target / expect: readiness and probes 5 / 8 est (beside stage
3), each auto gate 2 / 2 est, round boundary 3 / 4, each final gate 6 / 6, report 5 / 5 est, each leg hand-off 6 / 6
est, docs at the end 55 / 55 (in the background, off the path). `scripts/pathclock.py` holds the same numbers.

Effort is xhigh for every stage (ML-01 verdict). Read your effort from $CLAUDE_EFFORT (get_session self as fallback),
stamp it in stages.jsonl, and never ask for /effort. Below xhigh, record an incident and continue. Never run the
Agent-tool fallback panel below xhigh: hand off to the other leg once, and if that leg is also below xhigh, stop and
report. The user sets the Code tab's effort picker to xhigh once; the repo's `.claude/settings.local.json` (gitignored)
holds `effortLevel` and `maxEffortLevel` at xhigh.

From the spec gate on, the run is unattended until the report: read "Unattended run" below before stage 3.

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
- Stamp the run in `<tools>/stages.jsonl`: append one JSON line per event, `{stage, event, utc, note}`, with `utc`
  from `date -u +%Y-%m-%dT%H:%M:%SZ`.
  - Stages 0-5 stamp `start` and `end`. Review rounds stamp `panel_launch`, `lead_json` and `gate` (stage 6), then
    `apply_end` and `final_gate` (stage 7). Readiness stamps `readiness_start` and `readiness_end`, the report
    `report_start` and `report_end`, docs at the end `docs_start` and `docs_end`.
  - A leg that hands off stamps `handoff`; the next leg's first stamp is `up`. A pause for anything else is `pause`
    and its end `resume`. A problem you continue past is `incident`.
  - Each session or leg adds `session` (the first 8 characters of $CLAUDE_CODE_SESSION_ID) and `effort` to its first
    stamp.
  - Every user touch is a row: `{stage, event: "touch", kind, utc, asked_utc, answered_utc, recommended_taken, note}`,
    with `kind` one of question, restart, paste, approval, commit or other.
  - `$PY <skill>/scripts/pathclock.py <tools>/stages.jsonl` reports each step against Target and Expect, the waits,
    and every delegated run over 10 min.

### 1. Interview
Ask before starting; the user wants to be asked. Send round 1 after reading this file alone (sub-type and setting,
layout, look, variants, wear words), and Read `references/interview.md` and `references/research.md` and print the
sheet's §0 and §8 (`sed -n '/^## 0\./,/^## 1\./p;/^## 8\./,/^## 9\./p' <sheet>`) in the same message, so they load
while the user answers. Round 2 follows `interview.md`. In both rounds:
- 4-8 questions in AskUserQuestion rounds.
- Recommended option first.
- Each option states its physical consequence.
- Defaults are stated, not asked.
- Ask what any wear words mean (rounding, chipping, spalling...) and how much damage each variant gets.

### 2. Research
- **With a bundled sheet:** read §0-3 and §5-10 in full and, from §4, only the cards of the processes the interview
  chose and any card they name (`grep -n '^##'` the sheet, then Read by line range). Every sheet §5 invariant of the
  layout or a chosen process goes into spec §6 with its Enforce line and a check id that measures it in these
  variants: re-aim a sheet check whose region no preset fills (wood 11 with no fresh damage: measure the crack walls).
  Only one whose process or feature no preset has goes on the left-out list under spec §5, with the reason. Close the
  request's gaps and re-verify the numbers that hard checks depend on, in
  background agents while you draft the spec; the gate waits for them (`references/research.md` A).
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

Then generate `checks/<variant>.json` from the acceptance table, using the schema card at the top of
`references/checks.md`, not matcheck's source. Include perceptual checks, such as the visible joint at half depth, not
only mask-level ones. Before the gate, put every hard check through `references/checks.md`, "Hard checks that can
fail": tiling is hard, a direction the physics fixes is hard, and each hard check reads the rendered maps and names the
wrong build it catches, as a case in `checks/wrong_build_cases.py` (the suite is red without one). Write `SUITE.json`
too (`references/checks.md`, "Suite"). In the dry runs, every spec's weakest hard checks proved only the mask wiring.

**Gate:** the go question ("Unattended run"): a short summary (scale, layer model, the 3-6 key invariants in plain
words, the variant ladder, what's estimated), the standing decisions SD-1 to SD-6 and the deadline, then one
AskUserQuestion. It is the last question before the report.

### 4. Build
Follow the skeleton in `references/sd_craft.md` §3, using `scripts/sdkit.py` (quick reference in §2; grep `sdkit.py`
only for what §2 lacks):
- Script each stage as `build/NN_<stage>.py`. Run it with `run_python` (under 45 s); a longer job goes through
  `python3 <skill>/scripts/sdcall.py build/NN.py` (`py -3` on Windows): in the foreground (Bash timeout 600000 ms)
  when it should take under ~8 min, otherwise from a background shell. A rebuild runs the changed stage and every
  later one, plus the 1K exports, as one job: it takes seconds.
- Make the graph 16-bit at creation. Use only cheap noises (`sk.lib` refuses the FX-map noises that stall the engine).
  Save right after creating the package and after each stage.
- **Render `nowear` from the first height stage on** (`sk.nowear`), and run `mask_invariance` and `envelope` after
  every change. The brick build never had this controlled render.
- After each stage, export at 1024 and run that stage's checks before moving on. Calibrate every Histogram Scan from
  measured quantiles (`scripts/calibrate.py`); never set Position by intuition.
- Keep one Flood Fill random per visual feature. Shared randoms made "hero bricks" that printed a lattice.

### 5. Measure
- Export every variant plus its `nowear` at 2048 (`sk.export_outputs` / `sk.nowear`) in one foreground `sdcall.py`
  job. 28 renders take under 2 min.
- Then run the suite from one background shell: `$PY <skill>/scripts/suite.py SUITE.json --out review/round<N>`. It
  writes the scorecards, the wrong builds and the previews: lit views with height shadows, a hillshade, tiling sheets,
  crops at typical and worst sites, and compare sheets. Write the round's review files meanwhile
  (`references/review.md` §1).
- When it lands, read `review/round<N>/suite.json`, never the text: green means `green` true, `rc` 0 and `full` true.
  Otherwise fix each job in `red`: a hard check failed or measured nothing, a wrong build misbehaved, or a hard check
  has no case (`references/checks.md`, "Suite").
- Look at the previews yourself with Read, but treat your own verdict as provisional. In the brick build it was
  optimistic three times.
- Fix every **red** job before any review.

### 6. Review
Follow `references/review.md`:
1. Preflight: the 2K export, then the suite in the background; meanwhile the fix ledger, `review/REFERENCE.md`
   (round 1: `assets/reference_template.md`) and the lens table.
2. On a green suite only: from round 2, `scripts/fixcheck.py` (did each ledger fix land?); then
   `scripts/make_brief.py`, which writes the delta brief and the panel's args.
3. Run 4-6 lenses derived from the spec; a verifier re-measures each lens's findings, highs first, and one re-verify
   agent takes any high or medium a verifier left without a verdict.
4. A lead writes the plan and the scorecard.

Run the panel as a Workflow (`assets/workflows/review_round.js`); use the Agent tool only when Workflow is unavailable.
Reviewers never call Designer. While the panel runs, write fix drafts to `review/drafts/round<N>/` from the lens and
verdict files as they land, never in chat; drafts stay drafts until the plan gate. No split at lens launch: the
session that launched the panel drafts, settles the plan at the auto gate and applies ("Unattended run"). The split in
`references/review.md` §6 is for an attended run, and only when the user asks for it.

### 7. Iterate and hand off
- At the auto gate, settle every design call in the plan (a choice between looks, a requirement trade, a deviation)
  by SD-1 and SD-2 and log it ("Unattended run"); a call or a draft's open question that comes up during the apply is
  settled the same way, at once. In an attended run (an existing material, or on request) the plan gate asks the
  calls in one AskUserQuestion batch instead, the settled option first.
- Apply one build-measure batch per graph: edit the graph's plan items into their stage scripts in dependency order
  (per item, `decisions.py snap` its scripts before the edit and `decisions.py patch` after: the per-fix revert patch,
  `references/review.md` §1), run one rebuild from the earliest changed stage, re-calibrate once each Histogram Scan downstream of an edit
  (upstream scan first; keep the new Position in its script), then export at 2048, with its `nowear`, every preset
  that an edited node or preset parameter feeds (an edit to a shared node touches every preset). While the next graph
  builds, run the targeted set in the background: `suite.py` with `--configs` the touched configs and cross-case groups,
  `--kinds matcheck,wrong_builds` and `--beside-designer`, into `review/round<N+1>` after you read the last set's
  `suite_partial.json` (each set replaces it). Items that miss their acceptance go into a second batch for that graph.
- Give each plan item its own ledger row with measured before and after values, never one row per batch. Stamp the
  apply: `date -u` when the plan gate is settled and after the last batch's targeted checks, into the ledger's
  `apply` (`references/review.md` §1). Then review again with fewer lenses. Three rounds is typical. The stopping
  rule is in `references/review.md` §5.
- **Final gate:** after the last change, export every variant plus its `nowear` at 2048 in one foreground `sdcall.py`
  job (stage 5), then run the full suite into `review/round<N+1>` in the background, then `fixcheck.py` on its ledger
  (`references/review.md` §5); draft the report meanwhile and finalize it only on a green `suite.json`. The report
  states what was verified after the last change, in physical terms ("joint 10.5 mm at half depth; 0 damaged pixels
  below the mortar; damage 4.3 %"). Send the comparison images (SendUserFile).
- Write `<tools>/CONTEXT_PROMPT.md` from the template: requirements, architecture, how to edit, a measured-state
  table, open items, and the invariants to re-check. Also save a project memory note with the requirements as
  acceptance criteria.

## Unattended run

From the spec gate to the report the user is away. The run settles every call itself by the standing decisions,
logs each one so it can be reversed the next day, and stops green with an honest report.

**The go question.** The spec gate is one AskUserQuestion: "Approve the spec and run unattended to a finished material
(Recommended)" or "Change something first". Its text holds the spec summary (stage 3), the standing decisions and the
deadline (default: the next 08:00 local). On the go answer write `<tools>/RUN.json`: `{mode: "unattended", go_utc,
deadline_local, standing_decisions, continuation, owner, heartbeat, incidents: []}`. `owner` is the session id
($CLAUDE_CODE_SESSION_ID) that may call Designer, `heartbeat` the UTC the owner refreshes at every stamp, and
`continuation` how a later session picks the run up (`none` until one is set).

Standing decisions (spec.md §1 lists them too):
- **SD-1** Design calls take the recommended option.
- **SD-2** Look trades follow the no-pattern rule below.
- **SD-3** Two full review rounds, then apply and stop.
- **SD-4** After round 1, only highs are fixed.
- **SD-5** REFERENCE and the spec are updated once, at the end.
- **SD-6** No commit or push during the run.

**After the go answer**, until the stop point:
- No AskUserQuestion, no stop question, no split at lens launch.
- The plan gate is an auto gate: when `lead.json` lands, take each design call's option by SD-1 and SD-2 (`settled`,
  `references/review.md` §5) and go on. A draft's open question, or a call that comes up mid-apply, is settled the
  same way at once, never left for a gate. Technical choices (check method, sequencing, file layout) take the default.
- Every settled call or choice gets a row in `review/decisions.json` (`references/review.md` §1).

**SD-2, the no-pattern rule.** Per option, `adds_pattern` is yes, no or unknown:
- yes or no by measurement: its draft, its model or a 1K probe puts one of these tile-period stats (row or column-mean
  harmonics at k = 1..3, the column-mean envelope CV, lowfreq std) above the current build by more than max(5 % of
  the current value, the check's tolerance), or not. These stats decide, no others.
- An option whose text names a new repeat, lane, band, lattice or tiling landmark at any setting is measured before
  the call is settled; only when it cannot be measured does the wording decide (yes).
- An option that leaves the build as it is: no. Anything else unmeasured: unknown.
A call with a yes among its options is a look trade, and SD-2 overrides SD-1 there: unknown counts as yes, and the run
takes the first option, in the lead's order, that is no. If none is no, it takes the smallest measured increase and
flags it in the report. A call with no yes follows SD-1. Seeds and calibrations chosen against a look-related target are
look trades too: only a check that passed its null test on an unworn or no-op build may steer them.

**What the run never does on its own:** change a value the user gave verbatim (requirements, interview answers)
outside a lead design call, or retarget, relax or demote a check to turn it green. Such a change is reverted and logged
`not_made_needs_user`, and the run goes on. A lead design call that changes a spec value, a requirement reading or a
check target is taken under SD-1, logged `requirement_trade` and listed first in the report. A wrong-build case may be
corrected to match its own documented description, only when the corrected case still passes the real build and fails
its named wrong build; log the correction.

**Deadline.** Never start a step that cannot end green by the deadline minus 1 h, estimated from the stage table's
Expect and this run's stamps (`pathclock.py`). Stop green and report instead.

**Mid-run look.** When stage 5's suite is green, send the tiled and compare sheets (SendUserFile, status proactive)
with one line: "Look if you like; reply to steer, otherwise I continue." Never wait for a reply. Any session that gets
a user message during the run, owner or not, appends it verbatim to `<tools>/review/steer.jsonl` (`{utc, session,
text}`) and answers in one line where it will be used. The owner reads that file at each auto gate and before each
apply:
- a message from before the round 1 auto gate is input at that gate: it overrides SD-1 and SD-2 for the calls it
  addresses and may add or drop a plan item;
- a later one goes into the next apply's plan, or, when no apply is left, into the report as a requested change.
Each gets a decisions.json row (`user_steer`).

**Stop point.** Round 2's final gate is green, or the last green state is restored. Then the report, docs once in the
background, one notification, and RUN.json `mode: "done"`.

## Designer rules that save hours
- **One Designer caller at a time.** Subagents never call substance-designer tools; they read exported files. After a
  split (stage 6) only the new session calls Designer, and it never acts on a `findings.md` older than `lead.json`.
  Who calls Designer and who owns the CPU:

| Phase | Calls Designer | Owns the CPU |
|---|---|---|
| 4 build, 7 apply | main, one call at a time | Designer, plus the previous graph's checks on about half the cores (4 on an 8-CPU Mac) |
| 5 measure, final gate | main for the exports, then nobody | the suite (matcheck, wrong builds, previews) |
| 6 panel, until the plan gate | nobody | the panel's agents; no suite or numpy jobs beside them |

- **A timeout (~60 s) usually means Designer is still computing.** Don't retry. Wait (poll `designer_status`, or
  sample the process), then check. Long jobs go through `sdcall.py`. A Mac job several times slower than
  `sd_craft.md` §6: check App Nap (§1 there).
- **Watch for FX-map noises at high scale.** They stall the GL engine for minutes (Gaussian above ~200, BnW Spots 3
  near 96, Cells 4 near 110). For fine detail, use Fractal Sum Base levels (`sk.fractal`, `sk.level_for`).
- **Histogram Scan centre = 1 − Position. Blend divide = destination ÷ source.** Both have caused wrong fixes; the
  full cheat sheet is in `sd_craft.md` §5.
- **Only touch the material's own package.** Never edit or save other packages, and save the material's own package
  after each completed stage.

## Bundled files
- `references/method.md`: the physical reasoning (layout, layers, envelope, process cards, invariants, scale).
- `references/interview.md`, `research.md`, `review.md`: how to run those stages.
- `references/checks.md`: the schema card, the check vocabulary, and the measuring scripts' usage.
- `references/sd_craft.md`: bridge operation, sdkit, graph skeleton, recipes R1-R14, node cheat sheet, engine costs,
  transfer table.
- `references/materials/`: reference sheets (`_TEMPLATE.md` plus brick, asphalt, concrete, wood_planks, and any added
  later).
- `scripts/`:
  - `sdkit.py`: Designer-side helpers (run_python)
  - `sdcall.py`: long jobs without the 60 s limit
  - `matcheck.py`: checks → scorecard
  - `wrong_builds.py`: each hard check against its named wrong build
  - `previews.py`: lit views and sheets
  - `suite.py`: the three above in parallel, gated (stdlib)
  - `fixcheck.py`: re-measures the fix ledger (stdlib)
  - `calibrate.py`: Histogram Scan Position from quantiles
  - `make_brief.py`: a review round's delta brief and panel args (stdlib)
  - `pathclock.py`: stages.jsonl against Target and Expect, waits, long delegated runs (stdlib)
  - `decisions.py`: the run's decision log and per-fix revert patches (stdlib)
  - `setup_env.sh`
- `assets/`:
  - `spec_template.md`, `context_prompt_template.md`, `reference_template.md` (review REFERENCE.md)
  - `workflows/research_sheet.js`, `workflows/review_round.js`
- `evals/`: spec dry-run test cases (`evals.json`) and how to run them (`README.md`).
