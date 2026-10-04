# Tooling brief: measurement and Designer scripts (from the asphalt decal measurement, 2026-10-03/04)

The two round-2 documents beside this one cover the reviewer process: `review_round2_process_brief.md` and
`review_round2_implementation_spec.md` (review kit, composite cache, merge/render scripts, `review_round.js`, time
boxes). This brief covers what they leave out: the skill's measurement and Designer tooling, as exercised by the asphalt
material's session 2. That session measured a non-tiling decal graph, built its checks, wrong builds and composites, and
then profiled the suite. Every claim below was checked against the code at `d6fbde2` by four read-only investigators,
with file:line references. SK = `skills/sd-material-research`; T = the asphalt tools folder.

## 1. What happened

- **The gate passed things it should not have.** matcheck counts a hard check as failed only when `passed is False`.
  These hard checks are not failures:
  - an errored hard check (`passed: null` with an error);
  - a vacuous one (key set below `min_px`);
  - a NaN one (a value on a non-empty set; `evaluate` returns None, with no note at all).

  matcheck exits 0 for all three (SK/scripts/matcheck.py:1590, :1628; NaN :1453-1454, :1552-1559). On a config error
  it returns 2 before writing a scorecard (:1581-1583), so a caller reading the scorecard sees the previous run's
  pass. Line 3 of the scorecard, which callers grep, says "Hard failures: none" in every one of these cases (:1604).
  The asphalt suite had to add `T/checks/scorecard_gate.py`. Its first version still missed the NaN case, which this
  investigation found (fixed in T on 2026-10-04). Reachable NaN cases include `run_length` with no runs (:646-664),
  `spacing`, `seam` with no z values, `normal_valid` with ≤ 10 sloped px, and `dispersion`.
- **Decals don't fit a tool built for tiles.** All morphology, labelling, filtering and sweeping wraps across the
  border (matcheck.py:166-341, :785-788, :1170-1184, :1257-1307), and `references/checks.md:16` says so. There is no
  border region. The asphalt decal configs had to approximate "opacity 0 at the decal border" with two checks: a
  `components` `border_px` margin and a `value_range` beyond the 20 mm rim band (T/checks/gen_checks.py decal section).
  previews.py always writes the tiled 3×3 and 4×4 sheets and pads by wrapping (previews.py:555-561, :63, :170).
- **Parameters in pixels change meaning with resolution.** About 15 config keys are in px:
  - lengths: `border_px`, `window_px`, `exclude_px`, `half_width_px`, the previews `center_px`;
  - counts: `min_px`, `element_min_px`, `block_min_px`, `bin_min_px`, …

  At 1K a length doubles in mm and a count covers 4× the area (matcheck.py:703-707, :1180, :1193, :1558, …). 1K
  agreed with 2K on 183/183 decal verdicts without rescaling the px parameters, and on 37/37 (P1, Q1) with
  rescaling. That was an all-pass build, so it shows nothing about catching a failure (T/review/round2/speed_brief.md).
- **Shadows dominate preview time.** `previews.shadow_vis` builds full-frame float32 temporaries at every march step
  (previews.py:156-185), so it is memory-bandwidth bound. A row-blocked version with the same arithmetic gave:
  - 626/626 PNGs pixel-identical;
  - all 1,050 suite PNGs byte-identical between serial and 8-worker runs;
  - shadows 4-6× faster;
  - about 55 s off the asphalt suite (208 → 152 s at 12 workers)

  (T/ops/parallel_suite_prototype/shadow_bench.py, logs/).
- **The suite is serial and hand-built per material.** The asphalt suite is 65 independent jobs: 786 s serial, 208 s
  at 12 workers, 158 s at 8 workers once shadows are row-blocked (S1). Each material writes its own `run_all.sh` with the same step, exit-code and gate logic
  (T/checks/run_all.sh); the skill has no runner (SKILL.md:98).
- **Designer jobs.** The docs say to run sdcall "from a background shell" (SKILL.md:86-87, references/sd_craft.md:21-22).
  Over 29 jobs, background pickup was 31 s median against 2 s in the foreground.
  - A killed or timed-out sdcall does not stop its Designer job: it runs to completion and later calls queue behind it
    (sdcall.py:40-51; designer_plugin/sd_claude_bridge/bridge.py:143-156, :189-197).
  - The empty-reply path crashes with a JSONDecodeError (sdcall.py:44-54).
  - `only` in `export_outputs` skips file writes, not compute (sdkit.py:826-830). The asphalt nowear renders write 24
    lane maps, of which the checks read 7.
- **Dropdowns and presets.** `sdkit.expose(options=)` writes `label_<i>` annotations (sdkit.py:420-452). In Designer
  12.4.1 on Windows the saved .sbs holds `0;0;0`, so the material carries its own post-save XML writer for dropdowns
  and `<sbspresets>` (T/build/presets.py). sd_craft.md doesn't mention it, nor the registry-merge trap or the empty
  first compute after new node types (both in T/CONTEXT_PROMPT.md).
- **Windows friction.** matcheck, previews and sdcall open files with the locale encoding (matcheck.py:1577, :1601,
  :1623; previews.py:467, :673; sdcall.py:28). On cp1252 the scorecard .md comes out cp1252, a non-cp1252 character
  in a `why` crashes the .md write after the JSON is written, and sdcall crashes printing Designer's stdout.
  - Probes that read 16-bit RGBA with raw `cv2.imread` get BGRA order.
  - Windows Python can't open `/c/...` paths.
  - T/ops/main_loop/probe_io.py fixes these in one place, which removed about 7 of session 2's 15 friction events.

## 2. Changes, in order of value

Verdicts and exit codes stay the same for existing configs, except G1's exit 3, which only appears where a hard
check has no verdict. Rows marked **(output changes)** change files or console output by default; the rest are
opt-in or byte-identical.

| # | change | where | test | effort |
|---|---|---|---|---|
| **G1** | **Gate in the scorecard.** `card["gate"] = {pass, hard_failed, hard_errored, hard_vacuous, hard_nan, n_hard}`; pass only if all lists are empty and n_hard > 0. A NaN on a non-empty set gets note `nan: no measurable value`. The .md gets a `Gate: PASS/FAIL (reasons)` line before the existing summary, which keeps its wording. Exit 3 when nothing hard failed but the gate fails; `--lenient` restores exit 0. On a config error, write a failing scorecard before returning 2. | matcheck.py `main`, `run_check`, `evaluate` (isnan for np.float32 too); checks.md:12, :96 | fixtures: empty-region hard check → 3; unknown type → 3; NaN `run_length` → 3; a missing `tile_m` overwrites a seeded passing scorecard; an all-pass config → 0 with the same verdicts; the JSON gains `gate` and the .md the Gate line **(output changes)** | 70 min |
| G2 | Strict JSON: non-finite floats → null plus `value_repr` "nan"/"inf", so `jq` and JS readers parse it **(output changes: NaN/Infinity tokens become null)** | matcheck.py:1601 | `json.loads(..., parse_constant=raise)` on a NaN fixture | 20 min |
| G3 | UTF-8 everywhere: `encoding="utf-8"` on matcheck.py:1509, :1577, :1601, :1623, previews.py:467, :673 and sdcall.py:28, :30, :56; `stdout.reconfigure(errors="backslashreplace")` **(output changes: .md bytes on cp1252 machines)** | matcheck.py, previews.py, sdcall.py | a `why` of "≤ Δ" under cp1252 writes both files; sdcall prints "−" | 25 min |
| **S1** | **Row-blocked `shadow_vis`** (32-row bands, taps precomputed, in-place subtract; signature unchanged) | previews.py:156-185 | keep the old loop as `_shadow_vis_ref` in a test; square and non-square fields, mmx ≠ mmy, fractional light steps; assert `array_equal` | 25 min |
| **S2** | **`scripts/suite.py SUITE.json [--jobs N] [--timeout S]`** (stdlib): jobs with commands, timeouts and outputs to delete first; a thread pool (default 1 = serial); thread caps when N > 1; matcheck configs gated with G1's `gate` (or the T gate's rules); one line per job; exit 1/2. Material-specific steps stay jobs in the material's SUITE.json. | new | fakes: a job exiting 3, one past its timeout, errors, vacuous, NaN, a missing scorecard, a stale scorecard whose matcheck dies: each fails, the clean set passes; serial vs N-worker outputs byte-identical | 2 h |
| S3 | sdcall: run in the **foreground** when under ~3 min (docs). Print `sdcall START`/`sdcall DONE rc=` marker lines, keeping the existing "ok in X s" line as it is. Add a `<out>.running` lock so a timed-out job can't be re-sent while Designer still runs it (exit 4, `--force`). Exit 5 on a closed connection with no reply. **(output changes: marker lines, lock file, exit 4/5)** | SKILL.md:86-87, sd_craft.md:21-22, sdcall.py | a fake bridge (socketserver): reply → START/DONE rc 0; never replies → rc 3 and the lock stays; resend → 4; closes → 5 | 1 h |
| S4 | `--threads N` on previews.py and matcheck.py (sets OMP/OPENBLAS/MKL/NUMEXPR/VECLIB before numpy, `cv2.setNumThreads`); default unset. Measured: 6 concurrent composites took 55-73 s each against 28-34 s alone. | previews.py, matcheck.py | the env inside the process; output hashes equal with and without | 30 min |
| S5 | `only` honesty: the manifest records `only`; matcheck raises when a config reads a map the last export skipped (instead of reading a stale file); `matcheck.py --maps-used` lists the maps each render needs. Document that `only` saves writes (~45 % of a render), not compute. **(output changes: manifest key; a stale read now raises)** | sdkit.py:826-830, matcheck.py `Render.map`, sd_craft.md §2 | a full export, then `only=["height"]`; a config reading basecolor must raise | 1-1.5 h |
| **N1** | **`scale.tiling: false`** for non-tiling materials (default true). Pads without wrap in erode, dilate and the EDT; `label_wrap(wrap=(False, False))` (the parameter exists, no caller passes it); nearest/edge modes in the filters; sweeps stop at the edge; `seam` raises. Add a region spec `{"border_mm": X}` (px within X mm of the tile border). | matcheck.py helpers + Ctx | two blobs touching the left and right edges: 1 component with tiling, 2 without; a dilation at the top edge must not appear at the bottom; `border_mm` replaces the asphalt margin proxy with equal verdicts | 1.5 h |
| N2 | Previews honour `scale.tiling: false` / `previews.tiling`: no tiled sheets, edge padding in resize and shadows | previews.py:555-561, :63, :170 | an edge square on a non-tiling fixture doesn't bleed to the far edge; no `tiled*` files | 1 h |
| N3 | mm and mm² forms of the px keys (`border_mm`, `window_mm` forced odd, `exclude_mm`, `half_width_mm`, `min_mm2`, `element_min_mm2`, …), converted with ctx.mm and recorded in details; the px keys still work; giving both raises | matcheck.py Ctx `length_px`/`count_px` | a disk 30 mm from the border at 2048 and 1024: same verdict with `border_mm`, different with `border_px` | 1 h |
| N4 | checks.md "Non-tiling materials (decals, overlays)": no seam check; the rim-band and beyond-rim recipes; opacity core / border / margin hard checks; sizes on the rendered opening; nowear for a decal ("a hole not yet opened"); wrong builds (a smooth 30° bowl, a hole in the opacity core, a 60 mm rim band, an outline off the tile); and the halo lesson (a soft rim painted as plain surface makes halos on sealant, a dark frame in the wheel paths, a crack-free collar). method.md:126 and SKILL.md:77 get "tiling is hard, unless the material is a decal". | references/checks.md (~177), method.md, SKILL.md | a fresh agent given only the skill writes a pothole-decal spec with these checks and no seam check | 45 min |
| R1 | `scripts/sbsfix.py` (`--check`, `--dropdowns`, `--presets`), generalised from T/build/presets.py; `expose(options=)` also records the options in the registry; `sk.dropdown_spec()`. sd_craft.md gets the save → unload → sbsfix → reload rule. **(output changes: registry.json gains `dropdowns`)** | new; sdkit.py:420-452; sd_craft.md:43 | text fixtures: a `0;0;0` dropdown fails `--check`, is fixed by `--dropdowns`, then passes; byte round-trip | 1.5-2 h |
| R2 | sd_craft.md "Don't" bullets: the dropdown/presets reset, the registry merge (`sk.save_registry()` before the next stage), retry the first compute after new node types | references/sd_craft.md | docs | 15 min |
| R3 | `render_variant` restores only non-None old values (as `temp_size` does) **(behaviour change, the point of it)** | sdkit.py:940-955 | a mock owner that returns None | 15 min |
| D1 | checks.md lessons: measure deposit shares against a geometric floor, not `height > t` (heaps rise above any threshold; asphalt debris read about half); sizes from the rendered opening; px parameters and 1K dry runs (a 1K pass is a cue to export, not evidence); a suite judges the scorecard JSON (G1) | references/checks.md tips, :96 | docs | 25 min |
| D2 | `scripts/probe.py` (generic probe_io: `winpath`, `load` = matcheck's loader, `luma`, `scorecard`, `ctx`); setup_env.sh prints "Windows: export PYTHONUTF8=1" on stderr (its stdout stays the path) | new; setup_env.sh | 16-bit RGBA: raw cv2 vs probe.load channel order; a `/c/` path opens | 40 min |
| D3 | Previews `--tag` (tagged `compare_*` and `views_index` names) and `--no-compare`. Document "one previews job per group": `views_index.md` is rewritten even by a single-config run (previews.py:648-663, :714). Re-time checks.md:231 after S1. | previews.py, checks.md | two parallel tagged runs into one folder keep both indexes | 45 min |

## 3. Order of work

1. **G1-G3** (about 2 h). The gate can't pass a build that measured nothing, and Windows output is UTF-8. After G1,
   the asphalt `scorecard_gate.py` can read `card["gate"]`; keep it until then.
2. **S1, S4, S2** (about 3 h). Shadows first: one function, bit-identical, and every suite and composite gains. Then
   the runner with thread caps. Validate S2 on the asphalt suite: serial vs 8 workers byte-identical, two injected
   failures caught (the method used for T/checks/run_all.sh on 2026-10-04: a fake `PY` replaying saved outputs, 17 s).
3. **N1-N4** (about 4.5 h). The non-tiling path, then switch the asphalt decal configs to `scale.tiling: false` and
   `border_mm`, and compare verdicts with today's proxies.
4. **S3, S5, R1-R3** (about 4 h). Designer-side robustness; R1 needs no Designer for its tests.
5. **D1-D3** (about 2 h). The docs and the probe helper.

Total about 15-16 h. Each step ends with the asphalt full suite unchanged: PASS, 26 configs, 581 wrong-build cases.
Since the skill is linked into the checkout, check what the asphalt sessions are running before landing changes
mid-round.

## 4. Relation to the implementation spec

- No file conflicts. The spec edits the review workflow, `review.md` and SKILL.md's review section; adds SK/merge_panel.py,
  SK/render_findings.py and SK/tests/test_review_pipeline.py; and edits T scripts and T/CONTEXT_PROMPT.md (R2 quotes the
  latter). This brief edits matcheck, previews, sdkit, sdcall, `checks.md`, `sd_craft.md`, `method.md` and SKILL.md's
  measure/Designer lines.
- S1 is transparent to the spec's composite split (§3: `pv.shadow_vis`, same signature) and speeds up its cache build.
- S4 complements the spec's decision 9 (thread caps in `review_kit.py` and `composite_decal.py` only).
- G1's `gate` gives the lead, the delta brief's scorecard section and a suite's gate a field to read. The spec's
  merge and render scripts read the panel and lead JSON, not matcheck scorecards.
- If both land, the spec's `run_all.sh` changes (M2/M3: the review_kit self-test, the composite cache line, counting
  `rim_drop_1p5mm` like `inv16_ok`) become jobs in a SUITE.json for S2.

## 5. Keep

- Byte-identical defaults: tiling true, px keys, exit 0/1/2 for configs whose hard checks all have verdicts, no thread
  caps unless asked.
- One Designer call at a time. S3's lock enforces it, and nothing here calls Designer in parallel.
- matcheck reads rendered maps and wrong builds stay per material: the runner gates, it does not judge physics.

## 6. Decisions (user, 2026-10-04)

1. **G1's default:** exit 3 for errored, vacuous or NaN hard checks **by default**, with `--lenient` to get the old
   exit 0. A hard check without a verdict is not a pass, and callers that test `== 1` keep working.
2. **The suite runner lives in the skill** as `scripts/suite.py` (S2). Materials keep only their SUITE.json and their
   material-specific steps. The asphalt `checks/run_all.sh` and `scorecard_gate.py` stay until it lands, then move onto
   it.
3. **`sbsfix.py` now** (R1), together with the R2 docs. The asphalt `build/presets.py` can switch to it once its output
   matches byte for byte.
4. This brief is committed. The code changes are committed only after a yes for each change. The asphalt-side fixes
   are already in T, which is not in git: `checks/scorecard_gate.py`, the `run_all.sh` gate, `ops/`.
