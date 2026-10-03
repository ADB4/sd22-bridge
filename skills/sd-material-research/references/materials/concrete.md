# Portland-cement concrete surfaces: reference sheet

> **Scope:** cast-in-place portland-cement concrete from new to heavily deteriorated. Horizontal flatwork
> (sidewalks, slabs-on-grade, interior floors, driveways, jointed pavement panels) and vertical formed surfaces
> (walls, columns, retaining walls). Polished concrete gets a short entry; board-formed and other architectural
> sub-variants get a paragraph each and are left to live research. Not covered: precast decorative products,
> terrazzo, shotcrete as a main case, pervious concrete, coatings and paint.
> **Researched:** 2026-10-02, revised 2026-10-03. **Confidence:** layout rules, finish textures, defect sizes and
> severity scales are well sourced (NRMCA, PCA, ACI, FHWA, LTPP, DOT specs). Solar reflectance is measured in the lab
> (LBNL) and the field (LBNL pavements); the visible/solar ratio comes from one spectral library. Roughness values,
> map-crack cell sizes, broom striation spacing, stain geometry and the mortar cover over coarse aggregate are
> estimates. US practice dominates; metric framed-panel walls get one paragraph.

Every number carries a source tag `[n]` (see Sources) or `(est.)` with a one-line reason.
Ranges are given; the variant or region is stated where it matters.

## 0. Physical summary
Concrete is aggregate (60-75 % of volume [43]) glued by cement paste (23-32 % [18]) with 2-8 % air [18][43].
Flatwork is placed, struck off and bull-floated, which pushes coarse aggregate down [9]; floating, troweling and
brooming then work a mortar layer at the top (est. 3-10 mm: moderate scaling exposes aggregate after 3-10 mm of mortar
loss [2]), capped by a paste-rich skin. Formed surfaces copy the form face (plywood, overlaid plywood, boards, steel)
and carry the form's seams, tie holes and lift joints. Slabs are cut into panels by joints placed at construction [6].
Three facts procedural versions most often get wrong:
1. **Wear removes concrete and reveals more of the same slab.** Scaling and flaking strip paste and mortar and leave
   coarse aggregate standing proud [16]; traffic abrasion planes paste and rock together, paste faster [44]; grinding
   cuts everything to one plane [31]. Spalls and pop-outs show fractured aggregate [14][16]. Steel appears only where
   removal reaches cover depth [13]. Wear never widens the kerf: a joint spall removes slab concrete beside it, and the
   kerf and its sealant keep their width (crack width is measured excluding chipped edges [50]). A joint opens only
   when the panels move (shrinkage, heave, creep), which is a layout-level process (4.5), not wear.
2. **Cracks obey the layout.** Joints are planned cracks [6]. Uncontrolled cracks come from over-long or L-shaped
   panels, re-entrant corners, restraint and settlement [4][6][7]; D-cracks crowd along joints and corners [17][57] and
   early ASR starts at joints and corners [19]. Random full-slab Voronoi webs are wrong except for crazing
   (cells <= 40-50 mm [3][16]).
3. **Aged concrete is darker, wet concrete much darker.** Traffic dirt darkens concrete over time [46]; wetting roughly
   halves solar reflectance [45]. Efflorescence and carbonation whiten some mixes [45]. Abrasion and scaling swap paste
   colour for rock colour, darker or lighter depending on the rock [31][45]. ACI treats some cracking and curling as
   normal on every slab [29].

## 1. Construction and layout
**Flatwork (slab-on-grade).**
- Joint types: contraction (control) joints, tooled while plastic or sawn after set, induce the crack at a planned line;
  isolation/expansion joints with premolded filler separate slabs from walls, columns, footings, curbs, driveways,
  poles; construction joints end a pour, often keyed [6]. Sidewalk joints line up with curb joints [41].
- Spacing rules: maximum joint spacing 24-36 x slab thickness, never more than 4.5 m [6]; PCA uses 30 x thickness,
  ~3 m for 100 mm slabs, and allows ~6 m for 200 mm slabs [16]; <= 24 x thickness to limit curling [10]. Use <= 4.5 m
  for flatwork. Panels square or nearly so, length <= 1.5 x width, no L-shaped panels [6]. Joint depth >= 1/4 of
  thickness and >= 25 mm [6] (1/4-1/3 [4][42]). Sawing too early ravels the kerf edges [6].
- Sidewalks (US): tooled dummy joints at 5 ft (1.524 m) nominal, contraction joints <= 15 ft (4.57 m), expansion joints
  <= 45 ft (13.7 m) and around poles, posts and driveway ends, a longitudinal joint at mid-width for walks >= 8 ft [41];
  another city: contraction joints <= 1.5 x thickness-in-inches feet (6 ft for 4 in), 1/2 in expansion joints at
  driveways and rigid structures and <= 100 ft [40]. All edges and tooled joints rounded with a 1/4 in (6 mm) edger [40].
- Columns get round or square block-outs; square ones are turned 45 deg so the joints meet their corners [6].
- Finishing order: strike off, bull float (embeds aggregate), wait for bleeding to end, float, trowel, texture (broom
  after floating for exterior work), edge, joint, cure [9]. Exterior slabs are broomed for traction [4]; the broom runs
  perpendicular to traffic [33].

**Formed walls and columns.**
- **Forming systems set the tie grid.** US modular steel-ply: panels 24 in (610 mm) wide, 3-10 ft (0.9-3.0 m) tall,
  fillers 4-22 in [37]; ties pass through the side rails, so tie columns sit on the seams every 610 mm, rows at 1, 3, 5,
  7 ft from the top, then 1 ft on centre lower down on tall walls [36]. European framed panels (Doka Framax): 1.35,
  2.70 or 3.30 m tall, 0.30-2.40 m wide, two tie rows per 2.70 m panel height and ties up to 1.35 m apart; the tie
  sleeve is closed with 22 or 26 mm plugs [67]. Job-built plywood and board forms: "ties in a uniform pattern" [38] on
  a grid set by form design (est. 0.45-0.9 m), usually aligned to sheet or board joints (est.).
- Job-built and architectural forms: overlaid plywood (HDO) facing, true to 1/8 in (3 mm), level horizontal and plumb
  vertical joints, chamfered corners (3/4 in = 19 mm strips) [38].
- Tie holes: snap ties with 1 x 1 in (25 x 25 mm) plastic cones give a ~1 in breakback [35]; specs keep steel
  >= 1-1.5 in (25-38 mm) from the face and tie depressions <= 7/8 in (22 mm) across [38][66]; flat ties break back only
  1/4 in (6 mm) [36]. Tie holes are plugged except where ties are stainless [74], with mortar meant to match the wall
  [38][74].
- **Surface class** limits offsets and fins at form joints ("abrupt irregularities") and gradual bulges under a 1.5 m
  straightedge: Class A 3 mm, B 6 mm, C 13 mm, D 25 mm [66]. ACI 347 makes C the default for permanently exposed
  surfaces when nothing is specified [66]; ACI 301 specifies A for surfaces exposed to public view [74].
- **Lifts and layers.** A lift (the concrete between two horizontal construction joints) is placed in several layers
  [25]. Lift joints are straight and level at the top of a lift, formed to a grade strip, often hidden by a rustication
  strip; the form is re-anchored and tightened over the hardened lift to stop offsets and grout leakage [66]. Lift
  height 1.2-3 m (est.: framed panels 2.70 m [67]; low-lift forms 1.5-3 m [66]). Layer lines are dark horizontal lines
  between placements, visible only where a delay let the lower layer stiffen [7][27]; they follow the top of the placed
  layer, roughly level but undulating (est.). Vertical form lines between panels can start cracks [7].
- **Wall joints.** Vertical contraction joints (a V-groove or rustication with sealant) at about 1 x wall height for
  walls over 3.6 m, 3 x height for walls under 2.4 m, <= 7.6 m apart, one 3-4.5 m from corners [68]; DOT retaining
  walls: contraction joints <= 9.1 m [69] or 7.6 m with every fourth an expansion joint [70]. Expansion joints in long
  walls 60-90 m apart, 19-25 mm wide [68].
- **Retaining walls** drain the backfill through weep holes: 75 mm diameter, 150 mm above final grade, ~3.7 m apart
  [69] or <= 3 m apart [70]; a second row lower down on tall walls [69]. Each is a water source (4.13, 4.14).
- **Board-formed walls** copy the boards: grain relief, board-joint lines, board-to-board offsets and per-board shade
  (est.: absorbent boards darken the face). The shade is a w/c difference through the outer ~20 mm, not a skin
  colour: a draining form lowers w/c through that zone (CPF liners: "the outer 20 mm" [75], durability like 15-20 mm
  of extra cover [76]); raw boards absorb less and unevenly, so the depth is an estimate (est. several mm to ~20 mm).
  Model board tone through F0-F1, so it survives decades of erosion until aggregate shows (4.1). Dressed widths follow the nominal-minus-1/2-3/4 in rule [56]. The tie grid
  is usually aligned to boards (est.). Research the specific style live; this sheet gives only the general rules.

**What the layout fixes.** Set at construction and never moved by aging: joint centrelines, kerf/groove widths and
depths, isolation-filler strips, slab edges and their tooled radius, panel outlines, broom direction per panel, form
panel seams and fins, tie-hole grid, chamfers, board lines, lift joints and rustications, wall joints, weep holes,
rebar or mesh positions and cover depth, and the coarse-aggregate particle field. Aging may damage material beside or
inside these footprints, but the footprints themselves are inputs. Panel movement (4.5) is the one geometry change, and
it is a layout parameter applied to the `nowear` render too.

## 2. Dimensions and scale
| Feature | Typical | Range | Variant / notes | Source |
|---|---|---|---|---|
| Sidewalk thickness | 100 mm | 100-150 mm | 4 in walks <= 8 ft wide, 5 in for 8-10 ft, 6 in driveways | [40][41] |
| Contraction joint spacing, slab | 3 m (100 mm slab) | 2.4-4.5 m | 24-36 x thickness, NRMCA cap 4.5 m [6]; PCA allows ~6 m at 200 mm [16] | [6][16] |
| Sidewalk tooled joint spacing | 1.524 m | 1.5-1.8 m | 5 ft nominal; deeper contraction joint <= 4.57 m | [40][41] |
| Expansion / isolation joint | 13 mm filler | 13 mm | 1/2 in premolded filler, not above surface | [40] |
| Joint depth | T/4 | T/4-T/3, >= 25 mm | 25-33 mm in a 100 mm slab; model 8-12 mm (est.: invisible at 2-4 px, saves height range) | [4][6][42] |
| Sawcut kerf width | 3 mm | 3-5 mm | one blade (est.: diamond blade kerf); sealant reservoirs widened to 6-10 mm (est.) | (est.) |
| Joint opening (panel separation) | 0-2 mm | 0-25 mm | working joints open with shrinkage and cooling (est. from 4.3); roots, heave, creep 5-25 mm (est.) | (est.) |
| Tooled groove (bit) width | 5 mm | 3-6 mm | plus a 6 mm radius shoulder each side, so 15-18 mm visible (est.) | [40], (est.) |
| Edge radius (edger) | 6 mm | 3-13 mm | 1/4 in specified [40]; other edger sizes (est.: hand-tool range) | [40] |
| Coarse aggregate top size | 19-25 mm | 9.5-37.5 mm | 3/4-1 in flatwork [2]; "1 in x No. 4" Caltrans primary [43]; pavements larger (est.) | [2][43] |
| Fine aggregate (sand) | < 4.75 mm | 0.075-4.75 mm | passes No. 4 sieve [43]; lower bound (est.: No. 200 sieve) | [43] |
| Mortar cover over coarse aggregate (flatwork) | 5 mm (est.) | 3-10 mm (est.) | inferred: moderate scaling exposes aggregate after 3-10 mm loss [2]; paper scaling ~3 mm [18] | (est.) |
| Paste skin / laitance | 0.1-0.5 mm | 0.1-3 mm | cement skin ~0.1 mm [61]; crazing <= 3 mm deep [3]; delaminations 3-6 mm thick [11] | [3][11][61] |
| Formed-face mortar skin | 5 mm | 5-12 mm | ~5 mm mortar skin [61]; up to ~D/2 for 25 mm aggregate (est.: wall effect) | [61], (est.) |
| Broom striation depth | 2 mm | 1.5-3 mm | ACI 330.1 / MasterSpec 1/16-1/8 in; light broom +/-1.6 mm | [21][33][39] |
| Broom striation spacing | 2-4 mm (est.) | 1-6 mm (est.) | bristle tracks merge into ridges; estimated from bristle pitch | (est.) |
| Tining / drag (pavement) | 3 x 3 mm grooves | 1.5-6 mm deep | 13 mm transverse (random 10-21 mm), 19 mm longitudinal pitch; burlap drag ~0.2 mm deep | [21][22] |
| Diamond grinding | 5-6 mm groove pitch | 160-200 blades/m | removes 2.5-20 mm; leaves fins | [21][22] |
| Exposed aggregate etch | 1.5-6.5 mm | 0.1-7 mm | 0.2-0.5 x chip size (3-38 mm chips) | [34] |
| Form panel (modular US / framed EU) | 610 x 2440 mm | 0.3-2.4 x 0.9-3.3 m | US fillers 102-559 mm [37]; Doka 1.35/2.70/3.30 m tall [67] | [37][67] |
| Tie hole | 25 mm dia, 25 mm deep | 22-26 mm | US cone grid 610 mm x 305-610 mm [35][36]; Doka plugs 22/26 mm, ties <= 1.35 m apart [67] | [35][36][38][67] |
| Abrupt irregularity (fin, offset at form or board joints) | 13 mm (Class C) | 3-25 mm | Class A 3, B 6, C 13, D 25 mm [66]; architectural specs grind fins > 1.6-3 mm [39] | [39][66] |
| Chamfer | 19 mm | | 3/4 in strips | [38] |
| Board width (board-formed) | 140 mm | 89-184 mm | 1x4 / 1x6 / 1x8 dressed widths (est.: nominal minus 1/2-3/4 in [56]) | [56], (est.) |
| Wall contraction joint spacing | 1-3 x wall height | <= 7.6-9.1 m | 1 x H above 3.6 m, 3 x H below 2.4 m [68]; DOT walls <= 7.6-9.1 m [69][70] | [68][69][70] |
| Weep hole | 75 mm dia | | 150 mm above grade, 3-3.7 m apart | [69][70] |
| Lift height (walls) | 2.4-2.7 m (est.) | 1.2-3 m (est.) | framed panel height [67]; low-lift 1.5-3 m [66] | (est.) |
| Base-restraint crack spacing (walls) | 1.5 x H | 1-2 x H | start at the base, progress upward | [68][71] |
| Bug holes (surface air voids) | 2-10 mm (est.) | <= 15-16 mm | formed surfaces only | [25][30] |
| Bug hole area fraction | <= 1 % | <= 2 % | acceptable smooth-form (1 %) / as-cast (2 %); fill if > 6 mm deep | [39] |
| Crazing cell size | 20-40 mm | 10-50 mm | <= 40 mm typical, 12-20 mm unusual; <= 3 mm deep | [3][16][18] |
| Plastic shrinkage crack spacing | 0.3-1 m | few cm-3 m | parallel, rarely reach slab perimeter; may reach mid-depth | [5][16] |
| Map (pattern) crack cell, drying or ASR | 100-300 mm (est.) | 50-500 mm (est.) | estimated from published photographs [19][24] | (est.) |
| D-crack zone width | 0.3-0.6 m | | disintegration within 1-2 ft of the joint or crack | [57] |
| Crack width, hairline | < 0.1 mm (est.) | | "barely perceptible" [24]; 0.1 mm is the tightest design guide [50] | [24][50] |
| Crack width, "reasonable" in RC | 0.10-0.41 mm | | ACI 224R design guide, wet/aggressive to dry exposure; some cracks exceed it | [50] |
| Crack width, LTPP severity | L < 3 mm | M 3-13 / H >= 13 mm | longitudinal; transverse M 3-6, H >= 6 mm | [17] |
| Scaling depth | 3-13 mm (pavement) | 3 to > 20 mm | rating 1: <= 3 mm; medium 5-10, severe 11-20, very severe > 20 mm | [17][18][23] |
| Pop-out diameter / depth | 25-50 mm | 5-300 mm | 6 mm to "a few inches" [14]; pavements 25-100 mm wide, 13-50 mm deep [17][57]: depth ~0.5 x diameter | [14][16][17][57] |
| Spall (non-joint) | >= 25 mm deep, >= 150 mm | smaller occur | circular/oval, or elongated along joints | [16] |
| Joint spall width (from joint face) | < 75 mm (low) | 75-150 / > 150 mm | measured within 0.3 m of the joint | [17] |
| Blister | 5-100 mm dia | | skin ~3 mm thick over a void; troweled slabs | [16] |
| Rebar cover at a visible face | 38-50 mm exposed | 19-50 mm | ACI 318: 38 mm (No. 5 and smaller) / 50 mm exposed to weather, 19 mm interior slabs and walls (No. 11 and smaller); "usually 50-68 mm" specified [18]; 76 mm only for faces cast against earth [28] | [18][28][60] |
| Patch (partial depth) | >= 40 mm deep | | rectangular, vertical edges, 100 mm beyond unsound concrete | [16] |

**Recommended tile sizes (2048 px).** Pixel figures are arithmetic on the dimensions above.
- **Sidewalk / plaza field: 3.048 m** (2 x 2 panels of 1.524 m) = 1.49 mm/px. Tooled groove 3-6 mm = 2-4 px,
  shoulders 4 px each, pop-outs 17-34 px. Hairline cracks and broom striations are sub-pixel: draw cracks as 1-2 px
  albedo/normal lines and treat broom as an anisotropic normal/roughness band. The 15 ft contraction joint needs a
  3 x 3 tile (4.572 m, 2.23 mm/px; widen tooled grooves to >= 4.5 mm or draw them in normal/albedo only). The 45 ft
  expansion joint cannot repeat in a practical tile: add it as a non-tiling decal or a separate panel variant.
- **Sawcut floor or driveway: 3.0 m** (one panel, the kerf split across the tile border) = 1.47 mm/px, so a 3 mm kerf
  is 2 px. A 6 m 2 x 2 tile would make the kerf 1 px; do not use it for close views.
- **Formed wall, US modular: 2.4384 m** (4 panels x one 8 ft panel height) = 1.19 mm/px. Tie columns at 610 mm and
  rows at 0.305/0.914/1.524/2.134 m from the top repeat exactly; tie holes 18-21 px; Class A fins ~2-3 px. Framed EU
  panels: 2.70 m (1.32 mm/px) holds two 1.35 m tie columns and one panel height.
- **Board-formed wall:** the tile must hold whole repeats of board width, tie spacing and board-end stagger, e.g.
  16 x 140 mm = 2.24 m with ties every 4 boards (560 mm) both ways and 2.24 m boards staggered by half (est.);
  1.09 mm/px. Lift joints and wall joints rarely fit a square repeat: add them as decals or a separate variant.
- **Close-up: 0.5 m** (0.24 mm/px) for broom striations (4-16 px period), sand grains, crazing, bug holes, pop-outs;
  1.0 m (0.49 mm/px) when one joint must cross the tile.
- **Pavement panel (JPCP):** panels ~3.7 x 4.5 m (est.: 12 ft lane x 15 ft joints) do not fit a square repeat; map one
  2048 tile per panel with non-uniform UV scale (1.8 x 2.2 mm/px) or accept a 4.572 m single-panel tile.

## 3. Layer model (stratigraphy)
**Flatwork (troweled, floated or broomed slab), top down.**

| Layer | Physical | Depth below original surface | Appearance | Visible when |
|---|---|---|---|---|
| D. Deposits | dirt, tyre rubber, oil, efflorescence/calcite, biofilm, lichen, moss, sealer | above (0-1 mm (est.); moss and lichen more) | darker (dirt, oil, rubber, biofilm) or white (salts) | any age; own mask |
| L0. Finish skin | paste-rich skin (laitance) densified by trowel; carries broom grooves | 0-0.5 mm [61], (est.) | uniform grey; trowel burn darker [12][16]; smooth (trowel) or striated | new |
| L1. Surface mortar | paste + sand, coarse aggregate pushed below by floating | ~0.5-5 mm (3-10 mm, est.) | grey "salt and pepper" sand speckle; matte, open pores | dusting, light wear, light scaling (rating 1-2) |
| L2. Concrete body | coarse aggregate (rounded gravel or crushed rock) in mortar | 3-10 mm (est.) down to slab bottom | rock colours (gravel multicoloured, limestone pale grey, basalt dark (est.)); natural, fractured or cut faces | moderate+ scaling, wear, pop-outs, spalls, grinding (CPC B to C) [23][31] |
| L3. Reinforcement | mesh in slabs; rebar in walls, structural slabs, decks | at cover: 19-50 mm at visible faces [60] | orange-brown rust, metallic only where freshly abraded | only in spalls deeper than cover [13][16] |
| L4. Subbase | granular fill | below slab | not visible except at broken edges | out of scope |

**Formed surface, face inward.** F0 cement skin copying the form (plywood or board grain, overlay gloss; ~0.1 mm [61])
-> F1 mortar skin where coarse aggregate cannot pack against the form (~5 mm [61], up to D/2 (est.)) -> F2 concrete
body -> F3 rebar at cover. Bug holes, fins, offsets, tie cones, layer lines and sand or form streaks belong to the
as-built F0 surface [25][27][39].

**Original surface envelope.** The as-finished surface: the struck-off plane plus broom grooves, trowel finish, tooled
joints and edge radii, sawcuts and saw raveling, stamped relief, form print, fins and offsets, tie-cone recesses and
plugs, rustications and as-cast bug holes. Removal processes (dusting, wear, scaling, flaking, pop-outs, spalls,
grinding, delamination, surface erosion) only go below it. Only deposits (dirt film, rubber, oil, salts, calcite,
biofilm, lichen, moss, sealer, extruded sealant, paint) sit above it, each with its own mask. **Rigid motions**
(curling, faulting, joint opening, heave, ASR blowups [10][17][19]) move whole panels without removing material: apply
them with the same parameters to the `nowear` render, so the envelope compares like with like (`checks.md`). Patches
are replacement material near the envelope (+/- 1 mm (est.); LTPP rates patch settlement up to 6 mm and more [17]) with their own mask, excluded from the
envelope check.

**Cross-section: slab A | joint | slab B (flatwork), with damage on slab A only.**
```
            dirt film / efflorescence = deposits (above envelope, own mask)
 envelope -> ======broom======.     .--. kerf 3-5 mm, sealant recessed      .======broom======
             paste skin L0   / r6  |    |                              r6  \  L0
     ___spall (slab A)___   /      |seal|      L1 mortar + sand speckle     \_______________
    / fractured aggregate \_/       |    |  (o)    (O)     (o)   (O)    (o)    L2 aggregate
   |  (O)  (o)  (O)  (o)  |         |....|<- crack below the joint, width unchanged by wear
   |___________ slab A ___|  (o)    |    |   (O)    slab B    (o)     (O)
      #rebar# (cover 38-50 mm, only if reinforced)  |    |       #rebar#
```
The spall removes slab A concrete and shows slab A's fractured aggregate and mortar. The kerf, sealant and slab B
edge are untouched; the joint looks wider from above only because slab A's arris is gone. If slab A's spall goes below
the sealant top, slab B's sawn kerf face shows: a flat vertical face cut through aggregate. That is the one allowed
view of a neighbour's side.

**Wall face, from the form inward:** `form | F0 skin | F1 mortar skin ~5 mm | F2 body (O)(o)(O) | #rebar# at cover`.
Tie cone: 22-25 mm recess, later plugged [35][38][67]; bug hole: <= 15 mm cavity in F0/F1 [25]; fin or offset at a
seam: 3-25 mm by surface class [66].

## 4. Processes: aging, wear, damage, deposition
Cards 4.1 and 4.17 are construction-time (as-built) processes; they set the envelope that later removal works on.
**Aggregate reveal has three forms by removal process** (used by 4.6, 4.7, 4.19 and section 10):
- *Scaling, flaking, paste erosion* (freeze-thaw, salts, acid etching): mortar is removed, rock is not. Particle tops
  keep their natural shape and stand proud [16].
- *Abrasion* (traffic): paste and rock wear together, paste faster; rock tops are planed and polished, the mortar
  recessed a little between them; the recess stops growing once rock carries the load [44].
- *Cutting* (grinding, polishing, diamond grinding, saw cuts): one plane through paste, sand and rock; aggregate is
  seen in cross-section, flush [31].
In scaling and abrasion, a particle exposed beyond about half its size loosens and drops out, leaving a socket (est.: exposed
aggregate finishes keep the etch at 0.2-0.5 x chip size [34]); very severe scaling loses whole particles [16].

### 4.1 As-built colour and finish variation (trowel burn, curing mottle, batch and form colour)
- **Mechanism:** surface w/cm sets paste colour. Hard troweling densifies the surface, lowers w/cm and leaves the ferrite
  phase dark, so burned areas are darker; early troweling or worked-in bleed water is lighter; higher w/cm is lighter
  [12][16]. Calcium chloride mottles dark; poly sheet in contact cures lighter, wrinkles leave dark streaks [8][16].
  Slag cement is lighter, fly ash and silica fume darker; forms of different absorption or release agent give different
  shades [12]. Sand colour shifts concrete albedo as much as cement does [45]. On formed faces the form's absorption
  sets w/c through the outer ~20 mm [75][76], so form and board shade belongs to F0 and F1 together, not to the
  0.1 mm cement skin alone: a weathered board-formed wall keeps its board tone after the skin erodes (est.: it fades
  only as F2 aggregate comes through).
- **Acts on:** L0 / F0 (form shade: F0-F1). **Removes / adds:** nothing (colour; burnish lowers roughness). **Reveals:** nothing.
- **Never:** changes height beyond trowel chatter; continues across a construction joint as if one batch (est.:
  batches and pours change at joints).
- **Where:** late-troweled zones in overlapping power-trowel arcs (est.: 0.9-1.2 m rings); edges and joints worked by
  hand tools (est.); sheet-wrinkle lines; whole panels or pours (batch); whole form panels, boards or lifts (formed).
- **Shape and scale:** arcs and swirls 0.3-1.2 m (est.); panel-sized blocks; streaks along sheet folds.
- **Progression:** fixed at construction; some types fade with wear and age, trowel burns resist treatment [12].
- **Signature per map:** albedo trowel burn -0.03 to -0.08 linear (est.), panel-to-panel luma CV 2-6 % (est.); roughness
  burnish 0.30-0.45 vs 0.50-0.60 around (est.); height chatter ripples <= 0.3 mm (est.); AO none.
- **Severity scale:** none published. **Sources:** [8][9][12][16][45].

### 4.2 Plastic shrinkage cracking
- **Mechanism:** evaporation exceeds bleeding before set; capillary tension cracks the plastic surface [5].
- **Acts on:** L0-L1, can reach mid-depth [16]. **Removes / adds:** nothing at first. **Reveals:** a dirt-filled line.
- **Never:** forms a polygon network (that is crazing or map cracking) or follows joints; it rarely reaches the slab
  perimeter [5], so these cracks may float free of the joint net.
- **Where:** horizontal surfaces on hot, dry, windy days (wind > 5 mph) [5]; whole placements.
- **Shape and scale:** roughly parallel cracks 0.3-1 m apart [5], few cm to 3 m [16]; surface width 0.1-1 mm tapering
  to tips (est.).
- **Progression:** forms in hours [5]; later widened by drying shrinkage and dirt; edges may ravel (est.).
- **Signature per map:** height groove <= 0.5 mm (est.); albedo dark 1-2 px line; roughness slightly up; AO faint.
  **Severity scale:** LTPP width bands if they open [17]. **Sources:** [5][16].

### 4.3 Drying-shrinkage, restraint and settlement cracking
- **Mechanism:** concrete shrinks ~1.6 mm per 3 m on drying and ~0.7 mm per 3 m for a 22 degC night drop [16]; restraint
  (subgrade, re-entrant corners, embedments, footings) turns that into tension; also subgrade settlement and plastic
  settlement over shallow bars [4][7][16][18].
- **Acts on:** full depth of slab or wall. **Removes / adds:** nothing until the edges spall. **Reveals:** a dark line;
  when spalled, the same slab's interior (4.9).
- **Never:** makes a closed cm-scale network; moves or widens a joint; wanders across a working joint (est.: a joint is a
  free edge; misaligned T-joints are the exception and pass "sympathy" cracks across). A crack below a sawcut is the
  joint working, not damage [6].
- **Where:** slabs: mid-panel, perpendicular to the long side, when spacing exceeds 24-36 x thickness or L > 1.5 W [6];
  diagonally from re-entrant corners of L-shaped slabs, block-outs and openings [7][53]; at slab-to-wall or column
  contact without isolation [4][6]; lines mirroring shallow rebar (plastic settlement) [18]; pavement corner breaks cut
  a corner at ~45 deg between two joints [17]. Walls: base-restrained vertical cracks start at the footing and grow
  upward, spaced 1-2 x wall height [68][71]; they are narrowest at the base and widest some way up (around 0.1 x their
  length above the base or higher) [72], and often stop below the top (est.); diagonal cracks from opening corners [7];
  cracks at vertical form lines [7].
- **Shape and scale:** one or two cracks per bad panel (est.); slab cracks 0.1-3 mm wide (est.; LTPP low < 3 mm [17]);
  straight at metre scale, meandering at aggregate scale; going around aggregate is not diagnostic [18].
- **Progression:** weeks to months; widens; arrises ravel and spall; faulting across the crack on slabs on grade [17].
- **Signature per map:** height groove 0.1-3 mm wide plus spalled shoulders later; albedo dark line, optional white
  efflorescence fringe; roughness up in the crack; AO strong.
- **Severity scale:** LTPP longitudinal L < 3, M 3-13, H >= 13 mm; transverse L < 3, M 3-6, H >= 6 mm; M also by spalling
  < 75 mm or faulting up to 13 (longitudinal) / 6 mm (transverse), H by spalling >= 75 mm or larger faulting [17];
  ACI 224R design guide 0.10-0.41 mm [50]. **Sources:** [4][6][7][16][17][18][50][53][68][71][72].

### 4.4 Crazing
- **Mechanism:** shrinkage of the paste-rich skin (wet mix, overworking, cement dusted on, late curing, wet-dry cycles)
  [3][16].
- **Acts on:** L0 only, rarely > 3 mm deep [3]. **Removes / adds:** nothing. **Reveals:** nothing; seen through dirt in
  the cracks and wet/dry contrast.
- **Never:** reaches aggregate; grows into map-cracking scale; predicts later failure [3][16].
- **Where:** most visible on steel-troweled surfaces [3]; whole placements; also on formed faces (est.).
- **Shape and scale:** irregular hexagons <= 40 mm, 12-20 mm in unusual cases [3]; < 50 mm, "chicken-wire" [16][18].
- **Progression:** appears day 1 to week 1, then static; more visible as dirt embeds [3][16].
- **Signature per map:** height ~0 at slab scale; albedo thin dark network, strongest while drying after rain [3][16];
  roughness unchanged. **Severity scale:** none. **Sources:** [3][16][18].

### 4.5 Panel movement: curling, faulting, joint opening, heave (rigid motion)
- **Mechanism:** the top dries or cools and shrinks more than the bottom, lifting edges and corners; hot tops curl
  down [10][16]. Working contraction joints open as the slab shrinks and cools (4.3: ~2.3 mm per 3 m for drying plus a
  22 degC drop [16]); joints next to sawcuts that never cracked carry the extra length and open wider (est.). Tree roots
  and frost heave lift and push sidewalk panels; slabs on slopes creep (est.).
- **Acts on:** whole panels. **Removes / adds:** nothing. **Reveals:** the joint opening (kerf + separation), a step at
  joints; corner cracks under load.
- **Never:** is modelled by adding height inside one panel's damage mask; moves a joint centreline beyond the
  separation; appears only in the preset render (it belongs to `nowear` too).
- **Where:** thin slabs, long joint spacing, slabs on vapour retarders, at joints, edges, corners [10]; trees and
  driveway aprons for heave (est.).
- **Shape and scale:** curl lip 0.5-3 mm at joints (est.); faulting in mm [17]; opening 0-2 mm on working joints,
  5-25 mm with roots or heave (est.); corner breaks ~45 deg [17].
- **Progression:** curl at early age, decreasing with time; heave grows with the tree; lifted edges chip under hard
  wheels [10].
- **Signature per map:** per-panel planar offset/tilt; joint mask width = kerf + opening; small normal step and AO line
  at joints; chips on the high side.
- **Severity scale:** faulting in mm [17]. **Sources:** [10][16][17].

### 4.6 Scaling, mortar flaking and delamination
- **Mechanism:** freeze-thaw of a saturated surface, made worse by deicers; weak surfaces from worked-in bleed water,
  overfinishing, no air entrainment or poor curing [2][16]. Delamination: a 3-6 mm troweled layer sealed over bleed
  water or air breaks off under traffic [11][16].
- **Acts on:** L0 -> L1 -> mortar between L2 particles. **Removes:** paste, then mortar. **Reveals:** sand speckle, then
  coarse aggregate with intact natural surfaces that stand out of the scaled surface [16]. Mortar flaking ("popoffs")
  strips the thin mortar over near-surface particles, flat particles first [14][16].
- **Never:** fractures coarse aggregate (that is a pop-out) [16]; reveals a uniform "sub-layer" colour, joint filler or
  subbase; leaves aggregate lower than the mortar around it, except sockets where very severe scaling (> 20 mm) has
  lost whole particles [16]; raises the surface.
- **Where:** where water stands and salt is applied: low spots, along joints and cracks, slab edges, driveway aprons,
  walking and wheel paths (est.); pavement scaling "may occur anywhere" [17]; freeze-thaw paste damage starts near
  joints and cracks [20]; often after the first or second winter on poor concrete [16].
- **Shape and scale:** starts as small local patches that merge [2]; ragged outlines with 1-3 mm terraces (est.); depth
  3-13 mm on pavements [17]; light (no coarse aggregate), medium 5-10 mm, severe 11-20 mm, very severe > 20 mm [18].
- **Progression:** ASTM C672 visual rating, a lab test on cast specimens, withdrawn 2021 [23]: 0 none; 1 very slight,
  <= 3 mm, no coarse aggregate visible, no pop-outs; 2 slight to moderate and/or a few pop-outs; 3 moderate, some coarse
  aggregate exposed; 4 moderate to severe, aggregate clearly exposed; 5 severe, coarse aggregate over the entire
  surface. [23] suggests mass-loss equivalents (not part of C672): 0-50, 51-210, 211-500, 501-1300, 1301-2100,
  > 2100 g/m2, i.e. at most ~0.9 mm uniform (est.: density 2.3 t/m3), so field scaling is patchy: ~3 mm deep over ~30 %
  equals the top band (est.). Presets use C672-style ratings (adapted): new 0, in-service 0-1, weathered 1-3,
  distressed 3-5.
- **Signature per map:** height terraces below the envelope with aggregate domes 1-5 mm proud of the mortar (est.),
  never more than ~half the particle size; normal crisp patch rims; albedo fresh scars lighter than the dirty skin
  (+0.02-0.06 linear, est.), aggregate in rock colours; roughness mortar 0.90-0.95, aggregate 0.60-0.80 (est.); AO in
  crevices around aggregate.
- **Severity scale:** C672-style 0-5 [23]; light to very severe [18]; airfield PCI scaling low < 1 %, medium 1-10 %,
  high > 10 % of slab area [57]. **Sources:** [2][11][14][16][17][18][20][23][57].

### 4.7 Dusting, abrasion and traffic wear
- **Mechanism:** a weak skin powders under traffic [1][16]; traffic removes paste and texture faster than aggregate and
  then polishes the aggregate tops [21][44].
- **Acts on:** L0 -> L1 -> L2 tops. **Removes:** paste, sand, then aggregate tops are planed and polished (abrasion form
  above). **Reveals:** the CPC sequence: cream (paste) -> salt-and-pepper (sand) -> coarse aggregate, with colour
  shifting from grey toward the aggregate's hue [31].
- **Never:** deepens or widens joints; works in sheltered low spots more than on contact high points (est.); leaves
  rounded rock domes standing several mm proud (that is scaling).
- **Where:** wheel paths, sidewalk centrelines, doorways and thresholds, stair nosings, ramps, turning areas, forklift
  aisles (est.); joint arrises and slab edges chip first (est.).
- **Shape and scale:** diffuse bands (est.: wheel paths 0.6-0.9 m wide); highways with studded tyres wear 0.04-0.5 mm/yr
  [44], pedestrian and non-studded traffic far slower (est.); turf-drag texture depth falls ~1/3 after the first
  winter [21].
- **Progression:** fast while paste and texture wear (first ~5 yr), slow once hard aggregate carries the wear; paste
  between particles wears faster and leaves aggregate raised [44]. Stage 1 texture softened; 2 sand speckle; 3 polished
  flat aggregate tops 0.5-2 mm over the mortar (est.).
- **Signature per map:** height texture amplitude reduced, slight dish <= 0.5-5 mm (est.); albedo path darker where
  tyres and dirt dominate, lighter where fresh paste is abraded (est.); roughness polished tops 0.40-0.60 (est.);
  AO reduced.
- **Severity scale:** LTPP "polished aggregate", no levels [17]; WSDOT rut depth [44]. **Sources:** [1][16][17][21][31][44].

### 4.8 Pop-outs
- **Mechanism:** a porous near-surface particle (chert, shale, pyrite, coal, soft limestone) swells with water or
  freezing, or ASR gel forms; a cone of mortar breaks away [14][16].
- **Acts on:** L0-L2 above one particle. **Removes:** a cone of mortar plus the top of the particle. **Reveals:** the
  fractured particle at the bottom, part still adhered [14][16]. ASR pop-outs are small, the particle often unsplit, with
  a damp or discoloured spot [14]. Pyrite particles leave a rust-brown spot (est.).
- **Never:** a smooth hemispherical hole; a pit with paste at the bottom; a cone not centred on a particle.
- **Where:** exterior horizontal surfaces exposed to freezing while moist [14]; randomly placed (particles are random),
  more in wet zones (est.).
- **Shape and scale:** conical, "inverted pyramids" [55]; 6 mm to a few inches [14]; usually 5-50 mm, up to 300 mm [16];
  25-100 mm wide and 13-50 mm deep on pavements [17][57], so depth ~0.5 x diameter, capped at the particle, and cone
  walls 45-60 deg (est. from those ratios).
- **Progression:** mostly in the first year; ASR pop-outs within days to weeks [14][16]; deeper particles later [55].
- **Signature per map:** height cone with a rough flat bottom at the particle; albedo bottom = fresh fracture of the
  particle (chert often pale (est.)), walls fresh mortar; roughness 0.80-0.90 (est.); AO strong.
- **Severity scale:** count; airfield PCI counts them above ~3 per yd2 [57]. **Sources:** [14][16][17][23][55][57].

### 4.9 Joint and crack spalling
- **Mechanism:** incompressibles in open joints, curled lips, hard wheels, freeze-thaw, D-cracking or ASR weakening near
  joints, misaligned dowels [6][10][16][17][19]. Saw raveling (kerf edges chipped when sawing too early [6]) is
  as-built: it belongs in `E` and the `nowear` render, so a new slab may already show it (est.: 1-5 mm chips along part
  of a joint).
- **Acts on:** slab concrete within 0.3 m of the joint or crack face [17]. **Removes:** wedge-shaped arris pieces.
  **Reveals:** fractured mortar and aggregate of the same slab; below the sealant top, the neighbour's sawn face.
- **Never:** widens the kerf or sealant below; moves the joint line; takes material from the neighbouring slab just
  because one side spalled (est.: each side has its own damage).
- **Where:** along joints and cracks, joint crossings and T-intersections (est.), the higher lip of curled joints [10],
  industrial joints under hard wheels [6].
- **Shape and scale:** elongated along the joint; width from the joint face L < 75, M 75-150, H > 150 mm [17]; shallow
  road joint spalls up to 75 mm wide by 150-300 mm long are often left unrepaired (source inconsistent [16]);
  partial-depth repair limit = top 1/3 of the slab [16]; conchoidal, ragged outline (est.).
- **Progression:** chipped arris (few mm) -> raveled band (10-30 mm, est.) -> 75-150 mm spalls -> loose pieces and patches
  [16][17].
- **Signature per map:** height ramp from the envelope down to 10-40 mm at the joint face (est.), sharp outer breakout
  edge; albedo fresh fracture lighter, later dirt-filled; roughness 0.85-0.95 (est.); AO in the trough.
- **Severity scale:** LTPP L/M/H [17]. **Sources:** [6][10][16][17][19].

### 4.10 D-cracking (frost damage of coarse aggregate)
- **Mechanism:** saturated frost-susceptible coarse aggregate dilates and fractures [20]; it starts at joints at the
  bottom of exterior slabs and shows years later [4].
- **Acts on:** L2 near joints, then the whole depth. **Removes:** later, disintegration and spalls. **Reveals:**
  fractured aggregate.
- **Never:** starts mid-panel; spreads evenly over the slab; forms a uniform polygon map.
- **Where:** next to joints, cracks and free edges, starting at slab corners [17]; disintegration within 0.3-0.6 m of the
  joint [57]; a figure-of-eight ("hourglass") patch at joint crossings (est.: corners of four slabs meet there).
- **Shape and scale:** closely spaced crescent-shaped hairline cracks roughly parallel to the joint [17][24]; spacing
  25-75 mm (est.); dark colouring of the cracks and surrounding area [17][57].
- **Progression:** appears 10-15 yr after construction [20]; low = tight cracks; moderate = well-defined with some loose
  pieces; high = significant missing material [17].
- **Signature per map:** albedo dark damp band along joints (-0.05 to -0.10 linear, est.) with fine crack lines; height
  later spalls at the joint; roughness up where disintegrating.
- **Severity scale:** LTPP L/M/H [17]; PCI [57]. **Sources:** [4][17][20][24][57].

### 4.11 Alkali-silica reaction (map cracking, gel, staining)
- **Mechanism:** reactive silica, high-alkali pore solution and moisture make an expansive gel [15][19].
- **Acts on:** the body; cracks show at the surface. **Removes:** nothing at first; later spalls at joints. **Adds:**
  gel or lime exudation (deposit).
- **Never:** develops in concrete kept dry [15]; forms random maps on restrained members (cracks align with the
  restraint: longitudinal in pavements, vertical in columns) [19]; shows extensive map cracking in the "new" preset
  (typical onset 10-15 yr [15], 5-15 yr [20]; earlier with highly reactive aggregate (est.); ASR pop-outs can appear in
  weeks [14]).
- **Where:** pavements: first at and perpendicular to joints, map cracking first at slab corners, then around the slab
  perimeter with little in the centre, then the whole slab with longitudinal bias [19]; above-grade wet/dry faces show
  it most [19]. The width of the early joint band is not published (est. 0.3-1 m).
- **Shape and scale:** cells 100-300 mm (est.); cracks up to 5-10 mm wide when severe [19], up to 12.7 mm [24]; a broad
  brownish "permanently damp" border; white gel or lime exudations; joint closure, sealant extrusion, crushing and
  spalls at joints [19].
- **Progression:** fine cracks near joints -> perimeter map -> whole slab plus joint spalls [19].
- **Signature per map:** albedo brownish damp bands 20-50 mm wide (est.) along cracks, white exudation spots; height
  cracks, later joint spalls and sealant extruded above the surface (deposit mask); roughness gel glossy when wet (est.).
- **Severity scale:** descriptive only [19]. **Sources:** [14][15][19][20][24].

### 4.12 Steel corrosion: reinforcement and tie ends
- **Mechanism:** chlorides or carbonation depassivate steel (pH < 9); rust is 2-4 x the steel volume and cracks,
  delaminates and spalls the cover [13]; cracks run in the plane of the bars [18]. Tie ends left close to a formed face
  (flat ties broken back only 6 mm [36], snap ties not broken back or plugs lost) corrode first because their cover is
  a few mm (est.); specs ask for >= 25-38 mm of cover over tie ends and for plugged holes [38][66][74].
- **Acts on:** cover concrete over bars; tie ends at tie holes. **Removes:** cover in spalls. **Reveals:** the rusted
  bar at cover depth. **Adds:** rust stain (deposit).
- **Never:** exposes a bar in a spall shallower than the cover; shows bars that are curved, random or off the layout
  grid; occurs in plain (unreinforced) sidewalks; puts tie-end rust off the tie grid.
- **Where:** reinforced members with shallow cover and salt or water: decks, parking slabs, walls in splash zones,
  drip edges [13] (est. for locations); tie-end rust on the tie grid, more on wet and north faces (est.).
- **Shape and scale:** cracks along bars at the bar spacing (est.: 150-450 mm); spalls >= 25 mm deep, >= 150 mm across
  [16], elongated along bars (est.); bar shows as a half-exposed cylinder in a trough along its axis (est.: spalls break
  in the bar plane [18]); rust runs 0.1-1 m down walls (est.); tie-end rust: a 5-20 mm orange-brown spot on the tie
  with a downward streak 50-500 mm (est.).
- **Progression:** rust spots and stains -> cracks along bars -> hollow delamination -> spall exposing the bar -> section
  loss [13][16]. Tie-end spots appear within the in-service preset (est.).
- **Signature per map:** height spall to cover depth with the bar profile; albedo orange-brown rust on the bar and
  as a stain below it; roughness rust 0.70-0.90 (est.); metallic 0 for rust.
- **Severity scale:** none general; crack width guide [50]. **Sources:** [13][16][18][36][38][50][66][74].

### 4.13 Efflorescence, leaching and calcite deposits
- **Mechanism:** water dissolves soluble salts or calcium hydroxide, moves to the surface and evaporates or carbonates,
  leaving white deposits; needs salts, water and evaporation together [16]. Leachate through cracks also builds calcite
  crusts and straw stalactites on soffits, up to 2 mm/day, stained yellow to red by rusting steel [51].
- **Acts on:** the surface at water exits. **Adds:** white salt or calcite. **Reveals:** nothing (a deposit).
- **Never:** appears without a water path; runs uphill; covers sheltered dry areas evenly.
- **Where:** cracks, joints, cold joints and lift joints, tie holes, weep holes, wall bases, slab edges, soffits
  [16][19][51] (est. for lift joints, tie holes and weep holes); more in winter (slow evaporation) [16]. Retaining walls
  and abutments are wetted from the backfill: leaching shows at cracks where that moisture escapes [73], and a diffuse
  bloom over the face, strongest in a band above grade, where the back is not waterproofed (est.).
- **Shape and scale:** walls: white fans and streaks running down from point sources to the next ledge or to grade
  (est.: gravity; 0.2-3 m), horizontal bands with short drips along lift joints (est.); floors: halos and rims along
  cracks and joints (est.); 0-1 mm thick, thicker crusts at long-term leaks (est.).
- **Progression:** early "frosting" lightens and shrinks with time unless salt keeps coming [16]; leaching crusts grow;
  efflorescence and carbonation measurably whitened some grey-cement mixes [45].
- **Signature per map:** albedo linear 0.50-0.80 (est.); roughness 0.90-1.00 (est.); height +0-1 mm, straws on soffits;
  own deposit mask. **Severity scale:** none. **Sources:** [16][19][45][51][73].

### 4.14 Run-off staining, soiling and biological growth
- **Mechanism:** rain run-off is a film ~0.25 mm thick flowing up to 0.9 m/min; it drops its dirt where it is absorbed
  or slows [65]. Algae, mosses and biofilm colonize where moisture persists (RH > 70 %) [52]; biofilms need the surface
  pH to fall below ~10, and fresh concrete is above 12 until carbonation lowers it [64]. Lichens colonize exposed
  pavements and roof tiles over decades [62][63]. Foot and vehicle traffic darken concrete over time [46].
- **Acts on:** the surface. **Adds:** dirt, biofilm, lichen, moss (deposits).
- **Never:** algae or moss on dry, sunny, rain-washed faces; any growth on new, uncarbonated concrete (est.: < 3-5 yr);
  streaks sideways or upward on vertical faces; growth far above a splash zone without a water source (est.).
- **Where:** strips and ground next to buildings, close to the ground on north sides [52]; under drips, ledges, wall
  caps, weep holes and joints (est.); in joints and cracks of flatwork and in low spots (est.). Wall tops and corners
  take 20-30 x the rain of the face centre and wash clean [65]; on smooth faces run-off splits into streams that recur
  at the same places, while heavily textured faces carry a broken, even flow [65], so board-formed walls soil more
  evenly and streak less (est.). Lichens: sunny horizontal tops, ledges, chamfers and perches (est.).
- **Shape and scale:** streaks 10-50 mm wide below ledges, chips and low points of the top edge, ending ragged where
  water soaks in (est.); splash band 0.3-0.5 m above grade (est.); moss lines in joints 5-20 mm wide (est.). Lichen:
  round patches 5-100 mm (est.) growing up to 1.7 mm/yr in radius on sidewalk concrete [62]; one species covered
  ~2.5 % of concrete roof tiles at 30 yr, ~23 % at 45 yr, ~49 % at 60 yr [63].
- **Signature per map:** albedo green-grey to black (biofilm), dark grey (soot/dirt), lichen grey-green, orange or black
  (est.); roughness biofilm 0.60-0.80, moss 0.90 (est.); height moss +2-10 mm, lichen +0.1-1 mm (est.).
  **Severity scale:** none. **Sources:** [46][52][62][63][64][65].

### 4.15 Traffic soiling: oil drips and tyre marks
- **Mechanism and where:** oil soaks into pores under the engine of parked cars, about 1-1.5 m from the stall front;
  tyre rubber transfers on turning arcs, stop lines and garage aprons (est.). **Never:** in pedestrian-only areas or
  free of the parking/driving geometry. **Shape:** soft-edged oil blotches 0.1-0.6 m, overlapping; tyre bands
  150-250 mm wide (est.).
- **Signature per map:** albedo fresh oil x0.3-0.6 (est.); a lab oil dip then rinse changed grey-cement concretes
  little (-0.05 mean on smooth mixes, mostly from white cement) [45]; roughness fresh oil 0.30-0.50 (est.); rubber
  near-black (deposit). **Sources:** [45], (est.).

### 4.16 Patch repairs
- **Mechanism:** unsound concrete is sawn and chipped out and replaced [16].
- **Acts on:** replaces a block >= 40 mm deep [16]. **Adds:** new material near the envelope.
- **Never:** irregular blob outlines; feathered edges (chipped edges must be perpendicular or undercut [39]); a patch at
  a joint that fills the joint (the joint must be restored [16]).
- **Where:** spalls (patch 100 mm beyond unsound concrete [16]); tie holes plugged with mortar meant to match [38][74];
  honeycomb cut out with a 13-19 mm deep saw cut outline [30]; drilled-out pop-outs [16].
- **Shape and scale:** rectangles with vertical edges, often aligned to joints [16]; tie plugs 22-25 mm discs.
- **Signature per map:** albedo offset from the parent (est.: new cementitious patches read darker or more uniform; a
  repair is never as good as the original surface [27]); roughness from a different finish (est.); height flush
  +/- 1 mm with a hairline perimeter crack (est.); own patch mask. Old tie plugs: ring cracks, shade offset, or lost
  plugs showing the cone recess (est.).
- **Severity scale:** LTPP patch L none measurable, M settlement up to 6 mm, H >= 6 mm [17].
  **Sources:** [16][17][27][30][38][39][74].

### 4.17 As-built defects of formed surfaces
- **Mechanism:** air trapped against the form leaves bug holes [25][30]; too little paste or vibration leaves honeycomb
  [25][43]; mortar leaking through form joints and tie holes leaves form streaks, aggregate-textured and lacking cement
  with dark colour beside them [27]; heavy bleeding along the form washes paste off as sand streaks [25][27]; a delay
  between placements leaves layer lines (dark horizontal lines) or, if the layer had set, cold-joint lines [7][25][27];
  displaced or mismatched forms leave offsets and fins [27][66].
- **Acts on:** F0-F1 at casting (part of the envelope, not aging).
- **Never:** bug holes on troweled flatwork (est.: finishing closes surface voids); lift joints that are not straight
  and level [66]; layer lines that cross each other (est.); tie holes off the system's grid [36][38][67].
- **Where:** bug holes on vertical surfaces [30], more near the top of a lift and on battered forms (est.); honeycomb
  where consolidation is hard: congested rebar, embedments, narrow sections [27], wall bases and leaking form joints
  (est.); fins and offsets at panel seams and board joints [39][66]; form streaks along leaking seams and just below
  lift joints (est.: grout leaks under the re-set form [66]); layer lines where placement was delayed [7].
- **Shape and scale:** bug holes <= 15-16 mm [25][30][54], 0.1-2 % of the area, fill if > 6 mm deep [39]; honeycomb
  50-300 mm patches with exposed coarse aggregate (est.); abrupt irregularities by class 3/6/13/25 mm [66]; form and
  sand streaks 10-50 mm wide (est.); layer lines 5-20 mm dark bands, roughly level with +/- 20-100 mm undulation over
  metres and a step <= 1 mm (est.).
- **Signature per map:** height pits (bug holes), ridges and steps (fins, offsets), rough cavities (honeycomb), faint
  step at layer lines (est.); albedo honeycomb shows aggregate, layer lines darker, sand and form streaks speckled with
  a dark fringe [27]; roughness honeycomb and streaks high.
- **Severity scale:** surface classes A-D [66]; ACI 347.3R surface categories CSC1-4 and surface void ratio over a
  2 x 2 ft area [26]. **Sources:** [7][25][26][27][30][36][38][39][43][54][66][67].

### 4.18 Wetting and damp zones
- **Mechanism:** water fills pores and forms a film, cutting diffuse scattering and adding a specular film.
- **Acts on:** the surface. **Adds:** water (transient deposit).
- **Never:** leaves the colour unchanged; ponds on high points.
- **Where:** puddles only in low spots and joints; joints, cracks and D-crack/ASR zones stay damp longest [17][19];
  crazing shows best while drying [3]. Walls: wicking band at the base, below leaking joints and weep holes, and
  shaded north faces stay damp most of the year and read darker (est. 10-30 % darker from the wet ratio).
- **Signature per map:** albedo x0.40-0.80, typically ~0.5 (16 grey-cement mixes, weathered dry 0.20-0.44 -> wet
  0.10-0.22 solar; mean drop 0.15, 0.23 over all mixes including white cement) [45]; roughness damp 0.40-0.60, water
  film or puddle 0.02-0.10 (est.). **Sources:** [3][17][19][45].

### 4.19 Polished concrete (brief)
- **Process:** grinding with progressively finer diamonds removes the skin to a chosen depth, then polishes (cutting
  form above). Exposure classes A cream (85-95 % paste fines), B salt-and-pepper (85-95 % fine aggregate), C full
  aggregate (80-90 %) [31]; gloss levels 1-4 by DOI 0-9 / 10-39 / 40-69 / > 70 and 60 deg gloss < 10 / 5-25 / > 35 /
  > 50 [32]. Aggregate is cut flat (cross-sections), not protruding; colour shifts grey -> brown as paste is removed
  [31].

### 4.20 Surface erosion of vertical faces (brief)
- **Mechanism:** acids in rain and soft water etch cement-rich paste and carbonated surfaces, showing more fine
  aggregate [65]. **Acts on:** F0 -> F1. **Removes:** paste skin. **Reveals:** sand speckle of the same wall, form print
  and board grain softened (est.).
- **Never:** reveals coarse aggregate on a sound wall within decades (est.: F1 is ~5 mm [61]); raises the surface.
- **Where and scale:** exposed, wetted faces; tops and windward corners most (est.: they take the most rain [65]);
  0-1 mm over decades (est.). **Signature:** albedo slightly lighter and warmer (sand colour), roughness up, form print
  amplitude down. **Sources:** [61][65].

## 5. Invariants
Check ids and parameters are in section 9; regions are defined there. `coverage(region=A, within=B)` is the share of B
that A covers: to test "X lies inside Y", put Y in `region` and X in `within`. No check uses a mask derived from the
height it constrains: reveal masks (`agg_exposed`, `rebar_visible`) come from the removal depth `R` and the layout.

1. **Layout footprints are fixed.** Joints, edges and radii, isolation strips, form seams, tie holes, board lines, lift
   joints, wall joints, weep holes, the aggregate particle field and the rebar layout are identical in every variant.
   *Why:* made at construction [6][36][41]. *Enforce:* one layout generator emits every layout mask; no warp, blur or
   damage node writes into them; panel movement (4.5) is a layout parameter shared with `nowear`. *Check:*
   `mask_invariance` per layout mask (`layout_*`), 0 changed.
2. **Removal only lowers.** Wear, scaling, flaking, delamination, pop-outs, spalls, grinding and erosion go down; only
   deposits go up. *Why:* they remove material [2][14][16]. *Enforce:* `H = min(E, ...)` before deposits are added;
   rigid motions are built into `E` and so into `nowear`. *Check:* `envelope` except deposit and patch.
3. **Removal reveals the same slab in a fixed order:** paste -> sand speckle -> coarse aggregate -> steel only at cover.
   *Why:* floating pushes aggregate down [9] under a mortar layer (3-10 mm, est. from [2][18]); bars sit at cover
   [13][60]. *Enforce:* rock colour where `R` exceeds the particle's depth, bar where `R` exceeds cover. *Check:*
   `agg_reveal_depth` (exposed rock >= 2 mm (est.) below the intact surface; skip for exposed-aggregate and polished
   finishes, where aggregate is part of `E`) and `rebar_depth`.
4. **Exposed aggregate is never below the mortar around it, and never above the envelope.** It stands proud after
   scaling, is planed nearly flush after abrasion and is flush after cutting; beyond ~half its size it drops out and
   leaves a socket (4 intro). *Why:* paste is removed faster than rock [16][44]. *Enforce:* `H = max(M, min(A_top, W))`
   with the three forms in section 10; dropped particles in `agg_loss`. *Check:* `agg_not_below` (passes a ground plane
   and buried particles, fails a recessed "aggregate layer"); `agg_protrusion` as a tuning target.
5. **The kerf keeps its width; damage beside it belongs to the slab.** The joint opening is kerf + panel separation
   (4.5); visible widening beyond that is spalling of one or both arrises. *Why:* crack width excludes chipped edges
   [50]; spalls are measured from the joint face [17]. *Enforce:* spall and wear fields are multiplied by `slab` and
   never dilate `joint`. *Check:* `layout_joint`, `joint_width`, `no_damage_in_joint`.
6. **Sealant or filler loss deepens the joint, never widens it** (the brick-mortar recess analogue). *Enforce:* the
   sealant level lives inside `joint` only; extruded sealant (ASR, heat) is a deposit. *Check:* covered by 1, 2 and 5.
7. **Cracks are anchored to causes.** Restraint cracks start or end at edges, joints, re-entrant corners, openings,
   footings or other cracks [6][7][53][71]; plastic shrinkage cracks are parallel and may float [5]; corrosion cracks
   follow bars [18]; D-cracks stay within 0.3-0.6 m of joints [57] and start at corners [17]; early ASR starts at and
   perpendicular to joints and at corners [19]. *Enforce:* seed restraint cracks from layout features and clip them by
   `panel_id`; multiply D-crack masks by a 600 mm joint band. *Check:* `dcrack_band`, `crack_anchor`, `corrosion_dir`.
8. **Crack families keep their scale.** Crazing cells 10-50 mm [3][16]; plastic cracks 0.3-1 m apart [5]; map cells
   100-300 mm (est.); wall restraint cracks 1-2 x wall height apart [71]. *Check:* `craze_cells`, `map_cells`.
9. **Deposits come from water sources and follow water.** Efflorescence, leachate, rust and run-off sit downstream of
   a source (cracks, joints, tie holes, lift joints, weep holes, bars, wall tops): straight down on walls to the next
   ledge or grade, as rims, halos and low-spot fills on floors; backfilled walls may bloom anywhere on the wetted face
   [16][51][73]. *Enforce:* build `downstream` from the source masks in the layout/crack branch (straight down with
   +/- 50 mm lateral spread on walls, est.; dilation plus low spots on floors) and `wetted_face` for backfilled walls,
   independent of the deposit parameters; deposits are drawn only inside them. *Check:* `efflor_source`, `runoff_down`.
10. **Wear follows traffic and contact.** Texture loss, polish and aggregate exposure concentrate in paths and on
    arrises, not in sheltered corners [21][44]. *Check:* `wear_in_paths`, `rough_path`.
11. **Finish features belong to their surface type.** Bug holes, fins, offsets, tie holes and form print only on formed
    faces [25][30]; broom, float and trowel only on flatwork; one broom direction per panel, perpendicular to traffic
    [33]. *Enforce:* separate flatwork and formed generators. *Check:* `broom_dir` (close-up), `fins` at the class limit.
12. **Pop-outs are cones on particles with fractured aggregate at the bottom** [14][16]. *Check:* `popout_size`,
    `popout_depth`.
13. **Steel is visible only on its layout and below cover.** *Check:* `rebar_depth`, `layout_rebar`.
14. **Wet darkens and smooths; water lies low.** *Why:* wetting roughly halves reflectance [45]. *Check:* wet/dry
    albedo ratio, `puddles_low`.
15. **Colour varies per panel and per cause, not as a lattice.** Panels, pours, lifts and boards differ [12]; trowel
    burns are darker [12][16]; soiled < aged < new < efflorescence. *Check:* `panel_cv`, `lowfreq`, `seam`.

## 6. Common procedural mistakes
| Wrong (what procedural materials often do) | Right (physics) | How to fix it in the graph |
|---|---|---|
| Slab with no joints, or a random Voronoi crack web over the whole tile | Slabs are cut into 1.5-4.5 m panels; cracks are few and tied to panels, corners and joints [6][41] | Layout generator first; crack generator seeded by layout features, clipped by `panel_id` |
| "Erosion" dilates the joint mask so joints widen with age | Kerf width is fixed; arrises spall on the slab side [17][50]; opening comes from panel movement only | Never dilate `joint`; spall field multiplied by `slab`; opening as a layout parameter |
| Scaling reveals a flat, darker "under layer" | Scaling exposes sand, then rock-coloured aggregate standing proud [16] | Aggregate particle field with own IDs and colours; `max(M, min(A_top, W))` |
| Ground or polished floor with rounded aggregate standing proud | Cutting makes one plane through paste and rock [31] | Cutting form: `W = M = E - R` |
| Aggregate keeps rising out of the mortar with age | Beyond ~half its size it drops out (est., [16][34]) | Drop the particle, socket in `agg_loss` |
| Coarse aggregate visible on a new trowel or broom finish | Floating buries aggregate under mortar [2][9]; only exposed-aggregate or polished finishes show it new | Aggregate reveal gated by removal depth |
| Bug holes and pores sprinkled on floors | Bug holes are formed-surface air voids [25][30]; flatwork shows sand speckle and craze lines | Separate flatwork and formed generators |
| Pop-outs as dark round holes | Conical pits with pale fractured aggregate at the bottom [14][16][55] | Cone `min` centred on a particle; bottom albedo from that particle |
| Rebar showing in shallow spalls, or wavy random bars | Steel only at cover depth, straight, on a grid [13][60] | Rebar from a layout; reveal where removal >= cover |
| Rust or efflorescence streaks with no source, or running sideways | Deposits start at cracks, joints, tie holes, weep holes, bars and run down walls [16][51] | Derive streaks from `source` with a downward spread |
| Rust only at cracks over bars on a formed wall | Shallow tie ends rust first, on the tie grid (4.12) | Tie-end rust from the tie mask x breakback |
| Crazing drawn as big 100-300 mm cells, or ASR as fine cm-scale cells | Crazing <= 40-50 mm [3][16]; map cracking is far coarser (est.) | Separate generators with scale checks |
| Cracks as wide, deep trenches everywhere | Most service cracks are hairline to a few mm (est.; [17][50]); they read through dirt and moisture | Sub-pixel cracks in albedo/roughness; height only for spalled cracks |
| Spall faces smooth and rounded | Fractured mortar and broken aggregate, sharp breakout edge [16] | Fracture noise plus aggregate cross-section colours inside spalls |
| Perfectly sharp 90 deg slab edges and joint lips | Tooled edges and joints are rounded to ~6 mm [40]; sawcuts are sharp but ravel | Edge profile from layout distance field |
| Scaling spread evenly | Concentrated at low spots, joints, edges, paths and salt zones (est.); patches merge [2] | Weight scaling by ponding, joint distance and path masks |
| Trowel burn as random grey noise | Dark burnished overlapping arcs from late troweling, lower roughness [9][12] | Arc/swirl masks, albedo down, roughness down |
| Broom texture in random directions or running over tooled margins | Broom perpendicular to traffic, one direction per panel [33]; margins smooth (est.) | Directional noise per panel, masked out near edges and joints |
| Albedo copied from physicallybased.info 0.51 linear for all concrete | That value traces to a new-concrete solar albedo [47][48]; field pavements 0.18-0.35 solar [59] | Use section 7 by state |
| Neutral grey concrete | Concrete reflects more red than blue [58] | Slightly warm grey (section 7) |
| Wet concrete shown only as lower roughness | Wetting roughly halves reflectance [45] | Wet preset multiplies albedo by ~0.5 (0.40-0.80) |
| Tie holes scattered, or a 610 mm grid on every wall | The grid comes from the forming system [36][38][67] | Tie layout from the chosen system |
| Perfect fin-free seams on a utility wall | Class C allows 13 mm offsets and fins [66] | Fin and offset height from the surface class |
| Pour lines as ruler-straight lines every 0.5 m | Lift joints are straight and level at 1.2-3 m (est.); layer lines appear only after delays and undulate [7][27] | Separate lift-joint layout from optional layer lines |
| Patches as irregular blobs | Saw-cut rectangles with vertical edges, often joint-aligned, colour offset [16][27] | Rectangle generator snapped to panel axes |

## 7. PBR reference values
**Solar vs visible.** LBNL measured **solar** reflectance (300-2500 nm) [45][59]. A spectral library of urban concretes
gives visible (CIE Y, D65) / solar = 0.82-1.08, median 0.90, with visible Y 0.19-0.38 over 7 samples, and reflectance
at 450 nm only 0.55-0.81 x that at 650 nm: concrete is a warm grey [58]. The visible values below are ~0.9 x solar,
and the warm tint is about linear B = 0.85-0.95 x R (est. from the spectral slope [58]). LBNL's 16 grey-cement lab
mixes (25 weeks, most of them rough castings) span unexposed 0.19-0.52, weathered 0.20-0.44, wet 0.10-0.22, abraded
0.13-0.55, formed 0.25-0.41 solar, with sand colour as strong a driver as cement [45]. Sixteen in-service PCC streets
measured 0.18-0.35, mean 0.26 solar [59].

| Component / state | Albedo (linear luma; sRGB 0-255) | Roughness | Notes | Source |
|---|---|---|---|---|
| Grey concrete, new, dry | 0.30-0.40 (149-170) | trowel 0.45-0.60, float 0.75-0.85, broom 0.80-0.90 (est.) | central band; lab 0.19-0.52 solar by sand colour; grows ~0.08 in the first 6 weeks | [45][58], (est.) |
| Grey concrete, in service / weathered, dry | 0.20-0.30 (124-149) | 0.80-0.92 (est.) | field streets 0.18-0.35 solar [59]; traffic dirt darkens [46] | [45][46][59] |
| Heavily soiled (parking, tyre lanes) | 0.08-0.15 (80-108) | 0.60-0.85 | rubber, oil, soot (est.) | (est.) |
| Wet (weathered grey) | 0.10-0.20 (89-124) | damp 0.40-0.60; film/puddle 0.02-0.10 (est.) | x0.40-0.80 of dry, typically ~0.5 | [45] |
| White-cement concrete, new | 0.55-0.75 (196-225) | per finish | best white mixes up to 0.77 solar | [45] |
| Slag-cement concrete | grey value +0.02-0.05 (est.) | per finish | lighter than plain portland [12] | [12], (est.) |
| Exposed coarse aggregate (cut or abraded faces) | 0.13-0.55 (101-196), by rock | natural faces 0.60-0.80; traffic-polished tops 0.40-0.60 (est.) | rocks 0.17-0.55 (basalt dark, plagioclase/chert pale); abraded concrete 0.13-0.55 | [45] |
| Fresh fracture (spall, pop-out, scaling scar) | aged value +0.03-0.08 (est.) | 0.85-0.95 (est.) | clean of the dirt film | (est.) |
| Efflorescence / calcite crust | 0.50-0.80 (188-231) (est.) | 0.90-1.00 (est.) | white CaCO3 and salts; can whiten grey mixes [45] | [16][45] |
| Rust stain on concrete | ~sRGB (140-170, 80-100, 45-60) (est.) | substrate | orange-brown | (est.) |
| Rusted rebar or tie end | ~sRGB (90-130, 50-70, 30-45) (est.) | 0.70-0.90 | metallic 0 (oxide); bare steel only if freshly abraded | (est.) |
| Biofilm (algae) / black crust | green-grey sRGB (60-100, 70-110, 50-70); black 40-60 (est.) | 0.60-0.80 (est.) | | (est.) |
| Moss | sRGB (70-110, 90-130, 30-60) (est.) | 0.90 (est.) | in joints, shaded bases | (est.) |
| Lichen | grey-green sRGB (130-170, 140-170, 110-140); orange (190-230, 110-150, 30-60) (est.) | 0.80-0.95 (est.) | sunny tops and ledges | (est.) |
| Fresh oil stain | parent x 0.3-0.6 (est.) | 0.30-0.50 (est.) | rinsed lab oil soiling barely changed grey mixes [45] | [45], (est.) |
| Joint sealant / asphalt-fibre filler | 0.03-0.08 (48-80) (est.) | 0.50-0.90 (est.) | dark | (est.) |
| Formed face, new | as new grey; lab formed 0.25-0.41 solar | HDO overlay 0.45-0.60, plywood 0.65-0.80, boards 0.80-0.90 (est.) | HDO is specified for smooth architectural faces [38] | [38][45], (est.) |
| Polished concrete L1 / L2 / L3 / L4 | parent paste and aggregate | 0.60-0.75 / 0.40-0.55 / 0.20-0.35 / 0.05-0.15 (est.) | DOI 0-9 / 10-39 / 40-69 / > 70, 60 deg gloss < 10 / 5-25 / > 35 / > 50 | [32], (est.) |
| physicallybased.info "Concrete" | 0.51 (189) | 0.5 | traced to a "new concrete 0.55" solar albedo; upper bound for very new light concrete only | [47][48] |
| CIE R1 road surface | Q0 0.10 -> ~0.31 if Lambertian (est.) | | photometric class for concrete or brightened asphalt, mostly diffuse | [49] |

Metallic is 0 everywhere except freshly abraded steel.

## 8. Variants and presets
| Variant (ages est.; D-cracking and ASR show at 10-15 yr [15][20]) | Includes (stage) |
|---|---|
| **New** (0-1 yr) | as-built finish, per-panel shade, trowel burn (interior), saw raveling at some joints, optional crazing and plastic cracks, crisp tooled edges, early efflorescence possible; rating 0; pop-outs 0-1 per m2 in freeze climates (est.); walls: bug holes, fins/offsets by class, layer lines if delayed, no growth |
| **In service** (2-10 yr) | soiling, texture softened in paths (wear stage 1), arris chipping (spall L, < 75 mm [17]), a few restraint cracks at re-entrant corners or long panels, partial sealant loss, rating 0-1, a few pop-outs, moss in shaded joints; walls: tie-end rust spots, first run-off streaks, efflorescence at cracks and lift joints |
| **Weathered** (10-25 yr) | wear stage 2 (sand speckle) in paths, scaling 2-3 near joints and low spots, joint spalls L-M, cracks M with efflorescence fringes, D-cracking low (if susceptible aggregate), 1 patch per few panels (est.), oil/tyre marks where driven; walls: run-off streaks, biofilm under ledges, lichen on tops, efflorescence at cracks, lift joints and weep holes, surface erosion begins, rust where cover is thin |
| **Distressed** (25+ yr, freeze-thaw with deicers) | scaling 4-5 with sockets, joint spalls M-H, one dominant failure (D-cracking M-H, ASR map cracking, or corrosion spalls with exposed bars if reinforced), patch mosaic, curl/faulting steps or root heave, heavy soiling |

Interview questions (recommended default in brackets):
1. Flatwork or formed wall? [flatwork, sidewalk]
2. Use and traffic: pedestrian walk, driveway, interior floor, parking, roadway? [pedestrian: no oil or tyre marks]
3. Finish: broom, steel trowel, float, exposed aggregate, stamped, polished class/level; formed: HDO plywood, plain
   plywood, board-formed, steel? [broom exterior; trowel interior; plywood for walls]
4. Joints: tooled 1.524 m sidewalk grid or sawcut panels (size)? Any panel movement (roots, heave)? [tooled 5 ft; floors
   sawcut 3 m; none]
5. Aggregate: crushed stone or rounded river gravel; rock and sand colours? [crushed grey limestone, grey sand]
6. Cement colour: grey, white, slag-light? [grey]
7. Climate: freeze-thaw with deicers or none (removes scaling, D-cracking, pop-outs)? [moderate freeze-thaw]
8. Reinforcement: none, mesh, rebar (cover)? [none for walks; rebar at 50 mm for walls]
9. Walls: retaining (wetted from behind, weep holes) or free-standing? Height and lift height? Forming system (US
   modular, framed metric, job-built, board-formed) and tie type? Surface class A-D? Wall joints, cap or coping?
   [free-standing, 2.4 m, US modular snap ties, Class C]
10. Exposure: orientation and shade, run-off from above, splash zone, road salt? [moderate, north-facing base damp]
11. Variant / age? [weathered]
12. Wet state: dry, damp, wet with puddles? [dry]
13. Tile purpose: slab-scale or close-up? [slab-scale 3.048 m; close-up 0.5 m as a detail map]
14. Dominant failure for distressed: D-cracking, ASR, corrosion or none? [none]

## 9. Acceptance targets
Scale: sidewalk `{"tile_m": 3.048, "resolution": 2048, "normal_format": "directx"}` (floor 3.0, wall 2.4384 or 2.70,
close-up 0.5). `height_depth_mm`: 25 for new/in-service flatwork (joints modelled 8-12 mm deep), 50 for
weathered/distressed flatwork (spalls 10-40 mm, pop-outs to 50 mm [17]), 80 with corrosion spalls (cover 38-50 mm plus
the bar), 40 for walls (25 mm tie cones). Keep the deepest feature above 0 so `height_usage` does not count it as
clipped.

Masks to export. Layout (identical in `nowear`): joint (kerf/groove plus opening), edge, panel_id, particles (coarse
aggregate footprints), path, rebar_layout, downstream, wetted_face; walls: seam, tie, lift, wall_joint, weep. Process:
scaled, wear, spall, popout, agg_exposed, agg_loss, patch, crack_restraint, craze, dcrack, asr, rebar_visible, efflor,
runoff, crack_corrosion, deposit (union of all deposits), puddle; walls: bughole. Omit a mask from a region list when the variant does
not export it (e.g. `edge` in a tile with no free slab edge).

Flatwork, weathered sidewalk (targets for other variants in the table below):
```json
{
"regions": {
  "joint": {"mask": "joint", "threshold": 0.5}, "slab": {"mask": "joint", "threshold": 0.5, "invert": true},
  "removed": {"or": ["scaled", "wear", "spall", "popout", "agg_loss", "patch"]}, "removed_d": {"or": ["removed"], "dilate_mm": 20},
  "slab_intact": {"and": ["slab"], "not": ["removed_d", "deposit"]}, "removal": {"or": ["scaled", "wear"]},
  "particles_d": {"mask": "particles", "threshold": 0.5, "dilate_mm": 1},
  "agg_in_removal": {"mask": "particles", "threshold": 0.5, "and": ["removal"], "not": "agg_loss", "erode_mm": 1},
  "mortar_removal": {"and": ["removal"], "not": ["particles_d", "agg_loss"]},
  "joint_band": {"mask": "joint", "threshold": 0.5, "dilate_mm": 600}, "anchor_net": {"or": ["crack_restraint", "joint"]},
  "craze_cells": {"and": ["slab"], "not": "craze"}, "allowed_wet": {"or": ["downstream"]},
  "path_slab": {"and": ["slab_intact", "path"]}, "verge_slab": {"and": ["slab_intact"], "not": "path"},
  "puddle_d": {"mask": "puddle", "threshold": 0.5, "dilate_mm": 300}, "puddle_ring": {"and": ["puddle_d"], "not": "puddle"}
},
"checks": [
  {"id": "layout_joint", "type": "mask_invariance", "mask": "joint", "against": "nowear", "max_changed_frac": 0, "severity": "hard", "why": "I1"},
  {"id": "layout_particles", "type": "mask_invariance", "mask": "particles", "against": "nowear", "max_changed_frac": 0, "severity": "hard", "why": "I1, I4"},
  {"id": "envelope", "type": "envelope", "against": "nowear", "except": ["deposit", "patch"], "except_dilate_mm": 2, "tolerance_mm": 0.05, "max_violation_frac": 0, "severity": "hard", "why": "I2"},
  {"id": "joint_width", "type": "run_length", "region": "joint", "axis": "both", "max_mm": 50, "stat": "median", "target_mm": [3, 6], "severity": "hard", "why": "I5"},
  {"id": "panel_size", "type": "run_length", "region": "slab", "axis": "both", "min_mm": 500, "stat": "median", "target_mm": [1515, 1522], "severity": "hard", "why": "1, 2"},
  {"id": "no_damage_in_joint", "type": "coverage", "region": "removed", "within": "joint", "max_frac": 0.001, "severity": "hard", "why": "I5"},
  {"id": "agg_reveal_depth", "type": "order", "upper": "agg_exposed", "lower": "slab_intact", "direction": "below", "lower_stat": "p50", "neighborhood_mm": 300, "margin_mm": 2.0, "tolerance_mm": 0.2, "max_violation_frac": 0.02, "min_px": 500, "severity": "hard", "why": "I3"},
  {"id": "agg_not_below", "type": "order", "upper": "agg_in_removal", "lower": "mortar_removal", "lower_stat": "p10", "neighborhood_mm": 10, "margin_mm": 0, "tolerance_mm": 0.3, "max_violation_frac": 0.05, "min_px": 500, "severity": "hard", "why": "I4"},
  {"id": "agg_protrusion", "type": "height_diff", "a": "agg_in_removal", "b": "mortar_removal", "stat_a": "p90", "stat_b": "p50", "local_mm": 50, "target_mm": [0.5, 8], "min_px": 500, "why": "I4, 4.6"},
  {"id": "dcrack_band", "type": "coverage", "region": "joint_band", "within": "dcrack", "target": [0.95, null], "min_px": 200, "severity": "hard", "why": "I7"},
  {"id": "crack_anchor", "type": "components", "region": "anchor_net", "metric": "count", "connectivity": 8, "target": [null, 1], "why": "I7"},
  {"id": "efflor_source", "type": "coverage", "region": "allowed_wet", "within": "efflor", "target": [0.95, null], "min_px": 200, "severity": "hard", "why": "I9"},
  {"id": "rebar_depth", "type": "order", "upper": "rebar_visible", "lower": "slab_intact", "direction": "below", "lower_stat": "p50", "neighborhood_mm": 500, "margin_mm": 35, "tolerance_mm": 0.5, "max_violation_frac": 0.02, "min_px": 100, "severity": "hard", "why": "I13"},
  {"id": "wear_in_paths", "type": "concentration", "region": "wear", "driver": "path", "within": "slab", "target": [2, null], "why": "I10"},
  {"id": "rough_path", "type": "value_order", "map": "roughness", "regions": ["path_slab", "verge_slab"], "stat": "median", "order": "ascending", "why": "I10"},
  {"id": "scaled_cov", "type": "coverage", "region": "scaled", "within": "slab", "target": [0.01, 0.10], "why": "4.6"},
  {"id": "popout_size", "type": "components", "region": "popout", "metric": "eq_diameter_mm", "stat": "median", "target_mm": [15, 50], "why": "I12"},
  {"id": "popout_depth", "type": "height_diff", "a": "popout", "b": "slab_intact", "stat_a": "p10", "stat_b": "p50", "local_mm": 150, "target_mm": [-30, -5], "min_px": 50, "why": "I12"},
  {"id": "craze_cells", "type": "components", "region": "craze_cells", "metric": "eq_diameter_mm", "stat": "median", "connectivity": 4, "target_mm": [15, 40], "why": "I8"},
  {"id": "albedo", "type": "value_range", "map": "basecolor", "region": "slab_intact", "space": "linear", "stat": "median", "target": [0.20, 0.30], "why": "7"},
  {"id": "rough_finish", "type": "value_range", "map": "roughness", "region": "slab_intact", "stat": "median", "target": [0.80, 0.92], "why": "7"},
  {"id": "panel_cv", "type": "per_element", "elements": {"from": "id_map", "map": "panel_id"}, "metric": "luma_median", "region": "slab_intact", "stat": "cv", "target": [0.02, 0.08], "why": "I15"},
  {"id": "lowfreq", "type": "lowfreq", "map": "basecolor", "region": "slab_intact", "sigma_mm": [250, 500], "target": [null, 0.05], "why": "I15"},
  {"id": "puddles_low", "type": "order", "upper": "puddle_ring", "lower": "puddle", "lower_stat": "p95", "neighborhood_mm": 500, "max_violation_frac": 0.05, "min_px": 200, "why": "I14 (wet preset)"},
  {"id": "seam", "type": "seam", "maps": ["basecolor", "height", "normal", "roughness"], "target": [null, 3], "severity": "hard"},
  {"id": "normals", "type": "normal_valid", "normal_format": "directx", "severity": "hard"},
  {"id": "height_clip", "type": "height_usage", "metric": "clipped_frac", "target": [null, 0.001], "severity": "hard"}
]
}
```
Notes. `panel_size` is the slab run between joints (pitch - joint width): walk 1515-1522 mm, sawcut floor 2990-2998 mm
(one panel per tile), minus any joint opening; `spacing` cannot measure a period of half the tile or more. With free
slab edges in the tile, add `edge` to `anchor_net` and set the `crack_anchor` target to the component count of joints
OR edges in `nowear`. `rebar_depth` margin = cover - 3 mm. Drop checks whose process the variant lacks. On a synthetic
tile built per section 10, the correct build passed every hard check (`agg_not_below` 0.029); one with a recessed
aggregate layer, spalls eating the joint and curl only in the preset failed `agg_not_below` (0.36),
`agg_reveal_depth`, `no_damage_in_joint`, `layout_joint` and `envelope`. Optional, same pattern:
`{"id": "layout_rebar", "type": "mask_invariance", "mask": "rebar_layout", "against": "nowear", "max_changed_frac": 0}`;
`{"id": "corrosion_dir", "type": "orientation", "region": "crack_corrosion", "axis_deg": 0, "tolerance_deg": 15,
"target": [0.7, null]}` (axis = outer bar direction); `{"id": "map_cells", "type": "components", "region":
"map_cells", "metric": "eq_diameter_mm", "stat": "median", "connectivity": 4, "target_mm": [100, 300]}` with
`"map_cells": {"and": ["slab"], "not": "asr"}` (est.).

| id | new | in service | weathered | distressed | from |
|---|---|---|---|---|---|
| joint_width (mm, + opening) | tooled 3-6, sawcut 3-5 | same | same | same | 2, I5 |
| scaled_cov | 0 | <= 0.01 | 0.01-0.10 | 0.10-0.50 | 4.6 |
| agg_protrusion (mm) | n/a | n/a | scaling 0.5-8; abrasion 0.3-2.5 | same; ground floors -0.3-0.3 | 4 intro |
| spall width: `run_length` spall across the joint, p95 (mm) | <= 5 (saw raveling) | <= 75 | <= 150 | <= 300 | 4.9 |
| popout_size / `count_per_m2` | 0-1 per m2 | 15-50 mm / 0-2 | 15-50 / 0-4 | 15-50 / 0-6 (est.) | 4.8 |
| albedo (linear, clean slab) | 0.30-0.40 | 0.22-0.32 | 0.20-0.30 | 0.12-0.25 (est.) | 7 |
| wet / dry albedo ratio (wet preset) | 0.40-0.80 | same | same | same | 4.18 |
| height_depth_mm | 25 | 25 | 50 | 50 (80 with corrosion) | 9 |

Close-up tile (0.5 m), flatwork: `{"id": "broom_dir", "type": "orientation", "map": "height", "region": "slab_intact",
"axis_deg": 0, "tolerance_deg": 10, "target": [0.7, null], "severity": "hard"}` (axis = traffic + 90 deg);
`{"id": "broom_relief", "type": "height_diff", "a": "slab_intact", "b": "slab_intact", "stat_a": "p95", "stat_b": "p05",
"local_mm": 20, "target_mm": [1.2, 3.5]}` (est.: peak-to-valley of 1.5-3 mm striations);
`{"id": "broom_pitch", "type": "spacing", "map": "height", "axis": "y", "min_mm": 1, "max_mm": 8, "target_mm": [1, 6]}`
(est.).

Formed wall additions (replace the flatwork joint, particle-reveal and path checks):
```json
{
"regions": {
  "face": {"not": ["seam", "tie", "lift", "wall_joint", "weep"]},
  "face_clean": {"and": ["face"], "not": ["deposit", "bughole"]},
  "allowed_wet": {"or": ["downstream", "wetted_face"]}
},
"checks": [
  {"id": "layout_seam", "type": "mask_invariance", "mask": "seam", "against": "nowear", "max_changed_frac": 0, "severity": "hard", "why": "I1"},
  {"id": "layout_tie", "type": "mask_invariance", "mask": "tie", "against": "nowear", "max_changed_frac": 0, "severity": "hard", "why": "I1"},
  {"id": "tie_pitch", "type": "spacing", "region": "tie", "axis": "x", "target_mm": [605, 615], "severity": "hard", "why": "1: US modular; use the chosen system's pitch"},
  {"id": "tie_size", "type": "components", "region": "tie", "metric": "eq_diameter_mm", "stat": "median", "target_mm": [19, 27], "why": "2"},
  {"id": "lift_level", "type": "orientation", "region": "lift", "axis_deg": 0, "tolerance_deg": 2, "target": [0.95, null], "why": "4.17"},
  {"id": "bughole_cov", "type": "coverage", "region": "bughole", "within": "face", "target": [0.001, 0.02], "why": "4.17"},
  {"id": "bughole_size", "type": "components", "region": "bughole", "metric": "eq_diameter_mm", "stat": "p95", "target_mm": [null, 15], "why": "4.17"},
  {"id": "fins", "type": "ridge", "between": ["seam", "face"], "band_mm": 10, "threshold_mm": 13, "max_frac": 0.05, "why": "I11: threshold = class limit 3/6/13/25 mm"},
  {"id": "efflor_source", "type": "coverage", "region": "allowed_wet", "within": "efflor", "target": [0.95, null], "min_px": 200, "severity": "hard", "why": "I9"},
  {"id": "runoff_down", "type": "orientation", "region": "runoff", "axis_deg": 90, "tolerance_deg": 15, "target": [0.6, null], "why": "I9"},
  {"id": "albedo", "type": "value_range", "map": "basecolor", "region": "face_clean", "space": "linear", "stat": "median", "target": [0.20, 0.32], "why": "7"}
]
}
```
Keep `envelope`, `rebar_depth` (lower = `face_clean`), `seam`, `normals` and `height_clip` from the flatwork block;
add `mask_invariance` for `lift`, `wall_joint` and `weep` when exported. `tie_pitch` needs at least two tie columns in
the tile (2.4384 m US tile: four).

## 10. Substance Designer build notes
Material-specific only; general craft lives in `references/sd_craft.md`.
- **Layout generator.** Flatwork: Tile Generator (current `pattern_tile_generator`) with square tiles, X/Y = panels per
  tile (2 x 2 at 3.048 m), no offset or jitter; its gap gives `joint` at an exact px width (3-6 mm = 2-4 px) plus any
  opening (4.5). Tooled shoulders and edge radii come from a distance field of the panel mask (~4 px radius at
  1.49 mm/px). Sawcut floors: one panel with the kerf split across the tile border. Walls: panel seams from the chosen
  forming system; tie holes by Tile Sampler on the system's grid; lift joints and rustications as straight horizontal
  bands; optional layer lines as undulating bands from a 1-D noise; boards as a 1 x n stripe tile with per-board IDs.
- **Per-unit IDs and randoms.** Flood Fill on the panel mask, then Flood Fill to Random Grayscale for `panel_id`
  (per-panel shade, a few degrees of broom-direction jitter) and Flood Fill to Gradient for curl tilt. Aggregate
  particles get their own IDs from Tile Sampler or Shape Splatter (rounded blobs for river gravel, angular polygons
  for crushed stone), 4.75-25 mm, each with a top height `A_top` (3-10 mm below `E`, est.), a size `D` and a colour
  from an aggregate palette, never a generic "damage colour". At a cut plane coarse aggregate covers ~40-50 % of the
  area (est.: 60-75 % aggregate by volume, ~60 % of it coarse [43]). The particle field is a layout output.
- **Height composition order** (16-bit throughout):
  1. `E` = finish texture (broom, trowel, form print) combined with layout geometry: `min` for grooves, radii, tie
     cones and saw raveling, `max` for fins and offsets inside `seam`; then rigid motions (curl tilt, faulting, heave
     per panel). Export `E` as the `nowear` height.
  2. As-built defects: bug holes `subtract` (formed faces only).
  3. Removal depth `R` = max(scaling, flaking, wear, erosion) >= 0; mortar level `M = E - R`.
  4. Aggregate reveal, one form per zone (4 intro): `H = max(M, min(A_top, W))`, with
     scaling/flaking/erosion `W = E`; abrasion `W = E - R` and `M = W - p`, p 0.5-2 mm (est.); cutting `W = M = E - R`.
     Where `A_top - M > 0.5 D` (est.), drop the particle: `H = min(M, particle underside)`, write `agg_loss`.
     `agg_exposed` = particles where `A_top > M` (or cut by the plane), from `R` and the particle field.
  5. Discrete removals by `min`: pop-out cones (walls 45-60 deg) on particle centres, spalls (times `slab`),
     delamination flakes (`E` - 3 to 6 mm).
  6. Joint interior: inside `joint`, `H` = sealant level (lowered where sealant is lost) or the kerf floor 8-12 mm
     below `E`; nothing else writes there. Darken the slot in albedo and AO.
  7. Steel: bar profile `H = max(H, E - cover - r + sqrt(r^2 - d^2))` for distance `d < r` from the bar axis (r = bar
     radius 5-16 mm), inside spalls whose floor reaches the bar plane; `rebar_visible` where the bar shows.
  8. Deposits by `add` with their masks (efflorescence crust, moss, lichen, rubber, extruded sealant).
- **Masks from the layout only:** joint, edge, isolation strip, panel_id, particles, seam, tie, board lines, lift,
  wall_joint, weep, rebar layout, traffic paths (from the use case), and `downstream` / `wetted_face` from the source
  masks. Damage masks may read them; nothing writes them.
- **Known pitfalls.**
  - A blur or warp after the layout moves joints: warp the noise inputs, never layout masks. Soften damage edges with a
    normalized blur, `blur(D * mask) / blur(mask)`, then apply the hard mask (a fin-free method from the brick build).
  - 8-bit height turns 1.5-3 mm broom relief into a few steps once `height_depth_mm` is 25 or more; use 16-bit.
  - Hairline and craze cracks are sub-pixel at slab scale: draw them in albedo, roughness and AO at 1-2 px; keep height
    cracks >= 2 px wide.
  - Sand speckle at 0.24 mm/px needs very fine noise; high-scale FX-map noises have stalled Designer's GL engine on this
    setup, so build it from Fractal Sum Base min/max levels.
  - Broom: directional noise per panel aligned across traffic, masked out of the smooth margins along edges and joints
    (est.); real striation geometry only in the close-up tile, a normal/roughness hint at slab scale.

## 11. Reference imagery
Search terms and what to measure (prefer raking light and a coin, ruler or crack-width card in shot):
- "concrete scaling deicer sidewalk", "concrete popout chert", "joint spall concrete pavement": patch rims and
  terraces, aggregate standing proud, cone walls over a pale fractured particle, spall width against the unchanged kerf.
- "D-cracking concrete pavement joint", "alkali silica reaction pavement map cracking": crescent cracks and dark bands
  along joints, brownish crack borders, perimeter-first pattern.
- "concrete crazing drying after rain", "plastic shrinkage cracks slab", "trowel burn concrete floor", "broom finish
  concrete close up", "sidewalk heaved by tree roots": cell size, parallel cracks, burnished arcs, striation pitch,
  smooth margins, joint opening and faulting.
- "snap tie holes architectural concrete", "bug holes formed concrete wall", "board formed concrete detail", "concrete
  wall lift joint grout leak", "retaining wall efflorescence weep hole", "concrete wall rust stain form tie", "lichen
  concrete wall top": tie grid vs seams, bug holes, fins and offsets, sandy bands under lift joints, streak sources.
- "calthemite", "rebar corrosion spall rust staining", "wet concrete sidewalk drying", "polished concrete class A B
  C": straws, bars at cover, joints dark longest, paste -> sand -> aggregate sequence.

## Sources
1. NRMCA. *CIP 1 Dusting Concrete Surfaces*. https://www.nrmca.org/wp-content/uploads/2021/01/01pr.pdf. Dusting, weak top 6 mm.
2. NRMCA. *CIP 2 Scaling Concrete Surfaces*. https://www.nrmca.org/wp-content/uploads/2021/01/02pr.pdf. Scaling stages, 3-10 mm mortar loss, air content.
3. NRMCA. *CIP 3 Crazing Concrete Surfaces*. https://www.nrmca.org/wp-content/uploads/2021/01/03pr.pdf. Cell size, depth, visibility.
4. NRMCA. *CIP 4 Cracking Concrete Surfaces* (2014). https://www.nrmca.org/wp-content/uploads/2021/01/04pr.pdf. Crack types, D-crack origin, joint depth, cover.
5. NRMCA. *CIP 5 Plastic Shrinkage Cracking* (2014). https://www.nrmca.org/wp-content/uploads/2021/01/05pr.pdf. Spacing, pattern, conditions.
6. NRMCA. *CIP 6 Joints in Concrete Slabs on Grade* (2014). https://www.nrmca.org/wp-content/uploads/2021/01/06pr.pdf. Joint types, spacing, depth, timing, saw raveling.
7. NRMCA. *CIP 7 Cracks in Residential Basement Walls*. https://www.nrmca.org/wp-content/uploads/2021/01/07pr.pdf. Wall cracks, pour lines, form lines.
8. NRMCA. *CIP 11 Curing In-Place Concrete*. https://www.nrmca.org/wp-content/uploads/2021/01/11pr.pdf. Sheet-wrinkle mottling.
9. NRMCA. *CIP 14 Finishing Concrete Flatwork* (2017). https://www.nrmca.org/wp-content/uploads/2021/01/14pr.pdf. Finishing sequence, trowel burns, broom, edging.
10. NRMCA. *CIP 19 Curling of Concrete Slabs* (2018). https://www.nrmca.org/wp-content/uploads/2021/01/19pr.pdf. Curling causes, 24 x thickness.
11. NRMCA. *CIP 20 Delamination of Troweled Concrete Surfaces*. https://www.nrmca.org/wp-content/uploads/2021/01/20pr.pdf. 3-6 mm delaminations.
12. NRMCA. *CIP 23 Discoloration* (2019). https://www.nrmca.org/wp-content/uploads/2021/01/23pr.pdf. Colour causes, trowel burn, SCMs, forms.
13. NRMCA. *CIP 25 Corrosion of Steel in Concrete*. https://www.nrmca.org/wp-content/uploads/2021/01/25pr.pdf. Rust volume, pH, cover.
14. NRMCA. *CIP 40 Aggregate Popouts*. https://www.nrmca.org/wp-content/uploads/2021/01/40pr.pdf. Pop-out and popoff anatomy.
15. NRMCA. *CIP 43 Alkali Aggregate Reactions*. https://www.nrmca.org/wp-content/uploads/2021/01/43pr.pdf. ASR conditions and timing.
16. PCA. *Concrete Slab Surface Defects: Causes, Prevention, Repair*, IS177 (2001). https://www.concreteisbetter.com/wp-content/uploads/2013/06/Slab-Surface-Prevention-Repair-a.pdf. Defect sizes, colour, spalls, patches, ACI 116R scaling classes.
17. FHWA. *LTPP Distress Identification Manual*, FHWA-HRT-13-092, JPCC chapter. https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/ltpp/13092/002.cfm. Severity bands.
18. FHWA. *Petrographic Methods of Examining Hardened Concrete*, FHWA-HRT-04-150 (2006), ch. 4, 6, 7. https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/pccp/04150/chapt4.cfm. Scaling classes, voids, paste volume, typical cover.
19. Thomas et al. / FHWA. *ASR Field Identification Handbook*, FHWA-HIF-12-022 (2011). https://www.fhwa.dot.gov/pavement/concrete/asr/pubs/hif12022.pdf. ASR patterns, staining, joints.
20. FHWA. *Guidelines for Detection, Analysis and Treatment of Materials-Related Distress*, FHWA-RD-01-163, vol. 1. https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/pccp/01163/01.cfm. D-cracking, ASR, paste freeze-thaw timing.
21. FHWA. *Concrete Pavement Texturing*, Tech Brief FHWA-HIF-17-011 (2019). https://www.fhwa.dot.gov/pavement/pubs/hif17011.pdf. Drag, broom, tining, grinding dimensions, texture wear.
22. FHWA. *Technical Advisory T 5040.36 Surface Texture for Asphalt and Concrete Pavements* (2005). https://www.fhwa.dot.gov/pavement/t504036.cfm. Tining and drag dimensions.
23. National CP Tech Center (Iowa State). *Deicer Scaling Resistance of Concrete Mixtures Containing Slag Cement, Phase 2* (2012). https://rosap.ntl.bts.gov/view/dot/26320/dot_26320_DS1.pdf. ASTM C672 rating table (C672 withdrawn 2021) and the report's suggested mass-loss equivalents.
24. ACI Committee 201. *ACI 201.1R-08 Guide for Conducting a Visual Inspection of Concrete in Service* (preview). https://www.concrete.org/Portals/0/Files/PDF/Previews/201.1R-08_preview.pdf. Crack-pattern definitions, ASR crack width.
25. ACI. *ACI CT-13 Concrete Terminology*. https://files.engineering.com/files/1bcbf14e-69d9-463b-929a-f33fedab3f2d/ACI_Concrete_Terminology.pdf. Bug holes, honeycomb, laitance, fin, cold-joint lines, lift, lift joint, grade strip, sand streak, popout.
26. ACI Committee 347. *ACI 347.3R-13 Guide to Formed Concrete Surfaces* (preview). https://www.concrete.org/Portals/0/Files/PDF/Previews/347.3R-13_PREVIEW.pdf. CSC1-4, surface void ratio.
27. ACI Committee 309. *ACI 309.2R Visible Surface Effects of Consolidation* (-15 preview for the list; definitions from the -98 edition). https://www.concrete.org/Portals/0/Files/PDF/Previews/309_2R_15_preview.pdf. Form streaking, sand streaking, layer lines, form offsets, repairs.
28. ACI. *FAQ: cover for concrete cast against ground*. https://www.concrete.org/frequentlyaskedquestions.aspx?faqid=903. 76 mm cover, faces cast against earth only.
29. ACI. *FAQ: acceptable cracking*. https://www.concrete.org/frequentlyaskedquestions.aspx?faqid=906. Cracking and curling expected.
30. ASCC. *Position Statement #8 Bugholes in Formed Concrete*. https://cecoconcrete.com/content/Resources/ASCC%20Position%20Statements/ASCC%20PS%238%20Bugholes%20in%20formed%20concrete%20CI.ACI.pdf. Bug-hole size, repair saw cut.
31. ASCC Concrete Polishing Council. *Aggregate Exposure Chart* (2024). https://ascconline.org/Portals/ASCC/CPC_Aggregate_Exposure_Chart_02-06-24_WebSC.pdf. Exposure classes, colour shift.
32. ASCC Concrete Polishing Council. *Appearance Chart*. https://ascconline.org/Portals/ASCC/CPC-Appearance-Chart-10_2_25%20(Corrected).pdf. DOI, gloss, haze by level.
33. The Construction Specifier. *Specifying broomed exterior concrete surfaces* (2015). https://www.constructionspecifier.com/specifying-broomed-exterior-concrete-surfaces/2/. Broom depth per ACI 330.1 and MasterSpec, direction.
34. Solomon Colors. *Guide spec 03 35 23 Exposed Aggregate Concrete Finishing*. https://www.solomoncolors.com/tech-docs/pdf/Archtectural/03-35-23-Exposed-Aggregate-v1.pdf. Etch depth vs chip size (manufacturer data).
35. MASCO. *Concrete Forming & Accessories catalog*, snap ties. https://masons-supply.masco.net/catalogs/formingaccessories/86/. Cone size, breakback.
36. Dayton Superior / Symons. *Steel-Ply Quick Install Guide* (2023). https://www.daytonsuperior.com/docs/default-source/application-guides/steel-ply-quick-install-guide.pdf?sfvrsn=a2769560_3. Tie placement and rows, flat-tie breakback.
37. Symons by Dayton Superior. *Steel-Ply Forming System brochure*. https://www.edconline.com/assets/brochures/symons-forming-steel-ply-brochure.pdf. Panel and filler sizes.
38. Lee County (FL) Utilities. *Section 03100 Concrete Formwork*. https://www.leegov.com/utilities/Documents/New%20Development/Technical%20Specifications/L-03100%20-%20CONCRETE%20FORMWORK.pdf. Tie holes, HDO, chamfers, tolerance.
39. Mile High Flood District. *Section 03 35 00 Concrete Finishing* (2015). https://www.mhfd.org/files/ffedcaff1/03_35_00_Concrete_Finishing.pdf. Bug-hole area, fins, broom texture, patch edges.
40. City of Salina (KS). *Section 103 Concrete Sidewalks* (2015). https://www.salina-ks.gov/media/Construction%20Documents/Standard%20Specifications/Division%20100%20-%20General/103-Concrete-Sidewalks%2011-04-2015.pdf. Thickness, edge radius, joint rules, 1/2 in expansion filler.
41. Oregon DOT. *Standard Drawing RD720 Curb Line Sidewalks* (2025). https://www.oregon.gov/ODOT/Engineering/202601/RD720.pdf. 5 ft tooled joints, 15/45 ft joints.
42. Pavement Interactive. *Joint sawing (PCC)*. https://pavementinteractive.org/?p=10402. Joint depth T/4-T/3.
43. Caltrans. *Concrete Technology Manual*, ch. 3 (2013). https://dot.ca.gov/-/media/dot-media/programs/engineering/documents/structureconstruction/ctm/sc-ctm-chpt3-a11y.pdf. Volume fractions, aggregate types and shape.
44. Cotter & Muench / WSDOT. *Studded Tire Wear on PCC Pavement*, WA-RD 744.3 (2010). https://depts.washington.edu/trac/bulkdisk/pdf/744.3.pdf. Studded-tyre wear rates, raised aggregate.
45. Levinson & Akbari / LBNL. *Effects of composition and exposure on the solar reflectance of portland cement concrete*, LBNL-48334, Cem. Concr. Res. 32 (2002). https://digital.library.unt.edu/ark:/67531/metadc737346/m2/1/high_res_d/820773.pdf. Measured lab solar reflectance by state (Figure 5, all 16 grey-cement mixes).
46. US EPA. *Reducing Urban Heat Islands: Cool Pavements* (compendium chapter, draft). https://19january2017snapshot.epa.gov/sites/production/files/2014-06/documents/coolpavescompendium.pdf. Reflectance range, darkening with traffic.
47. physicallybased.info. *Materials API, Concrete*. https://api.physicallybased.info/materials. Dataset value and its references.
48. Lagarde, S. *Feeding a physical based lighting mode* (2011, blog). https://seblagarde.wordpress.com/2011/08/17/feeding-a-physical-based-lighting-mode/. Provenance of the 0.55 value only.
49. AGi32 documentation. *R-Tables for Roadway Lighting* (CIE classes). https://docs.agi32.com/AGi32/Content/references/R-Tables%20for%20Roadway%20Lighting.htm. R1 Q0 = 0.10.
50. Mancs, L. *Evaluation and Epoxy-Injection Repair of Cracks in Concrete*, ASPIRE (Winter 2018). https://www.aspirebridge.com/magazine/2018Winter/SafetyAndServiceability.pdf. ACI 224R Table 4.1 crack widths; width excludes chipped edges.
51. Smith, G. K. *Calthemite deposits form stalactite straws beneath concrete structures*, Cave and Karst Science 43(1) (2016), reprint. https://literature.wolkersdorfer.info/literature/Calthemite%20Deposits%20Form%20Stalactite%20Straws%20Beneath%20Concrete%20Structures.pdf. Leachate deposits, colour, growth.
52. Piotrowska et al. *Abiotic determinants of the historical buildings biodeterioration...*, PLOS ONE 9(10) (2014). https://repozytorium.p.lodz.pl/items/4a04de44-da0d-45ad-866a-5a33c0d1c4f7. Where growth colonizes concrete.
53. RMIT Learning Lab. *buildright: concrete slab reinforcement, re-entrant corners*. https://learninglab.rmit.edu.au/Toolbox/buildright/content/bcgbc4010a/10_floor_systems/03_concrete_slab_reinforcement/page_007.htm. Re-entrant corner weakness.
54. ICRI. *Concrete Repair Terminology*. https://www.icri.org/resources/concrete-repair-terminology/. Bug holes, honeycomb, efflorescence, D-cracking definitions.
55. Taylor, P. / National CP Tech Center. *Concrete Pavement Surface Defects* (slides, 2023). https://intrans.iastate.edu/app/uploads/2023/11/2023MS_1_Taylor-CP-Surface-Defects.pdf. Pop-out shape, flaking around aggregate.
56. SPIB. *Nominal vs actual lumber sizes*. https://blog.spib.org/nominal-vs-actual-lumber-sizes/. Dressed-width rule for board widths.
57. North Dakota Aeronautics Commission. *PCI review: PCC distresses* (durability cracking, popouts, scaling; ASTM D5340-based, 2018). https://apps.aero.nd.gov/app/pavement/pavement-inspection/pci-review/distresses-pcc/durability-cracking.html. D-crack band, pop-out size and density, scaling area classes.
58. Kotthaus, S., Smith, T. E. L., Wooster, M. J., Grimmond, C. S. B. *Derivation of an urban materials spectral library through emittance and reflectance spectroscopy*, ISPRS J. Photogramm. Remote Sens. 94 (2014) 194-212, doi:10.1016/j.isprsjprs.2014.05.005; data: *Spectral Library of Impervious Urban Materials* v1.0 (LUMA SLUM), https://doi.org/10.5281/zenodo.4263842. Concrete samples C001-C006, C008: visible/solar ratio and spectral slope (computed for this sheet with CIE Y, D65 and ASTM G173 weighting).
59. Pomerantz, M., Akbari, H., Chang, S.-C., Levinson, R., Pon, B. *Examples of cooler reflective streets for urban heat-island mitigation: Portland cement concrete and chip seals*, LBNL-49283 (2003). https://www.osti.gov/biblio/816205. Field solar albedo of 16 PCC streets 0.18-0.35, mean 0.26.
60. ACI 318-19 *Building Code Requirements for Structural Concrete*, Table 20.5.1.3.1 (specified cover, cast-in-place nonprestressed), as reproduced in ideCAD documentation. https://help.idecad.com/ideCAD/beam-reinforcement-detailing. 38/50 mm exposed to weather, 19 mm interior (No. 11 and smaller), 76 mm cast against earth.
61. Kreijger, P. C. *The skin of concrete: composition and properties*, Materials and Structures 17 (1984) 275-283, doi:10.1007/BF02479083. Cement skin ~0.1 mm, mortar skin ~5 mm, concrete skin ~30 mm (values seen only as quoted by secondary sources).
62. Engelberts, G., Dalhuisen, F. D., Bodde, W., Sparrius, L. B. *Urban lichenometry: growth of Circinaria contorta on city sidewalks*, Lindbergia (2026), doi:10.25227/linbg.028935. https://research.wur.nl/en/publications/urban-lichenometry-growth-of-circinaria-contorta-on-city-sidewalk/. Peak radial growth 1.68 mm/yr on concrete pavement.
63. Garty, J. *Some observations on the establishment of the lichen Caloplaca aurantia on concrete tiles in Israel*, Studia Geobotanica 8 (1988) 13-21. https://www.openstarts.units.it/. Coverage 2.5 / 23 / 49 % at 30 / 45 / 60 yr (the methods give 20 yr for the youngest roofs).
64. Stohl, L., Manninger, T., Dehn, F., von Werder, J. *Understanding bioreceptivity of concrete: material design and characterization*, Materials and Structures (2025), doi:10.1617/s11527-025-02863-y. Fresh pH > 12; biofilms need < 10; carbonation lowers surface pH.
65. PCI. *Designer's Notebook DN-29: Weathering* (reprinted in Ascent, 2013). https://www.saraschok.com/corporate787/corporateFiles/1834/DN-29Weathering.pdf. Run-off film, streams vs broken flow, corner rain load, dirt deposition, acid etching of paste.
66. ACI Committee 347. *ACI 347-01 Guide to Formwork for Concrete*, §3.4 Table 3.1, §5.3.4, §5.4-5.5, §6.5 (class values also in ACI 117-10 §4.8.3; summary in ASCC *Guidance for Concrete Contractors #17*, https://ascconline.org/Home/News/ID/337/Guidance-for-Concrete-Contractors-17-in-a-Series). Surface classes A-D, Class C default, tie-end cover, grade strips, rustications, re-anchoring at lift joints, low-lift heights.
67. Doka. *Framax Xlife* product page and User Information 999783014 (Framax S Xlife, 12/2021). https://www.doka.com/en/system-groups/doka-wall-systems/framed-formwork/framax-xlife/index; https://direct.doka.com/_ext/downloads/downloadcenter/999783014_2021_12_online.pdf. Panel sizes, ties 1.35 m apart, two tie rows per 2.70 m, 22/26 mm plugs.
68. ACI Committee 224. *ACI 224.3R-95 Joints in Concrete Construction*, §3.3.2, §8.3, §9.1. https://www.concrete.org/store/. Wall contraction and expansion joint spacing, base-restraint crack spacing.
69. WSDOT. *Bridge Design Manual* M 23-50.24 (2025), ch. 8 Walls and Buried Structures, §8.1.10-8.1.11. https://wsdot.wa.gov/publications/manuals/fulltext/m23-50/chapter8.pdf. Weep holes, wall contraction and expansion joints.
70. FDOT. *Standard Plans Index 400-010* (FY2019-20). https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/design/standardplans/2020/idx/400-010.pdf. Wall joints <= 25 ft, every fourth an expansion joint; 3 in drains <= 10 ft.
71. ACI Committee 207. *ACI 207.2R-95 Effect of Restraint, Volume Change, and Reinforcement on Cracking of Mass Concrete*, §4.2.2. https://www.concrete.org/store/. Base-restrained cracks start at the base, spaced 1-2 x height.
72. El Khoury et al. *Engineering Structures* 345 (2025) 121536, doi:10.1016/j.engstruct.2025.121536 (citing CIRIA C766). https://eprints.whiterose.ac.uk/id/eprint/237099/. Maximum width of base-restrained wall cracks above the base.
73. Wisconsin DOT. *Structure Inspection Manual*, Part 4 ch. 4 and Part 2 ch. 5 (2017). https://wisconsindot.gov/dtsdManuals/strct/inspection/insp-fm-pt2ch5.pdf. Leaching at cracks where moisture from the fill escapes.
74. ACI Committee 301. *ACI 301-99 Specifications for Structural Concrete*, §2.3.1, §5.3.7.2, §6.3.6.2. https://www.concrete.org/store/. Class A for surfaces exposed to public view, plugging tie holes, colour-matched repairs.
75. Water Power & Dam Construction, on controlled permeability formwork. https://www.waterpowermagazine.com/?p=885. With impermeable forms the outer 20 mm is the poorest concrete; draining surplus water makes it the best (trade source, seen only as a search summary).
76. Sustainable Development Group, *Zemdrain Controlled Permeability Formliner*. https://wearesdg.com/?p=2376. Lower near-surface w/c and porosity in the cover zone; durability equivalent to 15-20 mm extra cover (manufacturer source, seen only as a search summary; see also ACI abstract https://www.concrete.org/publications/internationalconcreteabstractsportal/m/details/id/949).
