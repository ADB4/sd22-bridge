# Round 3 speed review: reworking the material workflow for speed

2026-10-04. Covers the whole `sd-material-research` pipeline on this Mac (M1 Pro, 8 CPUs, 32 GB), from the interview to
the final gate: the bridge, the MCP server, `sdkit`, the measure scripts, the skill's docs and workflows, and how sessions
run them. Method: live Designer profiling on copies (E1-E12), offline timings (O1-O5), transcript mining (3 agents), six
finders with three adversarial skeptics, three competing workflow designs scored by two judges, and a completeness critic
with two gap finders: 20 agents in four workflows. Everything else lives in
`sd-material-research-dev/speed_review/` (`$OUT`): the progress file, `results/` (every timing, return and detail file),
`results/proposals.json` (all proposals, full schema) and the decision page source `speed_rework_decisions.html`.

Code under review is `code-review-fixes-public` (pub, `3cc34de`); the live install and every live timing is `main`
(`ae8551d`). Neither branch moved during the review. Where the two differ, the proposal says so (section 4, landing notes).
Nothing in the repo or in any tools folder was changed. Tags: `mac` = measured here on a quiet machine (none: see
section 3), `mac-loaded` = measured here with load above 2, `mac-tx` = from a Mac transcript, `win` = from a round-2
document (Windows, 32 CPUs), `est` = estimate. Savings overlap; they are never added up.

## 1. Summary

**Two Mac-only Designer defects make every Designer step 5-46× slower today.** macOS App Nap drops a background Designer
to scheduler priority 4, and the same job then runs 7.5-14.5× slower (E2b). The bridge's graph lookup walks every node of
every open package on every op, 87 % of rebuild time (E2). Fixing both took one job from 264 s to 5.7 s (`mac-loaded`).
They explain the brief's unexplained 77.4 s vs 15.5 s rebuilds and the 20-64 s first `search_library` calls in the Mac
transcripts. The fixes cost about 3 h (DZ-01, DZ-02). On Windows (`win`) Designer was already fast,
which is why the round-2 documents found it was "not the bottleneck"; on the Mac that becomes true only after these fixes.

**Measurement is fast here and parallelizes well.** One 2K matcheck config takes 5.85 s and 6 workers give 4.6× (O5), so a
scenario-R suite drops from ~12 min serial to ~3 min (MS-01). The row-blocked shadow rewrite buys little on the Mac
(shadows are 2.5-11 % of previews, O2).

**Review panels and applies dominate, before and after.** In the reference material (section 2) they are ~420 of ~571 min
today and ~338 of ~445 after the rework (~76 %). The remaining lever is the panel's shape and round count, which no
measurement here settles: the light-panel trial (TR-01) is how to find out.

**Recommendation: keep today's stages and gates and apply the best fixes (design D1), plus nine grafts.** About 25 h of
work (est) against the round-2 plan's 32-40 h. All three user gates and the whole quality floor stay.

| # | stage | today (min) | recommended | target | main proposals | evidence for the target |
|---|---|---|---|---|---|---|
| S0 | orient, read the skill | 4 | 3 | 3 | ML-07, SH-02 | doc reads 2.3 model min, ~83k tokens (`mac-tx`) |
| S1 | interview, 2 rounds | 10 | 10 | 10 | SH-02 (reading hidden, not counted) | 7.7 min are the user's (`mac-tx`); gate kept |
| S2 | research, bundled sheet | 26 | 18 | 17 | RS-01 | main idled 8.8 of 25.8 min (`mac-tx`); its own 16.9 model min is the floor |
| S3 | spec and approval | 12 | 11 | 10 | ML-07 | spec 5.7 model min + 3.5 rework (`mac-tx`) + gate est 3 |
| S4 | first build to green 1K checks | 45 | 34 | 30 | DZ-01, DZ-02, ML-01 | Designer jobs 11.2 min (`mac-tx`) → est 1-2 (E2b D7) |
| S5 | first 2K export and suite | 17 | 7 | 5 | MS-01, DZ-03 | 28 renders ~1.5 min held (E7) + suite 2.6-3.2 min (O5) |
| S6 | review panel ×3 | ~230 (180-300) | ~194 | ~160 | RV-03, RV-05, SH-01 | brick panels 123.6 min (`mac-tx`) scaled to asphalt; boxes sim 46.5 → 35.2 min a round |
| S7 | apply ×3 | ~190 (147-217) | ~144 | ~100 | RV-01, RV-02, RV-04, MS-01, XS-01 | win R1 115 + brick decay; brick batched applies 25.9/15.9/7.1 (`mac-tx`) |
| S8 | hand-off and resume ×3 | 37 | 24 | 10 | XS-02 | resume 7.3 min (`win`) + prompt est 5, hidden under the panel |
| | **total** | **~571 (478-668)** | **~445 (372-524)** | **~345** | | all `est`; saves ~126 min (~22 %) |

Step 1 put scenario R at 646 min. The completeness check (G1, section 8) found that S6's 290 gave round 1 the oversized
26-agent Windows round-2 panel, so S6 and S7 were re-derived on the skill's panel shape; the 22 % saving and the ranking
are unchanged. Targets need more than D1: the light-panel trial for S6, and fewer or shorter rounds for S7.

Decide on the private page, https://claude.ai/artifact/4gUHUtoGXFAq2spU6xzfL8: accept, reject or defer each of the 31
proposals, 9 shape grafts and 2 trials, with a note. Choices save to the page's store (collection `decisions`, one row
per id).

## 2. Where the time goes

**Scenario R**, the reference every saving is measured against: an asphalt-class material with a bundled research sheet;
a core graph of about 600 nodes and a detail graph of about 120 (asphalt: 610 and 117); 5 + 9 presets, each with a
nowear render (28 renders per full 2K export); one first build to green 1K checks; three review and apply rounds, each
ending with a full 2K export and suite; a session split at each round boundary. Detail: `$OUT/results/1_reference_scenario.md`.

| stage | today | how it was built | what dominates |
|---|---|---|---|
| S0-S3 | 52 | asphalt first build 29b1b020 (`mac-tx`): model 53.9 of 91 min, 346k output tokens (53 % thinking); research agent 25.8 min | model turns; main idle 8.8 min under research. The spec draft already overlapped research (real S0-S3 ~42 min, `mac-tx`), so 52 overstates by ~10 |
| S4 | 45 | same build: lane 16.0 + check-fix 9.1 + detail 2.8 model min, 11.2 min of Designer jobs | 17 responses of 5k+ tokens took 28.9 of 53.9 model min; Designer jobs napped |
| S5 | 17 | `win`: 52 renders 2.4 min; `run_all.sh` 13.5-14.2 min serial | the serial suite |
| S6 | ~230 | brick 3afca382 panels 28.4/46.5/48.7 min (`mac-tx`) × chain factor 1.3-1.85 + brief 6-25 min a round (`win`) | lens → verifier chains at xhigh; main idle 120.7 of 222.6 min on brick |
| S7 | ~190 | `win` R1 apply 115 min (10 items, 2 graphs, an 18.6 min stall, 896k context) + brick decay (`mac-tx`) | one build-measure cycle per fix; suite waits |
| S8 | 37 | resume 7.3 min (`win`) + CONTEXT_PROMPT est 5, ×3 | split on the critical path |

What the Mac costs behind S4, S5 and S7 (all `mac-loaded`; "napped" is the normal state while a session works in another
window, "held" is with the job holding an `NSProcessInfo` activity, "fixed" adds the non-recursive lookup):

| item | napped (today) | held | fixed |
|---|---|---|---|
| lane rebuild, stages 02-06 | 392 s (run B), 672 s (run A) | est 110-130 s | est 6-10 s |
| stages 05+06 + 1K export (v0 + nowear) | 139-264 s | 16.8-18.7 s | 5.7-5.8 s |
| graph lookup per sdkit op | 67-166 ms | 12-14 ms | 0.1 ms |
| one 1K render | 8-19 s | 2.7 s | same |
| full 2K export, 28 renders | est 7-20 min | est 1.5 min | same |
| calibration cycle | 28-72 s | 4.5-8.5 s | same |
| first `search_library` / package load | 20.3 s / 10.3 s | 3.3 s / 2.0 s | same |

These hidden Mac costs are not in the S5/S7 "today" column, which borrows Windows durations, so DZ-01 and DZ-02 save
more on this Mac than scenario R shows.

## 3. Experiments

Designer runs used copies only (`$OUT/probe/asphalt_speedprobe.sbs`, tools copied to `$OUT/probe/tools`), one call at a
time, on Designer 12.4.1 running main's plugin. Offline runs used `$SKPY` on extracted trees. The 1-minute load never
fell below about 3 (WindowServer, VS Code, mediaanalysisd, NordVPN), so **every timing here is `mac-loaded`**; there are
no quiet-machine (`mac`) numbers. The App Nap and lookup A/B pairs ran back to back under the same load, so their ratios
stand; absolute seconds need a quiet re-time when the fixes are built (each top-10 `verify_after` says which). Raw job
JSONs: `$OUT/results/raw/`; every row: `$OUT/results/timings.jsonl`.

| id | question | method | n | result: median (range) | tree |
|---|---|---|---|---|---|
| E1 | per-request overhead | `s.call` loop in one `$VPY` process; separate `tool_call.py --raw ping` processes | 40; 5 | ping 25.0 ms (6.2-31.9) = `POLL_MS`; info 25.2 ms; one process per call 493 ms (468-537), of which import 0.42 s | main |
| E2 | where the lane rebuild goes; why runs differ 5× | stages 02-06 + 2K probe + 1K export, per-step timers and cProfile, run twice, then with a non-recursive `_graphs_in` prototype | 1 per run | run A 744 s total (cold-ish, load 8-10); run B 432 s, stages 392 s, of which `C._graph` lookups 342 s (**87 %**, 4,492 calls at 67-166 ms); run C (B + prototype) stages 73.1 s (**5.4×**) | main (+prototype) |
| E2b | the 5× spread (found while running E2) | the same job (stages 05+06 + export v0/nowear 1K) with Designer frontmost, in the background, and in the background holding an `NSProcessInfo` activity (`probe/tools/build/nap.py`); `ps -o pri` sampled | 1-2 each | active 18.7 s vs background 139.4 s (**7.5×**, PRI 4); held 18.2 s (PRI 46) vs not held 264.4 s (**14.5×**); held + prototype lookup 5.75 s (5.72-5.78, n=2); Graph view open or closed: no effect | main (+prototype) |
| E3 | hidden main-thread work after a job | `ping` × 15 right after a 1K export, probe graph closed, then open | 15 + 15 | 24.1 ms (9.9-31.4) closed, 24.4 ms (7.1-27.3) open: none. The earlier "open is faster" reading was App Nap | main |
| E4 | `sk.lib` cost | first instance of 10 new library packages; second instance; repeats of one | 10 each | first 332 ms (185-632); second 18 ms (9-24); repeat 12.7 ms (7.9-22.4) | main |
| E5 | `_graph()` lookup cost | `getChildrenResources(True)` vs `(False)` on 3 packages; `C._graph` with 1 and 3 loaded | 5-10 | recursive 77 ms at 728 nodes, 12 ms at 351, 0.8 ms at 28; non-recursive 0.02 ms, same 2 graphs found; `C._graph` 3 packages 101 ms (57-395) | main |
| E6 | undo-group cost | 200 nodes via `C.cmd_create_node` vs the `sd` API, with and without one undo group per node | 1 | API 0.168 s, with groups 0.241 s (~0.37 ms per group); `C.cmd_*` 1.51 s (napped, slow lookups; 0.86-0.95 ms per node held after the fix, E2b D7) | main |
| E7 | export split | compute vs write, 1K/2K, all 27 outputs vs the 7 the checks read, preset vs nowear, activity held | 1-2 | 1K: 2.24 s compute + 0.42 write; 2K after a size change 4.94 + 1.54; 2K same size 1.56 + 1.51; 2K only-7 1.26 + 0.81; nowear 1.56 + 1.49. Designer caches unchanged nodes | main |
| E8 | sdcall pickup | a no-op job × 5 foreground; background completions vs the main loop | 5; 4 | foreground 0.091 s (0.076-0.102); background delivered 0.9-13 s after exit, at the next tool boundary (`win`: 31 s median is model time, not the job) | main |
| E9 | cold vs warm | first `search_library` and package load in a fresh process, napped (04:43) and after a user restart, held (05:38) | 1-3 | napped cold: search 20.3 s, load 10.3 s; held cold: 3.3 s and 2.0 s, first compute 2.04 vs 1.94 s warm. No real cold penalty when not napped | main |
| E10 | `save_package` | MCP calls with `graph=` | 5 | 0.1-0.5 s per save (0.21-1.32 incl. queueing) | main |
| E11 | preview path | MCP `render_preview` of the lane (27 outputs at 2K) | 3 | 3.7-19.2 s, napped and partly queued; an sdkit 1K export is 2.7 s held. Each preview also adds ~10k+ tokens of images to the context | main |
| E12 | one calibration cycle | probe 2 nodes at 2K, `calibrate.py`, drive one Position, re-export 1K | 2 + 2 | held: probe 1.2-4.9 s, calibrate 0.57 s (0.56-0.81, n=3), export 2.65 s; not held: probe 21-44 s, export 7-27 s | main; calibrate pub |
| O1 | matcheck per check | cProfile + per-check timer, classic 2K and lane_v2 1K | 1 | classic 58 checks 6.79 s (import 0.57; edge_profile 1.85, value_range 1.3); slowest single check 0.77 s; lane 37 checks 1.82 s | pub |
| O2 | previews | per-variant time and `shadow_vis` share | 1 | lane 1K 1.63 s, classic 2K 3.78 s; shadows 2.5-11 % | pub |
| O3 | wrong_builds | synthetic 6-case set (3 hard checks × rustic/weathered, 2K) | 3 | 3.56 s (3.56-3.57): 0.59 s per case; `Swap` flush 0.008 s (re-derivation is the cost) | main |
| O4 | process overhead | bare python, `$SKPY` imports, `setup_env.sh` | 3 each | 0.03 s; 0.20 s (0.19-0.32); 0.24 s | pub |
| O5 | worker count | 12 matcheck jobs, 2 threads each, `xargs -P` | 1 per P | P1 70.2 s, P2 37.0 (1.9×), P4 20.7 (3.4×), P6 15.2 (**4.6×**); 5.85 s per 2K job serial | pub |

E2's two runs and E2b explain the brief's open question: the same Mac stage scripts ran 77.4 s and then 15.5 s on
Oct 3 (`mac-tx`) because Designer was napped for one and active for the other, and the recursive lookup multiplies
whatever priority Designer has. On Windows (`win`: lane 02-06 about 19 s) neither applies as strongly.

## 4. The recommended workflow

D1, "lean current shape": same stages, same three gates, same panel shape (lenses, verifiers, lead, three rounds), each
stage with its best verified fixes. Both judges picked it (8/10 each; realistic ~507 on the old baseline, ~445 on the
re-derived one). Drafts and scores: `$OUT/results/3_D{1,2,3}.md`, `3_design.json`, `3_synthesis.md`.

```
S0 orient (read SKILL.md only) ── S1 interview ◆gate ── S2 research ── S3 spec ◆gate
   └ read stage docs while the user answers          ├ 2-3 gap agents in parallel
                                                     └ main drafts the spec skeleton and check configs
S4 build graph 1 ──── build graph 2 ──── S5 full 2K export (activity held) ── suite, 6 workers x 2 threads
     └ 1K checks of graph 1 run here         └ in the background: ledger skeleton, REFERENCE.md, BRIEF delta
Round k:  S6 panel (Workflow; lens → verifier per lens, pipelined; xhigh; no suite or numpy beside it)
             ├ old session: CONTEXT_PROMPT at lens launch, then only waits for the panel
             └ new session: resumes, drafts fixes from per-lens files (never run in Designer before the plan)
          ◆plan gate (every design call asked here) ── S7 apply: one Designer batch per graph
             └ graph k's targeted checks + wrong builds + nowear run while graph k+1 builds (≤ 4 workers)
          final 2K export ── full suite in the background ── round report drafted, finalized only on rc 0 + green JSON gate fields
```

**Gates kept:** S1 interview and S3 spec approval unchanged; the plan gate before every round's fixes, now held in the new
session (XS-02) and carrying every design call (RV-02), so nothing stops mid-apply.

**Quality floor kept:** verifiers keep their own method and run at xhigh, and a boxed verifier's unchecked high or medium
finding goes to one re-verify agent (SH-01); every hard check still fails its named wrong build, in every round-closing
suite and in every per-fix targeted set (MS-01, SH-04); the nowear render stays in every export; a full suite runs after
the last change, gated on exit codes and JSON gate fields (MS-01, SH-05); one Designer caller (only the new session after
a split; SH-03 says who owns Designer and the CPU in each phase); research before the spec (RS-01 shortens S2, S3 still
waits for it).

**Grafts from the runners-up** (SH-01 to SH-09 on the page; no minutes counted except SH-02's ~1.5): the verifier-box
guard, ask-then-read, a phase ownership table, wrong builds and nowear in per-fix sets, the report drafted under the final
suite, a scripted fixcheck of every ledger acceptance number, a catch ledger as the rigor format, no suite during the
panel, and a 1 h test list for the assumptions nothing here measured.

**Trials, no minutes claimed until measured:** TR-01, the light panel (D3): a judge map in the spec, CG-tell rows as
default checks with wrong builds, a check-audit lens, all lenses kept for the trial round; worth ~90-150 min of S6 if it
works (est). TR-02, longest-chain-first lens launch with a streaming lead. ML-01's effort tiers roll out as an A/B on the
next material (high on one graph, xhigh on the other), with a stop rule: back to xhigh if first-1K hard passes drop, fix
cycles rise, or wrong builds or evals regress.

**Dropped from the shape, with the reason:** XS-03 (same idle window as RS-01, builds before the spec gate, and its build
minutes shrink under DZ-01/02); MS-03/DZ-04 (RV-01's calibrate-once rule and DZ-02's 4.5-8.5 s cycle take most of it);
MS-04 (RV-01's per-graph sets cover it; its hash-skip needs export determinism, unverified); MS-05 (~0.3-1.2 min once
MS-01 runs in parallel); MS-02's foreground rule (conflicts with XS-01's background suite; its numbers go into DZ-03's doc
pass); ML-02 (splits are forced anyway at 645-896k context; XS-02 hides the resume); ML-04's pack (its decision batch is
RV-02); ML-06/RS-03 (0.5-0.7 min/h, copies the sheet's hard checks); ML-05 and ML-03 (1.3 and 3 min/h; ML-05 waits on the
sdkit merge, ML-03 saves 0 for R); RV-06 (same tail as RV-03; a shared kit bug would hit lens and verifier alike); the
panel's effort tiers from PB-10 (the panel stays at xhigh); RS-04 (0 min for a bundled sheet).

**Effort and order** (est ~25 h: D1 20.75 + grafts ~4 + GAP-1 0.5): DZ-01 and DZ-02 first, because every Designer-bound
saving assumes them; then one SKILL.md doc pass for RV-01, RV-02, ML-01, DZ-03 and MS-02's numbers (~2.5 h, auto-merges
on pub and main); RS-01; RV-03 with SH-01 and GAP-1, then RV-05 and RV-04; XS-01 and XS-02; MS-01 last, after the
main/pub merge, because `wrong_builds.py` exists only on main.

**Landing notes, pub vs main.** DZ-01: the same code in both (`getChildrenResources(True)` at pub `commands.py`:205 and :1073, main
:197 and :1031); build on pub. DZ-02 lands in `bridge.py`, which differs: pub rewrote `_poll`/`_service`/`_handle` (modal
check, `MSG_NOSIGNAL`, idle timeouts, `MAX_LINES_PER_POLL`), so the activity wraps pub's `_handle` (:263-281) and main
(:199-211) needs a hand cherry-pick. Pub's anyio lock adds ~0.1 ms per MCP call (G3, `mac-loaded`), so main's timings
carry over. DZ-03 lands after pub (SRV-03's "not accepting connections" text), or caps status polls at 6 per job: on
main, longer foreground waits plus polling can fill `listen(8)` and print "may have crashed" (brick reached ~7 queued
connections, `mac-tx`). MS-01 needs pub's matcheck exit codes (`b1f07e0`: 1 with NaN, 3 unmeasured) and main's
`wrong_builds.py`; on main alone a runner that gates on rc passes errored or vacuous hard checks (main `matcheck.py`:1628).
RV-03 rewrites `review_round.js` (pub changes only :99). The SKILL.md doc edits auto-merge. The `sdkit.py` merge conflict
(main `_fn_extra` vs pub `_check_spec`) blocks ML-05 only, and must keep KIT-02's heavy-noise guards in `P()` and
`drive()` (pub `sdkit.py`:389, :1056).

**Why the runners-up lost.** D2, overlap first (judges 7 and 6; realistic 508-512 on the old basis for ~25.5 h): the same
time as D1 for ~4.5 h more work; it bends two gates (Designer builds the skeleton before spec approval, research starts
before interview round 2); its one-caller safety relies on the unlanded sdcall `.running` lock; its streaming lead,
hash-skip and verifier effort tiers are unnamed trades. D3, numbers first with a light panel (judges 5 and 5; realistic
450-465 for ~38 h, likely 45+): S6 290 → 145 rests on an unvetted light panel plus RV-06 stacked on RV-03 (the same tail),
S8 double counts ML-02 with XS-02, and it drops the process lens (brick R1 damage F2/F4 first-form tells), the tiling
lens (win R2 pothole_wall echo) and the cross-lens redundancy round 2 kept (4 multi-lens clusters). Its best parts are
grafted above or offered as TR-01.

## 5. Proposals, ranked by minutes saved per hour of work

Savings are minutes per scenario-R material after the skeptics' corrections, on step 2's basis (S6 290, S7 205); on the
re-derived baseline, S6-only items scale by about 0.8 and S7 items by about 0.93. They overlap, so they are never added;
the stage table in section 1 counts each minute once. "Trade-off" means the proposal gives up some rigor; its cost is
below (top 10) or in `proposals.json` and on the page. All 31, with every field: `$OUT/results/proposals.json`.

| # | id | proposal | stages | kind | saves (min) | effort (h) | min/h | skeptic | shape | trade-off |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RV-01 | Apply in one build-measure batch per graph, calibrate once per graph | S7 | doc rule | 8-30 | 0.5 | 38 | overstated | yes | **yes** |
| 2 | RV-03 | Panel runner: Workflow route, time boxes, cap 6, `unverified` status | S6 | code | 20-50 | 2 | 17.5 | overstated | yes | **yes** |
| 3 | RV-02 | Ask every design call at the plan gate | S6 S7 | doc rule | 0-15 | 0.5 | 15 | dup of ML-04 | yes | - |
| 4 | DZ-01 | Non-recursive graph lookup in the bridge | S4 S7 | code | 6-15 | 1 | 10.5 | holds | yes | - |
| 5 | XS-03 | Build the package skeleton while research runs | S2 S3 S4 | process | 3-7 | 0.5 | 10 | holds | - | - |
| 6 | DZ-02 | Hold an App Nap activity around every bridge command | S4 S5 S7 | code | 8-30 | 2 | 9.5 | holds | yes | - |
| 7 | RV-04 | Main works the panel window: ledger, notes, fix drafts | S6 S7 S8 | process | 4-15 | 1 | 9.5 | overstated | yes | **yes** |
| 8 | MS-01 | Parallel suite runner for this Mac (6 x 2 threads) | S5 S7 | code | 24-40 | 3.5 | 9.1 | holds | yes | - |
| 9 | XS-02 | Split sessions at panel launch, resume under the panel | S6 S7 S8 | process | 5-22 | 1.5 | 9 | overstated | yes | - |
| 10 | ML-01 | Tiered effort: high for scripted stages, xhigh for S3 and S6 | S4 S5 S7 S8 | doc rule | 3-12 | 1 | 7.5 | overstated | yes | **yes** |
| 11 | XS-01 | Round-closing suite in the background, named overlap work | S5 S6 S7 S8 | doc rule | 3-10 | 1 | 6.5 | overstated | yes | - |
| 12 | RS-01 | Bundled-sheet research as 2-3 parallel gap agents | S2 S3 | process | 6-10 | 1.5 | 5.3 | holds | yes | - |
| 13 | RV-05 | Persistent REFERENCE.md + script-made delta brief | S6 | structure | 10-22 | 3 | 5.3 | overstated | yes | **yes** |
| 14 | XS-04 | Draft the next fixes under the panel | S6 S7 | process | 3-12 | 1.5 | 5 | dup of RV-04 | - | **yes** |
| 15 | ML-02 | STATE.md checkpoint + state digest; split only when forced | S7 S8 | structure | 5-15 | 2.5 | 4 | overstated | - | **yes** |
| 16 | ML-03 | Move probed engine facts into sd_craft | S4 S7 | doc rule | 0-3 | 0.5 | 3 | overstated | - | - |
| 17 | DZ-03 | Re-time Designer doc rules (foreground sdcall to ~8 min) | S4 S5 S7 | doc rule | 0.5-3 | 0.75 | 2.3 | overstated | yes | - |
| 18 | DZ-04 | One-job Histogram Scan calibration | S4 S7 | code | 2-8 | 2.5 | 2 | dup of MS-03 | - | - |
| 19 | ML-04 | Decisions at the plan gate + generated apply pack | S7 | process | 2-8 | 2.5 | 2 | overstated | - | **yes** |
| 20 | MS-02 | Re-time checks.md numbers | S5 S7 | doc rule | 0-1 | 0.25 | 2 | overstated | - | - |
| 21 | MS-03 | One-command recalibration (`calibrate.py --spec`) | S4 S7 | code | 2-8 | 2.5 | 2 | overstated | - | - |
| 22 | RV-06 | Generic review toolkit in the skill | S6 | code | 3-12 | 4 | 1.9 | overstated | - | **yes** |
| 23 | MS-04 | Measure tiers: per-fix targeted jobs, full suite per round | S7 | structure | 1-4 | 1.5 | 1.7 | overstated | - | - |
| 24 | ML-05 | Ship a build skeleton (env, stage template, wrappers) | S4 S7 | code | 1-3 | 1.5 | 1.3 | overstated | - | - |
| 25 | ML-07 | Read less: section-scoped reads, a checks schema card | S0 S2 S3 | doc rule | 0.5-2 | 1 | 1.2 | dup of RS-02 | yes | **yes** |
| 26 | RS-02 | Index-first reading of sheets and stage docs | S0 S1 S2 S3 | doc rule | 0.3-1.5 | 0.75 | 1.2 | dup of ML-07 | - | **yes** |
| 27 | MS-05 | wrong_builds: keep real-derived caches across swaps | S5 S7 | code | 0.3-1.2 | 0.75 | 1 | overstated | - | - |
| 28 | ML-06 | Generate spec skeleton and check configs from the sheet | S3 | code | 0.5-3 | 2.5 | 0.7 | dup of RS-03 | - | **yes** |
| 29 | RS-03 | Spec and checks scaffold from sheet + interview | S3 | code | 0.5-3 | 3.5 | 0.5 | dup of ML-06 | - | - |
| 30 | RS-04 | Split the researcher by area (no-sheet materials) | S2 | code | 0-0 | 1.5 | 0 | holds | - | - |
| 31 | GAP-1 | Stamp per-agent and per-round times into round results | S6 S7 | code | 0-0 | 0.5 | 0 | unverified | - | - |

XS-03 (#5) holds but is not in the shape: it competes with RS-01 for the same idle research window and builds before the
spec gate. RV-02 duplicates ML-04's decision batch; the shape takes RV-02's form and drops ML-04's pack. GAP-1 saves
nothing itself but makes S6 and S7 measurable on the next round (section 8, G2).

### The top 10 in the recommended shape

**RV-01. Apply in one build-measure batch per graph, calibrate once per graph.** S7, doc rule, 0.5 h, 8-30 min (critical
path), medium; skeptic: overstated (finder 15-45). Keeps SB-A, SB-D, SB-G.
- Today: SKILL.md:119-120 (pub = main) says "apply the plan ... re-measure" and nothing about cycles. Windows round 1 ran
  one cycle per fix: 115 min for 10 items on 2 graphs (`win`); brick batched, 25.9/15.9/7.1 min a round (`mac-tx`).
- Evidence: ~8 cycles saved per R × 1.5-4 min each after DZ-01/02 and MS-01 (`est`); calibration loops 7.2, 3.5 and
  12.7 min (`win`). Overlaps RV-04, MS-03, MS-04, ML-01. The SKILL.md edit auto-merges.
- Rigor: per-fix attribution blurs; the ledger once found only 2 of 10 and 1 of 8 brick fixes had landed (`review.md`:14-18).
  Kept by SH-06's fixcheck, SH-04's per-fix wrong builds and the final full suite. Signal: "partial" or "not landed"
  counts next round. Verify: cycles and minutes per apply against 115 min / 10 items.

**RV-03. Panel runner: Workflow route by default, time boxes, cap 6, an explicit `unverified` status.** S6, code, 2 h,
20-50 min (critical path), medium; skeptic: overstated (finder 25-70). Keeps PB-3, PB-9, M6; replaces PB-5-7, M5.
- Today: SKILL.md:114-116 and `review.md`:171-178 use the Workflow only on opt-in; `review_round.js` (pub; main differs at
  :99) sets no box, cap or effort (:104-124, :143-149) and counts a finding without a verdict as rejected (:138-139).
- Evidence: brick panels 28.4/46.5/48.7 min, 29 agents at xhigh, 52 % thinking (`mac-tx`); boxes of 15 min per lens and 12
  per verifier simulate r2 46.5 → 35.2, r3 48.5 → 39.4 min (`est`); win R2 lens 26, verifier 32, lead 28 min.
- Rigor: a boxed verifier may skip a high or medium; verifiers changed 11 of 35 severities (`win`) and 10 of 25 (brick)
  and corrected overstated numbers (oil 2.5× → 1.5-1.8×). Kept by SH-01 and xhigh. Signal: a `not_checked` high or medium
  that reaches the plan. Verify: re-run brick's round-2 panel from files against its 46.5 min and severity changes.

**RV-02. Ask every design call at the plan gate.** S6-S7, doc rule + a `design_calls` field in the lead's PLAN
(`review_round.js`:72-93), 0.5 h, 0-15 min, medium; skeptic: duplicate of ML-04's batch. One mid-apply AskUserQuestion
blocked 18.6 min (`win`). Rigor: none. Verify: 0 AskUserQuestion calls during apply.

**DZ-01. Non-recursive graph lookup in the bridge.** S4, S7, code, 1 h, 6-15 min (critical path), high; skeptic: holds.
- Today: `_graphs_in` calls `pkg.getChildrenResources(True)` (pub `commands.py`:205, main :197), a walk over every node,
  on every `C.cmd_*` with a `graph` key and every sdkit op; again at pub :1073 (main :1031).
- Change: `getChildrenResources(False)` plus a stack walk of `SDResourceFolder.getChildren(False)` (prototype
  `$OUT/probe/tools/build/prof_e2.py`:14-25); no handle cache.
- Evidence: 77 ms at 728 nodes vs 0.02 ms, same graphs (E5); 87 % of run B; run C 392 → 73 s; held 12.0 → 0.85 s (E2,
  E2b). Overlaps DZ-02 (multiplicative: 14-38 min together, never add). Rigor: none. Verify: patched plugin, prof_e2
  napped ≤ 80 s and held ≤ 10 s; a graph in nested folders is still found.

**DZ-02. Hold an App Nap activity around every bridge command.** S4, S5, S7, code, 2 h, 8-30 min (critical path), high;
skeptic: holds.
- Today: `bridge._handle` (pub :263-281, main :199-211) runs `_dispatch` with no power assertion; a hidden Designer sits
  at scheduler priority 4.
- Change: `activity.py` from `$OUT/probe/tools/build/nap.py` (ctypes `beginActivityWithOptions:reason:`,
  UserInitiatedAllowingIdleSystemSleep | LatencyCritical), begun before `_dispatch` and ended in `finally`; macOS only,
  fail-open, `SD_CLAUDE_BRIDGE_NO_ACTIVITY=1` turns it off. Per command, so `search_library` and previews gain too.
- Evidence: 18.7 s active vs 139.4 s hidden (7.5×); held 18.2 s at PRI 46 vs 264.4 s (14.5×); first `search_library`
  20.3 → 3.3 s; calibration cycle 28-72 → 4.5-8.5 s (E2b, E9, E12). Rigor: none. Verify: the D3/D5 job hidden ≤ 20 s;
  a hidden full 2K export (est 1.5 min); a Windows no-op smoke test.

**RV-04. The main session works the panel window.** S6-S8, process, 1 h, 4-15 min (critical path), medium; skeptic:
overstated (finder 10-30). Needs RV-03's per-lens files. Replaces SB-B and SB-H's bookkeeping subagent.
- Today: `review.md`:179-180 says "prepare the next fixes" without naming the work; brick's main made 3 calls in 36 s,
  then idled 120.7 of 222.6 min (`mac-tx`). Change: ledger records, hand-off notes and fix drafts as lens files land.
- Rigor: drafts from unverified lens files can carry overstated numbers or wrong premises (~18 brick fixes were rewritten
  by verifiers, `review.md`:129). Kept: drafts never run in Designer before the plan and take the verifier's fix.

**MS-01. A suite runner sized for this Mac.** S5, S7, code, 3.5 h, 24-40 min (critical path), high; skeptic: holds.
Supersedes tooling S2, S4 and speed brief C.
- Today: no runner (pub SKILL.md:97-101 lists the scripts as manual steps); each script is one serial process
  (`matcheck.py` pub:1687, `previews.py` pub:695, `wrong_builds.py` main:228-258).
- Change: `scripts/suite.py`, a stdlib pool of subprocesses, `min(6, CPUs-2)` workers × 2 BLAS threads, outputs deleted
  before each job, one job per config, wrong-build config, cross group and graph's previews; gate on exit codes.
- Evidence: P6 = 4.6× (O5); 0.59 s per wrong-build case (O3); R's suite ~11.8 → ~2.6-3.2 min, 4 suites per R (`est`).
  Lands after the main/pub merge. Rigor: none (keeps R6 per config). Verify: `--jobs 1` and `6` give identical
  scorecards; a real R suite ≤ 3.5 min; `SUITE_JOBS=3` beside a panel.

**XS-02. Split the session at panel launch and resume under the panel.** S6-S8, process, 1.5 h, 5-22 min (critical
path), medium; skeptic: overstated (finder 10-31). Moves M7's split point.
- Today: CONTEXT_PROMPT comes at the end of stage 7 (pub SKILL.md:118-126, main :116-124) and round 2 splits after the
  gate, so a prompt (est 5 min) and a resume (7.3 min, `win`) sit on the path three times.
- Change: write CONTEXT_PROMPT at lens launch; the user opens the next session at once; the old one only waits; the plan
  gate is held in the new one. Needs the user at lens launch; whether a Workflow outlives its session is untested.
  Rigor: none. Verify: lead.json → first apply call ≤ 3 min.

**ML-01. Tiered effort.** S4, S5, S7, S8, doc rule, 1 h, 3-12 min (critical path), low; skeptic: overstated.
- Today: every main-session record of both Mac builds runs at xhigh. Change: high for stage scripting, check-fix, S5, fix
  scripting and S8; xhigh for S3 and the panel; switch at the spec and plan gates; roll out as an A/B.
- Evidence: model time ~9.9 s per 1k output tokens; thinking 53 % (asphalt) and 45 % (brick) at xhigh vs 23-24 % at
  high (`mac-tx`, confounded by task); the spec dry runs at high passed 30/30.
- Rigor: less reasoning in scripted turns; no past catch is tied to xhigh. Stop rule in section 4.

**XS-01. Run the round-closing suite in the background and name the overlap work.** S5-S8, doc rule, 1 h, 3-10 min,
medium; skeptic: overstated (most of its finder range goes to MS-01).
- Today: SKILL.md:96-105 and `review.md`:9-20 run export → matcheck → previews → ledger → BRIEF serially. Change: start
  the suite after each round-closing export; meanwhile write ledger records, the BRIEF delta and REFERENCE.md; launch
  lenses only on a green suite. Evidence: background completions arrive 0.9-13 s after exit (E8); win session 2 spent
  24 of 52 min in foreground suite waits. Rigor: none. Verify: the export → lens-launch gap.

## 6. The round-2 plan, re-ranked

None of the round-2 tooling items has landed on main; of the implementation spec only M0 is done and M1 partly (status per
item: `$OUT/2026-10-04_scout/plan_status.md`). Planned effort was ~30-37 h plus 2-2.5 h of build order. Each item is now
kept, changed, superseded by a proposal here, or dropped:

| item | decision | reason |
|---|---|---|
| Tooling G1 (gate in the scorecard, exit 3, `--lenient`) | change | land pub `b1f07e0`'s exit codes (1 with NaN, 3 unmeasured); MS-01 deletes outputs and gates on rc, so `card['gate']` and `--lenient` add no speed |
| G2 strict JSON, G3 UTF-8 | keep | interop and Windows friction; no Mac speed effect |
| S1 row-blocked `shadow_vis` | drop for R | shadows are 2.5-11 % of previews here (O2), ≤ 10 s a suite; keep only for fine-mm decal materials |
| S2 `suite.py`, S4 `--threads`, speed brief C | superseded by MS-01 | Mac defaults (6 × 2 threads, 4.6×), per-config wrong builds, thread caps set per child |
| S3 sdcall foreground, `.running` lock, exit 4/5 | change | keep the lock and exit codes on top of pub `d880e95` (one-caller safety); START/DONE markers matter less once DZ-03 makes background jobs rare |
| S5 `only` honesty | keep, off the speed path | a rigor item (a stale read raises); land it on pub's rewritten export block (`93064c4`) |
| N1-N4 non-tiling path; R1-R3; D1, D2 | keep | capability and robustness; 0 min for R. Put D1 and N4 under their own `checks.md` headings so section reads find them |
| D3 previews `--tag`/`--no-compare` | change | drop `--tag` (one previews job per graph); its re-timing goes into DZ-03's doc pass with MS-02's numbers |
| PB-1 review kit, M3 | change | generic rows would be RV-06 (not in the shape, 1.9 min/h); asphalt rows stay in the tools folder |
| PB-2 brief, PB-4 cross-lens redundancy | keep, via RV-05 | script-made delta brief (win: 4 agents, 19 min on R2's critical path) and a lens ownership table (4 multi-lens clusters, win) |
| PB-3 time boxes | keep for the panel only (RV-03) | not for research: fetches after 900 s gave the PAVER pothole walls and AAPTP roller-checking data the build used |
| PB-5 verify high/medium only | change, via RV-03 + SH-01 | needs the `unverified` status first (`review_round.js`:138-139); brick skipped 0 verifier runs, so it saves ~0 |
| PB-6 CPU budget | change | 8 CPUs: panel cap `min(6, CPUs-2)` with no suite beside it (SH-08); ≤ 4 suite workers beside Designer (SH-03) |
| PB-7 merge, M5 `merge_panel.py` | change / defer | keep the JS merge on the Workflow route, no merge agent; `merge_panel.py` + tests (3-4 h) deferred |
| PB-8 early fixcheck and brief | superseded | RV-05's delta brief takes seconds; fixcheck kept as SH-06 |
| PB-9 Workflow for the panel, M6 | keep, via RV-03 | M6 scoped to boxes, cap, `unverified`, `design_calls`, per-lens files (~2 h) |
| PB-10 effort tiers | change, via ML-01 | tiers apply to the main loop; the panel and verifiers stay at xhigh |
| M2 decal composite, M4 hooks | drop from this plan | asphalt material work, not in R |
| M7 prompts, CONTEXT_PROMPT | change, via XS-02 | the split moves to panel launch; the generic template moves to the skill; material prompts stay |
| M8 integration run | change | keep the full-suite integration run (quality floor); drop the composite-cache timing with M2 |
| SB-A one batch per graph, SB-D targeted sets, SB-G calibrate once | keep, via RV-01 | SB-D needs `wrong_builds.py --tag` (main only) |
| SB-B check rows in a subagent during the lane batch | keep, generalized in RV-04 | re-verify wrong builds on the final exports |
| SB-E foreground waits | change, via DZ-03 and XS-01 | Mac background pickup is 0.9-13 s (E8), not 31 s (win); XS-01 names the overlap work |
| SB-F preset subsets, 1K cue | keep | the value is in check time and turns; the Designer part is small after DZ-02 |
| SB-H digest, checkpoint, bookkeeping | change, via XS-02 and RV-04 | idle main writes the notes under the panel; ML-02's digest is not in the shape |
| SB-I export only the maps the checks read | drop | ~1 s per 2K render (E7: only-7 1.26 + 0.81 s vs 1.56 + 1.51), stale-map risk |
| build order 1 (apply pack, ledger skeleton) | change | decisions move to the plan gate (RV-02); ledger and drafts are RV-04's |
| Speed brief summary "Designer is not the bottleneck" | change | true on Windows; on the Mac only after DZ-01 + DZ-02 |

## 7. Rejected, so nobody proposes them again

| idea | why not (source) |
|---|---|
| Cache the graph handle; smarter partial rebuilds | after DZ-01 `C._graph` is 0.09 ms a call, and a full 02-06 rebuild is est 6-10 s; a stale handle risks wrong-graph edits |
| Optimize `deleteNode`, `C.cmd_*`, `_blend_notes`, undo groups, `sk.lib` loads; drop per-stage save and lint | App Nap artifacts or small: 0.7-1 ms per node held, lint 0.10 s and save 0.034 s a stage, 0.37 ms per undo group, 12-18 ms per `sk.lib` after first use (E2b D7, E4, E6) |
| Smaller `render_preview` | a size change forces a full recompute (E7: 4.94 vs 1.56 s) |
| Activity for the plugin's whole life; `NSAppSleepDisabled`; activity only in `run_python` | battery cost all day with no gain over per-command; the default needs a restart and is untested; `run_python`-only misses `search_library` (20-64 s napped) |
| 1K inner-loop measuring | a 1K pass is not evidence; saves 0.4 s export and 4 s matcheck per config |
| Decoded-map `.npy` cache; one process for several configs; trimming Python start-up | decode is 11 % of a matcheck run (O1; settled on Windows); start-up 0.20-0.24 s (O4), ~15 s a suite |
| Dedupe wrong-build cases across presets; selective cache flush | unknown R6 cost; a reused real-derived region could make a wrong build fail falsely and hide an R6 miss |
| Hard time box on research | late fetches gave the PAVER, roller-checking and PASER data the build used (29b1b020) |
| Research during the interview; merge the two rounds; auto-generated spec gate summary | 3 of 8 answers deviated from the recommended option; round 2 cost 79 s of user time (AskUserQuestion takes 4 questions); the spec gate took 3.4 min, 1.1 of it the user's (`mac-tx`) |
| Pipeline the Agent route; verify high/medium only to save time; shrink BRIEF at brick scale | barrier 0.6-1.3 min a brick round; 0 of 13 brick verifier runs would be skipped; 116 lines over 3 rounds (`mac-tx`) |
| Tell agents where the venv Python is | already fixed: `review_round.js`:24 and :99 pass `PY` |
| A cheap fixcheck-only round 3 | brick r3's realism lens still found 1 high and 2 new mediums |
| Lower effort for pre-gate long thinking | 9.4 of 19.1 long-think min ran under the research agent, off the critical path |
| Read less to make turns faster | context adds ~1 s a turn (1.9 s below 200k, 3.0-3.2 s at 200-700k); kept only as ML-07's small reading saving |
| Cheaper subagent for prose; trimming panel hand-backs; limiting kept thinking | 3.7 model min at hand-off with nothing to overlap; 2-3 s each while main idles; not controllable from the skill |
| Research before the interview | the research prompt is built from the answers (29b1b020 L131) |
| Lane lenses before the detail graph; early lenses from previews; per-graph plan gates | splits the lead's input; a later hard fail voids them; loses lane-vs-detail findings |
| D2 as the shape; D3 as the shape | section 4 |

## 8. Not covered

The completeness critic named five gaps (`$OUT/results/4_completeness.json`); two were closed in part by gap finders.

- **G1, partly closed:** S6 and S7 had no single panel shape. Re-derived (section 1). Still open: Windows round 1's panel
  timeline and lens count (on Windows only), and the asphalt-vs-brick chain factor (1.3-1.85, `est`). Settle both by
  timing the next real round with GAP-1's stamps.
- **G2, open (needs a real round):** no asphalt-class panel or apply has run on this Mac, and none with DZ-01/DZ-02. The
  S6/S7 targets and the value of RV-01, RV-03, RV-05, XS-01 and XS-02 rest on brick (`mac-tx`, before the skill existed)
  and Windows numbers. Experiment: the next Mac round with the Designer fixes in, per-stage times logged.
- **G3, closed for minutes:** the code review's speed items change no proposal (0 re-issued mutations after a timeout in
  either build, `mac-tx`). Open: why main answered `designer_status` in 15-18 s during brick's 600 s `run_python`
  (contradicts the offline SRV-02 repro), whether SRV-05's preview cap would have avoided the Windows 896k peak, and
  whether timed-out polls stay in the accept queue on macOS (the SRV-03 near miss).
- **G4, needs pub installed live:** DZ-01 and DZ-02 are measured on main only. The code paths are the same on pub (G3),
  but switching the live install to pub needs your yes. Experiment: pub with both patches, re-run E2b and E5.
- **G5, needs a quiet Designer run:** every timing is `mac-loaded` (load 3-10). Re-run E2b (napped, held, fixed) and O5
  (P1-P6) three times each at load below 1 before relying on the absolute seconds behind DZ-02 and MS-01.
- Also unmeasured: a napped full 28-render 2K export (est 7-20 min); the Mac parallel speedup of `wrong_builds` and
  previews (only matcheck was run in O5); whether a mid-session `/effort` change applies (ML-01); whether a Workflow
  outlives its session (XS-02); a Windows analogue of App Nap (EcoQoS for unfocused processes; Windows was already fast);
  the light-panel trial (TR-01); the token cost of reading exported PNGs into context (brick: 30 images, 11.1 MB base64,
  `mac-tx`), a possible lever on split counts that no proposal takes.

## 9. DECISIONS

2026-10-04. The user took the recommendation for every item. Eight page choices that differed were set back to the
recommendation at the user's request in chat, and eight undecided items were filled the same way. The page's store
(collection `decisions`, 42 rows) holds the final state.

| decision | items |
|---|---|
| accept (14 proposals in the shape) | DZ-01, DZ-02, DZ-03, MS-01, RS-01, ML-07, ML-01 (as an A/B with the stop rule), RV-01, RV-02, RV-03, RV-04, RV-05, XS-01, XS-02 |
| accept (completeness) | GAP-1 |
| accept (grafts) | SH-01 to SH-09 |
| accept as a trial | TR-01, the light panel: one trial round with all lenses kept; no minutes claimed until measured |
| defer | TR-02 (no minutes counted, and a streaming lead can split cross-lens clusters; revisit after a timed round) |
| reject | XS-03, XS-04 (duplicate of RV-04), DZ-04, MS-02 (its numbers go into DZ-03), MS-03, MS-04, MS-05, ML-02, ML-03, ML-04, ML-05, ML-06, RS-02 (duplicate of ML-07), RS-03, RS-04, RV-06 |

## 10. Implementation plan

About 25 h (est), in dependency order. Build in a worktree, never by switching branches in the live checkout. Each
milestone ends with the timing that proves it, run on a quiet machine (load below 1, n ≥ 3, median and range). Hand-off
for the building session: `speed_rework_impl_context.md` (untracked, repo root).

| # | milestone | items | files | tests | proof (today → target) |
|---|---|---|---|---|---|
| M0 | Land pub on main (the user's call, outside this plan) | prerequisite | merge `code-review-fixes-public`; `sdkit.py` conflict: keep main's `_fn_extra`, pub's `_check_spec` and KIT-02's guards in `P()`/`drive()` | pub's own checks; `P(noise_bnw_spots_3, {'scale': 120})` raises; one live sdkit stage | live install = the code under review. Without M0, M1 is cherry-picked to main by hand and M7 waits |
| M1 | Designer fixes, ~3 h | DZ-01, DZ-02 | `designer_plugin/sd_claude_bridge/commands.py` (`_graphs_in`, the :1073 site), new `activity.py`, `bridge.py` `_handle` | scratch package: graphs at top level, in a folder and a nested folder are listed and found, `create_graph` refuses a duplicate id; activity is a no-op off macOS, fails open, `SD_CLAUDE_BRIDGE_NO_ACTIVITY=1` turns it off; `ps -o pri` 46 during a job, 4 after | hidden D3/D5 job 139-264 s → ≤ 20 s; lane 02-06 hidden 392 s → ≤ 10 s; first `search_library` hidden after a restart 20.3 → ≤ 4 s; hidden 28-render 2K export ≈ 1.5 min; re-time E2b and O5 quietly (G5) |
| M2 | One doc pass, ~4 h (after M1's numbers) | RV-01, RV-02 (rule), ML-01, DZ-03, ML-07, SH-02, SH-03, SH-04, SH-05, SH-07, SH-08 | `SKILL.md` (stage table with an effort column, apply and gate rules), `references/sd_craft.md`, `checks.md` (schema card, re-timed numbers), `review.md`, `research.md` (section-scoped sheet reads) | the 3 iteration-1 evals stay 30/30 with the skill; every Designer timing in the docs matches M1's re-time | next first build: doc-read tokens and minutes below asphalt's 83k and 2.3 min (`mac-tx`); 0 AskUserQuestion calls during an apply; 0 client timeouts |
| M3 | Parallel research, ~1.5 h | RS-01 | `references/research.md` section A, `SKILL.md`:55-57 | replay 29b1b020's research prompt as 1 agent and as 3: coverage of `web_findings.md` (35 sources) unchanged | research wall 25.8 → ≤ 18 min; main idle under research 8.8 → ~0 |
| M4 | Panel runner, ~3.5 h | RV-03, RV-02 (`design_calls` field), SH-01, GAP-1, per-lens files for RV-04 | `assets/workflows/review_round.js`, `review.md`:171-178, `SKILL.md`:114-116 | replay brick's round-2 panel from files (no Designer): no finding without a verdict counted as rejected; every high/medium in a `not_checked` list re-verified. Workflow scripts can't call `Date.now()`, so for GAP-1 each agent writes its own start and end (`date -u`) into its per-lens file | replay critical path 46.5 → ~35 min (the RV-03 simulation); severity changes still found (brick 10 of 25) |
| M5 | Brief and panel-window work, ~4 h | RV-05, RV-04 | `REFERENCE.md` template, `scripts/make_brief.py` (delta brief + lens ownership table), `review.md` | `make_brief.py` on brick's review files; drafts never touch Designer before the plan gate | brief 19 min (win) → ≤ 1 min; per-agent brief lines well below round 2's 1,779 (win) |
| M6 | Overlap and split, ~4 h | XS-01, XS-02, SH-09 | `SKILL.md` stages 6-7, `assets/context_prompt_template.md` | SH-09's test list: a Workflow keeps running while a second session works the same tools folder; the activity holds in background sdcall jobs; Mac parallel speedup of `wrong_builds` and previews | lead.json → first apply call (today ~12 min on the path) → ≤ 3 min; export → lens launch ≈ suite time |
| M7 | Suite runner and fixcheck, ~5 h (after M0) | MS-01, SH-06 | `scripts/suite.py` + `SUITE.json` schema, `scripts/fixcheck.py`, `checks.md` | `--jobs 1` and `--jobs 6` give identical scorecards and `wrong_builds.json` (minus seconds); two injected failures are named with rc ≠ 0; an errored or vacuous hard check fails (rc 1 or 3) | R suite ~11.8 min serial → ≤ 3.5 min at 6 workers; `SUITE_JOBS=3` beside a panel |
| M8 | First material on the new workflow | TR-01, ML-01 A/B, GAP-1 timings | the material's own tools folder | the quality floor in section 4, unchanged | each stage against section 1's targets; re-set S6/S7 targets from GAP-1's stamps; keep or drop the light panel from the trial round's comparison |
