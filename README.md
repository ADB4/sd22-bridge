# Substance Designer bridge for Claude

Lets Claude read and edit graphs in Adobe Substance 3D Designer 2022 (12.x) on Windows 10. It has two parts:

- `designer_plugin/sd_claude_bridge` runs inside Designer. It opens a local socket on `127.0.0.1:9881` and executes commands on Designer's main thread. It needs nothing beyond Designer's own Python.
- `mcp_server/sd_designer_mcp.py` runs outside Designer under Python 3.10+. Claude Desktop (or Claude Code) starts it and it forwards tool calls to the plugin.

```
Claude Desktop --stdio--> sd_designer_mcp.py --127.0.0.1:9881--> plugin inside Designer --> sd API
```

## Requirements

- Windows 10 or 11
- Substance 3D Designer 2022 (12.x). Later versions should work too, but 2022 is the target.
- Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/). Use the 64-bit installer and tick "Add python.exe to PATH". This is separate from the Python inside Designer.
- Claude Desktop, or Claude Code

Tested on: Substance 3D Designer 12.4.1 build 6587 (Steam edition, Python 3.9.9), Windows 10 Pro 22H2, with Claude Code, 2026-09-30.

## Install

1. Right-click the downloaded zip > Properties > tick **Unblock** > OK, then extract it anywhere.
2. Double-click `install.bat`. If SmartScreen says "Windows protected your PC", click **More info > Run anyway**.
   The script:
   - copies the plugin to Designer's user plugin folder, whichever of these exists:
     - `Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins` (Adobe installs)
     - `Documents\Allegorithmic\Substance Designer\python\sduserplugins` (Steam edition)
   - creates a Python environment in `%LOCALAPPDATA%\sd-claude-bridge` and installs `mcp` and `pillow`
   - offers to add a `substance-designer` entry to Claude Desktop's config (backing up the old file)
3. Start Substance Designer (restart it if it was open). Open **Windows > Console**. You should see:
   ```
   [Claude bridge] v1.0.0 listening on 127.0.0.1:9881
   ```
   If the line is missing, see "Plugin doesn't load" below.
4. Quit Claude Desktop completely: right-click its tray icon > **Quit** (closing the window isn't enough). Open it again.
5. In Claude Desktop, check **Settings > Developer**: `substance-designer` should show as running. In a chat, the tools menu lists its tools.
6. Open a graph in Designer, then ask Claude: "Check the Designer connection."

## Things to ask

- "What's in the open graph? Explain how it works."
- "Add a Perlin noise and a Levels node, and blend the noise over the existing base color at 40%."
- "Build a simple brick material: tile generator for bricks, a noise for variation, and baseColor, normal, roughness and height outputs. Show me a preview."
- "Set every node's output size to 2048."
- "Rename all output identifiers to lowercase." (uses `run_python`)

Each edit Claude makes is one Ctrl+Z step in Designer if your build supports undo groups (`designer_status` reports `undo_groups`). Claude won't save the package unless you ask.

## Tools

| Tool | What it does |
| --- | --- |
| `designer_status` | Connection check, versions, current graph |
| `list_packages` | Open packages and their graphs |
| `get_graph` | Nodes, positions and connections of a graph |
| `get_node` | One node's inputs, parameters (with descriptions), options and outputs |
| `get_selection` | Nodes selected in the Graph view |
| `list_node_definitions` | Search atomic node ids |
| `search_library` | Find library nodes (noises, patterns, filters) and matching atomic nodes; legacy versions are flagged |
| `create_node` | Add an atomic node |
| `create_library_node` | Add a library node |
| `create_output` | Add an Output node with a PBR usage |
| `connect_nodes`, `disconnect_input` | Wire and unwire ports |
| `set_parameter` | Change a node's or the graph's parameter (numbers, vectors, colors, enums, strings, Gradient Map keys) |
| `move_nodes`, `delete_nodes` | Layout and cleanup |
| `create_graph`, `save_package` | New graph; save when asked |
| `render_preview` | Compute the graph and show Claude the output images (alpha, when used, as a separate image) |
| `run_python` | Run code inside Designer for anything else |

## Manual setup

Use this if the installer can't edit the Claude Desktop config, or you'd rather do it yourself.

1. In Claude Desktop, open **Settings > Developer > Edit Config**. This opens the folder with `claude_desktop_config.json`.
2. Add the entry below inside `"mcpServers"` (create that object if it isn't there). Replace `YOU` with your Windows user folder name, and keep the doubled backslashes:
   ```json
   {
     "mcpServers": {
       "substance-designer": {
         "command": "C:\\Users\\YOU\\AppData\\Local\\sd-claude-bridge\\venv\\Scripts\\python.exe",
         "args": ["C:\\Users\\YOU\\AppData\\Local\\sd-claude-bridge\\sd_designer_mcp.py"]
       }
     }
   }
   ```
3. Quit Claude Desktop from the tray icon and reopen it.

For Claude Code:

```
claude mcp add --scope user substance-designer -- "%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" "%LOCALAPPDATA%\sd-claude-bridge\sd_designer_mcp.py"
```

## Troubleshooting

### Plugin doesn't load

No "listening" line in Designer's Console:

1. Check that `sd_claude_bridge\__init__.py` exists in `Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins` (Adobe installs) or `Documents\Allegorithmic\Substance Designer\python\sduserplugins` (Steam edition). If your Documents folder is in OneDrive, look there. If Designer had never been started when you ran the installer, start it once, then run `install.bat` again.
2. In Designer, open **Tools > Plugin Manager**. If `sd_claude_bridge` is listed but unchecked, enable it. If it isn't listed, click **Browse** and pick `__init__.py` inside the `sd_claude_bridge` folder.
3. To load it automatically every launch, add the `sduserplugins` folder as a plugin path: **Edit > Preferences > Projects**, select your project file, open the **Python** tab, click **+** and choose the `sduserplugins` folder. Restart Designer.
4. If the Console shows `[Claude bridge] failed to start` with a traceback, that text explains why. A port conflict is handled automatically (it tries 9881 to 9890).

### Claude says the bridge is not running

- Designer must be open with the plugin loaded (step above).
- The plugin writes `%USERPROFILE%\.sd_claude_bridge\session.json` when it starts. If that file exists but Claude still can't connect, Designer probably crashed: restart it.
- Security software that blocks loopback connections can interfere. The bridge only listens on 127.0.0.1, so allowing it doesn't expose anything to the network.

### `substance-designer` doesn't appear in Claude Desktop

- Quit from the tray icon, not the window close button.
- **Settings > Developer** shows the server's error. Open the log there: a wrong path in the config is the usual cause.
- Run the server by hand to check it: `"%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" "%LOCALAPPDATA%\sd-claude-bridge\sd_designer_mcp.py" --check`. It should print `MCP server OK: 19 tools`.

### A tool fails on my Designer build

The plugin targets the 2022 Python API. If one structured tool fails, Claude can usually do the same thing with `run_python`, which runs any `sd` API code. Errors include the last lines of the Designer-side traceback. Designer's API reference is under **Help > Python API Documentation**.

### Previews are empty

`render_preview` computes the graph and saves output textures to `%TEMP%\sd_claude_bridge\previews`. Designer only computes nodes that feed an Output node, so a node with nothing downstream has no preview. Connect it to an Output node and preview that.

## Security

- The plugin listens on `127.0.0.1` only, and every request must carry a random token that changes each time Designer starts. The token is in `%USERPROFILE%\.sd_claude_bridge\session.json`.
- `run_python` executes arbitrary code inside Designer, so any program running as your Windows user that can read the session file could do the same. To turn it off, set a user environment variable `SD_CLAUDE_BRIDGE_ALLOW_PYTHON=0` and restart Designer.
- Change the port with `SD_CLAUDE_BRIDGE_PORT` (Designer side). The MCP server finds the port from the session file.

## Uninstall

Close Designer and Claude Desktop, then double-click `uninstall.bat`. It removes the plugin, the Python environment, the session and preview files, and the Claude Desktop config entry (with a backup).

## Development

A Claude session keeps the MCP server it started with, so edits to `sd_designer_mcp.py` reach Claude only in a new session. `tools\tool_call.py` lets you try a tool call from a shell instead. It imports the server and runs the call in-process, with the same argument validation, over the bridge to Designer (which must be running with the plugin loaded). Run it with the server's Python:

```
"%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" tools\tool_call.py search_library query="color dodge"
```

- Arguments are `key=value` pairs. A value is read as JSON when it parses; node ids stay strings.
- Or pass one JSON object: inline, as `@args.json`, or `-` for stdin. Windows drops unescaped double quotes from command-line arguments, so JSON with strings in it is safest in a file or on stdin.
- `--list` lists the tools. `--source` loads `mcp_server\` from this folder instead of the installed copy, to try an edit before running `install.ps1`. `--raw` sends a bridge command (the plugin's command names) and skips the MCP layer.
- Unknown parameter names are refused, since the server would quietly drop them, and so are empty names and paths such as `graph=` or `save_as=`. `--raw` has no schema to check against: there, a misspelled `save_as` is dropped and `save_package` overwrites the package's own file.
- Images are saved to `%TEMP%\sd_claude_bridge\tool_call`.
