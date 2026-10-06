# Process brief: speeding up the reviewer round (from round 2, 2026-10-03/04)

Round 2 took about 2 h from the user's prompt to the gate. The panel's output was good: verifiers cut 8 lens "highs" to 3,
downgraded 9 findings and rejected 2 of 35. The time went into repeated work, not into the review. This brief lists what
happened, why, and what to change for round 3 (`prompts/5_review_round3.md`) and in the skill's review stage.

## 1. What happened (measured from file times and agent usage)

| stage | agents | wall time | longest agent | subagent tokens |
|---|---|---|---|---|
| Preflight + reading (main session) | 0 | ~6 min | – | – |
| Brief: 4 writers (A, B, C1 + ledger, C2) | 4 | 23:26 → 23:45, 19 min | B (scale/architecture/files): 18.9 min, 132 tool calls | 1.32 M |
| Lenses | 8 | 23:46 → 00:25, 39 min | g5_tiling: 39.1 min, 79 calls; others 18-27 min | 2.75 M |
| Verifiers (pipelined, 5 lenses split a/b) | 13 (1 stopped) | 00:05 → 00:44 | g1_requirements_verify_a: 31.7 min | ~3.8 M |
| Wait for the stopped regressions verifier | – | ~5 min | – | – |
| Lead | 1 | 00:49 → 01:17, 28 min | – | 0.59 M |
| **Total** | **26** | **~2 h** | | **~8.4 M** |

Critical path: preflight 6 → brief 19 → g1 lens 26 → g1 verifier a 32 → wait 5 → lead 28 ≈ **116 min**. The g5 chain
(39 + 16 min) finished earlier and wasn't on it.

Other measurements:
- 222 helper scripts were written; 35 of them replay or copy `composite_decal.py`. The INV-16 / rim-band composite was
  rebuilt by at least five agents (g1, g1 verifier a, decal_patches verifier a, decal_potholes verifier a, the
  regressions verifier).
- Every agent decoded the same 16-bit 2K PNGs itself, but measured afterwards that is cheap: 0.04-0.16 s per map
  through `matcheck.Ctx`, about 1 s per config (a `.npy` reload is ~0.02 s). Decoding is not where the time went.
- The composite is expensive: `composite_decal.py` takes 92 s for its 4 sites (12-29 s each: bicubic resampling of the
  lane to 0.488 mm/px, the detail blend, low-pass, shading and PNG writes). One verifier's variant replay of it ran
  679 s, because every variant rebuilt the whole site.
- Every agent read the full round-2 brief: 1,282 new lines on top of round 1's 497, plus spec §13 and sheet cards for
  the decal lenses.
- At peak, 12 agents ran numpy/OpenCV at default thread counts on 32 logical CPUs: 73 % load, about 10 analysis
  processes. The user asked mid-round to leave threads free; the cap was then sent to each agent.
- Four issue clusters were found by 2-4 lenses each and then verified 2-4 times: the decal rim band (3 lenses), the
  INV-16 height reference (2), the `pothole_wall` echo (3), Q2 over P0 (4).
- The lead read 20 JSON files, re-measured three numbers, generated a 69 KB `review_result.json` and a 416-line
  `findings.md`. Its write of `findings.md` was blocked, so the text came back as a 54 KB hand-back into the main session.
- The main session received 26 hand-back messages; each one costs a turn and context.

## 2. Causes, ranked by minutes lost

1. **Shared work redone per agent:** composite rebuilds (92 s a run, 679 s for one variant replay), and measurement
   code written from scratch (222 scripts). Most of an agent's 15-30 min is model turns spent writing, running and
   debugging those scripts (40-130 tool calls per agent), not CPU time.
2. **The brief was rebuilt from scratch** by four agents (19 min on the critical path), and most of it (architecture,
   presets, files, cheat sheet, physics digest) didn't change since round 1.
3. **No time box.** Agents explored until satisfied: g5 39 min, the INV-16 verifier 32 min, the lead 28 min.
4. **Overlapping lens scopes.** Builder hypotheses and the user's questions were handed to several lenses, so the same
   issue was measured and verified repeatedly.
5. **CPU contention.** Too many concurrent agents at default thread counts, then a cap mid-run that slowed the tail.
6. **The lead did mechanical work** (merging verdicts, generating JSON) that `review_round.js` already does in code, and
   then hit a blocked write.

## 3. Changes, in order of value

| # | change | saves (est.) | where |
|---|---|---|---|
| 1 | **Cache the composite and ship a review toolkit.** Split `composite_decal.py` into `build_site()` (resample, blend: run once, save each site's layer stack as `.npz`) and `compose()` / `inv16()` (seconds), with the variants agents rebuilt as options: opacity profile (ring / AA-only / narrow band), reference height (worn G40 / as-built + rut / nowear), lane swap, decal on decal; images only on request. Add `checks/review_kit.py` with the measurements agents re-wrote: rim bands by inside/outside distance, sub-pixel outline and curvature, edge AA width and colour step, symmetrised lateral profiles, per-stone tables, crack wall / fill masks, shift and shuffle controls, each with a self-test. Verifiers keep their own method; the kit is shared infrastructure like `matcheck`. | composite variants ~11 min → ~20 s; fewer tool calls per agent | `composite_decal.py` refactor, new `checks/review_kit.py`, run by `run_all.sh` |
| 2 | **Keep a persistent `review/REFERENCE.md`** (architecture, presets, files + loader, cheat sheet, physics digest, invariants with check ids). The builder updates it at the end of each apply session. Each round adds only a **delta brief of ≤ 250 lines**: rules, decisions, scorecard deltas, ledger, keep-as-is / rejected / deferred, rubric, schema, lens roster. Lenses read the delta plus only their REFERENCE sections. | ~15-19 min off the critical path; 30-40 % fewer tokens per agent | skill `references/review.md` §2; `prompts/4_apply_round2.md` hand-off step |
| 3 | **Time-box every agent in its prompt**: lens ≤ 35 tool calls / ~15 min, verifier ≤ 25 / ~12 min, lead ≤ 30 / ~15 min; stop at the finding cap; report what was not checked. | 15-20 min of tail | lens/verifier/lead prompts |
| 4 | **One owner per hypothesis.** Round 3 runs 5 lenses (fixcheck, regressions + G1, realism lane + on-foot, G5, decals). Each builder hypothesis, open question and known cluster is assigned to exactly one lens; others skip it. | 2-4 fewer verifier runs; a simpler lead | delta brief §15 |
| 5 | **Verify high and medium findings only**, by cluster. Lows go to the lead as unverified, and it spot-checks one. Keep pipelining (a lens's verifier starts as soon as it finishes). | ~3-4 verifier runs | verifier prompts |
| 6 | **CPU budget from the start**: the 2-thread cap (`OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS=2`, `cv2.setNumThreads(2)`, one Python process per agent) goes in the brief's rules; no more than 8 agents at once; no split verifiers unless a lens has 5 or more high/medium findings. | user's machine stays responsive; less contention | delta brief §1; prompts |
| 7 | **Merge in code, judge in the lead.** A script merges lens + verifier JSON into confirmed / rejected / fix_status (the logic in `review_round.js`). The lead gets the merged file and writes only the plan, design calls and OVERALL as JSON; a script renders `findings.md` from it, run in the main session. This avoids the blocked write and the 54 KB hand-back. | ~10-15 min; no blocked write | new `review/render_findings.py`; lead prompt |
| 8 | **Start independent lenses early.** fixcheck and G5 need only the rules, the files section and the ledger; launch them as soon as the ledger is updated, while the delta brief is written. | ~5-10 min | round-3 prompt |
| 9 | **Use the Workflow tool for the panel when workflows are enabled** (`review_round.js`: pipeline per lens, a concurrency cap, resumable, results to files, no per-agent hand-back turns in the main session). The round-2 prompt said "Agent tool"; with ultracode on, the workflow is the faster route. | fewer main-session turns; resume after interruptions | `prompts/5_review_round3.md` decision line |
| 10 | **Tier the effort.** Mechanical agents (fixcheck's re-measurement, regressions' number diff, any brief assembly) can run at lower effort or on a faster model; realism lenses, verifiers of high findings and the lead stay on the strongest model. | some minutes per mechanical agent | agent options |

## 4. Round-3 runbook (target about 55-65 min instead of ~120)

| min | step |
|---|---|
| 0-8 | Preflight (scorecards newer than exports, previews present). Build the composite site cache in the background (~90 s). Update the ledger with the round-2 plan items. |
| 5-12 | Launch fixcheck and G5 (they need only rules, files and the ledger). Write the ≤ 250-line delta brief from a template. |
| 12-30 | The three other lenses, time-boxed at ~15 min, reading the cache. |
| 20-45 | Verifiers, pipelined, high/medium only, one per lens, ~12 min each. |
| 45-60 | Merge script, then the lead (plan + design calls as JSON, ~15 min), then `render_findings.py` in the main session. |
| 60+ | Gate: scorecard, plan, design calls. |

## 5. Keep

- **Adversarial verification.** It changed severities on 11 of 35 findings and caught overstated numbers: the rim
  frame was a −12.7 luma median but a −6 to −9 area mean, and the oil "2.5× cliff" was 1.5-1.8×. Don't drop it to save
  time; scope it.
- **Pipelining** each lens into its verifier: the verifier stage overlapped the lens stage by about 20 min.
- **The preflight identity check** (graph XML vs the backup taken at export) settled stale-export doubts in one script.
- **A progress file** (`review/round2/_progress.md`) so an interrupted round can resume.

## 6. Open points for the user

- Whether round 3 should switch the panel from the Agent tool to the Workflow tool (change 9).
- Whether to add `review_kit.py`, the composite cache and `render_findings.py` to the skill (bridge repo) or keep them in this material's
  `checks/`. Either way, no bridge-repo commit without asking.
- The concurrency ceiling that leaves this machine usable (8 agents at 2 threads is the proposal).
