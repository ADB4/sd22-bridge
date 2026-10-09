# Context: building the round-3 speed rework

## Task

On 2026-10-04 a speed review of the whole material workflow (the bridge, the MCP server, `sdkit`, the measure scripts
and the `sd-material-research` skill) ended with a report, `review_round3_speed_rework.md` in this repo's root, and my
decisions on every proposal. **Build what I accepted**, milestone by milestone, as section 10 of that report lays out.
Read sections 1, 4, 9 and 10 of the report first; read the rest by section when a milestone needs it.

What I accepted (report section 9; the decision page's store holds the same 42 rows):
- **Build:** DZ-01, DZ-02, DZ-03, MS-01, RS-01, ML-07, ML-01, RV-01, RV-02, RV-03, RV-04, RV-05, XS-01, XS-02, GAP-1 and
  the grafts SH-01 to SH-09.
- **Trial on the next material, not in this build:** TR-01 (light panel, all lenses kept) and ML-01's A/B.
- **Deferred:** TR-02. **Rejected:** XS-03, XS-04, DZ-04, MS-02 (its numbers go into DZ-03), MS-03, MS-04, MS-05,
  ML-02 to ML-06, RS-02 to RS-04, RV-06. Don't build those, and don't re-propose them without new evidence.

Every accepted proposal has a full record in `$OUT/results/proposals.json`: `today` (file:line, pub and main), `change`,
`evidence`, `rigor_cost`, `conflicts`, `depends_on` and `verify_after` (the timing that proves it). The grafts are in
`$OUT/step5/extra_items.json`. Use those records as the spec; where a record and the report disagree, the report wins
(it carries the step-4 corrections).

**Before any work, ask me these in one AskUserQuestion round:**
1. Has M0 happened (code-review-fixes-public landed on main, with the `sdkit.py` conflict resolved)? If not, should you
   build on a worktree branch off `code-review-fixes-public`, or off `main` with DZ-02 cherry-picked by hand?
2. Is Designer free for M1's proof timings (about 30 min), and can the machine be quiet (other sessions idle)?
3. Which milestones in this session? (Default: M1 to M4, then stop at the gate below.)
4. Commits: one per milestone on the worktree branch, nothing pushed? (Push only on a separate yes: `origin` is public.)

## Paths

Most paths contain spaces: quote them, and use `$HOME` rather than `~` inside quotes. Subagents and fresh Bash calls
don't inherit shell variables.

```
REPO="$HOME/Documents/Allegorithmic/Substance Designer/python/sduserplugins/sd-claude-bridge"
SD="$HOME/Documents/Allegorithmic/Substance Designer"
DEV="$SD/sd-material-research-dev"                     # skill dev folder, not in git
OUT="$DEV/speed_review"                                # the review: results/, probe/, step5/, decision page source
T="$SD/asphalt_materials_tools"; BRICK_T="$SD/brick_materials_tools"
TX="$HOME/.claude/projects/-Users-andybui-Documents-Allegorithmic-Substance-Designer-python-sduserplugins-sd-claude-bridge"
VPY="$HOME/Library/Application Support/sd-claude-bridge/venv/bin/python"   # MCP server venv (3.12)
SKPY="$HOME/.cache/sd-material-research/venv/bin/python"                   # analysis venv (numpy, scipy, PIL, cv2)
SK="skills/sd-material-research"                      # relative to a tree root
WT=<your scratchpad>/wt                                # the worktree you build in
```

Decision page: https://claude.ai/artifact/4gUHUtoGXFAq2spU6xzfL8 (collection `decisions`; read-only for this work).

## Live installs and branches

- **The live installs are symlinks into `$REPO`** (branch `main`): `sduserplugins/sd_claude_bridge`, the three files in
  `~/Library/Application Support/sd-claude-bridge/`, and `~/.claude/skills/sd-material-research`. Anything written under
  `$REPO/designer_plugin`, `$REPO/mcp_server` or `$REPO/$SK` lands in my live setup. Never pull, merge, reset, switch or
  stash anything in `$REPO`. Build in a worktree: `git -C "$REPO" worktree add "$WT" -b speed-rework-impl <base>`.
- Designer 12.4.1 runs whatever `$REPO` has checked out. To prove a Designer milestone live, the patched plugin has to be
  what Designer loads: ask me before pointing the install at the worktree, and restore it afterwards.
- `code-review-fixes-public` (pub) is the code as it will land; `main` is the live install. A merge of main into pub
  conflicts in `sdkit.py` (main's `_fn_extra` vs pub's `_check_spec`). Landing is my call (M0). Whoever resolves it keeps
  KIT-02's `_check_heavy` calls in `P()` and `drive()` (pub `sdkit.py`:389, :1056).
- Where pub and main differ for this work (report section 4, landing notes): DZ-01 is the same code in both
  (`getChildrenResources(True)` at pub `commands.py`:205 and :1073, main :197 and :1031). DZ-02 lands in `bridge.py`,
  which pub rewrote (modal check, `MSG_NOSIGNAL`, `MAX_LINES_PER_POLL`; `_handle` pub :263-281, main :199-211). DZ-03
  lands after pub, or caps status polls at 6 per job. MS-01 needs pub's matcheck exit codes (`b1f07e0`) and main's
  `wrong_builds.py` (`489003b`), so it waits for M0. RV-03 rewrites `review_round.js`; take pub's line :99. SKILL.md
  edits auto-merge.

## The plan

Report section 10 is the plan. Order: M1 → M2 → M3 → M4 → M5 → M6, and M7 after M0. Milestone notes the table doesn't
hold:

- **M1 (DZ-01, DZ-02).** Prototypes: `$OUT/probe/tools/build/prof_e2.py`:14-25 (`FAST_GRAPHS_IN`, the non-recursive walk)
  and `$OUT/probe/tools/build/nap.py` (the activity via ctypes). Wrap the activity per command in `_handle`, not per
  `run_python`: `search_library`, `render_preview` and `save_package` are commands too. Fail open: any exception in
  `begin` logs once and the command runs as today. Prove it with the patched module loaded as the plugin, not a monkeypatch.
- **M2 (doc pass).** Write DZ-03's numbers from M1's quiet re-time, not from the review's `mac-loaded` values. ML-01 goes
  in as an effort column plus the A/B and its stop rule (report section 4). RV-01's rule must keep a measured
  before/after value on every ledger row.
- **M4 (panel runner).** Add the `unverified` status before anything else: today a finding without a verdict counts as
  rejected (`review_round.js`:138-139). Verifiers stay at xhigh with their own method. A boxed verifier's `not_checked`
  high or medium goes to one re-verify agent before the lead (SH-01). Workflow scripts can't call `Date.now()`, so for
  GAP-1 each agent records its own start and end with `date -u` into its per-lens file.
- **M5 (RV-05, RV-04).** The cheat sheet and the verifier checklist stay in the part every lens reads: their premises
  (Histogram Scan direction, Blend divide) once caused wrong fixes (`review.md`:39-40). Fix drafts written during the
  panel stay drafts until the verifier and the plan land.
- **M6 (XS-01, XS-02, SH-09).** Run SH-09's test list first: whether a Workflow keeps running while its session only
  waits and a second session works the same tools folder is untested, and XS-02 depends on it.
- **M7 (MS-01, SH-06).** Cap workers at `min(6, CPUs-2)` with 2 BLAS threads each; ≤ 4 beside Designer; none while a panel
  runs (SH-03, SH-08). Gate on exit codes and the JSON gate fields, never on grep: `run_all.sh`'s grep once let errored
  and vacuous checks pass (win).

## Evidence

| where | what |
|---|---|
| `$REPO/review_round3_speed_rework.md` | the report: timelines, experiments, the shape, ranked proposals, decisions, plan |
| `$OUT/results/proposals.json` | all 31 proposals, full schema, with `verify_after` |
| `$OUT/results/timings.jsonl`, `raw/` | every E1-E12 and O1-O5 timing (all `mac-loaded`) and per-step profiles |
| `$OUT/results/1_reference_scenario.md`, `3_synthesis.md`, `4_*` | scenario R, the chosen shape, the step-4 corrections |
| `$OUT/probe/` | probe copies (`asphalt_speedprobe.sbs`, `brick_speedprobe.sbs`, `sdk_test.sbs`), tools copy with paths rewritten to `$OUT/probe/tools`, and the E-jobs in `jobs/` (E2b D3-D7 is the App Nap A/B) |
| `$OUT/_progress.md` | the review's log, including dead ends |

## Ground rules

- **Quality floor (unchanged by this work):** adversarial verification at xhigh; every hard check fails its named wrong
  build (R6); the `nowear` controlled render in every export; a full suite after the last change, before any report; one
  Designer call at a time; research before the spec. A change that weakens one stops and asks me.
- **Never** commit, stash, clean or delete `speed_review_context.md`, `code_review_context.md` or this file.
- Set `PYTHONDONTWRITEBYTECODE=1` for your own Python runs. Thread caps for parallel numpy work:
  `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=VECLIB_MAXIMUM_THREADS=2`.
- Tag every new number: `mac` (load below 2, n ≥ 3, median and range), `mac-loaded`, `mac-tx`, `win`, `est`.
- Keep `$OUT/_progress.md`-style notes for this work in `$OUT/impl/_progress.md`: what is done, what is next, where each
  result is, Designer state.

## Designer rules (for proof timings)

- Profile on the `$OUT/probe` copies only, with `graph="asphalt_speedprobe.sbs::asphalt_lane"` on every
  substance-designer call. Never save the original packages; never edit `$T`.
- Until DZ-02 is loaded, App Nap is the main variable: a hidden Designer runs 7.5-14.5× slower. For any A/B, record
  `ps -o pri= -p <pid>` and keep the state the same on both sides.
- Keep `run_python` under 45 s; longer jobs go through `"$REPO/$SK/scripts/sdcall.py"` in the foreground with the Bash
  timeout at 600000 ms. Never retry a call that timed out; check with `designer_status` or
  `sample <pid> 1 | grep SDSBSCompGraph_compute`. Avoid sdkit's `HEAVY` noises. Never quit, kill or relaunch Designer: ask me.
- When done, clear the probe from sdkit's state
  (`import sd; [d.pop(k) for d in (sd._sdk["reg"], sd._sdk["sections"]) for k in list(d) if k.startswith("asphalt_speedprobe.sbs::")]`)
  and unload the probe package.
- Don't call `render_preview` in the main loop (each adds ~10k+ tokens of images); export and read numbers instead.

## Context budget and hand-over

Keep the main session under about 500k tokens. At about 400k start nothing new that won't finish well under 500k; at
about 500k stop at a clean point (Designer job returned, every result saved), bring the progress file up to date, and
write `$OUT/impl/CONTINUE_PROMPT.md` (under ~80 lines, pointers not copies: my answers, the milestone reached, the exact
next action, Designer state, dead ends). Then give me the kick-off message in a code block.

## Gate and after

- Stop after M1 (the first live-Designer change) with its proof timings, and again after the last milestone of the
  session. In chat: what was built, the proof numbers against report section 10, and anything that failed.
- Ask before every commit, and say which branch. Never push without a separate yes.
- After the session: update the project memory (`speed-review-handoff.md`) with the milestones done and where the work is.
