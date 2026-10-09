# Context: speed review and rework of the material workflow

## Task

Making one material with the bridge and the `sd-material-research` skill takes many hours, and every stage is slow.
Review the whole workflow for speed: the code, the skill's docs and workflows, and the way sessions run it. Then
propose a reworked workflow that makes a new material much faster, with ranked changes and an implementation plan. I
chose these options on 2026-10-04:

- **Scope:** the whole pipeline, from the interview to the final gate, including the main session's own loop (model
  time, context growth, waits, hand-offs). Build (Designer), Measure (checks) and Review + apply are all in scope.
- **Depth:** a **structural rework**. The four round-2 documents are evidence and candidate parts, not the plan. Design
  the workflow from the measured time sinks, even if that drops planned work. Say what you drop and why.
- **Changes:** a **report and plan only**. Don't change code in the repo or in any material's tools folder. Prototypes
  and timing harnesses go in your scratch folder. A later session builds what I approve.
- **Environment:** this Mac, **with live Designer profiling** under the rules in "Designer profiling".
- **Code under review:** `code-review-fixes-public`, the code as it will land. The live install is `main`, so live
  timings measure main. Say so wherever the two differ.
- **Trade-offs:** proposals **may trade rigor for speed**. Each one must say what it gives up, which past catch it
  would have missed (with a source), and how a regression would show up.
- **Output:** a markdown report in the repo, like the round-2 briefs, **plus a private Artifact page** where I accept,
  reject or defer each proposal and the page saves my choices.
- **Target:** you measure today's stage times and **propose a target per stage**, with the evidence behind it.
- **Orchestration:** the Workflow tool for steps 1-4 (four workflows, about 20 agents). My opt-in is in my kick-off
  message; if it isn't there, ask me before step 1.

This file is untracked. Never commit, stash, clean or delete it. It was written against `main` at `ae8551d` and
`code-review-fixes-public` at `3cc34de`. If either has moved, review it as it is and say so in the report.

**Continuing:** if my kick-off message points you at `$OUT/CONTINUE_PROMPT.md`, an earlier session stopped at its
context budget. Follow that file: don't start over, and don't re-ask the questions it records as answered. The rules in
"Context budget and hand-over" apply to you too.

**Before any work, including extracting trees, ask me these in one AskUserQuestion round:**
1. Is Designer free for about 90 minutes of profiling? I can't use it meanwhile.
2. E9 needs one Designer restart and E3 needs the probe graph closed in the Graph view. May you ask me to do those by
   hand when you get there?
3. Have I copied any Windows data to this Mac (see "Evidence", the Windows-only row)? If so, where?
4. Go ahead with the plan below (about 20 agents, report plus Artifact, stop at the gate)?

## Paths

Most paths contain spaces: quote them, and use `$HOME` rather than `~` inside quotes. Subagents and fresh Bash calls
don't inherit shell variables. In workflow scripts, write paths out as absolute `/Users/andybui/...` strings.

```
REPO="$HOME/Documents/Allegorithmic/Substance Designer/python/sduserplugins/sd-claude-bridge"
SD="$HOME/Documents/Allegorithmic/Substance Designer"
DEV="$SD/sd-material-research-dev"                     # skill dev folder, not in git
OUT="$DEV/speed_review"                                # durable: progress file, results, probe copies, artifact source
SCOUT="$OUT/2026-10-04_scout"                          # scout reports from the session that wrote this file
T="$SD/asphalt_materials_tools"                        # asphalt tools, Mac copy (older than Windows; see Evidence)
BRICK_T="$SD/brick_materials_tools"
TX="$HOME/.claude/projects/-Users-andybui-Documents-Allegorithmic-Substance-Designer-python-sduserplugins-sd-claude-bridge"
APP="$HOME/Library/Application Support/Steam/steamapps/common/Substance 3D Designer 2022/Adobe Substance 3D Designer.app/Contents"
SDPY="$APP/plugins/pythonsdk/bin/python3.9"            # Designer's Python 3.9.9
VPY="$HOME/Library/Application Support/sd-claude-bridge/venv/bin/python"   # MCP server venv (3.12)
SKPY="$HOME/.cache/sd-material-research/venv/bin/python"                   # analysis venv (3.14: numpy, scipy, PIL, cv2)
SK="skills/sd-material-research"                      # relative to a tree root
SCRATCH=<your scratchpad directory>; each agent works in $SCRATCH/<agent-label>/   # gone in a new session
```

Extract both trees with no git state change (re-extract on resume):

```
mkdir -p "$SCRATCH/pub" "$SCRATCH/main"
git -C "$REPO" archive code-review-fixes-public | tar -x -C "$SCRATCH/pub"
git -C "$REPO" archive main | tar -x -C "$SCRATCH/main"
```

Line numbers in this file are for `pub` unless marked `main`.

## Live installs and branches

- **The live installs are symlinks into `$REPO`** (branch `main`): `sduserplugins/sd_claude_bridge`, the three files
  in `~/Library/Application Support/sd-claude-bridge/`, and `~/.claude/skills/sd-material-research`. Any file written
  under `$REPO/designer_plugin`, `$REPO/mcp_server` or `$REPO/$SK` lands in my live setup. Never pull, merge, reset,
  switch or stash anything in `$REPO`.
- Designer 12.4.1 runs main's plugin, so **live timings measure main**. Switching the install to pub needs my yes;
  propose it as an optional experiment if a decision depends on it.
- `code-review-fixes-public` holds 32 code-review commits on merge base `146488d`: 24 files, +1,024/-270, mainly
  `bridge.py`, `commands.py`, `sd_designer_mcp.py`, `sdkit.py`, `sdcall.py`, `matcheck.py` and `previews.py`, plus
  `tool_call.py`, `review_round.js`, `SKILL.md`, `checks.md`, `sd_craft.md` and the installers. Pub's MCP server
  serialises tools behind an `anyio.Lock` in a worker thread; main has no lock.
- `main` has 9 newer commits: the round-2 documents, sdkit's generic helpers (`0a78144`) and `scripts/wrong_builds.py`
  (`489003b`). A merge of main into pub **conflicts in `sdkit.py`** (main's `_fn_extra` against pub's `_check_spec`).
  Landing is my call: don't resolve it. Review `wrong_builds.py` and the new sdkit helpers from `$SCRATCH/main`.

## The pipeline and where the time goes today

The skill's stages (`$SK/SKILL.md`): 0 orient, 1 interview, 2 research, 3 spec (gate), 4 build in Designer through
`sdkit.py` stage scripts, 5 measure (`matcheck.py`, `previews.py`, `wrong_builds.py`), 6 review (an adversarial
panel, `review_round.js`), 7 iterate (apply the plan, re-measure, review again; three rounds is typical) and hand off.

"Mac" numbers come from this machine's transcripts and files, "Win" numbers from the round-2 documents (Windows, 32
logical CPUs). This Mac is an M1 Pro with 8 CPUs and 32 GB, so Windows numbers don't transfer.

| what | number | machine | source |
|---|---|---|---|
| Asphalt first build, prompt to wrap-up after the 1K checks of both graphs (no panel) | 91 min: model generation 53.9 (59 %), Bash 13.8, MCP 3.7, waiting on the research agent 8.8, waiting on me 9.9 | Mac | `$SCOUT/transcripts.md` §2a (29b1b020) |
| Same build, model output | 346k output tokens, 53 % thinking; 17 responses of 5k+ tokens took 28.9 of the 53.9 model minutes; one took 390 s | Mac | `$SCOUT/transcripts.md` §3 |
| Context growth | 63k → 358k after research → 645k peak, no compaction (brick: 633k) | Mac | same |
| Research agent (asphalt) | 25.8 min, 16.9 of it model time; 48 searches, 63 fetches | Mac | `$SCOUT/transcripts.md` §2a |
| Spec dry runs (3 evals), interview to spec, with skill vs without | 1326 s vs 692 s (1.92×), 2.19× tokens. Not like for like: pass rate 100 % vs 57 %, about 2.6× the tool calls | Mac | `$DEV/workspace/iteration-1/benchmark.md`:10-12 |
| Brick build, 3 review rounds (before the skill existed) | 223 min active; the 3 reviewer workflows took 123.7 min (28.4, 46.5, 48.7; 55.6 %), and the main session was idle for about 120 of them | Mac | `$DEV/notes/process_notes.md`:14, :47; `$SCOUT/transcripts.md` §2b |
| Brick Designer stall (FX-map noises at high scale) | about 19 min (about 18 with the 8-bit `$format`), then 6 s per full 2K compute of the 87-node core | Mac | `process_notes.md`:34, :373 |
| Brick calibration | about 29 Histogram Scan re-calibrations | Mac | `process_notes.md` |
| Lane render through sdkit at 1K | compute 2.3-3.2 s, total 2.7-3.5 s; 22 outputs, 27 once stage 06 ran; nowear costs the same | Mac | `$T/build/job_*.result.json` |
| Lane rebuild, stages 02-05 (one run) | 164.1 s in-script; sdcall 172.0 s including a 6-output 2K probe | Mac | `$T/build/job_rebuild_all.result.json`; `$SCOUT/designer_side.md`:66 |
| Lane rebuild, stages 04-05, three runs | 77.4 s in-script on the first run (sdcall 108.2 s with 10 exports totalling about 30 s), then 15.6 s and 15.5 s with more nodes. 04-06: 23.3 s. Win, later graph: lane 02-06 about 19 s | Mac / Win | 29b1b020 L805, L858; `job_rebuild_45/456.result.json` (last run only); speed brief:46 |
| Reviewer round 2 (asphalt) | about 2 h, critical path about 116 min, 26 agents, 8.4M subagent tokens, 222 helper scripts | Win | process brief §1 |
| Measurement suite | 786 s serial, 158 s at 8 workers with row-blocked shadows; real `run_all.sh` 13.5-14.2 min | Win | speed brief |
| Background sdcall pickup | median 31 s, against 2 s in the foreground (29 jobs) | Win | speed brief |
| Main-loop sessions | round-1 apply 115 min wall (103.5 active, 10 items on 2 graphs), peak context 896k, 7.3 min to resume after a split; session 2 (decal measurement and check building, not an apply) 52 min with 24 min in 4 foreground suite waits | Win | speed brief:48, :159; tooling brief:6 |
| Python start-up per process | `import numpy, PIL, scipy, cv2`: 0.46-0.69 s in the scout's runs, 0.21-0.22 s warm | Mac | `$SCOUT/measure_orchestration.md`; the prompt check |

The pattern: in the first build the model's own turns dominate; in the review rounds the panel dominates while the
main session waits; Designer compute is small once heavy noises are avoided. But the same Mac stage scripts ran 5×
slower on one run than on the next (04-05: 77.4 s, then 15.5 s), and nobody has explained why.

## Evidence

| where | what |
|---|---|
| `$REPO/review_round2_process_brief.md` (95 lines) | reviewer round 2: stage times, causes, 10 changes, round-3 runbook (Win) |
| `$REPO/review_round2_speed_brief.md` (187) | closing a gate and running an apply session faster: suite parallelism, batching, waits, main-loop weight (Win) |
| `$REPO/review_round2_tooling_brief.md` (138) | matcheck gate, suite runner, non-tiling path, sdcall, sbsfix: G1-G3, S1-S5, N1-N4, R1-R3, D1-D3 |
| `$REPO/review_round2_implementation_spec.md` (2,269) | build spec for the review speed-ups (M0-M8). Read by section (`grep -n '^#'`, then `sed -n`), never whole |
| `$SCOUT/*.md` | five scout reports: transcript timelines, prior numbers by stage, round-2 item status, Designer-side and measure-side time maps with file:line. **Leads, not verified findings.** Start with `README.md` |
| `$SCOUT/parsers/` | transcript parsers (`tx.py` loads a jsonl; durations are tool_result minus tool_use timestamps) and event logs for 29b1b020 and 3afca382 |
| `$TX/*.jsonl` and `$TX/<id>/subagents/` | Mac transcripts. Builds: **29b1b020** (asphalt first build, 2026-10-03) and **3afca382** (brick, 2026-10-02, 27 MB). Skill dev and dry runs: fe1b9824, 1e5c7edd, 96add40e. Skip a5c025b5 (the session that wrote this file). Stream them; never Read a whole file |
| `$DEV/notes/` | `process_notes.md` (brick timeline, "if I did this again"), `designer_helpers.md` (bridge timings and limits), `toolkit.md`, `review_notes.md`, `timeline.txt` (449 KB) |
| `$DEV/workspace/iteration-1/*/{with,without}_skill/timing.json` | dry-run timings per eval |
| `$T/build/` | the Mac asphalt build: stage scripts `01`-`08`, `job_*.py` with `.result.json` timings, `export.py`, `presets.py` |
| `$T/dump/` (1K, 401 MB); `$BRICK_T/dump/` (2K, classic); `$DEV/tests/brick_dumps/` (2K, rustic and weathered) | maps for offline profiling; configs in `$T/checks/` and `$DEV/tests/matcheck/{classic,rustic,weathered}.json` |
| `$SD/code_review_report.md` | the earlier code review. Speed items: SRV-02, SRV-03, SRV-04, SRV-05, PLG-05, KIT-02, the 3.06 s library scan |
| **Windows only, not on this Mac** | the asphalt round-2 data: `review/round2/`, `review/agents/`, `ops/` (parallel-suite and main-loop prototypes), `checks/run_all.sh`, `checks/scorecard_gate.py`, `composite_decal.py`, `prompts/`, `apply/`, the decal graph, the speed-brief logs and the Windows transcripts. Use their numbers through the briefs and tag them `win` |

## Already planned

None of the round-2 tooling items (G, S, N, R, D) has landed on main; pub overlaps G1 (different exit codes), G3 for
sdcall, the S3 empty-reply path, and the block S5 edits. Of the process brief's 10 changes only 9 is partly there, and
of the implementation spec only M0 is done and M1 partly. Status per item: `$SCOUT/plan_status.md`. Planned effort is
about 30-37 h (tooling 15-16 h, spec 15-21 h), plus 2-2.5 h for the speed brief's build order. Re-rank all of it
against your own proposals by minutes saved per hour of work; dropping an item needs a reason. One trap:
`review_round.js` counts a finding without a verdict as rejected (:138-139), so "verify high and medium only" needs an
`unverified` status first.

## Leads

Hypotheses, not findings. Detail and file:line are in the scout reports: ML in `transcripts.md` §2-3, RS in
`prior_numbers.md`, DZ in `designer_side.md` §1-4, MS and RV in `measure_orchestration.md`. The ones to start from:

- **ML:** what the 5k+ token turns produced (build scripts from scratch, debugging, spec prose, long thinking), how
  much of the skill a session reads, effort settings, and what a template, generator or cheaper subagent could take.
- **RS:** `research_sheet.js` runs research, two audits and a revise in serial phases, and the auditor and reviser both
  re-open sources; a bundled sheet still gets a research pass; two interview rounds cost 7.7 min of my time.
- **DZ:** the 77.4 s vs 15.5 s rebuild runs (first compute after new node types? cold library loads?); `sk.lib` loads
  and unloads a library package per call; `_graph()` scans every package per op; nested undo groups; a save and lint
  per stage; stages reset by prefix, so re-running one re-runs every later one; `only` filters writes, not compute;
  sdcall from a background shell (31 s pickup); calibration loops (3.5-12.7 min, Win).
- **MS:** everything serial; `shadow_vis` (S1); no thread caps; `wrong_builds.Swap` flushes every derived cache on
  enter and exit (in no brief); matcheck recomputes EDTs, labels and gradients per check; `checks.md` timings ("a full
  run at 2048 takes about 30 s"; previews "about 4 s per 2048 variant") need re-timing.
- **RV:** the Agent-tool route in `review.md` puts barriers between lenses and verifiers; `BRIEF.md` grows each round
  and every agent reads all of it; the main session idles during the panel instead of preparing fixes.
- **Gates:** I want the interview, spec and plan gates. Their cost can still shrink: fewer rounds, decisions written
  before an apply session (an undecided option blocked 18.6 min, Win), CONTEXT_PROMPT files of 28 KB (Win; the Mac
  asphalt one is 12 KB).

## Ground rules

- **Read-only code.** Write only to `$SCRATCH`, `$OUT`, the report file in `$REPO` (step 5) and, after the gate, the
  hand-off file and the project memory. Never write under `$REPO/designer_plugin`, `$REPO/mcp_server`, `$REPO/$SK` or
  any material's tools folder. Set `PYTHONDONTWRITEBYTECODE=1` for your own Python runs.
- **Keep the main loop light**; it is part of what you're reviewing. Read large files by section and take structured
  results from agents.
- **Progress file.** Keep `$OUT/_progress.md` current: update it after every experiment, every workflow return and
  every answer from me, with what is done, what is next, where each result is, and whether the probe package is
  loaded. Save each workflow's returned JSON to `$OUT/results/<step>_<name>.json` and each timing to
  `$OUT/results/timings.jsonl` as soon as you have it.
- **Tag every number** in the report: `mac` (you measured it here, with n and range), `mac-tx` (from a Mac transcript),
  `mac-loaded`, `win` (from a round-2 document) or `est`. Don't add up savings that overlap.
- **Quiet machine for timings.** Repeat each timing at least 3 times; report the median and range; time cold and warm
  runs separately; record the 1-minute load average. A timing counts as `mac` if the load stays under 2, otherwise
  `mac-loaded`, and you re-time any `mac-loaded` number a top-10 proposal depends on.
- **Thread caps** for any parallel numpy work:
  `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=VECLIB_MAXIMUM_THREADS=2`. The
  implementation spec (:1838) gives the Workflow tool's agent cap as min(16, CPUs - 2), which would be 6 here (not
  verified).
- **Quality floor.** Trade-offs are allowed but flagged. These mechanisms have a record of catching real defects; a
  proposal that weakens one must cite what it caught:
  - adversarial verification (round 2: it changed severities on 11 of 35 findings and caught overstated numbers);
  - every hard check failing its named wrong build (R6);
  - the `nowear` controlled render;
  - a full suite after the last change, before any report;
  - one Designer call at a time;
  - research before the spec (the brick build invented its targets reactively and needed extra rounds).
- **Don't re-measure what is settled** unless the Mac could change the decision. Example: PNG decode is 33-37 ms per
  2K map (Win), which is why a decode cache was dropped.

## Context budget and hand-over

Keep the main session under about **500k tokens** of context. Past that, turns get slow and less reliable (the round-1
apply peaked at 896k and took 7.3 min to resume, Win). When you get close, stop at a clean point and hand over to a
fresh session.

**Measure it.** At step 0, find your own transcript: run `echo SPEEDREVIEW-$(date +%s)`, then `grep -l` that marker in
`"$TX"/*.jsonl`, and record the path in `_progress.md`. Check the size at every step boundary, after every workflow
returns, and after every few experiments:

```
python3 - "<your transcript>" <<'EOF'
import json, sys
u = None
for line in open(sys.argv[1]):
    try: d = json.loads(line)
    except Exception: continue
    m = d.get("message")
    if d.get("type") == "assistant" and not d.get("isSidechain") and isinstance(m, dict) and m.get("usage"):
        u = m["usage"]
print(sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")) if u else "no usage")
EOF
```

Log each reading in `_progress.md`. Keep workflow returns compact (structured fields, no file dumps), so that one
return doesn't add 50k tokens.

**At about 400k:** start no new workflow, and no experiment batch that won't finish well under 500k. If you reach the
gate above 400k, write the continuation prompt anyway, so the post-gate work starts fresh.

**At about 500k, stop at the next clean point.** A clean point means:
- the current Designer job has returned (never stop mid-job or with a timed-out job still running);
- any running workflow has returned and its JSON is saved. Wait for it: a workflow can't be resumed from another
  session;
- every result so far is in `$OUT/results/`.

**Before you stop:**
1. Leave Designer clean: clear the probe from sdkit's state and unload the probe package (Designer profiling, setup
   step 5). If anything stays loaded, record exactly what.
2. Bring `_progress.md` up to date.
3. Write `$OUT/CONTINUE_PROMPT.md`. If one already exists, rename it to `CONTINUE_PROMPT.<n>.md` first. Keep it under
   about 80 lines, with pointers rather than copies:
   - "Read `$REPO/speed_review_context.md` first; this is continuation n";
   - my answers so far (setup questions and any decisions), so the next session doesn't ask again;
   - the step reached, what is done with the path of each result, and the exact next action;
   - the state of Designer and the machine: probe loaded or not, any job that may still be running, and the stopped
     session's transcript path;
   - where the numbers the next steps depend on are (the reference-scenario baseline, the verified proposals);
   - dead ends and surprises, so they aren't repeated;
   - the agents used so far against the budget of about 20;
   - a reminder to re-extract the trees, since `$SCRATCH` doesn't carry over.
4. In chat: say why you stopped and where, then give me the kick-off message to paste, in a code block:

   ```
   Read <OUT>/CONTINUE_PROMPT.md and continue the speed review from where it stopped. I opt in to the Workflow tool for its remaining workflows (stay within the agent budget it records). Keep the progress file current.
   ```

   Write `<OUT>` as the absolute path. The opt-in must stay in the message: it has to come from me.

## Designer profiling

Only the main session talks to Designer, one call at a time. Agents never call substance-designer tools or the bridge
socket; an agent that needs a Designer number describes the experiment in its output, and you run it afterwards.

**Setup**
1. `designer_status` and `list_packages`. If `asphalt_materials.sbs` or `brick_materials.sbs` is open, leave it alone.
2. Profile on copies only. Copy `$SD/asphalt_materials.sbs` to `$OUT/probe/asphalt_speedprobe.sbs`, and `$T/build`
   and `$T/registry.json` to `$OUT/probe/tools/`. For small cases (E4-E6), copy `$DEV/sdkit_test/sdk_test.sbs` to
   `$OUT/probe/` too; don't reuse its `job_export.py`, which configures a scratchpad that no longer exists.
3. **The Mac build scripts hard-code the originals, and every stage script ends with `sk.save()`.** Rewrite the copies
   in this order:
   - replace the literal `~/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools` (in `00_env.py`, every
     stage script, `export.py` and the `job_*.py` files) with the absolute `$OUT/probe/tools`. Exports and probes then
     land in `$OUT/probe/tools/dump`, because sdkit derives the dump folder from `TOOLS`;
   - then replace `asphalt_materials.sbs` with `asphalt_speedprobe.sbs` everywhere, including the `graphs` and
     `sections` keys of the copied `registry.json`. Otherwise `sk.use()` starts with an empty registry, `reset()`
     deletes nothing, and the stages build duplicates beside the existing 610 nodes;
   - in the `00_env.py` copy, set `sys.dont_write_bytecode = True` before `import sdkit`, so Designer's Python writes
     no `__pycache__` into the live skill. Put timing wrappers around `sk.*` after its `importlib.reload(sk)`, which
     every stage re-runs.

   `grep -rn "asphalt_materials" "$OUT/probe/tools"` and `grep -rn "asphalt_speedprobe_tools" "$OUT/probe/tools"`
   must both print nothing before the first run.
4. Pass `graph="asphalt_speedprobe.sbs::asphalt_lane"` (or the sdk_test copy's key) on every substance-designer call
   while profiling. Without it, tools act on the graph in the Graph view, and `save_package` would overwrite that
   package.
5. When you are done, clear the probe from sdkit's in-process state, or my next build in this Designer session writes
   probe keys into `$T/registry.json`:
   `import sd; [d.pop(k) for d in (sd._sdk["reg"], sd._sdk["sections"]) for k in list(d) if k.startswith("asphalt_speedprobe.sbs::")]`.
   Then unload the probe package. Never save the original packages; never edit `$T`.

**Safety**
- Keep `run_python` under 45 s. Beyond that, run the live `"$REPO/$SK/scripts/sdcall.py"` in the foreground with the
  Bash timeout at 600000 ms: the 120 s default kills the shell, not the Designer job, and the reply is lost. Use
  `run_in_background` only for E8 and for jobs that may pass 10 minutes.
- Never retry a call that timed out. Wait, then check with `designer_status` or
  `sample <pid> 1 | grep SDSBSCompGraph_compute`.
- Avoid the heavy FX-map noises in sdkit's `HEAVY`.
- Never quit, kill or relaunch Designer yourself. When E9 needs a restart, list the open packages and ask me to do it.
- If Designer seems stuck, stop and tell me.

**Experiments.** A starting list; add or drop one with a reason. Instrument inside the job with `time.perf_counter()`
and write the splits to the job's result JSON.

| id | question | method |
|---|---|---|
| E1 | Per-request overhead | `ping` and `info` × 20 in one `$VPY` process (`sys.path.insert(0, "$HOME/Library/Application Support/sd-claude-bridge")`, `import sd_designer_mcp as s`, time `s.call("ping")` in a loop); then × 5 as separate `"$VPY" "$REPO/tools/tool_call.py" --raw ping` runs for the per-process cost; one MCP `designer_status` for comparison |
| E2 | Where the lane rebuild's time goes, and why runs differ 5× | rebuild 02-05, then 06, on the probe, split into node creation, wiring, `lint`, `save`, compute and write per stage. Run it twice in a row. Compare 02-05 with the 164 s in `job_rebuild_all.result.json`, 04-05 with the 77.4 s / 15.5 s runs, and 02-06 with Win's ~19 s (a later graph) |
| E3 | Hidden main-thread work after a job | a `ping` right after a long job returns, with the probe graph open in the Graph view, then closed (I close it) |
| E4 | `sk.lib` cost | the first library instance vs 10 repeats of the same and of different library nodes |
| E5 | `_graph()` lookup cost | one sdkit op with 1, 3 and 5 packages loaded |
| E6 | Undo-group cost | 200 nodes through `C.cmd_*` inside `run_python` vs direct `sd` API calls |
| E7 | Export split | compute vs write at 1K and 2K; all outputs vs `only` the maps the checks read; one preset vs its nowear |
| E8 | sdcall pickup on this Mac | the same short job × 5 in the foreground and × 5 from `run_in_background` |
| E9 | Cold vs warm | `search_library` and the first compute after new node types, after a restart (I do it) vs warm |
| E10 | `save_package` | × 5 on the probe package, with `graph=` |
| E11 | Preview path | `render_preview` vs an sdkit export plus a local downscale |
| E12 | One calibration cycle | probe, `calibrate.py`, re-set Position, re-export |

**Offline timings** (no Designer; `$SKPY`; quiet machine). Run scripts from the extracted trees, never from `$REPO`:
matcheck and previews from `$SCRATCH/pub` (spot-check main where they differ), wrong_builds from `$SCRATCH/main` (pub
doesn't have it). Tag each number with its tree. **Always pass `--out` into `$SCRATCH`:** without it matcheck writes to
the config's `out_dir`, which is `$T/review` for the asphalt configs and would overwrite the real scorecards. Run the
configs in place, because their map `dir` is relative.

| id | question | method |
|---|---|---|
| O1 | matcheck per check | cProfile on `$DEV/tests/matcheck/classic.json` (2K) and `$T/checks/lane_v2.json` (1K): seconds per check and the top functions |
| O2 | previews | per-variant time and `shadow_vis`'s share at 2K |
| O3 | wrong_builds | per-case time and the share spent in `Swap` flushes and re-derivation. No cases module exists on this Mac: write one with 3-5 cases in `$SCRATCH/o3/` (pattern in main `references/checks.md`:222), run against `$DEV/tests/matcheck/{rustic,weathered}.json` with `--checks-dir "$DEV/tests/matcheck" --out "$SCRATCH/o3"`, and tag it as a synthetic case set |
| O4 | process overhead | Python start and imports, cold and warm; `setup_env.sh` per call |
| O5 | worker count for this Mac | 1, 2, 4 and 6 parallel matcheck jobs at 2 threads each: wall time and machine responsiveness |

## Review process

### Budget

- **Agents:** about 20 in total, over four workflows of fewer than 10 agents each. Ask me before going over.
- **Models:** transcript miners `model: 'sonnet', effort: 'medium'`; the completeness critic `effort: 'medium'`;
  finders, skeptics, designers and judges inherit the session model.
- **Time boxes**, written into every agent prompt: miners 30 tool calls / ~12 min; finders 40 / ~15 min; skeptics
  25 / ~12 min; designers, judges, the critic and gap finders 15 / ~10 min. At the limit an agent returns what it has,
  plus a `not_checked` list.
- **Prompts:** one short shared preamble (the Paths block written out absolutely, the Live installs paragraph, the
  ground rules), then only that agent's area and its leads. Pass schemas through `schema` only. Never paste this whole
  file into an agent or tell one to read it. Agents can't ask me anything; open questions go in their output.
- **Workflow scripts** have no file access and no `Date.now()` or `Math.random()`. Pass earlier results in through
  `args`, or as `$OUT/results/` paths the agents read.
- **Pipelines, not barriers.** Never let an untimed profiler hold a `parallel()` barrier: one did in round 2 and cost
  about 45 min.

### Steps

**0. Setup, inline.** Ask the four questions first. Then check both branch heads, extract the trees, read
`$SCOUT/README.md`, skim the scout reports, start `$OUT/_progress.md` and record your transcript path (Context budget
and hand-over).

**1. Measure.** Two tracks:
- *Transcript mining, one workflow of 3 Sonnet miners, started first* (light on CPU):
  - **M1:** 29b1b020. Split the model time by activity (writing build scripts, debugging, reading docs, writing spec
    and checks, long thinking with little output), count the tokens spent reading skill files, and list the friction
    events with the time each cost.
  - **M2:** 3afca382, the same, plus each reviewer workflow's critical path.
  - **M3:** the dry runs in 1e5c7edd and their `timing.json` files: where the with-skill runs spent the extra time,
    and how much of it bought the higher pass rate.
- *Designer timings in the main session* while the miners run (E1-E12), then the offline timings O1-O5 once they have
  returned.
- Then define **one reference scenario** (for example: a material with a bundled sheet, two graphs of about 600 and
  120 nodes, 5 + 9 presets, a first build and three review and apply rounds) and its baseline timeline per stage, from
  the measurements. Express every saving against it.

**2. Find and verify, one workflow.** Six finders in three pairs: DZ + MS, RS + RV, ML + XS. Run `pipeline()` over the
pairs: stage 1 runs the pair's two finders in parallel, stage 2 is one skeptic for both (9 agents). No barrier across
pairs.

| id | area | files and inputs |
|---|---|---|
| ML | main loop and model time | M1-M3 results, `SKILL.md` and what it tells a session to read, `assets/context_prompt_template.md` |
| RS | interview, research, spec | `references/{interview,research,method}.md`, `assets/workflows/research_sheet.js`, `assets/spec_template.md`, the dry runs |
| DZ | Designer side | `bridge.py`, `commands.py`, `sd_designer_mcp.py`, `sdcall.py`, `sdkit.py` (pub and main), `references/sd_craft.md`, `$T/build`, E1-E12 |
| MS | measure | `matcheck.py`, `previews.py`, `wrong_builds.py` (main), `calibrate.py`, `setup_env.sh`, `references/checks.md`, O1-O5 |
| RV | review and apply | `review_round.js`, `references/review.md`, the process brief, speed brief and implementation spec, judged as proposals: keep, change or drop |
| XS | what can overlap across stages | the stage graph: what runs beside what (research beside the build skeleton, the next fixes beside the panel, docs beside the suite), and what each gate really blocks |

Skeptics try to refute each proposal: re-derive the numbers, find double counting with other proposals, check that a
rigor cost is stated honestly, and check that the code path exists in pub. Verdicts: holds, overstated (with a
corrected saving), refuted, or duplicate (of which id).

**3. Design the workflow, one workflow.** Three designers each draft a complete workflow from the verified proposals
and the baseline timeline:
- **D1, lean current shape:** keep the stages and apply the best fixes.
- **D2, overlap first:** restructure what runs concurrently, and which gates block what.
- **D3, numbers first, light panel:** the checks and suite carry most of the verification; the panel only judges what
  numbers can't.

Each draft gives a stage timeline with an estimated wall time against the reference scenario, the proposals it uses,
its rigor costs and the gates it keeps. Two judges score every draft on time saved, quality risk, implementation
effort and fit with my gates. You synthesise the winner, grafting the best parts of the others, and record why the
others lost.

**4. Completeness, one workflow.** One critic gets the compact proposal list and the chosen shape, and names up to 5
gaps (a stage with no measurement, a proposal with no verification, an unread source). Run at most 2 gap finders on the
top ones. List the rest under "Not covered".

**5. Report and Artifact**, below. Then stop at the gate.

### Proposal schema

- `id` (area plus a counter: `DZ-03`), `title`, `stages`, `kind` (code, doc rule, process or structure)
- `today`: what happens now, with file:line (pub, plus main where it differs)
- `evidence`: claims, each with a source and a tag
- `saving`: minutes per reference material (low and high), whether it is on the critical path, and the ids it overlaps
- `effort_h`, `depends_on`, `conflicts` (pub commits, round-2 items, the sdkit merge)
- `rigor_cost`: `none`, or what it gives up, the past catch it would have missed (with source), and the regression
  signal
- `round2`: the round-2 items it keeps, replaces or drops
- `confidence` (high, medium or low) and `verify_after`: the timing to re-run once it is built

## Report and Artifact

**Report:** `$REPO/review_round3_speed_rework.md`, in the style of the round-2 briefs (plain sentences, tables, every
number tagged and sourced), under about 400 lines. Give the full schema for the top 10 proposals only; the rest go in
the section 5 table and in `$OUT/results/proposals.json`. Sections:
1. Summary: today's timeline and the proposed one per stage, with a target per stage.
2. Where the time goes: the reference scenario and its baseline.
3. Experiments: each E and O id with its method, n, median, range, machine and tree.
4. The recommended workflow: a stage diagram of what runs in parallel, which gates stay, and what is dropped. Then the
   two runner-up shapes and why they lost.
5. Proposals ranked by minutes saved per hour of work. Trade-offs flagged.
6. The round-2 plan re-ranked: kept, changed, dropped or superseded, each with a reason.
7. Rejected proposals, with the skeptic's reason, so nobody proposes them again.
8. Not covered, including checks that need Windows or pub installed live.
9. DECISIONS: empty until the gate.
10. Implementation plan: empty until the gate.

**Artifact:** call `Artifact` with `action: "quickstart"` and `intent: "other"` first, then load the
`artifact-capabilities` and `dataviz` skills before writing the page. One private page with:
- the before and after stage timeline as a chart;
- the proposals as cards I can filter by stage and kind, each with accept, reject or defer and a note. Trade-off
  proposals get a visible badge and show their rigor cost;
- my choices saved in the page's `db` capability, one row per proposal (id, decision, note).

Keep its HTML source in `$OUT/`.

## Gate and after

- **Stop after publishing.** In chat: the link, the top five proposals, the recommended shape with its per-stage
  targets, and any open questions. Wait until I say in chat that I've decided.
- **After I decide:**
  - read my rows with `ArtifactData`;
  - fill DECISIONS and the implementation plan in the report: milestones in dependency order, files, tests, and the
    timing that proves each milestone;
  - write an untracked hand-off, `$REPO/speed_rework_impl_context.md`, for the session that builds it, in this file's
    format;
  - update the project memory with the decisions and where the hand-off is.
- **Commits:** ask before committing the report, and ask whether it goes on `main` (as the round-2 briefs did) or on a
  branch. A branch is made in a separate worktree (`git -C "$REPO" worktree add "$SCRATCH/wt" -b speed-review-r3
  main`), never by switching branches in `$REPO`. Commit only the report. Push only on a separate yes: `origin` is the
  public repo. Never commit this file or the hand-off.
