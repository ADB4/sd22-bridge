# Asphalt pavement surfaces: reference sheet

> **Scope:** asphalt-concrete pavement surfaces seen top-down: roads, parking lots, driveways and paths, from fresh to failed. The main case is dense-graded hot-mix asphalt (HMA) with a 9.5-12.5 mm NMAS wearing course. The sheet also covers how stone-matrix asphalt (SMA), open-graded/porous asphalt (OGFC, PEM) and chip seal differ, and the maintenance items laid on asphalt: crack sealant, patches, sealcoat, fog seal and markings. **Not covered:** asphalt roof shingles, mastic (poured) asphalt flooring and roofing, airfield markings and grooving, concrete (PCC) pavements except as a layer under an overlay, and detailed shoulder features (rumble strips, raised markers): research those live.
> **Researched:** 2026-10-02, revised 2026-10-03. **Revised 2026-10-03 (asphalt lane build):** joint density deficit (typical 2-5 %), new 9.5 mm texture depth, LTPP severity wording, gearbox streak, the joint's hot-side step, gloss loss in weeks, the paving joint as the first crack, collector layer stacks, the PAVER pothole matrix; sources [51]-[57]. **Confidence:** distress definitions, severity bands, crack widths, rut and pothole depths, lane, wheel-path and marking geometry, layer and lift thicknesses and chip-seal construction come from FHWA/LTPP, US Army PAVER, DOT specifications and manuals (high). Visible albedo of new and old asphalt, street paint and concrete is measured (spectraldb); solar albedo with age is measured (LBNL); intermediate ages are interpolated (medium). Nearly all roughness values, oil-drip positions, paint wear at texture peaks, drying patterns and per-variant height ranges are estimates from physics, marked (est.) (low-medium).

Every number carries a source tag `[n]` (see Sources) or `(est.)` with a one-line reason.
Give ranges rather than single values, and say which variant or region a value applies to.

Conventions in this sheet: the lane axis (traffic direction) is tile **V** (image vertical, `axis_deg` 90), the lane centre is U = 0.5, "WP" means wheel path and "NWP" means outside the wheel paths. Variants V0-V4 are defined in section 8.

## 0. Physical summary

Asphalt concrete is crushed stone and sand glued by 4.7-6.8 % bitumen by mass [21]. A paver lays it hot in lifts 3-5 × the nominal maximum aggregate size (NMAS) thick, and rollers compact it to about 7 % air voids or less [12]. A road is a stack of these lifts, a wearing course over a binder course, on an unbound crushed-stone base [11]. Procedural versions most often get three facts wrong:

1. **Age makes dense asphalt lighter, and what lies beneath the surface is darker.** The black binder film oxidises and wears off the stone tips, so the aggregate's own colour takes over. Measured visible reflectance is 0.042 for new and 0.124 for old asphalt (sRGB 58 → 98/93/80) [36]; solar reflectance rises from 0.04-0.05 fresh to about 0.12 after 5 years and 0.15-0.20 weathered [30][31]. Crack walls, fresh patches and fresh crack sealant expose or add less-aged binder, so they are darker than the weathered surface [32][50]. Two exceptions: a raveled area as a whole measures *brighter*, because loose and exposed stone dominates [32], and chip seals start at the aggregate's albedo and darken [30].
2. **Wear removes the wearing course from the top down and reveals more of the same mix, never the base.** Weathering strips the fine mastic first, then raveling plucks out coarse stones; disintegration runs "from the surface downward" [2][14]. A 19-50 mm wearing course and a 50-100 mm binder course lie between the surface and the light grey unbound base [11]. Base shows only at the bottom of a pothole that has gone through every bound layer, or at a broken pavement edge. Mix and subgrade ruts are deformation and expose nothing [2][15]; only studded-tyre wear ruts remove material (4.6).
3. **Damage is organised by the lane.** Wheel paths are two 1.0 m strips whose inner edges lie 0.375 m either side of the lane centre [3][4]. Fatigue cracking, rutting, bleeding and polishing occur there [1][2]. Thermal transverse cracks cross the lane at spacings of tens of metres (23.6 ± 10.3 m in interior Alaska [28]); metre spacing (2.4-6 m) means a cement-treated base [29]. Block cracking ignores traffic [2], and oil collects in the lane centre between the wheel paths [44]. Crack width is a severity band (≤6, 6-19, >19 mm) set by how far the crack has opened, not by erosion of the surface [1]; M and H also cover narrower cracks with adjacent random cracking [1].

## 1. Construction and layout

**Roads: lanes, wheel paths, joints**
- Lane width is 3.6 m (12 ft) on high-speed roads, 3.0-3.6 m on urban arterials, and down to 2.7 m on low-volume rural roads [6].
- Wheel paths follow the AASHTO R 85 lane zones used for federal reporting: two 1.0 m (39 in) strips with inner edges 0.375 m either side of the lane centre, so 0.75 m apart [3][4]. The WP centrelines sit ±0.875 m from the lane centre. Each edge zone is (lane width − 2.75 m)/2: 0.43 m for a 3.6 m lane and 0.13 m for a 3.0 m lane (derived). The strips are a reporting convention; real lateral wander spreads load damage up to about 150 mm beyond them (est.).
- Paving lanes match traffic lanes. The surface-lift longitudinal joint is wanted at the centreline, but planned so it does not fall within wheel paths, recessed markings or striping [18]: in practice it runs beside the lane line, just outside the stripe (est.: 150-300 mm from the stripe edge). It is offset ≥150 mm (many specs 300 mm) from the joint in the lift below [18]. A joint is typically 2-5 % less dense than the mat (≤2 % is the recommended target; PennDOT averaged 91.4 % at the joint against 93.9 % in the mat), and its hot side is denser than its cold side [17][51]. The hot lane overlaps the cold lane by 25 ± 12 mm and is left about 2.5 mm higher after rolling [51]. Joints are where longitudinal cracks and raveling start [17][18]; the paving joint is usually the first longitudinal crack, open along 90-100 % of its length, 3-12 mm wide, by year 3-4 in Michigan and Wisconsin [55].
- Transverse construction joints sit at paving stops. About 55 % of localised raveling on OGFC occurs at transverse joints [25].
- Segregation is the as-built texture variation [19]. It shows as chevron-shaped coarse spots at the start and end of each truckload, a streak down the paver centre (gearbox: 150-200 mm wide, directly behind the main-screed centre, more open and generally darker [54]), and streaks at one or both lane edges. NCHRP 441 texture-ratio bands: low 1.16-1.56, medium 1.57-2.09, high > 2.09 [53]. The truckload interval is about 50 m for a 3.7 m × 40 mm lift (est.: 18 t load ÷ 2.35 t/m³ ÷ 0.148 m²).
- Markings follow the US MUTCD [7]. A normal line is 100-150 mm (4-6 in) wide and a wide line is at least twice that. Broken lane lines are 3.0 m segments with 9.1 m gaps (a 12.2 m cycle). Dotted lane lines are 0.9 m on, 2.7 m off. Thermoplastic edge lines on the inside of curves get 150-300 mm drainage gaps every 76 m [8]. FHWA recommends spacing crosswalk bars so they avoid the wheel paths [47]. Snow-plough states often use recessed (grooved-in) markings [18].

**Parking lots, driveways, paths**
- A 90° stall is ≥2.74 m (9 ft) wide; its length is 6.1 m (20 ft) in Johnsburg and 5.49 m (18 ft) in Lindon; compact 2.44 × 5.5 m. A two-way aisle is 7.3 m (24 ft) [45]. Stripes are 100 mm wide [13].
- Lots need ≥2 % slope; below 2 %, "bird baths" (ponds) form [13]. Stalls run along the perimeter and each aisle serves two rows [13].
- Driveways have two tyre tracks at the vehicle track width, about 1.5-1.6 m (est.: passenger-car track). Paths have no wheel paths, so damage there is thermal (block, transverse) and edge-driven (est.).

**Surface types**

| Type | Structure | Top-down look | Source |
|---|---|---|---|
| Dense-graded HMA | well graded from coarse to fine; impermeable | stones nearly flush in black mastic; 18-46 % (9.5 mm mixes) to 46-52 % (12.5 mm mixes) of the mass retained on 4.75 mm | [11][21] |
| SMA | gap-graded stone-on-stone skeleton of cubical crushed stone in a rich mastic with fibres or polymer | tightly packed coarse stones (64 % retained on 4.75 mm) with mastic in the gaps; deeper texture; more specular than AC | [11][21][37] |
| OGFC / PEM (porous) | near single-size coarse stone, 15-25 % voids, thin 19-32 mm lift over a dense layer | open "popcorn" texture with visible voids (86 % retained on 4.75 mm); drains, so less glare and spray in rain | [11][21][25] |
| Chip seal | binder sprayed, then one stone thickness of single-size chips rolled to about 70 % embedment; usually fog-sealed in Minnesota | fog-sealed: black, reads as new HMA; unfogged: aggregate colour, uniform chip size; streaks along V if the spray bar is set wrong | [24][30] |

**What the layout fixes.** These footprints are set at construction or maintenance, and no aging process may move them:
- lane lines and every marking footprint (dash, stall stripe, crosswalk bar, stop bar, arrow)
- longitudinal and transverse construction joints, curbs, gutters and pavement edges
- wheel-path strips, which follow from the lane geometry
- patch outlines and crack-seal bands once placed (a maintenance layout pass, section 3)
- the joint grid of any PCC slab under an overlay, since reflection cracks can only appear above it [1]
- utility covers.

Wear may remove material inside a footprint, as on a worn dash, but it never widens, moves or rounds the footprint. The one exception is shoving, which displaces the surface in plan (4.7). Exclude shove regions from layout checks.

## 2. Dimensions and scale

| Feature | Typical | Range | Variant / notes | Source |
|---|---|---|---|---|
| Lane width | 3.6 m | 2.7-3.6 m | 3.0-3.6 m urban arterials | [6] |
| Wheel path width | 1.0 m | | AASHTO R 85 / HPMS | [3][4] |
| Gap between wheel paths | 0.75 m | | inner edges ±0.375 m from lane centre | [3] |
| Lane line width | 100 mm | 100-150 mm | wide line ≥200 mm | [7] |
| Broken line | 3.0 m on + 9.1 m off | 1:3 ratio | 12.2 m cycle (US) | [7] |
| Parking stall (90°) | 2.74 × 5.49-6.1 m | compact 2.44 × 5.5 m | aisle 7.3 m two-way | [45] |
| Wearing (surface) course | 37.5 mm | 19-50 mm | dense 9.5-12.5 mm mix; OGFC 19-32 mm | [11][25] |
| Binder (intermediate) course | 57 mm per lift | 50-100 mm+ | 19 mm NMAS, 1-2 lifts | [11] |
| HMA over aggregate base (lots) | 64-152 mm HMA | base 100-584 mm | by traffic and subgrade | [13] |
| Full-depth HMA (lots) | | 100-290 mm | | [13] |
| Lift thickness ÷ NMAS | ≥3 fine-graded, ≥4 coarse/SMA | 3-5 optimum | | [12] |
| Porous asphalt (lots) | 50-100 mm | ≥16 % voids | over 50 mm choker and ≥200-230 mm reservoir | [13] |
| Thin overlay | ≤38-50 mm | | single lift | [20] |
| Surface NMAS | 9.5-12.5 mm | 4.75-19 mm | finer for city streets, 19 mm for industrial | [11] |
| Coarse fraction (>4.75 mm) | dense 12.5 mm: 46-52 % | dense 9.5 mm 18-46 %; SMA 64 %; OGFC 86 % | Virginia mixes | [21] |
| In-place air voids | ≤7 % | | dense mixes | [12] |
| Air voids, OGFC / PEM | 15 % / 18-22 % | 15-25 % | | [11][25] |
| Chip seal aggregate | FA-3 <9.5 mm (median 5.5 mm, ALD 3.75 mm); FA-2 <6.3 mm | flakiness 18-30 % (Class A-B) | one stone thick, ≈70 % embedded | [24] |
| Chip protrusion above membrane | ≈0.3 × ALD (1-1.5 mm, FA-3) | | est. from 70 % embedment [24] | (est.) |
| Microtexture | λ <0.5 mm | depth <0.2 mm | PIARC | [23] |
| Macrotexture | λ 0.5-50 mm | depth 0.1-20 mm | PIARC | [23] |
| Megatexture | λ 50-500 mm | depth 0.1-50 mm | PIARC | [23] |
| MTD, dense-graded | 0.4-0.6 mm | new 9.5 mm Superpave 0.36-0.75 (MPD 0.39-0.76); fine-graded 9.5 mm MPD 0.12-0.21 | new thin overlay | [20][52] |
| MTD, SMA | >1.0 mm | MPD 0.4-1.4 mm | NCAT test track | [20][22] |
| MTD, OGFC | 1.5-3.0 mm | MPD >1.0 mm new | | [20][22] |
| MTD, chip seal / microsurfacing / slurry | >1.0 / 0.5-1.0 / 0.3-0.6 mm | | | [20] |
| Laser texture by NMAS (ICC index ≈1.5 × MPD) | 9.5: 1.0-1.4 mm; 12.5: 1.6; 19: 1.5-1.7; 25: 2.0-3.5 | std grows with NMAS and segregation | Virginia | [21] |
| Crack width L / M / H (LTPP) | ≤6 / 6-19 / >19 mm | | longitudinal, transverse, block, reflection | [1] |
| Crack width L / M / H (PAVER) | <10 / 10-75 / >75 mm | | or any width with breakup within 100 mm | [2] |
| Slippage crack width L / M / H | <10 / 10-38 / >38 mm | | | [2] |
| Fatigue polygon, longest side | <0.3 m | <0.5 m | eq. diameter about 100-250 mm (derived) | [1][2] |
| Block size | | 0.3 × 0.3 to 3 × 3 m (0.1-10 m²) | | [1][2] |
| Cracks over cement-treated base | | 2.4-6 m spacing | transverse or block | [29] |
| Transverse crack spacing | 23.6 m | ± 10.3 m | interior Alaska, severe cold; sparser in mild climates (est.) | [28] |
| Edge-crack zone | ≤0.6 m from edge | 0.3-0.5 m | unpaved shoulders | [1][2] |
| Rut depth L / M / H | 6-13 / 13-25 / >25 mm | | mean depth under a straightedge | [2] |
| Rut, federal rating | good <5 mm | fair 5-10, poor >10 mm | 23 CFR 490 | [5] |
| Studded-tyre wear rate | | 0.04-0.5 mm/yr | measured on PCC; 60 % of HMA "rutting" in Washington is stud wear | [48] |
| Depression L / M / H | 13-25 / 25-50 / >50 mm | | | [2] |
| Pothole depth L / M / H | <25 / 25-50 / >50 mm | | | [1] |
| Pothole plan size | ≥150 mm | 100-760 mm | | [1][2] |
| Corrugation wavelength | <3 m | | ridges across traffic | [2] |
| Swell length | >3 m | | | [2] |
| Lane/shoulder drop-off L / M / H | 25-50 / 50-100 / >100 mm | | | [2] |
| Weathering L / M / H | stone edges exposed <1 mm / ≤¼ stone width / >¼ | | | [2] |
| Raveling, medium | >20 missing coarse stones per yd² (m²) | or clusters | | [2] |
| Patch, minimum | 0.1 m² | | | [1] |
| Patch crown | 3-6 mm | | throw-and-roll, edge seal | [27] |
| Sealant overband (band-aid) | 75-125 mm wide | 3-6 mm thick | | [26] |
| Crack width sealed / filled | 5-19 / 5-25 mm | | | [26] |
| Routed reservoir | 12-19 mm | | | [26] |
| Paint film | 0.38 mm (15 mil) wet per coat | final lines 2 coats; dry ≈0.2 mm per coat (est.) | 0.13-0.20 mm dry is the thin coat under thermoplastic | [8] |
| Thermoplastic above surface | 2.3 mm edge lines; 3.0 mm centre, skip, crosswalk | 6.1 mm rumble | | [8][10] |
| Polyurea / cold plastic | ≥0.5 mm / 0.4-2.3 mm | | | [8] |
| Glass beads | 0.3-0.85 mm | all <1.18 mm | 60 % embedded | [8][9] |
| Street dirt | 90 % of mass within 0.3 m of the curb | | half of particles 0.25-1 mm | [40] |
| Frost lip at thermal crack | +11-12 mm in February vs June | summer residual 0-3 mm (est.) | winter preset only | [28] |

**Recommended tile sizes at 2048 px** (mm/px = tile_m ÷ 2.048). Each tile must hold whole layout repeats, and the smallest important features must stay ≥3 px wide.

| Tile | Size | mm/px | Holds | Smallest features | Use |
|---|---|---|---|---|---|
| Detail | 1.0 m | 0.49 | uniform mix, no layout | 9.5-12.5 mm stones 19-26 px; 2.36 mm sand 5 px; beads 0.6-1.7 px, so roughness sparkle only | stone geometry, sockets, weathering; blended over the lane tile (section 10) |
| Mid | 2.0 m | 0.98 | uniform surface: lot, drive, path | stones 10-13 px; cracks ≥3 mm = 3 px | lots and paths without stripes; block cells up to 1 m |
| Lane | 3.66 m (one 12 ft lane; use the actual lane width for 3.0-3.6 m lanes) | 1.79 | exactly one lane across: lane lines split across U = 0/1 (56-84 px total), WP at px 255-814 and 1234-1793, centre zone px 814-1234 | M cracks ≥6 mm = 3.4 px; L cracks <5.4 mm fall under 3 px, so draw them 3 px wide or as darkening only; stones 5-7 px, so stone geometry comes from the detail tile | road lanes. The 12.2 m dash cycle does not fit: put dashes in decals or a trim sheet |
| Parking | 5.49 m | 2.68 | 2 stall widths (2 × 2.74 m) × one 18 ft (5.49 m) stall depth | 100 mm stripes 37 px; cracks ≥8 mm = 3 px | stall bodies. Tiled, the stripes run on without head ends: put head-end stripes, 20 ft stalls, aisles and stall oil stains in decals or a non-repeating trim |

**Height range per variant** (`height_depth_mm`, and where the as-built surface sits in the 0-1 range). One range cannot serve V0 and V4: V0 relief on the lane tile is a few mm, and a V4 pothole on a rut is over 100 mm deep. Use 16-bit height and world-unit normals, and export the `nowear` render with the same range and offset as its variant.

| Tile | V0 | V1 | V2 | V3 | V4 | Surface level | Why (est.) |
|---|---|---|---|---|---|---|---|
| Lane | 10 mm | 10 mm | 30 mm | 80 mm | 160 mm | 0.6 / 0.6 / 0.7 / 0.8 / 0.85 | V0-V1: thermoplastic +3 mm [8], ruts <5 mm [5]. V2: ruts ≤10, crack grooves, sealant +6 [26]. V3: potholes to 50 mm [1] on 13 mm ruts. V4: potholes to about 100 mm on 30 mm ruts, crowns and sealant above |
| Detail | 4 mm (8 SMA/OGFC) | 4 mm (8) | 24 mm | 32 mm | 40 mm | 0.85 (stone tips) | MTD 0.4-3 mm [20]; mastic up to 6 mm below the tips, plus sockets down to the ravel_depth targets (section 9) |

A winter preset adds frost lips (+11-12 mm [28]): raise the range by 15 mm and keep the surface level in mm. 16-bit is required: a paint coat (≈0.2 mm) is below one 8-bit step of a 60 mm range.

## 3. Layer model (stratigraphy)

Top to bottom for a dense-graded HMA road. Depth is measured below the stone tops of the as-built surface.

| Layer | What it is | Depth | Appearance | Visible when |
|---|---|---|---|---|
| D. Deposits | paint ≈0.2 mm per coat [8]; thermoplastic 2.3-3.0 mm [8]; sealant overband 3-6 mm [26]; sealcoat and fog-seal films [24][39]; dirt, loose stones, vegetation; bled binder [16]; oil and rubber (no thickness) | above the envelope | see section 7 | any time after placement |
| L0. Binder skin | thin bitumen film on every stone and grain (est.: of order 10 µm) | 0 | fresh: black, visible 0.042, slight sheen [36]; oxidises and wears off stone tips first | V0 everywhere; gone from WP tips by V1-V2 |
| L1. Mastic (fine-aggregate matrix) | sand + filler + binder between coarse stones | 0 to MTD (0.4-0.6 mm dense; >1 mm SMA; 1.5-3 mm OGFC) [20] | black → warm grey as binder oxidises and sand shows [32][36] | always; receding with weathering [2] |
| L2. Coarse aggregate | crushed stone 4.75 mm to NMAS (9.5-12.5 mm) [11] | tips at 0; bodies to about NMAS | rock colour: limestone/dolomite light grey-buff, granite grey or pink speckled, traprock (basalt) dark grey (est.: rock types; US crushed stone is 70 % limestone/dolomite, 14 % granite, 6 % traprock [41]) | edges exposed <1 mm (L) → ≤¼ stone width (M) → >¼ (H) [2] |
| L3. Body of the wearing course | the same mix, shielded from sun and tyres | to 19-50 mm [11] | black, less oxidised than the surface [32][50] | socket floors, crack walls, upper pothole walls |
| L4. Binder (intermediate) course | coarser mix, 19-25 mm NMAS [11] | about 40-150 mm | black, bigger stones; the tack-coated top is a slip plane (slippage cracks) [2] | M-H pothole walls; floor of many potholes (est.: delamination at the interface) |
| L5. Base | unbound crushed stone 100-584 mm (lots) [13], or HMA base (25-37.5 mm NMAS) [11] | below all bound layers | unbound: light grey-tan, loose, dusty, no binder (est.) | only in potholes deeper than every bound layer (bound layers total 64-152 mm on lots [13]) and at broken edges (4.13) |
| L6. Subbase / subgrade | compacted soil or borrow [11] | deepest | brown soil; its fines are what pumping deposits on the surface [1] | failed areas; pumping stains |

Other stacks (each needs its own `layer_index` thicknesses, section 10). "Beneath is darker" fails where the layer beneath is older or mineral:
- **Overlay on old asphalt:** beneath a 38-50 mm overlay [20] lies the old surface, oxidised grey and cracked. Its cracks reflect upward [2]. A delaminated or potholed overlay shows that lighter surface (est.).
- **Overlay on PCC:** a light grey concrete slab (visible 0.15 [36]; solar 0.18-0.35 field [30]) sits at overlay depth, with a joint grid that cracks the overlay above it [1].
- **Chip seal:** single-size chips one stone thick (ALD about 3.75 mm) about 70 % embedded in a black residual-binder membrane, over the old surface [24] or, on low-volume roads and shoulders, a primed granular base (est.). Lost chips reveal black binder, then the old grey surface or the base (4.25).
- **OGFC:** a 19-32 mm porous layer over impermeable dense mix [25]. Raveled OGFC reveals the darker, smoother dense layer (est.).
- **Sealcoat or fog seal:** a black film over aged grey asphalt or chips [24][39]. Worn film reveals the lighter surface beneath: wear lightens by removing a black deposit.
- **Cold-milled surface (temporary, before an overlay):** longitudinal grooves and fractured, light grey stone (est.).

**Original surface envelope.** The envelope is the as-built (`nowear`) height field: the L2 stone tips with the L1 mastic between them, including construction texture and segregation. The `nowear` render is this envelope plus the patches as placed, the deformation field and the as-built markings (I2).
- **Removal processes go below the envelope:** weathering, raveling, cracking, potholes, studded-tyre wear ruts, chip loss, scuffing and marking-removal scars. Polishing removes only microtexture.
- **Deposits sit above it, each with its own mask:** markings, sealant, sealcoat, fog seal, dirt, debris, vegetation and bled binder. Bled binder fills valleys from within and, except as a film at high severity, stays below the stone tips (est.). Export their union as `deposit`.
- **Patches are new material placed at a known time.** A patch replaces the envelope inside its footprint with its own surface (its own stones, crown 0 to +6 mm [27]) and resets the age there to zero. Treat it as a maintenance-layout feature: the `nowear` render contains every patch as placed, so the envelope check compares a patched surface with a patched reference. Damage that formed before the patch is gone inside the footprint; aging after the patch acts on it with the patch's own age.
- **Deformation moves the envelope itself.** Mix and subgrade rutting, shoving, corrugation, swell, depressions and frost heave conserve volume, so mix ruts push up shoulders beside them [15] and frost lifts crack edges 11-12 mm in winter [28]. Build deformation as a smooth displacement field applied to the whole stack, export it as `deform`, and put it in the `nowear` render as well, driven by the same parameters, so `envelope` compares like with like.

Cross-section at close range (detail tile). Neighbours sit side by side, and beneath each is the same course:

```
            overband 75-125 mm wide, 3-6 mm proud            socket: stone plucked out
             _______________________
   stone    /  sealant (black, then  \    stone                         stone
   /^^\    /   dusted grey)           \   /^^^\     .-.        .-.      /^^\
__/    \__/__________..__..____________\_/     \___/   \______/   \____/    \___ envelope
 mastic    |  wearing course  |  mastic         |  socket floor:    |     mastic
 (aged     |  crack walls =   |  (aged grey)    |  same mix, less   |     (aged)
  grey)    |  same mix, black |                 |  aged (est.)      |
-----------+--- wearing course (same mix, unoxidised, black) ----------------------  19-50 mm
-----------+--- binder course (19-25 mm NMAS, black) ------------------------------  ~40-150 mm
..........................aggregate base (unbound, light grey, loose)...............
```

Cross-section across a lane (lane tile). Deformation ruts bend the courses; a stud-wear rut cuts the wearing course:

```
 lane line | joint  | wheel path 1.0 m     | centre 0.75 m       | wheel path 1.0 m     | edge | lane line
 thermo    | beside | rut floor: binder    | (hump if mix ruts)  | rut floor            |      | paint
 2.3-3 mm  | stripe | worn, lighter;       | darker oil band;    | fatigue, bleeding,   |      | ~0.2 mm/coat
 deposit   |        | fatigue, bleeding    | no fatigue          | polishing            |      | deposit
 ======== wearing course 19-50 mm: same thickness under deformation ruts, thinner under wear ruts ==
 ======== binder course =======================================================================
 ........ aggregate base: exposed only where a pothole is deeper than every bound layer ......
```

A pothole exposes whatever layer lies at its depth in the stack. With a 37.5 mm wearing course, L and most M potholes still have a wearing-course floor; the bound layers total 64-152 mm on lots [13] and more on roads, so many H potholes still have a black floor:

```
 L: <25 mm             M: 25-50 mm               H: >50 mm            H, deeper than all bound
 ___      ___          ___          ___          ___         ___      ___               ___
    \____/                |        |                |       |            |             |
  wearing course          | wearing|                |binder |            | base: grey, |
  (same mix, black)       | ->binder                |course |            | loose stone |
                          |________|                |_______|            |_____________|
```

## 4. Processes: aging, wear, damage, deposition

Preset mapping used below: V0 fresh (0-6 months), V1 young (1-2 years), V2 weathered (3-7), V3 distressed (8-15), V4 failed (section 8).

### 4.1 Binder oxidation and fading
- **Mechanism:** bitumen loses oily fractions, oxidises and hardens under oxygen, UV and heat [32]. The thin film on stone tips is the first to oxidise and wear away, so the mineral colour shows [32].
- **Acts on:** L0 binder skin and the top of L1. **Removes / adds:** removes binder film, with no measurable height change. **Reveals:** stone colour (L2) and sand grains in the mastic.
- **Never:** darkens the pavement. Never makes crack walls or newer patches lighter than the older surface around them. Never changes texture depth by itself.
- **Where:** everywhere; faster in strong sun [2]. Fastest on WP stone tips, where traffic also wears the binder [37]. Slower in shade and under markings (est.: shielded from UV and tyres).
- **Shape and scale:** per stone first (tips), then a uniform rise in luma; WP slightly lighter than off-track [37].
- **Gloss:** "shiny black" when laid, losing gloss within weeks and dark grey within 6-12 months [56]; the road-lighting specular factor S1 falls from 5.0 new to 1.7 at 7 months and 0.4 at 3 years [57].
- **Progression:** V0 black (visible 0.042 [36]; solar 0.04-0.05 [30]) → V1 dark grey (low weathering can show at 6 months [2]) → V2 grey (visible about 0.12, "old black asphalt" [36]; solar about 0.12 at 5 years [30], 0.15-0.20 weathered [31]). The spectral change from year 1 to 3 equals that from year 3 to 10+ [32], so front-load the colour curve. Field reflectance runs 0.06-0.09 early, 0.09-0.135 mid and 0.105-0.24 late in aging (field spectra, 350-2500 nm) [34].
- **Interactions:** hardened binder leads to block cracking [2] and raveling [14]. The visible colour turns from neutral to warm: B/R is 0.93 new and 0.66 old [36]. Across field asphalts R460 ≈ 0.6-0.8 × R740 [33].
- **Signature per map:** albedo up, hue from neutral black to warm grey [36]; roughness up (est.: 0.55 → 0.85-0.95 on mastic); height, normal and AO unchanged.
- **Severity scale:** PAVER weathering L, "fading of the asphalt color" [2].
- **Sources:** [2][30][31][32][33][34][36][37]

### 4.2 Weathering: loss of the fine matrix
- **Mechanism:** "wearing away of the asphalt binder and fine aggregate matrix" by oxidation, traffic and water erosion, faster under high solar radiation [2].
- **Acts on:** L1 mastic. **Removes / adds:** removes mastic between stones, about 0.1-3 mm (est.: <1 mm at L up to ¼ of a 9.5-12.5 mm stone at M). **Reveals:** more of the same coarse stones (L2), which now stand proud.
- **Never:** lowers stone tips (stones stay at envelope height until plucked out). Never exposes base. Never widens joints or markings.
- **Where:** everywhere; strongest in WP, where the surface coarsens and small aggregate loosens [37]. Also at segregated spots and joints [17][19] and in sunny areas [2].
- **Shape and scale:** mastic recedes around each stone, sharpening its outline; texture depth rises.
- **Progression:** L: stone edges exposed <1 mm, possible at 6 months → M: up to ¼ of the stone's width → H: more than ¼, some stones lost [2]. V1 = L, V2 = M, V3 = H.
- **Interactions:** leads to raveling (4.3); the surface gets brighter as mineral dominates [32].
- **Signature per map:** height: mastic down relative to stones; normal: crisper stone rims; albedo up (stone faces); roughness up; AO slightly deeper between stones.
- **Severity scale:** PAVER weathering L / M / H [2].
- **Sources:** [2][17][19][32][37]

### 4.3 Raveling: loss of coarse aggregate
- **Mechanism:** the stone-binder bond fails through dust coatings, segregation, low compaction, moisture stripping or fuel softening. Traffic, studded tyres or snowplows then dislodge stones: "progressive disintegration ... from the surface downward" [14][42].
- **Acts on:** L2, then L3. **Removes / adds:** removes whole stones and clusters. **Reveals:** a socket lined with the same wearing-course mix, less oxidised (est.: shielded binder [32][50]). Repeated loss lowers the wearing course step by step; the binder course appears only after the wearing course is gone.
- **Never:** reveals base or subgrade colour (only potholes and broken edges do). Never leaves a socket deeper than about one stone per loss event (est.). Never raises a stone above the envelope.
- **Where:** segregated spots (end-of-load chevrons, centre streak, lane edges) [19]; low-density longitudinal joints [17][18]; transverse joints (55 % of OGFC raveling) [25]; fuel and oil drip zones [42]; WP (studs, shear) [14]; parking-lot turning areas (scuffing, 4.27).
- **Shape and scale:** sockets the size of the coarse stones (4.75-12.5 mm), then clusters. Medium = more than 20 missing coarse stones per yd² (m²), or clusters; high = "very rough and pitted", sometimes with the layer removed in places [2]. Loose stones collect nearby [32].
- **Progression:** V2: isolated sockets at segregation and joints → V3: medium patches → V4: high, merging into potholes.
- **Interactions:** raveled areas hold water [14] and grow into potholes. A raveled area as a whole measures brighter than normal pavement, because rock and loose gravel dominate [32]; only the socket floors may be darker (est.).
- **Signature per map:** height: sockets about one stone deep; normal: pitting; albedo: area average brighter [32], socket floors slightly darker (est.); roughness up; AO in sockets.
- **Severity scale:** PAVER raveling M / H (lighter loss is rated as weathering) [2]; LTPP records area only [1].
- **Sources:** [1][2][14][17][18][19][25][32][42]

### 4.4 Polishing
- **Mechanism:** tyre abrasion smooths the microtexture of exposed stone faces. On concrete test sections, limestone lost microtexture faster than granitic rock [23]; coarse aggregate in asphalt behaves similarly (est.).
- **Acts on:** exposed L2 tops. **Removes / adds:** removes microtexture (λ <0.5 mm, depth <0.2 mm [23]). **Reveals:** a smooth face on the same stone.
- **Never:** changes macro height. Never makes a whole wheel path mirror-like (that is bleeding, 4.5). At driving angles, wheel tracks measure slightly *less* specular overall (lower S1) and lighter (higher Q0), because the surface coarsens and binder wears [37].
- **Where:** WP; braking and turning zones (est.).
- **Shape and scale:** per stone top; flattened facets only on stones that protrude.
- **Progression:** from V2. PAVER counts it only when stones are "smooth to the touch" and protrusion is "negligible" [2].
- **Interactions:** not rated where bleeding is rated [2]; friction falls with age through polishing and wear [23].
- **Signature per map:** roughness down on stone-top pixels only (est.: 0.8 → 0.55-0.7); albedo very slightly up (est.); height, normal and AO unchanged.
- **Severity scale:** none [1][2].
- **Sources:** [1][2][23][37]

### 4.5 Bleeding and flushing
- **Mechanism:** excess binder (high binder content, low air voids or an over-applied seal) fills voids in hot weather and expands onto the surface. It does not reverse in cold weather, so it accumulates [2][16].
- **Acts on:** L1/L2, from within. **Removes / adds:** adds a binder film that fills macrotexture, up to and over stone tips at high severity. **Reveals:** nothing; it covers.
- **Never:** rises more than a film above the stone tips (est.).
- **Where:** "usually found in the wheel paths" [1][16]; chip-seal WP, where flat chips lie flat [24]; stop lines (est.: slow, heavy loads). Exceptions outside the WP: over-applied sealant or seal coats [2] and SMA fat spots (4.25).
- **Shape and scale:** two dark strips per lane, each about 0.3-0.8 m wide (est.: tyre-track width inside the 1.0 m WP); texture fills progressively.
- **Progression:** discoloured → losing texture → stones obscured, "shiny, glass-like", tacky [1]. PAVER L / M / H by how many days or weeks a year it is sticky [2]. V2 slight in WP, V3-V4 extensive.
- **Interactions:** lowers MTD; very slippery when wet (est.); excludes polished-aggregate rating in the same area [2].
- **Signature per map:** albedo toward binder black (linear 0.03-0.05, est.); roughness 0.15-0.35 (est.); height: valleys filled, MTD down; normal flattened; AO down.
- **Severity scale:** PAVER L / M / H [2]; LTPP area only [1].
- **Sources:** [1][2][16][24]

### 4.6 Rutting and depressions
Two mechanisms make wheel-path troughs, and they look different.
- **Mechanism (a) deformation:** permanent deformation from consolidation or lateral flow under wheel loads [2]. Mix rutting gives narrow ruts with raised edges where material flows up; subgrade rutting gives wide, shallow ruts without raised edges, often cracked [15]. Depressions are local settlement and can occur anywhere [2].
- **Mechanism (b) studded-tyre wear:** studs abrade the surface in each car track. In Washington, 60 % of what surveys record as rutting on HMA is stud wear [48]; wear on PCC runs 0.04-0.5 mm/yr [48]. Common wherever studs are legal (US Northwest, Alaska, Canada, the Nordic countries).
- **Acts on:** (a) the whole structure; (b) L1-L3 from the top. **Removes / adds:** (a) nothing, material moves; (b) removes mastic and plucks stone. **Reveals:** (a) nothing; (b) coarse, exposed stone of the same course, lighter than the surrounding surface (est.), and at depth the next lift.
- **Never:** (a) exposes lower layers or has sharp edges, or lies outside the WP [1][2]. (b) widens past the car track (est.).
- **Where:** both WP of each lane; worst where heavy vehicles stop or climb (est.). Wear ruts sit in the car tracks, narrower than truck duals (est.).
- **Shape and scale:** (a) a trough per WP about 1.0 m wide [3]; depth L 6-13, M 13-25, H >25 mm [2]; mix-rut shoulders hold the displaced volume (est.: a few mm). (b) a groove about 0.4-0.7 m wide (est.: car tyre track) centred in each WP, with gentle flanks. Depressions L 13-25, M 25-50, H >50 mm, showing as ponds or as stains left by ponding when dry [2].
- **Progression:** V1 <5 mm (federal "good") → V2 5-10 mm ("fair") → V3 L-M → V4 H [2][5].
- **Interactions:** ruts fill with water after rain [2][15]; fatigue cracking often shares the WP [1]; markings dip with deformation ruts (est.).
- **Signature per map:** height: low-frequency trough with soft edges; normal: very subtle; albedo: (a) unchanged or slightly worn, (b) lighter and coarser floor (est. from [37]); wet state: puddles; ring stains around dry depressions [2].
- **Severity scale:** PAVER rut and depression depth [2]; federal rut rating [5]; LTPP records measured depth [1].
- **Sources:** [1][2][3][5][15][37][48]

### 4.7 Shear deformation: shoving, corrugation, slippage, swell
- **Mechanism:** braking or accelerating traffic shears an unstable mix, or slides a poorly bonded surface lift [1][2]. Swell comes from frost or expansive soil [2].
- **Acts on:** the wearing course, or the bond between lifts (slippage). **Removes / adds:** nothing; material moves along the traffic direction. **Reveals:** crack walls only (slippage).
- **Never:** forms ripples parallel to traffic. Never occurs on straight, free-flowing sections without a braking, turning, climbing or abutment cause (est.).
- **Where:** intersections, hills and curves [1]; where asphalt abuts PCC [2]; slippage in braking and turning zones [2].
- **Shape and scale:** a shove is a short, abrupt wave. Corrugation is regular ripples less than 3 m apart, across the traffic direction. Slippage cracks are crescents whose two ends point in the direction of travel, widths L <10, M 10-38, H >38 mm. A swell is a gradual bulge more than 3 m long [2].
- **Progression:** V3-V4 only, at causes.
- **Interactions:** shoves push stop bars and patches out of line (est.), so exclude shove areas from layout checks.
- **Signature per map:** height waves of a few mm to cm (est.); crescent cracks; distorted markings.
- **Severity scale:** PAVER by ride quality; slippage by width [2].
- **Sources:** [1][2]

### 4.8 Fatigue (alligator) cracking
- **Mechanism:** repeated wheel loads crack the bound layer. Classically cracks start at the bottom and rise as parallel longitudinal hairlines, then interconnect [2]. In thick pavements they often start at the surface instead, from wheel-load tension in an aged, brittle top layer: longitudinal cracks in or near the WP that later join into alligator cells [49]; these stay in the wearing course (est.).
- **Acts on:** the bound thickness (bottom-up) or the wearing course (top-down); at the surface it opens gaps in L0-L3. **Removes / adds:** little at first; at high severity, edges spall and pieces loosen [1][2]. **Reveals:** crack walls of the same mix, darker and less aged [32]; pumped fines at high severity [1].
- **Never:** occurs outside repeated-load areas [1][2]. Never forms pieces larger than about 0.3-0.5 m [1][2] or a straight grid.
- **Where:** WP; top-down lines often at the WP edges [49]. Short transverse cracks spaced <0.3 m inside a WP also count as fatigue [1].
- **Shape and scale:** L: "an area of cracks with no or only a few connecting cracks" [1], parallel hairlines along V. M: a complete "chicken wire" network, perhaps slightly spalled. H: well-defined spalled pieces that may rock, possibly with pumping [1][2]. Pieces are many-sided and sharp-angled, usually <0.3 m on the longest side [1] (<0.5 m [2]).
- **Progression:** V2: L lines, patchy in WP → V3: M cells over a large share of WP (federal "good" is <5 % of WP area cracked [5]) → V4: H with pumping and potholes.
- **Interactions:** goes with rutting [2]; leads to potholes [2] and patches (4.15); cracks reduce reflectance [32]. Fatigue areas are patched, not crack-sealed (4.16).
- **Signature per map:** height: narrow V-grooves, later dirt-filled (est.: 2-10 mm visible depth); albedo: crack walls take the fresh-binder colour, dirt fill lightens toward soil; height and AO make the line read dark; roughness up in cracks; at H, pieces slightly tilted or sunken (est.).
- **Severity scale:** LTPP L / M / H [1]; PAVER L / M / H [2].
- **Sources:** [1][2][5][32][49]

### 4.9 Block cracking
- **Mechanism:** shrinkage of hardened asphalt plus daily temperature cycling. It is not load-related and signals a hardened binder [2].
- **Acts on:** the surface course. **Removes / adds:** a gap only; spalling at high severity. **Reveals:** darker crack walls [32].
- **Never:** is confined to WP; it often covers large areas and "sometimes will occur only in non-traffic areas" [2]. Never forms sharp-angled pieces under 0.3 m (that is fatigue) [2].
- **Where:** large areas of old, oxidised pavement; typical of parking lots, shoulders and paths (est.: low traffic means little kneading). Over cement-treated bases, shrinkage cracks reflect up at 2.4-6 m, sometimes as rectangular blocks [29].
- **Shape and scale:** roughly rectangular blocks from 0.3 × 0.3 m to 3 × 3 m (0.1-10 m²) [1][2]. LTPP rates it only once it extends at least 15 m [1]. Crack widths follow the LTPP bands [1].
- **Progression:** V2 L in lots and paths → V3 M → V4 H, spalled.
- **Interactions:** cracks are often sealed, giving networks of overbands ("tar snakes", 4.16); vegetation in old wide cracks (4.23).
- **Signature per map:** as for 4.8, on a rectangular pattern of larger cells.
- **Severity scale:** by crack width, LTPP [1] and PAVER [2].
- **Sources:** [1][2][29][32]

### 4.10 Transverse (thermal) cracking
- **Mechanism:** thermal contraction at low temperature. In interior Alaska the whole top 2 m of the embankment takes part [28]. Usually not load-associated [2].
- **Acts on:** the full pavement depth. **Removes / adds:** a gap; edge spalling later. **Reveals:** darker crack walls [32], and dirt or water in the gap.
- **Never:** is load-confined or wanders along the lane. Never forms with spacing finer than the block or fatigue range unless the base is cement-treated (2.4-6 m [29]).
- **Where:** "predominantly perpendicular to pavement centerline" [1], across lanes and shoulders. M-H cracks usually span the full width; L cracks may stop partway, starting at an edge or joint (est.). Transverse cracks are usually the first cracks a pavement shows [26].
- **Shape and scale:** spacing 23.6 ± 10.3 m (interior Alaska) [28]; 2.4-6 m over cement-treated bases [29]. Straight overall with a meandering path and some branching (est.). Cracks open in winter and close in summer, moving 14 mm a year on average in Alaska; crack edges sit 11-12 mm higher in February than in June [28].
- **Progression:** V1 hairline → V2 L, often sealed → V3 M with secondary cracks and spalls → V4 H, with a depression or potholes at the crack [28].
- **Interactions:** water enters at cracks, weakening the base and causing local depressions and potholes [28]; sealing (4.16).
- **Signature per map:** height: V-groove; frost lip at the edges in the winter preset only (`deform`); albedo: crack walls in fresh-binder colour; spalled shoulders at M-H.
- **Severity scale:** LTPP width ≤6 / 6-19 / >19 mm [1]; PAVER <10 / 10-75 / >75 mm [2].
- **Sources:** [1][2][26][28][29][32]

### 4.11 Longitudinal cracking and joint deterioration
- **Mechanism:** in WP, early fatigue, bottom-up or top-down [2][49]. Outside WP: a poorly built paving-lane joint, shrinkage, or reflection of a crack below [2].
- **Acts on:** the surface course, along the joint or WP. **Removes / adds:** a gap; raveling of low-density joint material [17][18]. **Reveals:** darker walls of the same mix.
- **Never:** wanders across lanes at random. Joint cracks never move off the joint footprint.
- **Where:** WP cracks inside or at the edges of the 1.0 m strips; non-WP cracks mostly on the paving joint beside the lane line or centreline [17][18]. LTPP rates the two separately because location matters [1].
- **Shape and scale:** long, nearly straight lines along V; joint raveling forms a band along the joint (est.: up to the 0.3 m notched-wedge taper width [17]).
- **Progression:** V2: L joint crack or open seam → V3: M with joint raveling → V4: H, spalled; WP cracks become fatigue (4.8).
- **Interactions:** WP longitudinal cracks with random cracking are rated as fatigue [1]; joint raveling leads to potholes along the seam (est.).
- **Signature per map:** dark line on the joint; coarser, lighter texture along the low-density cold side (est.).
- **Severity scale:** LTPP width bands [1]; PAVER [2].
- **Sources:** [1][2][17][18][49]

### 4.12 Reflection cracking
- **Mechanism:** movement of joints or cracks in an underlying layer (PCC slab joints, cement-treated base shrinkage cracks, old asphalt cracks) cracks the overlay above them [1][2][29].
- **Acts on:** the overlay. **Removes / adds:** a gap. **Reveals:** darker walls; at high severity, broken edges.
- **Never:** appears where nothing lies beneath. To identify reflection cracks at joints, the slab dimensions beneath must be known [1].
- **Where:** directly above the underlying joint grid or cracks; transverse and longitudinal [1].
- **Shape and scale:** follows the slab grid (est.: typical US jointed-slab spacing 4.5-6 m) or the 2.4-6 m cement-treated-base pattern [29]. Over cement-treated base, cracks <3 mm can be left alone; >6 mm need treatment [29].
- **Progression:** V1-V2 on overlays; widening and spalling at V3-V4.
- **Signature per map:** as 4.10, but on a grid locked to the hidden layer.
- **Severity scale:** LTPP [1]; PAVER <10 / 10-75 / >75 mm [2].
- **Sources:** [1][2][29]

### 4.13 Edge cracking, edge breakup and lane/shoulder drop-off
- **Mechanism:** loss of edge support and frost-weakened base or subgrade near an unpaved edge [1][2]; shoulder erosion or settlement [2].
- **Acts on:** the outer 0.3-0.6 m of pavement. **Removes / adds:** a gap, then breakup and material loss. **Reveals:** crack walls, then the binder course and base at the broken edge.
- **Never:** occurs where there is a curb or paved shoulder; LTPP applies it only to unpaved shoulders [1].
- **Where:** within 0.6 m of the edge [1] (0.3-0.5 m [2]): rural roads, driveways and paths.
- **Shape and scale:** crescent-shaped or fairly continuous cracks meeting the edge [1]. Drop-off L 25-50, M 50-100, H >100 mm [2].
- **Progression:** L no breakup → M breakup and loss on up to 10 % of its length → H on more than 10 % [1].
- **Signature per map:** ragged edge, crescent cracks, step down to the shoulder; base visible in the breakup (export `edge_break`); edge vegetation (4.23).
- **Severity scale:** LTPP L / M / H [1]; PAVER drop-off depth [2].
- **Sources:** [1][2]

### 4.14 Potholes and delamination
- **Mechanism:** moisture, freeze-thaw, traffic and poor support [27]. Pieces of high-severity fatigue cracking, or broken crack edges, are plucked out [2][28].
- **Acts on:** the wearing course, then the binder course, then base. **Removes / adds:** removes bound material. **Reveals:** whatever layer lies at that depth in the stack (`layer_index` from the section 2 thicknesses [11]); base only below all bound layers [1][11].
- **Never:** is a smooth round bowl with a soft rim. Never shows base colour in a hole shallower than the bound layers. Never has a plan dimension under 150 mm [1].
- **Where:** WP (from fatigue), at transverse cracks and joints [28], at raveled areas and edges [2]; repeated on the same weak spots (est.).
- **Shape and scale:** bowl-shaped, "generally ... sharp edges and vertical sides near the top", usually <760 mm across [2], minimum 150 mm [1]. PAVER rates by diameter (100-200 / 200-460 / 460-760 mm) × depth (13-25 / 25-50 / >50 mm) [2]. Profile (est.): the top 10-30 mm near-vertical, then a 30-60° bowl. Potholes cluster and stop growing after a while (CEDR POTHOLE). The outline follows broken crack pieces (est.); debris and water collect in the bottom (est.). A thin overlay (≤38-50 mm [20]) can instead lose its whole lift at the tack-coat interface: a flat-floored, sharp-edged area that shows the older, lighter surface (est.).
- **Progression:** V3: a few L-M potholes → V4: M-H, merging, many patched.
- **Interactions:** patched (4.15); bottom fills with water (4.24).
- **Signature per map:** height: deep, steep-walled; AO strong; albedo: black walls, floor of debris (grey) or base; wet: water-filled.
- **Severity scale:** LTPP depth L <25, M 25-50, H >50 mm [1]; PAVER diameter (100-760 mm) × depth (13-50+ mm) matrix [2].
- **Sources:** [1][2][11][20][27][28]

### 4.15 Patches
- **Mechanism:** maintenance replaces material within a footprint at a known time [1][27].
- **Acts on:** the patch footprint, which becomes a maintenance-layout feature. **Removes / adds:** replaces the old pavement with new mix: a new envelope inside the footprint, crowned 0 to +6 mm [27]. **Reveals:** new black mix, similar to a newly paved road [32].
- **Never:** spreads beyond its footprint. A saw-cut or milled patch never has soft, blobby edges. Never keeps the cracks or sockets of the pavement it replaced. Distresses inside a patch count as part of the patch [2].
- **Where:** over potholes, fatigue areas (WP), utility cuts and edges.
- **Shape and scale:** methods from [27]:
  - **Throw-and-roll:** cold mix dumped and compacted by truck tyres to a 3-6 mm crown; irregular outline that follows the hole.
  - **Edge seal:** the same, plus a ribbon of tack along the patch edge, sanded.
  - **Semi-permanent:** sides squared to vertical in sound pavement with a saw or cold mill, compacted by plate or roller; rectangular and flush.
  - **Spray injection:** tack, then binder and aggregate blown in and covered with loose aggregate; no compaction.

  Minimum area is 0.1 m² [1]. Rectangles align with the lane (est.).
- **Progression:** fresh patch black on grey (strong contrast); it then follows the 4.1 curve from its own placement date (est.). Seams crack and open from V3 (est.). Patches on patches appear in V4.
- **Interactions:** patch seams are weak joints (est.); LTPP severity includes rutting in the patch, L <6, M 6-12, H >12 mm [1].
- **Signature per map:** height: crown or flush, with a sharp seam line; albedo darker than older surroundings; roughness lower when fresh (est.); cold mix finer-textured (est.).
- **Severity scale:** LTPP L / M / H [1]; PAVER L / M / H [2].
- **Sources:** [1][2][27][32]

### 4.16 Crack sealing and filling
- **Mechanism:** maintenance places material in or over cracks. Crack sealing targets working cracks (mostly transverse), 5-19 mm wide; crack filling targets non-working cracks (longitudinal, block), 5-25 mm wide [26]. Many or badly deteriorated cracks are not sealed: that pavement is past crack sealing [26].
- **Acts on:** cracks. **Removes / adds:** adds rubberized asphalt, black, about 5 % reflectance [32], above the envelope (overband) or in the crack (fill). **Reveals:** nothing; it covers the crack.
- **Never:** appears without a crack beneath it. Never forms a band wider than about 125 mm in band-aid form [26] (hand pours vary, est.). Never sheets over a fatigue area (est. from [26]).
- **Where:** transverse cracks at their spacing, joints, longitudinal and block cracks. Fatigue areas are patched; sealed fatigue cracks are width fills at most (est.).
- **Shape and scale:** configurations [26]:
  - **Flush fill:** level with the surface.
  - **Reservoir:** routed 12-19 mm wide and deep, then filled flush or slightly recessed.
  - **Overband (band-aid):** 75-125 mm wide, 3-6 mm thick, squeegeed.
  - **Capped:** left to self-level.

  Fresh sealant may be "blotted" with sand or limestone dust [26], giving it a grey dusted top.
- **Progression:** V2: fresh, glossy black bands → V3: dusted, matte, worn through in WP (est.), with ruptures above the crack edges [26] → V4: pulled out in places (est.). Life is 2.5-9 years by material and configuration; fibre materials last ≤2 years [26].
- **Interactions:** overbands "detract from the general appearance" [26]; they track onto tyres if opened to traffic early [26].
- **Signature per map:** height: overband +3-6 mm with feathered edges, fills 0 to −2 mm (est.); albedo black, dusted grey later; roughness 0.25-0.45 fresh, rising as dust embeds (est.).
- **Severity scale:** LTPP counts a sealed crack in good condition as low severity [1].
- **Sources:** [1][26][32]

### 4.17 Pumping and water bleeding
- **Mechanism:** water seeps or is ejected through cracks under load, carrying fines from the support layers that "stained the surface" [1].
- **Acts on:** base and subgrade (fines removed), surface (deposit). **Removes / adds:** adds a fines stain on the surface. **Reveals:** nothing directly.
- **Never:** appears without cracks or joints. Never far from WP or edges (est.).
- **Where:** at high-severity fatigue cracks [1] and joints.
- **Shape and scale:** fan- or line-shaped light stains along cracks (est.: colour of base or subgrade fines), dark while wet.
- **Progression:** V4.
- **Signature per map:** albedo toward soil colour in a 50-300 mm halo (est.); roughness up; no height.
- **Severity scale:** none; recorded as length [1].
- **Sources:** [1]

### 4.18 Road markings: wear and ghosting
- **Mechanism:** markings are deposits. Tyres and snowplough blades abrade them, and removal by grinding or blasting scars the pavement [46].
- **Acts on:** the marking layer (D). **Removes / adds:** removes marking material inside its footprint. **Reveals:** the same wearing course, less weathered than the open surface (est.: shielded from sun and tyres). Removal leaves "color change and texture change" [46].
- **Never:** extends or moves the footprint. Never paints over sealant and new patches as if they were not there (markings are reapplied after maintenance, est.).
- **Where:** where tyres cross markings: WP crossings of stop bars and crosswalks (FHWA recommends crosswalk-bar spacing that avoids WP [47]), lane-change zones on skip lines, and turning paths (est.). Lane lines wear mostly from ploughs on raised thermoplastic tops and edges (est.).
- **Shape and scale:**
  - **Paint:** 0.38 mm wet per coat, final lines often two coats [8]; dry ≈0.2 mm per coat (est.: about half the wet film). Comparable to the 0.4-0.6 mm MTD of dense mixes [20], so it follows the texture and wears first off the stone tips that tyres touch, leaving paint in the valleys (est.).
  - **Thermoplastic:** 2.3-3.0 mm proud [8]; extruded molten, so it fills valleys under a flat top (est.).
  - **Recessed:** grooved into the surface (est.: 2-3 mm) so the marking sits flush or slightly below and survives ploughing [18].
  - **Beads:** 0.3-0.85 mm, about 60 % embedded [8][9].
- **Progression:** V0 crisp → V1-V2 bead loss and wear in WP crossings → V3 speckled or partial lines, cracks reflected through thermoplastic (est.) → re-striping offset from old lines creates ghosts. Agencies may cover leftover lines with black paint up to twice the line width, without defined edges [8].
- **Signature per map:** height: paint follows the surface; thermoplastic has a flat top with rounded edges (est.: 1-2 mm radius). Albedo: section 7. Roughness: beads give a sparkle speckle. Ghosts: a texture and colour scar in the old footprint [46].
- **Severity scale:** none; agencies use retroreflectivity minimums, e.g. 375 mcd/lux/m² white at install [8].
- **Sources:** [8][9][10][18][20][46][47]

### 4.19 Sealcoat (lots and driveways)
- **Mechanism:** a "black, shiny" emulsion painted or sprayed on asphalt. Tyres abrade it, wear is "visible in high traffic areas within a few months", and it is reapplied every 2-3 years [39].
- **Acts on:** deposit over L0. **Removes / adds:** adds a black film; traffic removes it. **Reveals:** the older, lighter grey asphalt beneath.
- **Never:** wears first in stalls; it wears first in drive aisles, stall entries and turning areas (est. from [39]).
- **Shape and scale:** covers the whole lot including cracks; worn lanes show grey stone tips through black (est.).
- **Signature per map:** albedo near black, linear 0.03-0.05 (est.); roughness 0.35-0.55 fresh (est.); no measurable height (est.).
- **Sources:** [39]

### 4.20 Oil, fuel and fluid drips
- **Mechanism:** vehicles drip engine oil, fuel and hydraulic fluid. Bitumen is soluble in petroleum solvents: spilled fuels and oils soften the binder so the pavement "disintegrate[s] and erode[s]" [42]. Oil lowers reflectance [32].
- **Acts on:** L0-L1 (stain); at heavy, repeated dosing, the whole wearing course (softening, raveling) [42]. **Removes / adds:** adds a stain; can then remove material. **Reveals:** raveled sockets in old heavy stains.
- **Never:** spreads uniformly over the lane. It concentrates where vehicles idle or park.
- **Where:** the lane centre between the wheel paths, which is "coated with oil thrown from cars" [44]; busy intersections, climbing lanes and toll plazas [42]; parking stalls at engine position (est.: centred across the stall, about 0.6-2.0 m in from the head end for nose-in parking); driveways at the garage end (est.).
- **Shape and scale:** drops 20-100 mm (est.) that merge into 0.3-1 m stains in stalls (est.); a diffuse band in the 0.75 m lane centre [3][44].
- **Progression:** V1 faint centre band → V2 visible band and stall stains → V3-V4 softened, pitted stains in stalls (est.).
- **Signature per map:** albedo down; roughness down while fresh (est.: 0.3-0.5); old stains matte and dark brown-black (est.); vary each stall's stain from its stall ID.
- **Sources:** [3][32][42][44]

### 4.21 Tyre marks
- **Mechanism:** sliding tyres deposit rubber. Skid marks come from hard straight-line braking; yaw marks from tyres sliding sideways on a curved path [43].
- **Acts on:** surface (deposit, no thickness). **Removes / adds:** adds rubber. **Reveals:** nothing.
- **Never:** appears as a uniform darkening of the wheel paths; marks are discrete events.
- **Where:** approaches to intersections, curves, parking-lot turns (est.).
- **Shape and scale:** a band one tyre wide (est.: 150-300 mm passenger cars), metres long. Striations follow tread shoulder blocks: perpendicular to the tyre heading without braking, parallel to the mark under lock-up [43].
- **Signature per map:** albedo: tyre linear 0.023 [35], so the marks are darker than aged asphalt and nearly invisible on fresh asphalt (est.); roughness about 0.7 [35] (dataset value, est.); fades with weathering (est.).
- **Sources:** [35][43]

### 4.22 Dirt, debris and fines
- **Mechanism:** traffic, wind and runoff carry soil and wear particles to low, low-traffic places (est.).
- **Acts on:** deposit (D). **Removes / adds:** adds sediment. **Reveals:** nothing; it hides texture.
- **Never:** accumulates on WP stone tips (est.: tyres sweep them).
- **Where:** 90 % of street-dirt mass lies within 0.3 m of the curb, and the curb lane (within about 0.9 m of the curb) holds 75-77 % [40]; the 90 % figure is Pitt and Amy (1973), quoted in [40]. Also macrotexture valleys, cracks, sockets, potholes (est.), stains outlining dried bird baths [2], pumping stains [1], loose stones near raveling [32], and the clogged pores of OGFC [25].
- **Shape and scale:** particles mostly 0.25-1 mm [40], so at lane scale it reads as a soft gradient; it fills valleys first (est.).
- **Signature per map:** albedo toward soil (est.: linear 0.12-0.30), lighter than weathered asphalt; roughness 0.9-1.0 (est.); height: fills valleys (deposit mask).
- **Sources:** [1][2][25][32][40]

### 4.23 Vegetation
- **Mechanism:** plants root in soil and fines trapped in old, wide cracks and joints where traffic is light (est.); an older crack holding green vegetation is a distinct spectral feature [32].
- **Acts on:** cracks and edges (deposit above envelope). **Reveals:** nothing.
- **Never:** grows in WP of trafficked lanes or in hairline cracks (est.).
- **Where:** M-H cracks in lots, paths and driveways; pavement edges, curb lines and joints (est.); LTPP lists weed growth in joints as seal damage [1]. Subgrade sterilant is used to prevent it [13].
- **Signature per map:** green, high roughness, small height above the surface; follows crack lines.
- **Sources:** [1][13][32]

### 4.24 Wetting, puddles and drying
- **Mechanism:** a water film over rough asphalt adds a mirror-like water surface (IOR 1.33 [35], so F0 ≈ 0.02) and darkens the diffuse albedo: light scattered by the rough surface is trapped by total internal reflection in the film and absorbed [38].
- **Acts on:** surface (state change, not material). **Reveals:** nothing.
- **Never:** pools on crowns or crests; never a uniform gloss over a textured surface while only damp (est.).
- **Where:** puddles in ruts ("noticeable only after a rainfall when the paths are filled with water" [2]), depressions and bird baths [2], lots with <2 % slope [13], potholes and raveled pits [14]. OGFC drains, so it shows little film or glare until clogged [25].
- **Shape and scale:** a water plane at the spill level of each low area (est.). When damp, valleys hold water while stone tips dry first (est.). Unrutted WP dry first (est.: tyres expel water); rutted WP dry last.
- **Signature per map:** diffuse albedo × about 0.50 for dark asphalt, × 0.55-0.6 for light stone and × 0.78 for white paint under a continuous film (computed from the model in [38], section 7); roughness 0.02-0.08 in puddles and 0.3-0.5 damp (est.).
- **Sources:** [2][13][14][25][35][38]

### 4.25 Surface-type specifics: chip seal, OGFC, SMA
- **Chip seal [24]:**
  - *Stack and as-built height:* one stone thickness of single-size chips (FA-3: median 5.5 mm, ALD 3.75 mm; FA-2 <6.3 mm) about 70 % embedded in the residual binder, over the old surface. Chips stand about 0.3 × ALD proud (est.), MTD >1.0 mm [20]. Traffic lays flat chips on their flattest side in the WP, so the seal is thinner there and binder rises toward the chip tops: darker WP, and bleeding if binder is heavy. A chip laid flat also covers more area in plan (its long and intermediate axes now lie flat, where a chip on edge shows long × least), so the binder between chips shrinks in the WP for two reasons. Model reorientation as a lower top *and* a larger footprint (est.: area × intermediate ÷ least dimension, capped where neighbours touch); the chip footprint is not a layout invariant, and only chip loss deletes chips. Off the WP and at the centreline the chips stand taller and are less embedded.
  - *Chip loss* (removal): whole chips pulled out by traffic and snowplough blades, down to the black membrane (socket ≈ ALD deep), then the membrane wears through to the old surface (lighter grey) or a granular base. It concentrates in the non-wheel-path areas and along the centreline seam; one unfogged section lost about 15 % of its chips along the centreline. Causes: too little binder, dusty chips, binder breaking before rolling, a poorly rolled centreline seam, plough down-pressure.
  - *Fog seal* (deposit): MnDOT fog-seals all chip seals except on residential streets; the diluted emulsion locks chips, adds embedment and makes the road look like new HMA. It wears off chip tips first and the surface lightens toward the chip colour (est.).
  - *Construction marks:* longitudinal streaks (ridges and lean bands) from a wrong spray-bar height or misaligned or plugged nozzles; rough, very dark transverse spots at distributor starts and stops.
  - *Colour:* unfogged new chip seal has the aggregate's albedo (solar 0.20 in San Jose), falling to about 0.12 in 5 years on trafficked urban streets, where scrubbing did not restore it [30] (traffic soiling; slower on low-traffic roads, est.). Hand-made samples with binder showing reached two-thirds of the aggregate's albedo [30].
  - Rural shoulders, rumble strips and edge drop-off on chip-sealed roads are not covered here; research them live.
- **OGFC [25]:** raveling is the main failure and progresses rapidly; about 55 % of localised raveling starts at transverse joints. Dust and silt clog the voids. GDOT's PEM lasted 6-8 years before raveling, while lime-treated OGFC lasts 12+ years. OGFC cuts glare and splash and is about 3 dB quieter when new. The underlying dense layer appears where it ravels.
- **SMA [11][37]:** a specular factor clearly above AC [37]; reflective cracks spall less than in dense mixes [11]. Rich mastic can show as fat spots where binder drained down, anywhere on the mat (est. from the draindown concern in [11]).

### 4.26 Preservation films: fog seal, slurry seal, microsurfacing
- **Mechanism:** a thin black layer sprayed or spread over aged asphalt: a fog seal is diluted emulsion with no aggregate [24]; slurry seal and microsurfacing add fine aggregate (MTD 0.3-0.6 and 0.5-1.0 mm [20]).
- **Acts on:** deposit over L0-L1. **Adds:** a black film or a fine-textured mat that fills the old macrotexture. **Reveals (when worn):** the older, lighter surface; WP tips first (est.).
- **Never:** hides cracks for long; old cracks reflect through within a few years (est.). Never adds measurable height for a fog seal (est.).
- **Signature per map:** albedo resets to near fresh (est.: linear 0.04-0.06); slurry and microsurfacing replace the coarse texture with a fine, sandy one; roughness 0.5-0.7 fresh (est.).
- **Sources:** [20][24]

### 4.27 Scuffing (est.)
- **Mechanism:** tyres twisted at low speed under power steering scrub the surface, tearing mastic and loosening stone, worst on fresh or hot asphalt and on sealcoat (est.).
- **Acts on:** L0-L2. **Removes:** mastic and loose stone. **Reveals:** the same mix.
- **Where:** parking-lot stall entries, turning areas, cul-de-sacs and driveway ends (est.).
- **Shape and scale:** curved arcs and fans one tyre wide (est.: 150-300 mm), coarser and lighter than the surround, with black smears on fresh asphalt (est.).
- **Sources:** none found; whole card (est.).

## 5. Invariants

Region names refer to the `regions` block in section 9.

**I1. The layout is fixed.** Lane lines, marking footprints, joints, wheel-path strips, stall stripes, patch outlines and any underlying slab grid are identical with and without wear. *Why:* they are set at construction or maintenance, and wear removes material inside them without moving them (section 1). *Enforce:* these masks come only from the layout generators (lane U-gradient, stall grid, patch layout pass). Damage nodes may read them but never feed them, and damage warps never touch them. The joint mask is separate from the marking mask. The `nowear` render keeps the maintenance layout (patches as placed). *Check:* `mask_invariance` on wheelpath, centre, marking, joint, patch against `nowear`, `max_changed_frac` 0 (hard; exclude shove regions, 4.7). On the detail tile, the same for aggregate.

**I2. Removal only goes down.** Weathering, raveling, cracks, potholes, wear ruts and chip loss never raise the surface; only deposits sit above the reference. *Why:* these processes remove material (section 3). *Enforce:* compose height as envelope E → patch placement (E′) → min() removals with a per-pixel age → + deformation field → max() deposits. `nowear` = E′ + the same deformation field + as-built markings, exported with the same height range and offset. Export `deposit` as the union of the deposit masks. *Check:* `envelope` against `nowear` with `except` ["deposit"], `tolerance_mm` 0.1 (hard), on each tile.

**I3. Wear reveals the same course, and base appears only in deep holes and broken edges.** Weathering and raveling expose more wearing-course mix; the binder course and base appear only where a hole is deeper than the layers above them, or at an edge breakup. *Why:* disintegration runs from the surface downward [14], and the bound layers lie between the surface and the base [11]. *Enforce:* pick floor material from depth with a layer-index map built from the stack's thicknesses (section 10), never from a noise. *Check:* `coverage` of base_outside within all = 0 (hard). For a surface treatment on a granular base, add the `seal_loss` mask to base_outside's `not` list. Detail tile: `height_diff` socket − mastic, `local_mm` 50, median, within [−1.5 × NMAS, −1] mm.

**I4. Exposed stones never sit below the mastic around them.** *Why:* weathering removes the matrix first, so stones stand proud until they are plucked out whole [2]. *Enforce:* height = max(stone field, mastic level); weathering lowers only the mastic level; raveling deletes whole stones by stone ID. The `aggregate` mask is the as-built exposed stone (stone footprint where the stone stands above the mastic in the `nowear` branch), exported from that branch, so it never reads the worn height. *Check:* `order` upper = agg, lower = mastic, `lower_stat` p50, `neighborhood_mm` 25, `max_violation_frac` 0.02 (hard, detail tile). `height_diff` agg − mastic follows the protrusion targets in section 9.

**I5. What lies beneath is darker, and age lightens (dense HMA).** Crack walls, fresh patches and fresh sealant are darker than the weathered surface; the surface gets lighter with age. Raveled areas as a whole are the exception: loose and exposed stone makes them brighter [32]. Stacks where the layer beneath is older or mineral reverse the rule (section 3: overlays, chip seal, sealcoat, fog seal). *Why:* the surface binder oxidises and wears off the stones, while deeper and newer binder is less aged [30][32][50]. *Enforce:* drive basecolor from an age-dependent "surface exposure" term applied to L0-L2 only. Crack walls and new patches take the fresh-binder colour; raveled areas mix exposed-stone colour and loose debris. *Check:* `value_order` basecolor luma median [crack_wall, surface] ascending (V2+), [sealant, surface] ascending (V2, fresh sealant only), [surface, ravel] ascending (V3+). `value_range` of surface luma per variant (section 9).

**I6. Load damage stays in the wheel paths.** Fatigue cracking, ruts and polishing lie inside the WP strips, plus up to about 150 mm of lateral wander; bleeding usually does [1]; block and thermal cracking ignore them. *Why:* they need repeated wheel loads [1][2]. *Enforce:* multiply these damage drivers by a softened WP mask whose blur extends ≤150 mm beyond the strip (est.: lateral wander). *Check:* `coverage` of fatigue within nwp_core ≤ 0.002 (hard, `min_px` 1000). Bleeding: `concentration` of bleed in wp ≥ 5 (soft; not for SMA fat spots or seal over-application). Ruts: rut_depth (section 9).

**I7. Ruts are smooth troughs, not cuts.** *Why:* deformation ruts bend the whole structure [2][15]; stud-wear ruts are worn gradually by many passes (est.). *Enforce:* deformation: a low-frequency displacement (one trough per WP, about 1.0 m wide, optional shoulders) in the `deform` field, never in the layer index. Stud wear (4.6 b): a removal by min() into height and `layer_index`, about 0.4-0.7 m wide, with a coarser, lighter floor. *Check:* `height_diff` wp_s − centre_s, `local_mm` 1500, median, per variant. `slope` on rut_flank (WP edges with cracks, potholes, patches, sockets and markings removed), p90 ≤ 8° (est.), `min_px` 2000.

**I8. Crack width is a severity band, and every open crack has walls.** *Why:* width comes from crack opening (LTPP ≤6 / 6-19 / >19 mm [1]); edges degrade by spalling only at M-H [1][2]. *Enforce:* draw cracks as a mask with a set mouth width per severity, a V-profile and fresh-binder walls; add spall shoulders only at M-H. Keep height cracks ≥3 px. *Check (lane tile):* `run_length` crack_open, `axis` both, `max_mm` 40, p50 within the variant band (section 9: the bands allow for the 3 px floor and for diagonal scanlines); `slope` between [crack_open, surface], `band_mm` 3, p50 ≥ 45°.

**I9. Each crack family keeps its geometry.** Transverse cracks cross the lane, perpendicular to traffic; longitudinal cracks run along joints or WP; fatigue polygons are under 0.3-0.5 m; blocks are 0.3-3 m [1][2][28]. *Enforce:* build each family from its own generator (warped lines across the lane; joint and WP lines; Voronoi cells masked to WP; a larger cell pattern) and export a mask per family. *Check:* `orientation` crack_t `axis_deg` 0, tolerance 15, ≥ 0.7 (lane + crack tile); crack_l `axis_deg` 90, tolerance 10, ≥ 0.8; V2 fatigue_lines `axis_deg` 90, tolerance 20, ≥ 0.6; V3-V4 `components` fatigue_cells eq_diameter p50 60-300 mm; block_cells 300 mm to half the tile.

**I10. Sealant sits only on cracks.** *Why:* it is placed in or over existing cracks [26]. *Enforce:* derive the sealant band by dilating the final crack mask (37-62 mm a side for overbands) and select which cracks are sealed by crack ID; never band a fatigue area. *Check:* `coverage` of sealant_stray within all ≤ 0.0005 (hard); `run_length` sealant, p50 75-125 mm (overbands); `height_diff` sealant − surface by configuration.

**I11. Markings sit on the surface and wear only inside their footprint.** *Why:* they are deposits 0.2-3.0 mm thick [8], and tyres wear them where they cross [47]. *Enforce:* marking material = footprint × (1 − wear), with wear driven by the WP mask (transverse markings), plough wear (raised lines) and texture peaks. Height = surface + thickness (paint) or max(surface, local peak + thickness) (thermoplastic); recessed markings sit in a groove cut by min(). *Check:* `mask_invariance` of marking (I1); `height_diff` marking_material − surface per type; `value_order` basecolor [marking_wp, marking_nwp] ascending (V2+) on crosswalk or stop-bar tiles only (on the lane tile marking_wp is empty).

**I12. Potholes are sharp, at least 150 mm across, and floored by the right layer.** *Why:* LTPP and PAVER definitions [1][2]; layer depths [11]. *Enforce:* pothole outlines grow from broken crack polygons; walls are steep near the rim; the floor uses the layer index (I3). *Check:* `components` pothole eq_diameter min ≥ 150 mm (`min_mm` 30 to drop anti-alias specks); `edge_profile` outer pothole, inner surface, `min_step_mm` 10, `peak_slope_deg` p50 ≥ 60°; `height_diff` pothole depth per variant.

**I13. Patches keep their footprint and their own age.** *Why:* a patch is new material placed at a known time [1][27][32]. *Enforce:* patch outlines from the maintenance layout pass (rectangles aligned to the lane for saw-cut patches; hole-shaped for throw-and-roll); the patch replaces the envelope before any removal step, and a per-pixel age map (age − patch age inside patches) drives all later aging, so patches weather, crack at their seams and take patches on patches. Cracks older than the patch are masked out inside it. *Check:* `height_diff` patch − patch_ring, `local_mm` 600, median −2 to +6 mm; `value_order` basecolor [patch, surface] ascending when the patch is newer.

**I14. Contamination follows traffic.** The lane centre is darker than the WP (oil [44]); WP are lighter (binder worn [37]; strongest where studded tyres are used); dirt gathers at curbs and in valleys [40]. *Enforce:* oil driver = centre mask × age; WP lightening = WP mask × age; dirt = curb distance × valley mask. *Check:* `value_order` basecolor luma median [centre_s, wp_s] ascending (V1+ roads; skip when bleeding covers >20 % of the WP); `value_order` on the dirt mask [lane_interior, curb_band] ascending when a curb is in the tile (export a `curb` mask; "curb_d": {"mask": "curb", "threshold": 0.5, "dilate_mm": 300}, "curb_band": {"and": ["curb_d"], "not": "curb"}, "lane_interior": {"not": "curb_d"}).

**I15. Water sits only in low places.** *Why:* water levels to the spill height of ruts and depressions [2]. *Enforce:* water mask = local height below a fill level inside rut and depression regions; output it as a mask, never as added height. The check constrains the water mask, not the height, so testing it against the height is not circular. *Check:* `order` upper = water_ring, lower = water, `lower_stat` p95, `neighborhood_mm` 500, `max_violation_frac` 0.05, `min_px` 2000 (wet preset); `value_range` roughness in water p95 ≤ 0.1.

**I16. Tiles read as pavement, not as a pattern.** *Why:* low-frequency blotches and repeated stains print a lattice. *Enforce:* blotch scales in whole fractions of the tile; per-stall and per-patch randomness from IDs. *Check:* `lowfreq` basecolor inside wp_s and inside centre_s separately (the lane banding itself is physics), `sigma_mm` [100, 300, 1000]; `seam` on all maps, hard (a strip tile that repeats only along the road uses `axis` for that direction); `normal_valid` directx; `height_usage` (16-bit, nothing clipped).

## 6. Common procedural mistakes

| Wrong (what procedural materials often do) | Right (physics) | How to fix it in the graph |
|---|---|---|
| "Aged" asphalt made darker with grime overlays | Dense asphalt lightens: visible 0.04 new → about 0.12 old [36] (solar 0.04-0.05 → 0.12-0.20 [30][31]); dark marks are local (oil, rubber, sealant, patches) | Drive an age term that raises surface luma; keep dark contributions in their own masks (4.20, 4.21, 4.16) |
| Fresh asphalt at sRGB 10-30 (near pure black) | Fresh asphalt is linear 0.042, sRGB 58 [36] | Clamp the fresh base to ≥ sRGB 55 |
| Raveling or "wear" reveals grey gravel or brown soil | Raveling exposes more of the same wearing course; base shows only in potholes deeper than all bound layers and at broken edges [11][14] | Layer-index floor material by depth (I3) |
| Alligator cracks spread across the whole lane | Fatigue cracking occurs only in the 1.0 m WP strips [1][2] | Multiply fatigue by the WP mask; use block cracking for traffic-free areas |
| One Voronoi crack pattern for every crack type | Each family has its own geometry: transverse across the lane every tens of metres, fatigue <0.3-0.5 m polygons in WP, blocks 0.3-3 m [1][2][28] | Separate generators and masks per family (I9) |
| Cracks as wide, rounded, eroded trenches | Cracks are narrow gaps (≤6 mm at L) with near-vertical walls; edges spall only at M-H [1][2] | Width per severity band, V-profile, spalls as a separate M-H term |
| Thin black lines inside cracks as "sealant" | Overbands are 75-125 mm wide, 3-6 mm proud, glossy black when fresh, then dusted and worn [26] | Dilate the crack mask for the band; add height; age gloss to matte |
| Glossy wheel paths labelled "polish" | Polish smooths stone tops only; at grazing view, wheel tracks are slightly less specular and lighter overall [37]. Glossy WP means bleeding [16] | Lower roughness on stone-top pixels only; use a bleed mask for glossy strips |
| Darker wheel paths from "tyre rubber" | WP are lighter (binder worn off tips); the lane centre is darker (oil drips) [37][44] | Value order centre < WP (I14) |
| Potholes as smooth round bowls with soft rims | Sharp edges and vertical walls near the top; ≥150 mm; outline follows broken pieces [1][2] | Grow outlines from fatigue cells; steep-wall profile; debris on the floor |
| Patches as soft-edged blobs the same colour as the road, pasted on after all aging | Saw-cut patches are rectangles with straight seams; throw-and-roll patches are crowned 3-6 mm; new patches are darker and then age and crack from their own date [27][32] | Patch layout pass before the removals, with type and age per patch ID and a per-pixel age map (I13) |
| Round, single-size "aggregate" blobs for every mix | Crushed, angular stone; coarse fraction 18-52 % (dense), 64 % (SMA), 86 % (OGFC); only chip seal is single-size [21][24] | Several Tile Sampler size classes with polygon shapes; target coverage per mix |
| Ruts drawn as grooves or as darker stripes | Deformation ruts are 1 m-wide smooth troughs, 6->25 mm deep, with shoulders in mix ruts; stud-wear ruts are narrower, smooth and lighter-floored; both hold water [2][15][48] | Displacement in `deform`, or a smooth min() for stud wear (I7); puddles in the wet variant |
| Pristine thermoplastic over cracks, or paint as a raised slab | Paint is about 0.2 mm per coat and follows the texture; thermoplastic is 2.3-3.0 mm with a flat top; both wear where tyres cross [8][47] | Conformal paint height; flat-topped thermo; wear driven by the WP mask |
| Uniform wet gloss and puddles anywhere | Puddles sit in ruts and depressions; damp asphalt is wet in valleys first; a film halves the diffuse albedo of dark asphalt [2][38] | Water mask from height (I15); albedo × 0.5-0.6 under film |
| Chip seal as a light, clean gravel texture everywhere | Most chip seals are fog-sealed black at first; chips are lost off the wheel paths and at the centreline; WP darker where binder rises [24] | Fog-seal deposit worn off tips; chip-loss driver = NWP + centreline seam (4.25) |
| Oil stains repeated at identical offsets in every stall | Each car drips differently, around the engine position (est.) | Stall-ID random offsets, sizes and ages |
| One tile showing a lane, stalls and dashed lines together | The 12.2 m dash cycle does not fit a lane tile [7] | Lane tile = lane width; dashes and arrows as decals |

## 7. PBR reference values

| Component / state | Albedo (sRGB 0-255 / linear) | Roughness | Notes | Source |
|---|---|---|---|---|
| Fresh dense HMA (binder film) | 58 / visible 0.042; RGB [0.043, 0.041, 0.040] | 0.5-0.65 (est.: smooth binder film over rough macrotexture) | measured visible (photopic); nearly flat spectrum; solar 0.04-0.05 agrees [30] | [30][36] |
| Young HMA (1-2 yr) | 63-80 / 0.05-0.08 | 0.65-0.85 (est.) | interpolated between new and old; WP tips lighten first | (est.) |
| Old / weathered HMA (≈5 yr+) | (98, 93, 80), luma 93 / visible 0.124; range 80-108 / 0.08-0.15 | 0.85-0.95 (est.) | measured "old black asphalt", warm (B/R 0.66) [36]; solar 0.12 at 5 yr [30], 0.15-0.20 weathered [31] | [30][31][36] |
| Late-aged, heavily worn | 85-124 / 0.09-0.20 (est.) | 0.9-0.95 (est.) | field reflectance 0.105-0.24 (350-2500 nm, includes NIR) [34]; exposed stone and debris dominate | [34] (est.) |
| Exposed coarse aggregate faces | 108-160 / 0.15-0.35 (est.) | 0.75-0.9; polished 0.55-0.7 (est.) | solar 0.20-0.40 on California aggregates [30]; visible taken lower because mineral surfaces absorb more in the visible [32]; traprock about 0.08-0.15 (est.) | [30][32] (est.) |
| Fines and sand (no binder) | 80-140 / 0.08-0.27 (est.) | 0.9-1.0 (est.) | solar 0.10-0.31 [30], visible taken lower | [30] (est.) |
| Chip seal, unfogged | new 108-124 / 0.15-0.20; 5 yr 89-97 / 0.10-0.12 (est.) | 0.8-0.9 (est.) | solar 0.20 → 0.12 (urban traffic soiling) [30]; visible taken at or below solar | [30] (est.) |
| Chip seal, fog-sealed | as fresh HMA, lightening as tips wear (est.) | 0.5-0.7 fresh (est.) | reads as new HMA | [24] (est.) |
| PCC slab under an overlay | (113, 109, 96) / visible 0.153 | 0.8-0.9 (est.) | measured concrete curb [36]; solar field 0.18-0.35 [30] | [30][36] |
| Crack sealant (rubberized) | about 63 / 0.05 | 0.25-0.45 fresh; 0.6-0.8 dusted (est.) | blotting with sand or limestone dust adds grey [26] | [26][32] |
| Bleeding binder | 48-63 / 0.03-0.05 (est.) | 0.15-0.35 (est.) | "shiny, glass-like" | [1][16] |
| Sealcoat or fog seal, fresh | 48-63 / 0.03-0.05 (est.) | 0.35-0.55 (est.) | "black, shiny" | [24][39] |
| New patch | as fresh HMA | 0.5-0.65 (est.) | similar to a newly paved road | [32] |
| White thermoplastic, new | ≥225 / ≥0.75 daylight reflectance; cap at 240 | 0.45-0.65 (est.); bead sparkle 0.05-0.15 (est.) | ≥10 % TiO2 | [10] |
| Yellow thermoplastic, new | luminance factor ≥0.45; blue absorbed | as white | | [10] |
| White street paint | new (212, 210, 189) / V 0.64; old (175, 167, 147) / V 0.39 | 0.6-0.8 (est.) | measured; slightly yellow (B < R) | [36] |
| Yellow street paint, old | (188, 146, 65) / V 0.33 | 0.6-0.8 (est.) | measured | [36] |
| Tyre rubber (skid marks) | 42 / 0.023 | 0.7 (dataset value) | | [35] |
| Oil stain | 48-69 / 0.03-0.06 (est.) | 0.3-0.5 fresh, 0.8-0.9 old (est.) | lowers reflectance | [32] |
| Unbound aggregate base | 108-150 / 0.15-0.30 (est.) | 0.9-1.0 (est.) | bare aggregate and fines; solar 0.10-0.40 [30] | (est.) |
| Dirt, soil | 97-149 / 0.12-0.30 (est.) | 0.9-1.0 (est.) | | (est.) |
| Water film or puddle | diffuse = dry × 0.50 (dark asphalt) to × 0.78 (white paint) | 0.02-0.08 (est.) | specular F0 = 0.02 (IOR 1.333) | [35][38] |
| Damp (water in valleys only) | area average dry × 0.6-0.8 (est.) | 0.3-0.5 (est.) | | (est.) |

Metallic is 0 everywhere, except metal utility covers (darker, iron-oxide features [32]). Roughness values are almost all (est.): the two dataset values (asphalt 0.5, tyre 0.7 [35]) are placeholders, not measurements.

**Measurement types differ:**
- **Solar reflectance** (LBNL pyranometer or solar-spectrum reflectometer, ASTM E1918 [30]; field spectra 350-2500 nm [34]) includes the near-infrared. For fresh and old asphalt it about equals the measured visible value (0.042 vs 0.04-0.05; 0.124 vs about 0.12) [30][36]. For mineral surfaces (aggregate, sand, concrete) it overstates the visible value: concrete measures 0.15 visible [36] against 0.18-0.35 solar [30], and aged asphalt's extra reflectance is largest in the NIR and SWIR [32].
- **Visible values** are photopic V(λ) reflectances and linear RGB from spectrophotometer measurements [36]. Use visible values for basecolor; physicallybased.info's fresh asphalt [35] is the same measurement as [36], not an independent one.
- **Road-lighting Q0** (Finnish mean 0.093 [37]) is a luminance coefficient seen at about 1° grazing, not an albedo. A Lambertian surface of albedo 0.12 would give only about 0.038 (ρ/π), so real asphalt scatters strongly forward at grazing angles (est.). Do not set asphalt roughness to 1.0.

**Wet values** come from the Lekner-Dorf model (p = 0.475 for water, mineral n = 1.5) [38], computed for this sheet. Dry → wet diffuse: 0.05 → 0.025; 0.12 → 0.061; 0.30 → 0.170; 0.75 → 0.583. The water surface adds a specular lobe with F0 = 0.02. This is the full-film case; damp surfaces darken less.

## 8. Variants and presets

**Variant ladder (dense HMA road; lots in brackets)**

| Variant | Age | Processes and stage |
|---|---|---|
| V0 fresh | 0-6 months | 4.1 black film everywhere; as-built segregation spots and joints; crisp markings; no cracks; MTD per mix (section 2) |
| V1 young | 1-2 yr | 4.1 dark grey, WP tips lighter; 4.2 L; 4.10 hairline transverse cracks (decal or crack tile); 4.20 faint centre oil band; 4.21 occasional tyre marks; ruts <5 mm; bead loss on markings [sealcoat worn in aisles] |
| V2 weathered | 3-7 yr | 4.1 grey; 4.2 M; 4.3 isolated sockets at segregation and joints; 4.4 starting; 4.10 L-M, sealed with fresh-to-dusted overbands (4.16); 4.11 L joint crack; 4.8 L lines in WP; ruts 5-10 mm; markings worn at WP crossings; dirt at curbs [4.9 L block cracking, stall oil stains, 4.27 scuffs] |
| V3 distressed | 8-15 yr | 4.2 H; 4.3 M; 4.5 in WP (hot climates); 4.8 M cells in WP; 4.10 M with spalls; 4.11 joint raveling; 4.12 on overlays; 4.14 a few L-M potholes; 4.15 patches of mixed ages, seams opening; ruts 6-13 mm; 4.13 on rural edges [4.9 M; 4.23 grass in wide cracks] |
| V4 failed | >15 yr or neglected | 4.3 H; 4.8 H with 4.17 pumping; 4.14 M-H, base only where a hole passes every bound layer; patches on patches; ruts 13->25 mm; 4.7 shoves at intersections; 4.6 depressions with bird-bath stains; 4.23 along edges and cracks |

Frost lips (4.10) belong to a winter preset only; summer variants keep 0-3 mm of residual cupping (est.).

Other surface types shift the ladder and need their own luma targets (section 9). Fog-sealed chip seal starts black and lightens as the fog wears off; unfogged chip seal starts at the aggregate's colour and darkens; both lose chips off the WP and at the centreline (4.25). OGFC ravels from transverse joints and clogs (4.25). SMA shows more specular mastic and less crack spalling. Sealcoated lots reset to black every 2-3 years [39].

**Interview questions (recommended default in bold)**
1. Setting: **road lane**, parking lot, driveway or path?
2. Surface type: **dense-graded 12.5 mm HMA**, 9.5 mm (city streets, drives), SMA (highways), OGFC (warm-climate highways) or chip seal (rural, low volume; fog-sealed or not)?
3. Aggregate colour: **mixed grey limestone/granite** (the US majority [41]), dark traprock, pink granite or light limestone?
4. Variant: V0-V4? **V2 weathered.**
5. Climate: **freeze-thaw** (transverse cracks, potholes; frost lips only in a winter preset), hot (bleeding, rutting, fast fading) or mild?
6. Studded tyres: **no**; yes gives worn, lighter, coarser wear ruts in the car tracks (4.6 b) and stronger WP lightening.
7. Traffic: **moderate with trucks**, light residential (block cracking, little rutting) or heavy (ruts, fatigue)?
8. Maintenance: **cracks sealed with overbands from V2**, mixed patch types, sealcoat on lots every 2-3 years [39]?
9. Markings: **solid lines in the tile at U = 0/1, dashes and symbols as decals**; paint, thermoplastic or recessed; US MUTCD or another standard?
10. Structure beneath: **full asphalt**, an overlay on old asphalt or PCC (reflection grid; old surface lighter beneath), a cement-treated base (2.4-6 m cracks [29]) or a surface treatment on granular base?
11. Wet variant: **dry, plus an optional wet preset** (puddles in ruts, film darkening)?
12. Tile set: **3.66 m lane tile plus 1.0 m detail tiles (WP and NWP)**; parking tile 5.49 m if needed?
13. Curb or gutter in the tile: **no** (use a separate trim); yes adds the 0.3 m dirt band [40].

## 9. Acceptance targets

Scale per tile and variant (section 2): lane tile `{"tile_m": 3.66, "resolution": 2048, "height_depth_mm": <10/10/30/80/160 for V0-V4>, "normal_format": "directx"}`; detail tile `{"tile_m": 1.0, "resolution": 2048, "height_depth_mm": <4/4/24/32/40>}`. The `nowear` render uses the same scale as its variant and contains the as-built surface, the patches as placed, the deformation field and the as-built markings (I2).

Masks to export. Lane tile: wheelpath, centre, marking (footprint), marking_material, joint, patch, crack, crack_t, crack_l, fatigue, block, sealant, ravel (clusters ≥50 mm), pothole, edge_break, bleed, dirt, water, deposit (union of marking_material, sealant, sealcoat or fog seal, bleed, dirt, debris, vegetation), layer_index (0 surface, 0.33 wearing body, 0.67 binder course, 1 base), plus the `deform` map. Detail tile: aggregate (as-built exposed stone, I4), stone_id, socket (footprints of deleted stones), ravel, deposit, layer_index. Chip seal adds chip_loss and seal_loss.

Lane tile regions:
```json
"regions": {
  "wp": {"mask": "wheelpath", "threshold": 0.5}, "centre": {"mask": "centre", "threshold": 0.5},
  "nwp": {"not": "wp"}, "nwp_core": {"not": "wp", "erode_mm": 150},
  "crack": {"mask": "crack", "threshold": 0.5}, "sealant": {"mask": "sealant", "threshold": 0.5},
  "dirt": {"mask": "dirt", "threshold": 0.5}, "bleed": {"mask": "bleed", "threshold": 0.5},
  "crack_open": {"and": ["crack"], "not": "sealant"}, "crack_wall": {"and": ["crack_open"], "not": "dirt"},
  "crack_buf": {"mask": "crack", "threshold": 0.5, "dilate_mm": 70},
  "sealant_stray": {"and": ["sealant"], "not": "crack_buf"},
  "ravel": {"mask": "ravel", "threshold": 0.5}, "pothole": {"mask": "pothole", "threshold": 0.5},
  "edge_break": {"mask": "edge_break", "threshold": 0.5}, "patch": {"mask": "patch", "threshold": 0.5},
  "marking": {"mask": "marking", "threshold": 0.5}, "marking_material": {"mask": "marking_material", "threshold": 0.5},
  "deposit": {"mask": "deposit", "threshold": 0.5},
  "disturbed": {"or": ["crack", "sealant", "ravel", "pothole", "patch", "marking", "edge_break"]},
  "surface": {"not": "disturbed"},
  "wp_s": {"and": ["wp", "surface"], "not": "bleed"}, "centre_s": {"and": ["centre", "surface"]},
  "base": {"mask": "layer_index", "threshold": 0.9}, "base_outside": {"and": ["base"], "not": ["pothole", "edge_break"]},
  "fatigue": {"mask": "fatigue", "threshold": 0.5}, "fatigue_cells": {"and": ["fatigue"], "not": "crack"},
  "fatigue_lines": {"and": ["fatigue", "crack"]}, "block_cells": {"mask": "block", "threshold": 0.5, "not": "crack"},
  "crack_t": {"mask": "crack_t", "threshold": 0.5}, "crack_l": {"mask": "crack_l", "threshold": 0.5},
  "marking_wp": {"and": ["marking", "wp"]}, "marking_nwp": {"and": ["marking", "nwp"]},
  "patch_d": {"mask": "patch", "threshold": 0.5, "dilate_mm": 300},
  "patch_ring": {"and": ["patch_d"], "not": ["patch", "pothole", "crack_buf", "sealant", "marking"]},
  "rut_flank": {"boundary": ["wp", "centre"], "band_mm": 300,
                "not": ["crack_buf", "pothole", "patch_d", "ravel", "sealant", "marking"]},
  "water": {"mask": "water", "threshold": 0.5},
  "water_d": {"mask": "water", "threshold": 0.5, "dilate_mm": 300},
  "water_ring": {"and": ["water_d"], "not": "water"}
}
```
Detail tile regions (it has no crack, patch or marking masks):
```json
"regions": {
  "ravel": {"mask": "ravel", "threshold": 0.5}, "socket": {"mask": "socket", "threshold": 0.5},
  "deposit": {"mask": "deposit", "threshold": 0.5}, "surface": {"not": "ravel"},
  "agg": {"mask": "aggregate", "threshold": 0.5, "and": ["surface"], "erode_mm": 0.5},
  "agg_d": {"mask": "aggregate", "threshold": 0.5, "dilate_mm": 1}, "mastic": {"and": ["surface"], "not": "agg_d"}
}
```

Targets (mm unless noted; "hard" = fails the material; "–" = not applicable; L = lane tile, D = detail tile). Luma is matcheck's `srgb255` luma; targets assume mixed grey aggregate: add about 10 for light limestone and subtract about 10 for traprock (est.).

| id | type and parameters | V0 | V1 | V2 | V3 | V4 | From |
|---|---|---|---|---|---|---|---|
| layout_fixed | `mask_invariance` wheelpath, centre, marking, joint, patch vs nowear (L); aggregate (D); max_changed_frac | 0 hard | 0 hard | 0 hard | 0 hard | 0 hard (excl. shoves) | I1 |
| envelope | `envelope` vs nowear, except ["deposit"], tolerance_mm 0.1 (L and D) | hard | hard | hard | hard | hard | I2 |
| no_base_outside | `coverage` base_outside, no within (L) | 0 hard | 0 hard | 0 hard | 0 hard | 0 hard | I3 |
| ravel_depth | `height_diff` socket − mastic, local_mm 50, median (D) | – | – | [−19, −1] | [−19, −1] | [−25, −1] | 4.3 |
| agg_above_mastic | `order` upper agg, lower mastic, lower_stat p50, neighborhood_mm 25, max_violation_frac 0.02 (D) | hard | hard | hard | hard | hard | I4 |
| agg_protrusion | `height_diff` agg − mastic, local_mm 25, median (D; derived from [2]) | [0.2, 0.8] | [0.4, 1.2] | [1.0, 2.5] | [2.0, 4.0] | [2.5, 6.0] | 4.2 |
| surface_luma | `value_range` basecolor srgb255 luma, surface, median (L), dense HMA | [55, 66] | [63, 85] | [80, 105] | [85, 112] | [85, 124] | 4.1, 7 |
| surface_luma, other surfaces (est.) | same; chip seal unfogged / fog-sealed / sealcoat | [105, 128] / [50, 66] / [48, 63] | – / [55, 80] / – | [90, 110] / [70, 100] / toward HMA | [85, 108] / – / – | same as V3 | 4.25, 7 |
| beneath_darker | `value_order` basecolor luma median [crack_wall, surface] ascending (L) | – | – | soft | soft | soft | I5 |
| sealant_fresh | `value_order` [sealant, surface] ascending (L) | – | – | soft | – | – | I5 |
| ravel_brighter | `value_order` [surface, ravel] ascending (L) | – | – | – | soft | soft | I5, [32] |
| socket_darker | `value_order` [socket, mastic] ascending (D; est.) | – | – | soft | soft | soft | 4.3 |
| centre_darker | `value_order` basecolor luma median [centre_s, wp_s] ascending (L, roads) | – | soft | soft | soft | soft | I14 |
| fatigue_in_wp | `coverage` fatigue within nwp_core, min_px 1000 | ≤0.002 hard | same | same | same | same | I6 |
| bleed_in_wp | `concentration` bleed, driver wp (not SMA) | – | – | ≥5 soft | ≥5 soft | ≥5 soft | I6 |
| fatigue_extent | `coverage` fatigue within wp (est.) | 0 | 0 | [0, 0.05] | [0.05, 0.4] | [0.4, 0.9] | 4.8 |
| rut_depth | `height_diff` wp_s − centre_s, local_mm 1500, median (L) | [−1, 1] | [−5, 0] | [−10, −3] | [−13, −6] | [−30, −13] | 4.6 |
| rut_slope | `slope` region rut_flank, stat p90, min_px 2000 (deg, L) | ≤8 | ≤8 | ≤8 | ≤8 | ≤8 | I7 |
| crack_width | `run_length` crack_open, axis both, p50, max_mm 40 (V4: 80) (L; 3 px floor = 5.4 mm) | – | – | [5, 9] | [6, 24] | [6, 45] | 4.8-4.11 |
| crack_wall | `slope` between [crack_open, surface], band_mm 3, p50 (deg, L) | – | – | ≥45 | ≥45 | ≥45 | I8 |
| crack_t_orient | `orientation` crack_t, axis_deg 0, tolerance_deg 15 (lane + crack tile) | – | ≥0.7 | ≥0.7 | ≥0.7 | ≥0.6 | 4.10 |
| crack_l_orient | `orientation` crack_l, axis_deg 90, tolerance_deg 10 | – | – | ≥0.8 | ≥0.8 | ≥0.7 | 4.11 |
| fatigue_lines | `orientation` fatigue_lines, axis_deg 90, tolerance_deg 20 | – | – | ≥0.6 | – | – | 4.8 |
| fatigue_cells | `components` fatigue_cells, eq_diameter_mm, p50 | – | – | – | [60, 300] | [60, 300] | 4.8 |
| block_cells | `components` block_cells, eq_diameter_mm, p50 (lots, paths; ≤ half the tile) | – | – | [300, 1000] (2 m tile) | same | same | 4.9 |
| sealant_stray | `coverage` sealant_stray, no within | ≤0.0005 hard | same | same | same | same | I10 |
| sealant_band | `run_length` sealant, axis both, max_mm 200, p50 (overbands) | – | – | [75, 125] | [75, 125] | [75, 125] | 4.16 |
| sealant_height | `height_diff` sealant − surface, local_mm 300, median; overband / flush or reservoir | – | – | [2, 6] / [−2, 0.5] | [1, 5] / same | [0, 4] / same | 4.16 |
| marking_width | `run_length` marking, axis x, p50 (longitudinal lines; runs wrap across U = 0/1) | [100, 150] | same | same | same | same | 1 |
| marking_height | `height_diff` marking_material − surface, local_mm 300, median | thermo [2.0, 3.2]; paint [0.1, 0.5]; recessed [−1, 0.5] (est.) | same | same | thermo [1.0, 3.0] (est.: worn) | same as V3 | 4.18 |
| marking_wear | `value_order` basecolor luma mean [marking_wp, marking_nwp] ascending (crosswalk or stop-bar tiles only) | – | – | soft | soft | soft | I11 |
| pothole_size | `components` pothole, eq_diameter_mm, stat min, min_mm 30 | – | – | – | ≥150 | ≥150 | 4.14 |
| pothole_depth | `height_diff` pothole − surface, local_mm 1000, stat_a p05, stat_b median | – | – | – | [−50, −13] | [−100, −25] | 4.14 |
| pothole_wall | `edge_profile` outer pothole, inner surface, min_step_mm 10, metric peak_slope_deg, p50 (deg) | – | – | – | ≥60 | ≥60 | I12 |
| patch_crown | `height_diff` patch − patch_ring, local_mm 600, median | – | – | [−2, 6] | [−2, 6] | [−6, 6] | 4.15 |
| patch_darker | `value_order` [patch, surface] ascending (newer patches) | – | – | soft | soft | soft | I13 |
| water_in_lows | `order` upper water_ring, lower water, lower_stat p95, neighborhood_mm 500, max_violation_frac 0.05, min_px 2000 (wet preset) | hard | hard | hard | hard | hard | I15 |
| water_rough | `value_range` roughness, water, p95 (wet preset) | ≤0.1 | ≤0.1 | ≤0.1 | ≤0.1 | ≤0.1 | 7 |
| chip_loss_nwp | `concentration` chip_loss, driver nwp (chip seal; est.) | – | – | ≥1.5 soft | ≥1.5 soft | ≥1.5 soft | 4.25 |
| stone_cv | `per_element` stone_id, luma_mean, cv (D; est.) | [0.05, 0.3] | same | same | same | same | 3 |
| lowfreq | `lowfreq` basecolor, region wp_s and region centre_s (two checks), sigma_mm [100, 300, 1000] (est.) | ≤0.08 | ≤0.08 | ≤0.10 | ≤0.15 | ≤0.20 | I16 |
| fins | `ridge` between [ravel, surface] and [sealant, surface], threshold_mm 0.3, max_frac | ≤0.01 | ≤0.01 | ≤0.01 | ≤0.01 | ≤0.01 | 10 |
| hygiene | `seam` all maps ≤3 (strip tiles: `axis` along the road only); `normal_valid` directx; `height_usage` unique_levels ≥1024 and clipped_frac ≤0.001 | hard | hard | hard | hard | hard | I16 |
| height_range | `height_usage` range_used (section 2 ranges) | ≥0.3 soft | same | same | same | same | 2 |

## 10. Substance Designer build notes
Material-specific only; general craft lives in `references/sd_craft.md` (recipes R1-R14).
- **Two-tile pipeline.** The lane tile carries everything ≥3 px: layout, cracks, potholes, patches, ruts, raveled clusters ≥50 mm, colour and the masks. Stones (5-7 px on the lane tile) come from 1.0 m detail tiles per variant, one for the WP and one for the NWP (or one tile with a weathering-intensity input), blended in the engine by the lane tile's WP mask. Run I2 on each tile separately; run I4, agg_protrusion, ravel_depth, socket_darker and stone_cv on the detail tiles only.
- **Layout generator.** The lane tile has no tiled units, so its layout is a set of 1D bands across U (lane axis = V): a Linear Gradient across U, cut into bands with Histogram Scan or Levels at the section 2 pixel positions.
  - wheelpath: px 255-814 and 1234-1793; centre: px 814-1234 (3.66 m tile [3]);
  - lane lines split across U = 0/1, 28-42 px on each side;
  - the longitudinal paving joint runs beside the lane line, outside the stripe footprint [18] (est.: 200-375 mm from U = 0, px 112-210), on one side only; its mask never overlaps the marking mask;
  - stall tile: a Tile Generator with 2 x 1 stripes at 100 mm (37 px) [13];
  - patches: a maintenance layout pass. Saw-cut patches are lane-aligned rectangles from a Tile Sampler or FX-Map with a patch_id and a patch age; throw-and-roll patches take the outline of the fatigue cells or pothole they cover [27]. Build a per-pixel age map: variant age outside patches, age − patch age inside.
  - over PCC: a rectangle grid locked to the slab joints, which drives the reflection cracks only.
- **Per-unit IDs and randoms.**
  - Stones (detail tile): scatter polygonal crushed shapes with a Tile Sampler in two or three size classes (4.75 mm to NMAS), with the coarse share set per mix (section 2 [11][21]). Flood Fill, then Flood Fill to Random Grayscale gives `stone_id`. Use it for the rock-type colour mix and to choose which stones ravel (threshold `stone_id` against the raveling driver, so a stone goes whole or not at all). The `aggregate` mask is the stone footprint where the stone shape stands above the as-built mastic level, computed in the as-built branch.
  - Crack cells: Flood Fill on the fatigue and block cell masks gives `cell_id`, for tilt or sinking at H and for the outlines of potholes that grow from cells. A crack id chooses which cracks are sealed (I10).
  - Stall id: oil-stain offset, size and age per stall.
- **Height composition order** (16-bit, mm-calibrated; matches I2 and I13):
  1. Envelope `E` = max(stone field, mastic level), with the mastic at −MTD below the stone tips (section 2) and segregation as a low-frequency change in mastic depth and stone density (coarse spots [19]).
  2. Patch placement: inside each patch footprint, replace `E` with the patch's own envelope plus its crown (0 to +6 mm [27]) → `E′`. Do not blend.
  3. Weathering lowers the mastic level only, by per-pixel age × (1 + WP boost); stones stay at `E′` (I4).
  4. Raveling: delete whole stones by `stone_id`; the socket floor is the local mastic level minus 0.5-1 stone (est.). Repeated loss steps the wearing course down. Stud-wear ruts (if chosen): a smooth min() trough per car track.
  5. Cracks by `min`: one generator and mask per family (I9), a set mouth width per severity [1] and a V-profile; spall shoulders only at M-H. Inside patches keep only cracks younger than the patch, plus seam cracks along the patch outline from V3.
  6. Potholes by `min`: steep walls near the rim, the floor depth per severity [1], and floor material from `layer_index` (I3).
  7. Deformation: add the `deform` field (rut troughs and mix-rut shoulders, depressions, shoves; frost lips in the winter preset), and export it.
  8. Deposits by `max` or `add` on their own masks: sealant overbands (+3-6 mm [26]) from the final crack mask; thermoplastic as max(surface, local peak + 2.3-3.0 mm) [8]; paint as surface + ≈0.2 mm per coat; dirt filling valleys; bled binder filling valleys up to just below the tips.

  The `nowear` output is steps 1, 2 and 7 plus the as-built markings (step 8 for markings only), at the variant's height range. Water is a mask computed from the final height (I15), never added to height.
- **layer_index** comes from the removal depth below `E′`, using the stack's thicknesses: dense HMA wearing course 19-50 mm, binder course, then base [11][13]; overlay: overlay 38-50 mm [20] → old surface (lighter, cracked) → old binder course; chip seal: chips (ALD) → membrane (est.: 1-3 mm) → old surface or primed base. Never take it from a noise.
- **Colour.** One age term drives the surface along the 4.1 curve, using the per-pixel age. Exposure is higher on stone tips (height above the mastic) and in the WP. Crack walls and fresh patches take the fresh-binder colour at their own age [32]; raveled areas take exposed-stone colour plus loose debris. Oil, rubber, sealant, sealcoat and fog seal are separate dark layers with their own masks.
- **Masks from the layout only:** wheelpath, centre, lane line, marking footprint, joint, stall stripes, patch footprint, slab grid (overlay case), curb distance, and the detail tile's aggregate. Damage drivers may read them; nothing writes to them.
- **Known pitfalls.**
  - **Transverse crack spacing does not fit the lane tile.** Real spacing is 23.6 ± 10.3 m [28], but a square 3.66 m tile repeats any transverse crack every 3.66 m, which reads as cement-treated-base cracking (2.4-6 m [29]). Keep transverse cracks out of the base lane tile. Ship them as decals or as a second "lane + crack" tile to mix in sparsely (est.). Reflection cracks over 4.5-6 m slabs have the same problem.
  - **Soft wheel-path edges.** Drive damage from a softened copy of the WP mask (blur ≤150 mm beyond the strip, about 84 px; est.: lateral wander), but keep the hard layout mask for the checks; nwp_core leaves that margin out.
  - **Cracks under 3 px.** L cracks under 5.4 mm wide fall below 3 px on the lane tile. Draw them 3 px wide or as albedo and roughness darkening only, and keep height cracks ≥3 px.
  - **Warps.** Warp the crack generators' inputs, never the lane, WP or marking masks; a warp after the layout moves lane lines and breaks I1.
  - **Sealant from the crack mask.** Derive the overband by dilating the final crack mask with a Distance node (37-62 mm a side [26]); drawing it independently gives stray sealant (I10).
  - **Sand speckle.** Build the 0.3-2.36 mm fines from Fractal Sum Base min/max levels. High-scale FX-map noises have stalled Designer's GL engine on this setup.
  - **Height range.** Set `height_depth_mm` per variant (section 2) and use 16-bit; export `nowear` at the same range and offset, or the envelope check compares different scales.
  - **Dash cycles and stall heads.** The 12.2 m broken-line cycle [7] and stall head ends do not fit a repeating tile; put them in decals.

## 11. Reference imagery
Search terms, and what to measure (prefer raking light, top-down shots, and a coin, ruler or crack-width card):
- "LTPP distress identification manual photos", "PAVER asphalt distress manual": the severity photos for fatigue, block, transverse and edge cracking, raveling and potholes; check widths against the bands in section 2.
- "aged asphalt road grey stone exposed close up", "new asphalt vs old asphalt": stone tips light, mastic receding; how the colour shifts from black to warm grey.
- "raveling asphalt close up", "segregation asphalt end of load chevron": socket size against stone size, how bright the raveled area reads, chevron spots at regular spacing.
- "alligator cracking wheel path", "top-down cracking wheel path", "block cracking parking lot": cell sizes and their confinement to the wheel paths (fatigue) or not (block).
- "crack seal overband tar snakes", "crack sealant blotted sand": band width, sheen, dusting and wear in WP.
- "pothole asphalt layers exposed", "overlay delamination": wall steepness, the layer seen at the floor, debris and water.
- "throw and roll pothole patch", "saw cut asphalt patch": crown, outline, seam cracks and the colour contrast with age.
- "rutting asphalt puddles wheel path", "studded tire wear ruts", "oil stripe centre of lane": deformation vs wear ruts; where water and oil sit relative to the WP.
- "thermoplastic road marking worn", "recessed pavement marking", "paint stripe worn asphalt texture": paint following texture vs thermoplastic's flat top; wear where tyres cross; ghost lines after removal.
- "chip seal close up", "fog seal chip seal", "chip seal loss of aggregate", "chip seal streaking": chip uniformity, black fog-sealed vs grey unfogged, where chips are lost.
- "open graded friction course texture", "SMA surface texture": voids and stone packing for the other surface types.
- "wet asphalt road drying": which areas dry first, and how much darker the film makes stone and paint.

## Sources
1. Miller, J. S. & Bellinger, W. Y. *Distress Identification Manual for the Long-Term Pavement Performance Program*, 5th rev. ed., FHWA-HRT-13-092 (2014). https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/ltpp/13092/13092.pdf. Distress definitions and severity bands, wheel-path rules, bleeding location, pothole and patch sizes.
2. US Army Corps of Engineers ERDC-CERL (M. Y. Shahin, PI). *Asphalt Surfaced Roads & Parking Lots PAVER Distress Identification Manual* (2009). https://transportation.erdc.dren.mil/triservice/downloads/PAVER/Road%20Asphalt%20Distress%20Manual.pdf. Severity bands for weathering, raveling, rutting, depressions, corrugation, slippage, potholes and drop-off.
3. Connecticut DOT & Connecticut Transportation Institute. *Network-Level Pavement Condition Data Collection Quality Management Plan*, v2.0 (2022). https://portal.ct.gov/dot/-/media/dot/policy/photolog/data-quality-management-plan_ctdot-version-20.pdf. AASHTO R 85 wheel paths: 1.0 m strips, inner edges 0.375 m from the lane centre.
4. FHWA. *HPMS Field Manual*, pavement data section. https://www.fhwa.dot.gov/policyinformation/hpms/fieldmanual/page06.cfm. Federal wheel-path and cracking-percent definitions.
5. eCFR. *23 CFR 490.313, Calculation of pavement condition measures*. https://www.ecfr.gov/current/title-23/chapter-I/subchapter-E/part-490/subpart-C/section-490.313. Rut and cracking rating thresholds (good / fair / poor).
6. FHWA. *Lane Width: flexibility in the AASHTO guidelines* (CSS resources). https://www.fhwa.dot.gov/planning/css/resources/lanewidth. Lane widths 2.7-3.6 m.
7. FHWA. *Manual on Uniform Traffic Control Devices*, 2009 ed. (superseded by the 11th ed., 2023), Part 3 Markings. https://mutcd.fhwa.dot.gov/htm/2009/part3/part3a.htm. Line widths, broken and dotted line patterns.
8. North Carolina DOT. *Standard Specifications*, Division 12, Section 1205 Pavement Marking General Requirements (2006). https://connect.ncdot.gov/resources/Specifications/2006%20Specifications%20Books/12.%20Pavement%20Markings,%20Markers%20and%20Delineation.pdf. Paint coats (15 mil wet each; 5-8 mil dry interim coat), thermoplastic thicknesses, drainage gaps, black cover paint, retroreflectivity.
9. Iowa DOT. *Materials specification 4184, Reflectorizing Spheres for Traffic Paint*. https://ia.iowadot.gov/erl/current/GS/content/4184.htm. Bead gradation.
10. City of Overland Park (KS). *Section 1085, Preformed Thermoplastic Pavement Markings*. https://ppm.opkansas.org/wiki/images/Sec1085.pdf. Daylight reflectance of white and yellow thermoplastic, TiO2 content.
11. NAPA & FHWA. *HMA Pavement Mix Type Selection Guide*, Information Series 128 (2001). https://www.fhwa.dot.gov/publications/research/infrastructure/pavements/asphalt/HMA.pdf. Mix types, course thicknesses, NMAS per course.
12. NCAT. *Relationship of Air Voids, Lift Thickness, and Permeability in Hot-Mix Asphalt Pavements*, research synopsis of NCHRP Report 531 (2004). https://eng.auburn.edu/research/centers/ncat/files/old-synopses/nchrpsyn531.pdf. Lift thickness ÷ NMAS, air voids.
13. Colorado Asphalt Pavement Association. *A Guideline for the Design and Construction of Asphalt Parking Lots in Colorado*, 1st ed. (2006). https://www.co-asphalt.com/assets/docs/AsphaltlParkingLotDesignGuide1.pdf. Lot sections, slopes, bird baths, porous asphalt, stripes.
14. Pavement Interactive. *Raveling*. https://pavementinteractive.org/reference-desk/pavement-management/pavement-distresses/raveling/. Causes and "surface downward" disintegration.
15. Pavement Interactive. *Rutting*. https://pavementinteractive.org/reference-desk/pavement-management/pavement-distresses/rutting/. Mix vs subgrade rut profiles.
16. Pavement Interactive. *Bleeding*. https://pavementinteractive.org/reference-desk/pavement-management/pavement-distresses/bleeding/. Mechanism; does not reverse in cold weather.
17. Pavement Interactive. *Longitudinal Joint Construction*. https://pavementinteractive.org/reference-desk/construction/placement/longitudinal-joint-construction/. Joint density deficit, hot vs cold side, notched wedge.
18. AAPTP. *Asphalt Paving Handbook*, §9.3 Longitudinal Joints (hosted by NAPA). https://handbook.asphaltpavement.org/?p=526. Surface-lift joints at the centreline but not within wheel paths, recessed markings or striping; ≥6 in offset between lifts.
19. AAPTP. *Asphalt Paving Handbook*, §10.2 Recognizing Physical Segregation, Causes, and Solutions (hosted by NAPA). https://handbook.asphaltpavement.org/?p=565. End-of-load, centre-streak and edge segregation patterns.
20. FHWA. *Evaluation of Pavement Safety Performance*, FHWA-HRT-14-065 (2015), ch. 4. https://www.fhwa.dot.gov/publications/research/safety/14065/004.cfm. Typical macrotexture depth by surface treatment; thin overlay thickness.
21. McGhee, K. K., Flintsch, G. W. & de León Izeppi, E. *Using High-Speed Texture Measurements to Improve the Uniformity of Hot-Mix Asphalt*, VTRC 03-R12 (2003). https://vtrc.virginia.gov/media/vtrc/vtrc-pdf/vtrc-pdf/03-r12.pdf. Gradations (Tables 1 and 6), binder content, laser texture by NMAS and segregation.
22. Moore, N. *Friction: Dynamics of Macro-Texture related to Friction*, NCAT Asphalt Technology News (Fall 2023). https://eng.auburn.edu/research/centers/ncat/newsroom/2023-fall/macro%20texture.html. Test-track MPD by mix type.
23. FHWA. *Concrete Pavement Texturing*, Tech Brief FHWA-HIF-17-011 (2019). https://www.fhwa.dot.gov/pavement/pubs/hif17011.pdf. PIARC micro/macro/megatexture ranges; polishing by aggregate type (concrete test sections, Hall et al. 2009).
24. Minnesota DOT. *Minnesota Seal Coat Handbook*, rev. (2021). https://www.dot.state.mn.us/materials/pavementpreservation/manualsandguides/documents/MN%20Seal%20Coat%20Handbook_March2021.pdf. Chip sizes, ALD, flakiness, 70 % embedment, chip orientation in WP, chip loss off the WP and at the centreline, fog seal, streaking, start/stop spots, flushing.
25. FHWA. *Open-Graded Friction Course How-To Document* (2022). https://www.fhwa.dot.gov/pavement/tops/pubs/tops_ogfc_how_to_report_508.pdf. OGFC voids, lift thickness, raveling at transverse joints, clogging, life.
26. Smith, K. L. & Romine, A. R. *Materials and Procedures for Sealing and Filling Cracks in Asphalt-Surfaced Pavements, Manual of Practice*, FHWA-RD-99-147 (1999). https://infopave.fhwa.dot.gov/InfoPave_Repository/Reports/C30/C30_60/99147a.pdf. Seal vs fill, configurations, overband size, blotting, life, when sealing is unsound.
27. Wilson, T. P. & Romine, A. R. *Materials and Procedures for Repair of Potholes in Asphalt-Surfaced Pavements, Manual of Practice*, FHWA-RD-99-168 (1999). https://rosap.ntl.bts.gov/view/dot/14190/dot_14190_DS1.pdf. Patch methods, crown.
28. Osterkamp, T. E. et al. *Low Temperature Transverse Cracks in Asphalt Pavements in Interior Alaska*, Alaska DOT&PF (1986). https://dot.alaska.gov/stwddes/research/assets/pdf/ak_rd_86_26.pdf. Crack spacing, seasonal movement, frost lips.
29. Portland Cement Association. *Reflective Cracking in Cement Stabilized Pavements*, IS537. https://www.cement.org/wp-content/uploads/2024/08/is537.pdf. 2.4-6 m crack intervals; 3 mm and 6 mm treatment thresholds.
30. Pomerantz, M., Akbari, H., Chang, S.-C., Levinson, R. & Pon, B. *Examples of Cooler Reflective Streets for Urban Heat-Island Mitigation: Portland Cement Concrete and Chip Seals*, LBNL-49283 (2003). https://www.osti.gov/servlets/purl/816205. Measured solar reflectance of asphalt with age, chip seals, aggregates, sand, PCC.
31. Pomerantz, M., Akbari, H., Chen, A., Taha, H. & Rosenfeld, A. H. *Paving Materials for Heat Island Mitigation*, LBL-38074 (1997). https://www.osti.gov/servlets/purl/291033. Asphalt solar albedo 0.05-0.10 new, 0.15-0.20 weathered.
32. Herold, M. *Understanding Spectral Characteristics of Asphalt Roads*, NCRST, UC Santa Barbara (2004). https://www.ugpti.org/smartse/research/citations/downloads/Herold-Understanding_Spectral_Characteristics_Asphalt_Roads-2004.pdf. Spectra of aging, cracks, raveling (brighter), sealant (about 5 %), patches, oil, paint.
33. Mei, A., Salvatori, R., Fiore, N., Allegrini, A. & D'Andrea, A. *Integration of Field and Laboratory Spectral Data with Multi-Resolution Remote Sensed Imagery for Asphalt Surface Differentiation*, Remote Sens. 6, 2765-2781 (2014). https://www.mdpi.com/2072-4292/6/4/2765. The "asphalt line": R460 ≈ 0.6-0.8 × R740 across field asphalts.
34. Yao, J., Xu, Q., Yu, F. & Yu, S. *The remote sensing method for large-scale asphalt pavement aging assessment with automated sample generation and deep learning*, Sci. Rep. (2025). https://pmc.ncbi.nlm.nih.gov/articles/PMC12749324/. Field spectroradiometer reflectance (350-2500 nm, Wuhan) by aging stage.
35. physicallybased.info. *Materials API v2* (Asphalt (Fresh), Tire, Water). https://api.physicallybased.info/v2/materials. Linear RGB, roughness, IOR; its asphalt colour is taken from [36].
36. Jakubiec, J. A. *Spectral Materials Database* (spectraldb.com): measurements 00117 New Black Asphalt, 00118 Old Black Asphalt, 00123 New White Street Paint, 00124 Old White Street Paint, 00126 Old Yellow Street Paint, 00129 Concrete Street Curb (spectrophotometer, G. Ward, Berkeley, 1995). https://spectraldb.com/measurements/00118/ (others at the same path). Measured visible reflectance and linear RGB.
37. Ekrias, A. *Road Surface Reflection Properties*, Finnish Transport Infrastructure Agency (2019). https://nmfv.dk/wp-content/uploads/2020/11/Road-Surface-Reflection-Properties-Research-Reports-of-the-Finnish-Transport-Infrastructure-Agency-May-2019.pdf. Q0 and S1 by surface and wheel track.
38. Lekner, J. & Dorf, M. C. *Why some things are darker when wet*, Applied Optics 27(7), 1278-1280 (1988). https://www.wgtn.ac.nz/scps/staff/pdf/darkerwhenwet.pdf. Wet-darkening model used for the wet values.
39. Van Metre, P. C., Mahler, B. J., Scoggins, M. & Hamilton, P. A. *Parking Lot Sealcoat: A Major Source of PAHs in Urban and Suburban Environments*, USGS Fact Sheet 2005-3147 (2006). https://pubs.usgs.gov/fs/2005/3147. Sealcoat appearance, wear in traffic areas, reapplication interval.
40. Selbig, W. R. & Bannerman, R. T. *Evaluation of Street Sweeping as a Stormwater-Quality-Management Tool...*, USGS SIR 2007-5156 (2007). https://pubs.usgs.gov/sir/2007/5156/index.html. Street-dirt distribution across the street (quoting Pitt and Amy 1973) and particle sizes.
41. USGS. *Mineral Commodity Summaries 2025: Stone (Crushed)*. https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-stone-crushed.pdf. US crushed-stone rock types.
42. Deniz, M. T., Eren, B. K., Yildirim, S. A., Topcu, A. & Girit, S. *The Effect of Fuel on Flexible Pavement* (Eurasphalt & Eurobitume congress paper A5EE-418). https://www.h-a-d.hr/pubfile.php?id=663. Fuel softens binder; where spills concentrate.
43. Beauchamp, G., Pentecost, D., Koch, D. & Rose, N. *The Relationship Between Tire Mark Striations and Tire Forces*, SAE 2016-01-1479 (2016). https://www.jsheld.com/uploads/The-Relationship-Between-Tire-Mark-Striations-and-Tire-Forces.pdf. Skid and yaw mark formation and striations.
44. SGI (Saskatchewan Government Insurance). *Motorcycle handbook: lane position*. https://sgi.sk.ca/motorcycle/-/knowledge_base/motorcycle-handbook/lane-position-blocking. Oil in the lane centre between the wheel tracks.
45. Village of Johnsburg (IL) Zoning Ordinance, Section 8 Off-Street Parking; City of Lindon (UT) Code 17.18.020. https://www.johnsburg.org/Documents/Government/Municipal Code and Ordinances/Zoning Ordinance/SECTION 8 - OFF STREET PARKING.pdf ; https://lindon.municipal.codes/Code/17.18.020. Stalls 9 × 20 ft and compact 8 × 18 ft (Johnsburg), 9 × 18 ft and 24 ft two-way aisles (Lindon).
46. Bryden, J. E. & Kenyon, W. D. *Methods for Removal of Pavement Markings*, final report, New York State DOT Engineering R&D Bureau (1986). https://trid.trb.org/View/274044. Removal scars: colour and texture change.
47. FHWA. *Evaluation of Pedestrian and Bicycle Engineering Countermeasures...*, FHWA-HRT-11-039 (2011), ch. 6. https://www.fhwa.dot.gov/publications/research/safety/pedbike/11039/006.cfm. Recommendation to space crosswalk bars to avoid wheel paths.
48. Cotter, A. & Muench, S. T. *Studded Tire Wear on Portland Cement Concrete Pavement in the Washington State Department of Transportation Route Network*, WA-RD 744.3 (2010). https://depts.washington.edu/trac/bulkdisk/pdf/744.3.pdf. Stud wear rates 0.04-0.5 mm/yr; 60 % of HMA "rutting" in Washington attributed to studs.
49. Pavement Interactive. *Longitudinal Cracking*. https://pavementinteractive.org/reference-desk/pavement-management/pavement-distresses/longitudinal-cracking/. Top-down cracking in thick pavements; first fatigue signs are longitudinal in or near the wheel path.
50. Clark, R. N. et al. *USGS Digital Spectral Library splib05a*, Open-File Report 03-395 (2003), sample GDS376 "Asphalt Blck_Road old". https://pubs.usgs.gov/of/2003/ofr-03-395/DESCRIPT/A/black_old_asphaltroof_gds376.html. "Surface color of asphalt is lighter than interior of sample."
51. Harman, T. & Buncher, M. *CAPRI-Brief: Asphalt Longitudinal Joint Current and Best Practices*, NCAT / Asphalt Institute (2024). https://eng.auburn.edu/capri/CAPRI-Brief-Longitudinal-Joints---03.26.001R.pdf. Joint density deficit and acceptance, overlap, hot-side height, PennDOT data.
52. Hanson, D. I. & Prowell, B. D. *Evaluation of Circular Texture Meter for Measuring Surface Texture of Pavements*, NCAT Report 04-05 (2004). https://eng.auburn.edu/research/centers/ncat/files/reports/2004/rep04-05.pdf. 9.5 mm gradations, MPD and MTD.
53. Stroup-Gardiner, M. & Brown, E. R. *Segregation in Hot-Mix Asphalt Pavements*, NCHRP Report 441 (2000). https://onlinepubs.trb.org/onlinepubs/nchrp/nchrp_rpt_441.pdf. Texture-ratio severity bands.
54. AAPTP. *Asphalt Paving Handbook*, mat problems (segregation, tearing, auger shadows, screed marks, joint problems). https://handbook.asphaltpavement.org/. Gearbox streak width, colour and location.
55. Kandhal, P. S. & Mallick, R. B. *Longitudinal Joint Construction Techniques for Asphalt Pavements*, NCAT Report 97-4 (1997). https://rosap.ntl.bts.gov/view/dot/13984/dot_13984_DS1.pdf. Joint crack extent and width at 1-4 years.
56. Holcim UK. *Asphalt Care: New Asphalt Surfaces* (leaflet, 2023). https://holcim.co.uk/sites/uk/files/2023-02/superdrive-asphalt-aftercare-leaflet-2023.pdf. Gloss lost in weeks, dark grey in 6-12 months.
57. Petrinska, I. *Road Surface Reflection Properties of Typical for Bulgaria Pavement Materials*, J. Tech. Univ. Gabrovo 52 (2016). https://izvestia.tugab.bg/images/Downloads/52_03-EE-06-min.pdf. Q0 and S1 against wear period.
