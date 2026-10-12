# <Material>: spec

> Package: `<path>.sbs` · Tools folder: `<path>_tools/` · Sheet: `references/materials/<m>.md` (date) · Spec version: 1

## 1. User requirements (acceptance criteria)
Write the user's words verbatim, numbered. Then list:
- the interview answers
- the defaults applied (and that they were applied, not chosen)
- any intentional deviations from physics the user chose, each with the invariant it relaxes
- the standing decisions approved at the go question (`SKILL.md`, Unattended run) and the deadline (default the next
  08:00 local):
  - SD-1 design calls take the recommended option
  - SD-2 look trades follow the no-pattern rule
  - SD-3 two full review rounds, then apply and stop
  - SD-4 after round 1, only highs are fixed
  - SD-5 REFERENCE and the spec are updated once, at the end
  - SD-6 no commit or push during the run

## 2. Scale and conventions
| Item | Value | Why |
|---|---|---|
| Tile size | `tile_m` m | holds N × M layout repeats |
| Resolution | 2048 (iterate at 1024) | |
| mm per px | `tile_m*1000/res` | |
| Height depth | `height_depth_mm` | deepest feature + margin |
| Normal | DirectX (exposed) | |
| Outputs | basecolor, normal, roughness, metallic, height, ambientocclusion, id, mask_... | |

## 3. Layout
The pattern, unit dimensions and joint/gap widths, with each value converted to px. The generator and its settings.
The randomness per unit (what varies, and by how much). The masks that come from the layout and only from the layout.

## 4. Layer model
A table per component, top to bottom: layer, depth below the as-built surface (mm and height-map units), albedo,
roughness, micro-texture, and when it shows. Then the as-built envelope, and an ASCII cross-section with neighbours
side by side.

## 5. Process plan
One row per included process:

| Process | Acts on → reveals | Drivers (where) | Shape and scale (mm → px) | classic / weathered / distressed stage | Graph mechanism | Mask output |
|---|---|---|---|---|---|---|

Under the table, give the order of operations: which process feeds which, and why.
Then the left-out list, each item with its reason: the processes left out on purpose, and each sheet §5 invariant
whose process or feature no variant here has. These get no §6 entry. An invariant that acts here but is hard to
measure stays in §6 with a check (soft if need be).

## 6. Invariants
Numbered. For each one:
- **Statement**
- **Physics:** one line
- **Enforce:** the structural mechanism in the graph
- **Check:** the check id(s) in `checks/<variant>.json` that measure it in these variants: at least one, never
  "none". Re-aim a sheet check whose region no preset fills to where the invariant acts here; only an invariant whose
  process or feature no variant has goes on §5's left-out list
- **Severity:** hard or soft. For each hard check, one line: the wrong build it fails, and why this spec's default
  passes it (see `references/checks.md`, "Hard checks that can fail"). Tiling is hard on every axis that tiles.

## 7. Variants and presets
A table of exposed parameters (rows) against variants (columns). Every parameter carries its physical meaning and
unit, e.g. "Erosion 0-1 → spall coverage 0-8 % of brick area", and is labelled with the stage it maps to.

## 8. PBR targets
Per region and per variant: albedo (sRGB luma p50 and range), roughness (p50), metallic. Each value cites the sheet
section or source it comes from.

## 9. Acceptance targets
| Check id | Type | Target (classic / weathered / distressed) | From | Hard/soft |
|---|---|---|---|---|

Generate `checks/<variant>.json` from this table. Keep the two in sync: the table is for people, the JSON is for the
script.

Spec values: one fenced block with the info string `json spec_values`, here at the end of §9. `scripts/speccheck.py`
checks it before the gate, and `checks/gen_checks.py` reads its percentages and check ids
(`speccheck.read_spec_values(path)`), so the configs cannot drift from the spec. List:
- every colour key §7 and §8 set, with the range it must stay in: `luma_box` [lo, hi] when §8 gives a luma range,
  `box` (one [lo, hi] per channel) when it gives per-channel bounds, in the same `space` as the `value` (srgb255,
  srgb, linear, raw; convert one of them when the spec mixes them). A key needs both a value and a range: a range with
  no key colour, or a key with no range, is left out. A per-variant key may name its `variant`;
- every parameter that changes what the maps show and is randomised (`kind` random: a value drawn per unit) or
  tabulated (`kind` table: a fixed per-unit list) per unit (panel, brick, board, stone, broom track), with the unit's
  size from §3 as `unit_m` (a unit, not a noise wavelength or a stroke length); `kind` constant or other for anything
  else; a per-unit entry on a second tile (a detail tile) carries its own `tile_m` (only per-unit entries take one);
- every percentage, coverage or fraction that §7 sets as a preset or §9 as a target, one entry per variant, with its
  base (`of`: tile area, groove length, ...) and the one check that measures it, also for a 0 preset (the check that
  measures it in the other variants). A ratio or a CV is not a percentage. A row computed by a script outside the
  configs is named `<script>:<row id>` (e.g. `ladder:wear_lines_path`).
- every value research could not source (an (est.) value, or one on the could-not-source list) that sets a check's
  number, as `estimates` {id, section, value, unit, what, checks, ends_checked}: `checks` names each check whose target,
  threshold, cap or min_gap this value bounds, hard or soft (an estimated colour names the value_order checks on its own
  channel between its region and the others). Leave out a check that only uses a region, sweep, mask or selector the
  value shapes, and a layout dimension the spec chooses and draws exactly (a board width, a tie pitch: a choice, not an
  estimate). speccheck flags each listed hard check that tests a magnitude; a direction (a value_order with a small
  min_gap, an order, a concentration with a floor of at most 1.2, a sign) stays hard. `ends_checked` names the listed
  hard checks whose bound you showed both ends of the range pass, every layer composited over the region included,
  while the check's wrong build still fails it (the check's Severity line in §6 shows the numbers).
Strict JSON, no comments; `null` is an open end; a point `value` is a preset, a [lo, hi] `value` a band;
`config_scale` is the factor from the spec's number to the config's (0.01 when the config holds a fraction and the
spec a percent).

```json spec_values
{
  "tile_m": [3.0, 3.0],
  "colour_keys": [
    {"id": "<key>", "section": "8", "space": "srgb255", "value": [0, 0, 0], "luma_box": [0, 255]}
  ],
  "per_unit": [
    {"id": "<param>", "section": "7", "unit": "<unit>", "unit_m": [1.0, 1.0], "kind": "random", "what": "<what varies, by how much>"}
  ],
  "percentages": [
    {"id": "<param>", "section": "9", "variant": "<config>", "value": [0, 1], "unit": "%", "of": "<base>", "checks": ["<check id>"], "config_scale": 0.01}
  ],
  "estimates": [
    {"id": "<value>", "section": "4", "value": [0.3, 1.5], "unit": "mm", "what": "<what could not be sourced>", "checks": ["<check id>"], "ends_checked": []}
  ]
}
```

## 10. Graph architecture
The sections, in build order, each with its inputs and outputs:
layout → per-unit randoms → as-built height → layer surfaces → driver maps → process masks → height composition
(with guards) → colour → roughness → normal/AO → outputs → wrappers.
Name the exposed inputs and their groups. Keep a node naming scheme that the registry will use.

## 11. Risks and open questions
List what research couldn't settle, the targets that are estimates, and the expensive nodes to watch
(see sd_craft engine notes).
