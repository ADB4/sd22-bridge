# Substance Designer craft: recipes, bridge use, pitfalls

Designer 12.4.1 through the sd_claude_bridge MCP. Everything here was measured or verified while building the brick
material. Material-specific build notes live in each sheet's section 10. This file covers what transfers.

**Contents:** 1 Operating the bridge · 2 sdkit quick reference · 3 Graph skeleton · 4 Recipes (R1-R14) ·
5 Node semantics cheat sheet · 6 Engine costs · 7 Transfer table

## 1. Operating the bridge

- **One Designer call at a time.** The bridge runs every command on Designer's main thread and serves nothing else
  meanwhile. Parallel calls queue and time out together. Subagents never call substance-designer tools; they read
  exported files.
- **~60 s client limit per MCP call.** Designer keeps computing after the client gives up, and later calls queue
  behind it.
  - Never retry a mutation that timed out: it would run twice.
  - Wait instead: poll `designer_status` (it answers in ~1 s when idle and fails after 15 s when busy), or sample the
    process: `sample <pid> 1 | grep -q SDSBSCompGraph_compute` in a background until-loop. The pid is in
    `~/.sd_claude_bridge/session.json`.
  - Keep each run_python under ~45 s.
- **Long jobs** (cold computes, several 2048 exports, nowear batches) go through `scripts/sdcall.py job.py` from a
  background shell. It is the same run_python, but with a 15 min socket timeout.
- **render_preview is for eyeballing only.** It returns at most 8 textures at ≤512 px, 8-bit, and computes every
  output. Numbers come from `sdkit.export_outputs` plus `matcheck.py`.
- **search_library is slow the first time** (~60 s, it parses ~485 packages). For a package you already know,
  `sk.find_lib("noise_perlin_noise")` is instant.
- **Designer's Python is 3.9 with no numpy or PIL.** Analysis runs outside, on exported 16-bit PNGs (`scripts/`).
- **Ctrl+Z is unreliable after big scripts** (nested undo groups). Checkpoint with `sk.snapshot("before_fix3")`.
- **Save only the material's own package**, after each completed stage. A `.autosave/` copy of a package open
  alongside it makes graph ids ambiguous: use `"file.sbs::graph_id"` keys.

## 2. sdkit quick reference

```python
import sys, importlib
K = "<skill>/scripts"
if K not in sys.path: sys.path.insert(0, K)
import sdkit as sk; importlib.reload(sk)
sk.configure("<tools>")                                   # loads <tools>/registry.json, dump -> <tools>/dump
sk.new_package("<dir>/concrete_materials.sbs")            # once
core = sk.new_graph("concrete_core", "<dir>/concrete_materials.sbs", relative=True)   # 16-bit, size from parent
sk.expose("height_depth_mm", "float", 12, label="Height Depth (mm)", group="Relief", vmin=1, vmax=60)
sk.expose("normal_format", "int", 0, label="Normal Format", group="Output", options=["DirectX", "OpenGL"])
with sk.section("Layout", (0.35, 0.45, 0.65, 0.25)):     # frames for layout()
    sk.lib("tg", "pattern_tile_generator", "tile_generator", seed="auto", x_amount=2, y_amount=2)
    sk.lib("ff", "flood_fill_2", "flood_fill"); sk.wire("tg", "ff", "mask")
    sk.flood_random("ff_tone", "ff", seed=57)            # one per visual feature
sk.fractal("pores_n", 9, 10)                              # cells = tile_mm / 2**level
sk.hscan("pores", "pores_n", ("add", 0.3, ("mul", ("get", "porosity"), 0.05)))   # Position: calibrate!
sk.nblur("dmg_b", "dmg_raw", "unit_mask", 0.3)            # blur(D*m)/blur(m)
sk.blend("h", "subtract", "dmg_b", "face", mult=("mm", 3.0))   # 3 mm, converted by height_depth_mm
sk.output("o_mask_joint", "mask_joint", src="joint_mask", label="Joint mask")
sk.drive("nrm", "normal_format", ("get", "normal_format", "int"))
sk.prune_dead(); sk.layout(); sk.save_registry(); sk.save()
sk.make_variant(core, "concrete_weathered", {"seed": 11, "scaling": 0.4},
                sk.PBR + [("mask_joint", None, "Joint"), ("mask_scaling", None, "Scaling"), ("slab_id", None, "Slab ID")])
sk.export_outputs("concrete_materials.sbs::concrete_weathered", size=10)         # quick 1024 look
sk.nowear("concrete_materials.sbs::concrete_weathered", ["scaling", "spalling", "dirt"], size=11)
```

**API summary:**
- Nodes: `lib`, `atom`, `output`, `P` (params; `#hex` on colours works), `set_seed` (keeps relative inheritance),
  `wire` (replaces the old link), `disconnect`, `delete`, `source_of`, `consumers`, `move_consumers`, `info`.
- Recipes: `blend`, `levels`, `hscan`, `blur`, `nblur`, `gconst`, `flood_random`, `fractal`, `level_for`.
- Inputs and functions: `expose`, `list_inputs`, `drive`, `undrive`.
- Variants and export: `probe`, `export_outputs` (+ manifest), `make_variant`, `render_variant`, `nowear`.
- Hygiene: `prune_dead`, `layout`, `lint`, `status`, `snapshot`, `save_registry`.

**Function specs** for `drive`, and for any value argument that takes a tuple:
- numbers; `("get", id[, "float"|"int"|"color"|"bool"])`
- `add sub mul div min max`; `("lerp", a, b, x)`; `("vec2", a, b)`
- sugar: `("clamp", x, lo, hi)`, `("neg", a)`, `("mm", mm_spec)` → mm / height_depth_mm

There is **no pow and no clamp node** in 12.4.1. Build curves as the min/max of lines, e.g. the spall Position
`min(0.0077+1.615E, 0.1918+0.958E, 0.459+0.29E)`.

## 3. Graph skeleton (build in this order)

1. **Layout** → binary unit mask, soft gap mask, per-unit IDs. Keep all jitter and warps upstream of everything else.
2. **Per-unit randoms**: one Flood Fill random per feature, each with its own seed.
3. **Edges** (arris).
4. **As-built height**: unit face, filler, composition. Export the `nowear` reference from here on.
5. **Layer surfaces** below the skin, in mm, with guards.
6. **Driver maps**: edge distance, traffic, water/low points, exposure.
7. **Process masks**: sources → union without the unit mask → normalised blurs → **hard mask last**.
8. **Height composition** with the order guards.
9. **Colour**, with revealed layers taking the unit's own colour.
10. **Roughness.**
11. **Normal and AO** in world units.
12. **Outputs**: PBR + a mask per layout element + a mask per process + unit ID.
13. **Wrappers**: one per variant.

After each stage: `export_outputs(size=10)` and run that stage's checks. A broken invariant costs ten times more to
unpick after the colour stage is built on top of it.

## 4. Recipes

**R1. Layout from a Tile Generator.**
- Settings: `pattern Square`, `size_mode "Normal - Size"`, `pattern_size = (L/(L+j), H/(H+j))`,
  `position_offset 0.5` for running bond.
- The tile must hold whole modules (brick: 8 × 225 mm = 24 × 75 mm = 1.8 m).
- Tolerances scale with an Irregularity input: `pattern_size_random`, `position_random`, `rotation_random`,
  `position_offset_random`, then two low-amplitude Perlin warps (s20 at 0.045·IRR², s50 at 0.014·IRR).
- `pattern_size_random` only shrinks units, so add a compensation (`+IRR*0.0075`) to keep the mean joint.
- Keep gaps ≥ ~6 mm at 2048 / 1.8 m, or Flood Fill merges units.
- Fix edge rendering separately (R3). Never fake it by shrinking the layout gap: that broke the joint width.
- Asphalt has no unit grid: its stones are the units (Tile Sampler shapes or thresholded cells).

**R2. Per-unit randoms.**
- `flood_fill_2::flood_fill` (input `mask`) → `flood_fill_to_random_grayscale` (one value per unit, **0 in gaps**).
- `flood_fill_to_gradient_2` gives a per-unit ramp; `angle_variation 1` gives random directions. It spans only
  ~0.15-0.85 inside a unit: measure derived maps, never assume 0-1.
- `floodfill_mapper::floodfill_mapper_grayscale` (`bbox` ← ff output, `pattern_input`) drops a randomly offset copy of
  a noise into each unit, so unit-scale noise never forms a wall-scale motif.
- `distance(mask, source, combinedistance False)` spreads each unit's value into the neighbouring gap, up to the
  midline ("which unit owns this gap").
- **One random per feature.** Shared randoms create hero units that print a lattice. Absorbency and grime sharing
  one random gave 26 dark bricks; spalls and kiln flash sharing one made damage sit on the flashed half.

**R3. Sharp, anti-aliased edges (arris).**
- `blur_hq_grayscale` Intensity 0.13 on the anti-aliased layout, then Levels in 0.35-0.85: a 1-px AA step.
  - Measured: 95-98 % of profiles carry an AA pixel; peak slope 78-80°.
  - Half-ramp ≈ 11-12 px per unit of Blur HQ Intensity at 2048.
  - The default Intensity is 10: always set it.
- Drive the edge width from an "edge radius (mm)" input for eased or tooled edges.
- The Bevel node is useless for crisp arrises.

**R4. Composition: height = max(unit, filler), filler footprint from the layout only.**
- `unit_h = lerp(filler_final, unit_h0, arris)`, then `height = max(unit_h, filler_final)`.
- `mask_<filler>` = 1 − arris, so the footprint comes from the layout, never from heights. Height-derived masks make
  the invariant check circular.
- **Don't** `multiply(arris, unit)` under max(): it hides half the AA ramp and gives binary, aliased edges.
- **Don't** let an opacity-gated subtract leave face height in the gaps. A subtract with `opacity = unit mask` keeps
  the *destination* in the gaps, so the joint never recesses. The sdkit test graph made exactly this mistake and the
  recess check caught it.
- Exposed aggregate (asphalt, worn concrete) flips the roles: `height = max(stone_h, binder_h)`, with the binder level
  = stone top − exposure (mm). Plucked stones are the only footprint change, and they get their own mask.

**R5. Unit face.**
- Per-unit level: Levels of a random, out 0.895-0.965.
- Per-unit tilt: an FF gradient, out ±0.012, addsub.
- Undulation: Perlin, small.
- Micro-grain: Fractal Sum L10-11 at ~0.06 mm RMS.
- Gaussian(160) gave 11 mm cells, the wrong scale, and faces 6-12× smoother than the mortar.
- Feed the same micro noise into roughness (±0.03), so relief and roughness agree.

**R6. Physical-scale noise: the Fractal Sum Base level rule.**
- Cell = `tile_mm / 2^level`; thresholded blobs come out at the size of `MinLevel`.
- `level ≈ log2(tile_mm / feature_mm)`; `sk.level_for(1800, 3.5)` = 9.
- At 2048, level 11 is 1 px: keep geometry at ≤ log2(res) − 1 and push finer detail into roughness.

**R7. Edge chips.**
- Centre a Tile Sampler (96×96, Pyramid, size [1, 0.55], scale_random 0.5) on a 1-2 px band just inside the arris
  (Levels on a Distance of the gap mask). Use separate samplers for bed and perp edges, one rotated 90°.
- × crystal facets × a per-unit factor → stretch → hscan (contrast 1). Add corner wedges at corners.
- Count comes from `mask_random`, size from scale.
- Paraboloid domes read as hole punches (90 % fit a circle).
- Chips centred on the arris reach across the joint and mirror onto the neighbour. Give each chip an owner unit:
  multiply each side's sampler by its own half-unit mask before the max.

**R8. Face spalls / patches.**
1. Start from per-unit noise (FF Mapper), so a spall never spans two units.
2. Multiply by a grow-from-one-edge ramp (FF gradient, random angle).
3. Apply a per-unit cap (an hscan of the ramp, so only the growth side may spall): max ~28 % of a brick.
4. Combine two independent per-unit randoms, so most units are light and a few heavy.
5. Threshold.
6. **Fill the filler with 1 first**, then Slope Blur Min (crystal slope map, Intensity ~0.6) for fractured outlines.
   Without the fill, the Min erodes from the joint side and fins come back.
7. Open/close with a normalised blur (~0.22). A bigger blur erases the facets.

**R9. Damage union, blurs, hard mask.**
- `dmg = max(chips, spalls)` without the unit mask → majority filter
  `hscan(blur(D·m)/blur(m))` → rake wall with a non-uniform normalised blur (per-unit width) → asymmetric Levels
  (crisp face-side lip, softer toe) → `damage_m = unit_bin × damage` **last**. Everything reads `damage_m`.
- Masking before blurring left a 1.4-2.5 mm fin on 20-44 % of damaged edges. The normalised blur took the lip fraction
  from 0.65 to 0.065.

**R10. Histogram Scan calibration.**
- The threshold centre is **1 − Position**: a higher Position gives more white. Reviewers got the direction backwards
  three times.
- Procedure:
  1. Probe the scan's *input* (`sk.probe`).
  2. Run `python calibrate.py input.png <coverage> --region <mask>`.
  3. Set Position, or an affine `--map param p1:c1 p2:c2` spec.
  4. Re-measure the coverage.
- Re-calibrate after **any** upstream change: a noise swap, facets or a cap shifted coverage 5-30×.
- Stretch a compressed input with Levels before scanning.
- Threshold the pattern alone, then multiply by a smooth zone. Scanning after the multiply makes plateaus.
- Gate a parameter's zero explicitly: `opacitymult = min(1, p*10)`.

**R11. Sub-layer revealed by damage.**
- `sub = unit_plane − depth_mm` (follow each unit's own tilted plane).
- Add per-island depth (Flood Fill on the damage mask, 0.8-1.1×), a small bowl (blurred damage, ~12 % of depth), and
  fracture relief (Crystal 1 + FS L7-9; Crystal 2 + Cells left 1-px Nyquist streaks).
- **Two-sided guard:**
  - floor ≥ filler + 1 mm: `max(sub, filler + 1 mm)`
  - filler ≤ face − max(recess, 1.25 × sub_depth + 1.5 mm)
- Then the micro-grain, which is smaller than the guard.
- Express every depth in mm through `("mm", x)`, so changing Height Depth only adds headroom.

**R12. Filler (mortar, joint sealant, gap floor).**
- Level in mm, plus sand (FS L9-11) and Perlin unevenness, plus wear.
- Wear "per joint segment" needs segment IDs from shifted copies of the layout generator. A Distance-owned unit random
  split every joint at its centreline (2.5 mm cliffs): Distance ownership is right for "which unit owns this gap",
  wrong for "one value per segment".
- Concavity: Distance falloff, 0.5 mm.

**R13. Colour.**
- Per-unit colours (A/B/C through randoms) plus hue/value axes, each with its own random; mottling with Clouds/Perlin.
- **Revealed layers derive from each unit's own colour** (HSL shift plus a small global tint). Target floor/face luma
  ~1.08-1.15 with |Δb*| ≤ 1.5. A global swatch reads as a decal; an AO-dirt ring around breaks reads as ink.
- AO-driven dirt is guarded off fresh breaks (dilated damage mask). A per-unit random decides which breaks are old
  enough to keep grime.
- Deposits (efflorescence, rust): threshold the pattern, then multiply by a zone that comes from the right source.
  Salts in a bed joint belong to the unit *above*: a Distance ownership shifted with Transformation. Probe a column
  to check the offset sign; +Y moved content up.
- Inclusions are applied after the sub-layer colour, so breaks carry them too.

**R14. Roughness.**
- Order as the physics says (brick: face < sub-layer < mortar; .86/.90/.93), with an HF term from the same micro-grain
  as the height.
- **Every addsub perturbation must be zero-mean.** A fracture texture averaging 0.29 pulled the sub-layer below the
  face: check the source's mean.

**Normal, AO and format.**
- Normal: `height_to_normal_world_units_2` with `surface_size` = tile size in cm, `height_depth` driven from the
  height-depth input, and **`normal_format` driven from the exposed input**. The node defaults to OpenGL; the sdkit
  test graph shipped OpenGL until `normal_valid` caught it.
- AO: `hbao_2::hbao` with `use_world_units`, `surface_size` and `height_depth_cm`.
- Set the graph `$format` to 16-bit at creation. Uniform/Blend chains default to 8-bit.

## 5. Node semantics cheat sheet (put it in every review brief too)

| Node | Behaviour |
|---|---|
| Histogram Scan | centre = 1 − Position (higher Position = more white). Contrast 0.9-1 ≈ a step. Ports `Input_1` → `Output`. |
| Blend | divide = destination / source. Add Sub = dst + 2·(src − 0.5). "subtract" is spelled `substract`. Copy = lerp(dst, src, opacity × opacitymult). A colour Blend skips a grayscale source; a grayscale Blend reads a colour source as black. |
| Levels | float4 params `levelinlow/levelinhigh/levelinmid/leveloutlow/levelouthigh`; invert = out 1 → 0. |
| Warp | 0.05 at 2048 ≈ 2.4 px std / 8 px max on a Perlin s20 gradient. Crystal gradients make contour rings: use smooth Perlin (0.02-0.08). Warp before per-unit mapping, never after. |
| Distance | `distance` ≈ 8 px per unit at 2048. `combinedistance False` propagates the source value into gaps. |
| Flood Fill | randoms are 0 in gaps. FF to Gradient spans ~0.15-0.85. |
| Transformation | +Y offset moved content up here. Verify by probing. |
| Enums | Set by label through `P` / `set_parameter`: stored values aren't list positions (Tile Sampler Pyramid = 8, Slope Blur Min = 6). |
| Parameters | `$` parameters set through set_parameter become Absolute: use `sk.set_seed`. Driven parameters ignore static values (`sk.info` shows DRIVEN). |
| Colour inputs | float4: pass `#hex` through `sk.P` / `sk.expose(kind="color")`. |
| Connections | On 12.4.1 the "output" end of a connection is whichever side you queried from. Use `sk.source_of` / `sk.consumers`. |

**Output ports:**
- Blur HQ `Blur_HQ`
- Histogram Scan `Output`
- Flood Fill `output`
- FF Mapper `Output`
- Tile Sampler `output`
- Slope Blur `Slope_Blur`
- Non-Uniform Blur `Non_Uniform_Blur`
- noises `output`
- HtNWU and HBAO `output`
- atomic nodes `unique_filter_output`

**Inputs:**
- Blend `source/destination/opacity`
- Levels, HSL and Transformation `input1`
- Warp `input1` + `inputgradient`
- Distance `mask` + `source`
- Blur HQ `Source`
- Slope Blur and Non-Uniform Blur `Source` + `Effect`
- FF Mapper `bbox` + `pattern_input`
- Tile Sampler `mask_map_input`
- Output `inputNodeOutput`

## 6. Engine costs

- **Stalls:** FX-map noises at high scale stalled the GL engine. Gaussian Noise above ~200, BnW Spots 3 at 96 and
  Cells 4 at 110 took **354 s** at 1024 (~9 min at 2048). `sk.lib` refuses these, and `sk.lint` flags them.
- **Safe:** Cells 4 at 48, Crystal 1 at ~40, Clouds 2 / Perlin at 3-50, Tile Sampler 96×96 (~1-2 s), Fractal Sum
  Base at any level.
- **Typical times:**
  - brick graph (321 nodes): 1.5 s at 1024, 6 s at 2048
  - warm 2048 export of a 9-output wrapper: 4-5 s
  - cold export: ~110 s (use sdcall.py)
- **First compute after new node types** can be slow once (shader compilation).

## 7. Transfer table

| Pattern | Asphalt | Concrete | Wood planks |
|---|---|---|---|
| Layout (R1) | stones as units (Tile Sampler / cells), no grid; tile 2-4 m | slab grid, sawcut 3-5 mm or tooled joint, near-straight | rows of boards, staggered butt joints, gaps 3-6 mm (deck) or ~0 (floor) |
| One random per feature (R2) | per-stone mineral colour, polish, protrusion | per-slab tone, finish direction, curing blotches; board/form tone on the F0-F1 colour (outer ~20 mm), so erosion of the skin keeps it | per-plank tone, sapwood edge, cupping sign; FF Mapper grain per plank |
| Edges (R3) | stone rounding by traffic | edger radius vs sharp sawcut | eased edges 1-3 mm |
| Composition (R4) | max(stone, binder): wear lowers the binder; plucked stones get their own mask | max(slab, sealant): scaling only inside slabs | max(plank, gap floor): wear never widens gaps |
| Sub-layer + guard (R11) | ravelled → coarser aggregate; pothole floor = base course | scaled paste → sand → coarse aggregate (ASTM C672 depth bands) | grey skin over fresher wood; latewood ridges |
| Chips (R7) | patch edges, kerbs | joint spalls, corner breaks | dents stretched along the grain, end splinters |
| Patches (R8) | ravelling from cracks, potholes | freeze-thaw scaling from joints and low areas | end checks, weathering per plank |
| Calibration (R10) | exposed-aggregate %, crack density | scaling % by severity, bughole % | knot density, check length |
| Orientation | wheel-path bands along the lane | broom striations across the slab | grain along the board: `orientation` check, not isotropy |
