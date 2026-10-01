# Context: Substance Designer 2022 <-> Claude bridge, phase 5 (confirm phase 4 live)

## Situation
I'm on Windows 10 with the Steam edition of Substance 3D Designer 2022, 12.4.1 build 6587 (bundled Python 3.9.9, PySide2). This folder holds a bridge that lets Claude drive Designer through MCP: a Designer plugin (`designer_plugin/sd_claude_bridge`) and a FastMCP stdio server (`mcp_server/sd_designer_mcp.py`, 19 tools).

History:
- Phases 1-3 (2026-09-30 to 10-01): install, verify all tools, run the README brick workflow, fix what it found.
- Phase 4 (2026-10-01):
  - Confirmed the phase-3 server changes in a live session.
  - Reran the brick prompt with a blind subagent.
  - Found that Claude Code cuts MCP server instructions at exactly 2048 characters (ours were 2662, so the end never arrived).
  - Added the features below and ran two multi-agent review rounds.

The plugin changes were tested live after a hot reload. The server changes were tested only through the new harness `tools/tool_call.py`, not through a live session. This session confirms them live and closes the loose ends.

## What phase 4 changed
Server (`sd_designer_mcp.py`):
- **INSTRUCTIONS:** rewritten to 1959 characters.
  - The render_preview details moved into that tool's docstring.
  - The delete rule now reads "Don't save, or delete nodes you didn't create, unless the user asks." This matches the `delete_nodes` docstring.
  - The base-parameter sentence again says enums like `$format` are "ignored and inherited", not offsets.
- **`--check` guard:** `MAX_TEXT = 2048`. `--check`, which the installer runs, exits 1 if INSTRUCTIONS or any tool description is longer.
- **render_preview:**
  - Captions append `, WxH px` from the plugin's per-image `size`.
  - The docstring covers three more points: only nodes that feed an Output are computed (wire one, then delete it afterwards), alpha comes as a second image, and captions give the computed size.
- **search_library docstring:** matches file names or node labels. A match with `graph_identifier` means passing both values. Atomic nodes (Levels, Blur, Emboss) aren't in the library.

Plugin (`commands.py`):
- **search_library:**
  - If the file name doesn't match, it matches the label and id of each shown graph. Such hits carry `graph_identifier` ("color dodge" gives `blend.sbs` with `color_dodge`).
  - Order: shown file-name matches, then label matches, then hidden ones.
  - The first call parses all 485 packages (about 1.94 s on the main thread), then takes about 7 ms (cached by mtime).
- **get_node:** adds `description` to inputs and parameters whose id doesn't start with `$`.
  - The HTML becomes text: block tags turn into spaces, other tags are stripped, entities are unescaped.
  - Descriptions are capped at 300 characters.
- **get_graph:**
  - Adds `graph_params`: the graph's own parameters, with `inheritance` on the `$` ones.
  - Adds `graph_params_note` when `$outputsize` isn't Absolute.
- **render:** each image gets `size: [w, h]` from `tex.getSize()`.
- **save_package:** refuses a `save_as` that isn't None and isn't a non-blank string. Before, `""` or `False` fell through to overwriting the package's own file.

New `tools/tool_call.py`:
- **What it does:** imports the installed server, or the repo copy with `--source`, and runs `mcp.call_tool` in-process (pydantic validation plus the live bridge).
- **Arguments:** `key=value` pairs (schema-aware, so numeric node ids stay strings), or JSON inline, from `@file` or from `-` (stdin). UTF-8, UTF-8 with BOM and UTF-16 are all read.
- **Other modes:** `--raw` sends bridge commands, `--list` lists the tools.
- **Safety:** it refuses unknown keys and empty string values.
- **Output:** images are saved to `%TEMP%\sd_claude_bridge\tool_call`.

Last installed: server file 2026-10-01 00:49:56, plugin `commands.py` 01:02:05. VERSION stays 1.0.0 (I declined the bump in phase 3).

## Where things are
- Designer: `G:\SteamLibrary\steamapps\common\Substance 3D Designer 2022`.
  - The `sd` API source is in `resources\python\sd\api`.
  - Adobe's API tests (and the property dumps in `tests\assets`) are in `resources\python\tests`.
  - The library packages are in `resources\packages`.
  - The bundled interpreter is `plugins\pythonsdk\python.exe`.
- Installed plugin: `Documents\Allegorithmic\Substance Designer\python\sduserplugins\sd_claude_bridge`. The Steam edition uses the Allegorithmic folders, not the Adobe ones.
- Designer log: `%LOCALAPPDATA%\Allegorithmic\Substance Designer\log.txt`. It has the `[Claude bridge] ... listening` line, the build number, and any traceback that escapes the plugin.
- Installed MCP server: `%LOCALAPPDATA%\sd-claude-bridge`, with its venv inside. It's registered at user scope in `%USERPROFILE%\.claude.json` (`claude` isn't on PATH).
- Harness: `"%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" tools\tool_call.py <tool> key=value ...`
- Bridge session file: `%USERPROFILE%\.sd_claude_bridge\session.json`. Previews: `%TEMP%\sd_claude_bridge\previews`.

## Already established (don't redo)
From phases 2-3:
- `APIException` derives from `BaseException`. commands.py catches `ERRORS = (Exception, APIException)`, and bridge.py's `_handle` catches `BaseException` so every request gets a reply. Keep that pattern.
- From an input, `SDConnection.getOutputProperty*` returns the queried input, not the upstream node. `_far_end()` handles this.
- `compute()` only cooks nodes that feed an Output node. There's no API to open a graph in the editor.
- Blends on 12.4.1: a color Blend skips a grayscale `source`, and a grayscale Blend reads a color `source` as black. A grayscale `opacity` mask is fine.
- Library enums:
  - `sFromValueId` raises ItemNotFound for enums declared by library graphs. An `SDValueInt` holding the enumerator's value works.
  - Their ids are the dropdown labels, and some are numbers ("90").
- Gradient keys are the struct `sbs::compositing::gradient_key_rgba` (`value`, `position`, `midpoint`). Designer writes `midpoint` 0.
- Legacy packages: `hideInLibrary=1`. The current version is usually a prefixed file or a `*_2` graph in the same file. `blend.sbs` is a collection of current blend-mode nodes.
- Undo:
  - Opening and closing a user package are undo steps of their own.
  - An empty `run_python` adds no undo step.
  - To test undo, ask me to press Ctrl+Z one press at a time.
- Graph wrappers of the same object have different `mHandle`s. Compare `getUrl()`.

From phase 4:
- **Truncation:** Claude Code truncates MCP server instructions at exactly 2048 characters. Phase 4's own session saw them end at "...when desig… [truncated]". Keep the guard on tool descriptions too.
- **Parent size:** `SDSBSCompGraph.getDefaultParentSize()` returns INT_MIN (unset) on 12.4.1. The pixel size of a graph is only knowable from a computed texture.
- **Descriptions:** `SDProperty.getDescription()` returns HTML.
  - Library descriptions use `b`, `i`, `br`, `h4`, `li`, `ul` and `p`. Atomic ones use `b`, `i`, `font` and `sup`.
  - The `$` base parameters all carry the same boilerplate, so get_node skips them.
- **Normal node:** `inversedy` true means OpenGL. The default, false, is DirectX.
- **Library listing:** a search for "emboss" lists Emboss With Gloss, Spot Emboss and Uber Emboss, plus the atomic Emboss. A graph with a label and no category counts as shown.
- **Quote stripping:** Windows argument parsing (cmd and Windows PowerShell 5.1) strips unescaped double quotes. Pass JSON containing quotes to the harness through `@file` or stdin.
- **Fallback limits:** pydantic rejects non-string `save_as` over MCP. The plugin guard exists for `--raw` and other direct callers.
- **Repo hygiene:** `py_compile` writes `__pycache__` into the repo. Use `compile()` or `sys.dont_write_bytecode = True`, and keep the repo free of `__pycache__`.
- **Sandbox:** in phase 4 it blocked a PowerShell command that combined a Python run with a `Remove-Item` ("system path 'e:'"). Run cleanup as its own command.
- **Blind reruns:** a subagent given only the user prompt and the scratch-graph rules is a good way to find friction in the tools.
- **Hot reload:** commands.py was hot-reloaded several times in phase 4. Until Designer restarts, tracebacks show odd `dispatch` line numbers.

## Tasks
1. **Confirm the server changes are live.**
   - Check that this session's server process (`Get-CimInstance Win32_Process`, command line containing `sd_designer_mcp`, parent = this session's claude.exe) started after the installed `sd_designer_mcp.py` was last written. Ignore old sessions' server processes. If it didn't start after, stop and tell me.
   - Check that this session's substance-designer instructions are complete:
     - no "[truncated]";
     - they end with "run_python covers anything the other tools don't.";
     - they contain "delete nodes you didn't create" and "ignored and inherited (enums like $format)".
     If they're still cut off, stop and tell me how many characters arrived.
   - Check that `render_preview` captions include `, WxH px`, e.g. "baseColor (id), 256x256 px". The normal output must still come as "color channels" plus "alpha channel (values ...)".
   - Check that the `search_library` tool description mentions node labels and `graph_identifier`.
2. **Fresh plugin load.**
   - Check the log. If Designer hasn't started since 2026-10-01 01:02 (the last `[ApplicationVersion]` line in the log is older), ask me to restart it so the plugin loads without the hot reloads.
   - After a fresh load, confirm through the live tools:
     - `search_library("color dodge")` returns `blend.sbs` with `graph_identifier` `color_dodge`, and `create_library_node` with it works;
     - `get_node` on a Normal shows descriptions;
     - `get_node` on a 3D Perlin Noise Fractal (`3d_perlin_noise.sbs`, `3D_perlin_noise_fractal`) reads "fractal pattern. Note A value of 0...", not run together;
     - `get_graph` shows `graph_params` and the note;
     - `save_package(graph="claude_smoke_test", save_as="")` is refused. The scratch package is unsaved, so the old code would only have raised "never been saved".
3. **Clean up.** The phase-4 scratch package (unsaved, graph `claude_smoke_test`, holding the brick material) may still be open.
   - If it is, you may use it for the read-only checks above.
   - Ask me to close it without saving before you call `create_graph` (it refuses duplicate names).
   - If Designer was restarted, the package is gone.
4. **Blind brick rerun with the full instructions.**
   - Give a subagent only the README prompt ("Build a simple brick material: tile generator for bricks, a noise for variation, and baseColor, normal, roughness and height outputs. Show me a preview.") and the scratch-graph rules: work in `claude_smoke_test`, no run_python, no saves, delete only its own nodes. Have it log every call and any friction.
   - Compare the result with phase 4's friction list:
     - `render_preview(node=X)` can't preview a node with nothing downstream;
     - `current_graph` is null because the scratch graph isn't open in the Graph view;
     - library parameters had no meanings (`interstice` component order, Normal format);
     - two Blend parameters are both labelled "Alpha Blending";
     - `midpoint` 0 is unexplained;
     - the graph resolution was invisible;
     - the `$` base parameters make get_node output noisy.
   - Check that the agent now uses the descriptions, `graph_params` and size captions, and that it cleans up any temporary Output it adds.
   - Then check its graph yourself with `get_graph` and `render_preview`.
5. **Optional. Ask me before each one.**
   - README:
     - a short "Development" note on `tools/tool_call.py`;
     - the "Tested on" line (I declined it in phase 4, so just ask).
   - `search_library`: also return matching atomic node ids (from `list_node_definitions`), so "levels" or "emboss" points to `create_node`.
   - `get_node`: a compact option that leaves out the six `$` base parameters (or shows them only when they aren't the defaults).
   - `get_graph`: when the node list is truncated by `limit`, only list connections between listed nodes, or say that more exist.
   - The render_preview summary's `rendered` counts textures, not images. Rename it, or add an image count.
   - Previewing unwired nodes via a temporary Output inside an undo group. This is a trade-off: it adds an entry to the undo history and temporarily edits the graph. Describe it before doing anything.

## Rules (same as phase 4)
- **Scratch only.** Never modify, save or delete anything in my own packages. Work only in a scratch graph: call `create_graph` with identifier `claude_smoke_test` (it goes into a new unsaved package), then pass `graph="claude_smoke_test"` to every tool. Save only if I agree, and only with save_as into `%TEMP%`.
- **Install from source.** Edit the source in this folder, then run `powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -SkipClaudeConfig` so the installed copies match. The installer's `--check` must print `MCP server OK: 19 tools`.
- **Hot reload.** Hot-reload commands.py with run_python: `import importlib, sys; m = next(v for k, v in sys.modules.items() if k.endswith("sd_claude_bridge.commands")); importlib.reload(m)`. This swaps the handlers but not `dispatch()` itself. Changes to `dispatch`, bridge.py or `__init__.py` need a Designer restart, so ask me.
- **Plugin compatibility.** Plugin code must stay Python 3.7 compatible and stdlib only. Check with `ast.parse(source, feature_version=(3, 7))`.
- **Probing.** Probe the API with run_python inside `try/except BaseException`. When probing setters, only set values you know are already current.
- **MCP server.**
  - Never print to stdout.
  - Keep INSTRUCTIONS and every tool description at 2048 characters or less; `--check` enforces it.
  - Test server edits with `tools/tool_call.py` (`--source` for the repo copy), then I start a new session to load them.
- **Designer's window.** You can't see it, so ask me what's on screen. You can read the log file yourself.
- **Run reviews offline.** Review subagents must not call the substance-designer tools while you're using them.

## When done
Give me a short report: what passed, what you changed and why, and anything still broken. Update the memory file `bridge-verification-status`.
