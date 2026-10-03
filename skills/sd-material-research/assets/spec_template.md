# <Material>: spec

> Package: `<path>.sbs` · Tools folder: `<path>_tools/` · Sheet: `references/materials/<m>.md` (date) · Spec version: 1

## 1. User requirements (acceptance criteria)
Write the user's words verbatim, numbered. Then list:
- the interview answers
- the defaults applied (and that they were applied, not chosen)
- any intentional deviations from physics the user chose, each with the invariant it relaxes

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
Also list the processes left out on purpose, and why.

## 6. Invariants
Numbered. For each one:
- **Statement**
- **Physics:** one line
- **Enforce:** the structural mechanism in the graph
- **Check:** the check id(s) in `checks/<variant>.json`
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

## 10. Graph architecture
The sections, in build order, each with its inputs and outputs:
layout → per-unit randoms → as-built height → layer surfaces → driver maps → process masks → height composition
(with guards) → colour → roughness → normal/AO → outputs → wrappers.
Name the exposed inputs and their groups. Keep a node naming scheme that the registry will use.

## 11. Risks and open questions
List what research couldn't settle, the targets that are estimates, and the expensive nodes to watch
(see sd_craft engine notes).
