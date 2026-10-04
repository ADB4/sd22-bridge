# Substance Designer bridge for Claude

Lets Claude read and edit graphs in Adobe Substance 3D Designer 2022 (12.x) on Windows 10/11 and macOS. It has two parts:

- `designer_plugin/sd_claude_bridge` runs inside Designer. It opens a local socket on `127.0.0.1:9881` and executes commands on Designer's main thread. It needs nothing beyond Designer's own Python.
- `mcp_server/sd_designer_mcp.py` runs outside Designer under Python 3.10+. Claude Desktop (or Claude Code) starts it and it forwards tool calls to the plugin.

```
Claude Desktop --stdio--> sd_designer_mcp.py --127.0.0.1:9881--> plugin inside Designer --> sd API
```

## Requirements

- Windows 10 or 11, or macOS
- Substance 3D Designer 2022 (12.x). Later versions should work too, but 2022 is the target.
- Python 3.10 or newer. This is separate from the Python inside Designer.
  - Windows: [python.org](https://www.python.org/downloads/windows/). Use the 64-bit installer and tick "Add python.exe to PATH".
  - macOS: [python.org](https://www.python.org/downloads/macos/) (the universal2 installer), or `brew install python@3.12`. The `python3` that comes with macOS is too old.
- Claude Desktop, or Claude Code

Tested on: Substance 3D Designer 12.4.1 build 6587 (Steam edition, Python 3.9.9), Windows 10 Pro 22H2, with Claude Code, 2026-09-30. macOS: the same Designer build on macOS 15.7 with Claude Code, 2026-10-02.

## Install on Windows

1. Right-click the downloaded zip > Properties > tick **Unblock** > OK, then extract it anywhere.
2. Double-click `install.bat`. If SmartScreen says "Windows protected your PC", click **More info > Run anyway**.
   The script:
   - copies the plugin to Designer's user plugin folder, into each of these that exists:
     - `Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins` (Adobe installs)
     - `Documents\Allegorithmic\Substance Designer\python\sduserplugins` (Steam edition)
   - creates a Python environment in `%LOCALAPPDATA%\sd-claude-bridge` and installs `mcp` and `pillow`
   - offers to add a `substance-designer` entry to Claude Desktop's config (backing up the old file)

   To leave Claude Desktop's config alone, run `powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -SkipClaudeConfig` instead.
3. Start Substance Designer (restart it if it was open). Open **Windows > Console**. You should see:
   ```
   [Claude bridge] v1.0.0 listening on 127.0.0.1:9881
   ```
   If the line is missing, see "Plugin doesn't load" below.
4. Quit Claude Desktop completely: right-click its tray icon > **Quit** (closing the window isn't enough). Open it again.
5. In Claude Desktop, check **Settings > Developer**: `substance-designer` should show as running. In a chat, the tools menu lists its tools.
6. Open a graph in Designer, then ask Claude: "Check the Designer connection."

## Install on macOS

1. Double-click the downloaded zip to extract it.
2. Run `install.command`. The reliable way is Terminal: type `sh ` (with the space), drag `install.command` from Finder into the Terminal window, and press Return.
   - Double-clicking `install.command` also works, but macOS may refuse a script downloaded from the internet ("Apple could not verify..."). Use Terminal instead, or allow it under **System Settings > Privacy & Security > Open Anyway**.
   - If macOS asks whether Terminal may access your Documents or Downloads folder, click **Allow**. The plugin goes into Documents.

   The script:
   - copies the plugin to Designer's user plugin folder, into each of these that exists:
     - `~/Documents/Adobe/Adobe Substance 3D Designer/python/sduserplugins` (Adobe installs)
     - `~/Documents/Allegorithmic/Substance Designer/python/sduserplugins` (Steam edition)
   - creates a Python environment in `~/Library/Application Support/sd-claude-bridge` and installs `mcp` and `pillow`
   - offers to add a `substance-designer` entry to Claude Desktop's config (backing up the old file)

   Options: `--skip-claude-config` leaves Claude Desktop's config alone, and `--claude-desktop` adds the entry without asking (for running the installer from Claude Code, which can't answer the prompt).
3. Start Substance Designer (restart it if it was open). Open **Windows > Console** and look for the `[Claude bridge] ... listening` line. If macOS asks whether Designer may accept incoming network connections, click **Allow**: the bridge only listens on 127.0.0.1.
4. Quit Claude completely with **Cmd+Q** (closing the window isn't enough), then open it again.
5. In Claude, check **Settings > Developer**: `substance-designer` should show as running.
6. Open a graph in Designer, then ask Claude: "Check the Designer connection."

## Things to ask

- "What's in the open graph? Explain how it works."
- "Add a Perlin noise and a Levels node, and blend the noise over the existing base color at 40%."
- "Build a simple brick material: tile generator for bricks, a noise for variation, and baseColor, normal, roughness and height outputs. Show me a preview."
- "Set every node's output size to 2048."
- "Rename all output identifiers to lowercase." (uses `run_python`)

Each edit Claude makes, except creating a graph, is one undo step in Designer (Ctrl+Z, or Cmd+Z on a Mac) if your build supports undo groups (`designer_status` reports `undo_groups`). Claude won't save the package unless you ask.

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
2. Add the entry below inside `"mcpServers"` (create that object if it isn't there). Replace `YOU` with your user folder name.

   Windows (keep the doubled backslashes):
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
   macOS:
   ```json
   {
     "mcpServers": {
       "substance-designer": {
         "command": "/Users/YOU/Library/Application Support/sd-claude-bridge/venv/bin/python",
         "args": ["/Users/YOU/Library/Application Support/sd-claude-bridge/sd_designer_mcp.py"]
       }
     }
   }
   ```
3. Quit Claude Desktop (tray icon > Quit on Windows, Cmd+Q on a Mac) and reopen it.

For Claude Code on Windows:

```
claude mcp add --scope user substance-designer -- "%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" "%LOCALAPPDATA%\sd-claude-bridge\sd_designer_mcp.py"
```

For Claude Code on macOS:

```
claude mcp add --scope user substance-designer -- "$HOME/Library/Application Support/sd-claude-bridge/venv/bin/python" "$HOME/Library/Application Support/sd-claude-bridge/sd_designer_mcp.py"
```

## Troubleshooting

### Plugin doesn't load

No "listening" line in Designer's Console:

1. Check that `sd_claude_bridge/__init__.py` exists in the `sduserplugins` folder listed under your platform's install steps. On Windows, if your Documents folder is in OneDrive, look there. If Designer had never been started when you ran the installer, start it once, quit it, then run the installer again.
2. In Designer, open **Tools > Plugin Manager**. If `sd_claude_bridge` is listed but unchecked, enable it. If it isn't listed, click **Browse** and pick `__init__.py` inside the `sd_claude_bridge` folder.
3. To load it automatically every launch, add the `sduserplugins` folder as a plugin path: open **Preferences > Projects** (Edit > Preferences on Windows; on a Mac, Preferences is usually in the application menu next to the Apple menu), select your project file, open the **Python** tab, click **+** and choose the `sduserplugins` folder. Restart Designer.
4. If the Console shows `[Claude bridge] failed to start` with a traceback, that text explains why. A port conflict is handled automatically (it tries 9881 to 9890).
5. Designer's log has the same lines, plus any traceback that escapes the plugin:
   - Windows: `%LOCALAPPDATA%\Adobe\Adobe Substance 3D Designer\log.txt`, or `%LOCALAPPDATA%\Allegorithmic\Substance Designer\log.txt` for the Steam edition
   - macOS: `~/Library/Application Support/Adobe/Adobe Substance 3D Designer/log.txt`, or `~/Library/Application Support/Allegorithmic/Substance Designer/log.txt` for the Steam edition

### Claude says the bridge is not running

- Designer must be open with the plugin loaded (step above).
- The plugin writes `.sd_claude_bridge/session.json` in your home folder when it starts (`%USERPROFILE%` on Windows, `~` on a Mac). If that file exists but Claude still can't connect, Designer probably crashed: restart it. With two Designers open, Claude talks to the one started last; when that one quits, the other takes over again within a few seconds.
- Security software that blocks loopback connections can interfere. The bridge only listens on 127.0.0.1, so allowing it doesn't expose anything to the network.

### `substance-designer` doesn't appear in Claude Desktop

- Quit Claude completely (tray icon > Quit on Windows, Cmd+Q on a Mac), not just the window.
- **Settings > Developer** shows the server's error. Open the log there: a wrong path in the config is the usual cause. On a Mac the logs are also in `~/Library/Logs/Claude/` (`mcp-server-substance-designer.log`).
- Run the server by hand to check it. It should print `MCP server OK: 19 tools`.
  - Windows: `"%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" "%LOCALAPPDATA%\sd-claude-bridge\sd_designer_mcp.py" --check`
  - macOS: `"$HOME/Library/Application Support/sd-claude-bridge/venv/bin/python" "$HOME/Library/Application Support/sd-claude-bridge/sd_designer_mcp.py" --check`

### The Mac installer can't write to Documents

macOS asked whether Terminal may access Documents and the answer was No. Allow it under **System Settings > Privacy & Security > Files and Folders > Terminal > Documents Folder**, then run the installer again.

### A tool fails on my Designer build

The plugin targets the 2022 Python API. If one structured tool fails, Claude can usually do the same thing with `run_python`, which runs any `sd` API code. Errors include the last lines of the Designer-side traceback. Designer's API reference is under **Help > Python API Documentation**.

### Previews are empty

`render_preview` computes the graph and saves output textures to `sd_claude_bridge/previews` in the temp folder (`%TEMP%` on Windows, `$TMPDIR` on a Mac). Designer only computes nodes that feed an Output node, so a node with nothing downstream has no preview. Connect it to an Output node and preview that.

## Security

- The plugin listens on `127.0.0.1` only, and every request must carry a random token that changes each time Designer starts. The token is in `.sd_claude_bridge/session.json` in your home folder.
- `run_python` executes arbitrary code inside Designer, so any program running as your user that can read the session file could do the same. To turn it off, set `SD_CLAUDE_BRIDGE_ALLOW_PYTHON=0` and restart Designer.
  - Windows: add it as a user environment variable.
  - macOS: apps opened from the Dock or Finder don't see shell variables. Run `launchctl setenv SD_CLAUDE_BRIDGE_ALLOW_PYTHON 0` in Terminal, then restart Designer. This lasts until you log out or restart the Mac.
- Change the port with `SD_CLAUDE_BRIDGE_PORT` (Designer side, set the same way). The MCP server finds the port from the session file.
- `SD_CLAUDE_BRIDGE_SESSION` moves the session file. Set it the same way for Designer and for the MCP server (Claude Desktop's `env` for the entry, which reinstalling keeps). `sdcall.py` reads it too, or takes `--session`.

## Uninstall

Quit Designer and Claude Desktop, then run the uninstaller: `uninstall.bat` on Windows, or `sh uninstall.command` in Terminal on a Mac. It removes the plugin, the Python environment, the session and preview files, and the Claude Desktop config entry (with a backup). If you registered the server with Claude Code, also run `claude mcp remove --scope user substance-designer`.

## Development

A Claude session keeps the MCP server it started with, so edits to `sd_designer_mcp.py` reach Claude only in a new session. `tools/tool_call.py` lets you try a tool call from a shell instead. It imports the server and runs the call in-process, with the same argument validation, over the bridge to Designer (which must be running with the plugin loaded). Run it with the server's Python:

```
"%LOCALAPPDATA%\sd-claude-bridge\venv\Scripts\python.exe" tools\tool_call.py search_library query="color dodge"
```

On a Mac:

```
"$HOME/Library/Application Support/sd-claude-bridge/venv/bin/python" tools/tool_call.py search_library query="color dodge"
```

- Arguments are `key=value` pairs. A value is read as JSON when it parses; node ids stay strings.
- Or pass one JSON object: inline, as `@args.json`, or `-` for stdin. Windows drops unescaped double quotes from command-line arguments, so on Windows JSON with strings in it is safest in a file or on stdin. A Mac shell keeps them inside single quotes.
- `--list` lists the tools. `--source` loads `mcp_server/` from this folder instead of the installed copy, to try an edit before running the installer. `--raw` sends a bridge command (the plugin's command names) and skips the MCP layer.
- Unknown parameter names are refused, as the MCP server refuses them too, and so are empty names and paths such as `graph=` or `save_as=`. `--raw` skips the MCP layer and has no schema to check against: there, a misspelled `save_as` is dropped and `save_package` overwrites the package's own file.
- Images are saved to `sd_claude_bridge/tool_call` in the temp folder.

### Working from the git repo

This folder is a git repo (`git@github.com:ADB4/sd22-bridge.git`) shared between a Mac and a Windows PC. It also holds the `sd-material-research` Claude Code skill in `skills/`. The installers copy files, so after a pull the copies are stale, and an edit made in a copy never reaches the repo. `tools/link_install.py` replaces the copies with links into the repo:

- `sduserplugins/sd_claude_bridge` links to `designer_plugin/sd_claude_bridge`
- `sd_designer_mcp.py`, `configure_claude.py` and `requirements.txt` in the install folder link to `mcp_server/`
- `~/.claude/skills/sd-material-research` links to `skills/sd-material-research`

To set up a machine:

1. Clone the repo. On the Mac it lives at `~/Documents/Allegorithmic/Substance Designer/python/sduserplugins/sd-claude-bridge`, but anywhere works: the script finds Designer's folders itself. On Windows, keep it out of a OneDrive-synced Documents folder, since OneDrive and `.git` don't mix (`C:\dev\sd-claude-bridge` is fine). If the machine has an older copy of this folder that isn't a git repo, rename it before cloning and compare it with the repo afterwards.
2. Run the installer once. It makes the Python environment and the Claude config. If the machine already has an install, run step 3 first: the installer replaces installed copies without a backup, while `link_install.py` sets aside any copy that differs from the repo.
3. Run `python3 tools/link_install.py` (Mac) or `py tools\link_install.py` (Windows).
4. Restart Designer.

After that, a `git pull` is the whole update. Restart Designer for plugin changes, and start a new Claude session for server and skill changes. Commit and push before you switch machines.

- `--status` shows what each location is. `--unlink` turns the links back into plain copies of the repo.
- A copy that differs from the repo is moved to `.link-backups/` in the repo, never deleted. Diff it against the repo and commit anything worth keeping.
- Windows: folders become junctions, which need no special rights. The three server files need file symlinks: turn on Developer Mode (Settings > System > For developers) or run the script from an administrator prompt. If that fails and nothing is left at that path, the script puts a plain copy back so the bridge keeps working.
- The installers leave links alone, so running one again is safe.
- With linked installs, `tool_call.py` already loads the repo's server, so `--source` isn't needed.
