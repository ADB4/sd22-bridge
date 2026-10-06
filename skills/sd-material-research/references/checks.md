# Checks: vocabulary and toolkit

The spec turns each physical claim into a numeric check on the exported maps. `scripts/matcheck.py` runs a
`checks/<variant>.json` and writes `scorecard_<variant>.md` and `.json`. Reference sheets and specs use the check
names below.

```bash
PY=$(bash <skill>/scripts/setup_env.sh)          # once; prints the venv python
$PY <skill>/scripts/matcheck.py <tools>/checks/weathered.json            # all checks
$PY <skill>/scripts/matcheck.py <tools>/checks/weathered.json --only joint_half_depth,no_damage_below_mortar
```
Exit code 0 means every hard check passed. 1 means a hard check failed, including one whose value is undefined (NaN),
which is what the wrong build often gives. 3 means none failed but a hard check measured nothing: it raised an error or
was vacuous (the header names it). 2 means a config error. Before running, matcheck rejects a hard check without a
target (it could never fail), a severity other than hard or soft, an unknown type, space, axis or normal_format, a
target that isn't `[low, high]`, a missing or non-numeric `scale.tile_m` or `scale.height_depth_mm`, and `--only` ids
that match no check. A 2048 config of about 60 checks takes about 5.5 s, a 1024 one about 2 s. The scorecard JSON
lists `hard_failed`, `hard_unmeasured`, `soft_failed`, `vacuous` and `errors`.

Schema card: the keys most configs use. Each type's own parameters are under "Types", each region base's under
"Regions". For a key or default none of these gives, print the matcheck lines that read it, each with its function,
instead of reading the source: `awk '/^ *def /{f=$2} /"<key>"/{print FNR, f, $0}' <skill>/scripts/matcheck.py`. A key
two types read can have two defaults (`tolerance_mm`: 1e-6 in `ck_order`, 0.05 in `ck_envelope`).

| Part | Keys |
|---|---|
| config | `material`, `variant` (names the scorecard), `scale` {`tile_m` (m, or [x, y]), `height_depth_mm`, `resolution`, `normal_format` directx/opengl}, `maps` {`dir`, `prefix`, `ext` (default `.png`), logical name → file stem, `masks` {name → stem}, `id`}, `compare` {render → {`dir`, `prefix`}}, `regions` {name → region}, `checks` [...], `out_dir`, `previews` |
| check | `id`, `type`, `severity` hard/soft (default soft), `why`, `min_px`, `skip`, and a target: `target` [min, max] with `null` for an open end, or `target_mm`, `target_deg` (the same [min, max]), `max_violation_frac`, `max_changed_frac`, `max_frac` (a number: the upper bound). Without a target a check reports `info`, except `value_order` and `normal_valid`: their implicit target is [1, null], so they pass or fail like a targeted check (a failing soft one is a soft miss; a vacuous one reports vacuous) |
| shared | `region`, `within`, `map`, `stat` (median mean min max std cv count sum pNN), `channel` (luma r g b lab_l lab_a lab_b chroma hue), `space` (raw linear srgb255 mm), `axis` (x y both) |
| space | Default `raw` (the stored 0-1 values) for `value_range`, `value_order`, `orientation` and `spacing` on a `map`, per_element `value_mean`, the region `map` base, and `below_local` on a map other than height (on height it reads mm); `linear` for `lowfreq`, `boundary_profile`, per_element `luma_mean` / `luma_median`, and `rel_below`. So a basecolor `value_range` reads sRGB-encoded values unless you set `space`. `mm` is height × `height_depth_mm`, on the height map only (on any other map it reads raw). `space` applies to luma and r/g/b; a CIELAB channel ignores it, mm included. On a region `map` base, select height with `min_mm` / `max_mm` and no `space`: the two together scale twice |
| region | one base (`mask` + `threshold` or `range`, `map` + `min`/`max`, `height_split`, `below_local`, `rel_below`, `boundary`, `sweep`, or none), then `invert` (flips the base; ignored when there is no base, so write "neither a nor b" with `not`), then `or` → `and` → `not` → `erode_mm` → `dilate_mm` |
| types | run_length components coverage concentration height_diff order mask_invariance envelope per_element slope edge_profile boundary_profile dispersion step lowfreq seam value_range value_order orientation spacing ridge normal_valid height_usage |

Units: lengths in **mm**, converted with `scale.tile_m` and the map size. Heights are in **mm** too: the height
map's 0-1 range spans `height_depth_mm`. All filters, morphology and connected components wrap around the tile
borders, because the maps tile.

Validated against the brick project's own metrics (classic, 2048):

| Metric | matcheck | Brick project |
|---|---|---|
| Joint at half depth | 10.5 mm | 9.7-10.6 |
| Mortar area | 0.175 | 0.175 |
| Recess | 5.76 mm | 5.8 |
| Damaged pixels below mortar | 0 | 0 |
| Damage coverage | 0.26 % | 0.26 % |
| Per-brick face luma | 0.92-1.12× | 0.92-1.12× |
| Low-frequency std | 2.5 % | 2.6 % |
| Arris anti-aliased (edge_profile aa_frac) | 0.947 | 0.95 |
| Peak arris slope p50 (edge_profile) | 78.3° | 78.3° |

The full regression suite (233 comparisons on the classic, weathered and rustic maps, plus 280 synthetic tests)
lives in the dev folder, `sd-material-research-dev/tests/matcheck/`.

## File layout

```json
{
  "material": "yellow stock brick",
  "variant": "weathered",
  "scale": {"tile_m": 1.8, "resolution": 2048, "height_depth_mm": 12.0, "normal_format": "directx"},
  "maps": {
    "dir": "../dump", "prefix": "brick_weathered_",
    "basecolor": "basecolor", "height": "height", "normal": "normal", "roughness": "roughness",
    "metallic": "metallic", "ao": "ambientocclusion",
    "masks": {"mortar": "mask_mortar", "damage": "mask_damage"},
    "id": "brick_id"
  },
  "compare": {"nowear": {"dir": "../dump", "prefix": "brick_weathered_nowear_"}},
  "out_dir": "../review",
  "regions": {
    "mortar": {"mask": "mortar", "threshold": 0.5},
    "unit":   {"mask": "mortar", "threshold": 0.01, "invert": true},
    "damage": {"mask": "damage", "and": ["unit"]},
    "face":   {"and": ["unit"], "not": "damage", "erode_mm": 3.5},
    "open_joint": {"height_split": {"low": "mortar", "high": "face", "frac": 0.5}}
  },
  "checks": [
    {"id": "joint_half_depth", "type": "run_length", "region": "open_joint", "axis": "both", "max_mm": 35,
     "target_mm": [9.5, 11], "severity": "hard", "why": "spec I2: 10 mm joints"},
    {"id": "layout_fixed", "type": "mask_invariance", "mask": "mortar", "against": "nowear",
     "max_changed_frac": 0, "severity": "hard", "why": "I1: wear never moves the joints"}
  ]
}
```

- **Paths.** Relative paths resolve from the JSON file's folder. A map file is `<dir>/<prefix><stem>`, plus `ext`
  (default `.png`) unless that file name already has an extension. A dot in the prefix or stem counts as one
  (`t_1.5m_basecolor` gets no `.png`, even with `ext` set), so then write each stem with its extension
  (`basecolor.png`). Logical
  names (`basecolor`, `mortar`, `id`, ...) map to file stems, and comparison renders reuse the same logical names
  with their own `dir` and `prefix`.
- **Images.** With OpenCV installed (`setup_env.sh` installs it), every PNG keeps its bit depth, including 16-bit
  colour. Without OpenCV, Pillow reads colour at 8 bits; 16-bit greyscale stays exact either way. Export height and
  masks as 16-bit greyscale.
- **Every check** has `id` and `type`, plus optional `why` (the invariant or spec section it enforces) and
  `severity` (`hard` = an invariant whose failure fails the material; default `soft` = a tuning target).
- **Channels** (`channel`, wherever a check reads a map's value): `luma` is Rec.709 and the default; `lab_l` (L*),
  `lab_a`, `lab_b`, `chroma` (C*ab) and `hue` (h_ab in degrees) are CIELAB (D65) from the sRGB values. `space`
  applies to luma and r/g/b only. An unknown channel is a config error. Use `chroma` to tell weathered grey
  (C* about 0-8) from fresh or sheltered wood, rust or warm stone without per-species RGB targets; `hue` is circular,
  so compare it with `value_range` only inside a range that doesn't cross 0/360.
- **Vacuity guard.** Each check reports `n_key`, the size of the set its value rests on (pixels, or elements,
  profiles or features as `details.n_key_unit` says). Below `min_px` (default 1) the check is reported as `vacuous`
  with `passed: null`: an invariant on an empty region must not count as a pass (on a hard check the run exits 3
  unless another hard check failed). Set `min_px` on every hard check whose region can be empty in some variant,
  e.g. `"min_px": 500` on a damage-order check. A `min_px` on a type that has no counted set (`seam`,
  `normal_valid`, `height_usage`) is a config error. What `n_key` counts: `order` the checked upper pixels (and 0
  when `lower` has fewer than `lower_min_px` pixels); `components` and `coverage` the `within` set (the whole tile
  without it), not the region; `height_diff` the smaller of `a` and `b`; `concentration` within ∩ driver; `slope`
  (between) and `ridge` the band; `orientation` on a region the mask dilated 1.5 px; `boundary_profile` the pixels
  in the in-range bins; `edge_profile` profiles; `dispersion` features; `per_element` elements. So for `components`,
  put the guard on a `coverage` of the same region.
- **Map sizes.** All maps of a run, and of its comparison renders, must have one size; a check that reads a map of
  another size reports a config error naming both sizes.
- **Scorecard.** The header lists hard failures, soft misses, vacuous checks and errors. A check that raises is
  reported as an error and the run goes on. If the map folder has a `<prefix>manifest.json` (written by
  `sdkit.export_outputs`), the header also gives the graph, export time and parameters, and warns about map files
  older than the export (stale) and about maps whose sizes differ from each other or from the manifest. It also
  repeats the export's own warnings: an 8-bit height or normal map, and Outputs skipped for having no identifier.

## Regions

A region is a boolean pixel set, built in this order: base → `invert` (base only) → `or` → `and` → `not` → `erode_mm`
→ `dilate_mm`.

| Base | Meaning |
|---|---|
| `{"mask": "m", "threshold": 0.5, "invert": false}` | mask ≥ threshold |
| `{"mask": "m", "range": [0.2, 0.8]}` | lo ≤ mask ≤ hi, e.g. the anti-aliased ramp of a soft mask |
| `{"map": "roughness", "min": 0.9, "max": 1.0}` | value range of any map (for height, `min_mm` / `max_mm` work too). Add `channel` (and `space`) to select by a colour channel of the rendered map, e.g. `{"map": "basecolor", "channel": "lab_l", "min": 80}` for white efflorescence as rendered |
| `{"height_split": {"low": "mortar", "high": "face", "frac": 0.5}}` | pixels below the level `frac` of the way from the low region's height to the high one's (`stat`, default median; `"below": false` gives the pixels above) (e.g. joint opening at half depth) |
| `{"below_local": {"ref": "face", "radius_mm": 10, "offset_mm": 0.5}}` | pixels lower than the mean of `ref` within a `radius_mm` box, minus `offset_mm`. `map` (default height, in mm), `space`, `channel` and `min_px` (ref pixels needed in the box, default 10) are optional. Pixels with too few ref neighbours are excluded |
| `{"rel_below": {"map": "basecolor", "ref": "face", "scale": 0.5}}` | pixels whose value is below `scale` × a statistic of the whole `ref` region (`stat`, default median; `space` default linear; `channel` default luma), e.g. "dark specks: luma below half the face median" |
| `{"boundary": ["unit", "mortar"], "band_mm": 2}` | pixels within `band_mm` of both regions (arris band) |
| `{"sweep": {"ref": "lift_joint", "direction": "down", "length_mm": 300}}` | pixels 1 to `length_mm` past the `ref` region in one direction (`down` = toward the bottom of the image, `up`, `left`, `right`), wrapped; `include_ref: true` adds the ref pixels. The band below vs above a water source tests gravity directly (see "Hard checks that can fail") |
| no base | `and` starts from all pixels; `not` alone means everything except |

Because `not` runs before `dilate_mm`, a ring around a feature takes two regions. `{"mask": "patch", "dilate_mm":
300, "not": "patch"}` is empty: it removes the patch from itself, then dilates nothing. Write it as
`"patch_d": {"mask": "patch", "threshold": 0.5, "dilate_mm": 300}` and `"patch_ring": {"and": ["patch_d"], "not":
"patch"}`. A check whose region can be empty also needs `min_px`, so it reports vacuous instead of passing.

A name that isn't defined in `regions` is used as a mask name with threshold 0.5. Regions are built per render, so
`mask_invariance` with a `region` compares that region built from the main maps and from the `against` maps.
Never base a region that an invariant checks on the height it constrains: use layout masks or the `nowear` render.
`erode_mm` / `dilate_mm` are Euclidean and wrap: erosion keeps pixels farther than r px from the outside (the brick
interior is reproduced by 3.6 mm at 0.88 mm/px; 3.5 mm keeps the pixels exactly 4 px away).

## Types

| type | value | key params | use for |
|---|---|---|---|
| `run_length` | stat of the widths of a region along scanlines (mm) | `region`, `axis` x/y/both, `min_mm` / `max_mm` filter, `step_px` | joint/gap width, plank width, brick height and length. Runs wrap across the tile border and count once; a scanline entirely inside the region gives no run (a band parallel to the scan axis is NaN); widths are whole pixels, so a median can flip by one pixel |
| `components` | from connected parts of a region (tile-wrapped) | `region`, `within`, `metric` count / count_per_m2 / eq_diameter_mm / largest_mm / small_island_count / small_island_frac / aspect (PCA elongation, 1 = round) / fill (area ÷ bounding box), `min_mm`, `below_mm`, `stat`, `connectivity` 4/8, `border_px` (opt-in: only components that reach within N px of the tile border) | pits, chips, exposed aggregate, potholes, knots, floating islands; aspect for checks vs knots, fill for ragged vs blobby outlines; `small_island_count` + `border_px` for the specks a warped coordinate draws where it interpolates across the wrap |
| `coverage` | \|region ∩ within\| ÷ \|within\|: the share of `within` that `region` covers (whole tile without `within`) | `region`, `within` | damage %, raveled %, moss %. To ask "what share of the deposits sit near cracks", the deposits are `within` and the crack band is `region`; swapping them asks the opposite question |
| `concentration` | coverage inside a driver region ÷ coverage outside it (`inf` when the region never occurs outside; NaN when `within` has nothing outside the driver) | `region`, `driver`, `within` | "chips sit on arrises", "raveling is in the wheel paths" |
| `height_diff` | stat(h in a) − stat(h in b), in mm | `a`, `b`, `stat` (or `stat_a` / `stat_b`), optional `local_mm` (compare block by block), `over_blocks` | joint recess, sub-layer depth, ridge height, aggregate protrusion |
| `order` | fraction of `upper` pixels below the level of `lower` (+ `margin_mm`) | `upper`, `lower`, `lower_stat` max/mean/min/median/pNN (default p95), `neighborhood_mm` (default 20; `null` = one global level over all of `lower`), `margin_mm`, `tolerance_mm`, `lower_min_px` (default 10: the least `lower` pixels a mean/median/pNN neighbourhood level needs, and the least in all, below which the check is vacuous), `direction` above/below | "damaged brick never drops below the mortar", "exposed aggregate stays below the as-built top". Upper pixels with no `lower` pixel in reach are skipped and counted in `details` |
| `mask_invariance` | changed pixels ÷ reference mask area | `mask` (or `region`), `against` | **the layout is fixed**: wear never moves joints, gaps or edges |
| `envelope` | fraction of pixels higher than the `against` render by more than `tolerance_mm` (default 0.05) | `against`, `except` (deposit regions), `except_dilate_mm`, `within` | removal only goes down; deposits are the only exception |
| `per_element` | statistic across units | `elements` (an ID map by default, or `{"from": "components", "region": "unit"}`; ID values shared by separate units are split into one element each unless `"split_components": false`; colour ID maps are keyed at 8 bits per channel, and ID values with fewer than `element_min_px` pixels in all are dropped), `metric` coverage (default) / luma_mean / luma_median / height_mean / value_mean, `region`, `within`, `stat` max (default) / cv / pNN / count_outside / frac_outside / range_max / range_min (relative to the `normalize` mean or median, with `band`, default 0.12) / corr / abs_corr (with `metric2`, `region2`), `element_min_px` (default 50 measured px), `min_area_mm2` | per-brick colour CV, worst-damaged plank, tone outliers, revealed-layer colour tracking the face colour. Use luma_median and normalize median when damage specks skew a unit's mean |
| `slope` | surface angle stat (deg) | `between` [a, b] + `band_mm`, or `region`; `min_deg` | rake-wall slope, crack walls, rut flanks (for arris sharpness prefer `edge_profile`: a band slope mixes the face into the edge) |
| `edge_profile` | sharpness of height steps, from 1-D profiles across every rising step of at least `min_step_mm` (default 3.6) inside a `window_px` (default 11) window, centred on the 50 % crossing | `metric` aa_frac (share of profiles with ≥1 px between 10 % and 90 %: anti-aliased) / mean_ramp_px / peak_slope_deg (steepest pixel pair) / rise_10_90_mm, `stat`, `outer` (low side, e.g. mortar) and `inner` (high side, e.g. unit) regions, `exclude` + `exclude_px` (the crossing pixel and the next `exclude_px` − 1 on the inner side), `orientations` top/bottom/left/right, `step_px` + `offset_px` to subsample | arris sharpness and anti-aliasing at unit edges: brick classic gives aa_frac 0.95 and peak 78°. A value of 0 means aliased stair steps; a long rise means a blurred edge |
| `boundary_profile` | a map's statistic in bins of signed distance from a region's edge (+ inside, − outside); the value is the `min` or `max` bin, or `pooled` over `range_mm` | `region`, `map` (default basecolor), `space`, `channel`, `bins_mm` [lo, hi, step], `range_mm`, `value` min/max/pooled, `stat`, `bin_min_px` (default 20), `reference` + `radius_mm` (divide by the local mean of a reference region: a relative profile), `exclude_mm`, `within` | dark rims or halos at damage edges, a revealed layer that should brighten (or darken) inward, edge-wear gradients. Read `profile_mm_n_stat` in details |
| `dispersion` | variance ÷ mean of feature counts in `window_mm` windows (index; Poisson scatter ≈ 1, a regular grid < 1, clustering > 1), or the share of empty windows | `region`, `window_mm` (default 30), `metric` index / empty_window_frac, `min_mm` (feature size floor), `within` + `min_cover` (default 0.5: windows mostly inside), `connectivity` | "pits cluster", "knots sit in whorls", "pop-outs are scattered", catching a uniform random sprinkle where nature clusters |
| `step` | fraction of neighbouring pixel pairs inside a region (eroded 1 px) whose height differs by more than `threshold_mm` | `region`, `threshold_mm` (default 1), `axis` x/y/both | cliffs inside what should be a smooth surface (a damage floor, a rut, a patch): stair-stepping from 8-bit height or a hard-edged mask leaking into height |
| `lowfreq` | the worst over `sigma_mm` of a statistic of luma after a Gaussian low-pass, relative to the mean | `map`, `sigma_mm` list (default [40, 160]), `space` (default linear), `channel`, `stat` std_over_mean (default) / frac_beyond (share beyond ± `pct` %, default 8) / peak_pct / trough_pct / pNN (% deviation of that percentile), `region` (a masked, normalised low-pass inside it, e.g. faces only) | blotches that print a lattice when tiled; peak_pct and trough_pct catch one bright or dark patch that std hides |
| `seam` | the worst \|z\| of the wrapped border pair's mean difference against the distribution of all interior adjacent column (row) pairs: about 0-2 for a seamless tile | `maps` (default `["height", "basecolor"]` only), `two_sided` (default true), `axis` x (the left\|right border: the tile repeats along x) / y (top\|bottom) / both (default), `method` mean_abs (default) / rowmedian (opt-in), `floor_mm` / `floor` | tileability; a strip that tiles along one direction only uses `axis`. Target ≤ 3 (est.: an interior pair is rarely more than 3σ off); `details` also gives the old ratio (border ÷ mean neighbour difference). Two-sided also flags a border *smoother* than the interior (brick classic: roughness −1.67); `two_sided: false` flags only rough seams. A non-tiling map gives a very large z. On busy maps (cracks, holes, deposits crossing the border) the mean statistic's spread grows until only a ~0.1-1 mm step fails; `method: rowmedian` scores the median over rows of the signed second difference at the border pair instead (scale floor 0.005 mm for the height, 0.5/255 for the other maps), which fails a 0.02 mm lane / 0.005 mm detail step and stays ≤ 3 on a seamless tile (asphalt round 1: 0 of 150 maps; ~0.5 % of interior positions exceed 3). Keep both |
| `value_range` | stat of a map in a region | `map`, `region`, `space` raw / srgb255 / linear, `channel` luma/r/g/b | albedo and roughness targets |
| `value_order` | 1 if the stats are ordered across regions, else 0 | `map`, `regions`, `stat`, `order` ascending/descending, `min_gap` | roughness face < damage < mortar |
| `orientation` | coherence-weighted fraction of structure within `tolerance_deg` (default 15) of `axis_deg` (counter-clockwise from +x, y up), from a structure tensor | `region` or `map`, `window_mm`, `pre_sigma_mm` | checks run along the grain; transverse cracks run across the lane. `dominant_deg` in details is a 15° bin centre (±7.5°) |
| `spacing` | dominant period along an axis (mm), by autocorrelation of the profile averaged across the other axis: the first peak within 10 % of the highest in the search range, so a multiple of the period isn't reported | `region` or `map`, `axis` x/y, `min_mm`, `max_mm` | course height, fastener rows at joist spacing, broom striations. Lags stop at half the tile, so a period needs at least two repeats in the tile; a joint that appears once per tile can't be measured this way (use the layout itself) |
| `ridge` | fraction of a boundary band that forms fins (higher than both sides by > `threshold_mm`) | `between`, `band_mm`, `threshold_mm`, `half_width_px`, `against` (opt-in comparison render, e.g. nowear) | blur and mask-order artifacts at damage edges. With `against`, the test runs on the height minus that render's, so relief both share (a rut flank, as-built texture) cancels and only what the process added or removed can form a fin |
| `normal_valid` | 1 if the green convention matches the height gradient, x tilts against dh/dx, z > 0, and the slope scale median((n.x/n.z) ÷ −dh/dx) is within 1 ± `scale_tolerance` (default 0.15) | `normal_format`, `map`, `scale_tolerance` | DirectX/OpenGL flips, broken normals, and a `height_depth_mm` or `tile_m` that doesn't match the normal's intensity. `details.failed` says which test failed. The default tolerance only catches scale errors above ~15 % (11 mm against a true 10 mm passes); use 0.05 to tighten. A flat height map fails |
| `height_usage` | `metric` range_used / clipped_frac / unique_levels | | 8-bit height, clipped peaks |

## Two families every material needs

1. **Layout invariance.** The footprints set at construction (joints, gaps, board edges, slab joints, lane markings)
   come from the layout and nothing else.
   - Export a `nowear` render: the same graph and seeds with every aging parameter (wear, damage, deposits) at its
     off value. Keep what was built or placed on purpose: the layout, the as-built finish and markings, and
     maintenance features at the moment they were placed (patches, repointing, sealant footprints). `sk.nowear`
     zeroes only the parameters you list, so list the aging ones, not the maintenance ones.
   - Check `mask_invariance` on every layout mask against it.
2. **Envelope and ordering.** Removal processes only lower the surface, and they reveal what lies *beneath* the
   removed material in the same component.
   - `envelope` against `nowear`, with the deposit masks in `except`, covers "only goes down". When a deposit mask
     has a soft edge (flushing, dirt, debris), its anti-aliased rim rises above `nowear` below the 0.5 threshold:
     set `except_dilate_mm` (1-2 px) so a correct build passes.
   - `order` covers "the revealed layer stays above the neighbour" wherever the spec requires it (the brick rule).
   - Deformation that moves the whole surface without removing material (slab curl, faulting, ruts, board cup,
     frost heave) belongs in the `nowear` render as well, driven by the same parameters, so `envelope` compares like
     with like. Otherwise list the uplifted area in `except`. matcheck reads the exported maps, so "apply it after the
     check" is not an option.

## Hard checks that can fail

A hard check is worth having only if a physically correct material passes it and a typical wrong one fails it. The
dry runs found the same failure modes in every material, so check each hard check against these before the spec gate.

- **Tiling is hard.** "Tileable" is almost always a requirement, so `seam` is a hard check with a target (≤ 3) on
  every map that tiles, along every axis that should tile (`axis` for strips). List those maps in `maps`: without it,
  `seam` reads only height and basecolor. A soft seam check with no target lets a seam through every automated gate.
- **A certain direction gets a hard check, even when the magnitude is an estimate.** If the physics fixes the order
  (oiled wood is darker and more saturated than weathered grey; wet is darker than dry; fresh fracture is lighter
  than a sooted face), add a hard `value_order` on the right channel (`lab_l`, `chroma`) between layout regions, with
  a small `min_gap`. Keep the magnitude targets soft. Otherwise a build with the order reversed passes every hard gate.
- **Measure the rendered maps, not the mask wiring.** A deposit multiplied by mask M and then checked to lie inside M
  passes by construction. So does a `concentration` whose driver is the map the mask was built from, or a
  `mask_invariance` / `coverage` between two masks built from the same layout bands. These checks only prove the
  wiring. Replace or pair each one with a check that reads what the viewer sees:
  - the deposit selected from the rendered basecolor (`map` region with `channel`), not from its own mask
  - gravity as mass below vs above the source: `concentration` of the rendered deposit with `driver` = a `sweep`
    down from the source and `within` = the sweeps down and up (a deposit that runs upward scores 0)
  - a per-unit state (oiled boards, repaired slabs, replaced bricks) through `per_element` on the unit IDs, reading
    the rendered colour: `metric: value_mean, map: basecolor, channel: chroma` with `stat: corr`,
    `metric2: coverage, region2: <state mask>`, target ≥ 0.9 (est.). A build that exports a correct mask but ignores
    it in the colour fails this (0.26 on the synthetic test, against 1.0 for a correct build); a check on the mask
    alone does not.
  - the driver mask's own shape (`orientation`, `run_length`, a `sweep` band) when the mask itself is the claim
- **Every hard check names the wrong build it catches.** In the spec, write one line per hard check: the mistake it
  fails, and why the spec's own default passes it (soft edges, anti-aliasing, seeds, the estimated ranges of other
  parameters). A check that fails the spec's own default, or that no plausible mistake can fail, is not hard.

`scripts/wrong_builds.py` replays those lines on the exported maps. Each case edits the maps in memory into the named
wrong build and runs the check through matcheck's own functions; it behaves when the check passes the real maps and
fails the edited ones. Keep the cases next to the configs, e.g. `<tools>/checks/wrong_build_cases.py`:

```python
import numpy as np
import wrong_builds as wb          # edit helpers; `import matcheck as mc` for dilate, erode, ...

def opengl(ctx):                   # returns [(render, map, array)]; render "" = the main render
    n = ctx.main.map("normal").copy()
    n[..., 1] = 1.0 - n[..., 1]
    return [("", "normal", n)]

def drift(ctx):                    # a drift nowear shares: passes mask_invariance against nowear, not against classic
    return [("", "mortar", np.roll(ctx.main.map("mortar"), 3, 1)),
            ("nowear", "mortar", np.roll(ctx.render("nowear").map("mortar"), 3, 1))]

CASES = [("weathered", "normal_valid", "OpenGL normals (green flipped)", opengl),
         ("weathered", "mortar_vs_classic", "mortar drifted 3 px in the variant and its nowear", drift),
         ("weathered", "height_levels", "8-bit height",
          lambda ctx: [("", "height", np.round(ctx.main.map("height") * 255) / 255.0)])]
```
```bash
$PY <skill>/scripts/wrong_builds.py --cases <tools>/checks/wrong_build_cases.py --checks-dir <tools>/checks --out <tools>/review
```
- A case is `(config, check id, wrong build, edit)`. Arrays are in the map's own units (height 0-1 over
  `height_depth_mm`). Edit a copy (`.copy()`, `np.roll`, `np.where`): a map changed in place fails the case. Helpers:
  `wb.paint`, `wb.luma_shift`, `wb.height_units(ctx, mm)`, `wb.normal_from(ctx, h)` (the normal of an edited height),
  `wb.stepped(a, step)` (a map that does not tile), `wb.once(ctx, key, fn)` (inputs several edits share).
- A case on a check that is not hard in its config is skipped, so one loop can cover every variant. Optional:
  `CONFIGS` (configs that must be covered even before they have cases) and `CROSS_CASES = {group: fn(load)}` for hard
  checks across variants (a ladder), where `fn` yields `(check, wrong build, real_pass, wrong_pass, real, wrong)`.
- `--only` takes configs, groups or check ids. It writes `wrong_builds.md` and `.json`. Exit code 0 when every case
  behaves and every hard check has a case, 1 when a case misbehaves (the real build fails, or the wrong build passes
  or reads vacuous) or a hard check has none, 2 on a config or cases-module error.
- A case takes about 0.5 s at 2048 (a `normal_valid` case about 1 s), plus about 0.4 s per config to load its maps.

## Tips

- **Give every process a mask output.** Without masks, the checks can only measure the result, not the cause.
- **Use the core of a soft mask as `order`'s `lower`.** A layout mask is anti-aliased, so `mask ≥ 0.5` includes ramp
  pixels on the unit's edge, which sit at unit height. Against those, `lower_stat: max` flags damaged pixels that
  are fine: on brick classic, `max` with mortar ≥ 0.5 flags 10 % of the damaged pixels, and the cause is the ramp,
  not sand grains in the joint. Define the lower region as the core (`{"mask": "mortar", "threshold": 0.99}`), then
  use `max` as the strict form and `p95` as the robust one, and decide in the spec which is hard.
- **"Kept within X of nowear" is an `envelope` with a negative tolerance.** With `tolerance_mm: -0.5`, `within` a region
  and `target: [0.98, null]`, the value is the share of that region not lowered more than 0.5 mm below the reference:
  e.g. stone cores that a grunge subtracted from stones and mastic alike would fail (asphalt `agg_tips_kept`), while
  an `order` check against the lowered mastic still passes.
- **A drift shared with nowear passes `mask_invariance` against nowear.** Add a comparison render of the clean variant
  (e.g. `"compare": {"v0": ...}`) and check the layout masks against it as well.
- **Read `details` in the JSON scorecard** before tuning: quantiles, worst-case values and pixel counts.
- **Calibrate thresholds from measurements.** When a process mask comes from a Histogram Scan, measure the coverage,
  adjust, and re-measure. The brick project learned that a higher Histogram Scan Position means more white.

## Previews

`scripts/previews.py` renders the images a reviewer looks at, from the same checks.json files (scale, maps, regions).

```bash
$PY <skill>/scripts/previews.py <tools>/checks/classic.json <tools>/checks/weathered.json --out <tools>/review/round1
```
- `--sites N`: crop sites per variant, 1 typical + N-1 worst (default 3). `--no-shadows`: skip cast shadows.
- About 4 s and 1 GB peak RSS per 2048 variant (about 15 s and 3.3 GB at 4096).
- Use a fresh `--out` per round. Crops from an earlier run with more sites are not deleted.
- `scale.normal_format` must be `directx` or `opengl`. When the normal map's tilt disagrees with the height map's
  (e.g. a flipped green channel), the index and stderr carry a warning; the lit views still follow the config.
- Two configs with the same `variant` get distinct prefixes (`<variant>_2`). Non-square tiles keep their physical
  aspect in the downsized views.

Per variant, `<out>/<variant>_*.png`:

| file | shows |
|---|---|
| `albedo_1024` | basecolor only |
| `lit_front_1024` | front light (az 130.6°, el 62.6°), no cast shadows |
| `lit_raking_a_1024`, `lit_raking_b_1024` | raking light from the upper left (az 143.7°, el 21.2°) and from the lower right, cast shadows |
| `hillshade_1024` | normals from the height map, grey albedo, light a: relief without colour (compare with `lit_raking_a`) |
| `lit_raking_full` | light a at 1:1 |
| `tiled3x3_albedo`, `tiled3x3_lit` | 3×3 tiles at 1536 px, front light |
| `tiled4x4_lit_small` | 4×4 tiles at 1024 px: repetition at distance |
| `crop<k>_<site>_{lit_raking,albedo,height,roughness,normal,masks}` | 512 px at 1:1. Height is stretched per crop (black and white in mm are in the index). Masks are tinted over grey albedo |
| `zoom3x_raking` | 256 px around a layout corner in crop 1, nearest-neighbour ×3 |

With two or more configs, `compare_front.png` and `compare_crop_raking.png` are also written. The crop comparison uses
the first variant's typical site in every variant. `views_index.md` lists every file with what it shows, its scale
(1:1 crop = 450 mm, 3×3 = 5.4 m for a 1.8 m tile) and the shader caveat, plus each site's origin and why it was picked.

Crop sites:
- `typical`: the window closest to the tile means of luma, height, roughness and each mask's coverage.
- Worst sites, taken in turn until there are N-1, none overlapping another site by more than 25 %:
  - `most_<mask>`: the most coverage of each non-layout mask's region.
  - `brightest_element` / `darkest_element`: per-element luma, from the first `per_element` luma_mean check or the
    `id` map. It shows the most extreme element not already inside a crop; the window shifts (as little as possible)
    so the whole element fits without breaking the 25 % rule.
  - `lowfreq_peak` / `lowfreq_trough`: luma low-passed at σ 35 mm.
- Layout masks come from `previews.layout_masks`, else from the masks in `mask_invariance` checks, else from masks
  that match `id == 0`.

Optional block in checks.json. `sites` are added on top of N, e.g. at a failing check's location:
```json
"previews": {"layout_masks": ["mortar"],
             "sites": [{"name": "corner_chip", "center_px": [1000, 400], "why": "R2 finding 4"}],
             "elements": {"elements": {"from": "components", "region": "unit"}, "region": "face"}}
```

**Shader.** It is views.py's toy model, reproduced within 1 level with `--no-shadows`:
- One directional light. Lambert plus a GGX D-term specular, 0.08 × AO ambient. Exposure is 1/max(L.z, 0.2): a flat
  face shows about its albedo under the front light (×1.01 with AO 1) but ×1.14 under the raking lights, so compare
  colour only between views with the same light.
- Linear shading between sRGB decode and encode. Downsizing is Lanczos in linear light, wrapped at the tile border.
- Raking views and the hillshade add height-field cast shadows: a march toward the light (wrapped) up to height
  range / tan(elevation), softened over 1 px. Without them, a 6 mm raked joint under a 21° light renders lit and
  looks crumpled, and the brick reviewers misread it that way.
- No IBL or interreflection, and metallic is ignored. Faces tilted toward a raking light clip.

Judge colour from albedo and relief from the hillshade with the lit views. Check any dark rim against the height crop.
Colour PNGs go through matcheck's loader (16-bit with OpenCV, 8-bit with the Pillow fallback), and the index states
the bit depth of the normal and basecolor reads.
