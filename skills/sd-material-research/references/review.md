# Reviewer panel

Numbers catch what they were designed to catch. Independent reviewers catch the rest: decal-like albedo, shape
vocabulary, tiling landmarks, false correlations. In the brick build the main agent's own verdict was optimistic three
times ("chips now look like realistic half-moon bites"), and the panel's measurements (circle-fit share, cross-joint
mirroring) moved the work forward. The panel is worth it, but it took 55 % of the brick build's wall time, so run it
only on material that already passes its numeric checks.

## 1. Before a round (preflight)

1. Export every variant and the `nowear` reference at 2048 (`sk.export_outputs`, `sk.nowear`). Run them as one
   foreground `sdcall.py` job when they take more than ~40 s.
2. `matcheck.py checks/<v>.json` for every variant. **Fix every hard failure first.**
3. `previews.py checks/*.json --out review/round<N>`.
4. Fill the fix ledger `review/round<N>/ledger.json`: for every planned fix, record the implemented change (node names,
   params, script), its acceptance checks with the measured before/after values, and anything not done and why. One
   row per plan item, even when one batch applied several; a row without a measured after value counts as
   `not_landed`. The ledger replaces "the reviewers rediscover that half the fixes didn't land": in the brick build,
   2 of 10 and 1 of 8 fixes had fully landed when the next round started. Stamp the apply with
   `date -u +%Y-%m-%dT%H:%M:%SZ` when the plan gate is answered and after the last batch's targeted checks, and put
   `apply: {started, ended, stall_min}` first in the ledger (`stall_min`: minutes lost waiting on the user, or on a
   Designer job past its expected time).
5. Write or append `review/BRIEF.md` (§2).
6. Leave Designer idle until the plan gate. Reviewers work from files only.

## 2. Brief template (`review/BRIEF.md`, append one section per round)

1. **Rules.** Never call substance-designer tools. Inputs are read-only. Write helper scripts only under
   `review/agents/round<N>/<lens>/`. Python: `$(bash <skill>/scripts/setup_env.sh)`; `matcheck.py` and `previews.py`
   are importable for loading maps, regions and labels, so don't write PNG decoders. Return JSON matching the schema.
2. **User requirements**, verbatim, with ids R1..Rn, each marked hard or soft. Include the interview answers and the
   intentional deviations.
3. **Physics digest** from the spec:
   - the layer model and ASCII cross-section
   - the process cards (acts on, reveals, **Never**, where, shape and scale)
   - the invariants INV-1..k, each with its check id
   - the sheet's common-mistakes table, as the watch list
4. **Scale:** tile m, px, mm/px, height depth per variant, normal format, and the viewing distance of each view.
5. **Graph architecture:**
   - sections in build order, with node names and current parameters
   - the composition (max/min/lerp)
   - which masks come from the layout only
6. **Node semantics cheat sheet:** copy `sd_craft.md` §5. Histogram Scan direction and Blend divide order have caused
   wrong fixes.
7. **Variant presets** table.
8. **Files:** per variant, with purpose; the preview shader model and its caveats (one light, height-field shadows on
   the raking views only, no IBL; judge colour from albedo-only views); full-res maps for re-measuring.
9. **Current scorecard**, invariants first, plus any metric caveats or deprecations.
10. **History:** for each previous round, each plan item → implemented change → measured acceptance (from the ledger).
    Also: the keep-as-is list (the regression contract), rejected items (don't re-report) and deferred items.
11. **Severity rubric:**
    - **high:** breaks a hard requirement or invariant, or is a tell visible at the variant's use distance
      (whole tile or tiled)
    - **medium:** visible at 1:1 or in raking light, or a realism problem
    - **low:** close-zoom polish
    - Admissibility: every finding maps to an R-id, an INV-id or a cited spec fact. Taste gets said as taste, and
      capped at low.
12. **Acceptance-target rules:** compute every target on current data and check it against a baseline (the clean
    variant, a shifted or shuffled control). Prefer rank-based or local-reference metrics. Unreachable targets get
    replaced, not chased.
13. **The verifier checklist** (§4), so reviewers know what their findings will be tested against.

## 3. Lenses

**Round 1: 4-6 lenses.**
- **G1 Requirements and invariants.** One verdict per R-id and per INV-id. Try to break each invariant visually and
  numerically: layout invariance against nowear, envelope, order, registration of colour/roughness/height switches.
- **G2 Scale, proportion and layout.** Dimensions against the sheet, installer tolerances, calibration of parameters
  against measured values, CAD-perfect layouts.
- **G3 Process semantics.** One lens per 1-3 process cards. Check each card's mechanism, drivers, reveal, shape, scale
  and profile, and its **Never** rules. Also look for shape-vocabulary tells.
- **G4 Surface, edges and signal.** Micro-texture, porosity, edge anti-aliasing, Nyquist streaks and anisotropy,
  normal validity, height quantisation.
- **G5 Large surface and tiling.** 3×3 and 4×4 sheets: landmarks (with coordinates and period), lattices, banding,
  low-frequency blotches, outlier units.
- **G6 Colour, PBR and variants.** Albedo and roughness against sheet §7, value order, deposits, revealed-layer colour,
  variant distinctness.

**Round 2 and later: 3-5 lenses.**
- **Fixcheck:** fill `fix_status` for every ledger item.
- **Regressions:** check the keep-as-is contract and compare previous and current numbers.
- **Fresh-eyes realism:** what still reads CG at 1:1 and 3×?
- Plus G1 and G5.

**Final round: 3 lenses.** Fixcheck; requirements plus tiling; realism plus regressions.

**Deriving lenses from the spec:**
- Every process card whose signature reaches two or more maps becomes (part of) a G3 lens. Its Never lines become the
  lens's refutation tests, and its shape and scale numbers become the lens's metric targets.
- Every invariant goes to G1. Every revealed layer gets a sub-brief: colour from its own unit, depth, rake wall,
  texture coarser than the skin, no ring.
- Every row of the sheet's common-mistakes table goes to exactly one lens as a "look for" item.
- Merge down to 4-6 lenses by shared maps and regions.

**CG tells that numbers can catch** (add the matching check to `checks.json` once a lens finds one):

| Tell | Check |
|---|---|
| fins/moats at removal edges | `ridge`, `edge_profile` |
| relief vs colour misregistration | `run_length` on a half-depth region vs on the mask |
| binary edges and Nyquist streaks | `edge_profile` aa_frac, `orientation` isotropy |
| thresholded-noise shape vocabulary (circles, ribbons, islands) | `components` aspect/fill/small_island |
| false correlation | `per_element` corr |
| decal floors and ink rings | `boundary_profile` |
| banded deposits | `boundary_profile` |
| tiling landmarks | `lowfreq`, `per_element` outliers |
| CG-uniform statistics | `dispersion` |
| ID-driven cliffs | `step` |
| calibration drift | `height_diff` vs parameter |
| variant collapse | cross-variant per_element spreads |

## 4. Adversarial verification (one verifier per non-empty lens)

1. **Reproduce independently.** Recompute at least one key number per finding with your own script on the full-res
   16-bit maps, not the reviewer's script and not the previews.
2. **Refute claim by claim**, in this order:
   1. Is it visible in the maps?
   2. Is it a preview-shader artifact? Does it appear in albedo-only or the hillshade, or only in lit views?
   3. Is it a downsampling artifact? Check at 1:1.
   4. Is it a metric artifact? Look at threshold choice, a reference window that includes the feature, a global vs
      local reference, the resolution limit, and circular masks (a region built from the map it tests, a deposit
      checked inside the mask it was multiplied by, two masks built from the same bands).
   5. Is the premise wrong? Check against the cheat sheet and the actual parameter values.
   6. What is the basis: requirement, invariant, spec fact, or taste?
   7. Is any claim of clustering, repetition or correlation tested against a control?
   8. Does the stated consequence actually follow?
3. **Don't kill a finding over an overstated number.** Correct it, downgrade it, keep the core. Default to
   `real=false` only when the core is unsupported. `artifact` names what inflated the numbers and never rejects by
   itself: a finding that is entirely an artifact is `real=false`.
4. **Review the fix.** Would it create a singular feature or lattice, add a bevel, break an invariant or registration,
   rescale other layers, or conflict with another requirement (e.g. "subtle")? Give a better fix.
5. **Check the acceptance target** on current data and on a baseline. Replace it if it's unreachable.

Verifiers take every finding of their lens: highs, then mediums, then lows. Never guess a verdict: a finding the time
box (§6) left unmeasured goes in `not_checked`. One re-verify agent applies this same method to every high or medium
without a verdict before the lead runs; a low without a verdict goes to the lead `unverified`.

Brick numbers: 69 findings, 3 rejected outright, 22 downgraded, ~18 harmful or infeasible fixes rewritten. Expect
calibration from the verifier, not a high rejection rate.

## 5. Synthesis and stopping

**Lead (one agent, after the barrier):**
- Merge duplicates, keeping their source ids. Agreement across lenses counts as confidence.
- Re-measure disputed numbers itself, and correct wrong premises.
- Resolve conflicts with the user's requirements in writing (e.g. "don't add colour variety: the user asked for subtle").
- Order fixes by dependency: layout → height/structure → process masks → colour → micro-detail.
- Cap the list (10 / 8 / 5 by round), and give every fix acceptance checks and guard rails.
- Re-measure every `unverified` high or medium before planning it (`spot_checks`); defer an unverified low unless its
  numbers reproduce.
- Put every choice only the user can make (between looks, a requirement trade, a deviation) in `design_calls`: the
  question, 2-4 options, the recommended one, and what the answer changes.
- List keep-as-is, deferred and rejected items.

**Outputs:**
- `review/round<N>/review_result.json`
- `review/round<N>/findings.md`, in this format:
  - OVERALL: 2-6 paragraphs
  - `SC: met|mostly_met|not_met | R-id requirement (variant) | evidence`
  - `INV: pass|fail | INV-id | values`
  - `=== P<n> title [variants]`, each with WHY / CHANGE / ACCEPT
  - FIXSTATUS, UNVERIFIED, REJECTED, DEFERRED, TIMING (the per-agent table, `panel_min`, and the ledger's `apply`)
- Show the user the scorecard and the plan before building the fixes, and ask the plan's `design_calls` there, in one
  batch (`SKILL.md` stage 7); none during the apply. If they said not to stop, take each call's recommended
  option and list it in the report.

**Stop when:**
- all hard checks pass in every variant;
- every hard requirement is `met` and every soft one at least `mostly_met`;
- there are 0 high findings, and no medium finding visible at use distance;
- the last round's fixes landed.

**Also stop:**
- after a dry round (no new medium-or-higher finding confirmed by a verifier, the re-verify agent or the lead's
  `spot_checks`) in which every lens returned;
- after 3 full rounds (ask the user before a 4th);
- when the user accepts.

When more than half the ledger is partial, run a cheap fixcheck-only round (checks plus one agent) instead of the full
panel.

**Final gate.** The last change is followed by a 2048 export of every variant and its `nowear`, then a full
`matcheck.py` run on every variant. The report says what was verified after the last change. Don't say "three review
rounds confirmed it" when the final fixes were never reviewed.

## 6. Running it

- **Workflow** (the default): `Workflow({scriptPath: "<skill>/assets/workflows/review_round.js", args: {...}})`. The
  args are documented in the script. It pipelines review → verify per lens, sends every high or medium left without a
  verdict to one re-verify agent (its verdicts match by `lens/id`, or by a bare id no other finding sent to it shares),
  then runs the lead. Every agent runs at xhigh; the runtime caps concurrency.
- **Time boxes:** lens 15 min and 35 tool calls, verifier 12 min and 25 (args `box_lens`, `box_verify`). The re-verify
  agent and the lead have none. A lens cut by its box names the limit in `box` and lists what it skipped in
  `not_reached`; the lead is told, and those areas count as unreviewed.
- **Status:** `confirmed`; `rejected` (the verdict says `real=false` or severity `none`; `artifact` alone never
  rejects); `unverified` (no verdict). An unverified finding goes to the lead marked so, never into rejected. The lead
  also gets the rejected list (id, lens, title, why) and can overrule a rejection it re-measures. Save the result as
  `review/round<N>/review_result.json`.
- **`dead`:** agents that returned nothing. A dead lens leaves its area unreviewed: say so at the plan gate, and run it
  again in the next round, or now with the Agent tool from the script's lens and verifier prompts. A one-lens Workflow
  would overwrite `lead.json`.
- **Files and stamps:** each agent runs `date -u` first and last and writes its result, stamps first, to
  `review/round<N>/`: `<lens>.json`, `<lens>.verdicts.json`, `reverify.verdicts.json`, `lead.json`. The result's
  `timing` table and `panel_min` come from those stamps and stay in `review_result.json`; findings.md TIMING lists
  them with the ledger's `apply` stamps (§1).
- **Agent tool** (fallback, only when Workflow is unavailable; launch it only when this session's records show xhigh,
  `SKILL.md` Effort): the same prompts, schemas and files from the script. One message with one Agent per lens; one
  verifier per non-empty lens, given all its findings, highs first; one re-verify agent for every high or medium
  without a verdict or in a `not_checked` list; then the lead.
- **While the panel runs,** read the lens and verdict files as they land, and write ledger records, hand-off notes and
  fix drafts from them. Drafts stay drafts until the plan gate: none runs in Designer before it, and each takes the
  verifier's fix where it differs. Run no suite or numpy jobs beside the panel (its agents measure too), never edit
  the maps it reads, and never call Designer from a subagent.

## 7. Catch ledger

Every trade of rigor for speed in this workflow gets a row: what it still catches, what it could miss, with the source,
and the signal that shows it failing. Check the signals at each plan gate and tell the user when one fires. A new
trade adds its row before it is used.

| Trade | Still caught | Could be missed | Signal |
|---|---|---|---|
| One build-measure batch per graph (`SKILL.md` stage 7) | fixes that didn't land: each ledger row keeps its measured before/after values, and a full run follows the last change | which fix in a batch caused a regression; brick's ledger found 2 of 10 and 1 of 8 fixes fully landed (§1) | more `partial`, `not_landed`, `regressed` or `not_checked` fix_status rows next round |
| High effort for scripted stages (`SKILL.md`, Effort) | design turns stay at xhigh (spec, panel); no past catch is tied to xhigh (round-3 speed review) | reasoning depth in check-fix and fix turns | a lower share of hard checks passing at the first 1K export, more fix cycles, wrong builds regressing, or the developer's eval re-run below 30/30 |
| Time-boxed lenses and verifiers (§6) | every high or medium gets a verdict at xhigh by the verifier's own method: what a box left goes to the re-verify agent (§4); verifiers take lows after them | a finding a boxed lens never reached; a ledger item a boxed lens never reached (fix_status `not_checked`); an overstated low the verifier's box cut (it reaches the lead `unverified`, never re-verified); verifiers changed 11 of 35 severities (`win`) and 10 of 25 on brick (`mac-tx`) | a high or medium reaching the lead `unverified`; lows reaching the lead `unverified` (`stats.unverified` above `stats.unverified_high_medium`); `stats.severity_changed` per verified high or medium below those rates (widen `box_verify`); a lens whose `box` is not `not_hit` or whose `not_reached` is non-empty (`stats.lenses_boxed`); fix_status `not_checked` rows |
| Fix drafts from lens files while the panel runs (§6) | drafts never run in Designer before the plan gate and take the verifier's fix | an overstated number or wrong premise in a draft; about 18 brick fixes were rewritten by verifiers (§4) | a draft that reaches Designer before the plan gate, or one that differs from the verifier's fix |
| Section-scoped sheet reads (`SKILL.md` stage 2) | invariants (§5) and targets (§9) are read in full | an interaction held in a skipped process card (asphalt I10: sealant only on cracks) | a sheet §5 invariant of the layout or a chosen process missing from `spec.md`, in its §6 without a check id, or on its left-out list while a preset has the process or feature it governs |
