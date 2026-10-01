"""Register the Substance Designer MCP server with Claude Desktop.

Run with the Python that should launch the server (the installer uses the
virtual environment's python.exe). Existing config is backed up first and
other servers are left untouched.
"""

import glob
import json
import os
import shutil
import sys
import time

SERVER_NAME = "substance-designer"


def config_paths():
    paths = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        paths.append(os.path.join(appdata, "Claude", "claude_desktop_config.json"))
    # Microsoft Store / MSIX installs keep a redirected copy of %APPDATA%.
    local = os.environ.get("LOCALAPPDATA")
    if local:
        pattern = os.path.join(local, "Packages", "Claude_*", "LocalCache", "Roaming", "Claude")
        for folder in glob.glob(pattern):
            paths.append(os.path.join(folder, "claude_desktop_config.json"))
    return paths


def merge(path, entry, remove=False):
    config = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8-sig") as f:
                text = f.read().strip()
            config = json.loads(text) if text else {}
        except ValueError as e:
            print("  ! %s is not valid JSON (%s). Left unchanged; edit it by hand." % (path, e))
            return False
        if not isinstance(config, dict):
            print("  ! %s does not contain a JSON object. Left unchanged." % path)
            return False
        if remove and SERVER_NAME not in config.get("mcpServers", {}):
            return False
        backup = path + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
        n = 1
        while os.path.exists(backup):
            n += 1
            backup = path + ".bak-" + time.strftime("%Y%m%d-%H%M%S") + "-%d" % n
        shutil.copy2(path, backup)
        print("  backup: %s" % backup)
    elif remove:
        return False
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    servers = config.setdefault("mcpServers", {})
    if remove:
        servers.pop(SERVER_NAME, None)
    else:
        servers[SERVER_NAME] = entry
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print("  %s: %s" % ("removed entry from" if remove else "updated", path))
    return True


def main():
    remove = "--remove" in sys.argv
    here = os.path.dirname(os.path.abspath(__file__))
    entry = {"command": sys.executable, "args": [os.path.join(here, "sd_designer_mcp.py")]}
    paths = config_paths()
    if not paths:
        print("  ! APPDATA is not set; cannot find the Claude Desktop config.")
        return 1
    ok = False
    for i, path in enumerate(paths):
        # Always handle the standard location; only touch MSIX copies that exist.
        if i == 0 or os.path.isdir(os.path.dirname(path)):
            ok = merge(path, entry, remove) or ok
    if remove:
        if not ok:
            print("  Claude Desktop config had no '%s' entry." % SERVER_NAME)
        return 0
    print()
    print("  Entry written:" if ok else "  Add this entry to claude_desktop_config.json by hand:")
    print(json.dumps({"mcpServers": {SERVER_NAME: entry}}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
