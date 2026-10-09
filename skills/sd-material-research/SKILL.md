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
  stage 7. A leg of an unattended run reads RUN.json and the run block first ("Unattended run", Legs).

### 0. Orient
- Call `designer_status` and `list_packages`.
- Create the tools folder next to the package, `~/Documents/Allegorithmic/Substance Designer/<m>_tools/`, with
  `research/`, `checks/`, `build/`, `dump/` and `review/`. Keep everything there, not in a session scratchpad, so
  the work survives the session. A file that must go to a scratchpad goes in a subfolder named after the material and
  variant (`<scratchpad>/<m>_<variant>/`): parallel sessions and agents can share one scratchpad.
- Run `PY=$(bash <skill>/scripts/setup_env.sh)` (numpy, scipy, Pillow, OpenCV).
- Preflight part 1, so the night never needs a restart: time the `designer_status` call above (over 15 s counts as
  timeout), then `$PY <skill>/scripts/preflight_night.py part1 --tools <tools> --wake --designer-status
  <ok|timeout|error>` (`review/preflight.json`). Exit 1, Designer started before the newest plugin file: ask once for a
  restart (a touch row, kind restart), after every plugin change this session lands. Exit 2, not running or not
  answering: `open -a` the app named in preflight.json, `sample <pid> 3` for a modal dialog on the main thread, and
  tell the user now, while they are here. An existing material's package must show a file path in `list_packages`.
- Stamp the run in `<tools>/stages.jsonl`, one JSON line per event, `{stage, event, utc, note}`:
  `$PY <skill>/scripts/runstate.py stamp --tools <tools> --stage <S> --event <e> [--note ...] [--extra '<json>']`.
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
- The message that launches the research ends with the next-needed line ("Unattended run", Messages): the user can
  leave until the post-research questions.

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
too (`references/checks.md`, "Suite"), then `$PY <skill>/scripts/guards.py configs --checks-dir <tools>/checks`: the
standard guard checks (soft, never demoted) that the apply's regression gate reads. In the dry runs, every spec's
weakest hard checks proved only the mask wiring.

**Readiness**, beside the spec writing once research has landed (stamps `readiness_start` and `readiness_end`), so
that every approval card and power problem shows while the user can still settle it:
- `$PY <skill>/scripts/preflight_night.py part2 --tools <tools> --keep-awake-setting <true|false|unknown>`: AC power,
  lid, free disk, and the app's `keep_awake_while_working` from get_settings (read it, never set it).
- `preflight_night.py caffeinate start --tools <tools> --until <deadline as local ISO, e.g. 2026-10-10T08:00:00>`: one
  detached caffeinate to the deadline plus 3 h, its pid in RUN.json.
- `$PY <skill>/scripts/designer_relaunch.py check --tools <tools>`: `relaunch_safe` false means the last Designer launch
  waited for a click on a Steam dialog, so a relaunch at night would stop there; its `advice` goes into the go question.
- First material only: create the routines leg-a, leg-b and run-watchdog (`assets/routines.md`); a later material
  only rewrites the pointer file. Then run the probe chain (`assets/routines.md`, Probe); it sets RUN.json
  `continuation`.
- From here on RUN.json changes only through `runstate.py set` and `incident`, so the go answer keeps what readiness
  wrote. This session may call request_keep_awake (it holds only this session); legs never do.

**Gate:** the go question ("Unattended run"): a short summary (scale, layer model, the 3-6 key invariants in plain
words, the variant ladder, what's estimated), the standing decisions SD-1 to SD-6 and the deadline, then one
AskUserQuestion. Ask it once `review/preflight.json` and both probe files are written, or a probe leg is held by an
approval card. Its text also gives the readiness result: the continuation route, any part-2 problem, the relaunch advice, and any card that
would appear at night, which the user settles there (approve it for the routine, or choose auto mode for the project;
the skill never changes that setting). It is the last question before the report; the reply to the go answer ends
with the nothing-needed line ("Unattended run", Messages).

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
  job. 28 renders take under 2 min. An export run in the background writes `<job>.done` with its rc
  (`sdcall.py job.py; echo $? > job.done`); never grep piped output for a sentinel.
- Then run the suite from one background shell: `$PY <skill>/scripts/suite.py SUITE.json --out review/round<N>`. It
  writes the scorecards, the wrong builds and the previews: lit views with height shadows, a hillshade, tiling sheets,
  crops at typical and worst sites, and compare sheets. Write the round's review files meanwhile
  (`references/review.md` §1).
- When it lands, read `review/round<N>/suite.json`, never the text: green means `green` true, `rc` 0 and `full` true.
  Otherwise fix each job in `red`: a hard check failed or measured nothing, a wrong build misbehaved, or a hard check
  has no case (`references/checks.md`, "Suite").
- Look at the previews yourself with Read, but treat your own verdict as provisional. In the brick build it was
  optimistic three times.
- Fix every **red** job before any review. Unattended, follow "When something breaks unattended" (Designer rules):
  the run never ends red.

### 6. Review
Follow `references/review.md`:
1. Preflight: the 2K export, then the suite in the background; meanwhile the fix ledger, `review/REFERENCE.md`
   (round 1: `assets/reference_template.md`) and the lens table.
2. On a green suite only: from round 2, `scripts/fixcheck.py` (did each ledger fix land?); then
   `scripts/make_brief.py`, which writes the delta brief and the panel's args.
3. Run the round's lenses (`references/review.md` §3: round 1 the families derived from the spec plus a check audit,
   round 2 the same plus fixcheck and regressions); a verifier re-measures each lens's findings, highs first, and one
   re-verify agent takes any high or medium a verifier left without a verdict.
4. A lead writes the plan and the scorecard.

Run the panel as a Workflow (`assets/workflows/review_round.js`); use the Agent tool only when Workflow is unavailable.
Run `realpath` on the skill folder in Bash first and pass the literal result in `scriptPath`: the symlink path is
refused. A copy of the script in the tools folder is the fallback.
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
  (per item, `decisions.py snap` its scripts and `guards.py rows --item <id> --scorecards <the last scorecards>` before
  the edit, `decisions.py patch` after: the per-fix revert patch and the item's guard rows, `references/review.md` §1),
  run one rebuild from the earliest changed stage, re-calibrate once each Histogram Scan downstream of an edit
  (upstream scan first; keep the new Position in its script), then export at 2048, with its `nowear`, every preset
  that an edited node or preset parameter feeds (an edit to a shared node touches every preset). While the next graph
  builds, run the targeted set in the background: `suite.py` with `--configs` the touched configs and cross-case groups,
  `--kinds matcheck,wrong_builds,previews` and `--beside-designer`, into `review/round<N+1>` after you read the last
  set's `suite_partial.json` (each set replaces it). Items that miss their acceptance go into a second batch for that
  graph.
- **Regression gate**, after each targeted set, since no panel reviews the last apply: fill the batch's ledger rows and
  run `fixcheck.py`; exit 1 on a `regressed` or `guard_broken` row stops that item. Meanwhile a background eye agent
  (10-min box) reads the tiled 3x3 albedo sheet of every touched preset, plus the lit and compare sheets where a guard
  row moved, against each item's `tell`, and writes `review/round<N+1>/eye.json` `{item, tell_seen,
  finding_still_visible, files}`; read only the sheets it flags. A flag or a seen tell acts at once: one repair (20 min
  or less), then the item's per-fix revert (`decisions.py`), rebuilt behind the targeted set, and the item becomes the
  residual "reverted: created <tell>". An eye agent's "looks fine" stays provisional. A 1K per-item probe is only for
  attributing a tell seen in a batch.
- Give each plan item its own ledger row with measured before and after values, never one row per batch. Stamp the
  apply: `date -u` when the plan gate is settled and after the last batch's targeted checks, into the ledger's
  `apply` (`references/review.md` §1). Two full rounds; round 2 applies highs only (SD-3, SD-4; the stop rule is in
  `references/review.md` §5).
- **Final gate:** after the last change, export every variant plus its `nowear` at 2048 in one foreground `sdcall.py`
  job (stage 5), then run the full suite into `review/round<N+1>` in the background, then `fixcheck.py` on its ledger
  (`references/review.md` §5); draft the report meanwhile (an unattended run writes it with `morning_report.py`, Stop
  point) and finalize it only on a green `suite.json`. The report states what was verified after the last change, in
  physical terms ("joint 10.5 mm at half depth; 0 damaged pixels below the mortar; damage 4.3 %"). Send the comparison
  images (SendUserFile).
- Write `<tools>/CONTEXT_PROMPT.md` from the template: requirements, architecture, how to edit, a measured-state
  table, open items, and the invariants to re-check. Also save a project memory note with the requirements as
  acceptance criteria.

## Unattended run

From the spec gate to the report the user is away. The run settles every call itself by the standing decisions,
logs each one so it can be reversed the next day, and stops green with an honest report.

**The go question.** The spec gate is one AskUserQuestion: "Approve the spec and run unattended to a finished material
(Recommended)" or "Change something first". Its text holds the spec summary (stage 3), the standing decisions and the
deadline (default: the next 08:00 local). On the go answer set `<tools>/RUN.json` with `runstate.py set` (readiness
wrote it first): `mode` "unattended", `go_utc`, `deadline_local` (local ISO), `standing_decisions`, `owner`,
`next_leg`, `estimate`; `continuation`, `caffeinate_pid` and `incidents` stay as readiness left them. `owner` is the
session id ($CLAUDE_CODE_SESSION_ID) that may call Designer, `next_leg` the routine that takes over next, and
`continuation` the route a later leg comes up by (`none` until the probe sets it); the owner's heartbeat is
`review/heartbeat` (Legs).

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

**Legs.** The run continues across sessions (legs) started by the routines in `assets/routines.md`. The leg RUN.json
names as `owner` is the only Designer caller. While you own the run:
- Stamp with `$PY <skill>/scripts/runstate.py stamp --tools <tools> --stage <S> --event <e>` (it adds your session and
  effort to your first stamp and refreshes `review/heartbeat`), keep `runstate.py heartbeat --loop 900` running in a
  background shell, and change RUN.json only through `runstate.py set` and `incident`. At every stage end, rewrite the
  run block at the top of `CONTEXT_PROMPT.md` (`assets/context_prompt_template.md`).
- At every stamp run `context_size.py`. At 400k hand off at the next clean point: a green targeted set, a final gate,
  `lead.json` with its runner result saved, or a stage end. At 500k hand off at the next point where every job you
  launched has written complete files. A Workflow you launched may keep running, its files are the interface; stop
  background agents, shells and Monitors (TaskStop) or let them finish.
- Hand-off: stamp `handoff`, write the run block, `runstate.py set owner=pending`, note T (`date -u +%FT%TZ`), check
  list_task_runs and call `run_scheduled_task` on RUN.json `next_leg` (it has no run in progress). `runstate.py
  wait-up --tools <tools> --since T` (3 min; on a timeout, one retry and an incident) prints the new leg's `up` row:
  set `owner` to its session and `next_leg` to the other leg routine. Then make no Designer call and write no file.
- A new leg stamps `up`, waits until `runstate.py owner-check` passes (3 min), runs `preflight_night.py caffeinate
  check --tools <tools>` (it restarts a dead caffeinate and logs an incident), and goes on from the run block's next
  step. Legs never call request_keep_awake. Every edit the run block prescribes is rebuilt behind the targeted suite plus wrong builds and
  its guard rows before anything else: a hand-off once carried a defect that zeroed the groove fill with every hard
  check green.
- A session woken while it is not the owner (`owner-check` exit 3) only logs a user message to `review/steer.jsonl`
  and ends its turn.
- A leg that dies: the run-watchdog routine (`assets/routines.md`) runs every 30 min. When the heartbeat is over 45 min
  old and no leg run shows `running`, it starts `next_leg` and hands it the run as above; a leg that still shows
  `running` gets only the "blocked" notification. It never calls Designer and acts at most twice a run, so keep the
  heartbeat loop running whenever you own the run.
- RUN.json `continuation` is the route the sitting-1 probe chose. `routine` is the above. `compaction` (route B): one
  session with `autoCompactWindow` about 440000 in the repo's `.claude/settings.local.json`, the run block current at
  every stage end and re-read after a compaction. `fireAt` (route C): the next leg from `create_scheduled_task` with
  fireAt now + 2 min, only when the probe showed no approval card for it. If routes A and B both fail the probe, say at
  the go question that the run will likely stop after round 1's apply, with a report. Hand-offs assume this machine.

**Mid-run look.** When stage 5's suite is green, send the tiled and compare sheets (SendUserFile, status proactive)
with one line: "Look if you like; reply to steer, otherwise I continue." Never wait for a reply. Any session that gets
a user message during the run, owner or not, appends it verbatim to `<tools>/review/steer.jsonl` (`{utc, session,
text}`) and answers in one line where it will be used. The owner reads that file at each auto gate and before each
apply:
- a message from before the round 1 auto gate is input at that gate: it overrides SD-1 and SD-2 for the calls it
  addresses and may add or drop a plan item;
- a later one goes into the next apply's plan, or, when no apply is left, into the report as a requested change.
Each gets a decisions.json row (`user_steer`).

**Messages.** Every message that hands control back while work goes on ends with exactly one of two lines:
- "Next needed from you: <what> at about <HH:MM local> (in <n> min). You can step away; this Mac shows a banner when I
  ask."
- After the go answer: "Nothing needed from you until the report, est ready <HH:MM>-<HH:MM> local. Keep the app open,
  the Mac on power with the lid open, and Designer running. Notifications reach <where>."
The time comes from `date +%H:%M`; the range sums the stage table's Target, then its Expect, over the steps left.
`<where>` is "this Mac's desktop only", or "this Mac and your phone" when get_settings shows
`connect_new_sessions_to_remote_control` on. While the user is present, repeat the line when the estimate moves by more
than 30 min. Unattended, when a leg runs more than 50 % past Expect, write the new range into RUN.json `estimate` so
the report shows the miss.

**Notifications** (PushNotification), at most two a run:
- "blocked: <step only you can do> since HH:MM", only after self-recovery has failed for 30 min;
- "<material> ready: N highs open, M calls to check, see REPORT.md".
The mid-run look's SendUserFile is neither, and nothing waits on it.

**Stop point.** Round 2's final gate is green, or the last green state is restored. Then, in this order:
1. Stamp `report_start`. With `runstate.py set`, record `proposed_commits` (a JSON list of `{repo, files, message}`,
   one per commit the run would make; none is made, SD-6) and, when the run stopped early, `stop_reason`.
2. Launch the final eye pass in the background (one agent, box 15 min, beside the docs): it reads the final gate's
   `*_tiled3x3_albedo.png` of every preset and writes `review/eye_final.json` (`[{preset, sees, files}]`).
3. Run `$PY <skill>/scripts/morning_report.py --tools <tools>`. It writes `<tools>/REPORT.md`: the verdict (8 lines or
   fewer), the images to look at first, every decisions.json row with its "reverse <id>", what needs the user, the
   open defects by severity under the pre-apply severity caveat, the eye pass, incidents, the proposed commits and the
   path clock, in 500 prose words or fewer, then a numbered answer batch. Exit 1 means the prose is still over the
   cap: say so in the final message. When `eye_final.json` lands, run it again (it replaces the file whole).
4. Send the report's "Look first" images (SendUserFile), then the "ready" notification. `runstate.py set mode=done`,
   stamp `report_end`, run the docs once in the background, and when they end, `preflight_night.py caffeinate stop
   --tools <tools>`.
The last leg's final message is the verdict and the answer batch as the script prints them, so a typed reply works
("1 none, 2 yes", "reverse D2-3"). It asks nothing else.

## Designer rules that save hours
- **One Designer caller at a time.** Subagents never call substance-designer tools; they read exported files. In an
  unattended run only the leg RUN.json names as `owner` calls Designer (Legs). After a split (attended runs) only the
  new session calls Designer, and it never acts on a `findings.md` older than `lead.json`.
  Who calls Designer and who owns the CPU:

| Phase | Calls Designer | Owns the CPU |
|---|---|---|
| 4 build, 7 apply | main, one call at a time | Designer, plus the previous graph's checks on about half the cores (4 on an 8-CPU Mac) |
| 5 measure, final gate | main for the exports, then nobody | the suite (matcheck, wrong builds, previews) |
| 6 panel, until the plan gate | nobody | the panel's agents; no suite or numpy jobs beside them |

- **A timeout (~60 s) usually means Designer is still computing.** Don't retry. Wait (poll `designer_status`, or
  sample the process), then check. Watches use one background Bash until-loop per landing event, relaunched after each
  landing; a Monitor expires at 30 min whatever its script does. Long jobs go through `sdcall.py`. A Mac job several
  times slower than `sd_craft.md` §6: check App Nap (§1 there).
- **Watch for FX-map noises at high scale.** They stall the GL engine for minutes (Gaussian above ~200, BnW Spots 3
  near 96, Cells 4 near 110). For fine detail, use Fractal Sum Base levels (`sk.fractal`, `sk.level_for`).
- **Histogram Scan centre = 1 − Position. Blend divide = destination ÷ source.** Both have caused wrong fixes; the
  full cheat sheet is in `sd_craft.md` §5.
- **Only touch the material's own package.** Never edit or save other packages, and save the material's own package
  after each completed stage.
- **When something breaks unattended**, act at once and never wait for the user. Each incident is one `runstate.py
  incident` line (the report lists them). Never click a dialog (no computer use). The run stops green or reverted,
  never red.

| What broke | What the run does | If that fails |
|---|---|---|
| A red suite or targeted set | At most 2 fix attempts or 45 min per red job. Attribute first: per applied item, latest first, copy the stage scripts aside, `decisions.py revert` the item, rebuild from its earliest stage at 1K, rerun the red job, restore the copy. Then revert the smallest set that restores green, with its dependents (`revert-plan`), rebuild, re-export and confirm that the last green scorecard reproduces (0 changed rows). Mark the reverted items not_done, their ledger note starting "reverted:" with the diagnosis, and go on with the independent items. | Revert the whole batch to the last green state and go on with the next graph or step |
| A wrong build misbehaves, and also misbehaves on the pre-apply build | A case defect: correct the case to its own documented description ("Unattended run"), never revert the fix | - |
| A fix whose only cure changes a user-given value or relaxes a check | Revert it, log `not_made_needs_user`, go on | - |
| Designer does not answer | 1. A timeout is Designer computing, for up to 3x the job's expected time. 2. `ps -o pri=` 4 is App Nap: `open -a` it. 3. `designer_relaunch.py check` samples it for a modal. 4. On a modal or a dead process, one `designer_relaunch.py relaunch --tools <tools> --package <package> --job <last stage job> --golden <last good export folder> --out <its new export folder>`: it kills, relaunches, waits up to 30 min for the bridge, reopens the package from its last save, reruns the job and diffs the export. It stops early on a Steam launch dialog or a Designer modal (`blocked_*`). | A second failure, any `blocked_*`, or exit 4: stop on the last green state (the stage scripts reverted to it by patch, the rebuild listed as pending in the report) and send "blocked" |
| A lens dies or stalls | Rerun it once in the background from the script's prompts (`references/review.md` §6, `dead`) | Its area is unreviewed: the plan and the report say so |
| A drafts, docs, edits or ledger workflow dies | The owner does that work itself | - |
| A leg dies | The run-watchdog (Legs) | "blocked" from the watchdog |

- **User rules.** No commit or push during a run (SD-6). Commits are asked once, in the morning answer batch, one
  option per commit; nothing is ever pushed, and no push is offered. A next-day reversal ("reverse D2-3") runs
  unattended: `decisions.py revert-plan --id`, then per graph one batch (revert the row's items, latest first, and
  build its `revert.alternative`, drafting it first when it says "draft at reversal"), the final gate, a `user_steer`
  row, and `morning_report.py --addendum --kind reversal` with the suite and guard results. No new panel unless asked.

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
  - `fixcheck.py`: re-measures the fix ledger, flags regressed rows and broken guards (stdlib)
  - `guards.py`: the standard guard checks and an item's guard rows (stdlib)
  - `calibrate.py`: Histogram Scan Position from quantiles
  - `make_brief.py`: a review round's delta brief and panel args (stdlib)
  - `findings.py`: a review round's findings.md from the lens, verdict and lead files, in seconds (stdlib)
  - `pathclock.py`: stages.jsonl against Target and Expect, waits, long delegated runs (stdlib)
  - `decisions.py`: the run's decision log and per-fix revert patches (stdlib)
  - `runstate.py`: RUN.json under a lock, stamps, the heartbeat, the owner check (stdlib)
  - `context_size.py`: this session's context size against the leg budget (stdlib)
  - `preflight_night.py`: Designer freshness, power and the night's caffeinate (stdlib)
  - `morning_report.py`: the run's REPORT.md and answer batch; `--addendum` after a reversal or a user edit (stdlib)
  - `designer_relaunch.py`: Designer's state, Steam's launch dialogs, and the run's one relaunch (stdlib)
  - `setup_env.sh`
- `assets/`:
  - `spec_template.md`, `context_prompt_template.md` (with the run block), `reference_template.md` (review
    REFERENCE.md), `routines.md` (the leg routines)
  - `workflows/research_sheet.js`, `workflows/review_round.js`
- `evals/`: spec dry-run test cases (`evals.json`) and how to run them (`README.md`).
