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
  - `checks/<variant>.json`: the numeric checks, run with `<skill>/scripts/matcheck.py`.
  - `build/NN_*.py`: the scripts that built and revised the graph, in order.
  - `registry.json`: node name → uid for every graph.
  - `research/`: notes and sources. `review/`: `REFERENCE.md`, scorecards, `round<N>/` (brief, ledger, panel, previews).

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
4. run `matcheck.py` for every variant
5. compare against the table below

## Current measured state (2048)
| check | variant A | variant B | variant C |
|---|---|---|---|

The last review scorecard: <...>.

## Open items
1. ...

Re-check the hard invariants after every change: <list check ids>.

## What I'd like to do next
<describe the next change here>
