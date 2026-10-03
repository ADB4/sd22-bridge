# <Material family>: reference sheet

> **Scope:** which sub-types and uses this sheet covers, and which it does not.
> **Researched:** YYYY-MM-DD. **Confidence:** one line on what is well sourced and what is estimated.

Every number carries a source tag `[n]` (see Sources) or `(est.)` with a one-line reason.
Give ranges rather than single values, and say which variant or region a value applies to.

## 0. Physical summary
One paragraph: what the material is, how it is made or installed, and the two or three physical facts
that procedural versions most often get wrong.

## 1. Construction and layout
- How the units or components are arranged (bond, board layout, lane geometry, slab joints, ...).
- The layout rules real installers follow (stagger, joint spacing, fastener rows, minimum offsets).
- **What the layout fixes.** These footprints are set at construction, and no aging process may change them.

## 2. Dimensions and scale
| Feature | Typical | Range | Variant / notes | Source |
|---|---|---|---|---|

Cover unit sizes, joint or gap widths, layer thicknesses, grain or aggregate sizes, defect sizes
(chips, spalls, pits, crack-width severity bands), relief depths in mm, and spacing of periodic features.
End with **recommended tile sizes** for real-time tiling at 2048 px (tile in m, resulting mm/px), and say why
(each must hold a whole number of layout repeats, and the smallest features must stay at least 2-3 px wide).

## 3. Layer model (stratigraphy)
List the layers top to bottom. For each one, give:
- what it is physically
- its depth below the original surface (mm)
- its appearance: albedo and hue, roughness, micro-texture
- when it becomes visible

Then define the **original surface envelope**: the as-built surface. Removal processes can only go below it,
and only deposits (dirt, salts, sealant, growth, paint) can sit above it.
Finish with an ASCII cross-section that shows neighbouring components side by side, e.g. brick | joint | brick.
The diagram makes clear what lies *beneath* each component and what lies *beside* it.

## 4. Processes: aging, wear, damage, deposition
Write one subsection per visually significant process, using this card:

### 4.x <Process>
- **Mechanism:** the physics or chemistry, in 1-3 sentences.
- **Acts on:** <layer(s)>. **Removes / adds:** <material>. **Reveals:** <the layer beneath, in the same component>.
- **Never:** what it does not do. These are invariant candidates, e.g. "does not widen the joint footprint".
- **Where:** the spatial drivers, such as edges and corners, wheel or foot-traffic paths, low points and standing
  water, sun or shade, splash zone, gravity direction, joints, grain direction, fastener lines.
- **Shape and scale:** sizes, depths, outline character (conchoidal, faceted, rounded, ragged), profile (step,
  slope, bowl), orientation, and statistics (coverage %, spacing, count per m²).
- **Progression:** stage 1 → 2 → 3, and which preset level maps to which stage.
- **Interactions:** what it causes or is caused by (e.g. cracking → raveling → pothole).
- **Signature per map:** height, normal, albedo, roughness, AO.
- **Severity scale:** the published scale, if one exists (e.g. FHWA LTPP low/medium/high, ASTM C672 0-5).
- **Sources.**

## 5. Invariants
Number the conservation and causality rules a believable result must obey. For each one, give:
- **Statement.**
- **Why:** the physics.
- **Enforce:** how the graph guarantees it *structurally*, e.g. "mask_mortar comes from the layout generator only".
- **Check:** a check type from `references/checks.md` with the parameters you would use.

## 6. Common procedural mistakes
| Wrong (what procedural materials often do) | Right (physics) | How to fix it in the graph |
|---|---|---|

## 7. PBR reference values
| Component / state | Albedo (sRGB 0-255 and/or linear) | Roughness | Notes | Source |
|---|---|---|---|---|

Include fresh, aged and wet states where they differ. Metallic is 0 except for exposed metal.
Say whether a source measures solar reflectance, visible albedo or photo-derived values: they differ.
Keep dielectric albedo inside roughly sRGB 30-240 unless a measured source says otherwise.

## 8. Variants and presets
- A suggested variant ladder (e.g. new / weathered / distressed): which processes each includes, at which stage.
- Interview questions specific to this material, each with a recommended default.

## 9. Acceptance targets
Default numbers for `checks.json`, with units and per variant where relevant. Each one cites the section it comes from.

## 10. Substance Designer build notes
Material-specific only (general craft lives in `references/sd_craft.md`):
- the generator for the layout
- how to get per-unit IDs and randoms
- the height composition order (max / min / subtract)
- which masks must come from the layout only
- known pitfalls for this material

## 11. Reference imagery
Search terms and what to look for in real photos, especially raking-light and close-up shots.

## Sources
A numbered list: author or organisation, title, year, URL, and what each was used for.
Prefer, in order:
1. Standards and government manuals (ASTM, BS EN, FHWA/LTPP, USDA FPL Wood Handbook, ...).
2. Industry associations (BIA, Asphalt Institute, PCA/ACI, ...).
3. Peer-reviewed papers.
4. Conservation guidance (Historic England, NPS Preservation Briefs, ...).
5. Measured PBR datasets.

Forums and blogs only for visual examples, never for numbers.
