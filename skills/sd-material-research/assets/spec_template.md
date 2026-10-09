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

## 10. Graph architecture
The sections, in build order, each with its inputs and outputs:
layout → per-unit randoms → as-built height → layer surfaces → driver maps → process masks → height composition
(with guards) → colour → roughness → normal/AO → outputs → wrappers.
Name the exposed inputs and their groups. Keep a node naming scheme that the registry will use.

## 11. Risks and open questions
List what research couldn't settle, the targets that are estimates, and the expensive nodes to watch
(see sd_craft engine notes).
