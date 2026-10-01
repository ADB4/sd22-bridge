# Context: Substance Designer 2022 <-> Claude bridge, phase 4 (confirm phase 3 live)

## Situation
I'm on Windows 10 with the Steam edition of Substance 3D Designer 2022, 12.4.1 build 6587 (bundled Python 3.9.9, PySide2). This folder holds a bridge that lets Claude drive Designer through MCP: a Designer plugin (`designer_plugin/sd_claude_bridge`) and a FastMCP stdio server (`mcp_server/sd_designer_mcp.py`, 19 tools). Phase 1 (install) and phase 2 (verify every tool) were finished on 2026-09-30. Phase 3 (finished 2026-10-01) ran the README brick workflow, fixed what it turned up, and went through two multi-agent review rounds. The plugin changes were tested live after a hot reload. The server changes were tested only by importing the installed module and calling `mcp.call_tool`, not through a live session. This session confirms them live and closes the loose ends.

## What phase 3 changed
Plugin (`commands.py`):
- `set_parameter`:
  - Library-graph enums now work, including numeric labels (Tile Generator `pattern`, and `pattern_rotation` "90").
  - Gradient Map `gradientrgba` keys can be set.
  - Clear errors for image slots (connectable and read-only), function-only parameters and read-only parameters, a readable reason for any APIException, and a note when a function graph drives the value.
- `get_node` shows struct values (gradient keys) as `{"position", "value", "midpoint"}`.
- `search_library`:
  - Adds a label to every match, and a `hidden_in_library` flag on legacy and helper packages, which are listed last.
  - Lists `graphs` when a package has several shown graphs.
  - Reads each matched .sbs's XML, with caching.
- `create_library_node`:
  - Loading the package, instancing and unloading happen in one undo group.
  - The default graph skips hidden helpers and deprecated versions.
- `render_preview` labels node previews by node label, and adds a note for Blends whose `source` is the other kind.
- `create_graph` refuses an identifier that's already open in another package. `graph=` resolves duplicates to the graph shown in the Graph view, and accepts `"<full .sbs path>::id"`.

Server (`sd_designer_mcp.py`):
- `render_preview`:
  - When alpha varies, it comes as a second grayscale image.
  - Captions name the output when a node has several.
  - PNGs shrink to stay under about 3.5 MB.
- The `set_parameter` value type accepts nested gradient-key lists and objects.
- INSTRUCTIONS cover legacy packages, gradient keys, Blend behavior and alpha previews. The `get_graph` docstring documents the full-path form.

VERSION stays 1.0.0 (I declined the bump).

## Where things are
- Designer: `G:\SteamLibrary\steamapps\common\Substance 3D Designer 2022`. The `sd` API source is in `resources\python\sd\api`, Adobe's API tests (and the property dump `tests\assets\test_read_content.txt`) are in `resources\python\tests`, and the library packages are in `resources\packages`.
- Installed plugin: `Documents\Allegorithmic\Substance Designer\python\sduserplugins\sd_claude_bridge`. The Steam edition uses the Allegorithmic folders, not the Adobe ones.
- Designer log: `%LOCALAPPDATA%\Allegorithmic\Substance Designer\log.txt`. It has the `[Claude bridge] ... listening` line, the build number, and any traceback that escapes the plugin.
- Installed MCP server: `%LOCALAPPDATA%\sd-claude-bridge`, with its venv inside. It's registered at user scope in `%USERPROFILE%\.claude.json` (`claude` isn't on PATH).
- Bridge session file: `%USERPROFILE%\.sd_claude_bridge\session.json`. Previews: `%TEMP%\sd_claude_bridge\previews`.

## Already established (don't redo)
From phase 2:
- `APIException` derives from `BaseException`. commands.py catches `ERRORS = (Exception, APIException)`, and bridge.py's `_handle` catches `BaseException` so every request gets a reply. Keep that pattern.
- From an input, `SDConnection.getOutputProperty*` returns the queried input, not the upstream node. `_far_end()` handles this.
- `compute()` only cooks nodes that feed an Output node. There's no API to open a graph in the editor, and the Edit menu shows only "Undo", without action names.
- Reconnecting the server with /mcp left the old process running. A new session is the reliable way to load server changes.

From phase 3:
- Blends on 12.4.1: a color Blend skips a grayscale `source` (its output equals the destination exactly), and a grayscale Blend reads a color `source` as black. A grayscale `opacity` mask is fine.
- `SDTexture.getPixelFormat()` returns `SBSPixelFormat` (`LUM16`, `RGBA16`, ...).
- The Normal node's `input2alpha` defaults to on, which puts the height in alpha. Shape Glow puts its whole result in alpha, over white RGB.
- Library enums:
  - `SDValueEnum.sFromValueId` and `sFromValue` raise ItemNotFound for enums declared by library graphs. An `SDValueInt` holding the enumerator's value works.
  - Library enum ids are the dropdown labels, and some are numbers.
- Gradient keys are the struct `sbs::compositing::gradient_key_rgba` with members `value`, `position` and `midpoint`. Designer writes `midpoint` 0.
- Legacy packages:
  - `hideInLibrary=1` marks the "(Legacy)" and "(Deprecated)" graphs. About 138 packages are legacy, for example `tile_generator.sbs` and `clouds_2.sbs`.
  - The current version is usually a prefixed file (`pattern_tile_generator.sbs`, `noise_clouds_2.sbs`), or a `*_2` graph in the same file (`normal_sobel_2`).
  - `blend.sbs` is a collection of current blend-mode nodes (Difference, Color Dodge, ...).
- Undo:
  - Opening and closing a user package are undo steps of their own.
  - An empty `run_python` adds no undo step.
  - To test undo, ask me to press Ctrl+Z or Redo one press at a time, then read back with `get_graph` and `list_packages`.
- Graph wrappers of the same object have different `mHandle`s. Compare `getUrl()`, which differs per package.
- Function-only inputs are `pixelprocessor.perpixel` and `valueprocessor.function`. Image slots are connectable and read-only. MDL and Model value inputs are connectable but not read-only, and can be set.
- Testing server code without a new session:
  - In the venv python, add `%LOCALAPPDATA%\sd-claude-bridge` to `sys.path`, `import sd_designer_mcp as m`, then `await m.mcp.call_tool(name, args)` (this runs pydantic validation and the tool) or call `m.call(cmd, args)` for raw bridge commands.
  - PowerShell pipes add a BOM, so decode stdin with `utf-8-sig`.
  - Tool-call arguments arrive as parsed JSON, so a JSON string you write in a tool call keeps its quotes.

## Tasks
1. **Confirm the server changes are live.**
   - Check that this session's server process (`Get-CimInstance Win32_Process`, command line containing `sd_designer_mcp`, parent = this session's claude.exe) started after the installed `sd_designer_mcp.py` was last written. If it didn't, stop and tell me. Old sessions' server processes may still be running; ignore them.
   - Check that this session's substance-designer instructions mention `hidden_in_library` and say alpha comes as a second image.
   - In a scratch graph, feed a noise into a Normal node, then into an Output. `render_preview` must return two images for it, captioned "color channels" and "alpha channel (values ...)".
   - On a Gradient Map, `set_parameter("gradientrgba", [[0, "#3b3530"], [1, [0.63, 0.32, 0.18]]])` must pass validation with no pydantic error, and `get_node` must then show two keys.
   - Feed a Tile Generator into a Shape Glow (`shape_glow.sbs`), then into an Output. `render_preview(node=<glow>)` captions must name output `output` and output `mask`.
2. **Clean up.** The phase 3 scratch package (unsaved, graph `claude_smoke_test`, with extra test Blends) may still be open. `create_graph` now refuses a duplicate name, so ask me to close it without saving before you create the new scratch graph. If Designer was restarted, it's gone; check the log for the listening line.
3. **Brick rerun through the live tools only (no run_python).** Run the README prompt again: "Build a simple brick material: tile generator for bricks, a noise for variation, and baseColor, normal, roughness and height outputs. Show me a preview." Check that the search leads to `pattern_tile_generator` and `noise_clouds_2` without help, that the gradient keys go through `set_parameter`, and that the normal preview shows alpha separately. Note anything awkward, not just errors.
4. **Optional. Ask me before each one.**
   - Ask me to search Designer's Library for "Spot Emboss". The code treats `spot_emboss.sbs` as shown (it has a label and a tag, but no category). If the Library doesn't list it, adjust `_library_graphs`.
   - `search_library` matches file names only, so "color dodge" doesn't find `blend.sbs`. Matching labels too means parsing all 485 packages once (about 1.9 s on Designer's main thread, then cached).
   - Add a small test harness to the repo (for example `tools/tool_call.py`) that runs tool calls through the installed server code, so later sessions can test server changes without a restart.
   - Update the README "Tested on" line.

## Rules (same as phase 3)
- Never modify, save or delete anything in my own packages. Work only in a scratch graph: call `create_graph` with identifier `claude_smoke_test` (it goes into a new unsaved package), then pass `graph="claude_smoke_test"` to every tool. Save only if I agree, and only with save_as into `%TEMP%`.
- Edit the source in this folder, then run `powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -SkipClaudeConfig` so the installed copies match.
- Hot-reload commands.py with run_python: `import importlib, sys; m = next(v for k, v in sys.modules.items() if k.endswith("sd_claude_bridge.commands")); importlib.reload(m)`. This swaps the handlers but not `dispatch()` itself. Changes to `dispatch`, bridge.py or `__init__.py` need a Designer restart, so ask me.
- Plugin code must stay Python 3.7 compatible and stdlib only. Check with `ast.parse(source, feature_version=(3, 7))`.
- Probe the API with run_python inside `try/except BaseException`, so a mistake can't hang the call. When probing setters, only set values you know are already current: in phase 3 a guessed enum int (8 instead of 9) silently changed the Tile Generator's pattern.
- MCP server: never print to stdout. After editing, the installer runs `--check`. Test through the installed module as above, then I start a new session to load it.
- You can't see Designer's window, so ask me what's on screen. You can read the log file yourself.

## When done
Give me a short report: what passed, what you changed and why, and anything still broken.
