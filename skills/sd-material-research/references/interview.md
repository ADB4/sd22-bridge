# Interview

The interview fixes the decisions that change the physics and the graph before research narrows down. The user asks to
be questioned before work starts, and answers become acceptance criteria, so treat it as part of the job rather than a
formality.

## How to ask

- Use AskUserQuestion: at most 4 questions per call.
- Put the recommended option first and mark it "(Recommended)". Choose the recommendation from physics and from what
  hides tiling best, not from what is easiest to build.
- Each option's description states its physical or visual consequence, so the user chooses with understanding. Good
  example from the brick project:
  > "Raked: a flat joint recessed about 6 mm. Strong shadow lines and crisp brick arrises, so the sharp edges really show."
- Mention the knock-on effect in the question when one exists, e.g. "Weathered shifts the shared colour family toward
  faded and stained; Rustic toward darker and more varied."
- Plan for at most two rounds before research, and one more after research if it surfaces a decision the user should
  own (lime vs cement mortar, painted vs bare wood, which distress types).
- Don't ask what the defaults below already answer, unless the request hints otherwise.

## Defaults (state them, don't ask)

| Setting | Default |
|---|---|
| Use | Real-time tiling surface |
| Resolution | 2048 for delivery; iterate at 1024 or 512 |
| Tile size | From the material sheet: whole layout repeats, smallest features at least 2-3 px |
| Normal format | DirectX, exposed as a `normal_format` input |
| Height | 16-bit; `height_depth_mm` holds the deepest feature with margin |
| Outputs | basecolor, normal, roughness, metallic, height, ambientocclusion, an ID map, `mask_<layout>` for each layout mask, `mask_<process>` for each process |
| Variant structure | One core graph with exposed parameters, plus one wrapper graph per variant |
| Package | `~/Documents/Allegorithmic/Substance Designer/<material>_materials.sbs`, with a tools folder next to it |

## Question bank

Pick the 4-8 questions that matter for this request. Each material sheet's section 8 adds material-specific questions
with recommended defaults.

1. **Sub-type and setting.** Which real thing is this? A road or a parking lot; deck boards or floorboards; a facing
   brick wall or a garden wall. This decides the layout rules and which processes dominate.
2. **Layout.** The bond or pattern, the unit standard (UK, US or EU sizes), board widths and stagger, joint or saw-cut
   spacing, lane and marking layout.
3. **Look.** The colour family, species or aggregate type, and the finish: raked or flush joints, broom or trowel
   finish, painted or bare wood.
4. **Variants.** How many, and the ladder. The default is three: new or clean, weathered, distressed or rustic. Name
   each by what it physically shows.
5. **Processes** (multiSelect). Which wear, damage and deposits to include, and which to emphasise or exclude. List the
   options from the sheet's section 4 with one-line physical descriptions.
6. **Variant structure.** Core plus wrappers (recommended), one graph with a variant switch, or standalone graphs.
7. **Hard requirements.** Anything the user said in their own words, like the brick list: "erosion subtracts from the
   brick and does not expose more mortar", "sharp edges with little bevel", "subtle colour variation for large
   surfaces". Don't ask about these again. Copy them verbatim into the spec as acceptance criteria and confirm your
   reading of any ambiguous one.
8. **What a wear word means.** "Erosion" or "weathering" can mean several processes:
   - **rounding:** arris wear widens the joint's *visible* shadow while its footprint stays fixed
   - **chipping:** discrete flakes at edges
   - **spalling:** face delamination revealing a sub-layer
   - **raveling:** loss of fines and binder

   The user's own description of the brick mentioned rounding, and the brick build never modelled it. When the
   request uses such a word, ask which processes it means (multiSelect), with the physical difference in each option.
9. **How much, per variant.** Damage coverage or stage for each variant, e.g. classic about 0.3 % of units, weathered
   about 4 %, distressed about 6 %, or a published severity level (LTPP low/medium/high, ASTM C672 rating). Without
   this, "weathered" is a guess that reviews keep moving.
10. **References and use distance.** Does the user have reference photos? They are the best source; read them.
    How close will the material be seen: wall or road at a few metres, or a close-up prop? Ask only when the request
    hints it isn't the default real-time tiling surface.
11. **Package and location.** Only ask if the user might want something other than the default.

## Write it down

Record the answers, the defaults you applied and the user's verbatim requirements in the spec's
"User requirements" section. Every later review scores against that section.
