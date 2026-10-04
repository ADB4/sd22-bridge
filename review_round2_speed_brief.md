# Round 2 speed brief: closing session 3 and running session 4 faster

2026-10-04. The measurements come from transcripts, file times and timing runs on copies in the scratchpad (five
analysts; logs and prototypes in `<scratchpad>/asphalt_decal/speed_brief/`, cited by file below), checked by two
adversarial reviewers. The reviewer process itself (brief, lenses, verifiers, lead, round-3 runbook) is in session 3's
`review/round2/process_brief.md` and is not repeated here. This brief covers the rest of round 2: closing session 3's
paused gate, and session 4 (8 fixes on lane, detail and decal).

**Status (2026-10-04 03:10).**
- Done:
  - The prototypes are in `ops/`, with a README on the status of each.
  - The gate wrap-up tools are tested and ready for session 3's gate: `extract_findings.py`, `apply_pack.py` (batches
    and undecided calls) and `ledger_skeleton.py`.
  - The `run_all.sh` rigor gap (item C) is fixed. Each output is deleted before the step that writes, every exit code
    counts, and the new `checks/scorecard_gate.py` reads each scorecard's JSON. It was validated by an injected-failure
    run (4 of 4 failures named, exit 1, 17 s) and a real full run (26/26 configs ok, wrong builds 581/0, INV-16 ok, PASS,
    12.9 min).
- Left on purpose:
  - Writing `findings.md`, the DECISIONS and the apply pack's decided options belongs to session 3's paused gate (it
    still asks "save findings.md?").
  - Prompt 4's read list belongs to `implementation_spec.md` M7.
  - The parallel runner (item C) is not built.

**Summary.** Designer is not the bottleneck: a full 2K re-measure is 52 renders in about 2.4 min, and a stage rebuild
takes 4-20 s. Session time goes to:
- serial CPU checks (the suite);
- foreground waits;
- one build-measure cycle per fix;
- slow pickup of background jobs;
- context growth.

The one large, measured win is the suite: 13 min serial → 2.6 min with 8 workers and an exact faster shadow routine.
The other savings are estimates and overlap, so don't add them up.

## Where the time goes

| item | measured | source |
|---|---|---|
| Suite as 65 independent jobs | 786 s at 1 worker → 208 s at 12 workers → **158 s** at 8 workers with row-blocked shadows (152 s at 12) | `logs/par_p1`, `par_p12`, `par_p8f`, `par_p12f` (prototype `run_all_par.sh`, uncapped threads) |
| Real `run_all.sh` | 13.5-14.2 min, all serial | session-2 runs (file times) |
| Parallel output identity | all 1,050 PNGs byte-identical between the 1-worker and 8-worker fast runs; row-blocked shadows 626/626 pixel-identical to the original | `out/p1` vs `out/p8f`; `out/*_orig` vs `*_fast` |
| matcheck, 26 configs | 3.1-3.4 min serial (4.5 min in the loaded session-2 gate run) → 46-63 s parallel | `trun_mc26*`, `par_p8f`, Designer analyst |
| Wrong builds | 581 cases ≈ 4.7 min serial; lane 88-180 s serial (load-dependent) → 28 s as 6 per-config processes | `par_p1`; apply analyst's mirror |
| composite_decal, 4 sites | 90-136 s serial → 42.5 s as 4 per-site processes (361/361 values identical); keep it one job inside the parallel suite | `par_p1`, `trun_cd_orig_P1`, apply analyst |
| PNG decode | 33-37 ms per 2K map, 7-12 % of matcheck | Designer analyst |
| 2K export per render | lane 3.1 s, detail 3.2 s, decal 2.1 s; 52 renders ≈ 2.4 min; rebuild lane 02-06 ~19 s, detail 07-08 ~7 s, decal 09-10 ~10 s; sdcall 1.6 s per job | `build/job_*.result.json` |
| Background sdcall pickup | median 31 s per job (foreground 2 s), from 29 past jobs | transcripts (Designer analyst) |
| Main loop | session 2: 52 min wall, 24 min in 4 foreground suite waits; round-1 apply: 115 min, peak 896k context, 7.3 min / ~123k tokens to resume after a split | `context_cost/*_main.txt`, `apply/tl_*.txt` |
| Concurrency | 6 composites at once: 55-73 s each at default threads, against 28-34 s alone | review analyst (`review_round/`) |
| This brief's first run | ~45 min lost: one untimed profiler held a parallel() barrier | the lesson behind the time boxes in item C |

## Before session 4: close session 3's gate

1. **Save `findings.md` by extraction, not re-typing.** awk pulls the lead's 54 KB text out of its tool-results file in
   48 ms (tested), or `render_findings.py` renders it from `review_result.json`. That saves ~3-4 min of generation and
   ~14k tokens.
2. **Generate an apply pack** (`apply/apply_pack.py` prototype, 12.7 KB): per plan item, the decided option, the graph
   and stages, the files, and the verifier targets as numbers. Generate the ledger skeleton as well (8 items, 29 targets,
   0 unmatched). Point prompt 4's read list at them instead of `review_result.json` (69 KB) and 12 verify JSONs
   (~205 KB). That saves ~5-6 min and ~100k tokens at session start (estimate).
3. **Write the DECISIONS before session 4.** An undecided option blocks on AskUserQuestion: 18.6 min in the round-1
   apply.

## Session 4 runbook (ranked by value; the savings overlap)

A. **One batch per graph: lane → detail → decal, not one build-measure cycle per fix.**
   - The plan's dependencies stay inside one graph, except on P1 (checks only), so this is 3 cycles instead of about 7.
   - Saving: estimate 25-40 min.
   - Keeps: the cascade (rebuild every later stage) and one Designer call at a time.

B. **Write P1 in a subagent while the main loop runs the lane batch.**
   - Saving: estimate 15-30 min; it shares time with A.
   - Conditions:
     - re-verify P1's wrong builds on the final exports, because they edit the current exports;
     - a change to the skill's `matcheck.py` needs your approval to commit.

C. **A parallel suite runner, built properly before it is used as the gate.** This is the measured win: about 10.5 min
   per suite run, 20-30 min over 2-3 runs. Build it from the prototype, but the prototype is not gate-ready:
   - **Fail like the serial suite, and stricter.** Wrap every job in `timeout`, collect every exit code, and exit 1 on
     any non-zero rc.
   - **Delete `scorecard_<c>.*` before each matcheck**, and read pass/fail from the scorecard JSON. Fail on hard
     failures, on any `errors`, and on vacuous hard checks.
   - **Fix the same gap in today's `run_all.sh`.** It only greps "Hard failures: none", so an errored or vacuous hard
     check passes. After a config error it reads the old scorecard. It also ignores the exit codes of `accept_r1.py`,
     `decal_extra.py`, `previews.py` and `composite.py`. Nothing slipped through in session 2: every config reads
     "Errors: none. Vacuous: none."
   - **Wrong builds per config** needs a `--tag` option in `checks/wrong_builds.py` (only the scratch copy has it). It
     also needs a real merge step:
     - take the expected configs from the same lists the suite uses, plus `ladder`;
     - fail if any per-config file is missing or older than the run;
     - rebuild `wrong_builds.md/json` with the "Not covered" header and exit 1 on bad or uncovered checks;
     - delete the per-config files before each run.
     (`wb_merge.py` today only compares rows.)
   - **Use the unsplit layout that was measured** (p8f): one job per matcheck config, wrong-build config and lane
     composite; previews one job per graph; `composite_decal` one job. Splitting previews and composites per preset or
     site was slower (199 s) and loses the `compare_*` sheets and the combined composite sheet.
   - **Shadows:** run the row-blocked `shadow_vis` as a wrapper in the tools folder. Record in the gate report that it
     was used (justified by the identity checks). Moving it into the skill's `previews.py` needs your approval to commit.
   - **Threads:** set `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=2` so the machine stays usable. The 158 s was measured
     without the cap, so re-time with it.
   - **Validate once against a serial run:**
     - same scorecards, `wrong_builds` summary and composite JSON;
     - one run with a broken config and one with an over-time job, both of which must fail.

D. **Targeted check sets while iterating.**
   - During a batch, run that graph's configs and wrong builds. Always include the cross-graph jobs: `ladder`,
     `wb_ladder`, `accept_r1`, `composite.py` and `composite_decal`, since they read lane and detail together and the
     decal composite reads both. The decal set takes 44-58 s (`par_dec8f`, `par_dec12fs`); the lane set is estimated at
     ~2.4 min.
   - Run every set when any of these change:
     - `build/presets.json` or `calibration.json`;
     - `00_env.py` or `00_decal_env.py`;
     - the `fade`/`PALETTE` copies in `06_shade.py`, `08_detail_build.py` and `00_decal_env.py` (they are copies, keep
       them in step);
     - `checks/gen_checks.py`, `wrong_builds.py` or `ladder.py`;
     - the skill's `matcheck.py`, `previews.py` or `sdkit.py`.
   - Saving: with C in place, small (a few minutes per round); its value is shorter loops, not a second saving on top
     of C.
   - Keeps: the full suite after the last change, before any report.

E. **Wait the right way.**
   - Run sdcall jobs under ~3 min in the foreground: pickup is 2 s, against 31 s in the background.
   - Background a suite only when there is real work to overlap (the ledger, docs, the next fix's script). Otherwise run
     the 2.6-min parallel suite in the foreground.
   - Saving: 3-5 min per session in pickup (measured), plus the overlap (estimate).

F. **Tune soft metrics on a preset subset, with sweeps.**
   - A decal iteration on 4-5 presets (8-10 renders instead of 22) saves ~25-30 s of Designer time plus checks.
   - One sdcall job can render 3-4 candidate settings (AA band width, facet amplitude, lump scale) for scratch checks.
     The precedent is `job_decal_outline_sweep`.
   - 1K agrees with 2K on today's all-pass build: 183/183 decal verdicts, though without rescaling the pixel-unit
     parameters; with rescaling (`apply/k1/make1k.py`), 37/37 on P1 and Q1. That shows nothing about catching a
     failure. Treat a 1K pass as a cue to export at 2K, not as evidence.
   - Judge the pixel-scale fixes (colour AA, wall striations, rim band) at 2K only.
   - The gate exports every preset at 2K.

G. **Calibrate once per graph, after its structural edits.** Past loops took 7.2, 3.5 and 12.7 min.
   - Regenerating presets can wait until a save only while no save happens. Any batch that ends in a save re-runs
     `presets.py` if 02, 07 or 09 ran (prompt 4's rule).
   - Every save is followed by `presets.py --check`.
   - Not needed if the decal fixes stay in stage 10.

H. **Keep the main loop light.** Each prototype below is in the scratchpad, mostly tested.
   - **`state_digest.py`:** 2.1 KB in 0.08 s covering freshness, hard pass/total and soft fails for 26 configs, the
     ladder, wrong-build counts and INV-16. It replaces ~61k tokens of scorecard reading.
   - **Put the `wrong_builds.md` summary first** and move its 581-row table to a second file (~19k tokens per read).
   - **`probe_io.py`:** RGBA order, `/c/` paths, UTF-8 and the scorecard schema. It removes ~7 of session 2's 15
     friction events. Start commands with `PYTHONUTF8=1`.
   - **Read code through `codemap.py`** (23 scripts in 15 KB) and the spec through `spec_section.py`. The round-1
     apply read 80k chars of spec.
   - **A bookkeeping subagent** for the ledger and the context file (estimate 8-12 min).
   - **A checkpoint file at every batch boundary:** a resume drops from 7.3 min to ~2 min (estimate).
   - **Trim `CONTEXT_PROMPT.md` from 28 KB to ~12 KB.**

I. **Optional: export only the nowear outputs the checks read** (traced: lane 7 of 24 maps). It saves ~27 s per full
   export and 7 s for decal. It relies on C's error gate to fail loudly on a missing map.

**Session 4 overall:** the apply analyst estimates ~3-4 h if the prompt is run literally and ~1.5-2 h with this
runbook. Both figures are scaled from the round-1 apply (103.5 min active for 10 items on 2 graphs), not measured.

## Keep as is

- The full suite (all graphs, ladder, wrong builds, composites) after the last change, before any report or gate.
- R6: every hard check passes on the real maps and fails its named wrong build.
- One Designer call at a time; the suite runner never touches Designer.
- The stage cascade, nowear as the controlled reference, and `presets.py --check` after every save.
- Previews and composites shown at the gate.
- Ask before committing to the bridge repo (the skill's `previews.py`, `matcheck.py`, `sdkit.py`).

## Dropped

- **A decoded-map `.npy` cache:** decode is 7-12 % of matcheck.
- **Lower PNG compression or raw arrays from Designer:** that saves write time only (~70 s per full export), for a large
  change.
- **A wrapper graph that computes several presets per call:** speculative, and it adds graphs to the package.
- **Stopping verifiers from re-running matcheck:** 2 of 993 subagent Bash calls did.
- **Splitting previews and composites per preset or site inside the suite:** slower (199 s against 158 s), and it loses
  the compare sheets.

## Build order before session 4 (about 2-2.5 h, once)

1. Extract `findings.md`; generate the apply pack and the ledger skeleton; edit prompt 4's read list (30 min).
2. ~~Fix today's `run_all.sh` gate gaps (exit codes, stale scorecards, errors and vacuous hard checks).~~ Done
   2026-10-04 (`checks/scorecard_gate.py`; see Status).
3. Build the parallel runner: time boxes, exit codes, the `--tag` patch and the real merge, the thread cap, the shadow
   wrapper. Validate it against a serial run and two deliberate failures (60-75 min).
4. `state_digest.py`, `probe_io.py`, and the `wrong_builds.md` summary split (40 min).
