"""MCP server that lets Claude drive Adobe Substance 3D Designer.

It talks to the sd_claude_bridge plugin running inside Designer over a
loopback socket. Connection details (port + token) are read from the session
file the plugin writes when Designer starts, so Designer can be restarted
without restarting this server.

Run by an MCP client (Claude Desktop, Claude Code) over stdio:
    python sd_designer_mcp.py
"""

# No `from __future__ import annotations`: mcp 1.7-1.13 call issubclass() on each tool parameter's
# annotation and fail at import when it's a string.
import collections
import contextlib
import functools
import io
import itertools
import json
import os
import socket
import sys
from typing import Union

import anyio
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

SESSION_FILE = os.environ.get("SD_CLAUDE_BRIDGE_SESSION") or os.path.join(
    os.path.expanduser("~"), ".sd_claude_bridge", "session.json"
)

NOT_RUNNING = (
    "Substance Designer bridge is not running. Start Substance Designer and check Windows > "
    "Console for '[Claude bridge] ... listening'. If that line is missing, load the plugin "
    "with Tools > Plugin Manager > Browse and pick __init__.py inside the sd_claude_bridge folder."
)

# Claude Code cuts server instructions (and tool descriptions) after 2048 characters, so keep
# INSTRUCTIONS short and put tool-specific detail in the tool docstrings. --check enforces it.
MAX_TEXT = 2048

INSTRUCTIONS = """\
Tools for Adobe Substance 3D Designer 2022 (12.x) via a local bridge plugin.

- Call designer_status first. Tools act on the graph open in Designer's Graph view unless you
  pass `graph`. Don't save, or delete nodes you didn't create, unless the user asks.
- Library nodes (noises, patterns, filters: Tile Generator, Perlin Noise, Clouds 2, Bevel):
  search_library, then create_library_node. Skip matches marked hidden_in_library: they are
  "(Legacy)" versions (tile_generator.sbs, clouds_2.sbs); the current one is usually the
  prefixed file (pattern_tile_generator.sbs, noise_clouds_2.sbs).
- Atomic nodes: create_node("blend"), create_node("levels"), ... Most output
  `unique_filter_output`. Blend inputs are `source` (foreground), `destination` (background),
  `opacity` (mask). Output nodes take `inputNodeOutput`. get_node lists ports and parameters.
- A Blend is grayscale or color depending on its `destination`. A `source` of the other kind
  doesn't work: a color Blend skips a grayscale source, a grayscale Blend reads a color source
  as black. Most noises are grayscale: colorize them with create_node("gradient") (Gradient Map)
  and its `gradientrgba` keys, e.g. [[0, "#3b3530"], [1, "#a0522d"]], or use them as the
  `opacity` mask. render_preview notes mismatches.
- Base parameters start with `$`. `$outputsize` is log2 (11 = 2048). Unless get_node shows
  `inheritance` Absolute, the value is an offset from the input or parent graph ($outputsize)
  or ignored and inherited (enums like $format); set_parameter makes it absolute. Node "graph"
  sets the graph's own.
- Layout: x grows to the right. Leave 160-200 px between columns and 130 px between rows.
- Check your work with render_preview. Designer computes only nodes that feed an Output node.
  A varying alpha comes as a second image (a Normal node puts the height there by default).
- Each edit (except create_graph) is one Ctrl+Z step when designer_status reports
  undo_groups=true. run_python covers anything the other tools don't.
"""

class _Server(FastMCP):
    async def call_tool(self, name, arguments):
        # FastMCP drops argument names it doesn't know and runs the tool with its defaults, so a
        # save_package with "saveAs" would overwrite the package's own file. Refuse them instead.
        tool = self._tool_manager.get_tool(name)
        if tool is not None:
            known = list(tool.parameters.get("properties") or {})
            unknown = sorted(set(arguments or {}) - set(known))
            if unknown:
                raise ToolError("Unknown parameter %s for %s; nothing was sent to Designer. Parameters: %s"
                                % (", ".join(map(repr, unknown)), name, ", ".join(known) or "none"))
        return await super().call_tool(name, arguments)


mcp = _Server("substance-designer", instructions=INSTRUCTIONS)
_ids = itertools.count(1)


class BridgeError(RuntimeError):
    pass


# Plugin commands that change nothing in Designer, so repeating one after a timeout is safe.
READ_ONLY = {"ping", "info", "list_packages", "get_graph", "get_node", "get_selection",
             "list_node_definitions", "search_library", "render"}

# Tool hints for clients that group or auto-approve tools. An unannotated tool counts as one that
# may change or delete things (destructiveHint defaults to true).
READS = ToolAnnotations(readOnlyHint=True)
ADDS = ToolAnnotations(readOnlyHint=False, destructiveHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def _timeout_text(cmd: str, timeout: float) -> str:
    text = "Designer did not answer within %d s. It may be busy (computing, or a modal dialog is open)" % timeout
    if cmd in READ_ONLY:
        return text + ". Check Designer and try again."
    return (text + " and still running this call, so don't repeat it: wait until designer_status answers, "
            "then check whether the change happened.")


def _log(msg: str) -> None:
    # stdout carries the MCP protocol; diagnostics go to stderr.
    print("[sd-mcp] " + msg, file=sys.stderr, flush=True)


def call(cmd: str, args: dict | None = None, timeout: float = 120.0):
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            session = json.load(f)
    except FileNotFoundError:
        raise BridgeError(NOT_RUNNING) from None
    except (OSError, ValueError) as e:
        raise BridgeError("Could not read %s: %s" % (SESSION_FILE, e)) from None
    if not isinstance(session, dict):
        raise BridgeError("Could not read %s: it isn't a JSON object." % SESSION_FILE)
    try:
        port = int(session["port"])
    except (KeyError, TypeError, ValueError):
        raise BridgeError("%s has no valid port. Restart Designer to rewrite it." % SESSION_FILE) from None

    request = {"id": next(_ids), "token": session.get("token", ""), "cmd": cmd, "args": args or {}}
    payload = (json.dumps(request) + "\n").encode("utf-8")
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=5)
    except TimeoutError:
        # A refused connection means nothing listens; a timeout means the listen queue is full.
        raise BridgeError(
            "Designer isn't accepting connections: it's probably busy with a long job, with earlier calls "
            "queued behind it. Wait, then try designer_status again. Don't restart Designer unless it's frozen."
        ) from None
    except OSError:
        raise BridgeError(
            NOT_RUNNING + " (A session file exists, so Designer may have closed or crashed.)"
        ) from None

    with sock:
        sock.settimeout(timeout)
        try:
            sock.sendall(payload)
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(1 << 16)
                if not chunk:
                    raise BridgeError("Designer closed the connection before replying.")
                buf += chunk
        except TimeoutError:
            raise BridgeError(_timeout_text(cmd, timeout)) from None
        except OSError as e:
            raise BridgeError("Designer closed the connection before replying (%s)." % e) from None

    try:
        response = json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
    except ValueError as e:
        raise BridgeError("Designer's reply isn't valid JSON: %s" % e) from None
    if not isinstance(response, dict):
        raise BridgeError("Designer's reply isn't a JSON object.")
    if not response.get("ok"):
        message = response.get("error") or "unknown error"
        tb = (response.get("traceback") or "").strip().splitlines()
        if tb:
            message += "\n" + "\n".join(tb[-6:])
        raise BridgeError(message)
    return response.get("result")


def _clean(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


# Designer answers one request at a time, so tools run one at a time too. Each runs in a worker
# thread: the server keeps answering pings and reading cancellations meanwhile, and a call the
# client cancels while it waits here never reaches Designer.
_designer = anyio.Lock()


def _tool(annotations=None, wait=True):
    """Register fn as a tool that runs in a worker thread behind _designer. wait=False skips the
    lock, so designer_status can still report a busy Designer (its 15 s timeout)."""
    def register(fn):
        @functools.wraps(fn)  # FastMCP reads the parameters and docstring through __wrapped__
        async def run(**kwargs):
            async with _designer if wait else contextlib.nullcontext():
                result = await anyio.to_thread.run_sync(functools.partial(fn, **kwargs))
                # A running call can't be stopped, so one the client cancelled still gets here. mcp
                # has already answered it, and a second answer fails an assertion that stops the
                # whole server: end it as cancelled instead.
                await anyio.lowlevel.checkpoint_if_cancelled()
                return result
        mcp.tool(annotations=annotations)(run)
        return fn
    return register


# ------------------------------------------------------------------ status
@_tool(READS, wait=False)
def designer_status():
    """Check the connection and report Designer/Python versions, the graph open in the
    Graph view, grid size and whether undo grouping and run_python are available."""
    return call("info", timeout=15)


@_tool(READS)
def list_packages():
    """List open user packages (.sbs) and the graphs inside each."""
    return call("list_packages")


# ------------------------------------------------------------------- read
@_tool(READS)
def get_graph(graph: str | None = None, include_values: bool = False, limit: int = 400):
    """Read a graph: node ids, definitions, positions and connections.

    graph: graph identifier (or "file.sbs::identifier", or "<full .sbs path>::identifier");
    omit for the graph open in Designer.
    include_values: also return every node's parameter values (large).
    Connections are [from_node, from_output, to_node, to_input].
    """
    return call("get_graph", _clean(graph=graph, include_values=include_values, limit=limit))


@_tool(READS)
def get_node(node: str, graph: str | None = None, all_params: bool = False):
    """Full detail for one node: connectable inputs (and what feeds them), parameters with
    current values, descriptions and enum options, outputs, and annotations.
    Library nodes add what their widgets call each part: `components` for vectors (the Tile
    Generator's interstice: Interstice X, Random, Interstice Y, Random) and `value_labels` for
    bools ({"false": "DirectX", "true": "OpenGL"}).
    `$` base parameters still inherited unchanged are only named, in `inherited_base_params`;
    all_params=true lists them in full."""
    return call("get_node", _clean(node=node, graph=graph, all_params=all_params))


@_tool(READS)
def get_selection():
    """Nodes currently selected in Designer's Graph view."""
    return call("get_selection")


@_tool(READS)
def list_node_definitions(query: str = ""):
    """Search atomic node definition ids (e.g. query "blend", "warp", "function")."""
    return call("list_node_definitions", {"query": query})


@_tool(READS)
def search_library(query: str, limit: int = 25):
    """Search Designer's bundled library packages by file name or node label (noises, patterns,
    filters, generators). Returns package_path values for create_library_node, each with its
    label. A match with graph_identifier is one node in a package of several (blend.sbs holds
    Color Dodge, Difference, ...): pass both. Matches marked hidden_in_library are legacy
    versions or helpers; they are listed last. Atomic nodes (Levels, Blur, Emboss, ...) are not
    packages: matching ones come under `atomic`, for create_node.
    Examples: "perlin", "tile generator", "clouds", "bevel", "slope blur", "color dodge"."""
    return call("search_library", {"query": query, "limit": limit})


# ------------------------------------------------------------------ write
@_tool(ADDS)
def create_node(definition: str, x: float | None = None, y: float | None = None, graph: str | None = None):
    """Create an atomic node, e.g. "uniform", "blend", "levels", "blur", "hsl", "normal",
    "transformation", "warp", "directionalwarp", "gradient" (gradient map), "curve",
    "grayscaleconversion", "shuffle", "distance", "emboss", "sharpen", "pixelprocessor".
    Omit x/y to place it right of the existing nodes. Returns its id and port names."""
    return call("create_node", _clean(definition=definition, x=x, y=y, graph=graph))


@_tool(ADDS)
def create_library_node(
    package_path: str,
    graph_identifier: str | None = None,
    x: float | None = None,
    y: float | None = None,
    graph: str | None = None,
):
    """Instance a library graph (from search_library) as a node in the current graph."""
    return call(
        "create_library_node",
        _clean(package_path=package_path, graph_identifier=graph_identifier, x=x, y=y, graph=graph),
    )


@_tool(ADDS)
def create_output(
    identifier: str,
    usage: str | None = None,
    x: float | None = None,
    y: float | None = None,
    label: str | None = None,
    graph: str | None = None,
):
    """Create an Output node with an identifier and optional PBR usage
    (baseColor, normal, roughness, metallic, height, ambientOcclusion, emissive, opacity)."""
    return call("create_output", _clean(identifier=identifier, usage=usage, x=x, y=y, label=label, graph=graph))


@_tool()
def connect_nodes(
    from_node: str,
    to_node: str,
    to_input: str,
    from_output: str | None = None,
    graph: str | None = None,
):
    """Connect an output of from_node to an input of to_node. from_output defaults to the
    node's first output. On a bad port name the error lists valid ports."""
    return call(
        "connect",
        _clean(from_node=from_node, to_node=to_node, to_input=to_input, from_output=from_output, graph=graph),
    )


@_tool()
def disconnect_input(node: str, input: str, graph: str | None = None):
    """Remove whatever is connected to one input of a node."""
    return call("disconnect", _clean(node=node, input=input, graph=graph))


@_tool()
def set_parameter(
    node: str,
    property: str,
    value: Union[float, int, bool, str, list[float], list[Union[list[Union[float, str, list[float]]], dict]]],
    graph: str | None = None,
):
    """Set a node parameter, or with node "graph" one of the graph's own (get_graph graph_params).
    The value is converted to the parameter's type: float/int/bool/string; lists for float2-4 /
    int2-4 (one number fills every component); colors as [r,g,b(,a)] in 0-1 or "#rrggbb";
    enums as the option id string (get_node lists options); Gradient Map keys (`gradientrgba`) as
    [[position, r, g, b(, a)], ...], [[position, "#rrggbb"], ...] or the objects get_node shows,
    replacing all keys. `$` parameters become Absolute; the result shows `inheritance`.
    Example: node "graph", property "$outputsize", value [11, 11] makes the graph 2048x2048, and
    every node that inherits its size follows."""
    return call("set_parameter", _clean(node=node, property=property, value=value, graph=graph))


class NodeMove(BaseModel):
    node: str = Field(description="node id")
    x: float
    y: float


@_tool()
def move_nodes(moves: list[NodeMove], graph: str | None = None):
    """Reposition nodes (one undo step for the whole batch)."""
    return call("move_nodes", _clean(moves=[m.model_dump() for m in moves], graph=graph))


@_tool(DESTRUCTIVE)
def delete_nodes(nodes: list[str], graph: str | None = None):
    """Delete nodes by id. Only when the user asked for it or the nodes were created by you."""
    return call("delete_nodes", _clean(nodes=nodes, graph=graph))


@_tool(ADDS)
def create_graph(identifier: str, package_path: str | None = None):
    """Create a new Substance compositing graph, in a new unsaved package unless
    package_path names an open package."""
    return call("create_graph", _clean(identifier=identifier, package_path=package_path))


@_tool(DESTRUCTIVE)
def save_package(graph: str | None = None, save_as: str | None = None):
    """Save the package that contains the graph. Overwrites its .sbs file unless save_as gives a
    new full path. Only call when the user asks to save."""
    return call("save_package", _clean(graph=graph, save_as=save_as))


# ---------------------------------------------------------------- preview
MAX_IMAGE_BYTES = 3_500_000  # stays under the API's 5 MB per image once base64-encoded
# The API scales images above 1568 px down anyway, and refuses ones above 2000 px once a request
# holds more than 20 images. The images of one call stay under MAX_PREVIEW_BYTES together: the
# request limit is 32 MB, and earlier results stay in the conversation.
MAX_PREVIEW_SIZE = 1568
MAX_PREVIEW_BYTES = 8_000_000


def _png(im, max_size: int) -> Image:
    im.thumbnail((max_size, max_size))
    while True:
        out = io.BytesIO()
        im.save(out, format="PNG", optimize=True)
        if out.tell() <= MAX_IMAGE_BYTES or max(im.size) <= 256:
            return Image(data=out.getvalue(), format="png")
        # Noisy 2048 px textures can exceed the limit: shrink until it fits.
        im.thumbnail((im.width * 3 // 4, im.height * 3 // 4))


def _load_images(path: str, max_size: int) -> list[tuple[str | None, Image]]:
    """The preview as PNGs for Claude, each with an optional caption note: the color channels,
    then the alpha channel as its own grayscale image when it varies. Composited over a
    background, alpha hides things: a Normal node stores the height there by default (the
    normal map looks washed out) and Shape Glow puts its whole result in alpha over white."""
    try:
        from PIL import Image as PILImage
    except ImportError:
        with open(path, "rb") as f:
            return [(None, Image(data=f.read(), format="png"))]

    with PILImage.open(path) as im:
        im.load()
        if im.mode.startswith("I;16") or im.mode == "I":
            # 16-bit grayscale (most noises): scale to 8 bits. A plain convert()
            # clips everything above 255, so the preview came out solid white.
            im = im.convert("I").point(lambda v: v * (1 / 257.0)).convert("L")
        elif im.mode not in ("RGB", "RGBA", "L", "LA"):
            im = im.convert("RGBA")
        if im.mode not in ("RGBA", "LA"):
            return [(None, _png(im, max_size))]
        alpha = im.getchannel("A")
        color = im.convert("RGB" if im.mode == "RGBA" else "L")
    low, high = alpha.getextrema()
    if low == 255:
        return [(None, _png(color, max_size))]
    if low == high:
        note = "fully transparent: nothing reaches this output?" if high == 0 else "alpha is %d everywhere" % low
        return [(note, _png(color, max_size))]
    return [
        ("color channels", _png(color, max_size)),
        ("alpha channel (values %d-%d)" % (low, high), _png(alpha, max_size)),
    ]


def _preview_content(images: list, max_size: int) -> list:
    """Caption and image blocks for the first 8 textures."""
    content: list = []
    per_node = collections.Counter(item.get("node") for item in images)
    for item in images[:8]:
        caption = "%s (%s)" % (item.get("label"), item.get("node"))
        if per_node[item.get("node")] > 1:  # e.g. Bevel's height and normal
            caption = "%s output `%s` (%s)" % (item.get("label"), item.get("output"), item.get("node"))
        size = item.get("size")
        if size and len(size) == 2:  # the computed size; the image below may be scaled down
            caption += ", %sx%s px" % (size[0], size[1])
        try:
            for note, image in _load_images(item["path"], max_size):
                content.append(caption + ("; " + note if note else ""))
                content.append(image)
        except Exception as e:  # keep going if one image fails
            content.append("%s: could not read %s: %s" % (caption, item.get("path"), e))
    return content


def _image_bytes(content: list) -> int:
    return sum(len(block.data) for block in content if isinstance(block, Image))


@_tool(READS)
def render_preview(node: str | None = None, graph: str | None = None, max_size: int = 512):
    """Compute the graph and return images of its Output nodes (or of one node's outputs).
    Use after edits to check the result. Designer computes only nodes that feed an Output node,
    so a node with nothing downstream has no image yet: wire it to an Output first (and delete
    that Output afterwards if you added it).
    When alpha varies, it comes as a second grayscale image after the color channels (a Normal
    node stores the height there by default; Shape Glow puts its result there).
    Captions give each texture's computed size. max_size (64-1568) caps the returned image size;
    when the images together pass 8 MB, all of them shrink further and the summary's max_size
    says to what."""
    result = call("render", _clean(node=node, graph=graph), timeout=600)
    images = result.get("images") or []
    size = max(64, min(int(max_size), MAX_PREVIEW_SIZE))
    content = _preview_content(images, size)
    total = _image_bytes(content)
    while total > MAX_PREVIEW_BYTES and size > 64:
        # Too much for one result: shrink every image (PNG size follows the pixel count roughly).
        smaller_size = max(64, int(size * min(0.75, (MAX_PREVIEW_BYTES / total) ** 0.5)))
        smaller = _preview_content(images, smaller_size)
        if _image_bytes(smaller) >= total:
            break  # nothing shrinks without Pillow
        size, content, total = smaller_size, smaller, _image_bytes(smaller)
    # A texture can give two images (color channels, then alpha), so count both.
    summary = {
        "graph": result.get("graph"),
        "textures": len(images),
        "images": sum(1 for block in content if isinstance(block, Image)),
    }
    if size != max_size:  # clamped, or shrunk to fit one result
        summary["max_size"] = size
    if len(images) > 8:
        summary["textures_omitted"] = len(images) - 8
    if result.get("notes"):
        summary["notes"] = result["notes"]
    content.insert(0, json.dumps(summary))
    return content


# ----------------------------------------------------------------- escape
@_tool(DESTRUCTIVE)
def run_python(code: str):
    """Run Python inside Designer (its own interpreter, Python 3.9 in Designer 2022).
    In scope: sd, app (SDApplication), ui (QtForPythonUIMgr), pkg_mgr, graph (current graph or
    None), SDPropertyCategory. print() output is returned; assign to `result` to return data.
    The whole run is one undo step when supported. Use for anything the other tools don't cover."""
    return call("run_python", {"code": code}, timeout=600)


def main() -> None:
    if "--check" in sys.argv:
        # Used by the installer: proves the packages import and the tools register.
        tools = anyio.run(mcp.list_tools)
        too_long = [("instructions", len(INSTRUCTIONS))] if len(INSTRUCTIONS) > MAX_TEXT else []
        too_long += [(t.name, len(t.description or "")) for t in tools if len(t.description or "") > MAX_TEXT]
        if too_long:
            print("Too long for Claude Code (max %d characters): %s" % (MAX_TEXT, too_long))
            sys.exit(1)
        print("MCP server OK: %d tools (%s)" % (len(tools), ", ".join(t.name for t in tools)))
        return
    _log("starting; session file: %s" % SESSION_FILE)
    mcp.run()


if __name__ == "__main__":
    main()
