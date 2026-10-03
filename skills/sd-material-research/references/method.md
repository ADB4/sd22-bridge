# The method: from physics to graph

Read this before writing a spec. It explains the reasoning the whole skill is built on. The other stages assume you
think about the material this way.

## 1. Why procedural wear looks fake

Most procedural materials paint wear on: a grunge mask darkens the colour, the same mask pushes the height down, and
the mask lands wherever the noise puts it. Real surfaces are the result of two things:

1. **Construction.** Components are laid out (bricks and joints, boards and gaps, slabs and saw-cuts, aggregate in
   binder), and each component is a stack of physical layers.
2. **Processes after construction.** Each process acts on a specific layer for a physical reason. It removes or adds
   material there, reveals what lies beneath, and happens where its drivers are: edges, traffic, water, sun, gravity.

Build the graph in the same order (the as-built surface first, then each process acting on the right layer, in the
right places, at the right scale) and most realism problems never appear. The rest can be measured.

**The brick rule** came out of the user's brick material and is the template for everything else. Erosion of a brick
removes brick: it rounds the arrises and spalls the face, which shows more brick underneath. It does not reveal more
mortar. The mortar sits *beside* the brick face, not *beneath* it, so the joint footprint stays the same width. A graph
that widens the mortar mask where bricks are damaged is making a physical error, and viewers read it as "CG" even when
they can't say why.

## 2. Construction: layout, layers, envelope

**Layout.** Each component has a footprint: where it is in plan. Construction sets footprints once. Aging changes
heights, colours and roughness *within* footprints. It can also cover them with deposits, such as dirt filling a joint
or moss in a deck gap, but it does not move them. In a graph this means the layout masks come from the layout generator
and nothing else.

Some processes do change geometry, and they have their own physical drivers. Moisture movement opens wood gaps. A
pothole removes a whole piece of pavement down to the base. Settlement cracks open joints. Model these as explicit
processes with a driver, never as a side effect of a wear mask.

**Layers (stratigraphy).** For each component, list what lies beneath the surface, top to bottom, with depths in mm.
For example:
- brick face (fire-skin) → brick body
- mortar surface → mortar body
- asphalt binder film on the aggregate → mastic (binder plus fines) → coarse aggregate in the matrix → lower courses → base
- concrete paste skin → mortar fraction (paste plus sand) → coarse aggregate
- wood finish or grey weathered surface → wood, with earlywood softer than latewood

A removal process shows the next layer down *in the same component*.

**Envelope.** The as-built surface is the original surface envelope. Removal processes (erosion, abrasion, spalling,
scaling, raveling, chipping) can only go below it. Only deposits (dirt, salts, sealant, paint, biological growth) and a
few swelling processes sit above it. When something rises above the envelope, name the process that put it there.

**Draw the cross-section.** Put neighbouring components side by side (brick | joint | brick, board | gap | board,
aggregate | binder | aggregate) and ask, for each process: what is *beneath* the material it removes, and what is merely
*beside* it? Most fake-looking wear comes from confusing the two.

## 3. Process cards

Describe each process you include with a card. The bundled sheets in `references/materials/` already have cards; for a
new material, research them.

| Field | Question it answers |
|---|---|
| Mechanism | What physically happens (freeze-thaw, abrasion, UV photodegradation, oxidation, salt crystallisation, impact)? |
| Acts on | Which layer of which component? |
| Removes / adds | Material lost or gained? |
| Reveals | What lies beneath in the *same* component? |
| Never | What doesn't it do? These become invariants. |
| Where | Its drivers: edges and corners, traffic paths, low points and water, sun and shade, splash zone, gravity, joints, grain. |
| Shape and scale | Sizes and depths in mm; outline character; profile (step, slope, bowl); orientation; coverage and spacing statistics. |
| Progression | Stage 1 → 2 → 3, and which variant reaches which stage. |
| Interactions | What causes it, and what it causes. |
| Map signature | What it does to height, normal, albedo, roughness and AO. |

Example (brick, edge erosion and chipping):
- **Acts on:** the brick arris and the face near it. **Removes:** fired clay. **Reveals:** the brick body: the same
  brick, slightly different colour and texture, rougher.
- **Never:** widens the mortar footprint: the joint keeps its width. On raked and recessed joints, damage also never
  drops below the adjacent mortar level, which would expose the mortar's side. That second rule is the user's
  "never expose more mortar", and it is a hard check there. On flush, struck and concave joints a deep spall can
  drop below the mortar face and leave the mortar as a ledge; the joint still keeps its width (brick.md §4).
- **Where:** arrises and corners, more on exposed courses, per-brick susceptibility (softer bricks erode more).
- **Shape:** conchoidal chips, 5-40 mm.
- **Signature:**
  - height: a step down from the face, with a short sloped wall
  - albedo: a sub-brick colour derived from that brick's own colour
  - roughness: slightly higher than the face

One-line examples from the other bundled materials (details and sources are in their sheets):
- **Asphalt raveling** strips binder and fines from between the coarse aggregate, so the aggregate stands proud and
  later dislodges, leaving sockets. Texture gets coarser and lighter where the binder film wears off the stone. It
  does not add black binder anywhere; that would be bleeding, a different process with its own driver.
- **Concrete scaling** flakes off the near-surface paste and mortar, and severe scaling exposes coarse aggregate.
  Exposed aggregate sits *below* the original surface, never above it.
- **Wood weathering** erodes the softer earlywood faster than the latewood, so latewood ridges stand proud. Checks
  run along the grain, never across it. Fasteners and knots end up standing above the eroded wood.

## 4. Invariants

An invariant is a rule the result must never break. Each one gets a structural enforcement in the graph and a numeric
check (`references/checks.md`). Every material has these families:

1. **Layout invariance.** Layout masks are identical with every wear and damage parameter at zero and at the preset.
   Check: `mask_invariance` against a no-wear render.
2. **Envelope.** Removal only goes down. Deposits are the only thing above the as-built surface, and they have their
   own masks. Check: `envelope` against the no-wear render, excluding deposit regions.
3. **Beneath, not beside.** What a removal reveals belongs to the same component's lower layers. A neighbour's
   footprint never grows, and a neighbour's side face is exposed only where the spec explicitly allows it (e.g. hard
   cement mortar left proud of eroded soft brick). Check: `order` (the revealed layer stays above the neighbour's local
   level) plus `mask_invariance`.
4. **Drivers.** Each process lives where its drivers are: chips on arrises, fatigue cracking in wheel paths, raised
   grain along the grain, rust runs below the source on vertical surfaces. Check: `coverage` inside vs outside the
   driver region, `orientation`, `spacing`.
5. **Identity through damage.** A unit keeps its identity: the revealed layer's colour and roughness derive from that
   unit's own properties, so a damaged yellow brick shows yellow-buff body, not a global "damage colour". Check:
   `per_element` correlation between face and revealed-layer colour.
6. **Scale.** Every feature size comes from a physical size. Check: `run_length` and `components` against the
   dimensions table.

Material-specific invariants come from the process cards' **Never** lines.

**Severity.** Hard means the material fails if the check fails, so a hard check must measure the physical property in
the rendered maps and must pass the spec's own default. Three rules from the dry runs (details in
`references/checks.md`, "Hard checks that can fail"):
- Where the physics fixes a direction (darker, more saturated, lower, below the source), that order is hard even when
  the magnitudes are estimates and stay soft.
- A check that compares a mask with the mask it was built from, or a deposit with the mask it was multiplied by, proves
  only the wiring. It can stay as a soft wiring test, but the invariant needs a check on the rendered result.
- Tiling is a hard check on every axis that should tile.

## 5. Physical scale

- **Tile size.** Pick `tile_m` so the tile holds a whole number of layout repeats. Then mm per px = `tile_m * 1000 / resolution`.
  Example: 1.8 m at 2048 px is 0.879 mm/px, and holds 8 × 24 metric bricks of 225 × 75 mm (brick plus joint).
- **Features below 2-3 px** can't carry geometry reliably. Express them through roughness and normal variation, or
  accept that they disappear at that tile size.
- **Height depth.** The height map's 0-1 range spans `height_depth_mm`. Choose it so the deepest feature fits, with
  margin. Compute normals with world units (Height to Normal World Units, tile size in cm, height depth in cm) so slopes
  are physically right. Use 16-bit for height.
- **Convert every parameter.** Noise scales, blur radii, chip sizes and crack widths all come from millimetres:
  "a 25 mm chip at 0.879 mm/px is 28 px". Put the conversion in the spec so reviewers can check it.

## 6. From spec to graph: enforce by structure

A numeric check catches a broken invariant. Graph structure keeps it from breaking in the first place. Patterns that
carry across materials (node-level recipes are in `references/sd_craft.md`):

- **Layout first.** Build the layout and per-unit IDs and randoms (Flood Fill and friends) before anything else.
  Export the layout masks from that branch only.
- **As-built height first.** Build the no-wear surface and export it as the `nowear` reference. Every later process is
  a change relative to it.
- **Removal is a subtraction with guards.**
  `H = H0 - depth(process) * mask(process)`, or a lerp toward the next layer's surface. Then clamp with the spec's
  order constraints, e.g. `H_unit = max(H_unit, neighbour_level + margin)`.
- **Compose components explicitly.** For example `height = max(brick, mortar)`, with the mortar footprint coming
  from layout only.
- **Deposits last.** Each deposit has its own mask, which the envelope check excludes.
- **Drivers are explicit maps.** Edge distance, a traffic-density map, a water map (low points from height, AO),
  exposure and gravity direction. Process masks are driver × per-unit susceptibility × noise, never noise alone.
- **Revealed colour comes from the unit.** Build the sub-layer colour from each unit's own base colour (an HSL shift,
  plus a texture of its own).
- **Export a mask per process** (`mask_<process>`), plus the ID map. The checks need them, and users can drive other
  effects with them.

## 7. Talk physics with the user

The user likes to be asked, and to understand why.

- In interview questions, state each option's physical consequence. The brick joint question explained that the
  sub-brick layer sits between the brick face and the mortar, so eroded areas step down into it without touching the
  mortar mask.
- When a request is physically off (e.g. "erosion should show more mortar"), explain the physics in two sentences and
  offer the plausible version. It is still their material. If they keep the request, record it in the spec as an
  **intentional deviation**, and drop or adjust the invariant it breaks so the checks don't fight the user.
- Report results in physical terms: "joint 10.1 mm at half depth, 0 damaged-brick pixels below mortar level", rather
  than "looks good".
