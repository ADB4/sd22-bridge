# Review round speed-ups: implementation spec

Assembled 2026-10-04 from the four section drafts T/review/round2/_spec/A.md-D.md, checked against each other and
against the code. Where this file and a draft disagree, this file wins (§0.4 lists every such call). Sources:
REPO/review_round2_process_brief.md ("the brief", in git since eb484d1) and T/review/round2/review_result.json (the
round-2 lead's plan, "the plan").

| name | Windows | macOS |
|---|---|---|
| T | `C:\Users\andy\Documents\Allegorithmic\Substance Designer\asphalt_materials_tools` | `~/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools` |
| REPO | `C:\Users\andy\dev\sd-claude-bridge` | the bridge checkout |
| S | REPO/skills/sd-material-research (linked as `~/.claude/skills/sd-material-research`) | same |
| SK | S/scripts | same |
| PY | `/c/Users/andy/.cache/sd-material-research/venv/Scripts/python.exe` (Git Bash) | `PY=$(bash ~/.claude/skills/sd-material-research/scripts/setup_env.sh)` |
| `<a>` | T/review/agents/round2 (the round-2 agents' scripts, the prior art) | same |

Line numbers: REPO as of eb484d1; T as of 2026-10-04 (T/composite_decal.py has 617 lines). T is not a git repo.

## 0. Purpose, scope, and relation to the brief and the plan

Round 2 took about 2 h. The brief (§2) traces the time to repeated work: composite rebuilds (92 s a run, 679 s for one
variant replay), 222 helper scripts, a brief rebuilt by four agents, no time boxes, overlapping lens scopes, CPU
contention, and a lead that merged verdicts by hand and then hit a blocked write. This spec turns the brief's changes
into code, file edits and tests that can be built and reviewed on macOS from the bridge repo (main) and a copy of T.

### 0.1 Brief change -> where it is implemented

| # | brief change (§3) | here |
|---|---|---|
| 1 | composite cache (`build_site` once, `compose` in seconds) and `checks/review_kit.py` | §3, §4 |
| 2 | persistent `review/REFERENCE.md` plus a delta brief of at most 250 lines | §6.1 (a, b), §6.5, §6.6 |
| 3 | time boxes: lens 35 calls / 15 min, verifier 25 / 12, lead 30 / 15; report what was not checked | §6.1 (f), §6.2 (`BOX`, `not_checked`), §6.7 |
| 4 | one owner per hypothesis; five round-3 lenses | §6.1 (c), §6.7 |
| 5 | verify high and medium findings only; lows go to the lead unverified, it spot-checks one | §5 (`unverified`), §6.1 (d), §6.2 |
| 6 | CPU budget: 2 threads, one Python process per agent, at most 8 agents | §3.2, §4.0, §6.1 (f), §6.2 (`COMMON`, `run`) |
| 7 | merge in code, the lead writes judgement as JSON, a script renders findings.md | §5, §6.2 |
| 8 | start fixcheck and G5 early | §6.1 (c), §6.2 (`early`, `brief_task`), §6.7 |
| 9 | Workflow tool when workflows are enabled | §6.1 (f), §6.3, §6.7 |
| 10 | tiered effort | §6.2 (`effort`; the merge agent runs at `low`), §6.7 |

### 0.2 Relation to the plan

The plan (fixes P1-P8, design calls Q1-Q7) is material work for session 4 (T/prompts/4_apply_round2.md). This spec
builds the tools that work and round 3 measure with. The kit implements the measurement behind each plan row (§4.2),
and the composite exposes the P1(a) terms (§3.4, plan `fixes[0].change` (a), `acceptance[5..7]`). The new check rows
in decal_extra.py, accept_r1.py, wrong_builds.py and gen_checks.py, the graph changes, and switching composite_decal's
`--options` default from `r2` to `p1` belong to the plan items and are written in session 4. Nothing here adds a metric
or a fix the plan or the brief does not define.

### 0.3 Scope

In:
- T/composite_decal.py split into build / cache / compose / render, with the variant options and the P1(a) hooks; the
  same split without a cache in T/composite.py; frozen legacy copies and T/checks/test_composite_decal.py (§3).
- T/checks/review_kit.py with `--selftest`, and three lines in T/checks/run_all.sh (§4).
- SK/merge_panel.py, SK/render_findings.py, SK/tests/test_review_pipeline.py (§5).
- S/assets/workflows/review_round.js, S/references/review.md, S/SKILL.md (§6.1-§6.4).
- T/review/REFERENCE.md, T/prompts/4_apply_round2.md, 5_review_round3.md, 6_apply_round3.md, T/CONTEXT_PROMPT.md
  (§6.5-§6.8).
- macOS setup (§2).

Out:
- Plan rows P1-P8 as check rows in the callers, and the graph work (session 4).
- Kit functions for the rows in §9 item 7 (no prior art in reach); their owners write them in the caller first.
- Any Designer call. Nothing here needs Designer, except an optional re-export on the Mac (§2.3).
- Rendering round 2's own findings.md (§9 item 10).

### 0.4 Cross-section decisions (where the drafts disagreed)

| # | point | drafts | this spec | why |
|---|---|---|---|---|
| 1 | cache flag | A `--build-only`; D `--build-cache` | `--build-only` | A owns the CLI. `--out` stays required (composite_decal.py:567), so the preflight is `"$PY" composite_decal.py --out review/round<N>/decal/composite --build-only`, and the cache lands in review/round<N>/cache. |
| 2 | merge / render scripts | C: `SK/merge_panel.py --round-dir DIR`, `SK/render_findings.py --round-dir DIR`; D: `T/review/merge_round.py <N>`, `T/review/render_findings.py <N>` | C | They read only the schemas that review_round.js owns and contain nothing material-specific, and the workflow (in REPO) calls the merge script. A T path would tie the skill to one material. The brief's open point (skill vs material folder) still goes to the user (§9 item 9). The kit and the cache stay in T, as both drafts say. |
| 3 | where the merge rule lives | D: JS `mergeRound()` plus a Python mirror, parity-tested by a Node harness; C: one mechanical workflow agent runs merge_panel.py | C | One implementation. D's MERGE block, `check_merge.mjs` and its tests D3-D5 are dropped. C's `classify_js` parity test keeps the old line-138 rule on record. |
| 4 | statuses | D: confirmed / rejected / unverified, artifact sub-claims counted as confirmed; C adds `confirmed_subclaim` | C | The renderer needs it for the "sub-claim" REJECTED rows. Totals agree: D's 30 confirmed = C's 26 + 4. |
| 5 | lead schema | D: slim `LEAD` (`clusters`, `next_round`, no `fix_status`, no `date`); C: `LEAD` = round-2 review_result.json minus `counts` | C, plus D's `spot_check` and `not_checked` as optional keys | Round 2's review_result.json then is the test fixture. `date` comes from the workflow's `args.date`, because workflow scripts cannot call `Date`. |
| 6 | `not_checked` | D: required in FINDINGS and VERDICTS | required in the JS schemas, optional in merge_panel.py (round-2 files lack it); collected in merged.json `not_checked` | brief change 3 |
| 7 | unverified findings | D: `reason` low / verifier_missing | merged.json `unverified_reason` with the same two values; `missing_verifiers` lists only lenses with a high or medium finding and no verifier file | brief change 5: a lens with only lows has no verifier by design |
| 8 | kit inside the composite | B.7: composite uses `rk.plane_residual`, `rk.ring_median`; A: its own formulas | `inv16_terms` calls `rk.plane_residual` (the same lstsq) and `rk.ring_median(..., d_out=)`, a new optional argument that reuses the cached `d<k>/dist_out_mm` | B's band is lo < d <= hi, A's ring lo <= d <= hi. They select the same px on this grid: (d/p + 0.5)² is never an integer at d = 2, 6, 20 or 40 mm. |
| 9 | thread cap | B: kit sets 4 variables; A: cv2 only if set; D: adds `VECLIB_MAXIMUM_THREADS` | both review_kit.py and composite_decal.py, at the top before any numpy import: `os.environ.setdefault(k, "2")` for `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`; after `import cv2`: `cv2.setNumThreads(int(os.environ["OMP_NUM_THREADS"]))` | macOS numpy wheels use Accelerate (vecLib) |
| 10 | run_all.sh insertion | B: after line 17 `cd "$HERE" \|\| exit 2` | after line 19 `fail=0` | Inserted before line 19, the self-test's `fail=1` would be reset. The composite line (today :38) stays word for word and moves to :41. |
| 11 | A's test skip rule | "newest dump mtime <= 2026-10-03 23:19" (local time) | newest mtime of T/dump/asphalt_{lane,detail,decal}_* <= mtime of T/review/round2/decal/composite/composite_decal.json (2026-10-03 23:19:54 -0500), compared as epoch seconds | timezone-proof; tar keeps both mtimes |
| 12 | legacy copy | A: freeze composite_decal.py only | freeze composite.py too | the frozen composite_decal would otherwise import the edited composite.py |
| 13 | D1 `node --check` | on review_round.js as a module | wrap the body in an async function first (§6.4) | the script's top-level `return` is illegal in a module |
| 14 | B.8 gaps | open | closed from the code: seam_lip_registration is `lip_registration` (<a>/decal_patches_verify_b/v3_lip.py:21-78), not `edge_jaggedness`; crown `ramp_mm` (<a>/decal_patches_verify_b/v4b_plateau.py:21); wall-top ray normal (<a>/decal_potholes_verify_b/v1_walls.py:28-29, 105-111); granite `tol` 0.006 (<a>/realism_onfoot_verify_b/f5_granite.py:50, f5_granite.json `tol`); f1_stones boundary count (<a>/realism_onfoot_verify_a/f1_stones.py:51-53) | §4 |
| 15 | workflow `agent()` options | C.7, D: unknown whether `agent()` takes `model` / `effort` | it does: `effort` 'low'..'max', `model`; scripts have no file system and no `Date` | Workflow tool reference |

### 0.5 Who calls what

| caller | calls | when |
|---|---|---|
| main session, preflight | `composite_decal.py --out review/round<N>/decal/composite --build-only` (background, ~90 s); `checks/review_kit.py --selftest` | before the lenses start |
| T/checks/run_all.sh | `review_kit.py --selftest` (new, first); matcheck per config; ladder.py; accept_r1.py; decal_extra.py; wrong_builds.py; previews.py x3; composite.py x5; `composite_decal.py --out review/$R/decal/composite` (now reads or rebuilds the cache in review/$R/cache) | every measurement run |
| decal_extra.py, accept_r1.py, wrong_builds.py | `import review_kit as rk`; wrong_builds.py also `composite_decal.WRONG_BUILDS` | after session 4 wires the plan rows |
| composite_decal.py | `review_kit` (`plane_residual`, `ring_median`; P2 later: `area_mean_step`, `band_colour_abs`, `rendered_relief_share`, `visible_share`, `stack_leak_px`) | `--options p1`, P2 |
| lens / verifier agents | `composite_decal.get_stack(name, cache_dir=..., on_stale="error")`, `compose`, `inv16`, `inv16_terms`; review_kit; matcheck | during the panel; never rebuild |
| workflow review_round.js | lens -> verifier agents (pipelined); one `merge` agent runs `merge_panel.py`; the lead agent writes `lead.json` | the panel |
| main session, after the panel | `render_findings.py --check`, then `render_findings.py --result` (and `merge_panel.py` first on the Agent-tool route) | before the gate |

## 1. Order of work

Estimates are for implementing plus a code review with Claude on the Mac. M5 depends only on M1 and can move anywhere
after it. Run the tests named in each row before the next milestone; ids refer to §8.

| M | what | files | acceptance (§8) | depends | est. |
|---|---|---|---|---|---|
| M0 | Commit this spec (ask first); pull on the Mac | REPO/review_round2_implementation_spec.md | - | - | 5 min |
| M1 | Mac setup: links, venv, copy T, smoke test | §2 | S1-S3 | M0 | 45 min |
| M2 | Composite split: legacy copies, `build_site`/`save_stack`/`load_stack`/`get_stack`, `compose`, `render`, options (opacity, lref, lane, order), CLI flags, composite.py `build_window`/`render_window`/`blend_lane_detail` | T/composite_decal.py, T/composite.py, T/checks/legacy/{composite_decal_r2,composite_r2}.py, T/checks/test_composite_decal.py | A1-A6, A10-A12 | M1 | 3-4 h |
| M3 | Review kit: all functions, `--selftest`, run_all.sh lines; round-2 reproduction (report) | T/checks/review_kit.py, T/checks/run_all.sh | B-selftest, B-repro | M1 | 4-6 h |
| M4 | P1(a) hooks: `inv16_terms`, `P1_GATES`, `--options p1`, `WRONG_BUILDS` (default stays `r2`) | T/composite_decal.py, test_composite_decal.py | A7-A9 | M2, M3 | 1-2 h |
| M5 | Merge and render scripts with tests | SK/merge_panel.py, SK/render_findings.py, SK/tests/test_review_pipeline.py | C-syn, C-merge, C-render | M1 | 3-4 h |
| M6 | Workflow and skill docs | S/assets/workflows/review_round.js, S/references/review.md, S/SKILL.md | D1-D4 | M5 | 1.5-2 h |
| M7 | Material docs: REFERENCE.md, prompts 4/5/6, CONTEXT_PROMPT | T/review/REFERENCE.md, T/prompts/*.md, T/CONTEXT_PROMPT.md | D5-D9 | M2-M6 (quotes their commands) | 1-1.5 h |
| M8 | Integration: full run_all.sh on the Mac, cache timing, commits | - | I1-I3 | M2-M7 | 1 h |

Total about 15-21 h. Commits (§7) come after M5 and M6, each only after the user says yes.

## 2. macOS setup

### 2.1 What is in git

In git and pushed to main: 317afcd (Windows/OpenCV fix, setup_env.sh prints the venv python), 146488d "material
check" (matcheck opt-ins the asphalt checks need: seam `method: rowmedian` with `floor_mm` / `floor`, ridge `against`,
components `border_px`; references/checks.md), eb484d1 (the brief at the repo root). Nothing under T is in git: the T
copy is the only source for build/, checks/, review/, prompts/, spec.md and composite*.py.

### 2.2 Steps

| step | command (macOS unless noted) | check |
|---|---|---|
| 1. Bridge repo | `git -C <checkout> pull --ff-only` | `git log --oneline -4` shows this spec's commit, then eb484d1, 146488d, 317afcd |
| 2. Links | once per Mac `./install.command`; then `python3 tools/link_install.py` | `python3 tools/link_install.py --status`: `~/.claude/skills/sd-material-research` -> `<checkout>/skills/sd-material-research` |
| 3. Venv | `PY=$(bash ~/.claude/skills/sd-material-research/scripts/setup_env.sh)` (creates `~/.cache/sd-material-research/venv` with numpy, pillow, scipy, opencv-python; needs `python3`) | `echo $PY` -> `$HOME/.cache/sd-material-research/venv/bin/python`; `"$PY" -c "import numpy, scipy, PIL, cv2"` exits 0 |
| 4. Thread cap | `export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2` in every shell that runs Python | - |
| 5. Old Mac copy | the first build was on this Mac (2026-10-03): `mv ".../Substance Designer/asphalt_materials_tools" ".../asphalt_materials_tools_mac_20261003"`, the same for `asphalt_materials.sbs`. Move, never delete | the names are free |
| 6. Pack (Windows, Git Bash) | `cd "/c/Users/andy/Documents/Allegorithmic/Substance Designer" && tar -cf ~/asphalt_mac.tar --exclude=asphalt_materials_tools/dump_round1 --exclude=asphalt_materials_tools/dump/cal --exclude=asphalt_materials_tools/dump/decal asphalt_materials.sbs asphalt_materials_tools` | about 1.6 GB+ (PNGs don't compress, so no `-z`) |
| 7. Unpack | `tar -xf asphalt_mac.tar -C ~/Documents/Allegorithmic/Substance\ Designer/` | in T: `ls dump/*.png \| wc -l` -> 812 (lane 288 = 12 exports x 24 maps, detail 216 = 18 x 12, decal 308 = 22 x 14); `ls dump/*.json \| wc -l` -> 52; mtimes kept |
| 8. Smoke test | §2.4 | S1 |

`dump/*.png` + `dump/*.json` (812 + 52 files, 1.54 GB) are the 2K exports every check and test reads. With the copied
PNGs the inputs are bit-identical to what round 2 measured, so every test below that quotes a round-2 number holds as
written, and Designer is not needed. The round-2 fixtures (T/review/round2/*.json, T/review/agents/round2/, T/review/
round2/decal/composite/composite_decal.json) travel in the same tar.

### 2.3 Re-export instead (only if dump/ is not copied)

Needs Designer on the Mac with the bridge plugin running and the package open. From T:
```
"$PY" ~/.claude/skills/sd-material-research/scripts/sdcall.py build/job_export_2k.py --timeout 1800
"$PY" ~/.claude/skills/sd-material-research/scripts/sdcall.py build/job_decal_2k.py --timeout 900
```
- `job_export_2k.py`: lane v0 v1 v2 v3 v4 v3x and detail v0 v1_nwp ... v4_wp, each with its nowear, into dump/: 30
  exports, 94 s on Windows. No rebuild.
- `job_decal_2k.py`: the 11 decal presets plus nowear, 22 exports, 47 s; retries any preset with fewer than 14 outputs.
- Both overwrite their `.result.json`. Then back up `review/scorecard_*.{md,json}` and run
  `PY="$PY" bash checks/run_all.sh mac` (~12 min on Windows). Exports from another machine may differ in the last
  bits: the smoke test then holds to its tolerance only, and tests A1-A9 and the B reproduction rows become reports.

### 2.4 Smoke test (S1)

cwd T; paste the R7 loader (`load()`, T/review/BRIEF.md §8, lines 1114-1126) above this:
```python
import numpy as np
for cfg in ("lane_v4", "detail_v4_wp", "decal_p1_v4"):
    c, v = load(cfg); s = v["surface_level"] * c.depth_mm
    rel, rel0 = c.height_mm() - s, c.height_mm("nowear") - s
    luma, rough = c.map_values("basecolor", "srgb255"), c.main.gray("roughness")
    print(cfg, round(c.mm, 3), round(float(rel.min()), 1), round(float(rel.max()), 1), round(float(rel0.min()), 1),
          round(float(rel0.max()), 1), round(float(np.median(luma)), 1), round(float(np.median(rough)), 3))
```
Expected (Windows, 2026-10-04; maps 2048 x 2048 float32; exact for copied PNGs, +-0.2 mm / +-0.5 luma / +-0.005
roughness after a re-export):
```
lane_v4      1.787  -46.5   8.2  -19.7  5.2  103.5  0.915
detail_v4_wp 0.488   -9.5  -0.1   -0.7 -0.1  101.0  0.917
decal_p1_v4  0.488 -105.9  -0.0   -0.0 -0.0  101.1  0.92
```
On a miss with copied PNGs, match the Windows venv: numpy 2.5.3, scipy 1.18.1, pillow 12.3.0, opencv-python 5.0.0.93
(`"$PY" -m pip install <pkg>==<ver>`).

### 2.5 Path rules for all new code

- T scripts find files through `os.path.expanduser("~/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools")`
  or their own `__file__`, and the skill through `~/.claude/skills/sd-material-research/scripts`. No absolute paths.
- run_all.sh takes T from its own location (lines 10-11), the skill from `$HOME` (line 12); `PY` defaults to `python3`
  (line 13), which has no numpy, so always pass `PY="$PY"`. registry.json holds no absolute paths.
- Windows-only strings today: usage comments (line 5 of checks/accept_r1.py and checks/decal_extra.py), the Python
  lines in the prompts (§6.6, §6.7), BRIEF.md §1's "Don't use scripts/setup_env.sh here".
- `os.path.join` / `pathlib`; `encoding="utf-8"` on every text open (BRIEF.md and the specs contain ≤ × Δ −; the
  Windows default codepage is cp1252); `newline="\n"` on writes.

### 2.6 Back to Windows (if round 3 runs there)

Tar back the changed T files: `composite.py`, `composite_decal.py`, `checks/` (review_kit.py, test_composite_decal.py,
legacy/, run_all.sh), `review/REFERENCE.md`, `prompts/`, `CONTEXT_PROMPT.md`, `review/round2/_spec/`,
`review/round2/implementation_spec.md`. Exclude `review/*/cache/` (about 2.6 GB per round; rebuilt by the preflight).
Then `git pull` on Windows for merge_panel.py, render_findings.py and the skill edits. Record which machine holds the
current copy in CONTEXT_PROMPT.md "Machines and setup".

## 3. Composite split: build once, compose variants in seconds (brief change 1, first half)

### 3.1 Today's structure (T/composite_decal.py, 617 lines)

| line | name | what it does | cost driver |
|---|---|---|---|
| 61-67 | imports | `import composite as cp` (brings `mc` = matcheck, `pv` = previews); cv2 optional | |
| 69-87 | constants | `TILE_MM` = 1000/2048 = 0.48828125; `DETAIL_PRESETS` v0 0.25, v1 1.5, v2 5, v3 11, v4 20 yr; `AGES`; `LANE_AGE` {v3: 11, v4: 20}; `FEATURES` (10 lane masks, L73 order: sealant ... fatigue); `DECAL_MASKS` (8, L74); `KINDS`; `SITES` (L76-81); `OUTLINE_COL`, `CORE_COL`, `LINE_PX` 6; `SIGMA_REF_MM` 40; `SHADOW_PAD_MAX` 400 | |
| 92 | `resample(a, y0, x0, step, n, wrap, filt)` | n x n grid; whole-px origin at step 1 = exact crop (`cp.window` or clipped `np.ix_`), else PIL resize with a fractional box | lane: bicubic, step 0.273 |
| 117 | `lowpass(h, sigma_px)` | `cv2.GaussianBlur` BORDER_REFLECT (scipy fallback) | sigma 81.92 px on 2048² |
| 128, 145 | `Lane(key)`, `.on_grid(y0, x0, n, p)` | loads T/checks/lane_<key>.json via `cp.ctx_of`: h (mm), bc (linear), r, wps, w, seg + 10 FEATURES; resamples all bicubic with wrap, clips bc, wps, w, seg, FEATURES to [0, 1] | 18 decodes; 20 planes to n² |
| 154-175, 178, 185 | `Details`, `.side`, `.pair(preset)`; `detail_on_grid`; `mix(gw, gn, Wp)` | detail config loaded once (bc lin, h - mean, r - mean, mean bc, mm); LANCZOS, world-aligned, exact crop at the default p; WP/NWP lerp by `wheelpath_soft` -> (dbc, dmean, dh, dr) float32 | |
| 195-239 | `Decal(tag, values)`, `.rim_band()` (215), `.on_grid(oy, ox, y0, x0, n, p)` (230) | decal Ctx in memory (1.0 m, 2048 px, prefix `asphalt_decal_<tag>_`): bc, rel = height_mm - surface_level x depth, r, 8 masks; rim band on its own tile; LANCZOS (NEAREST for detail_age), no wrap, clipped | 11 decodes, an EDT |
| 242, 248 | `preset_index(age)`, `nearest_preset(years)` | per-px nearest detail preset to detail_age x 30 yr, ties to the younger | |
| 255, 268 | `plateau_centre(v)`, `pick_site(lc, how)` | deterministic site px from the lane masks | |
| 298 | `luma255(alb_lin)` | sRGB luma 0-255 | 5+ passes per decal in inv16 |
| 302, 312 | `shadows(H, p)`, `shade_views(alb, rough, H, p)` | edge pad (<= 400 px) + `pv.shadow_vis` (SK/previews.py:156, `ceil(span / 0.235 mm)` steps over (n + 2 pad)²); normals by `np.gradient`, raking and front `pv.shade` (previews.py:127) | the shadow march |
| 322, 328 | `edges(m)`, `under_view(alb_lane, L, layers)` | the "under" PNG (`pv.mask_overlay`, previews.py:429) | 6 px erosions |
| 346, 353, 357 | `save`, `maxabs`, `med` | 8-bit PNG (compress 3); rounded masked stats (6 and 3 decimals) | |
| 361-438 | `inv16(layers, L, C, p)` | per-decal INV-16 numbers from arrays only | EDT per decal, luma255 |
| 444-534 | `run_site(name, spec, lane, details, decals, p, out)` | one site end to end -> (info, sheet row) | everything |
| 537, 565-613 | `table(results)`, `main(argv)` | console table; CLI, loads lanes/decals once, loops sites, sheet, JSON, exit 1 on any `inv16_ok` false | |

`run_site` phases: grid 446-450 (`pick_site`, n, Yc, Xc, y0, x0); lane on grid 451; `det(preset)` closure 455-461
(memoised `mix`); lane + detail blend 463-471; `Lref = lowpass(H, 40 / p)` 472; decal loop 474-505 (grid sampling,
per-px preset gather, `alb_d`, `r_d`, `h_d = (Lref + rel + w * Dh)` at 492, layer dict, alpha blend, cov); cores
506-509; `inv16` 510; shading 512-513; images 514-520; info 521-526; sheet row 530-534.

| site | lane (age) | pick | window | grid n | decals (tag @ V offset m) | detail presets drawn (px) |
|---|---|---|---|---|---|---|
| p3_joint_v4 | v4 (20 yr) | joint | 1.0 m | 2048 | p3_v4 @ 0 | v1 295,527, v4 105,112 |
| p1_wpfatigue_v4 | v4 | left WP | 1.0 m | 2048 | p1_v4 @ 0 | v2 1,034,594, v4 189,568 |
| q0q3_wp_v4 | v4 | right WP | 1.1 m | 2253 | q0_v4 @ 0, q3_v4 @ +0.25 | q0: v3 1,978,704, v4 232,768; q3: v1 1,111,360, v2 2,416, v4 175,488 |
| q1_wp_v3 | v3 (11 yr) | left WP | 1.0 m | 2048 | q1_v3 @ 0 | v1 535,527, v2 8,092, v3 133,923 |

Inputs: lane T/checks/lane_<v>.json -> T/dump/asphalt_lane_<v>_* (3.66 m, 2048 px, 1.787109375 mm/px; depth v4 65 mm,
v3 40 mm; masks incl. `deform`; the nowear render through the config's `compare.nowear`); details
T/checks/detail_<p>_{wp,nwp}.json (v0: detail_v0.json) -> T/dump/asphalt_detail_*; decals: T/build/presets.json
`asphalt_decal[tag].values` + T/dump/asphalt_decal_<tag>_{basecolor,height,normal,roughness,metallic,ambientocclusion,
opacity,pothole,patch,seam,layer_index,debris,detail_weight,detail_age}.png. Decal tile corner (world mm; rows = V along
the road, cols = U across) = (Yc + off x 1000 - 500, Xc - 500). At the default p every decal and detail sample is an
exact crop; only the lane is resampled.

CLI today (L566-571): `composite_decal.py --out DIR [--sites a,b] [--px-mm 0.488]` (0.488 snaps to `TILE_MM` within
0.5 %, L577). Writes DIR/composite_<site>_{albedo,lit_raking,lit_front,height,lane_only_lit_raking,under}.png,
DIR/composite_decal_sheet.png (a 4-panel 512 px row per site), DIR/composite_decal.json; prints a table; exits 1 when
any `inv16_ok` is false. Round 2 wrote T/review/round2/decal/composite/. Caller: run_all.sh:38.

Time (measured, composite_decal.json): 92.4 s; sites 21.0 (p3) / 28.9 (p1) / 25.6 (q0q3) / 12.1 (q1) s; ~4.8 s loading
and the sheet. The spread follows the shadow march (estimated: q1 ~3 s, span 26.6 mm; p3 ~8 s, 59.1; q0q3 ~8 s, 54.1;
p1 ~19 s, 134.0, pad capped). The other ~10-18 s per site is resampling (20 lane planes), detail mix, blend, low-pass,
decal sampling, inv16, two `pv.shade` passes, `under_view`, 6 PNGs and 4 panel resizes. Only resampling, mix, blend,
low-pass and decal sampling go into the cache. The phase split is an estimate; `build_seconds` (§3.2) measures it.

### 3.2 New structure (same file)

```python
BUILD_VERSION = 1          # bump when build_site / Lane / Decal / Details / resample / the npz schema change
CACHE_FORMAT = 1
class StaleCache(Exception): ...
Stack = dict               # key -> ndarray (lazy, from np.load) plus "meta" -> dict (parsed meta_json)
Comp = dict                # see compose()

def site_grid(name, lane, p) -> dict                     # L446-450 factored out: cy, cx, pick, n, Yc, Xc, y0, x0
def build_site(name, p=TILE_MM, lanes=None, details=None, decals=None, presets=None) -> Stack   # in memory
def save_stack(stack, path) -> None                       # np.savez (uncompressed) to path + ".tmp.npz", then os.replace
def load_stack(path) -> Stack                             # np.load(path, allow_pickle=False); lazy per key
def cache_path(cache_dir, name) -> str                    # <cache_dir>/composite_<name>.npz
def cache_inputs(name) -> list[str]                       # files build_site reads (§3.2.3)
def is_stale(path, name, p) -> tuple[bool, str]           # (stale, reason)
def get_stack(name, p=TILE_MM, cache_dir=None, on_stale="error") -> Stack   # "error" | "rebuild" | "use"
def opacity_profile(kind, a_exp, fp_soft, dist_out_mm, full_mm=0.5, zero_mm=1.5) -> ndarray
def rim_band_of(a, dist_out_mm, mm) -> dict               # Decal.rim_band L218-228 as a pure function
def compose(stack, opacity="export", lref="lane40", lane="worn", sigma_ref_mm=40.0,
            ring_mm=(20.0, 40.0), order=None) -> Comp     # arrays only, ~1 s
def inv16(layers, L, C, p) -> list[dict]                  # L361, unchanged signature and output
def inv16_terms(W, N, U, gates=P1_GATES, seat_ring_mm=(2.0, 6.0), seat_alpha_min=0.998,
                seat_exclude=()) -> dict[str, dict]       # tag -> P1(a) terms (§3.4); adds keys, never edits legacy ones
def render(comp, stack, out, name, images=IMAGES) -> PIL.Image   # L511-534: shading, PNGs, sheet row; only when asked
def run_site(name, stack, out, options, images=True) -> tuple[dict, PIL.Image | None]
def main(argv=None) -> int
```

`Lane`, `Details`, `Decal`, `resample`, `lowpass`, `detail_on_grid`, `mix`, `preset_index`, `pick_site`, `luma255`,
`shadows`, `shade_views`, `under_view`, `table` keep their code. `Decal.rim_band` calls `rim_band_of`. The thread cap
of §0.4 item 9 goes at the top of the file. Add `sys.path.insert(0, os.path.join(HERE, "checks"))` and
`import review_kit as rk` (needed from M4).

#### 3.2.1 build_site(name) -> Stack, saved as T/review/round<N>/cache/composite_<site>.npz

1. `lane = Lane(spec["lane"])`. Nowear inputs as <a>/g1_requirements_verify_a/inv16_verify.py:49-60:
   `R = lane.ctx.render("nowear")`, `h_n = lane.ctx.height_mm("nowear")`,
   `bc_n = mc.srgb_to_linear(R.map("basecolor")[..., :3])`, `r_n = R.gray("roughness")`, `w_n = R.gray("detail_weight")`;
   `deform = lane.ctx.main.gray("deform")`.
2. `g = site_grid(name, lane, p)`; `L = lane.on_grid(y0, x0, n, p)`; the four nowear maps with the same call
   (`resample(..., True, Image.BICUBIC)`; bc_n and w_n clipped to [0, 1]); `deform_g` the same, not clipped
   (inv16_verify.py:254).
3. `det(preset)` as L455-461 with `Wp = L["wps"]` (the wear lane's; the nowear blend uses it too).
4. Lane-only worn: L463-470 verbatim -> `lane/H`, `lane/alb`, `lane/rough`. Nowear: the same expressions with h_n, bc_n,
   r_n, w_n in place of L["h"], L["bc"], L["r"], L["w"] (L["seg"], dh, dbc, dmean, dr unchanged).
5. References: `ref/G40_lane = lowpass(lane/H, 40/p)` (= today's `Lref`, L472); `ref/G40_nowear = lowpass(nowear/H,
   40/p)`; `Hdef = (sl*D + 2*(deform_g - 0.5)*D).astype(f32)` with sl, D = presets.json `asphalt_lane[<v>].values`
   `surface_level`, `height_depth_mm` (v4 0.8, 65; v3 0.7, 40); `ref/G40_deform = lowpass(Hdef, 40/p)`.
6. Per decal k in placement order: L477-492 up to `r_d`, without the blend: `G`, `sel`, the Dbc/Dmean/Dh/Dr gather,
   `alb_d`, `r_d`, and `wDh = (w * Dh)` float32 (`Lref + rel + wDh` reproduces L492 bit for bit: numpy evaluates L492
   as `(Lref + rel) + (w * Dh)`). `fp_soft = max(G["pothole"], G["patch"])` (`fp_soft >= 0.5` equals L493's fp).
   `dist_out = max(EDT(~fp) - 0.5, 0) * p` (L416; = `rk.true_dist` d_out). `lum = luma255(alb_d)`. Tile arrays from
   `dec.maps` for the rim band.
7. Lane feature bitfield, view masks, meta; `save_stack`.

#### 3.2.2 npz keys

Grid px (j, i) spans world V [y0 + j p, y0 + (j+1) p) mm and U [x0 + i p, x0 + (i+1) p) mm; p = 0.48828125.

| key | dtype | shape | units / values |
|---|---|---|---|
| `meta_json` | str (0-d) | () | JSON, below |
| `lane/H` | float32 | (n, n) | mm, lane + detail height (today's `lane_only[2]`, L468) |
| `lane/alb` | float32 | (n, n, 3) | linear albedo 0-1 (L469) |
| `lane/rough` | float32 | (n, n) | 0.02-1 (L470) |
| `lane/feat` | uint16 | (n, n) | bit k = `FEATURES[k] >= 0.5` (k = L73 order); wear lane |
| `lane/view_masks` | float32 | (n, n, 5) | `under_view` inputs, clipped 0-1: sealant, max(crack, crack_l, crack_t), ravel, oil, max(pumping, dirt) |
| `nowear/H`, `nowear/alb`, `nowear/rough` | float32 | as `lane/*` | the same blend over the nowear render |
| `ref/G40_lane`, `ref/G40_nowear` | float32 | (n, n) | mm, G40 of `lane/H`, of `nowear/H` |
| `ref/G40_deform` | float32 | (n, n) | mm, G40 of the as-built + rut surface Hdef |
| `d<k>/a` | float32 | (n, n) | exported opacity on the grid, 0-1 (0 outside the tile) |
| `d<k>/fp_soft` | float32 | (n, n) | max(pothole, patch), 0-1 |
| `d<k>/dist_out_mm` | float32 | (n, n) | mm beyond the outline, 0 on the footprint |
| `d<k>/seam` | bool | (n, n) | seam >= 0.5 (its only use, L403-406) |
| `d<k>/sel` | uint8 | (n, n) | detail preset index 0-4 into `DETAIL_PRESETS` |
| `d<k>/rel` | float32 | (n, n) | mm, decal height - surface_level x depth |
| `d<k>/wDh` | float32 | (n, n) | mm, w_d x (D_mm - mean D_mm) |
| `d<k>/alb`, `d<k>/rough` | float32 | (n, n, 3), (n, n) | `alb_d` (L490, linear), `r_d` (L491) |
| `d<k>/lum` | float32 | (n, n) | `luma255(alb_d)`, 0-255 |
| `d<k>/tile_a`, `d<k>/tile_fp_soft`, `d<k>/tile_dist_out_mm` | float32 | (2048, 2048) | the decal's own tile (0.48828125 mm/px), for `rim_band_of` under any opacity profile |

`meta_json` keys: `format`, `build_version`, `site`, `spec` (SITES[name] as JSON lists), `lane_key`, `lane_age_yr`,
`lane_detail_preset`, `lane_mm_per_px` (1.787109375), `lane_surface_level`, `lane_height_depth_mm`, `mm_per_px`, `n`,
`grid_origin_world_mm` [y0, x0] and `centre_world_mm` [Yc, Xc] (full floats), `lane_px` [cy, cx], `pick` (dict from
`pick_site`), `sigma_ref_mm` 40.0, `features` (FEATURES list), `decals` (placement order; each {`k`, `tag`, `kind`
(KINDS text), `kind_id`, `off`, `corner_world_mm`, `preset_values` (the 9 fields main() copies, L592-593), `rim_band`
(Decal.rim_band() dict), `tile_mm_per_px`}), `layer_order` [tags], `inputs` [{`path` relative to T, `mtime`, `size`}],
`inputs_read_at` (epoch s, taken before the first read), `build_seconds` {`load`, `lane_grid`, `nowear_grid`, `detail`,
`blend`, `lowpass`, `decals`, `save`, `total`}, `versions` {numpy, scipy, PIL, cv2 or null}.

Size (uncompressed float32): ~0.55 GB per single-decal site, ~0.92 GB for q0q3 (n 2253, two decals), ~2.6 GB for the
four, per round. Loading is lazy per key; `compose` reads ~20 planes (~0.35 GB).

#### 3.2.3 Cache validity

`cache_inputs(name)`: T/checks/lane_<v>.json; every T/dump file starting `asphalt_lane_<v>_` (wear, nowear, deform);
every T/dump file starting `asphalt_detail_` and every T/checks/detail_*.json (conservative); every T/dump file starting
`asphalt_decal_<tag>_` for the site's tags; T/build/presets.json; SK/matcheck.py. Code files are not inputs:
`BUILD_VERSION` covers them, so editing compose or inv16 never forces a rebuild.

Stale when: the file is missing or unreadable; `format` != CACHE_FORMAT or `build_version` != BUILD_VERSION;
|`mm_per_px` - p| > 1e-9; `spec` != SITES[name]; any input's mtime > `inputs_read_at`; the input path set differs from
`meta.inputs`. The reason names the first offending file. `get_stack(on_stale="error")` (the library default) raises
`StaleCache(reason)`, so parallel agents never start 90 s builds; the CLI uses `"rebuild"`.

#### 3.2.4 compose(stack, **options) -> Comp

```python
order = order or list(range(len(decals)))                         # decal on decal: subset or reorder
a_k   = opacity_profile(opacity_k, d<k>/a, d<k>/fp_soft, d<k>/dist_out_mm)   # opacity: one str, or a list per k
H0, alb0, rough0 = by lane: worn -> lane/*; nowear -> nowear/*;
                   under -> np.where(drawn, nowear/*, lane/*), drawn = OR_k (a_k > 0)   # [..., None] for alb
H, alb, rough = H0.copy(), alb0.copy(), rough0.copy(); cov = zeros_like(H)
for k in order:                                                     # L476-505 without the sampling
    R_k  = reference(lref, ...)                                     # §3.3
    h_d  = (R_k + rel_k + wDh_k).astype(float32)
    layer = {tag, kind, off, a, fp=fp_soft>=0.5, core_own=fp & (a>=0.999), seam, rel, sel, alb, r, h=h_d, lum,
             below_alb=alb, below_h=H, below_cov=cov, rim=rim_band_of(profile on the tile arrays), corner, ref=R_k,
             ref_offset_mm}
    a3 = a[..., None]; alb = (1-a3)*alb + a3*alb_d; rough = (1-a)*rough + a*r_d; H = (1-a)*H + a*h_d
    cov = 1 - (1-cov)*(1-a)
cores as L506-509
return {"p", "n", "options", "alb", "rough", "H", "C": (alb, rough, H), "lane_only": (alb0, rough0, H0),
        "L": {f: bool (n, n) from lane/feat}, "layers"}
```

`inv16(comp["layers"], comp["L"], comp["C"], comp["p"])` is today's function. Its only edit: use `lay.get("lum")` in
place of `luma255(lay["alb"])` at L375 and of `luma255(lj["alb"])` at L407/L409 when present (same values). Bool
feature masks work with its `>= 0.5` / `< 0.5` tests. `render()` = L512-534 on `comp`, with `lane/view_masks` (the
5-plane array) in place of L for `under_view`.

#### 3.2.5 CLI

Unchanged: `--out` (required), `--sites`, `--px-mm`, the six PNGs, sheet, JSON, table, exit code. Added:
`--cache DIR` (default `<out>/../../cache`, i.e. review/<round>/cache for run_all.sh's `review/$R/decal/composite`),
`--rebuild` (ignore the cache), `--build-only` (refresh stale caches, write nothing else; the preflight step),
`--no-images`, `--options r2|p1` (default `r2`; P1 flips it in its own session-4 change). The JSON adds top-level
`options` and `cache` ({`dir`, per site {`from_cache`, `build_seconds`}}) only.

Agent use (cwd T, `sys.path` includes T):
```python
import composite_decal as cd
S = cd.get_stack("p1_wpfatigue_v4", cache_dir="review/round3/cache")   # raises StaleCache if stale; never builds
W = cd.compose(S, opacity="aa", lref="deform_med")
rows = cd.inv16(W["layers"], W["L"], W["C"], W["p"])
```

Targets: `--build-only`, all four sites, <= 90 s at 2 threads (today's 92 s includes the shadow march and PNG writes
that the build skips); from a warm cache, per site: `compose` <= 1 s, `compose` + `inv16` <= 4 s, the three composes of
the P1 terms <= 10 s; `render` costs what today's shading + PNG phase costs, only when asked.

### 3.3 Options (prior art under `<a>/`)

Five round-2 scripts are or wrap verbatim copies of composite_decal.py (g1_requirements/cdec.py, decal_patches_verify_a/
my_composite_decal.py, regressions_verify/composite_decal_rv.py, g1_requirements_verify_a/cdv.py, decal_potholes_verify_a/
cdv.py). The closest precursor of build/compose is <a>/regressions_verify/r1_composite.py: `prepare()` :72-120 (build),
`variant()` :123-157 (compose with reference modes and an opacity hook).

**Opacity (`opacity=`)**, on the grid and, for the rim band, on the tile arrays:

| value | formula | from |
|---|---|---|
| `export` (default) | `a = d<k>/a` (today: opacity 1 to ~6 mm, 0 from 20 mm) | composite_decal.py:480 |
| `aa` (P2(1), Q1-1) | `a = clip(2 * fp_soft, 0, 1) * (a_exp > 0)` = Levels(DL_fp, 0, 0.5), min the border guard | <a>/decal_potholes_verify_a/va1c_band_colour.py:39 (pothole only, no guard); plan P2(1) |
| `narrow` (Q1-2) | `a = where(fp, 1, clip((zero_mm - dist_out) / (zero_mm - full_mm), 0, 1)) * (a_exp > 0)`, full 0.5, zero 1.5 mm | <a>/decal_patches/a2_rim_experiment.py:61, <a>/decal_patches_verify_a/v3_rim.py:96; the same ramp without the guard in <a>/decal_potholes_verify_a/va1_rim.py:90, <a>/decal_potholes/m3_composite.py:96 |

The guard `(a_exp > 0)` follows a2/v3, because P2(1) keeps the border guard; inside the window it only differs at tile
border truncation. `aa` uses max(pothole, patch), because DL_fp is the union of every kind. m3_composite.py blends with
the v4 detail only (:30); the spec keeps the per-px preset (`sel`). m1c_aa_sim.py (decal tile only) and the recolour
modes (va1c `dec_aa`, v3_rim `ringwp`) change the decal graph, not the composite: not carried.

**Reference height (`lref=`)**, per decal k; G40 = `lowpass(., 40/p)`:

| value | formula | from | role |
|---|---|---|---|
| `lane40` (default) | `R = G40(H0_run)`: worn -> `ref/G40_lane`; nowear -> `ref/G40_nowear`; under -> computed; `sigma_ref_mm` != 40 recomputes | composite_decal.py:472; inv16_verify.py `lp40`; r1_composite `worn40` | wrong build `lref_worn40` |
| `nowear40` | `R = ref/G40_nowear` for every run | inv16_verify.py `lp40_now` (:139-140); r1_composite `nowear40` | wrong build `lref_nowear40` |
| `deform_med` (P1(a) L_ref_d) | ring = `(dist_out >= 20) & (dist_out <= 40) & (a_k <= 0.002)`; `R_k = (ref/G40_deform + rk.ring_median(H_sofar - ref/G40_deform, fp_k, p, 20, 40, valid=a_k <= 0.002, d_out=dist_out_k)["value"]).astype(f32)`; H_sofar = the composite before decal k; empty ring -> `ValueError` naming the decal | inv16_verify.py:113-115, base :250-256 | P1 default |

`ring_mm` overrides (20, 40). Not carried (rejected or superseded): `ring_nc` (plan rejected[19]), `ring_pl`, `hybrid*`,
`deform_pl`, `deform_rpl` (inv16_verify.py:116-152), `closed40` / `inpaint` (<a>/regressions_verify/r1b_seat.py:48-68),
the Laplace membrane (r1c_membrane.py, rejected[18]), `add_out`, `hole60`, `a9995` (r1_composite.py:207-223).

**Lane swap (`lane=`)**: `worn` (default) | `nowear` | `under` (nowear only where an included decal draws, `a_k > 0` under
the active profile). Follows inv16_verify.py:49-60, 246-248: swap h, bc, r, w; keep wps, seg and the feature masks of the
wear lane. <a>/g1_requirements/inv16_swap.py:19-30 also swaps wps, seg and FEATURES; the layout is bit-exact between
wear and nowear (plan `keep_as_is[2]`), the features only feed counts, and the plan's baselines come from inv16_verify.
<a>/g1_requirements/inv16_under_only.py:18-22 (analytic, own footprint) is superseded by the recomposed `under` run that
the plan quotes. Because the lane-only blend is per px, `under` = `np.where(drawn, nowear, worn)` exactly.

**Decal on decal (`order=`)**: `None` = placement order; a subset (`[0]` = q0 alone) or a reorder (`[1, 0]`) recomputes
cores, `below_*`, `cov` and the `under_later_core` / `later_ring_over_core` rows of `inv16` (L387-411). The P2 metric
"earlier core under later alpha outside its footprint" is today's `later_ring_over_core.px` (q0_v4: 48,320).

### 3.4 P1(a) terms: inv16_terms(W, N, U, ...)

W, N, U = `compose(stack, lane="worn" | "nowear" | "under", **same other options)`. Per decal k of W:
`vis_k = fp_k & (a_k >= 0.999) & ~OR_{later j}(a_j > 0)` (= inv16's `vis`, L374; inv16_verify.py:174-181).

| key | formula | gate (plan acceptance[5..7]) | from |
|---|---|---|---|
| `swap.whole` {px, max_abs_mm, ptp_mm, minus_plane_max_abs_mm, albedo_luma_max, roughness_max} | `dH = W.H - N.H` over vis_k; `minus_plane_max_abs_mm = rk.plane_residual(dH, vis_k, p)["value"]` (float64 lstsq on [1, x_mm, y_mm]); luma via `luma255`; 4 decimals | `shape_ok`: minus_plane_max_abs_mm <= 1e-3, every decal | inv16_verify.py:184-191, 286-288 |
| `swap.under` {px, max_abs_mm, ptp_mm, albedo_luma_max, roughness_max, gated} | `W.H - U.H` over vis_k | `under_swap_ok`: all three <= 1e-4 at single-decal sites (p3, p1, q1); q0q3 reported | inv16_verify.py:290-291; verifier text "on single-decal sites" |
| `seat` {px, d_height_mm_p10_p50_p90, median_abs_mm, gated, ok} | ring = `(dist_out >= 2) & (dist_out <= 6) & (a_k >= seat_alpha_min) & ~later_draw(a_j > 0.002) & (below_cov_k < 0.5)` minus `seat_exclude` features; `d = h_d,k - H_below,k` (run W); percentiles, 2 decimals | `seat_ok`: abs(p50) <= 2.0 at p3_v4, p1_v4, q0_v4, q1_v3; q3_v4 reported | inv16_verify.py:211-214 |

`inv16_ok` under `--options p1` = legacy `inv16_ok` and `shape_ok` and (`under_swap_ok` where gated) and (`seat_ok`
where gated).
```python
P1_GATES = {"under_swap": {"p3_joint_v4", "p1_wpfatigue_v4", "q1_wp_v3"},    # site names
            "seat": {"p3_v4", "p1_v4", "q0_v4", "q1_v3"}}                     # decal tags
OPTIONS = {"r2": {"opacity": "export", "lref": "lane40", "terms": None},
           "p1": {"opacity": "export", "lref": "deform_med", "terms": ("shape", "under", "seat")}}   # P2 later: "aa"
WRONG_BUILDS = {"lref_worn40":   {**OPTIONS["p1"], "lref": "lane40"},     # must fail shape_ok
                "lref_nowear40": {**OPTIONS["p1"], "lref": "nowear40"}}   # must fail seat_ok at p1_v4 and q0_v4
```

Seat definition: the plan says "0.5-6 mm out, off crack/ravel", but every baseline and wrong-build number it quotes
(0.73/1.52/1.03/1.25; 1.63/1.37/0.74/0.59; 0.45/4.39/4.07/0.02) is inv16_verify's ring_vs_below (2-6 mm, alpha >=
0.998, sealant and cracks included; <a>/lead/g1v.txt:7). The spec follows inv16_verify. `seat_ring_mm=(0.5, 6.0),
seat_exclude=("crack", "crack_l", "crack_t", "ravel")` gives the plan's wording as a variant without baselines (§9).

### 3.5 T/composite.py (lane + detail, 178 lines): same split, no cache

Today: `ctx_of` :36, `opt` :41, `window` :48, `upsample` :56 (integer window, fixed-size bicubic), `lane_sites` :63,
`main` :88 (detail loads :104-109; per-site blend :126-152, shading :153-159 with an unpadded wrapping `pv.shadow_vis`,
4 PNGs :160-165; sheet :168-173). run_all.sh calls it 5 times (:34-37), 1024 px per 1 m (0.977 mm/px). Agents rebuilt
it three times (<a>/realism_onfoot/composite_probe.py:27, <a>/realism_onfoot_verify_b/composite_vb.py:194,
<a>/g5_tiling/composite_window.py; the last stays a lens job).

- Add `build_window(lc, det_wp, det_nwp, cy, cx, size=1.0, out_px=1024, wt_fn=None, lane_bc_override=None,
  extra_masks=()) -> dict(H, alb, rough, Wt, Wp, Lh, Lbc, q, dh, gain, masks, mm, n_lane)` as composite_vb.py:194-251,
  and `render_window(arrs, out, variant, name)` for :153-165. `main()` calls both; CLI and PNGs unchanged.
- No cache: the build is one 560 -> 1024 px upsample of ~9 planes and two crops per site (est. 1-2 s).
- Add `blend_lane_detail(Lh, Lbc, Lr, Wt, Sg, dbc, dmean, dh, dr) -> (H, alb, rough)` in composite.py with today's
  operation order; call it from composite.py:149-152 and composite_decal.py:466-470 (`build_site`), which keeps its
  `.astype(np.float32)` casts. Do not unify `upsample` vs `resample`, the site picks or the shadow padding (that would
  change round-1/2 images).

### 3.6 Tests: T/checks/test_composite_decal.py

Before editing, copy T/composite_decal.py to T/checks/legacy/composite_decal_r2.py and T/composite.py to
T/checks/legacy/composite_r2.py (frozen). In the legacy composite_decal: set `HERE` to T
(`os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`) and import `composite_r2 as cp`.

Run with `(cd "$T/checks" && "$PY" -m unittest -v test_composite_decal)` (stdlib unittest; the venv has no pytest). Test names start
`test_A<n>_` (e.g. `test_A7_terms_lane40`), so `-k A7` runs one.
Tests marked slow run only with `SDMR_SLOW=1`. Tests that need round-2 exports skip unless the newest mtime of
T/dump/asphalt_{lane,detail,decal}_* <= the mtime of T/review/round2/decal/composite/composite_decal.json (epoch
seconds). Old and new run on the same machine (cv2 / numpy builds move the last bits of G40).

| id | test | expected |
|---|---|---|
| A1 (slow) | JSON equality: new `main(["--out", tmp, "--cache", tmpc])` vs a fresh legacy run (`checks/legacy/composite_decal_r2.py --out tmp2`, ~92 s). The committed round-2 composite_decal.json is a cross-check only (diffs reported, not failed) | every key present today is present in both; numbers abs diff <= 1e-6; ints, strings, bools, null and list lengths equal; skip `seconds` (top level and per site); new keys only `options`, `cache` at the top level. Keys: top `what`, `mm_per_px`, `detail_presets_yr`, `sigma_ref_mm`, `sites`; per site `lane`, `lane_age_yr`, `lane_detail_preset`, `lane_px`, `pick`, `centre_world_mm`, `window_m`, `grid_px`, `mm_per_px`, `decals` (tag, offset_v_m + 9 preset fields), `height_span_mm`, `lane_only_height_span_mm`, `inv16`; per decal `tag`, `kind`, `offset_m`, `footprint_px`, `footprint_alpha_below_0.999_px`, `core_px`, `core_m2`, `tile_corner_world_mm`, `detail_presets_in_core`, `detail_presets_drawn`, `lane_features_under_core_px` (10), `leak` {px, albedo_luma, height_mm, roughness}, `later_ring_over_core` {px, max_abs_luma, median_luma_composite_minus_own, max_abs_height_mm} (q0_v4), `under_later_core` [{later, footprint_px, seam_px, seam_depth_mm_min, leak, own_maps_apart}] (q0_v4), `rim_band` {px, max_mm, min_mm, alpha_max_beyond_20mm, measured_on, ok}, `inv16_ok`, `ring_step` {ring_px, ring_luma, lane_px, lane_luma, step_luma}, `ring_vs_below` {class: px, ring_luma, below_luma, d_luma, d_height_mm} |
| A2 | spot values (tol 0.002 on rounded values; ints exact) | p1_v4 `ring_step.step_luma` -11.764; q0_v4 `later_ring_over_core.px` 48,320, `under_later_core[0].own_maps_apart.height_mm` 12.612045; p3_v4 `ring_vs_below.sealant.d_luma` 16.303; every `rim_band.max_mm` 19.7; every leak 0.0; height spans 59.1 / 134.02 / 54.12 / 26.58 mm (p3 / p1 / q0q3 / q1) |
| A3 (slow) | PNGs: q1_wp_v3 new vs legacy | the 6 PNGs and the one-row sheet decode to identical uint8 arrays |
| A4 | cache round trip: `build_site` in memory vs `load_stack(save_stack(...))` (q1_wp_v3) | every key equal (`np.array_equal`, same dtype); meta equal |
| A5 | staleness in a tmp folder with HERE patched (fake dump/checks/presets files, tiny arrays) | fresh after save; `os.utime(dump file, inputs_read_at + 10)` -> stale, reason names the file; `inputs_read_at - 100` -> fresh; a new `asphalt_decal_<tag>_x.png` -> stale; `build_version - 1`, p 0.5, an edited `spec` -> stale; `get_stack(on_stale="error")` raises `StaleCache` |
| A6 | profiles on the cache | `export` equals `d<k>/a`; `aa`: a == 1 on every fp px, max a at dist_out > 2 mm == 0 (P2 target <= 0.002); `narrow`: a == 1 at dist_out <= 0.5, 0 at >= 1.5, `rim_band.max_mm` <= 1.5; `rim_band_of(tile_a, ...)` == `meta.decals[k].rim_band` |
| A7 | P1 terms, `lref="lane40"` (tol 0.01 mm on 2-decimal, 1e-3 on 4-decimal values) | `swap.whole.minus_plane_max_abs_mm` p3 5.3602, p1 3.7604, q0 3.8384, q3 3.6826, q1 2.8709; `swap.whole.max_abs_mm` 5.4127 / 11.7789 / 10.8663 / 9.6025 / 5.3989; `swap.under.max_abs_mm` 3.394 / 10.106 / 10.8663 / 8.6016 / 5.0497; seat p10/p50/p90 p3 [-3.04, -0.73, 1.15], p1 [-4.25, -1.52, 5.22], q0 [-4.49, -1.03, 5.75], q3 [-2.56, -1.47, 6.05], q1 [-1.97, -1.25, 3.68]; `shape_ok` false everywhere (wrong build `lref_worn40`) |
| A8 | P1 terms, `lref="nowear40"` | whole and under swaps 0.0; seat p50 -0.45 / 4.39 / 4.07 / -0.02 / 0.02 (p3/p1/q0/q3/q1); `seat_ok` false at p1_v4 and q0_v4, true at p3_v4 and q1_v3 (wrong build `lref_nowear40`) |
| A9 | P1 terms, `lref="deform_med"` | `minus_plane_max_abs_mm` <= 1e-3 (0.0); whole max_abs (a pure offset, ptp 0.0) 1.2525 / 4.9684 / 4.6136 / 4.5799 / 0.0356; under 0.0 at p3/p1/q1, 1.6667 (q0) and 1.4142 (q3) reported; seat p50 -1.63 / -1.37 / -0.74 / -5.09 / -0.59; `inv16_ok` (p1) true at every site |
| A10 | exit code and caller | `main` returns 1 when a monkeypatched `inv16` reports `inv16_ok` false; run_all.sh still contains the line `(cd "$T" && "$PY" composite_decal.py --out "review/$R/decal/composite") \|\| fail=1` |
| A11 (slow) | timing (report; fails only above 3x the target) | `--build-only` all four <= 90 s; per site from cache: `compose` <= 1 s, `compose` + `inv16` <= 4 s, P1 terms <= 10 s; logged from `build_seconds` and `time.perf_counter` |
| A12 (slow) | composite.py refactor: `composite.py --lane lane_v3.json --wp detail_v3_wp.json --nwp detail_v3_nwp.json --out tmp` vs `legacy/composite_r2.py` with the same arguments | every PNG decodes to identical uint8 arrays |

A7-A9 numbers are <a>/g1_requirements_verify_a/inv16_verify.json (`lp40`, `lp40_now`, `deform_med`; same grid and
sites), which the plan's acceptance rows quote.

## 4. checks/review_kit.py: the shared measurement toolkit (brief change 1, second half)

### 4.0 Rules for the module

- One file, T/checks/review_kit.py. Imports: os, sys, json, math, time, numpy, scipy.ndimage, cv2, and `matcheck as mc`
  from `~/.claude/skills/sd-material-research/scripts` (the same `SK` path and `sys.path.insert` as the top of
  checks/decal_extra.py).
- The thread cap of §0.4 item 9 comes first, before numpy is imported.
- Functions take arrays (plus mm per px) and return a dict of plain Python floats and ints, unrounded. Key `value` holds
  the number the plan row reads; other keys are details. Functions that can return maps take `return_maps=False` and add
  `maps` only when it is True.
- No targets in the kit; thresholds stay in the callers. The only thresholds in the file are self-test tolerances.
- No file writes, no Designer calls, no network. `--selftest` prints to stdout only.
- The kit imports none of accept_r1.py, decal_extra.py, composite_decal.py; they import it.

### 4.1 Conventions

| item | rule |
|---|---|
| grids | decal, detail, composite: `MM_TILE = 1000/2048 = 0.48828` mm/px. Lane: `MM_LANE = 3660/2048 = 1.78711` mm/px (`ctx.mmx`). Use `ctx.mm` from the config; the constants only in self-tests. |
| axes | axis 0 = rows, axis 1 = columns. On the lane, columns = U (across), rows = V (along); `u_mm = (col + 0.5) * mm`. |
| arrays | maps float64 (H, W), except luma float32 as matcheck returns it; masks bool from `gray >= 0.5` unless a row says otherwise; colour (H, W, 3). |
| height | mm, positive up: `ctx.height_mm()` = raw x `height_depth_mm`. Removal `rem = h_nowear - h` (>= 0 in a hole). `h_rel = h - surface_level * height_depth_mm`. |
| luma | sRGB 0-255: `ctx.map_values("basecolor", "srgb255", "luma")` (`mc.LUMA` = 0.2126, 0.7152, 0.0722). The composite has linear albedo; `luma255` encodes sRGB first, then weights. |
| angles | degrees, radians internally. |
| wrap | lane and detail tile: `mc.wrap_edt` / `mc.label_wrap` / `mc.gaussian_wrap` (matcheck.py:166, 205, 278). Decal footprints stay >= 100 mm from the border, so decal code uses plain `ndi.distance_transform_edt`, as all decal prior art does. Each function takes `wrap: bool`, default as its prior art. |

Distance from an outline (the prior art disagrees):

| script | inside | outside |
|---|---|---|
| <a>/g1_requirements_verify_b/f5_wall.py:`inside_mm` | (EDT(fp) - 0.5)+ x mm | - |
| <a>/decal_potholes_verify_a/va1_rim.py:`analyse` | EDT(fp) x mm | (EDT(~fp) - 0.5)+ x mm |
| fixcheck/wall_wrongbuild.py, fixcheck_verify/wall_verify.py, decal_potholes_verify_b/v1b_walls_hp.py | EDT(fp) x mm | - |
| decal_patches/a6_edge_width.py | EDT(fp) x mm | EDT(~fp) x mm |
| SK/matcheck.py:1257 `signed_distance_mm` | EDT - 0.5 | -(EDT - 0.5) |

The kit uses the true distance from the 0.5 contour on both sides, `(EDT - 0.5)+ x mm`: it matches matcheck's
`signed_distance_mm` (so `opacity_border`), composite_decal's `dist_out` (L416), and the plan's "true inside distance
1.5 mm" (rim_drop_1p5mm, f5_wall). Two exceptions keep their baselines: `wall_comb_hp` and `wall_top_depths` use
EDT x mm, as v1b and v1_walls do (only directions and ray starts depend on it there). The wrong-build generators take
whatever distance the caller passes; wrong_builds.py passes EDT x mm, the builder's `DH_wall` convention.

### 4.2 Plan rows -> kit functions

"matcheck" = a JSON check row from gen_checks.py, no kit function. "§9" = no prior art pinned (open point 7).

| plan row (P#, kind) | kit function | caller | prior art (`<a>/`) |
|---|---|---|---|
| footprint_solid (P1, hard) | matcheck components; `fp_holes`, `island_slit` for tests | gen_checks.py, wrong_builds.py | g1_requirements/fp_holes.py, r6_wrong.py (B) |
| rim_drop_1p5mm (P1, hard) | `inside_profile` -> `removal_at_d_1p5mm` | decal_extra.py (hard-counted) | g1_requirements_verify_b/f5_wall.py:`profile` |
| pothole_wall_depth (P1, soft) | `inside_profile` -> `near_vertical_depth_mm` | decal_extra.py | f5_wall.py:`profile` |
| lip / bevel wrong builds (P1) | `cone_removal`, `lip_cut`, `bevel_removal`, `height_raw` | wrong_builds.py, self-test | fixcheck/wall_wrongbuild.py, fixcheck_verify/wall_verify.py:`lip`, r6_wrong.py (D) |
| agg_tips_kept tol -0.1 (P1, hard) | matcheck | gen_checks.py, wrong_builds.py | lead/lead_measure.py:39 |
| opacity_core 0.999, opacity_border 2 mm (P1/P2, hard) | matcheck | gen_checks.py | - |
| inv16 shape / under swap / seat (P1, hard) | `plane_residual`, `ring_median` | composite_decal.py `inv16_terms` (§3.4) | plan P1 (a) |
| area-mean composite - beneath 2-20 mm (P2) | `area_mean_step` | composite_decal.py | decal_patches_verify_a/v3_rim.py:`lumlin`, `numbers` |
| band_colour_0_2mm p90 (P2) | `band_colour_abs` | composite_decal.py | decal_potholes_verify_a/va1c_band_colour.py |
| rendered_crack_relief_0_20mm (P2) | `rendered_relief_share` | composite_decal.py | va1_rim.py:`analyse` (B) |
| P3 sealant_visible_0_20mm (P2) | `visible_share` | composite_decal.py | va1_rim.py:`analyse` (D) |
| earlier core under later alpha (P2) | `stack_leak_px` | composite_decal.py | v3_rim.py:`q0q3` |
| colour_aa_rim (P2) | `aa_share` (moves from decal_extra.py:63) | decal_extra.py | decal_extra.py:`aa_share` |
| rim_colour_width p50 (P2) | `edge_crossing_stats` | decal_extra.py | decal_potholes_verify_a/va2_aa.py:`crossings`, `profiles`, `stats` |
| rim_edge_jaggedness (P2) | `edge_jaggedness` | decal_extra.py | va2_aa.py:`stair` |
| seam_lip_registration (P2) | `lip_registration` | decal_extra.py | decal_patches_verify_b/v3_lip.py:`crossings` |
| outline_band_10_30 (P2) | `outline_spectrum` | decal_extra.py | decal_patches_verify_b/v1_outline.py:`radial`, `band_rms`, `round_shape` |
| tight_bends (P2) | `curvature_shares` | decal_extra.py | v1_outline.py:`curvature_share` |
| saw-side control (P2) | `straight_side_rms` | decal_extra.py (report) | v1_outline.py:`saw_sides` |
| patch_covers_hole (Q2, P0) (P2) | `cover` | decal_extra.py | v1_outline.py:`cover` |
| wall_comb_hp (P3) | `wall_comb_hp` | decal_extra.py | decal_potholes_verify_b/v1b_walls_hp.py ("built") |
| wall_top_spread (P3) | `wall_top_depths` | decal_extra.py | decal_potholes_verify_b/v1_walls.py:28-29, 104-128 |
| bowl_facets: IQR_s3, azimuth (P3) | `bowl_mask`, `bowl_metrics` | decal_extra.py | decal_potholes_verify_b/v2_bowl.py:`metrics` |
| bowl_facets risers up-inward (P3) | §9 | - | decal_potholes_verify_b/write_result.py:100-118 (text only) |
| mpd_v0 (P4) | `mpd` | accept_r1.py | realism_onfoot_verify_a/mpdlib.py |
| stone wall width p50 (P4) | `stone_table` | accept_r1.py | realism_onfoot_verify_a/f1_stones.py, geom.py |
| agg_protrusion V0, stone_top_spread_mm (P4) | matcheck / accept_r1.py:1025 (unchanged) | - | - |
| mastic ring - open floor, rim + 3 mm skirt slope (P4) | §9 | - | - |
| oil_deficit_step_sym (P5) | `col_mean`, `sym_deficit_step` | accept_r1.py | lead/lead_measure.py (C) |
| V1 along-V landmarks, V2 oil residual (P5) | `along_v_landmarks` | accept_r1.py | g5_tiling_verify/v1_oil.py:`landmarks` |
| oil_drop_area_share 20-100, share > 200 mm (P5) | `oil_morph` | accept_r1.py | v1_oil.py:`morph` |
| oil_plate_share, flooded cells, open-wall luma, open-crack share (P5) | §9 | - | - |
| spall_luma_minus_ring -10 (P5) | accept_r1.py:711 `m_spall` (target only) | accept_r1.py | - |
| joint_spall_darker (P5, hard) | matcheck value_order; `paired_delta` to verify | gen_checks.py | g1_requirements_verify_b/f4_joint_spall.py |
| cold_edge_step_local, cold_edge_registration, band-side shares (P6) | `cold_edge_rows` | accept_r1.py | realism_lane_verify_a/v_edgestep.py, realism_lane/fins_wall.py:38-63 |
| V4 gap floor - nowear (P6) | `paired_delta` | accept_r1.py | f4_joint_spall.py |
| band albedo edge 10-90 %, band width std / wander (P6) | §9 | - | - |
| granite speckled share, on-foot share (P7) | `granite_specks` | accept_r1.py | realism_onfoot_verify_b/f5_granite.py |
| fines/mastic hp3 ratio (P7) | `hp_std_ratio` | accept_r1.py | realism_onfoot_verify_b/f6_fines.py |
| plain-stone within std p50 (P7) | accept_r1.py:920 `d_onfoot_std` (unchanged) | - | - |
| crown_lump_std (P1e / Q7) | `crown_params`, `crown_lump_std` | decal_extra.py | decal_patches_verify_b/v4b_plateau.py:14-27 |
| seam_floor_std, seam_dirty_share (P8) | `seam_bins` | decal_extra.py | decal_patches_verify_b/v2_seam.py:36-80 |
| seam_spall_share, face_relief_ratio, debris_top_follows_floor, base fines-gap, Q3/Q0 kerf (P8/P2) | §9 | - | - |

Crack wall and fill masks (in the brief's kit list) stay in accept_r1.py (regions `a_crack`, `a_crack_open`,
`spall_mask` at :696); no plan row needs them in the kit.

### 4.3 Loaders (thin, optional)

```python
def load_decal(tag, checks_dir=HERE) -> dict
def load_lane(v, checks_dir=HERE) -> dict
def load_detail(tag, checks_dir=HERE) -> dict
def preset(graph, tag) -> dict      # build/presets.json["asphalt_" + graph], entry["tag"] == tag -> entry["values"]
```

| key | load_decal (checks/decal_<tag>.json) | load_lane (checks/lane_<v>.json) | load_detail (checks/detail_<tag>.json) |
|---|---|---|---|
| `ctx` | `mc.Ctx(cfg, checks_dir)` | same | same |
| `v` | `preset("decal", tag)` | `preset("lane", v)` | `preset("detail", tag)` |
| `mm` | `ctx.mm` (0.48828) | `ctx.mmx` (1.78711) | `ctx.mm` |
| `h`, `h0` | `height_mm()`, `height_mm("nowear")`, float64 mm | same | `h` only |
| `lum`, `lum0` | basecolor srgb255 luma (main, nowear) | same | `lum` |
| masks (bool) | `pot`, `pat`, `seam` = gray(name) >= 0.5 | `sealant`, `ravel`, `crack`, `oil`, `pumping`, `dirt` | `socket` >= 0.5, `deposit` >= 0.5 |
| soft | `pot_soft`, `pat_soft`, `opacity`, `debris`, `layer_index` (float64 0-1) | `oil_soft` | `sid` = gray("stone_id") float64 |
| derived | `rem = max(h0 - h, 0)`, `h_rel = h - surface_level * height_depth_mm` | `u_mm` (W,) | `bc` = map("basecolor")[..., :3] float64 sRGB 0-1 |

Decal map names are composite_decal.py:74 `DECAL_MASKS`. A name missing from a config raises `mc.ConfigError`.

### 4.4 Functions

#### 4.4.1 Distances, bands, plane

```python
def true_dist(mask, mm, wrap=False, reach_mm=200.0) -> (d_in, d_out)   # float64 mm, 0 on the other side
def bands(mask, mm, edges_mm, side="out", exclude=None, wrap=False, d=None) -> {"lo-hi": bool}
def plane_residual(dH, mask, mm) -> {"value": max|dH - plane|, "std", "coef": [a, b, c]}
def ring_median(v, fp, mm, lo=20.0, hi=40.0, valid=None, d_out=None) -> {"value": median, "px"}
```
- `true_dist`: `d_in = max(EDT(mask) - 0.5, 0) * mm` on the mask; `d_out = max(EDT(~mask) - 0.5, 0) * mm` off it. With
  wrap=True: `mc.wrap_edt(~mask, reach_mm / mm)` for d_in and `mc.wrap_edt(mask, ...)` for d_out; values beyond the
  reach are invalid, as in matcheck.
- `bands`: for each (lo, hi), the px with lo < d <= hi on `side` ("out": d_out off the mask; "in": d_in on it), minus
  `exclude`. Key `"%g-%g" % (lo, hi)`. The first outside ring has d = 0.5 x mm > 0, so it falls in "0-2". `d` passes a
  precomputed distance for that side.
- `plane_residual`: least squares `a + b*x + c*y` (x, y in mm at pixel centres, float64 `np.linalg.lstsq`) over the
  mask; residual over the mask. The inv16 shape term.
- `ring_median`: median of v over `bands(fp, mm, [(lo, hi)], "out", d=d_out)` & valid. Used for the P1 L_ref offset
  (ring 20-40 mm, alpha <= 0.002) and the seat term.

#### 4.4.2 Edges and outlines (decals)

```python
def aa_share(vals, mask, min_step) -> (share | None, n_crossings)            # verbatim decal_extra.py:63-78
def edge_crossings(mask) -> [(axis, ys, xs, inside_after), ...]             # verbatim va2_aa.py:crossings
def crossing_profiles(vals, crossings, half=4) -> (N, 2*half) float64        # verbatim va2_aa.py:profiles
def edge_crossing_stats(vals, mask, floor, half=4) -> dict
def edge_jaggedness(vals, mask, floor) -> {"value": std_px, "n": rows}       # verbatim va2_aa.py:stair
def lip_registration(h_rel, lum, m_soft, drop_mm=2.0, out_px=3, grad_share=0.7, lum_floor=8.0) -> dict
```
- `aa_share`: for each row or column crossing of the mask edge, luma at p-1..p+2; step = v(p+2) - v(p-1); a crossing
  counts when |step| >= min_step; "hard" when |v(p+1) - v(p)| / |step| >= 0.85; returns 1 - hard/total. Uses `np.roll`
  (wraps). colour_aa_rim: vals = luma, mask = pothole, min_step 4. decal_extra.py keeps `aa_share = rk.aa_share`.
- `edge_crossing_stats`: profiles oriented outside -> inside, 8 px (p-3..p+4). lo = mean of the first 2 px, hi = mean
  of the last 2, d = hi - lo; crossings with |d| < floor dropped; fewer than 20 kept -> `value None`. t = (P - lo)/d;
  inter = count of 0.1 < t < 0.9; pos(level) = first index with t >= level, linearly interpolated with the previous
  sample; w1090 = pos(0.9) - pos(0.1) px. Keys: `n`, `share_with_intermediate_px`, `inter_px_mean`, `w1090_px_p50`
  (= `value`), `w1090_px_p90`, `share_w1090_le_2px`, `step_p50` (median |d|, the colour step). Floors (va2): luma 10,
  roughness 0.02, height 1 mm, mask 0.5. rim_colour_width: luma, mask = pothole, floor 10.
- `edge_jaggedness`: row crossings only, left edges (inside to the right), leftmost per row; profile at offsets -3..+4;
  edge e = sub-px 0.5 crossing of t between samples k-1 and k, k = clip(argmax(t >= 0.5), 1, 7). Runs break where
  consecutive rows differ by more than 1 or |dx| > 3 px; runs shorter than 15 rows are skipped. Result = std over all
  runs of `e - median_filter(e, 9, mode="nearest")`. Row: rim_edge_jaggedness (luma, floor 10).
- `lip_registration` (port of v3_lip.py:21-78; m_soft = the footprint's soft mask, clipped 0-1: `patch` for patches,
  `pothole` for potholes; h_rel in mm, lum = srgb255 luma, all float64): (gy, gx) = np.gradient(m); for each axis and
  both scan directions, crossings j with m[j] < 0.5 <= m[j+1], 5 < j < W - 8, and |d_axis m| / |∇m| >= 0.7 at j or
  j+1. xm = j + (0.5 - m[j]) / max(m[j+1] - m[j], 1e-9). hout = h[j - 3]; tgt = hout - 2; window h[j-2 .. j+5];
  a crossing is kept ("has") when some window sample <= tgt, h[j-2] > tgt and min(window) <= hout - 3. k = max(first
  index <= tgt, 1); xh = (j - 2 + k - 1) + (h0 - tgt) / max(h0 - h1, 1e-9) with h0, h1 = window[k-1], window[k].
  one_pair = (h0 - h1) >= 0.85 (hout - min(window)). Luma: lo = lum[j-3], li = lum[j+4], lt = (lo + li)/2; first
  window index kl (>= 1) where (lum - lt) sign(li - lo) >= 0; xl = (j - 2 + kl - 1) + clip((lt - l0)/(l1 - l0), 0, 1);
  colour kept where has & |li - lo| >= 8. Keys: `n_h`, `n_l`, `value` = `std_xh_minus_xm_px`, `mean_xh_minus_xm_px`,
  `std_frac_xh`, `share_drop_in_one_pair`, `colour` = `std_xl_minus_xm_px`, `mean_xl_minus_xm_px` (None without colour
  crossings). Plan targets: height <= 0.15 px, colour <= 0.25 px on curved outlines.

```python
def radial_outline(m, nth=8192, step=0.2) -> {"th", "r_px", "grad", "cy", "cx"}   # verbatim v1_outline.py:radial
def band_rms(sig, L_mm, bands=BANDS) -> {"1-4": mm, ...}                         # verbatim v1_outline.py:band_rms
def curvature_shares(x_px, y_px, mm, sig_mm=1.5, step_mm=0.25) -> dict           # verbatim v1_outline.py:curvature_share
def outline_spectrum(m, mm, nth=8192) -> dict                                    # v1_outline.py:round_shape
def straight_side_rms(m, mm, inset_px=20) -> dict                                # verbatim v1_outline.py:saw_sides
def cover(P, Q, mm, q_opacity=None, search_px=40, step_px=2) -> dict             # v1_outline.py:cover + opacity
BANDS = ((1, 4), (4, 10), (10, 30), (30, 100))   # wavelength mm along the perimeter
```
- `radial_outline`: m = soft mask (clipped 0-1, float64). nth rays from the centroid of m >= 0.5, bilinear samples
  (map_coordinates order 1) every 0.2 px up to 0.98 x the nearest-border distance; the outermost 0.5 crossing by linear
  interpolation. `grad` = |∇m| there. Assumes a star-shaped outline (true for every decal).
- `outline_spectrum`: x = cx + cos(th) r, y = cy + sin(th) r; segment lengths sum to the perimeter L (mm). r resampled
  uniformly in arc length to 16384 samples, then `band_rms`: rfft of r - mean, p = |F|² / n² x 2, lambda_k = L/k,
  RMS = sqrt(sum p for lambda in [lo, hi)). Keys: `perimeter_mm`, `r_mean_mm`, `band_rms_mm`, `feather_10_90_px`
  {p10, p50, p90, cv} of 0.8/|∇m|, `curvature`. `value` = band_rms_mm["10-30"].
- `curvature_shares`: resample the closed curve every 0.25 mm of arc, gaussian_filter1d (sigma 1.5 mm, wrap), k = |x'y''
  - y'x''| / (x'² + y'²)^1.5. Keys `R_lt5`, `R_lt10` (= `value`, tight_bends), `R_lt20` (share with k > 1/R),
  `perimeter_mm`.
- `straight_side_rms`: per bbox side (inset 20 px from the corners) the sub-px 0.5 crossing per row or column,
  detrended linearly -> `rms_mm`; all sides concatenated through `band_rms`. The saw-cut control (round 2: 0.000 in 10-30).
- `cover`: P = earlier opening (p0_v3 `pothole` >= 0.5), Q = later patch (q2_v4 `patch` >= 0.5); the tiles share a
  centre by construction. Keys: `P_px`, `P_outside_Q_px` (= `value`), `P_outside_share`, `max_beyond_Q_mm`,
  `min_margin_mm_centred`, `best_shift` {min_margin_mm, dy_mm, dx_mm}; with q_opacity, `P_under_low_opacity_px` =
  count(P & q_opacity < 0.998). The shift scan maximises P's minimum signed margin (inside +) over its boundary px. No
  bounds check (P's boundary is >= 205 px from the border).

```python
def fp_holes(fp, mm, opacity=None) -> {"components", "hole_px", "closing3mm_adds_px", "opacity_min_filled", ...}
def island_slit(fp, mm, centre_yx, island_mm=40.0, slit_mm=3.0, angle_deg=0.0) -> fp_wrong (bool)
```
- `fp_holes` (verbatim fp_holes.py): components = `ndi.label(fp)[1]` (4-connected); hole_px = (binary_fill_holes(fp) &
  ~fp).sum(); closing3mm_adds_px with `binary_closing(3x3, iterations=round(3/mm))`. matcheck's components (used by
  footprint_solid) are 8-connected, so a diagonal-only cut splits under 4 only; the self-test uses a 6 px slit.
- `island_slit`: fp with a disc of `island_mm` diameter at `centre_yx` set False, and a `slit_mm`-wide straight band
  from the centre past the outline at `angle_deg` set False (r6_wrong.py B: "a 40 mm island and a 3 mm slit where DL_fp
  is 0"). Read r6_wrong.py B when porting so wrong_builds.py's placement matches its 7/7 readings.

#### 4.4.3 Composite rim bands (P2; arrays from §3's cache)

```python
def lin_to_srgb(c)        # c <= 0.0031308: 12.92 c; else 1.055 c**(1/2.4) - 0.055
def meanlin_luma(alb_lin, m) -> float            # 255 * lin_to_srgb(mean over m of alb_lin (3,)) @ LUMA  (v3_rim.py:lumlin)
def area_mean_step(alb_comp_lin, alb_beneath_lin, fp, mm, lo=2.0, hi=20.0, valid=None) -> dict
def band_colour_abs(lum_comp, lum_lane, fp, mm, lo=0.0, hi=2.0, by=None) -> dict
def local_ref(v, valid, sigma_px) -> float64     # verbatim va1_rim.py:local_ref (reflect mode)
def rendered_relief_share(H_comp, H_lane, crack, plain_ok, fp, mm, lo=0.0, hi=20.0, sigma_mm=8.0, alpha=None) -> dict
def visible_share(alpha, feature, fp, mm, lo=0.0, hi=20.0) -> dict
def stack_leak_px(fp_early, alpha_late, fp_late) -> {"value": int}
```
Inputs: `alb_*_lin` (H, W, 3) float32 linear; `lum_*` (H, W) sRGB luma 0-255 (composite `luma255`); `H_*` mm; `alpha`
float32 0-1; `fp` = `pothole | patch` >= 0.5 on the 0.48828 mm grid; `valid` = px no later decal draws over.
- `area_mean_step`: band = `bands(fp, mm, [(lo, hi)], "out")` & valid; `value` = meanlin_luma(comp, band) -
  meanlin_luma(beneath, band), signed. Plan target |value| <= 1.
- `band_colour_abs`: x = |lum_comp - lum_lane| over (0, 2] mm out; `value` = p90; also p50, `n_gt6`, and per-feature
  {p50, p90} for each bool mask in `by` (va1c: sealant, crack, pumping, plain).
- `rendered_relief_share`: refH = local_ref(H_lane, plain_ok, 8 mm / mm); cm = band & crack; `value` =
  Σ(H_comp - refH)[cm] / Σ(H_lane - refH)[cm], None without crack px. crack = max(crack, crack_l, crack_t) >= 0.5 of the
  lane layer; plain_ok = ~crack & ~sealant. With alpha: `alpha_weighted_visible` = Σ(1 - alpha)[cm] / n.
- `visible_share`: `value` = mean(1 - alpha) over band & feature (P3: feature = lane sealant >= 0.5).
- `stack_leak_px`: count(fp_early & alpha_late > 0 & ~fp_late) (round 2 Q0 under Q3: 48,320; target <= 4,832).

#### 4.4.4 Pothole walls and bowls (P1, P3)

```python
def inside_profile(rem, fp, mm, exclude=None, max_mm=80.0, bin_mm=0.25) -> dict     # f5_wall.py:profile
def wall_comb_hp(rem, fp, mm, wall_mm) -> dict                                      # v1b_walls_hp.py "built"
def wall_top_depths(rem, fp, soft, mm, wall_mm, every=2) -> dict                    # v1_walls.py:28-29, 104-128
def bowl_mask(rem, fp, mm, wall_mm, debris) -> bool
def bowl_metrics(rem, bowl, mm, bowl_deg, phi) -> dict                              # verbatim v2_bowl.py:metrics
def slope(z, mm) -> (deg, gx, gy)                                                   # vb_common.py:slope
```
- `inside_profile`: d = true inside distance; sel = fp & ~exclude & d < max_mm; bins of 0.25 mm; per-bin median by
  `mc.grouped_median` (matcheck.py:296); x = bin centres, NaN bins dropped. sm = uniform_filter1d(med, 4) (1 mm),
  slope = np.gradient(sm, x); i0 = argmax slope over x < 6 mm; j = first index >= i0 with slope < tan 60° (else the
  last). Keys: `near_vertical_depth_mm` = sm[j], `at_d_mm` = x[j], `removal_at_d_1mm`, `removal_at_d_1p5mm`,
  `removal_at_d_2mm`, `removal_at_d_5mm` = np.interp(d, x, med) (unsmoothed). rem = max(h0 - h, 0); exclude =
  `ctx.region("debris_any")`, as f5_wall reads it. Rows: rim_drop_1p5mm (hard, >= 6 mm) and pothole_wall_depth (soft,
  >= 0.75 x wall_mm). wall_verify.py:`wall_metrics` gives other numbers; the spec follows f5_wall because the plan's
  baselines are f5_wall's.
- `wall_comb_hp`: dmm = EDT(fp) x mm; wpx = fp & dmm > 0.5 & dmm < wall_mm/5.7 - 0.3; ref = arctan2 of
  np.gradient(gaussian_filter(dmm, 3 px)) (gy, gx order); (gy, gx) = np.gradient(rem, mm); a = wrap(arctan2(gy, gx) -
  ref) into [-π, π); hp = a - mgauss(a, wpx, 3 px), mgauss(a, m, s) = G_s(where(m, a, 0)) / max(G_s(m), 1e-9).
  `value` = degrees(median |hp[wpx]|); also `p90`. Target <= 2.
- `wall_top_depths` (v1_walls): soft = the pothole soft mask (`pot_soft`, gray("pothole") float64, as
  vb_common.py:29). sm = gaussian_filter(soft, 3.0 px); (ry, rx) = np.gradient(sm). Ray starts: every 2nd px of
  edge = fp & ~binary_erosion(fp) (np.nonzero order); (ny, nx) = (ry, rx) at the start, divided by hypot + 1e-12.
  Samples at steps np.arange(0, 40, 0.25) px along the ray (map_coordinates order 1, mode "nearest") of rem; then
  uniform_filter1d(3) along the ray, dz = gradient(zr, 0.25 x mm), sl = degrees(arctan(max(dz, 0))). Per ray: the first
  sample with sl > 70, then the first later one with sl < 65; top = zr there. Rays without both are dropped. `value` =
  (p95 - p05) of top / wall_mm; also q05..q95 and std. Target >= 0.4.
- `bowl_mask` (v1b): fp & rem > wall_mm + 2 & rem < p99(rem[fp]) - 3 & debris < 0.05 & dmm > wall_mm/5.7 + 8.
  `phi` = arctan2 of np.gradient(gaussian_filter(dmm, 8 px)) (v1b `refb`).
- `bowl_metrics` keys: `planarity_raw_pm3` (= decal_extra bowl_planarity, now a report row), `slope_iqr_s3` (slope IQR
  after a sigma 3 mm Gaussian), `planarity_s3_pm3`, `normal_dev_s6_p50`/`p75` (angle of the sigma-6 mm normal from the
  ideal cone normal [tan b cos phi, tan b sin phi, 1]), `azimuth_dev_s6_p50`, `floorlike_share_s3_lt15deg`, `bowl_px`.
  bowl_facets reads `slope_iqr_s3` (>= 6) and `azimuth_dev_s6_p50` (>= 3).

Wrong-build generators (z = removal in mm):
```python
def cone_removal(d_mm, k_wall=5.7, lip_mm=20.0, bowl_deg=45.0, depth_mm=60.0):
    z = np.minimum(k_wall * d_mm, lip_mm + np.tan(np.radians(bowl_deg)) * np.maximum(d_mm - lip_mm / k_wall, 0))
    return np.minimum(z, depth_mm) * (d_mm > 0)                       # fixcheck/wall_wrongbuild.py
def lip_cut(depth, d_mm, fp, L, bowl_deg):                            # fixcheck_verify/wall_verify.py:lip
    lip = np.where(d_mm < L / 5.7, 5.7 * d_mm, L + np.tan(np.radians(bowl_deg)) * (d_mm - L / 5.7))
    return np.where(fp, np.minimum(depth, lip), depth)
def bevel_removal(depth, d_mm, fp, top_mm=5.0, deg=60.0):             # r6_wrong.py D, "top 5 mm at 60 deg"
    t = np.tan(np.radians(deg)); z = np.where(d_mm < top_mm / t, t * d_mm, top_mm + 5.7 * (d_mm - top_mm / t))
    return np.where(fp, np.minimum(depth, z), depth)
def height_raw(z_mm, surface_level, depth_mm, fp):                    # wall_wrongbuild.py
    return np.clip(surface_level - np.where(fp, z_mm, 0) / depth_mm, 0, 1).astype(np.float32)
```
Normals for a wrong build come from wrong_builds.py:117 `normal_from(ctx, h_units, green=-1.0)`, swapped in with
wrong_builds.py:52 `Swap`.

#### 4.4.5 Crowns and seams (P1e, P8)

```python
def crown_params(v) -> (ramp_mm, w_mm)          # v = the decal preset values
def crown_lump_std(crown_mm, pat, seam, mm, ramp_mm, w_mm) -> dict   # v4b_plateau.py:14-27
def seam_bins(h_rel, lum, pat_soft, seam, mm, bin_mm=10.0) -> dict   # v2_seam.py:36-80
```
- `crown_params` (v4b_plateau.py:19-21): `w_mm = min(10, seam_mm_per_year x max(0, patch_age_years - 3))`; `ramp_mm =
  30 + (min(120, max(40, 0.2 x size_mm)) - 30) x (kind == 2)`.
- `crown_lump_std`: din = EDT(pat) x mm; dseam = EDT(~seam) x mm (1e9 without a seam); plateau = pat & din > ramp_mm +
  15 & dseam > 1.6 w_mm + 30 (v4b_plateau.py:22; v4_targets.py:51 uses `wmax + 4` instead, a different table). `value`
  = std(crown_mm[plateau]); also `plateau_px`. crown_mm = h_rel. Target >= 0.15 mm (Q7).
- `seam_bins`: `radial_outline(pat_soft, nth=4096)` gives the perimeter; nb = int(perimeter/10). A seam px's bin =
  floor(angle about (cy, cx) / 2π x nb). Per bin with >= 8 px: floor = p02(h_rel); dirty = median(lum of px with h_rel
  <= p25) > 85; width = n x mm² / bin arc length. Keys: `floor_std_mm` (= `value`, seam_floor_std >= 0.5 at PA >= 6),
  `dirty_bin_share` (seam_dirty_share, within +-0.15 of clamp((PA - 3) x 0.06, 0, 0.8)), `width_cv`, `bins`.

#### 4.4.6 Lane profiles (P5, P6)

```python
def col_mean(v, surf) -> (W,) float64            # Σ_rows where(surf, v, 0) / max(Σ surf, 1)  (= accept_r1.py:794)
def sym_deficit_step(p, pn, mm, centre_mm=1830.0, half_mm=600.0, step_mm=50.0, sigma_mm=15.0, R_mm=620.0) -> dict
def oil_morph(m, mm, band) -> dict               # verbatim v1_oil.py:morph
def along_v_landmarks(L, mm, band, thr=(6.0, 8.0), min_m2=0.02, sigma_mm=50.0) -> (dict, r)   # v1_oil.py:landmarks
def cold_edge_rows(h, h0, S, R, mm, t_mm, d_mm, cols=400, windows_mm=((0, 4), (4, 8), (12, 20))) -> dict
def paired_delta(a, a_ref, mask) -> {"value": median(a - a_ref), "mean", "n"}
```
- `sym_deficit_step` (lead/lead_measure.py C, lines 68-94): dfc = gaussian_filter1d(p - pn, sigma/mm, mode="wrap");
  u = (i + 0.5) mm; i0 = argmin|u - 1830|; A = -dfc[i0]; n = int(600/mm); k = round(50/mm); left = dfc[(i0 - arange(n +
  k + 1)) % N], right = dfc[(i0 + arange(n + k + 1)) % N]; sym = (left + right)/2. Keys: `sym_step` (= `value`) =
  max|sym[k:k+n] - sym[:n]|, `left_step`, `right_step`, `A`, `biweight_step` = 1.54 A x 50/620, `ceiling` = max(3,
  1.3 x biweight_step). Inputs: p = col_mean(luma V, surf), pn = col_mean(luma nowear, surf), surf = accept_r1 region
  `a_surface_d10` (passed in). Three scripts disagree; the spec follows the lead, because the plan's baselines and
  ceilings are the lead's numbers and Q4 adopted them:

  | script | smoothing | surf | centre / window |
  |---|---|---|---|
  | lead_measure.py (C) | sigma 15 mm, wrap | a_surface_d10 | i0 = argmin\|u - 1830\|, n + k + 1 samples, modulo |
  | realism_lane_verify_b/oil_v3.py | sigma 15 and 30 mm, no wrap | ~(crack, sealant, ravel, pumping, dirt), undilated | round(1830/mm - 0.5), n samples |
  | accept_r1.py:812 m_oil_lateral | none (raw, not symmetrised) | a_surface_d10 | max_change at 1455 / 2205 +- 150 mm |

  m_oil_lateral and m_oil_soft_edge stay as report rows.
- `oil_morph`: `mc.label_wrap(m, 8)`; eqd = 2 sqrt(cnt/π) x mm. Keys: `cover_tile`, `cover_band`, `n_components`,
  `share_20_100mm`, `share_gt_200mm`, `share_lt_20mm` (area shares), `largest_eqd_mm` (top 4), `count_median_eqd_mm`
  (eqd >= 5), `area_weighted_median_eqd_mm`. m = mask_oil >= 0.5; band = (U >= 1455) & (U <= 2205) mm (v1_oil.py:36).
- `along_v_landmarks`: B = mc.gaussian_wrap(L, 50 mm/mm); r = B - median over rows of B (per column; removes every
  lateral band); rb = r inside the band, else 0. For each T, wrapped 8-connected components of rb <= -T with area >=
  0.02 m². Keys: `min_r`, `rsd_band` (1.4826 MAD), `n_le_<T>`, `comps_le_<T>` (u_mm, v_mm, area_m2, min_luma; at most 4,
  darkest first). Also returns r. Rows: V1 `n_le_6` (target 0); V2 `min_r` >= -13 and `n_le_8` <= 2.
- `cold_edge_rows`: rows with sealant in the first `cols` columns; x0 = first sealant column.
  - `step_local` (v_edgestep.py "now"): rows whose mean R over [x0 - int(20/mm), x0 - int(8/mm)) > 0.5; per row step =
    median h[y, x0:x0+3] - median h[y, x0-2:x0]; `value` = p50 (also p10, p90, rows). Q3 target [t + 0.3d, t + 0.6d +
    0.5] (V4 [7.2, 11.9], V3 [6.4, 9.3]). accept_r1.py:371 m_cold_edge_step becomes a report row. The lens's range
    ended at t + 0.6d + 1 mm; Q3 adopted the verifier's + 0.5.
  - `registration` (fins_wall.py:38-63): rows whose mean R over [x0 - 11, x0 - 4) px > 0.5; depth = -median((h -
    h0)[y, x0-2:x0]); `registration_share` = mean(depth > 0.6 d + 0.3); target <= 0.10.
  - `band_side_share` {"a-b": share}: the same depth test on [x0 - round(b/mm), x0 - round(a/mm)) per window.
    `free_wall_share`: wall = R & ~mc.erode(R, 4 mm) & cold & ~mc.dilate(S, 8 mm), cold = columns [int(20/mm),
    int(240/mm)); share = mean(-(h - h0)[wall] > 0.6 d + 0.3). Plan: <= 0.05 at 0-4 mm, <= 0.10 at 4-8, free walls
    +-0.25 at 12-20.
  - Inputs: h, h0 mm; S = sealant >= 0.5; R = ravel >= 0.5; t = `sealant_thickness_mm`, d = `ravel_depth_mm`.
- `paired_delta`: the f4_joint_spall method (V4 vs nowear at the same px): "V4 gap floor - nowear <= -3 luma" and
  verifying joint_spall_darker.

#### 4.4.7 Detail stones and grain (P4, P7)

```python
def label_stones(sid) -> (lab int64, n, border bool (n+1,))      # verbatim realism_onfoot_verify_a/geom.py:label_stones
def stone_distances(lab, mm) -> (d_in, d_out, near)             # verbatim geom.py:distances
def per_label_median(lab_vals, vals, n) -> (med (n+1,), cnt)    # verbatim geom.py:per_label_median (>= 10 px)
def stone_table(h, sid, socket, deposit, mm) -> dict            # f1_stones.py:15-70
def mpd(H, mm, spacing_mm=None, lp=False, step=1) -> float      # verbatim realism_onfoot_verify_a/mpdlib.py:mpd
def granite_specks(bc, sid, socket, deposit, tol=0.006, min_bared_px=120) -> dict   # f5_granite.py:15-99
def hp_std_ratio(L, fines, mastic, mm, k_mm=3.0) -> dict        # f6_fines.py:21-54
```
- `label_stones`: fp = sid > 0.001; key = round(maximum_filter(sid, 3, wrap) x 65535); label = unique(4-connected
  component x 70000 + key); border = labels touching the image edge.
- `stone_table`: ring = ~fp & 1 < d_out <= 3 & ~socket & ~deposit (deposit = gray >= 0.02); ring_med = per-label
  median of h over the ring by nearest label; tip = per-label max h; prot = tip - ring_med; ok = area >= 30 & ~border &
  socket share < 0.5 & finite prot. zone = footprint plus outside px with d_out <= 3 & ~socket, assigned to the nearest
  label; z = (h - ring_med)/prot; wall = zone & ok & prot > 0.15 & 0.1 < z < 0.9; nwall = bincount per label. Boundary
  count verbatim f1_stones.py:51-52: `bnd = fp & (ndi.minimum_filter(np.where(fp, lab, 0), size=3, mode="wrap") !=
  lab)`, `nb = np.bincount(lab[bnd], minlength=n + 1)`; wall_width = nwall / max(nb, 1) x mm. Keys: `value` = p50
  wall_width over ok & prot > 0.15 (target >= 1.2 mm), `protrusion_p10_50_90`, `wall_width_p10_50_90`,
  `mastic_ring_std_mm`, `n_ok`, per-stone arrays under `maps`. h may carry any offset. Labelling follows geom.py (the
  plan's wall-width baselines are f1_stones'); accept_r1.py:865 `stones` and fixcheck_verify/stones_verify.py label
  differently, and accept_r1 keeps its own for stone_top_spread_mm.
- `mpd` (ISO 13473-1 style): rows and columns, each resampled to exact 100 mm segments (10 per 1 m) by linear
  interpolation with wrap; per segment subtract the mean and the linear trend; MSD = mean of the two 50 mm half-segment
  peaks; `value` = mean MSD over all segments. mpd_v0 uses the defaults (`raw`); target [0.39, 0.76].
- `granite_specks`: STONES = [[0.0, #66625d], [0.2, #7a7671], [0.45, #8a8680], [0.7, #958f84], [0.9, #a09887], [1.0,
  #a59f93]]; gv = clip((sid - 0.02)/0.98, 0, 1); E = per-channel np.interp(gv, keys, STONES RGB 0-1); rr = bc /
  max(E, 1e-4) with bc = basecolor sRGB 0-1 (not linear); m = mean_c rr; spread = max_c rr - min_c rr. inside = sid >
  0.019 & ~socket & ~deposit (deposit >= 0.5); bared = inside & spread < tol & 0.6 < m < 1.02; bared_core = bared &
  EDT(bared) > 1.5; speck = bared_core & m < 0.86. key = round(sid x 65535); per key nb = bared px, ns = speck px;
  sel = nb >= min_bared_px. `value` = share of sel stones with ns >= 0.03 nb (`share_speck_ge_3pct`; round 2 used
  tol 0.006, min 120 -> 0.219 / 0.211, f5_granite.json). On foot: 2x2 blocks with b4 = all bared, m4 = mean m, b4c = b4
  & EDT(b4) > 1, sp4 = b4c & m4 < 0.86, stones with nb4 >= 30; `onfoot_share` = share with ns4 >= 2. Targets [0.36,
  0.47] and >= 0.33.
- `hp_std_ratio`: k = int(round(k_mm/mm)) | 1 (7 at 0.48828); hp = L - uniform_filter(L, k, mode="wrap"); `value` =
  std(hp[fines]) / std(hp[mastic]). `onfoot_ratio`: 2x2 mean of L, masks all-true per 2x2 block, k = 3. fines =
  mc.erode(deposit >= 0.5 & socket < 0.5, 1.5 mm); mastic = mc.erode(sid < 0.001 & deposit < 0.02 & socket < 0.02,
  1.5 mm); L = sRGB luma 0-255. Targets >= 0.5, on foot >= 0.45.

### 4.5 Controls for clustering, landmark and registration claims

```python
def null_summary(real, controls, sign=+1) -> dict
def shift_scan(score, search_px, step_px=2) -> {"best": (score, dy, dx), "at_zero": score(0, 0)}
def outline_registration(outline, target, mm, near_mm=3.0) -> dict
def drop_field(shape, mm, density_u, band, cover_band, seed, d_lo=20.0, d_hi=100.0) -> bool (H, W)
def shuffle_control(stat_fn, values, n=200, seed=0) -> dict
```
- `null_summary`: keys `real`, `n`, `p05`, `p50`, `p95`, `mean`, `std`, `z` = (real - mean)/std, `share_ge_real` =
  mean(sign x control >= sign x real).
- `shift_scan`: `score(dy, dx)` on the integer grid +-search_px in steps of step_px. `cover` uses it; the Q2/P0 claim
  "no shift within +-73 mm fixes it" is this scan.
- `outline_registration` (va1_rim.py F, from line 220): real = share of outline px within near_mm of target (EDT of
  ~target x mm <= near_mm). Controls rotate the outline px about its centroid by 90/180/270° ((y, x) -> (cy - (x - cx),
  cx + (y - cy)) and powers) and mirror it in x; `chance` = mean of the near-target mask over the outline's bbox. Returns
  `null_summary` over the controls plus `chance`.
- `drop_field` (from v1_oil.py:`drop_field`): rng = default_rng(seed); discs in batches of 40 until the cover over
  `band` columns reaches cover_band; column from the cdf of `density_u` ((W,), e.g. the biweight G = (1 - clip(|U -
  1830|/620, 0, 1)²)² of v1_oil.py:38), row uniform, diameter log-uniform in [d_lo, d_hi] mm; stamped with wrap,
  stencil radius ceil(d_hi/2/mm) + 1. The oil drop control: replace the oil, keep band cover and mean darkening, 8 seeds.
- `shuffle_control`: real = stat_fn(values); controls = stat_fn(rng.permutation(values)) n times; returns
  `null_summary`.
- Rule for callers: every clustering, landmark or registration claim in a lens or verifier JSON reports `real` and one
  control from this set (round 2: the drop field for oil knots, rotation for outline-to-crack registration, the shift for
  Q2/P0).

### 4.6 Self-test: `python checks/review_kit.py --selftest`

Seeded (`np.random.default_rng(0)` unless stated), at most 2048² (lane tests), mostly 512² or 1024²; one process, about
30 s or less. One line per test, `PASS|FAIL <id> value=<v> expect=<e> tol=<t>`, then
`review_kit selftest: <k>/<n> pass (<s> s)`. Exit 0 if all pass, else 1. `--only id,id` runs a subset. "AA disc" =
coverage from 4x4 supersampling, box-averaged. mm = 0.48828 unless "lane" (1.78711). n = 52.

| id | function | synthetic input | expected | tol |
|---|---|---|---|---|
| aa_hard | aa_share | binary disc r 100 px in 512²; vals = 50 + 50 mask; min_step 4 | 0.000 | exact |
| aa_soft | aa_share | same mask; vals = gaussian_filter(50 + 50 mask, 1 px) | 1.000 | >= 0.98 |
| w_binary | edge_crossing_stats | half-plane mask x >= 256 in 512²; vals = 100 mask; floor 10 | w1090_px_p50 0.80; share_with_intermediate 0 | +-0.01 |
| w_gauss | edge_crossing_stats | same mask; vals[:, x] = 100 Φ((x - 255.5)/1.0) | w1090_px_p50 2.70; share_with_intermediate 1.0 | +-0.02 |
| jag_straight | edge_jaggedness | 1024 rows; inside x >= e, e = 256.3; vals = 100 clip(x + 0.5 - e, 0, 1); mask = vals >= 50; floor 10 | 0.000 | <= 0.005 |
| jag_noise | edge_jaggedness | same, e_row = 256 + N(0, 0.3) iid per row | 0.29 (≈ 0.976 x 0.3) | +-0.03 |
| lip_grid | lip_registration | AA disc r 300 px in 1024² as m_soft; h_rel = -5 mm where m >= 0.5, else 0 (a lip on the pixel grid); lum = 100 + 50 (m >= 0.5) | value 0.289 (uniform +-0.5 px sawtooth = 1/√12) | +-0.03 |
| lip_reg | lip_registration | same disc; h_rel = -5 m (registered to the AA outline); lum = 100 + 50 m | value <= 0.10 (the grid case reads 0.29) | - |
| ring_round | outline_spectrum | AA disc r 300 px in 1024² | r_mean_mm 146.48; every band <= 0.01 mm | +-0.1 mm |
| ring_mod | outline_spectrum | AA shape r(θ) = 300 + 2 sin(46θ) px (λ ≈ 20 mm) | band_rms_mm["10-30"] = 2 x 0.48828/√2 = 0.690 mm; other bands <= 0.03 | +-0.04 |
| bend_small | curvature_shares | radial_outline of an AA disc r 8 mm | R_lt10 >= 0.95 | - |
| bend_large | curvature_shares | AA disc r 60 mm | R_lt10 <= 0.01 | - |
| saw | straight_side_rms | AA square 600 px with exactly straight sides | band_rms_mm all <= 0.005 | - |
| cover_shift | cover | P disc r 100 px at (512, 512); Q disc r 130 px at (512, 542); 1024² | P_outside_Q_px > 0; best_shift dx_mm 14.65, dy_mm 0, min_margin_mm 14.65 | +-1.0 mm |
| cover_conc | cover | Q centred on P | P_outside_Q_px 0; min_margin_mm_centred 14.65 | +-0.5 mm |
| holes | fp_holes, island_slit | disc r 200 px; island_slit(island 40 mm, slit 3 mm) | island only: hole_px = π·41² ≈ 5281, components 1; island + slit: components 2 | +-3 %; exact |
| band_step | area_mean_step | fp disc r 200 px; beneath linear grey 0.2; comp = 0.18 on (2, 20] mm out, else 0.2 | 255 (srgb(0.18) - srgb(0.2)) = -5.90 | +-0.05 |
| band_abs | band_colour_abs | lum_comp = lum_lane + 4 on (0, 2] mm out | p50 = p90 = 4.0 | +-1e-6 |
| relief_full | rendered_relief_share | H_lane 0 with a 1 px crack grid every 40 px at -2 mm; alpha 0 off fp; H_comp = H_lane off fp | 1.000 | +-1e-6 |
| relief_none | rendered_relief_share | same; H_comp = 0 on the (0, 20] band | 0.000 | +-0.01 |
| visible | visible_share | alpha 0.25 on the band | 0.75 | +-1e-6 |
| leak | stack_leak_px | fp_early = rows 0-99 x cols 0-99; alpha_late > 0 on cols 90-199; fp_late = cols 95-199 (rows 0-99) | 500 | exact |
| plane | plane_residual | dH = 3 + 0.01x + 0.02y mm on a disc; then + a 2 mm Gaussian bump (sigma 10 mm) | <= 1e-9; then >= 1.8 | - |
| rim_design | inside_profile | disc fp r 400 px in 1024²; d = true inside distance; rem = cone_removal(d, 5.7, 20, 45, 60) | removal_at_d_1p5mm 8.55; near_vertical_depth_mm 20.3 | +-0.5; +-0.8 |
| rim_lip3 | inside_profile | rem = cone_removal(d, 5.7, 3, 30, 60) | removal_at_d_1p5mm 3.56 (fails >= 6); near_vertical_depth_mm <= 4 | +-0.5 |
| rim_bevel | inside_profile | rem = bevel_removal(cone_removal(d, 5.7, 20, 45, 60), d, fp, 5, 60) | removal_at_d_1p5mm 2.60 (fails) | +-0.5 |
| comb_smooth | wall_comb_hp | disc r 400 px; rem = min(5.7 x gaussian_filter(EDT x mm, 2 px), 20); wall_mm 20 | <= 2.0° | - |
| comb_stair | wall_comb_hp | rem = min(5.7 x EDT x mm, 20) | > 2.0° | - |
| top_const | wall_top_depths | rem = cone_removal(EDT x mm, 5.7, 20, 45, 60); soft = the AA disc coverage | spread/wall <= 0.15 | - |
| top_vary | wall_top_depths | lip = 20 (1 + 0.4 sin 3θ) per angle θ about the centre; same soft | 0.4 x 1.975 = 0.79 | +-0.15 |
| cone | bowl_mask, bowl_metrics | rem = cone_removal(analytic R - r, 5.7, 20, 45, 80), debris 0 | slope_iqr_s3 <= 1.0; azimuth_dev_s6_p50 <= 1.0; planarity_raw_pm3 >= 0.9 (a pure cone must fail bowl_facets) | - |
| lump_flat | crown_lump_std | pat disc r 400 px; crown 4 mm constant; no seam; ramp_mm 10, w_mm 0 | 0.000 | +-1e-6 |
| lump_noise | crown_lump_std | crown 4 + N(0, 0.3) mm iid | 0.30 | +-0.03 |
| crown_p | crown_params | {size_mm 300, kind 2, seam_mm_per_year 1, patch_age_years 8}; then kind 1 | (60, 5); (30, 5) | exact |
| seam_wave | seam_bins | AA patch disc r 300 px; seam = outer 20 px ring; h_rel = -5 + sin(4θ) mm; lum 120 | floor_std_mm 0.707; dirty_bin_share 1.0 | +-0.05; exact |
| seam_flat | seam_bins | h_rel = -5; lum 50 | floor_std_mm <= 0.01; dirty_bin_share 0.0 | - |
| oil_bw | sym_deficit_step | lane: p - pn = -20 (1 - clip(\|u - 1830\|/620, 0, 1)²)², pn = 0 | sym_step = 1.5396 x 20 x 50/620 = 2.48; A 19.98 | +-0.05 |
| oil_cliff | sym_deficit_step | lane: p - pn = -20 for \|u - 1830\| <= 300 mm | sym_step = 20 (2Φ(25/15) - 1) = 18.09 | +-0.2 |
| morph | oil_morph | lane 2048²: 30 non-overlapping 50 mm discs in the band | share_20_100mm 1.0; share_gt_200mm 0.0; count_median_eqd_mm 50 | exact; exact; +-2 |
| lm_lateral | along_v_landmarks | lane: L = 100 + 10 cos(2π u/3660) | n_le_6 0; min_r 0 | +-1e-3 |
| lm_disc | along_v_landmarks | same + a -12 luma disc, 200 mm diameter at (1830, 1830) mm | n_le_6 1; min_r = -12 (1 - e^-2) = -10.38 | +-0.3 |
| drop | drop_field, oil_morph | lane 2048², density G, band 1455-2205 mm, cover 0.10, seed 1 | band cover in [0.10, 0.125]; the same seed gives an identical mask; share_20_100mm >= 0.6 | - |
| cold | cold_edge_rows | lane rows 2048 x 400; h0 0; S = cols >= 100, h = +3; R = cols 80-99, h = -9; t 3, d 14 | step_local 12.0; registration_share 1.0; with h = -8 on R: step 11.0, share 0.0 | exact |
| paired | paired_delta | a = a_ref + 3 on a mask | 3.0 | exact |
| stone_ramp | stone_table | 512²; 9 discs r 20 px (sid 0.3-0.7, distinct); h 0 off stone; on stone h = 3 x clip(d_in/(4 x mm), 0, 1) | protrusion p50 3.0; wall_width p50 >= 1.2 mm | +-0.01 |
| stone_prism | stone_table | same, h = 3 on the whole stone | wall_width p50 <= 0.3 mm | - |
| mpd_sin | mpd | 2048²: H = sin(2πx/10 mm) + sin(2πy/10 mm) | 0.99 | +-0.02 |
| mpd_flat | mpd | H = 0 | 0.0 | exact |
| granite | granite_specks | 25 stones r 20 px, sid = 0.02 + 0.98 g; bc = STONES(g) x 0.95; 10 stones carry a 7x7 px speck x 0.75 at the centre; tol 0.004 | value 0.400; onfoot_share 0.400 | exact |
| fines | hp_std_ratio | 1024², mastic half N(0, 10), fines half N(0, 5) iid luma | 0.50 | +-0.03 |
| ctl_shuffle | shuffle_control | x ~ N(0, 1) (500), y = x + 0.1 N; stat = corr(x, y) over permuted y | z >= 10; share_ge_real 0.0 | - |
| ctl_rot | outline_registration | AA ellipse semi-axes 300 x 150 px; target = 3 mm ring on its own outline | real 1.0; rot90 and rot270 <= 0.1 | - |

Analytic expectations (the
sRGB step, Φ, 1 - e^-2, 1/√12) are computed in the test, not typed in. If a tolerance proves too tight on the first run,
report the measured value and widen it in a separate commit; never change a function to make a test pass.

run_all.sh, inserted after line 19 (`fail=0`), cwd is checks/ there:
```bash
"$PY" review_kit.py --selftest > "$T/review/review_kit_selftest.txt" 2>&1 \
  || { fail=1; echo "review_kit: self-test FAILED (review/review_kit_selftest.txt)"; }
echo "review_kit: $(tail -n 1 "$T/review/review_kit_selftest.txt")"
```
A failing self-test fails the run (exit 1), like a hard check: every kit-measured row would otherwise be unverified.

### 4.7 Round-2 reproduction (report, M3)

With the copied round-2 exports, each ported function must reproduce its prior-art script on the same inputs. Run the
kit on the configs the prior-art script used (read its `__main__`), compare with the numbers below and with the
script's JSON where it wrote one; a miss means the port differs (diff it against the script), not that the target moved.

| function | round-2 value (as the plan or the script reports it) | prior-art output |
|---|---|---|
| inside_profile | rim_drop_1p5mm 9.43; near_vertical_depth_mm 20.59 / 25.31 / 20.63 / 16.02 | g1_requirements_verify_b/f5_wall.py |
| wall_comb_hp | 5.7-6.7 on the pothole decals (bowl 0.3-0.8) | decal_potholes_verify_b/v1b_walls_hp.py |
| wall_top_depths | spread/wall 0.04-0.13 | decal_potholes_verify_b/v1_walls.py |
| bowl_metrics | P1 slope_iqr_s3 3.0, azimuth_dev_s6_p50 2.3 | decal_potholes_verify_b/v2_bowl.py |
| lip_registration | Q1 V4 0.291, Q2 0.291 (colour 0.376), P2 / P0 0.123 / 0.127 (colour 0.196 / 0.226), Q0 V4 0.014 | decal_patches_verify_b/v3_lip.json |
| area_mean_step | -7.26 / -6.23 / -5.86 / +0.12 / +2.28 | decal_patches_verify_a/v3_rim.py |
| stack_leak_px | q0 under q3: 48,320 | v3_rim.py `q0q3`; = composite `later_ring_over_core.px` |
| seam_bins | floor std 0.003 / 0.021 / 0.029; dirty 1.00 | decal_patches_verify_b/v2_seam.py |
| sym_deficit_step | V2-V4 3.90 / 4.90 / 5.75 (biweight 3.0 / 4.04 / 5.06) | lead/lead_measure.py (C) |
| oil_morph | V1 / V2 share_20_100mm 0.297 / 0.073, share_gt_200mm 0.386 / 0.862 | g5_tiling_verify/v1_oil.py |
| along_v_landmarks | V1 n_le_6 2 at -11.8; V2 min_r -19.5, n_le_8 4 | v1_oil.py |
| cold_edge_rows | step_local V4 12.63, V3 8.2; registration_share 0.572 / 0.449 | realism_lane_verify_a/v_edgestep.py, realism_lane/fins_wall.py |
| mpd | V0 0.226 (V1 WP control 0.521) | realism_onfoot_verify_a/mpdlib.py |
| stone_table | wall width p50 0.55 / 0.50 / 0.43 | realism_onfoot_verify_a/f1_stones.py |
| granite_specks | V4 WP / NWP 0.219 / 0.211; on foot 0.192 / 0.193 | realism_onfoot_verify_b/f5_granite.json |
| hp_std_ratio | 0.331 / 0.337 (on foot 0.312 / 0.319) | realism_onfoot_verify_b/f6_fines.py |
| straight_side_rms | 0.000 in 10-30 (saw-cut) | decal_patches_verify_b/v1_outline.py |

### 4.8 Who imports the kit, and the verifier rule

| file | imports | rows (written in session 4 with the plan items) |
|---|---|---|
| checks/decal_extra.py | `import review_kit as rk` (same folder) | `aa_share` moves to the kit (`aa_share = rk.aa_share` stays). New: rim_colour_width, rim_edge_jaggedness, seam_lip_registration, outline_band_10_30, tight_bends, patch_covers_hole, wall_comb_hp, wall_top_spread, bowl_facets (bowl_planarity becomes report), crown_lump_std (crown_residual_std becomes report), seam_floor_std, seam_dirty_share, pothole_wall_depth, rim_drop_1p5mm (written with `"hard": true`; run_all.sh counts it like inv16_ok, plan P1 (c)). colour_aa_outline becomes report. |
| checks/accept_r1.py | `import review_kit as rk` | oil_deficit_step_sym, V1 landmarks, V2 oil residual, oil_drop_area_share, share > 200 mm, cold_edge_step_local, cold_edge_registration, band-side shares, V4 gap floor - nowear, mpd_v0, stone wall width, granite speckled and on-foot shares (onfoot_stone_std_share stays as report), fines/mastic ratio. Existing ids stay as report rows (plan guard rail). |
| composite_decal.py | `sys.path` += checks; `import review_kit as rk` | `inv16_terms` (§3.4) now; area_mean_step, band_colour_abs, rendered_relief_share, visible_share, stack_leak_px with P2 |
| checks/wrong_builds.py | `import review_kit as rk`; `composite_decal.WRONG_BUILDS` | generators `cone_removal`, `lip_cut`, `bevel_removal`, `height_raw`, `island_slit` for the new cases |
| checks/gen_checks.py | none | matcheck JSON only (footprint_solid, opacity_core 0.999, opacity_border 2 mm, agg_tips_kept -0.1, joint_spall_darker) |

Verifier rule (the brief: "verifiers keep their own method; the kit is shared infrastructure like matcheck"):
- Lenses and verifiers may import the kit, and should, instead of rewriting these measurements.
- A verifier re-measuring a lens's high or medium finding must not count the same kit function on the same input as
  independent confirmation (same code, same bug). It uses its own method, or the kit plus a §4.5 control, or a
  different kit function measuring the same property, and states per re-measured number `"method": "own"`,
  `"review_kit.<fn>"` or `"review_kit.<fn> + <control>"` (inside `independent_numbers` or `basis`).
- A verifier that finds a kit bug reports it as a finding against `checks/review_kit.py` with a failing synthetic case;
  the fix ships with a new self-test row.

## 5. Merge script, lead contract, render_findings.py (brief changes 7 and 5)

Code merges lens and verifier JSON, the lead writes only judgement as JSON, code renders findings.md. Line numbers
refer to today's files; new files list their functions in file order.

### 5.0 Decisions

| item | decision | why |
|---|---|---|
| where | SK/merge_panel.py, SK/render_findings.py, tests in SK/tests/test_review_pipeline.py | They only read the panel schemas that S/assets/workflows/review_round.js owns, so a schema change touches one repo; nothing material-specific. Kit and composite cache stay in T/checks (§0.4 item 2). |
| deps | Python >= 3.9 standard library only (`json`, `re`, `argparse`, `pathlib`, `textwrap`, `collections`, `datetime`, `os`, `sys`, `tempfile`, `unittest`) | runs from the venv or any python3, macOS or Windows; no numpy, so no thread cap needed |
| file I/O | UTF-8 read and write; `json.dump(..., indent=1, ensure_ascii=False)`; `\n` newlines and a trailing newline; write `<name>.tmp`, then `os.replace` | as <a>/lead/make_review_result.py:707; the atomic replace avoids half-written files |
| who runs them | merge: the workflow's `merge` agent (§6.2), or the main session on the Agent-tool route; render: the main session | round 2's lead could not write findings.md from a subagent (brief §1) |

### 5.1 Prior art and where it disagrees

Prior art: review_round.js (merge :128-140 and PLAN :72-93), <a>/lead/make_review_result.py (the round-2 lead's
hand-built result: clusters, rejected rows and counts typed in, :451-522, :693-695), T/review/BRIEF.md §14 (:1723-1764,
file schemas), and the two findings.md formats (round 1 on disk, round 2 in the lead's hand-back).

| point | review_round.js | round-2 lead | spec | why |
|---|---|---|---|---|
| finding with no verdict | rejected, "no verdict" (:139) | confirmed after re-measuring (regressions-2/-3) or borrowing g1_requirements_verify_a (regressions-1) | status `unverified`; the lead confirms or rejects each | brief change 5 sends lows to the lead unverified; a missing verifier (round 2's stopped one) is no evidence against a finding |
| `real` with `artifact != none` | rejected (:138) | confirmed; the sub-claim goes to REJECTED (g1_requirements-1, fixcheck-1, realism_onfoot-4, decal_potholes-2) | `confirmed_subclaim` | the verifier prompt says "real=false only when the core is unsupported", so `real=true` asserts the core and the artifact label can only refer to part of the claim |
| lead output | PLAN (:72-93): string acceptance and guard rails, scorecard `verdict`, invariant `pass: bool` | review_result.json: structured acceptance rows, `merged`/`gated_by`, scorecard `status`, invariant status strings, `design_calls` | round 2's shape (§5.3.2) replaces PLAN | it rendered the established format and passed the gate; acceptance rows are what the next fixcheck re-measures; "pass (thin at V4)" needs a string |
| counts | logged (:140) | typed by hand (:693-695) | computed by render_findings.py | cannot drift |
| fix_status | lens reports passed through (:132); verifier `fix_status_checks` dropped | one row per ledger id, by hand | merge groups reports and checks per ledger id; the lead writes the final row | evidence and judgement stay apart |
| verifier files | VERDICTS only | §14 adds `fix_status_checks`; files also carry `answer_checks`, `verifier`, `scripts`, `scope` | merge reads all of them | matches the files on disk |
| FIXSTATUS line | round 1: `- F0-1 title — landed (...)` | round 2: `- P1 partial: note` | round 2 | the JSON has `fix` + status enum + `note` |
| WHY / CHANGE | round 1: inline paragraph | round 2: bullet lists | paragraph for a string, bullets for a list | the round-2 JSON strings contain no newlines |

### 5.2 merge_panel.py

#### 5.2.1 CLI

```
merge_panel.py --round-dir DIR [--out FILE] [--lenses k1,k2,...] [--ledger FILE]
  DIR      review/round<N>; N = int(re.search(r"round(\d+)$", Path(DIR).resolve().name)) (error if absent)
  --out    default DIR/merged.json
  --lenses the expected lens keys: only these are merged; a key without DIR/<key>.json is a warning and goes to
           merged.json "missing_lenses". Default: all discovered.
  --ledger default DIR/ledger.json if it exists (dict with items[].id), else none
exit 0 ok (warnings on stderr); 2 on any error of §5.2.7 (nothing written)
stdout, last line exactly:
round <N>: <F> findings: <c> confirmed, <s> confirmed (sub-claim artifact), <u> unverified, <r> rejected; <L> lenses, <V> verifier files[; no verifier: k1, k2][; no lens file: k3]
```
Round 2 prints:
`round 2: 35 findings: 26 confirmed, 4 confirmed (sub-claim artifact), 3 unverified, 2 rejected; 8 lenses, 12 verifier files; no verifier: regressions`

#### 5.2.2 File discovery

- Lens file: any `DIR/*.json` whose top level is an object with a list `findings` and no list `verdicts`. Key = file
  stem; sorted by file name. This skips review_result.json, ledger*.json, merged.json, lead.json and the verifier
  files. Round 2: decal_patches, decal_potholes, fixcheck, g1_requirements, g5_tiling, realism_lane, realism_onfoot,
  regressions.
- Verifier files of lens `k`: `^{re.escape(k)}_verify(?:_([a-z]))?\.json$`, the plain file first, then `_a`, `_b`, ...
  Round 2 has 12 (fixcheck and g5_tiling one each, the other five a/b, none for regressions).
- Lens keys: `findings`, `fix_status`, `strengths` (required); `answers`, `not_checked` (optional, default `[]`).
  BRIEF §14 marks `answers` required, but a lens that owns no question may leave it out.
- Verifier keys: `verdicts` (required); `fix_status_checks`, `answer_checks`, `not_checked` (optional, default `[]`).
  Any other top-level key (`verifier`, `scripts`, `scope`) is copied raw into `verifier_meta`.

#### 5.2.3 Classification

```python
def classify(v: dict | None) -> tuple[str, str | None]:
    if v is None:                        return ("unverified", None)
    if not v["real"]:                    return ("rejected", "not_real")
    if v["severity_adjusted"] == "none": return ("rejected", "severity_none")
    if v["artifact"] != "none":          return ("confirmed_subclaim", None)
    return ("confirmed", None)

def classify_js(v: dict | None) -> bool:   # exact port of review_round.js:138 (the old rule), for the parity test only
    return bool(v) and v["real"] and v["artifact"] == "none" and v["severity_adjusted"] != "none"
```
A finding's verdict is the one whose `id` equals the finding `id` in that lens's verifier files.
`severity_final` = `v["severity_adjusted"]` if a verdict exists, else the lens `severity`.
`unverified_reason` = None unless unverified; then `"low"` if the lens severity is low, else `"verifier_missing"`.
`missing_verifiers` = lenses with >= 1 high or medium finding (lens severity) and no verifier file.

#### 5.2.4 Grouping

- fix_status: key = `re.match(r"^\s*([PD]\d+)\b", fix)` group 1, else `"other"`. Lens rows go to `reports` (with
  `lens`), verifier `fix_status_checks` to `checks` (with `verifier` = file stem); `statuses` counts report statuses.
  Key order: ledger order, then other keys in first-seen order, then `"other"`. Ledger ids without a report go to
  `ledger_ids_without_report` (warning).
- answers / answer_checks: two flat lists with `lens` (and `verifier`); not paired (round 2: 0 of 13 check questions
  equal an answer string), the lead pairs them.
- strengths: `[{lens, text}]`. not_checked: `[{lens, file, text}]` from lens and verifier files.

#### 5.2.5 Cluster hints (for the lead; code does not cluster)

For every finding whose status is not `rejected`:
```python
FILE_RE = re.compile(r"\b([A-Za-z0-9_]+\.(?:py|sbs|js|json))\b")      # over cause + " " + proposed_fix
SITE_RE = re.compile(r"\b(decal_[pq]\d_v\d|lane_v[0-4]x?|detail_v[0-4](?:_n?wp)?)\b")  # over " ".join(variants) + " " + evidence
# invariants: invariant_ids as given
```
Key `f"{kind}:{value}"`, kind in `file`, `site`, `inv`. A key becomes a hint when its ids come from 2 or more lenses.
Hint = `{key, kind, value, ids (sorted), lenses (sorted)}`, sorted by `(len(ids), ["file","site","inv"].index(kind),
value)`. Round 2: 37 hints (10 file, 18 site, 9 inv); every cross-lens pair inside the lead's 22 clusters (19 pairs)
shares at least one hint.

#### 5.2.6 merged.json

```jsonc
{
  "schema": "sdmr.merged/1",
  "round": 2,                                   // int
  "round_dir": "<absolute path>",
  "generated": "2026-10-05T10:12:00",           // local time, isoformat(timespec="seconds")
  "rule": "confirmed: real and severity_adjusted != none; artifact != none on such a verdict = confirmed_subclaim; no verdict = unverified",
  "lenses": [{"key": "g1_requirements", "file": "g1_requirements.json",
              "verifier_files": ["g1_requirements_verify_a.json", "g1_requirements_verify_b.json"],
              "n_findings": 5, "n_verdicts": 5}],
  "missing_verifiers": ["regressions"],          // lenses with >= 1 high/medium finding and no verifier file
  "missing_lenses": [],                          // --lenses keys without a lens file
  "counts": {"findings": 35, "confirmed": 26, "confirmed_subclaim": 4, "unverified": 3, "rejected": 2,
             "by_final_severity": {"high": 3, "medium": 21, "low": 9},   // non-rejected findings; all three keys always present
             "fix_reports": 69, "fix_checks": 35, "strengths": 49, "answers": 9, "answer_checks": 13},
  "index": [{"id": "g1_requirements-1", "lens": "g1_requirements", "status": "confirmed_subclaim",
             "severity": "high", "severity_final": "medium", "artifact": "metric",        // artifact/fix_assessment null when unverified
             "fix_assessment": "partial", "unverified_reason": null, "title": "..."}],    // lens order, then finding order
  "findings": [{ /* the 12 FINDINGS keys verbatim */ "lens": "...", "status": "...", "reject_reason": null,
                 "severity_final": "...", "unverified_reason": null,
                 "verdict": { /* the 12 VERDICTS keys verbatim */ "file": "x_verify_a.json" } /* or null */,
                 "keys": {"files": [], "sites": [], "invariants": []} }],
  "confirmed": ["id", ...], "confirmed_subclaim": ["id", ...], "unverified": ["id", ...],   // index order
  "rejected": [{"id": "fixcheck-2", "lens": "fixcheck", "title": "...", "reason": "not_real", "why": "<verdict.reasoning>"}],
  "orphan_verdicts": [{"id": "...", "file": "..."}],      // verdict ids matching no finding of that lens
  "fix_status": {"P1": {"reports": [{"lens": "fixcheck", "fix": "...", "status": "partial", "note": "..."}],
                        "checks": [{"verifier": "fixcheck_verify", "fix": "...", "agree": true, "note": "..."}],
                        "statuses": {"landed": 2, "partial": 1}}, "...": {}, "other": {}},
  "ledger_ids_without_report": [],
  "strengths": [{"lens": "...", "text": "..."}],
  "answers": [{"lens": "...", "question": "...", "answer": "...", "basis": "..."}],
  "answer_checks": [{"lens": "...", "verifier": "...", "question": "...", "agree": false, "note": "..."}],
  "not_checked": [{"lens": "...", "file": "x.json", "text": "..."}],
  "verifier_meta": [{"file": "decal_patches_verify_a.json", "keys": {"verifier": "...", "scripts": "..."}}],
  "cluster_hints": [{"key": "file:composite_decal.py", "kind": "file", "value": "composite_decal.py",
                     "ids": ["decal_patches-4", "g1_requirements-1", "g1_requirements-5", "regressions-1"],
                     "lenses": ["decal_patches", "g1_requirements", "regressions"]}]
}
```
The lead reads `counts`, `index`, `missing_*` and `cluster_hints` first (a few KB) and opens `findings[i]` only when needed.

#### 5.2.7 Functions (file order)

```python
SEVERITIES = ("high", "medium", "low")
FINDING_KEYS = ("id","title","severity","category","requirement_ids","invariant_ids","variants","visible_at",
                "evidence","cause","proposed_fix","acceptance")                     # review_round.js:42
VERDICT_KEYS = ("id","real","reproduced","independent_numbers","artifact","basis","premise_errors",
                "severity_adjusted","fix_assessment","better_fix","acceptance_fixed","reasoning")  # :67
ARTIFACTS = ("none","preview_shader","downsampling","metric","quantisation")
LEDGER_ID_RE, FILE_RE, SITE_RE, VERIFY_RE   # as above
def load_json(path: Path) -> Any
def round_number(round_dir: Path) -> int
def discover(round_dir: Path, only: list[str] | None) -> tuple[list[dict], list[str]]   # [{key, file, verifier_files}], missing_lenses
def check_lens(doc: dict, name: str) -> list[str]                           # error strings
def check_verifier(doc: dict, name: str) -> list[str]
def classify(v: dict | None) -> tuple[str, str | None]
def classify_js(v: dict | None) -> bool
def ledger_key(fix: str) -> str
def hint_keys(f: dict) -> dict[str, list[str]]                              # {"files","sites","invariants"}
def build_hints(findings: list[dict]) -> list[dict]
def merge(round_dir: Path, only=None, ledger_path: Path | None = None) -> tuple[dict, list[str], list[str]]  # merged, errors, warnings
def summary_line(m: dict) -> str
def main(argv: list[str] | None = None) -> int
```
Errors (exit 2, nothing written): a missing required lens or verifier key; a finding or verdict missing one of its 12
keys; `severity`, `artifact`, `severity_adjusted` or `fix_assessment` outside its enum; a duplicate finding id across
lenses; a duplicate verdict id across one lens's verifier files (two verdicts on one finding need a person); no lens
files. Warnings: orphan verdicts, a lens with a high/medium finding and no verifier, a `--lenses` key without a file,
ledger ids without a report.

### 5.3 Lead contract

#### 5.3.1 What the lead does and does not do

Time box (brief change 3): <= 30 tool calls, about 15 min. It reads `round<N>/merged.json` (counts, index,
missing_*, hints first), the delta brief's rules, scorecard and ledger sections, and the current scorecards. It does
not re-read lens or verifier files, write findings.md, compute counts or copy findings. It saves `round<N>/lead.json`
with Python `json.dump` (the route that worked in round 2) and returns the same object. On the Agent-tool route its
final message is at most 5 lines: the path, the number of fixes, the number of design calls, anything left unjudged.

Its judgement, in order:
1. Cluster every `confirmed`, `confirmed_subclaim` and `unverified` finding into `C1..Ck` (`confirmed[]` in lead.json),
   using `cluster_hints`; keep source ids; a partial member is `"<id> (<part>)"` (round 2's C4).
2. Re-measure at least one `unverified` finding and record it in `spot_check`. A high or medium there lost its
   verifier: check its key number before planning on it. Place each unverified id in a cluster (lead-confirmed) or in a
   REJECTED row whose id is exactly the finding id.
3. For every `confirmed_subclaim`, write a REJECTED row `"sub-claim <id>"` naming the sub-claim the artifact label
   refers to (from `verdict.premise_errors` / `reasoning`).
4. Plan at most 10 / 8 / 5 fixes for rounds 1 / 2 / 3+, in dependency order (layout -> height/structure -> process
   masks -> colour -> micro-detail), with acceptance rows and guard rails. Design calls for what the user must decide,
   cross-linked by `gates` and `gated_by`; recommended option first; header <= 12 chars.
5. Scorecard (one row per requirement per graph), invariants, one final `fix_status` per ledger id (from
   `merged.fix_status[id].reports/checks`), keep-as-is (from strengths), deferred, conflicts resolved, premises corrected
   (Histogram Scan centre = 1 - Position; Blend divide = dst/src), overall assessment, stop rule; `missing_lenses`,
   `missing_verifiers` and what it skipped go in `not_checked`.

#### 5.3.2 LEAD schema (replaces PLAN in review_round.js:72-93)

Round 2's review_result.json minus `counts` is a valid instance (the test fixture). `?` marks optional keys.

```js
const STR = { type: 'string' }, STRS = { type: 'array', items: { type: 'string' } }, INTS = { type: 'array', items: { type: 'integer' } }
const LEAD = { type: 'object', properties: {
  round: { type: 'integer' }, date: { type: 'string', description: 'YYYY-MM-DD' },
  scope: STR,                                   // ? heading parenthetical, e.g. "lane + detail + decals"
  lead_measurements: STR,                       // ? path of the lead's re-measurement JSON, relative to T
  plan: { type: 'object', properties: {
    fixes: { type: 'array', items: { type: 'object', properties: {
      priority: { type: 'integer' }, title: STR,
      variants: STRS,                           // graphs/configs, free text ("lane_v1", "decal p0_v3 p1_v4 ...")
      source_ids: STRS,                         // finding ids, optionally "<id> (<part>)", or free refs ("ledger P5")
      merged: STRS,                             // cluster ids "C<n>", optional " (<part>)"
      gated_by: STRS,                           // design call ids "Q<n>"
      depends_on: INTS,                         // priorities of earlier fixes
      why: STR, change: STR,                    // or arrays of strings (rendered as bullets)
      acceptance: { type: 'array', items: { type: 'object', properties: {
        check: STR, kind: { type: 'string', description: '^(hard|soft|report|suite)\\b, optional qualifier: "hard (new)", "soft margin"' },
        target: STR, baseline: STR, wrong_build: STR /* ? */ }, required: ['check', 'kind', 'target', 'baseline'] } },
      guard_rails: STRS,
    }, required: ['priority','title','variants','source_ids','merged','gated_by','depends_on','why','change','acceptance','guard_rails'] } },
    requirements_scorecard: { type: 'array', items: { type: 'object', properties: {
      id: STR /* "R<n>" */, title: STR /* ? */, graph: STR /* "lane V0-V4, V3x" */,
      status: { type: 'string', enum: ['met', 'mostly_met', 'not_met'] }, evidence: STR,
    }, required: ['id', 'graph', 'status', 'evidence'] } },
    invariants: { type: 'array', items: { type: 'object', properties: {
      id: STR /* "INV-<n>" */, title: STR /* ? */, status: { type: 'string', description: '^(pass|fail)\\b, e.g. "pass (thin at V4)"' }, values: STR,
    }, required: ['id', 'status', 'values'] } },
    keep_as_is: STRS,
    deferred: { type: 'array', items: { type: 'object', properties: {
      id: STR /* cluster id or free text */, title: STR, severity: STR, reason: STR, default: STR, target_round: { type: 'integer' },
    }, required: ['id', 'reason', 'target_round'] } },
    conflicts_resolved: { type: 'array', items: { type: 'object', properties: { conflict: STR, resolution: STR }, required: ['conflict', 'resolution'] } },
    premises_corrected: STRS,
    remeasured: STRS,                           // ? one line per number the lead re-measured
    overall_assessment: STR,
  }, required: ['fixes','requirements_scorecard','invariants','keep_as_is','deferred','conflicts_resolved','premises_corrected','overall_assessment'] },
  design_calls: { type: 'array', items: { type: 'object', properties: {
    id: STR /* "Q<n>" */, header: { type: 'string', description: '<= 12 chars (the gate question chip)' }, question: STR,
    options: { type: 'array', items: { type: 'object', properties: { label: STR, recommended: { type: 'boolean' }, consequence: STR },
               required: ['label', 'recommended', 'consequence'] } },   // 2-4 options, the recommended one first
    gates: INTS,                                // fix priorities this call gates
  }, required: ['id', 'header', 'question', 'options', 'gates'] } },
  confirmed: { type: 'array', items: { type: 'object', properties: {   // the clusters C1..Ck
    id: STR, title: STR, severity: { type: 'string', enum: ['high', 'medium', 'low'] },
    source_ids: STRS, verdict: STR /* verifier notes, condensed */, plan: STR /* "P2, Q1, Q2" | "DEFERRED" | "DEFERRED (engine call)" */,
  }, required: ['id', 'title', 'severity', 'source_ids', 'verdict', 'plan'] } },
  rejected: { type: 'array', items: { type: 'object', properties: { id: STR, reason: STR }, required: ['id', 'reason'] } },
  fix_status: { type: 'array', items: { type: 'object', properties: {
    fix: STR /* ledger id */, status: { type: 'string', enum: ['landed', 'partial', 'not_landed', 'regressed', 'not_checked'] }, note: STR,
  }, required: ['fix', 'status', 'note'] } },
  stop_rule: { type: 'object', properties: { met: { type: 'boolean' }, why: STR,
    next_round: STR /* ? "<preamble> (1) ...; (2) ..."; the renderer also accepts the key "round<N+1>" (round 2 wrote "round3") */ },
    required: ['met', 'why'] },
  spot_check: { type: 'object', properties: { id: STR, result: STR }, required: ['id', 'result'] },   // ? id "none" if no unverified finding
  not_checked: STRS,                            // ?
}, required: ['round', 'date', 'plan', 'design_calls', 'confirmed', 'rejected', 'fix_status', 'stop_rule'] }
```

REJECTED row ids follow fixed forms, because the renderer groups by id:

| id form | meaning | round-2 count |
|---|---|---|
| a finding id, `^[a-z0-9_]+-\d+$` | finding rejected (verifier, or the lead on an unverified one) | 2 |
| `sub-claim <finding id>` | the sub-claim behind an artifact label | 4 |
| starts with `round-` | carry-forward of an earlier round's list | 1 |
| anything else (`fix <id> parts`, `<id> numbers`, `<lens> answer targets`) | rejected fix parts, targets, numbers | 32 |

A `counts` key in lead.json is ignored; if it differs from the computed counts, that is warning W2.

### 5.4 render_findings.py

#### 5.4.1 CLI

```
render_findings.py --round-dir DIR [--lead FILE] [--merged FILE] [--ledger FILE] [--out FILE] [--result FILE]
                   [--check] [--no-keep-decisions]
  --lead    default DIR/lead.json         --merged default DIR/merged.json
  --ledger  default DIR/ledger.json if it exists (items[].id gives the FIXSTATUS order and the V9 check)
  --out     default DIR/findings.md       --result  also write review_result.json there (§5.4.6)
  --check   validate only; print errors and warnings; write nothing
  DECISIONS: if --out exists, its DECISIONS section (heading line through the line before the next "## ") is copied
             verbatim, unless --no-keep-decisions
exit 0 ok; 2 on any validation error (nothing written)
stdout last line: "findings.md: <lines> lines; <F> findings, <C> confirmed, <R> rejected, <K> items, <P> fixes, <Q> design calls"
```

#### 5.4.2 Validation (errors unless marked warning)

| # | rule | round-2 fixture |
|---|---|---|
| V1 | every `confirmed` and `confirmed_subclaim` id appears in some cluster's `source_ids`, parsed with `^([a-z0-9_]+-\d+)\b` | 30/30 |
| V2 | every `unverified` id appears in a cluster or as an exact REJECTED row id | 3/3 (C2, C22, C7/C8) |
| V3 | every `confirmed_subclaim` id has a REJECTED row `sub-claim <id>` | 4/4 |
| V4 | every merged `rejected` id has a REJECTED row with that exact id, and no `confirmed`/`confirmed_subclaim` id has one (the lead downgrades or defers, it cannot reject a verified finding) | 2/2, 0 |
| V5 | priorities are exactly 1..n; `depends_on` names only lower priorities; n <= the cap (10/8/5) | 8 <= 8 |
| V6 | `P in Q.gates` ⇔ `Q in fix[P].gated_by`; every id named exists | consistent |
| V7 | each design call has 2-4 options, exactly one `recommended`, and it is `options[0]`; `len(header) <= 12` | 7/7 |
| V8 | scorecard status in the enum; invariant status matches `^(pass\|fail)\b`; acceptance kind matches `^(hard\|soft\|report\|suite)\b` | ok |
| V9 | the set of `fix_status[].fix` equals the ledger ids; status in the enum | 20 = 20, same order |
| V10 | cluster ids unique; deferred ids of the form `C\d+` exist; `P\d+` / `Q\d+` tokens in `cluster.plan` exist | ok |
| W1 | warning: a cluster's severity above the highest `severity_final` of its members | 0 |
| W2 | warning: lead.json `counts` differs from the computed counts | 0 |

#### 5.4.3 Counts

```python
fid = lambda s: (m := re.match(r"^([a-z0-9_]+-\d+)\b", s)) and m.group(1)
in_clusters  = {fid(s) for c in lead["confirmed"] for s in c["source_ids"] if fid(s)}
row_ids      = {r["id"] for r in lead["rejected"]}
lead_conf    = [i for i in merged["unverified"] if i in in_clusters]
lead_rej     = [i for i in merged["unverified"] if i in row_ids]
confirmed    = merged["confirmed"] + merged["confirmed_subclaim"] + lead_conf
counts = {"findings": merged["counts"]["findings"],
          "confirmed": len(confirmed),
          "rejected": len(merged["rejected"]) + len(lead_rej),
          "merged_items": len(lead["confirmed"]),
          "confirmed_by_severity": {s: n_of(confirmed, severity_final == s) for s in ("high","medium","low")},
          "merged_by_severity":    {s: n_of(lead["confirmed"], severity == s) for s in ("high","medium","low")}}
```
Round 2: `{findings 35, confirmed 33, rejected 2, merged_items 22, confirmed_by_severity {3, 21, 9}, merged_by_severity
{3, 15, 4}}`, equal to review_result.json `counts`.

#### 5.4.4 findings.md layout (exact templates)

Order and line formats from round 1's file; round 2 added design calls, DEPENDS/SOURCES and the stop rule. `N` = round,
`j(xs)` = `", ".join(xs)`. Empty optional parts are left out with their separators.

```
# Reviewer round {N}: findings and plan[ ({scope})]

## DECISIONS (user)                               <- or the preserved section from the existing file

(to be filled after the gate)

{date}. {L} lenses ran: {j(lens keys)}. There are {V} verifier results ({j("<key> <n>" for lenses with n>0)}).[ No verifier
result for: {j(missing_verifiers)}.] Lens and verifier results: `review/round{N}/<lens>[_verify[_a|_b]].json`, merged by
merge_panel.py into `review/round{N}/merged.json`.

Rule: a finding is confirmed when its verdict says it is real with a severity above none.[ {s} verdicts put an artifact
label on a sub-claim and keep the core real ({j(ids)}); they count as confirmed and their sub-claims are under REJECTED.][
{u} findings had no verdict ({j(ids)}); the lead confirmed {len(lead_conf)} and rejected {len(lead_rej)}.] Totals: {F}
findings, {C} confirmed ({h} high, {m} medium, {l} low) and {R} rejected. They merge into {K} items, C1-C{K} in the JSON.

## OVERALL

{overall_assessment}
[
Lead measurements: `{lead_measurements}`.]
[
Spot check: {spot_check.id}: {spot_check.result}]
[
### Re-measured by the lead
- {remeasured[i]}]
[
### Premises corrected
- {premises_corrected[i]}]
[
### Not checked
- {not_checked[i]}]

## Scorecard

SC: {status} | {id}[ {title}] ({graph}) | {evidence}
...

INV: {status} | {id}[ {title}] | {values}
...

## Design calls

Decide these before the fixes are built. The recommended option comes first.

{id} [{header}] {question} Gates {j("P%d" % g for g in gates)}.
1. (recommended) {label}: {consequence}
2. {label}: {consequence}
                                                  <- blank line between calls
Conflicts resolved:
- {conflict}: {resolution}

## Plan ({n} items, dependency order)

=== P{priority} {title} [{"; ".join(variants)}]
WHY: {why}                                        <- a list renders as "WHY:" then "- item" lines
CHANGE: {change}
ACCEPT:
- {check}, {kind}: {target}; baseline {baseline}[; wrong build {wrong_build}]
GUARD RAILS:
- {guard_rails[i]}
DEPENDS: {j("P%d" % d) or "none"}[; gated by {j(gated_by)}]
SOURCES: {j(source_ids)}[ (items {j(merged)})]
                                                  <- blank line between blocks
## FIXSTATUS (round-{N} ledger)

- {fix} {status}: {note}                          <- ledger order

## REJECTED (don't re-report)

Findings:
- {id}: {reason}
Sub-claims:
- {finding id}: {reason}
Fix parts and targets:
- {id}: {reason}

- {id}: {reason}                                  <- rows whose id starts with "round-"

## DEFERRED

- {id}[ ({j(finding ids of cluster id)})][ {title}][ [{severity}]]: {reason.rstrip(".")}.[ Default: {default}.] Round {target_round}.

## KEEP-AS-IS (regression contract for round {N+1})

- {keep_as_is[i]}

## Stopping rule

{"Met" if met else "Not met"}: {why}

Round {N+1}: {preamble}
1. {part 1}
2. {part 2}
```
`preamble` and parts come from `re.split(r"\s*\((\d+)\)\s*", next_round)`: element 0 is the preamble, odd elements the
numbers, even ones the texts, a trailing `;` stripped. Round 2's `round3` gives 5 parts.

#### 5.4.5 Wrapping

`textwrap.fill(width=120, break_long_words=False, break_on_hyphens=False)` with prefixes: paragraphs, `WHY:`/`CHANGE:`
strings and design-call lines none; `- ` bullets `- ` then two spaces; `1. ` options and parts `1. ` then three spaces.
Never wrapped: headings, `=== `, `SC: `, `INV: `.

#### 5.4.6 review_result.json (`--result`)

Same shape as round 2: `{round, date, counts, [lead_measurements], plan, design_calls, confirmed, rejected, fix_status,
stop_rule, merged}`. Every key except `counts` (§5.4.3) and `merged` (merged.json's path relative to the round dir) is
copied from lead.json unchanged, in that key order; `spot_check` and `not_checked`, when present, follow `stop_rule`.
Next round's ledger step reads this file as it did in round 2.

#### 5.4.7 Functions (file order)

```python
WIDTH = 120
FID_RE = re.compile(r"^([a-z0-9_]+-\d+)\b")
def load_inputs(args) -> tuple[dict, dict, list[str] | None, str | None]   # merged, lead, ledger_ids, existing_md
def finding_ids(source_ids: list[str]) -> list[str]
def next_round_text(lead: dict, n: int) -> str | None                      # "next_round", else "round{n+1}"
def validate(merged, lead, ledger_ids) -> tuple[list[str], list[str]]      # errors, warnings (V1-V10, W1-W2)
def compute_counts(merged, lead) -> dict
def wrap(text: str, first: str = "", cont: str = "") -> list[str]
def section_decisions(existing_md: str | None) -> list[str]
def section_intro(merged, lead, counts) -> list[str]
def section_overall(lead) -> list[str]
def section_scorecard(lead) -> list[str]
def section_design_calls(lead) -> list[str]
def section_plan(lead) -> list[str]
def section_fixstatus(lead, n, ledger_ids) -> list[str]
def section_rejected(lead) -> list[str]
def section_deferred(lead) -> list[str]
def section_keep(lead, n) -> list[str]
def section_stop(lead, n) -> list[str]
def render(merged, lead, ledger_ids, existing_md) -> str                   # "\n".join(...) + "\n"
def build_result(merged, lead, counts, merged_rel: str) -> dict
def main(argv: list[str] | None = None) -> int
```

### 5.5 Main-session runbook (round 3)

```bash
PY=$(bash ~/.claude/skills/sd-material-research/scripts/setup_env.sh); S=~/.claude/skills/sd-material-research/scripts
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2
R="$HOME/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools/review/round3"
# Agent-tool route only (the workflow's merge agent already did this):
"$PY" "$S/merge_panel.py" --round-dir "$R" --lenses fixcheck,regressions_g1,realism,g5_tiling,decals
#   then launch the lead (§5.3.1) -> $R/lead.json
"$PY" "$S/render_findings.py" --round-dir "$R" --check
"$PY" "$S/render_findings.py" --round-dir "$R" --result "$R/review_result.json"
# gate: ask design_calls as-is; write DECISIONS into findings.md; a re-render keeps it
```
If merged.json lists `missing_lenses` after a workflow run, restore that lens's JSON from the workflow transcript's
`journal.jsonl` (it records each agent's return value) into `$R/<key>.json`, re-run merge_panel.py, then re-run the lead.

### 5.6 Tests: SK/tests/test_review_pipeline.py

`unittest`; inserts SK into `sys.path`. Fixture dir `$SDMR_ROUND2_DIR`, default
`~/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools/review/round2`; fixture tests `skipTest` when it is
missing. Output goes to `tempfile.TemporaryDirectory()`, never into the fixture folder (round 2's gate is paused and its
findings.md is not saved). Run from S: `SDMR_ROUND2_DIR=... "$PY" -m unittest discover -s scripts/tests -v`.

C-syn (synthetic, no fixture):

| test | input | expected |
|---|---|---|
| `test_classify` | verdicts: None; (real F, none, medium); (F, metric, none); (T, none, none); (T, metric, none); (T, none, low); (T, quantisation, medium) | unverified; rejected/not_real; rejected/not_real; rejected/severity_none; rejected/severity_none; confirmed; confirmed_subclaim |
| `test_classify_js` | same 7 | F, F, F, F, F, T, F |
| `test_discover` | tmp dir: `a.json`, `a_verify.json`, `b.json`, `b_verify_b.json`, `b_verify_a.json`, `ab.json`, `ledger.json` (`{"items":[]}`), `review_result.json` | lenses `[a, ab, b]`; `a` -> `[a_verify.json]`; `ab` -> `[]`; `b` -> `[b_verify_a.json, b_verify_b.json]` |
| `test_lenses_missing` | same dir, `--lenses a,b,c` | exit 0; `missing_lenses == ["c"]`; summary line ends `; no lens file: c` |
| `test_unverified_reason` | lens `a` with findings a-1 (high), a-2 (low), no verifier file | a-1 `verifier_missing`, a-2 `low`; `missing_verifiers == ["a"]`; with only a-2: `missing_verifiers == []` |
| `test_not_checked` | `a.json` with `not_checked: ["x"]`, `a_verify.json` with `not_checked: ["y"]` | merged `not_checked` == [{lens a, file a.json, text x}, {lens a, file a_verify.json, text y}] |
| `test_duplicate_verdict` | the same id in `b_verify_a` and `b_verify_b` | `main()` returns 2; no merged.json |
| `test_missing_key` | a finding without `acceptance` | returns 2; the error names the file and the id |
| `test_ledger_key` | `"P10 ..."`, `"D3: x"`, `" P1"`, `"R7 process"`, `"INV-2 all"` | P10, D3, P1, other, other |
| `test_wrap` | a 300-char bullet | every line <= 120; the first starts `- `, the rest with two spaces |
| `test_decisions_kept` | an existing md with `## DECISIONS (user, 2026-10-05)\n\n- Q1: option 1\n\n## OVERALL` | output contains both lines verbatim and not `(to be filled after the gate)` |
| `test_v4_no_reject_confirmed` | lead with a REJECTED row naming a confirmed id | `validate` returns 1 error |
| `test_spot_check_line` | fixture-shaped lead plus `spot_check {id: "x-1", result: "ok"}` | OVERALL contains `Spot check: x-1: ok` |

C-merge (merge on round 2):

| assertion | expected |
|---|---|
| lenses | `[decal_patches, decal_potholes, fixcheck, g1_requirements, g5_tiling, realism_lane, realism_onfoot, regressions]`; 12 verifier files; `missing_verifiers == ["regressions"]`; `missing_lenses == []` |
| counts | findings 35; confirmed 26; confirmed_subclaim 4; unverified 3; rejected 2; `by_final_severity == {"high":3,"medium":21,"low":9}` (= review_result `counts.confirmed_by_severity`) |
| confirmed_subclaim | `[decal_potholes-2, fixcheck-1, g1_requirements-1, realism_onfoot-4]` (sorted), equal to the ids of review_result's `sub-claim <id>` rows |
| unverified | `[regressions-1, regressions-2, regressions-3]`; `unverified_reason` verifier_missing, verifier_missing, low |
| rejected | `fixcheck-2` (not_real), `g5_tiling-4` (severity_none), equal to review_result's bare-finding-id REJECTED rows |
| main check | `set(confirmed + confirmed_subclaim + unverified)` == the 33 finding ids parsed (FID_RE) from review_result `confirmed[].source_ids`; the exceptions are exactly the 4 sub-claim ids (status `confirmed_subclaim`) and the 3 unverified ids (lead-judged) |
| JS parity | `classify_js` over the same verdicts: 26 true, 9 false; the 9 = 2 rejected + 4 sub-claim + 3 unverified |
| fix_status | 69 reports, 35 checks. Per id (reports, checks): P1 (3,0) P2 (4,0) P3 (3,2) P4 (3,1) P5 (4,2) P6 (3,2) P7 (4,0) P8 (5,3) P9 (2,1) P10 (3,3) D1 (5,1) D2 (3,2) D3 (2,1) D4 (3,1) D5 (2,1) D6 (3,3) D7 (6,3) D8 (3,1) D9 (3,2) D10 (5,3) other (0,3: g1_requirements_verify_b's R7, INV-2, INV-10 rows); key order P1..P10, D1..D10, other; `ledger_ids_without_report == []` |
| other lists | strengths 49, answers 9, answer_checks 13, orphan_verdicts 0, not_checked 0 |
| hints | 37 (file 10, site 18, inv 9); `file:composite_decal.py` ids `[decal_patches-4, g1_requirements-1, g1_requirements-5, regressions-1]`; `inv:INV-16` has 10 ids; all 19 cross-lens id pairs inside review_result's 22 clusters share >= 1 hint |
| summary line | exactly the round-2 line of §5.2.1 |
| idempotent | two runs give identical JSON except `generated` |

C-render (merged.json from C-merge + review_result.json as lead.json):

| assertion | expected |
|---|---|
| `--check` | 0 errors, 0 warnings |
| `## ` headings in order | `DECISIONS (user)`, `OVERALL`, `Scorecard`, `Design calls`, `Plan (8 items, dependency order)`, `FIXSTATUS (round-2 ledger)`, `REJECTED (don't re-report)`, `DEFERRED`, `KEEP-AS-IS (regression contract for round 3)`, `Stopping rule` |
| intro | contains `Totals: 35 findings, 33 confirmed (3 high, 21 medium, 9 low) and 2 rejected. They merge into 22 items, C1-C22 in the JSON.` (wrapped lines joined with spaces) and `the lead confirmed 3 and rejected 0` |
| OVERALL | the `Lead measurements:` line; `### Premises corrected` with 22 bullets; no `### Re-measured by the lead`, no `Spot check:`, no `### Not checked` (absent in the fixture) |
| Scorecard | 15 lines `^SC: `, 16 lines `^INV: ` |
| Design calls | 7 lines `^Q\d+ \[` in order Q1..Q7; 23 lines `^\d+\. `; `(recommended)` 7 times, each on the first option; 15 bullets after `Conflicts resolved:` |
| Plan | 8 lines `^=== P\d+ `, P1..P8 in order; each block has WHY:, CHANGE:, ACCEPT:, GUARD RAILS:, DEPENDS:, SOURCES: in that order; 63 `- ` lines between ACCEPT: and GUARD RAILS: (9/15/4/6/13/6/4/6); 50 between GUARD RAILS: and DEPENDS: (4/7/4/7/9/6/5/8); P3's line `DEPENDS: P1, P2; gated by Q7` |
| FIXSTATUS | 20 bullets, the first `- P1 partial:`, in ledger order P1..P10, D1..D10 |
| REJECTED | 39 bullets: Findings 2, Sub-claims 4, Fix parts and targets 32, carry-forward 1 (`- round-1 REJECTED:`) |
| DEFERRED / KEEP-AS-IS | 9 / 14 bullets; the first DEFERRED line starts `- C12 (realism_lane-5) V2 L lines straight, full-dark tips [medium]:` |
| Stopping rule | starts `Not met: 3 high findings;`; `Round 3: Third full round` followed by 5 lines `^\d+\. ` |
| line length | no line over 120 chars except those starting `#`, `=== `, `SC: `, `INV: ` |
| `--result` | `build_result(...)` minus key `merged` == the fixture dict (same `counts`, every other key identical) |
| DECISIONS | placeholder `(to be filled after the gate)` present (no existing file in the temp dir) |

The rendered file will not match the lead's 416-line hand-back word for word (its OVERALL and WHY prose was richer than
the JSON); the tests check structure and counts. The expected numbers come from a scratch prototype on the round-2
files; the rendered output itself was not produced, so C-render's line counts are checked against review_result.json,
not against a rendered file.

## 6. Skill, prompt and brief edits

### 6.1 S/references/review.md (in git)

**(a) §1 preflight.** Keep items 1-4 (lines 11-18). Replace lines 19-20:
```
5. Write or append `review/BRIEF.md` (§2).
6. Leave Designer idle. Reviewers work from files only.
```
with:
```
5. Build the shared review cache and self-test the review kit, in the background while you do 6. Anything that two
   reviewers would otherwise rebuild (a composite, a resampled layer stack) is built once; reviewers read it and never
   rebuild it. Asphalt: `composite_decal.py --out review/round<N>/decal/composite --build-only` (~90 s) and
   `checks/review_kit.py --selftest`. A failing self-test blocks the round like a hard check.
6. Check that `review/REFERENCE.md` is current (its `Valid for` line names the exports you measured), then write the
   delta brief `review/round<N>/BRIEF.md` (§2).
7. Leave Designer idle. Reviewers work from files only.
```

**(b) §2.** Replace lines 22-46 (heading and items 1-10) with the block below. Lines 47-56 (items 11 and 12) stay word
for word under a new lead-in, `**Severity rubric and acceptance-target rules** (delta §6; copy them into each delta
brief):`, with their item numbers dropped. Delete line 57 (item 13); R9 now holds the checklist.
```
## 2. Reference and delta brief

Round 2's brief was rebuilt from scratch by four agents (19 min on the critical path), though most of it hadn't
changed since round 1. Split it in two.

**`review/REFERENCE.md` (persistent).** Written with round 1's brief. The builder updates the changed sections at
the end of every apply session (stage 7). Its sections:
- **R1 Requirements:** verbatim, ids R1..Rn, each hard or soft; interview answers; defaults; intentional deviations.
- **R2 Physics digest** from the spec: the layer model and ASCII cross-section; the process cards (acts on, reveals,
  **Never**, where, shape and scale); invariants INV-1..k with their check ids; the sheet's common-mistakes table as
  the watch list.
- **R3 Scale:** tile m, px, mm/px, height depth per variant, normal format, viewing distance of each view.
- **R4 Graph architecture:** sections in build order with node names and current parameters; the composition
  (max/min/lerp); which masks come from the layout only.
- **R5 Node semantics cheat sheet:** `sd_craft.md` §5. Histogram Scan direction and Blend divide order have caused
  wrong fixes.
- **R6 Variant presets** table.
- **R7 Files:** maps per variant; the loader snippet with its verified output; region names; previews; the preview
  shader and its caveats (one light, height-field shadows on the raking views only, no IBL; judge colour from
  albedo-only views); side reports; shared caches and the review kit.
- **R8 Metric caveats and deprecations.**
- **R9 Verifier checklist** (§4).
It opens with `Valid for:` (export and package times), `Changed in the last update:` (section ids) and a table of
which role reads which section.

**`review/round<N>/BRIEF.md` (delta, at most 250 lines).** Every agent reads it in full, plus R1 and the REFERENCE
sections its row in the lens table names. In round 1 there is no REFERENCE yet: write it first, then a delta with
§1 and §6-§9. Template, with a line budget per heading:

| heading | lines | content |
|---|---|---|
| `# Round <N> delta brief (<date>)` + preflight | 10 | export and scorecard times, identity check, cache and kit self-test, REFERENCE `Valid for` |
| `## 1. Rules` | 25 | Designer off; read-only inputs except your own result file; never run the shared generators with their default outputs; write only under `review/agents/round<N>/<key>/`; Python path; thread cap; time boxes and finding cap |
| `## 2. Requirement changes and decisions` | 30 | R-ids added or reworded (full text); the last gate's DECISIONS verbatim. Older decisions live in R1 |
| `## 3. Scorecard delta` | 45 | hard failures (expect none); invariants pass/fail per graph; each metric the ledger's acceptance names, before → after; new metric caveats. Name the scorecard files, don't copy them |
| `## 4. Ledger` | 30 | one line per item: id, change in a few words, builder's status, acceptance numbers |
| `## 5. Keep-as-is, rejected, deferred` | 35 | keep-as-is (the regression contract) one line each; rejected and deferred as id + reason in ≤ 12 words, with a pointer to the last findings.md |
| `## 6. Severity rubric and acceptance-target rules` | 15 | the text below |
| `## 7. Shared tools` | 15 | cache paths and how to load them; review-kit functions, one line each; what not to rebuild |
| `## 8. Output` | 10 | result paths; schema names in `review_round.js` (FINDINGS, VERDICTS, LEAD); `not_checked` |
| `## 9. Lenses and owners` | 30 | key, scope, owned items, REFERENCE sections, early or not, time box (§3) |
| total | ≤ 245 | |
```

**(c) §3.** Replace lines 75-81:
```
**Round 2 and later: 3-5 lenses.**
- **Fixcheck:** fill `fix_status` for every ledger item.
- **Regressions:** check the keep-as-is contract and compare previous and current numbers.
- **Fresh-eyes realism:** what still reads CG at 1:1 and 3×?
- Plus G1 and G5.

**Final round: 3 lenses.** Fixcheck; requirements plus tiling; realism plus regressions.
```
with:
```
**Round 2 and later, the final round included: 3-5 lenses.**
- **Fixcheck:** `fix_status` for every ledger item, re-measured.
- **Regressions + G1:** the keep-as-is contract, previous vs current numbers, one verdict per R-id and INV-id.
- **Fresh-eyes realism:** what still reads CG at 1:1 and 3×?
- **G5** tiling.
- A lens for a graph still in its first fix cycle (asphalt round 3: decals).
With a small ledger, merge them into 3: fixcheck; requirements + tiling; realism + regressions.

**One owner per hypothesis.** Every builder hypothesis, open question, user question and issue cluster carried over
from the last round goes to exactly one lens in the delta brief's lens table. Other lenses skip it and may name it in
`not_checked`. In round 2, four clusters were each found by 2-4 lenses and verified 2-4 times.

**Early lenses.** Fixcheck and G5 need only the rules, REFERENCE R1 + R7 and the ledger. Start them as soon as the
ledger is written, while the delta brief is being written.
```

**(d) §4.** Line 108 `## 4. Adversarial verification (one verifier per non-empty lens)` becomes
`## 4. Adversarial verification (high and medium findings)`. Insert after it, before item 1:
```
Verify **high and medium** findings only. Lows go to the lead unverified, and the lead spot-checks one. Each lens with
a high or medium finding gets one verifier, started as soon as that lens finishes. Split it in two (`_verify_a`,
`_verify_b`, the two halves of the list in severity order) only when the lens has 5 or more. Because each hypothesis
has one owner (§3), each issue cluster is verified once. A high or medium finding whose verifier returned nothing goes
to the lead as unverified, never as rejected. If an artifact explains only part of a finding, the verifier keeps
real=true, sets `artifact` to that label and names the sub-claim in `premise_errors`.
```

**(e) §5.** Replace lines 142-144:
```
**Outputs:**
- `review/round<N>/review_result.json`
- `review/round<N>/findings.md`, in this format:
```
with:
```
**Outputs.** `scripts/merge_panel.py` merges the lens and verifier JSON into confirmed / confirmed (sub-claim
artifact) / unverified / rejected findings, fix_status evidence per ledger id and cluster hints, in
`review/round<N>/merged.json`. The lead reads it and writes only its judgement as JSON (`LEAD` in
`assets/workflows/review_round.js`: clusters, plan, scorecard, design calls, OVERALL, fix_status, stop rule, spot
check) to `review/round<N>/lead.json`. `scripts/render_findings.py`, run in the main session, checks lead.json against
the merge and renders:
- `review/round<N>/review_result.json`
- `review/round<N>/findings.md`, in this format:
```
Lines 145-150 stay.

**(f) §6.** Replace lines 169-180 (the whole section) with:
```
## 6. Running it

**Budget.** Put it in the delta brief's rules and in every prompt.
- CPU: 2 threads per agent (`OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2`, plus
  `VECLIB_MAXIMUM_THREADS=2` on macOS; `cv2.setNumThreads(2)`), and one Python process per agent at a time. In round 2,
  12 agents at default thread counts ran 32 logical CPUs at 73 % until the user asked for a cap mid-round.
- At most 8 agents at once. Split a verifier only for a lens with 5 or more high/medium findings.
- Time boxes, stated in each prompt: lens ≤ 35 tool calls (~15 min), verifier ≤ 25 (~12 min), lead ≤ 30 (~15 min).
  An agent stops at its box or at the finding cap and lists what it didn't check (`not_checked`).
- Mechanical agents (fixcheck's re-measurement, a number diff, the merge) may run at lower effort. Realism lenses,
  verifiers and the lead keep the session's model and effort.

**Workflow** (when the user has opted into workflows: ultracode is on, or they asked; it is the faster route):
`Workflow({scriptPath: "<skill>/assets/workflows/review_round.js", args: {...}})`. The args are documented in the
script: `review_dir`, `round`, `date`, lenses with `early` / `effort`, an optional `brief_task` that writes the delta
brief while the early lenses run, `max_concurrent` (8), `time_box`, `threads`. It pipelines lens → verifier
(high/medium only), runs `scripts/merge_panel.py` in a low-effort agent, runs the lead and returns only the merge line,
the `lead.json` path and counts, so the main session gets no per-agent hand-backs. Resume an interrupted run with
`resumeFromRunId`.

**Without workflows** (Agent tool):
1. As soon as the ledger is written, spawn the early lenses (fixcheck, G5) in the background.
2. Write the delta brief, then spawn the other lenses in one message.
3. When a lens returns, spawn its verifier for its high and medium findings only.
4. Run `scripts/merge_panel.py --round-dir review/round<N> --lenses <keys>`, then the lead in a fresh Agent that
   reads `merged.json`.
Each agent writes its JSON to its file (with Python `json.dump`) and returns at most 8 lines.

**After the panel, in the main session:** `scripts/render_findings.py --round-dir review/round<N> --check`, then
`--result review/round<N>/review_result.json`. Read findings.md's scorecard, plan and design calls, not the lens files.

**While the panel runs,** prepare the next fix batch from the numeric results. Never edit the maps the panel is
reading, and never call Designer from a subagent.
```

### 6.2 S/assets/workflows/review_round.js (in git)

Lines 1-10 (`meta`): line 7 detail -> `'adversarial re-measurement of high and medium findings'`; line 8 detail ->
`'merge in code; lead: plan, scorecard, design calls'`.

Schemas: keep FINDINGS (:26-49) and VERDICTS (:51-70) with one addition each; delete PLAN (:72-93) and put §5.3.2's
`STR`/`STRS`/`INTS`/`LEAD` in its place.
- Before FINDINGS: `const NOT_CHECKED = { type: 'array', items: { type: 'string' }, description: 'what you did not check and why (time box, finding cap, owned by another lens)' }`.
- FINDINGS: add `not_checked: NOT_CHECKED,` after `strengths` (line 46); `required: ['findings', 'fix_status',
  'strengths', 'not_checked']`.
- VERDICTS: add `not_checked: NOT_CHECKED,` after `verdicts`; `required: ['verdicts', 'not_checked']`.

Replace lines 12-24 (args comment and constants) and 95-160 (COMMON to the end) with the code below; the schemas stay
between them.
```js
// args:
//   review_dir     absolute path of <tools>/review (REFERENCE.md here; round<N>/ holds BRIEF.md, ledger.json, previews, results)
//   round          round number (1, 2, ...)
//   date           YYYY-MM-DD for lead.json (workflow scripts cannot call Date)
//   lenses         [{key, prompt, early?, effort?, model?, sections?}], built from the spec (references/review.md §3)
//                    early     true: start before round<N>/BRIEF.md exists (reads the rules, REFERENCE R1 + R7, the ledger)
//                    effort    agent() effort for a mechanical lens ('low' | 'medium'); omit to inherit
//                    model     agent() model override; omit to inherit
//                    sections  REFERENCE ids this lens reads besides R1, e.g. ['R2', 'R7'] (the brief's lens table repeats them)
//   brief_task     optional prompt: an agent writes round<N>/BRIEF.md while the early lenses run; omit when it exists
//   max_findings   optional, default 7 / 6 / 5 for rounds 1 / 2 / 3+
//   max_concurrent optional, default 8: agents running at once in this workflow
//   time_box       optional, default {lens: {calls: 35, min: 15}, verify: {calls: 25, min: 12}, lead: {calls: 30, min: 15}}
//   threads        optional, default 2: numpy / OpenCV threads per agent
//   python         optional, the venv python (default: output of setup_env.sh)
//   skill_dir      optional, default ~/.claude/skills/sd-material-research
const A = args
const R = A.round || 1
const DIR = A.review_dir
const RD = `${DIR}/round${R}`
const MAXF = A.max_findings || (R === 1 ? 7 : R === 2 ? 6 : 5)
const MAXFIX = R === 1 ? 10 : R === 2 ? 8 : 5
const MAXC = A.max_concurrent || 8
const TB = Object.assign({ lens: { calls: 35, min: 15 }, verify: { calls: 25, min: 12 }, lead: { calls: 30, min: 15 } }, A.time_box || {})
const TH = A.threads || 2
const SKILL = A.skill_dir || '~/.claude/skills/sd-material-research'
const PY = A.python || `$(bash ${SKILL}/scripts/setup_env.sh)`

// ... NOT_CHECKED, FINDINGS, VERDICTS, STR/STRS/INTS, LEAD ...

const COMMON = `Read ${RD}/BRIEF.md (the round-${R} delta brief, at most 250 lines) completely, then section R1 of
${DIR}/REFERENCE.md and the REFERENCE sections the brief's lens table lists for you. If BRIEF.md does not exist yet (early
lenses), read REFERENCE R1 and R7 and ${RD}/ledger.json; the rules are below. Round files are in ${RD}/.
Never call substance-designer tools (Designer is single-threaded and reserved for the builder).
Read-only inputs, except your own result file named below. Helper scripts and images ONLY under ${DIR}/agents/round${R}/<your-label>/.
Python: ${PY}  (numpy, scipy, Pillow, OpenCV). Import ${SKILL}/scripts/matcheck.py (load_image, Ctx, regions, label_wrap)
and the material's review kit and caches (brief, Shared tools) instead of writing decoders or rebuilding composites.
CPU: start every Python run with OMP_NUM_THREADS=${TH} OPENBLAS_NUM_THREADS=${TH} MKL_NUM_THREADS=${TH} NUMEXPR_NUM_THREADS=${TH}
VECLIB_MAXIMUM_THREADS=${TH}, call cv2.setNumThreads(${TH}) after importing cv2, and run one Python process at a time.
Write your JSON to the file named below with Python json.dump (indent 1, ensure_ascii False, UTF-8), check it with
json.load, and return the same object.`
const BOX = k => `TIME BOX: at most ${TB[k].calls} tool calls (about ${TB[k].min} min). Stop at the box or the finding cap,
whichever comes first, and list in not_checked what you did not get to.`

// agent() behind the max_concurrent gate (the Workflow tool's own cap is min(16, CPUs - 2))
let running = 0
const waiting = []
async function run(prompt, opts) {
  while (running >= MAXC) await new Promise(res => waiting.push(res))
  running++
  try { return await agent(prompt, opts) } finally { running--; const next = waiting.shift(); if (next) next() }
}
const pick = l => Object.assign({}, l.effort ? { effort: l.effort } : {}, l.model ? { model: l.model } : {})

const lenses = A.lenses || []
phase('Review')
const briefDone = A.brief_task
  ? run(`${A.brief_task}
Write ${RD}/BRIEF.md only, at most 250 lines, from the template in ${SKILL}/references/review.md §2. Return its line count.`,
      { label: 'brief', phase: 'Review' })
  : Promise.resolve(null)

const results = await pipeline(lenses,
  async l => {
    if (!l.early) await briefDone
    return run(`${COMMON}
${BOX('lens')}
Be concrete and critical, like a senior material artist reviewing for production. Every finding cites files, coordinates
and numbers, names its cause in the graph, proposes a node/parameter-level fix and an acceptance check. Only report problems
that map to a requirement id, an invariant id or a cited spec fact; say "taste" otherwise. Do not re-report items the brief
lists as rejected or keep-as-is unless they regressed. Skip hypotheses and questions the lens table gives to another lens.
Return 0-${MAXF} findings, most severe first, with ids "${l.key}-<n>"; fill fix_status for every ledger item if the lens
table gives you the ledger (else leave it empty). Write ${RD}/${l.key}.json.

LENS ${l.key}: ${l.prompt}`, Object.assign({ label: `review:${l.key}`, phase: 'Review', schema: FINDINGS }, pick(l)))
  },
  async (rev, l) => {
    const hm = rev && rev.findings ? rev.findings.filter(f => f.severity === 'high' || f.severity === 'medium') : []
    if (hm.length === 0) return { lens: l.key, rev, verdicts: [] }
    const h = Math.ceil(hm.length / 2)
    const parts = hm.length >= 5 ? [['_a', hm.slice(0, h)], ['_b', hm.slice(h)]] : [['', hm]]
    const vs = await parallel(parts.map(([s, fs]) => () => run(`${COMMON}
${BOX('verify')}
You are the adversarial verifier for lens ${l.key}: its high and medium findings (lows go to the lead unverified). Apply
the verifier checklist (REFERENCE R9) to EACH finding: reproduce at least one key number with your own script on full-res
maps; refute claim by claim (visible? preview shader? downsampling? metric artifact? wrong premise? basis? controls for
statistical claims? does the consequence follow?). Correct overstated numbers and downgrade rather than reject; real=false
only when the core is unsupported. If an artifact explains only part of a finding, keep real=true, set artifact to that
label and name the sub-claim in premise_errors. Do not count the same review-kit function on the same input as independent
confirmation; state the method of each re-measured number. Review each fix (does it create a singular feature or lattice,
a bevel, break an invariant or registration, conflict with a requirement?) and the acceptance target (reachable on current
data, checked against a baseline?). Write ${RD}/${l.key}_verify${s}.json.

FINDINGS:
${JSON.stringify(fs, null, 1)}`, { label: `verify:${l.key}${s}`, phase: 'Verify', schema: VERDICTS })))
    return { lens: l.key, rev, verdicts: vs.filter(Boolean).flatMap(v => v.verdicts || []) }
  })
const noResult = lenses.filter((l, i) => !results[i] || !results[i].rev).map(l => l.key)
if (noResult.length) log(`no lens result: ${noResult.join(', ')}`)

phase('Synthesize')
const merge = await run(`Run exactly this one command and return its last stdout line verbatim. If it exits non-zero,
return "MERGE FAILED: " followed by its first stderr line. Do nothing else.
${PY} ${SKILL}/scripts/merge_panel.py --round-dir ${RD} --lenses ${lenses.map(l => l.key).join(',')}`,
  { label: 'merge', phase: 'Synthesize', effort: 'low' })
log(merge || 'merge: no result')
if (!merge || !merge.startsWith(`round ${R}:`))
  return { round: R, merge, lead_json: null, error: 'merge failed: fix the files, run merge_panel.py, then resume this run' }

const lead = await run(`${COMMON}
${BOX('lead')}
You are the lead material artist for round ${R}. Read ${RD}/merged.json: counts, index, missing_lenses, missing_verifiers
and cluster_hints first; open findings[i] only when you need its evidence. Do not re-read lens or verifier files, write
findings.md, compute counts or copy findings.
1. Cluster every confirmed, confirmed_subclaim and unverified finding into C1..Ck (confirmed[] in your JSON), using
   cluster_hints; keep source ids; a partial member is "<id> (<part>)".
2. Re-measure at least one unverified finding and record it in spot_check; a high or medium there lost its verifier, so
   check its key number before planning on it. Put each unverified id in a cluster or in a REJECTED row whose id is
   exactly the finding id.
3. For each confirmed_subclaim, add a REJECTED row "sub-claim <id>" naming the sub-claim its artifact label refers to.
4. Plan at most ${MAXFIX} fixes in dependency order (layout -> height/structure -> process masks -> colour -> micro-detail),
   each with acceptance rows {check, kind, target, baseline[, wrong_build]} and guard rails. Put what only the user can
   decide in design_calls (2-4 options, the recommended one first, header <= 12 chars), cross-linked by gates / gated_by.
5. Scorecard (one row per requirement per graph) and invariants from the current scorecards; one fix_status row per
   ledger id (from merged.fix_status); keep-as-is, deferred, conflicts resolved, premises corrected (Histogram Scan
   centre = 1 - Position; Blend divide = dst/src), overall assessment, stop rule; missing lenses or verifiers and what
   you skipped go in not_checked.
round = ${R}; date = "${A.date || 'today, YYYY-MM-DD'}". Write ${RD}/lead.json. A script renders findings.md from it.`,
  { label: 'synthesize', phase: 'Synthesize', schema: LEAD })

return { round: R, merge, no_result: noResult, lead_json: lead ? `${RD}/lead.json` : null,
  fixes: lead ? lead.plan.fixes.length : 0, design_calls: lead ? lead.design_calls.length : 0,
  stop_met: lead ? lead.stop_rule.met : null }
```

### 6.3 S/SKILL.md (in git)

Stage 6: replace lines 106-114 with:
```
Follow `references/review.md`:
1. Preflight: scorecards, previews, the fix ledger, the shared review cache and the kit's self-test.
2. Check that `review/REFERENCE.md` is current, and write the delta brief `review/round<N>/BRIEF.md` (≤ 250 lines).
3. Run lenses derived from the spec (4-6 in round 1, 3-5 later, one owner per hypothesis), and verify their high and
   medium findings adversarially.
4. Merge in code (`scripts/merge_panel.py`). The lead returns the plan, the design calls and OVERALL as JSON, and
   `scripts/render_findings.py` renders findings.md in the main session.

Budget every agent: 2 threads, at most 8 agents at once, time boxes (`references/review.md` §6). Use the Workflow
(`assets/workflows/review_round.js`) when the user has opted into workflows (ultracode is on, or they asked); it is the
faster route. Otherwise run the same agents with the Agent tool. Reviewers never call Designer. While the panel runs,
prepare the next fixes from the numbers.
```
Stage 7, line 117: after `fill the ledger with measured acceptance, re-measure,` insert
`update the changed sections of review/REFERENCE.md and its Valid for line,`.

### 6.4 Tests for §6.1-§6.3

| id | test | expected |
|---|---|---|
| D1 | `f=S/assets/workflows/review_round.js; (echo 'async function __wf(args, agent, parallel, pipeline, phase, log) {'; sed '/^export const meta/,/^}/d' "$f"; echo '}') > /tmp/rr.js && node --check /tmp/rr.js` (Node is optional) | exit 0 (the meta block, lines 1-10, is removed; the top-level `return` becomes legal inside the wrapper) |
| D2 | code review: in NOT_CHECKED, FINDINGS, VERDICTS and LEAD every name in `required` is a key of `properties` | true (the Workflow tool throws at `agent()` otherwise) |
| D3 | review.md delta template budgets | sum 245 ≤ 250 |
| D4 | `grep -n "Agent tool" S/SKILL.md S/references/review.md` | only the "Otherwise ... Agent tool" and "Without workflows (Agent tool)" lines |

The merge rule's parity with the old JS rule is C-merge "JS parity" (§5.6); D's Node harness is not needed.

### 6.5 T/review/REFERENCE.md: create once from the round-2 brief

These move from T/review/BRIEF.md (1,779 lines; "# Round 2" starts at line 500) into REFERENCE:

| id | REFERENCE section | BRIEF.md source (round-2 part) | lines |
|---|---|---|---|
| R1 | Requirements (stable part) | `## 2. User requirements …` up to `**Decisions after reviewer round 1**` (541-576) | 36 |
| R2 | Physics digest | `## 3. Physics digest` (629-807): layer model, process cards, invariants + check ids, watch list | 179 |
| R3 | Scale | `## 4. Scale` (808-876) | 69 |
| R4 | Graph architecture | `## 5. Graph architecture` (877-1004) | 128 |
| R5 | Node semantics cheat sheet | `## 6.` (1005-1033) | 29 |
| R6 | Variant presets | `## 7.` (1034-1090) | 57 |
| R7 | Files + loader, regions, previews, shader caveats, side reports | `## 8. Files` (1091-1188) | 98 |
| R8 | Metric caveats and deprecations | `### 9.6` (1403-1469) | 67 |
| R9 | Verifier checklist | `## 13.` (1705-1722) | 18 |
| | total | | 681 |

These stay in the delta, rewritten each round: preamble and preflight (500-516), §1 rules, the decisions part of §2
(577-628), §9.1-9.5 scorecard (as deltas), §10 history / keep-as-is / rejected / deferred / questions, §11-12 rubric and
target rules, §14 schemas (as names only), §15 lenses. Round 1's sections (8-499) stay in BRIEF.md as history.

Slicer (one-time, `"$PY" -`; verified on Windows, sizes as in the table):
```python
import os
T = os.path.expanduser("~/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools")
src = open(os.path.join(T, "review", "BRIEF.md"), encoding="utf-8").read().split("\n")
L = src[src.index("# Round 2 (2026-10-03): lane, detail and decals"):]
SECTIONS = [  # (id, title, block starts with, block ends before the first later line starting with)
    ("R1", "Requirements", "## 2. User requirements", "**Decisions after reviewer round 1**"),
    ("R2", "Physics digest", "## 3. Physics digest", "## 4. "),
    ("R3", "Scale", "## 4. Scale", "## 5. "),
    ("R4", "Graph architecture", "## 5. Graph architecture", "## 6. "),
    ("R5", "Node semantics cheat sheet", "## 6. Node semantics", "## 7. "),
    ("R6", "Variant presets", "## 7. Variant presets", "## 8. "),
    ("R7", "Files, loader, regions, previews, shader caveats, shared tools", "## 8. Files", "## 9. "),
    ("R8", "Metric caveats and deprecations", "### 9.6 Metric caveats", "## 10. "),
    ("R9", "Verifier checklist", "## 13. Verifier checklist", "## 14. "),
]
body, sizes = [], {}
for sid, title, head, stop in SECTIONS:
    i = next(k for k, s in enumerate(L) if s.startswith(head))
    j = next(k for k in range(i + 1, len(L)) if L[k].startswith(stop))
    blk = L[i:j]; blk[0] = "## %s. %s" % (sid, title); sizes[sid] = len(blk); body += blk
HEADER = open(os.path.join(T, "review", "REFERENCE_header.md"), encoding="utf-8").read().rstrip("\n").split("\n")
open(os.path.join(T, "review", "REFERENCE.md"), "w", encoding="utf-8", newline="\n").write("\n".join(HEADER + [""] + body) + "\n")
print(sizes, sum(sizes.values()))   # {'R1': 36, 'R2': 179, 'R3': 69, 'R4': 128, 'R5': 29, 'R6': 57, 'R7': 98, 'R8': 67, 'R9': 18} 681
```

Header (write it as T/review/REFERENCE_header.md before running the slicer, then delete it):
```
# Review reference: asphalt road lane, detail tile and decals (sd-material-research)

Valid for: 2K exports in dump/: lane 2026-10-03 20:36, detail 20:37, decals 22:29-22:30.
Changed in the last update: all (created from review/BRIEF.md "# Round 2", 2026-10-04).
Maintained by the builder at the end of each apply session (prompts 4 and 6, step 7). Read R1 always, then the
sections your row in the delta brief's lens table names.

| id | section | read by (default) |
|---|---|---|
| R1 | Requirements | everyone |
| R2 | Physics digest: layers, process cards, invariants + check ids, watch list | regressions_g1, realism, decals, verifiers |
| R3 | Scale | realism, g5_tiling, decals |
| R4 | Graph architecture | verifiers (fix review), lead |
| R5 | Node semantics cheat sheet | verifiers, lead |
| R6 | Variant presets | anyone who needs a preset value |
| R7 | Files, loader, regions, previews, shader caveats, side reports, shared tools | everyone who measures |
| R8 | Metric caveats and deprecations | regressions_g1, verifiers |
| R9 | Verifier checklist | verifiers, lead |
```

Hand edits after slicing:
1. Drop the `Marks:` line in R1 and every `**[new]**` / `**[changed]**` mark.
2. Rewrite references to the round-2 brief's own section numbers as R-ids ("in §8 below" -> "in R7", "owners per §15"
   -> "the delta brief's lens table"). Leave `spec §n`, `sheet §n` and `sd_craft.md §n` alone.
3. Append `### Shared tools` to R7 (≤ 15 lines): the cache (`composite_decal.py --out review/round<N>/decal/composite
   --build-only` -> review/round<N>/cache; `get_stack(name, cache_dir=...)`, `compose(...)` options, `inv16`,
   `inv16_terms`; "never rebuild the composite"), and the kit (`checks/review_kit.py`, one line per function group of
   §4.4-§4.5, the verifier rule of §4.8).

| id | test | expected |
|---|---|---|
| D5 | `grep -c '^## R[1-9]\. ' T/review/REFERENCE.md` | 9 |
| D6 | `wc -l T/review/REFERENCE.md` | 681 + header (18) + 1 blank − marks line + Shared tools ≈ 700-715 |
| D7 | `grep -c '\*\*\[new\]\*\*\|\*\*\[changed\]\*\*' T/review/REFERENCE.md` | 0 |
| D8 | `grep -o '[A-Za-z_.]* §[0-9]' T/review/REFERENCE.md \| grep -v -E '^(spec\|sheet\|sd_craft.md\|v2) '` | empty after hand edit 2 |

### 6.6 T/prompts/4_apply_round2.md and 6_apply_round3.md: who updates REFERENCE.md

`4_apply_round2.md`: after line 29 (`6. Update spec.md (the changed sections and §12 notes), CONTEXT_PROMPT.md and the
memory note. Save the package.`) insert, and renumber old step 7 (line 30) to 8:
```
   7. Update review/REFERENCE.md. Rewrite every section this session changed: R2 invariants and check ids for new
      checks, R4 for each stage script you re-ran, R6 from build/presets.json, R7 if maps, regions or exports
      changed, R8 for new metric caveats. Set "Valid for" to the new export times and "Changed in the last update"
      to the section ids ("none" if nothing changed).
```
`6_apply_round3.md`: the same step after line 24 (`6. Update spec.md, CONTEXT_PROMPT.md and the memory note. Save the
package.`); renumber old step 7 (line 25) to 8.

In both, the Python rule (line 50 / line 45) becomes:
`- Python: Windows C:\Users\andy\.cache\sd-material-research\venv\Scripts\python.exe (Git Bash); macOS
  PY=$(bash ~/.claude/skills/sd-material-research/scripts/setup_env.sh). Thread cap on every run (5_review_round3.md).`

### 6.7 T/prompts/5_review_round3.md: full replacement

Roster, where the sources disagree: review.md §3 "Final round" says 3 lenses; the brief (change 4) says fixcheck,
regressions + G1, realism lane + on-foot, G5, decals; the round-2 lead (`stop_rule.round3`) says fixcheck; regressions;
decal edges + composite on foot; realism on foot, lane + detail; decal interiors (no G5). The spec takes the brief's
five: the user approved the brief, it defines the early start of fixcheck and G5, and it keeps G1 and G5 from skill §3.
The lead's five scope items (1)-(5) map onto these lenses, each to exactly one owner; its two decal lenses (3) and (5)
merge into `decals`, which gets a split verifier only with 5 or more high/medium findings.

```
Asphalt material, session 5 of 7, only if session 4 said a third round is needed: reviewer round 3, the final round
(stage 6). Use /sd-material-research.
Tools folder: C:\Users\andy\Documents\Allegorithmic\Substance Designer\asphalt_materials_tools
(macOS: ~/Documents/Allegorithmic/Substance Designer/asphalt_materials_tools)

Where things stand: round 2's plan is applied and measured (review/round3/ledger.json), review/REFERENCE.md was
updated by session 4, and the stopping rule isn't met yet.

1. Read first:
   - CONTEXT_PROMPT.md.
   - The skill's references/review.md: §1, §2 (the delta template), §3, §4, §5 (stopping rule), §6.
   - The skill's assets/workflows/review_round.js: the args header (Workflow) or the schemas (Agent tool).
   - review/REFERENCE.md: the header and section table only.
   - review/round2/findings.md: DECISIONS, REJECTED and DEFERRED (don't re-report them).
   - review/round3/ledger.json. The latest scorecards: names and hard-failure lines only.

2. Decisions (don't re-ask): review/round2/findings.md DECISIONS, spec §1 and §13.
   - Reviewers never call Designer.
   - Run the panel with the Workflow tool (review_round.js) when workflows are enabled (ultracode on, or I say so);
     otherwise with the Agent tool, in the same order.
   - Five lenses, from the table below. Each item has one owner.
   - Verify high and medium findings only. The lead spot-checks one low.
   - Budget: 2 threads per agent, at most 8 agents at once; time boxes: lens 35 tool calls / ~15 min, verifier 25 /
     ~12 min, lead 30 / ~15 min.

3. Do (target ~60 min):
   1. Preflight (0-8 min):
      - In the background, from the tools folder: build the composite cache and self-test the kit:
        `"$PY" composite_decal.py --out review/round3/decal/composite --build-only && "$PY" checks/review_kit.py --selftest`
        (~90 s; the cache lands in review/round3/cache). A failing self-test stops the round.
      - Confirm the scorecards are newer than the last export; if not, run checks/run_all.sh round3.
      - Identity check: each graph's compNodes in the package equal the backup taken at the round-3 export.
      - Confirm the previews are in review/round3/ (lane, detail, composite, decal, decal/composite).
      - Confirm REFERENCE.md "Valid for" names the round-3 exports; if not, update the stale sections first.
   2. Early lenses (from ~5 min): start fixcheck and g5_tiling as soon as the preflight passes (Workflow:
      `early: true` with `brief_task`; Agent tool: background agents). They read the rules in their prompt,
      REFERENCE R1 + R7 and the ledger.
   3. Delta brief: review/round3/BRIEF.md from the template in references/review.md §2, at most 250 lines. §9 is the
      table below, plus one row per round-2 design call (findings.md DECISIONS) naming the lens that owns its topic.
   4. The other lenses (12-30 min): regressions_g1, realism, decals.
   5. Verifiers (20-45 min): pipelined, one per lens with high or medium findings; split only at 5 or more.
   6. Merge and lead (45-60 min). Workflow: it runs merge_panel.py and the lead itself (args: review_dir, round 3,
      date, the five lenses). Agent tool: S=~/.claude/skills/sd-material-research/scripts;
      `"$PY" "$S/merge_panel.py" --round-dir review/round3 --lenses fixcheck,regressions_g1,realism,g5_tiling,decals`,
      then the lead in a fresh agent (it writes review/round3/lead.json: at most 5 fixes, clusters, design calls,
      OVERALL, stop rule). Then, in this session:
      `"$PY" "$S/render_findings.py" --round-dir review/round3 --check && "$PY" "$S/render_findings.py" --round-dir review/round3 --result review/round3/review_result.json`
      -> findings.md, review_result.json. Read only findings.md's scorecard, plan and design calls into this session.

   | key | scope | owns (round-2 lead's round-3 items) | REFERENCE | early | effort |
   |---|---|---|---|---|---|
   | fixcheck | fix_status for P1-P8 and the 12 partial items (P1 P3 P5 P8 P10 D2 D3 D5 D6 D8 D9 D10), re-measured; if more than half stay partial, say so first | (1) | R1 R7 | yes | medium |
   | regressions_g1 | the keep-as-is contract; wrong builds for the new hard checks; one verdict per R-id per graph and per INV-1..16 | (2): INV-16 with the new seat, V1 centre margin, detail ladder after protrusion 1.0; cluster "INV-16 height reference" | R1 R2 R7 R8 | no | inherit |
   | realism | lane V0-V4 / V3x and the lane + detail composites at tile, tiled and 1:1 | (4): oil drops, pumping, overband, cold edge, stone fillet, MPD, granite, fines, the deferred fill / ravel calls | R1 R2 R3 R7 | no | inherit |
   | g5_tiling | lane and detail tiling (3×3 / 4×4, landmarks with period, seams, engine masks); decals 0 at the border | none of (1)-(5); leaves oil / pumping appearance to realism | R1 R3 R7 | yes | inherit |
   | decals | P0-P3, Q0-Q4 and the decal composites | (3): AA edge, seat steps and ridges, decal on decal, Q2 replacing P0, T&R outlines; (5): walls, facets, seams, debris, base vs the skin; clusters "rim band", "pothole_wall echo", "Q2 over P0" | R1 R2 R3 R7 | no | inherit |

4. Gate:
   - Show me the scorecard and the plan. Ask the design calls via AskUserQuestion, and record DECISIONS in
     findings.md.
   - Tell me the next prompt:
     - prompts/7_final_gate.md if the round is dry (no new confirmed medium-or-higher finding) or I accept;
     - prompts/6_apply_round3.md otherwise.
   - Update CONTEXT_PROMPT.md and the memory note. Stop.

5. Rules:
   - Python: Windows C:\Users\andy\.cache\sd-material-research\venv\Scripts\python.exe (Git Bash); macOS
     PY=$(bash ~/.claude/skills/sd-material-research/scripts/setup_env.sh).
   - Thread cap on every Python run, mine and the agents': OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
     NUMEXPR_NUM_THREADS=2 (macOS also VECLIB_MAXIMUM_THREADS=2); cv2.setNumThreads(2).
   - Don't touch other packages. Ask before committing to the bridge repo.
   - Keep this session's context lean: the panel reads files; this session reads only summaries.
   - If the session gets long, write IN PROGRESS into CONTEXT_PROMPT.md (finished agents, output paths; with the
     Workflow, its runId for resumeFromRunId) and tell me to paste this prompt again.
```

| id | test | expected |
|---|---|---|
| D9 | in the new file, the lens table's "owns" cells | exactly 5 rows; each of (1)-(5) appears in exactly one row (`(3)` and `(5)` both in `decals`); the merge/render commands match §5.5 |

### 6.8 T/CONTEXT_PROMPT.md: the macOS note (lines 40-42)

Replace
```
- **Moving back to macOS:** copy the package and `asphalt_materials_tools/` without `dump/` (regenerable 2K PNGs) to
  `~/Documents/Allegorithmic/Substance Designer/`, and pull the bridge repo. Every script finds its files through
  `os.path.expanduser("~/Documents/...")` and `~/.claude/skills/...`.
```
with
```
- **Moving to macOS:** move any older Mac copy aside, then copy the package and `asphalt_materials_tools/` with tar
  (keeps file times) without `dump_round1/`, `dump/cal/`, `dump/decal/` and `review/*/cache/`. `dump/*.png` +
  `dump/*.json` (812 + 52 files, 1.54 GB) are the 2K exports the checks and reviewers read. Without them, re-export on
  the Mac with `build/job_export_2k.py` (lane + detail, 30 exports, ~95 s) and `build/job_decal_2k.py` (22 exports,
  ~50 s) through `sdcall.py`, then re-run `checks/run_all.sh`. Pull the bridge repo; `PY=$(bash <skill>/scripts/setup_env.sh)`.
  Every script finds its files through `os.path.expanduser("~/Documents/...")` and `~/.claude/skills/...`
  (details: review/round2/implementation_spec.md §2).
```

## 7. File placement and commit plan

| file | where | git | M |
|---|---|---|---|
| this spec | REPO/review_round2_implementation_spec.md; identical copy T/review/round2/implementation_spec.md | REPO: yes (C0) | M0 |
| `composite_decal.py` refactor (`build_site`, cache, `compose`, `render`, options, `inv16_terms`, `WRONG_BUILDS`, CLI flags) | T/ | no | M2, M4 |
| `composite.py` (`build_window`, `render_window`, `blend_lane_detail`) | T/ | no | M2 |
| frozen `composite_decal_r2.py`, `composite_r2.py` | T/checks/legacy/ | no | M2 |
| `test_composite_decal.py` | T/checks/ | no | M2, M4 |
| `review_kit.py`; run_all.sh +3 lines after line 19 | T/checks/ | no | M3 |
| site cache `composite_<site>.npz` (generated, ~2.6 GB per round) | T/review/<round>/cache/ | no; never tar it | M8 |
| `merge_panel.py`, `render_findings.py`, `tests/test_review_pipeline.py` | SK/ | yes (C1) | M5 |
| `assets/workflows/review_round.js`, `references/review.md`, `SKILL.md` | S/ | yes (C2) | M6 |
| `review/REFERENCE.md` | T/review/ | no | M7 |
| `prompts/4_apply_round2.md`, `5_review_round3.md`, `6_apply_round3.md`, `CONTEXT_PROMPT.md` | T/ | no | M7 |

T has no history: copy each existing T file to `<name>.r2.bak` next to it before its first edit (the composite files go
to checks/legacy/ instead, §3.6).

Commits, each only after the user says yes in chat; push on a separate yes; messages end with the attribution line the
session gives:
- **C0** (M0): this spec. `Add the review round speed-up implementation spec`. (Alternative: skip C0 and read the
  identical T copy, which travels with the tar.)
- **C1** (after M5 passes C-syn, C-merge, C-render): SK/merge_panel.py, SK/render_findings.py,
  SK/tests/test_review_pipeline.py. `Review stage: merge panel JSON and render findings.md in code`.
- **C2** (after M6 passes D1-D4): review_round.js, review.md, SKILL.md. `Review stage: reference + delta brief, one owner
  per hypothesis, time boxes, thread cap, verify high/medium, merge in code`. C1 lands first, because C2's workflow
  calls merge_panel.py.
- The brief (review_round2_process_brief.md) is already in git (eb484d1) and is not part of any commit here.

## 8. Acceptance summary

`$T`, `$SK`, `$PY` as in the header; `$TMP` = any empty temp folder. Thread cap exported in every shell.

| id | test | command (cwd) | expected |
|---|---|---|---|
| S1 | smoke test | §2.4 snippet (T) | the three lines of §2.4, exactly |
| S2 | venv | `"$PY" -c "import numpy, scipy, PIL, cv2"` | exit 0 |
| S3 | links | `python3 tools/link_install.py --status` (REPO) | `~/.claude/skills/sd-material-research` -> `<checkout>/skills/sd-material-research` |
| A1-A12 | composite split, cache, options, P1 terms, composite.py | `(cd "$T/checks" && SDMR_SLOW=1 "$PY" -m unittest -v test_composite_decal)` | all pass (A1, A3, A11, A12 run only with `SDMR_SLOW=1`); numbers as §3.6 |
| A2 | spot values | `(cd "$T/checks" && "$PY" -m unittest -v -k A2 test_composite_decal)` | step_luma -11.764; 48,320; 12.612045; 16.303; rim 19.7; leaks 0; spans 59.1 / 134.02 / 54.12 / 26.58 |
| A9 | P1 default | `(cd "$T/checks" && "$PY" -m unittest -v -k A9 test_composite_decal)` | minus_plane <= 1e-3; seat p50 -1.63 / -1.37 / -0.74 / -5.09 / -0.59; `inv16_ok` true at every site |
| B-selftest | kit self-test | `(cd "$T/checks" && "$PY" review_kit.py --selftest)` | last line `review_kit selftest: 52/52 pass (<s> s)`, s about 30 or less; exit 0 |
| B-repro | kit vs prior art on round-2 exports | per §4.7 | report; each value within the rounding of the quoted number |
| C-syn, C-merge, C-render | merge and render | `(cd "$S" && SDMR_ROUND2_DIR="$T/review/round2" "$PY" -m unittest discover -s scripts/tests -v)` | all pass, 0 skipped; numbers as §5.6 |
| C-cli | merge CLI on round 2 | `"$PY" "$SK/merge_panel.py" --round-dir "$T/review/round2" --out "$TMP/merged.json"` | exit 0; last line `round 2: 35 findings: 26 confirmed, 4 confirmed (sub-claim artifact), 3 unverified, 2 rejected; 8 lenses, 12 verifier files; no verifier: regressions` |
| C-cli2 | render check on round 2 | `"$PY" "$SK/render_findings.py" --round-dir "$T/review/round2" --merged "$TMP/merged.json" --lead "$T/review/round2/review_result.json" --out "$TMP/findings.md" --check` | exit 0; 0 errors, 0 warnings; nothing written |
| D1 | workflow parses | §6.4 D1 | exit 0 |
| D2 | schema required ⊆ properties | code review | true |
| D3 | delta template budget | review.md §2 table | 245 <= 250 |
| D4 | Agent-tool mentions | `grep -n "Agent tool" "$S/SKILL.md" "$S/references/review.md"` | only the two intended lines |
| D5-D8 | REFERENCE.md | §6.5 | 9 sections; ~700-715 lines; 0 marks; no stray brief § refs |
| D9 | round-3 prompt roster | §6.7 | 5 rows; (1)-(5) each owned once; commands as §5.5 |
| I1 | full measurement run | back up `review/scorecard_*`, `review/{ladder,accept_r1,decal_extra,wrong_builds}.*` first; `PY="$PY" bash checks/run_all.sh mac` (T) | same exit code and the same "Hard failures" lines as the round-2 Windows run; a line `review_kit: review_kit selftest: 52/52 pass (...)`; `review/mac/cache/composite_{p3_joint_v4,p1_wpfatigue_v4,q0q3_wp_v4,q1_wp_v3}.npz`; `review/mac/decal/composite/composite_decal.json` equals round 2's under A1's rules (options `r2`) |
| I2 | cache build time | `"$PY" composite_decal.py --out review/mac/decal/composite --build-only --rebuild` (T) | <= 90 s at 2 threads (report; fails above 270 s); `build_seconds` per site in the JSON `cache` key |
| I3 | warm cache | the same without `--rebuild` | every site `from_cache` true; a few seconds |

## 9. Open points

1. **Under-swap gate at q0q3.** The plan says "<= 1e-4" without a site list; with `deform_med`, q0q3 reads 1.67 mm (q0)
   / 1.41 mm (q3), because q3's 20-40 mm ring lies on q0. The spec gates the single-decal sites only (the verifier's
   wording, `P1_GATES`). Confirm at the round-2 gate.
2. **Seat ring.** The plan text says "0.5-6 mm out, off crack/ravel", but all its baselines are inv16_verify's 2-6 mm
   ring with sealant and cracks included; the spec follows inv16_verify and keeps the plan's wording as a variant
   without baselines. Confirm.
3. **Seat under P2's `aa` opacity.** The ring needs alpha >= 0.998 at 2-6 mm, which is empty under AA-only opacity.
   `seat_alpha_min=None` measures the decal's own `h_d` there; P2 must pick this and re-baseline.
4. **P2's "48,320 -> 3,624"** (earlier core under later alpha) is not tied to a script; measure under `narrow` and
   `aa` on the first run, then pin.
5. **Composite timing and disk.** Per-site seconds are measured, the phase split is estimated; the first
   `--build-only` settles it through `build_seconds`. The cache is about 2.6 GB per round; deleting old round caches is
   the user's call.
6. **bowl_facets "risers up-inward <= 0.4"** exists only as text (<a>/decal_potholes_verify_b/write_result.py:100-118;
   the code is probably v2b_tiltfix.py, not read). No kit function until its owner writes it.
7. **Rows without a kit function** (prior art outside reach): oil_plate_share, cells >= 50 mm with > 90 % pumping,
   open-wall luma (pumping - off, U_mask >= 0.65), V4 open-crack share < 70 luma (realism_lane/pump_spall.py,
   realism_lane_verify_a/v_pump*.py); band albedo edge 10-90 %, band width std and edge wander (realism_lane/
   band_ends.py, realism_lane_verify_b/band_v.py; the kit's 8 px crossing window cannot read a 12 mm edge on the lane
   grid); mastic ring - open floor and rim + 3 mm skirt slope (realism_onfoot_verify_a/f1_fixsim.py); seam_spall_share
   (nearest: v2_seam.py's 1-12 mm band p01/p50); face_relief_ratio, debris_top_follows_floor, base fines-gap
   (decal_potholes/m4_relief_gravel_edge.py, m2_layers_base_debris.py, decal_potholes_verify_b/v3b_base_tophat.py); the
   Q3/Q0 shared kerf. Owners write them in the caller first; they move into the kit when a second agent needs them.
8. **Not yet run:** the 52 self-test expectations (analytic or from the prior art; widen a tolerance in a separate
   commit if needed, never change a function to pass), the §4.7 reproductions, `build_window`, and the rendered
   findings.md (C-render's counts come from a prototype checked against review_result.json).
9. **Skill vs material folder** for merge_panel.py / render_findings.py (the brief's open point 2). The spec puts them
   in the skill (§0.4 item 2). If the user prefers T, they go to T/review/ under the same names, and review_round.js
   takes their path as one more arg.
10. **Round 2's findings.md** was never saved. merge_panel.py + `render_findings.py --round-dir review/round2 --lead
    review/round2/review_result.json` can write it (and merged.json) into the round-2 folder; the user decides at the
    round-2 gate.
11. **Workflow file writes.** Whether workflow agents may write under review/round<N>/ with the harness's write rules
    is untested; round 2's lead could write JSON through Python but not through the Write tool, so every prompt says
    `json.dump`. Recovery for a missing lens file: §5.5.
12. **Concurrency on the Mac** (the brief's open point 3): 8 agents at 2 threads is the proposal; the Workflow tool's
    own cap is min(16, CPUs - 2), so a 10-core Mac is capped at 8 anyway.
13. **Windows-measured values.** S1's numbers and the venv versions in §2.4 come from Windows; run S1 before anything
    else on the Mac.
