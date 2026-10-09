# Context: <material> material in Substance Designer (continue iterating)

I'm continuing work on a procedural <material> material that was built in an earlier session through the Substance
Designer MCP bridge, using the sd-material-research skill. Read this whole file before touching the graph.

## Files
- Package: `<path>.sbs`. Open it in Designer first.
  - `<m>_core`: the parametric graph (~N nodes, framed sections). Its `$outputsize` is relative to its parent, so
    the wrappers drive resolution.
  - `<m>_<variant>` × N: wrapper graphs at 2048 (absolute), each instancing the core with a preset.
  - Outputs: <list>.
- Tools folder: `<path>_tools/`
  - `spec.md`: requirements, scale, layer model, invariants, presets, targets. The acceptance criteria live here.
  - `checks/<variant>.json`: the numeric checks; `checks/wrong_build_cases.py`: the wrong build each hard check
    catches; `SUITE.json`: runs them all with the previews (`<skill>/scripts/suite.py`).
  - `build/NN_*.py`: the scripts that built and revised the graph, in order.
  - `registry.json`: node name → uid for every graph.
  - `research/`: notes and sources. `review/`: `REFERENCE.md`, `round<N>/` (suite.json, scorecards, wrong builds,
    previews, ledger, fixcheck, brief, panel).

## User requirements (acceptance criteria)
1. <verbatim>
...
User choices: <interview answers>. Intentional deviations: <if any>.

## Architecture in one paragraph
<layout → randoms → as-built → layers → drivers → process masks → composition with guards → colour → roughness → outputs>
The invariants are enforced by structure. <Name the enforcing nodes.>

## How to edit
```python
import sys, importlib
K = "<skill>/scripts"
if K not in sys.path: sys.path.insert(0, K)
import sdkit as sk; importlib.reload(sk)
sk.configure("<tools>")                 # loads registry.json
sk.use("<m>_materials.sbs::<m>_core")   # the key new_graph registered
...
```
After any graph change:
1. run the layout
2. save
3. export
4. run the suite from a background shell,
   `$PY <skill>/scripts/suite.py <tools>/SUITE.json --out <tools>/review/round<N>` (`--configs` and `--kinds` for a
   targeted set), and read its `suite.json` (`suite_partial.json` after a targeted set, which never closes a round):
   `green`, `rc`, `full`, `red`; a `suite.json` that started before the last export is red, and a targeted set moves
   it aside (`references/checks.md`, "Suite")
5. with a fix ledger, run `$PY <skill>/scripts/fixcheck.py --ledger <tools>/review/round<N>/ledger.json` and read
   its `fixcheck/fixcheck.json` (`references/review.md` §1 step 4)
6. compare against the table below

## Current measured state (2048)
| check | variant A | variant B | variant C |
|---|---|---|---|

The last review scorecard: <...>.

## Open items
1. ...

Re-check the hard invariants after every change: <list check ids>.

## What I'd like to do next
<describe the next change here>

---

# Panel hand-off (written at lens launch)

The old session writes this block, from its `##` heading to the end, when the panel's Workflow call returns
(`references/review.md` §6). It goes first in `<tools>/CONTEXT_PROMPT.md`: above the material hand-off if the file has
one, replacing an older panel block. After the plan gate the new session rewrites its `Next:` line as `Spent: ...`
(`references/review.md` §6), so a resumed session skips it. The end-of-material hand-off (above) drops it.

Kick-off line for the new session. The old session gives it to the user in a code block and tells them: open it in a new
window or tab and keep the old session open (no `/exit`, `/clear` or archive) until it says the panel finished;
closing it may stop the panel.
```
Use sd-material-research to resume <material> round <N> under its running review panel: read "<tools>/CONTEXT_PROMPT.md", the panel hand-off first.
```

## Panel hand-off: round <N>
The old session launched round <N>'s review panel and only waits for it. This session owns the tools folder and is
the only Designer caller. Follow `references/review.md` §6, new session.
- Round <N>. Run ID `<run id>`. Transcript dir `<session dir>/subagents/workflows/<run id>` (`journal.jsonl`).
- Old session `<session id>`, folder `<session dir>`: the runner's return lands in `workflows/<run id>.json` at
  completion. Panel launch: <UTC>.
- Tools folder `<tools>`, package `<path>.sbs`. Requirements and architecture: `spec.md`, `review/REFERENCE.md`.
- Measured state, after the <exported_at> export: `review/round<N>/suite.json` <green, rc, full>; per variant, from
  `review/round<N>/scorecard_<variant>.json` <hard_failed, hard_unmeasured, soft_failed>; or <no `checks/` configs,
  gate waived by the user>; fixcheck: <rc, items not landed; none in round 1>.
- Ledger: `review/round<N>/ledger.json` (the last apply; none in round 1). This round's apply goes in
  `review/round<N+1>/ledger.json`, with `apply.split`.
- Drafts: `review/drafts/round<N>/`.
- Next: stamp your start and your effort (`SKILL.md` Effort); draft from the lens and verdict files as they land (a
  Monitor on `review/round<N>/`); wait for `lead.json`; reconcile the drafts; the plan gate from `lead.json` (every design call in one batch); while the user answers, save
  `review_result.json` once the run ends and write findings.md and the next ledger's rows; on the answer, mark this
  block spent; apply only once findings.md is newer than `lead.json`.
