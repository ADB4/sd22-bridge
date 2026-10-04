"""Run substance-designer MCP tool calls from a shell, without restarting Claude.

A Claude session keeps the MCP server it started with, so edits to sd_designer_mcp.py only
reach Claude in a new session. This script imports the server code and calls its tools
in-process instead: arguments go through the same pydantic validation as a real MCP call, then
over the bridge to Designer (which must be running with the plugin loaded).

Run it with the server's venv Python (it has the `mcp` package):

    set PY=%LOCALAPPDATA%\\sd-claude-bridge\\venv\\Scripts\\python.exe
    %PY% tools\\tool_call.py --list
    %PY% tools\\tool_call.py designer_status
    %PY% tools\\tool_call.py search_library query="color dodge"
    %PY% tools\\tool_call.py get_graph graph=claude_smoke_test include_values=true
    %PY% tools\\tool_call.py set_parameter @args.json
    type args.json | %PY% tools\\tool_call.py set_parameter -
    %PY% tools\\tool_call.py --raw get_graph graph=claude_smoke_test

On macOS the server's Python is ~/Library/Application Support/sd-claude-bridge/venv/bin/python
(quote the path: it has a space). Inline JSON works inside single quotes.

Arguments are key=value pairs, or one JSON object: inline, @file.json, or - for stdin (UTF-8
with or without a BOM, or UTF-16 as Windows PowerShell 5.1's > writes it). A key=value value is
parsed as JSON unless the tool takes only a string there; node ids look like numbers but stay
strings, also in lists (nodes=[1582876907,1582876909]). Windows argument parsing (cmd.exe and
Windows PowerShell 5.1) removes unescaped double quotes, so query="color dodge" works, but JSON
with quoted strings in it (the inline object form, gradient keys) must be escaped as \\" in cmd
or passed through a file or stdin. Unknown parameter names and empty values are refused before
anything is sent (the server refuses unknown names too). --raw has no schema, so it checks
nothing: the plugin ignores a misspelled key and runs with its default.

By default it loads the installed server (%LOCALAPPDATA%\\sd-claude-bridge, or on macOS
~/Library/Application Support/sd-claude-bridge). --source loads
mcp_server\\ from this repo instead, to try an edit before running the installer. --raw sends a
bridge command (the plugin's command names: get_graph, connect, render, ...) through call(),
skipping the MCP layer. Images are saved under sd_claude_bridge/tool_call in the temp folder
(%TEMP% on Windows, $TMPDIR on macOS).
"""

import argparse
import asyncio
import base64
import codecs
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_SERVER = os.path.join(os.path.dirname(HERE), "mcp_server")
if sys.platform == "win32":
    INSTALLED = os.path.join(os.environ.get("LOCALAPPDATA", ""), "sd-claude-bridge")
    VENV_PY = os.path.join(INSTALLED, "venv", "Scripts", "python.exe")
else:  # where install.command puts it on macOS
    INSTALLED = os.path.expanduser("~/Library/Application Support/sd-claude-bridge")
    VENV_PY = os.path.join(INSTALLED, "venv", "bin", "python")
OUT_DIR = os.path.join(tempfile.gettempdir(), "sd_claude_bridge", "tool_call")


def string_only(prop):
    """Does a JSON-schema property take only strings (or null)? Then key=value keeps the text:
    node ids look like numbers ("1582876907") but must stay strings."""
    types = {prop.get("type")} | {p.get("type") for p in prop.get("anyOf") or []}
    types.discard(None)
    return bool(types) and types <= {"string", "null"}


def string_items(prop):
    """Is the property a list of strings (delete_nodes' node ids)?"""
    return prop.get("type") == "array" and (prop.get("items") or {}).get("type") == "string"


def decode(data):
    """Text from bytes: UTF-16 with a BOM (what Windows PowerShell 5.1's > and Out-File write),
    else UTF-8 with or without a BOM."""
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def read_json_object(source):
    """The arguments object from "-" (stdin), "@file" or inline JSON text."""
    try:
        if source == "-":
            text = decode(sys.stdin.buffer.read())
        elif source.startswith("@"):
            with open(source[1:], "rb") as f:
                text = decode(f.read())
        else:
            text = source
        value = json.loads(text)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        where = "stdin" if source == "-" else source[1:] if source.startswith("@") else "the command line"
        raise SystemExit("Could not read the arguments from %s: %s" % (where, e))
    if not isinstance(value, dict):
        raise SystemExit("Arguments must be a JSON object, got %s" % type(value).__name__)
    return value


def parse_arguments(items, schema=None):
    """Tool arguments from the command line: key=value pairs, or one JSON object."""
    if not items:
        return {}
    first = items[0]
    if len(items) == 1 and (first == "-" or first.startswith("@") or first.lstrip().startswith("{")):
        return read_json_object(first)
    props = (schema or {}).get("properties") or {}
    out = {}
    for item in items:
        key, sep, raw = item.partition("=")
        if not sep or not key:
            raise SystemExit("Expected key=value, got %r" % item)
        if key in props and string_only(props[key]):
            out[key] = raw
            continue
        try:
            value = json.loads(raw)
        except ValueError:
            value = raw
        if key in props and string_items(props[key]):
            # Node ids: nodes=1582876907 or nodes=[1582876907,1582876909].
            value = [
                str(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
                for v in (value if isinstance(value, list) else [value])
            ]
        out[key] = value
    return out


def check_arguments(args, schema, tool):
    """Refuse unknown keys (the server refuses them too: a misspelled save_as would otherwise
    overwrite the package) and an empty name or path (save_as=, graph=), which is a mistake.
    A parameter value can still be "" (set_parameter on a string)."""
    props = (schema or {}).get("properties") or {}
    for key, value in args.items():
        if key not in props:
            raise SystemExit("Unknown parameter %r for %s. Parameters: %s" % (key, tool, ", ".join(props)))
        if isinstance(value, str) and not value.strip() and string_only(props[key]):
            raise SystemExit("Empty value for %r: leave the parameter out instead." % key)


def image_size(data):
    try:
        import io

        from PIL import Image

        with Image.open(io.BytesIO(data)) as im:
            return "%dx%d %s" % (im.width, im.height, im.mode)
    except Exception:
        return "?"


def show(blocks, tool):
    # Date, time and pid: two runs finishing in the same second must not share file names.
    stamp = "%s_%d" % (time.strftime("%Y%m%d_%H%M%S"), os.getpid())
    count = 0
    for block in blocks:
        kind = getattr(block, "type", None)
        if kind == "text":
            print(block.text)
        elif kind == "image":
            count += 1
            data = base64.b64decode(block.data)
            ext = (getattr(block, "mimeType", None) or "image/png").split("/")[-1]
            os.makedirs(OUT_DIR, exist_ok=True)
            path = os.path.join(OUT_DIR, "%s_%s_%d.%s" % (stamp, tool, count, ext))
            with open(path, "wb") as f:
                f.write(data)
            print("[image %d: %s, %s, %d bytes]" % (count, path, image_size(data), len(data)))
        else:
            print(repr(block))


def list_tools(server):
    for tool in asyncio.run(server.mcp.list_tools()):
        schema = tool.inputSchema or {}
        required = set(schema.get("required") or [])
        params = ["%s%s" % (name, "" if name in required else "?") for name in schema.get("properties") or {}]
        print("%s(%s)" % (tool.name, ", ".join(params)))


def main():
    parser = argparse.ArgumentParser(
        description="Call substance-designer MCP tools in-process (see the module docstring)."
    )
    parser.add_argument("tool", nargs="?", help="tool name, or a bridge command with --raw")
    parser.add_argument("arguments", nargs="*", help="key=value pairs, or one JSON object / @file / -")
    parser.add_argument("--list", action="store_true", help="list the tools and their parameters")
    parser.add_argument("--raw", action="store_true", help="send a bridge command, skipping the MCP layer")
    parser.add_argument("--source", action="store_true", help="load mcp_server/ from this repo")
    ns = parser.parse_args()

    # Descriptions can hold characters the console code page lacks.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sys.path.insert(0, REPO_SERVER if ns.source else INSTALLED)
    try:
        import sd_designer_mcp as server
    except ImportError as e:
        raise SystemExit("Could not import the server (%s). Run this with %s" % (e, VENV_PY))
    print("[server: %s]" % server.__file__, file=sys.stderr)

    if ns.list:
        list_tools(server)
        return
    if not ns.tool:
        parser.error("name a tool, or pass --list")
    schema = None
    if not ns.raw:
        tool = next((t for t in asyncio.run(server.mcp.list_tools()) if t.name == ns.tool), None)
        if tool is None:
            raise SystemExit("No tool %r. Use --list (or --raw for a bridge command)." % ns.tool)
        schema = tool.inputSchema
    args = parse_arguments(ns.arguments, schema)
    if schema is not None:
        check_arguments(args, schema, ns.tool)

    try:
        if ns.raw:
            print(json.dumps(server.call(ns.tool, args), indent=2, ensure_ascii=False))
            return
        result = asyncio.run(server.mcp.call_tool(ns.tool, args))
    except Exception as e:  # ToolError (validation or bridge errors), BridgeError
        print("ERROR: %s" % e, file=sys.stderr)
        sys.exit(1)
    if isinstance(result, tuple):  # (content, structured output) when a tool declares a schema
        result = result[0]
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        show(result, ns.tool)


if __name__ == "__main__":
    main()
