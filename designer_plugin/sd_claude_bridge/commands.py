"""Command handlers for the Claude bridge.

Each handler takes a dict of arguments and returns JSON-friendly data.
Handlers run on Designer's main thread (see bridge.py).

The sd API differs a little between Designer releases, so optional calls
are wrapped in _try() and missing features degrade to a clear message
instead of an exception. run_python is the escape hatch for anything the
structured commands don't cover.
"""

import contextlib
import glob
import html
import importlib
import io
import json
import math
import os
import re
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET

import sd
from sd.api.sdproperty import SDPropertyCategory

try:
    from sd.api.apiexception import APIException
except ImportError:
    APIException = Exception

# sd API calls raise APIException, which derives from BaseException, so
# `except Exception` alone lets them through. Catch ERRORS instead.
ERRORS = (Exception, APIException)

# 0, false, no or off (any case) turns run_python off.
ALLOW_PYTHON_SETTING = os.environ.get("SD_CLAUDE_BRIDGE_ALLOW_PYTHON", "1").strip()
ALLOW_PYTHON = ALLOW_PYTHON_SETTING.lower() not in ("0", "false", "no", "off")
OUTPUT_TAIL = 20000
MAX_ARRAY = 4096  # SDValueArray items _js reads (gradients in the library have up to 256 keys)
_MISSING = object()

# Fallback list, used only if the module manager can't be queried.
COMMON_ATOMIC = [
    "sbs::compositing::bitmap",
    "sbs::compositing::blend",
    "sbs::compositing::blur",
    "sbs::compositing::curve",
    "sbs::compositing::dirmotionblur",
    "sbs::compositing::directionalwarp",
    "sbs::compositing::distance",
    "sbs::compositing::dyngradient",
    "sbs::compositing::emboss",
    "sbs::compositing::fxmaps",
    "sbs::compositing::gradient",
    "sbs::compositing::grayscaleconversion",
    "sbs::compositing::hsl",
    "sbs::compositing::input_color",
    "sbs::compositing::input_grayscale",
    "sbs::compositing::input_value",
    "sbs::compositing::levels",
    "sbs::compositing::normal",
    "sbs::compositing::output",
    "sbs::compositing::passthrough",
    "sbs::compositing::pixelprocessor",
    "sbs::compositing::sharpen",
    "sbs::compositing::shuffle",
    "sbs::compositing::svg",
    "sbs::compositing::text",
    "sbs::compositing::transformation",
    "sbs::compositing::uniform",
    "sbs::compositing::valueprocessor",
    "sbs::compositing::warp",
]


# --------------------------------------------------------------------- basics
def _app():
    return sd.getContext().getSDApplication()


def _ui():
    return _app().getQtForPythonUIMgr()


def _pm():
    return _app().getPackageMgr()


def _try(fn, default=None):
    try:
        return fn()
    except ERRORS:
        return default


def _api(module, name):
    return getattr(importlib.import_module("sd.api." + module), name)


def _items(arr):
    """Turn an SDArray (or list, or None) into a Python list."""
    if arr is None:
        return []
    if isinstance(arr, (list, tuple)):
        return list(arr)
    try:
        return list(arr)
    except TypeError:
        return [arr.getItem(i) for i in range(arr.getSize())]


def _cls(obj):
    name = _try(obj.getClassName)
    return name if name else type(obj).__name__


def _gid(graph):
    return _try(graph.getIdentifier, "?")


def _tail(text, limit=OUTPUT_TAIL):
    if len(text) <= limit:
        return text
    return "...(truncated)...\n" + text[-limit:]


def _has_undo():
    try:
        from sd.api.sdhistoryutils import SDHistoryUtils  # noqa: F401

        return True
    except Exception:
        return False


def _undo(label):
    """Group the edits of one command into a single Ctrl+Z step when supported."""
    try:
        from sd.api.sdhistoryutils import SDHistoryUtils

        return SDHistoryUtils.UndoGroup("Claude: " + label)
    except ERRORS:
        return contextlib.nullcontext()


# ------------------------------------------------------------- JSON helpers
def _js(v, depth=0):
    """Best-effort conversion of sd values to JSON-friendly data."""
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        return round(v, 6)
    if depth > 4:
        return str(v)
    if isinstance(v, (list, tuple)):
        return [_js(x, depth + 1) for x in list(v)[:256]]
    if isinstance(v, dict):
        return dict((str(k), _js(x, depth + 1)) for k, x in v.items())

    name = type(v).__name__
    if name == "SDValueStruct":  # e.g. gradient keys: {"position", "value", "midpoint"}
        fields = {}
        for m in _items(_try(lambda: v.getType().getMembers())):
            mid = _try(m.getId)
            if mid:
                fields[mid] = _js(_try(lambda mid=mid: v.getPropertyValueFromId(mid)), depth + 1)
        return fields
    if name.startswith("SDValue"):
        if hasattr(v, "getSize") and hasattr(v, "getItem"):
            # Read every item: a cut gradient sent back through set_parameter would lose its keys.
            size = _try(v.getSize, 0) or 0
            items = [_js(_try(lambda i=i: v.getItem(i)), depth + 1) for i in range(min(size, MAX_ARRAY))]
            if size > MAX_ARRAY:
                items.append("(%d more items not shown)" % (size - MAX_ARRAY))
            return items
        if hasattr(v, "get"):
            inner = _try(v.get, _MISSING)
            if inner is not _MISSING:
                return _js(inner, depth + 1)

    if hasattr(v, "getComponents") and hasattr(v, "getName"):  # SDUsage
        return {
            "usage": _try(v.getName),
            "components": _try(v.getComponents),
            "colorspace": _try(v.getColorSpace),
        }

    for attrs in (("r", "g", "b", "a"), ("x", "y", "z", "w"), ("x", "y", "z"), ("x", "y")):
        if all(hasattr(v, a) for a in attrs):
            vals = [_try(lambda a=a: getattr(v, a)) for a in attrs]
            if all(isinstance(x, (int, float)) for x in vals):
                return [round(x, 6) if isinstance(x, float) else x for x in vals]
    return str(v)


# ---------------------------------------------------------- graph / nodes
def _all_packages():
    return _items(_try(_pm().getUserPackages))


def _graphs_in(pkg):
    return [r for r in _items(_try(lambda: pkg.getChildrenResources(True))) if _cls(r).endswith("Graph")]


def _graph(name=None):
    if not name:
        g = _ui().getCurrentGraph()
        if g is None:
            raise RuntimeError(
                "No graph is open in Designer's Graph view. Open one (double-click it "
                "in the Explorer) or pass `graph`."
            )
        return g
    name = str(name)
    pkg_hint = None
    if "::" in name:
        pkg_hint, name = name.split("::", 1)
    found = []
    for pkg in _all_packages():
        path = _try(pkg.getFilePath, "") or ""
        if pkg_hint and not _same_package(path, pkg_hint):
            continue
        for g in _graphs_in(pkg):
            if _gid(g) == name:
                found.append((g, path))
    if len(found) == 1:
        return found[0][0]
    if not found:
        raise RuntimeError("Graph %r not found in open packages. Use list_packages." % name)
    # Several open packages have a graph with this identifier. Take the one shown in the
    # Graph view. Wrappers of the same graph have different handles, so compare URLs.
    cur = _try(lambda: _ui().getCurrentGraph())
    cur_url = _try(lambda: cur.getUrl()) if cur is not None else None
    for g, _ in found:
        if cur_url and _try(lambda: g.getUrl()) == cur_url:
            return g
    paths = [p for _, p in found]
    names = [os.path.basename(p).lower() for p in paths]
    how = ""
    if all(paths) and len(set(names)) == len(names):
        how = ', pass "file.sbs::%s"' % name
    elif all(paths) and len(set(os.path.normcase(p) for p in paths)) == len(paths):
        how = ', pass "<full .sbs path>::%s"' % name
    raise RuntimeError(
        "%d open packages have a graph named %r: %s. Open the one you mean in Designer's Graph "
        "view%s, or close the other package."
        % (len(found), name, [p or "(unsaved package)" for p in paths], how)
    )


def _same_package(path, hint):
    """Does a package file path match the part before "::" (a file name or a full path)?"""
    if "/" in hint or "\\" in hint:
        return bool(path) and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(hint))
    return os.path.basename(path).lower() == hint.lower()


def _node(graph, node_id):
    node_id = str(node_id)
    n = _try(lambda: graph.getNodeFromId(node_id))
    if n is not None:
        return n
    for n in _items(graph.getNodes()):
        if _try(n.getIdentifier) == node_id:
            return n
    raise RuntimeError(
        "Node %r not found in graph %r. Use get_graph to list node ids." % (node_id, _gid(graph))
    )


def _props(node, category):
    return _items(_try(lambda: node.getProperties(category)))


def _ports(node):
    ins = [p.getId() for p in _props(node, SDPropertyCategory.Input) if _try(p.isConnectable, False)]
    outs = [p.getId() for p in _props(node, SDPropertyCategory.Output) if _try(p.isConnectable, True)]
    return {"inputs": ins, "outputs": outs}


def _summary(node):
    d = {"id": _try(node.getIdentifier)}
    df = _try(node.getDefinition)
    if df is not None:
        d["definition"] = _try(df.getId)
        label = _try(df.getLabel)
        if label:
            d["label"] = label
    pos = _try(node.getPosition)
    if pos is not None:
        d["pos"] = [round(pos.x, 1), round(pos.y, 1)]
    res = _try(node.getReferencedResource)
    if res is not None:
        d["instance_of"] = _try(lambda: res.getUrl()) or _try(res.getIdentifier)
    short = (d.get("definition") or "").split("::")[-1]
    if short == "output" or short.startswith("input"):
        ident = _try(lambda: node.getAnnotationPropertyValueFromId("identifier"))
        if ident is not None:
            d["io_identifier"] = _js(ident)
    return d


def _far_end(c, here):
    """(node id, port id) at the other end of connection c from here = (node id, port id).

    Don't trust the getOutputProperty/getInputProperty names: on 12.4.1 the
    "output" end is whichever side the connection was queried from, even an input.
    """
    a_node, a_prop = _try(c.getOutputPropertyNode), _try(c.getOutputProperty)
    b_node, b_prop = _try(c.getInputPropertyNode), _try(c.getInputProperty)
    if a_node is None or a_prop is None or b_node is None or b_prop is None:
        return None
    a = (a_node.getIdentifier(), a_prop.getId())
    b = (b_node.getIdentifier(), b_prop.getId())
    return b if a == tuple(here) else a


def _connections(nodes):
    seen = set()
    out = []
    for n in nodes:
        nid = n.getIdentifier()
        for p in _props(n, SDPropertyCategory.Output):
            here = (nid, p.getId())
            for c in _items(_try(lambda: n.getPropertyConnections(p))):
                far = _far_end(c, here)
                t = here + far if far else None
                if t and t not in seen:
                    seen.add(t)
                    out.append(list(t))
    return out


def _auto_pos(graph, x, y):
    if x is not None and y is not None:
        return [float(x), float(y)]
    xs, ys = [], []
    for m in _items(_try(graph.getNodes)):
        p = _try(m.getPosition)
        if p is not None:
            xs.append(p.x)
            ys.append(p.y)
    if x is None:
        x = (max(xs) + 192.0) if xs else 0.0
    if y is None:
        y = (sorted(ys)[len(ys) // 2]) if ys else 0.0
    return [float(x), float(y)]


def _set_pos(node, pos):
    float2 = _api("sdbasetypes", "float2")
    x, y = float(pos[0]), float(pos[1])
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError("node positions must be finite numbers, not %r" % (list(pos),))
    node.setPosition(float2(x, y))


def _find_loaded_package(path):
    want = os.path.normcase(os.path.abspath(path))
    pm = _pm()
    pools = []
    for getter in ("getUserPackages", "getPackages"):
        fn = getattr(pm, getter, None)
        if fn is not None:
            pools.extend(_items(_try(fn)))
    for pkg in pools:
        fp = _try(pkg.getFilePath)
        if fp and os.path.normcase(os.path.abspath(fp)) == want:
            return pkg
    return None


_LIBRARY_GRAPHS = {}  # .sbs path -> (mtime, graphs)
_PLAIN_LABELS = (["X", "Y"], ["X", "Y", "Z"], ["X", "Y", "Z", "W"])


def _widget_labels(paraminput):
    """What a parameter's widget calls its parts, from the .sbs XML: {"components": [...]} for a
    vector (the Tile Generator's interstice is Interstice X, Random, Interstice Y, Random), or
    {"value_labels": {"false": ..., "true": ...}} for a bool shown as two buttons (DirectX /
    OpenGL). None when the labels add nothing (X, Y, Z, W; False, True)."""
    labels = {}
    for opt in paraminput.iterfind("defaultWidget/options/option"):
        name, value = opt.find("name"), opt.find("value")
        key = (name.get("v") if name is not None else None) or ""
        if value is not None and re.match(r"label[0-3]$", key):
            labels[int(key[5])] = (value.get("v") or "").strip()
    if len(labels) < 2:
        return None
    parts = [labels.get(i, "") for i in range(max(labels) + 1)]
    if not all(parts) or parts in _PLAIN_LABELS or set(parts) in ({"False", "True"}, {"Off", "On"}):
        return None
    widget = paraminput.find("defaultWidget/name")
    if widget is not None and widget.get("v") == "buttons" and len(parts) == 2:
        return {"value_labels": {"false": parts[0], "true": parts[1]}}
    return {"components": parts}


def _library_graphs(path):
    """[{"id", "label", "hidden", "widgets"}] for the graphs of a .sbs file, read from its XML.

    hidden: Designer's Library doesn't list the graph, because of hideInLibrary (the
    "(Legacy)" versions in tile_generator.sbs, clouds_2.sbs, ... and helpers) or because it
    has neither category nor label (helpers like post_effects in pbr_render.sbs).
    widgets: {parameter id: _widget_labels()} for the parameters whose widget labels say more
    than X/Y/Z/W. The sd API has no widget accessor, so get_node reads them from here.
    """
    path = os.path.normpath(path)  # instances report "G:/...", glob gives "G:\..."
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return []
    cached = _LIBRARY_GRAPHS.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    graphs, stack = [], []
    try:
        for event, el in ET.iterparse(path, events=("start", "end")):
            if event == "start":
                stack.append(el.tag)
                continue
            stack.pop()
            if el.tag == "graph" and stack and stack[-1] == "content":
                ident = el.find("identifier")
                attrs = el.find("attributes")
                label = attrs.find("label") if attrs is not None else None
                hide = attrs.find("hideInLibrary") if attrs is not None else None
                category = attrs.find("category") if attrs is not None else None
                widgets = {}
                for pi in el.iterfind("paraminputs/paraminput"):
                    pid, info = pi.find("identifier"), _widget_labels(pi)
                    if pid is not None and info:
                        widgets[pid.get("v")] = info
                graphs.append({
                    "id": ident.get("v") if ident is not None else None,
                    "label": label.get("v") if label is not None else None,
                    "hidden": (hide is not None and hide.get("v") == "1")
                    or (category is None and label is None),
                    "widgets": widgets,
                })
                el.clear()
            elif el.tag in ("compNodes", "paramsArrays"):
                el.clear()  # node data isn't needed; keeps memory low on big packages
    except (ET.ParseError, OSError):
        pass
    _LIBRARY_GRAPHS[path] = (mtime, graphs)
    return graphs


def _main_graph(graphs, base):
    """The graph a package stands for: the one named like the file unless the Library hides it,
    else a shown one named like the file (normal_sobel.sbs keeps its current graph as
    normal_sobel_2 next to a hidden deprecated normal_sobel), else any shown one (shape_glow.sbs
    starts with a hidden helper), else the hidden one named like the file, else the first."""
    base = base.lower()
    named = next((g for g in graphs if (g["id"] or "").lower() == base), None)
    if named is not None and not named["hidden"]:
        return named
    shown = [g for g in graphs if not g["hidden"]]
    prefixed = [g for g in shown if (g["id"] or "").lower().startswith(base)]
    if prefixed or shown:
        return (prefixed or shown)[0]
    return named or (graphs[0] if graphs else None)


def _enumerators(sdtype):
    """[(option id, int value)] for an enum type, else None."""
    if "Enum" not in _cls(sdtype):
        return None
    out = []
    for e in _items(_try(sdtype.getEnumerators)):
        opt = _try(e.getId)
        if opt is not None:
            out.append((opt, _try(lambda e=e: e.getDefaultValue().get())))
    return out or None


def _enum_options(sdtype):
    return [opt for opt, _ in _enumerators(sdtype) or []] or None


def _param_value(node, prop):
    """A parameter's value as JSON; enums as their option id, like set_parameter takes."""
    value = _js(_try(lambda: node.getPropertyValue(prop)))
    if isinstance(value, int) and not isinstance(value, bool):
        sdtype = _try(prop.getType)
        if sdtype is not None:
            for opt, v in _enumerators(sdtype) or []:
                if v == value:
                    return opt
    return value


# Block tags are often the only thing between two sentences or list items ("pattern.<br><h4>
# Note</h4>A value..."), so they become spaces. Only real tags go: "Values < 0.5" stays.
_BREAKS = re.compile(r"<\s*(?:/\s*)?(?:br|p|li|ul|ol|h[1-6]|div|tr)\b[^>]*>", re.I)
_TAGS = re.compile(r"<\s*(?:/\s*)?[A-Za-z][^>]*>")


def _description(prop, label=None):
    """Designer's description of a property as plain text (it's HTML), or None."""
    text = _try(lambda: prop.getDescription())
    if not text:
        return None
    text = " ".join(html.unescape(_TAGS.sub("", _BREAKS.sub(" ", str(text)))).split())
    if not text or text == label or text == _try(prop.getId):
        return None
    return text if len(text) <= 300 else text[:297] + "..."


def _inheritance(owner, prop):
    """Name of a base parameter's inheritance method (Absolute, RelativeToInput, ...), or None."""
    method = _try(lambda: owner.getPropertyInheritanceMethod(prop))
    return None if method is None else getattr(method, "name", str(method))


def _inherited_unchanged(owner, prop, method):
    """Is a base parameter inherited with a value that changes nothing? An $outputsize offset
    of 0 (its getDefaultValue is 8, the default for Absolute), the default for the others."""
    if not method or method == "Absolute":
        return False
    neutral = [0, 0] if prop.getId() == "$outputsize" else _js(_try(lambda: prop.getDefaultValue()))
    value = _js(_try(lambda: owner.getPropertyValue(prop)))
    return neutral is not None and value == neutral


def _instance_widgets(node):
    """Widget labels ({parameter id: info}, see _widget_labels) of the graph a library node
    instances, read from its .sbs; {} for atomic nodes and graphs in unsaved packages."""
    ref = _try(node.getReferencedResource)
    path = _try(lambda: ref.getPackage().getFilePath()) if ref is not None else None
    if not path or not os.path.isfile(path):
        return {}
    gid = _gid(ref)
    return next((g.get("widgets") or {} for g in _library_graphs(path) if g["id"] == gid), {})


# ------------------------------------------------------------ value builder
def _to_bool(value):
    if isinstance(value, str):
        # Anything else is a mistake, not false: "OpenGL" from get_node's value_labels was
        # silently stored as false (DirectX).
        s = value.strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off"):
            return False
        raise ValueError(
            "bool parameter: pass true or false, not %r (get_node's value_labels say what each "
            "one shows)" % value
        )
    return bool(value)


def _vec(value, n):
    if isinstance(value, str):
        value = [v for v in re.split(r"[,\s]+", value.strip().strip("[]()")) if v]
    if isinstance(value, (list, tuple)):
        vals = list(value)
    else:
        vals = [value] * n
    if len(vals) != n:
        raise ValueError("expected %d components, got %d" % (n, len(vals)))
    return vals


def _color(value):
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("#"):
            h = s[1:]
            if len(h) not in (6, 8):
                raise ValueError("hex colors must be #rrggbb or #rrggbbaa")
            value = [int(h[i:i + 2], 16) / 255.0 for i in range(0, len(h), 2)]
        else:
            value = [v for v in re.split(r"[,\s]+", s) if v]
    if not isinstance(value, (list, tuple)):
        raise ValueError("colors need 3 or 4 components (0-1) or a hex string")
    vals = [float(v) for v in value]
    if len(vals) == 3:
        vals.append(1.0)
    if len(vals) != 4:
        raise ValueError("colors need 3 or 4 components (0-1) or a hex string")
    return vals


def _make_value(sdtype, value):
    tid = _try(sdtype.getId, "") or ""
    low = tid.lower()
    bt = importlib.import_module("sd.api.sdbasetypes")

    if low == "float":
        return _api("sdvaluefloat", "SDValueFloat").sNew(float(value))
    if low == "int":
        return _api("sdvalueint", "SDValueInt").sNew(int(round(float(value))))
    if low == "bool":
        return _api("sdvaluebool", "SDValueBool").sNew(_to_bool(value))
    if low == "string":
        return _api("sdvaluestring", "SDValueString").sNew(str(value))

    m = re.match(r"^(float|int)([234])$", low)
    if m:
        kind, n = m.group(1), int(m.group(2))
        if kind == "float" and n >= 3 and isinstance(value, str) and value.strip().startswith("#"):
            # Library graphs expose colors as float3/float4, not ColorRGBA.
            comps = _color(value)[:n]
        elif kind == "float":
            comps = [float(x) for x in _vec(value, n)]
        else:
            comps = [int(round(float(x))) for x in _vec(value, n)]
        base = getattr(bt, low)(*comps)
        return _api("sdvalue" + low, "SDValue" + kind.capitalize() + str(n)).sNew(base)

    if low == "colorrgba":
        return _api("sdvaluecolorrgba", "SDValueColorRGBA").sNew(bt.ColorRGBA(*_color(value)))

    cls = _cls(sdtype)
    if cls == "SDTypeArray":
        return _make_key_array(sdtype, value)

    if "Enum" in cls:
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            want = str(value).strip()
            try:
                return _api("sdvalueenum", "SDValueEnum").sFromValueId(tid, want)
            except ERRORS:
                pass
            # Enums declared by a library graph (the Tile Generator's "pattern") aren't
            # registered globally, so sFromValueId raises ItemNotFound. An int works. Their
            # ids are the dropdown labels, some of them numbers ("90" has the value 1), so
            # match labels only.
            for opt, v in _enumerators(sdtype) or []:
                if str(opt).strip() == want and isinstance(v, int):  # some labels end in a space
                    return _api("sdvalueint", "SDValueInt").sNew(v)
        raise ValueError(
            "property type %s is an enum: pass one of these option ids as a string: %s"
            % (tid, _enum_options(sdtype))
        )

    raise ValueError("unsupported property type %r; use run_python for this one" % tid)


KEYS_HELP = (
    "pass gradient keys as a list with one entry per key: [position, r, g, b(, a)] in 0-1, "
    "[position, [r, g, b(, a)]], [position, \"#rrggbb\"], or the {\"position\", \"value\", "
    "\"midpoint\"} objects get_node shows"
)


def _make_key_array(sdtype, value):
    """SDValueArray of gradient keys (the Gradient Map's `gradientrgba`) from JSON-style keys."""
    tid = _try(sdtype.getId, "") or ""
    item_id = _try(lambda: sdtype.getItemType().getId(), "") or ""
    item = _try(lambda: _api("sdtypestruct", "SDTypeStruct").sNew(item_id)) if item_id else None
    members = {}
    for m in _items(_try(item.getMembers) if item is not None else None):
        mid = _try(m.getId)
        if mid:
            members[mid] = _try(m.getType)
    if "position" not in members or "value" not in members:
        raise ValueError("unsupported property type %r; use run_python for this one" % tid)

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            raise ValueError(KEYS_HELP)
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError(KEYS_HELP)
    keys = []
    for key in value:
        if isinstance(key, dict):
            fields = dict(key)
        elif isinstance(key, (list, tuple)) and len(key) >= 2:
            fields = {"position": key[0], "value": key[1] if len(key) == 2 else list(key[1:])}
        else:
            raise ValueError("bad key %r: %s" % (key, KEYS_HELP))
        for mid in fields:
            if mid not in members:
                raise ValueError("gradient keys have the fields %s, not %r" % (sorted(members), mid))
        keys.append(fields)
    keys.sort(key=lambda f: float(f.get("position", 0)))

    SDValueStruct = _api("sdvaluestruct", "SDValueStruct")
    arr = _api("sdvaluearray", "SDValueArray").sNew(item, 0)
    for fields in keys:
        s = SDValueStruct.sNew(item)
        for mid, val in fields.items():  # midpoint stays 0 unless given, as Designer writes it
            s.setPropertyValueFromId(mid, _make_value(members[mid], val))
        arr.pushBack(s)
    return arr


def _api_reason(e):
    """Readable text for an APIException (its argument is an SDApiError)."""
    code = getattr(e, "mErrorCode", None)
    name = getattr(code, "name", None) or str(e)
    return {
        "DataIsReadOnly": "the parameter is read-only",
        "DataIsFunctionOnly": "the parameter is function-only: a function graph sets its value",
        "TypeConversionFailed": "the value doesn't convert to this parameter's type",
        "InvalidType": "the value has the wrong type for this parameter",
        "InvalidValue": "Designer rejected the value",
    }.get(name, name)


# ----------------------------------------------------------------- commands
def cmd_ping(args):
    return {"pong": True}


def cmd_info(args):
    from . import VERSION

    app = _app()
    d = {
        "bridge_version": VERSION,
        "python": sys.version.split()[0],
        "run_python_enabled": ALLOW_PYTHON,
        "undo_groups": _has_undo(),
    }
    ver = _try(lambda: app.getVersion())
    if ver is not None:
        d["designer_version"] = str(ver)
    grid = _try(lambda: importlib.import_module("sd.ui.graphgrid").GraphGrid.sGetFirstLevelSize())
    if grid:
        d["grid_size"] = grid
    g = _try(lambda: _ui().getCurrentGraph())
    if g is not None:
        pkg = _try(g.getPackage)
        d["current_graph"] = {
            "identifier": _gid(g),
            "type": _cls(g),
            "package": (_try(pkg.getFilePath) if pkg is not None else None) or "(unsaved)",
            "node_count": len(_items(_try(g.getNodes))),
        }
    else:
        d["current_graph"] = None
    d["open_packages"] = len(_all_packages())
    return d


def cmd_list_packages(args):
    out = []
    for pkg in _all_packages():
        out.append(
            {
                "file": _try(pkg.getFilePath) or "(unsaved)",
                "graphs": [{"identifier": _gid(g), "type": _cls(g)} for g in _graphs_in(pkg)],
            }
        )
    return {"packages": out}


def _params(node):
    params = {}
    for p in _props(node, SDPropertyCategory.Input):
        if _try(p.isConnectable, False):
            continue
        params[p.getId()] = _param_value(node, p)
    return params


def _graph_params(g):
    """The graph's own parameters: base ones ($outputsize, $format, ...) with their inheritance,
    and any it exposes."""
    out = {}
    for p in _props(g, SDPropertyCategory.Input):
        if _try(p.isConnectable, False):
            continue
        info = {"value": _param_value(g, p)}
        if p.getId().startswith("$"):
            method = _inheritance(g, p)
            if method:
                info["inheritance"] = method
            value = info["value"]
            if p.getId() == "$outputsize" and method == "Absolute" and isinstance(value, list) \
                    and all(isinstance(v, int) and 0 <= v <= 16 for v in value):
                info["size_px"] = [1 << v for v in value]  # log2: 11 is 2048
        out[p.getId()] = info
    return out


def cmd_get_graph(args):
    g = _graph(args.get("graph"))
    nodes = _items(g.getNodes())
    limit = int(args.get("limit") or 400)
    listed = nodes[:limit]
    out_nodes = []
    for n in listed:
        s = _summary(n)
        if args.get("include_values"):
            s["params"] = _params(n)
        out_nodes.append(s)
    d = {"graph": _gid(g), "type": _cls(g)}
    params = _graph_params(g)
    if params:
        d["graph_params"] = params
        size = params.get("$outputsize")
        if size and size.get("inheritance") not in (None, "Absolute"):
            # getDefaultParentSize() is unset on 12.4.1, so the pixel size isn't knowable here.
            d["graph_params_note"] = (
                "$outputsize is relative to the parent (an offset in log2), so its size in pixels "
                "isn't readable here. render_preview captions give each Output's computed size, "
                "which matches the graph only for outputs with no Absolute $outputsize upstream. "
                "set_parameter(node=\"graph\", property=\"$outputsize\", value=[11, 11]%s) makes "
                "the graph 2048x2048; nodes that inherit their size follow it."
                # Name the graph that was read: without graph=, the call edits the one in the view.
                % (", graph=\"%s\"" % args["graph"] if args.get("graph") else "")
            )
    connections = _connections(nodes)
    d.update({
        "node_count": len(nodes),
        "truncated": len(nodes) > limit,
        "nodes": out_nodes,
        "connection_format": "[from_node, from_output, to_node, to_input]",
    })
    if len(nodes) > limit:
        # Only links between listed nodes: the others would name nodes the reply doesn't show.
        ids = set(s.get("id") for s in out_nodes)
        shown = [c for c in connections if c[0] in ids and c[2] in ids]
        d["connections_omitted"] = len(connections) - len(shown)
        connections = shown
    d["connections"] = connections
    return d


def cmd_get_node(args):
    g = _graph(args.get("graph"))
    n = _node(g, args["node"])
    d = _summary(n)
    widgets = _instance_widgets(n)
    inputs, params, inherited = [], [], []
    for p in _props(n, SDPropertyCategory.Input):
        info = {"id": p.getId()}
        t = _try(p.getType)
        if t is not None:
            info["type"] = _try(t.getId)
        label = _try(p.getLabel)
        if label and label != info["id"]:
            info["label"] = label
        if not info["id"].startswith("$"):  # base parameters all carry the same boilerplate
            desc = _description(p, label)
            if desc:
                info["description"] = desc
        if _try(p.isConnectable, False):
            sources = []
            for c in _items(_try(lambda: n.getPropertyConnections(p))):
                far = _far_end(c, (d["id"], info["id"]))
                if far:
                    sources.append(list(far))
            info["connected_from"] = sources
            inputs.append(info)
        else:
            if info["id"].startswith("$"):
                method = _inheritance(n, p)
                if not args.get("all_params") and _inherited_unchanged(n, p, method):
                    inherited.append(info["id"])  # same six on every node: only list them
                    continue
            info["value"] = _param_value(n, p)
            if t is not None:
                opts = _enum_options(t)
                if opts:
                    info["options"] = opts
            info.update(widgets.get(info["id"]) or {})
            if info["id"].startswith("$") and method:
                info["inheritance"] = method
            params.append(info)
    d["inputs"] = inputs
    d["params"] = params
    if inherited:
        d["inherited_base_params"] = inherited
    d["outputs"] = [
        {"id": p.getId(), "type": _try(lambda: p.getType().getId())}
        for p in _props(n, SDPropertyCategory.Output)
    ]
    anns = {}
    for p in _props(n, SDPropertyCategory.Annotation)[:40]:
        val = _js(_try(lambda: n.getPropertyValue(p)))
        if val not in (None, "", []):
            anns[p.getId()] = val
    if anns:
        d["annotations"] = anns
    return d


def cmd_get_selection(args):
    ui = _ui()
    g = _try(ui.getCurrentGraph)
    if g is None:
        # The selection getters raise InvalidArgument when no graph is open.
        return {"graph": None, "selected": [], "note": "No graph is open in Designer's Graph view."}
    for name in ("getCurrentGraphSelectedNodes", "getCurrentGraphSelection"):
        fn = getattr(ui, name, None)
        if fn is not None:
            return {"graph": _gid(g), "selected": [_summary(n) for n in _items(fn())]}
    raise RuntimeError("This Designer build has no selection API; ask the user which nodes they mean.")


def cmd_list_node_definitions(args):
    ids = set()
    mm = _try(lambda: _app().getModuleMgr())
    if mm is not None:
        for m in _items(_try(mm.getModules)):
            for df in _items(_try(m.getDefinitions)):
                i = _try(df.getId)
                if i:
                    ids.add(i)
    source = "designer"
    if not ids:
        ids = set(COMMON_ATOMIC)
        source = "built-in fallback list"
    q = str(args.get("query") or "").lower()
    # sbs:: ids (what create_node builds) first; otherwise ~2600 mdl:: ids fill the list.
    found = sorted((i for i in ids if q in i.lower()), key=lambda i: (not i.startswith("sbs::"), i))
    res = {"source": source, "count": len(found), "definitions": found[:300]}
    if len(found) > 300:
        res["note"] = "Showing 300 of %d. Narrow the query, e.g. 'sbs::compositing' or 'sbs::function'." % len(found)
    return res


_ATOMIC = []  # [(definition id without "sbs::compositing::", label)], read once


def _atomic_nodes():
    """The atomic compositing nodes create_node makes (Levels, Blur, Emboss, ...). The Output
    node is left out: create_output makes it, and its definition is labelled "Input"."""
    if not _ATOMIC:
        mm = _try(lambda: _app().getModuleMgr())
        for m in _items(_try(mm.getModules) if mm is not None else None):
            for df in _items(_try(m.getDefinitions)):
                i = _try(df.getId) or ""
                if i.startswith("sbs::compositing::") and i != "sbs::compositing::output":
                    _ATOMIC.append((i.split("::")[-1], _try(df.getLabel) or ""))
        _ATOMIC.sort()
    return _ATOMIC or [(i.split("::")[-1], "") for i in COMMON_ATOMIC if not i.endswith("::output")]


def cmd_search_library(args):
    SDApplicationPath = _api("sdapplication", "SDApplicationPath")
    res_dir = _app().getPath(SDApplicationPath.DefaultResourcesDir)
    pkg_dir = os.path.normpath(os.path.join(res_dir, "packages"))
    files = sorted(glob.glob(os.path.join(glob.escape(pkg_dir), "**", "*.sbs"), recursive=True))
    tokens = [t for t in re.split(r"[\s_\-]+", str(args.get("query") or "").lower()) if t]
    limit = int(args.get("limit") or 25)
    hits, by_label = [], []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        # Reads the package XML: the first search reads all of them (about 2 s), then cached.
        graphs = _library_graphs(f)
        if not all(t in name.lower() for t in tokens):
            # Some packages hold several nodes named unlike the file (blend.sbs has Color
            # Dodge, Difference, ...), so match the labels and ids of the shown graphs too.
            for g in graphs:
                text = ("%s %s" % (g["label"] or "", g["id"] or "")).lower()
                if g["id"] and not g["hidden"] and all(t in text for t in tokens):
                    by_label.append({
                        "name": name,
                        "package_path": f,
                        "label": g["label"] or g["id"],
                        "graph_identifier": g["id"],
                    })
            continue
        main = _main_graph(graphs, name)
        hit = {"name": name, "package_path": f}
        if main is not None:
            if main["label"]:
                hit["label"] = main["label"]
            if main["hidden"]:
                hit["hidden_in_library"] = True
        shown = [g["id"] for g in graphs if not g["hidden"]]
        if len(shown) > 1:
            hit["graphs"] = shown  # choices for create_library_node's graph_identifier
        hits.append(hit)
    # The Library shows only current nodes: tile_generator.sbs is "Tile Generator (Legacy)",
    # pattern_tile_generator.sbs the current one. List those first, then the label matches.
    shown_hits = [h for h in hits if not h.get("hidden_in_library")]
    hidden_hits = [h for h in hits if h.get("hidden_in_library")]
    hits = shown_hits + by_label + hidden_hits
    # Levels, Blur, Emboss, ... aren't packages but atomic nodes: point to create_node for them.
    atomic = [
        {"definition": short, "label": label}
        for short, label in (_atomic_nodes() if tokens else [])
        if all(t in ("%s %s" % (label, short)).lower() for t in tokens)
    ]
    out = {"library_dir": pkg_dir, "total_packages": len(files)}
    if atomic:
        out["atomic"] = atomic
    out.update({"match_count": len(hits), "matches": hits[:limit]})
    notes = []
    if atomic:
        notes.append("`atomic` entries are built-in nodes, not packages: create them with create_node(definition).")
    if by_label:
        notes.append(
            "Matches with a graph_identifier are one node in a package of several: pass both "
            "package_path and graph_identifier to create_library_node."
        )
    if hidden_hits:
        notes.append(
            "hidden_in_library packages are legacy versions or helpers that Designer's Library "
            "doesn't show. Prefer the others."
        )
    if notes:
        out["note"] = " ".join(notes)
    return out


def cmd_create_node(args):
    g = _graph(args.get("graph"))
    definition = str(args["definition"]).strip()
    if "::" not in definition and _cls(g) == "SDSBSCompGraph":
        definition = "sbs::compositing::" + definition
    pos = _auto_pos(g, args.get("x"), args.get("y"))
    with _undo("create " + definition.split("::")[-1]):
        n = _try(lambda: g.newNode(definition))  # 12.4.1 raises InvalidArgument for unknown ids
        if n is None:
            raise RuntimeError(
                "Designer could not create %r (unknown id, or not valid in a %s). "
                "Try list_node_definitions." % (definition, _cls(g))
            )
        _set_pos(n, pos)
    d = _summary(n)
    d.update(_ports(n))
    return d


def cmd_create_library_node(args):
    g = _graph(args.get("graph"))
    path = os.path.normpath(str(args["package_path"]))
    if not os.path.isfile(path):
        raise RuntimeError("No such package file: %s (use search_library to find one)" % path)
    base = os.path.splitext(os.path.basename(path))[0]
    xml_graphs = _library_graphs(path)
    pos = _auto_pos(g, args.get("x"), args.get("y"))

    # Opening and closing the package are undo steps of their own, so they go in the group
    # too. Otherwise the first Ctrl+Z only reopens the library package in the Explorer.
    with _undo("add " + base):
        pkg = _find_loaded_package(path)
        opened_here = pkg is None
        if opened_here:
            pkg = _try(lambda: _pm().loadUserPackage(path, True))
        if pkg is None:
            raise RuntimeError("Designer could not load %s" % path)
        try:
            graphs = [r for r in _items(pkg.getChildrenResources(True)) if _cls(r) == "SDSBSCompGraph"]
            want = args.get("graph_identifier")
            if not want:
                main = _main_graph(xml_graphs, base)
                want = main["id"] if main else None
            res = next((r for r in graphs if _gid(r) == want), None)
            if res is None and not args.get("graph_identifier") and graphs:
                res = graphs[0]
            if res is None:
                raise RuntimeError(
                    "No matching graph in %s. Graphs available: %s" % (path, [_gid(r) for r in graphs])
                )
            n = _try(lambda: g.newInstanceNode(res))
            if n is None:
                raise RuntimeError("Designer could not instance %s" % _gid(res))
            _set_pos(n, pos)
        finally:
            if opened_here:
                # loadUserPackage opened the library package in the Explorer. Close it again,
                # as dragging from the Library would: it stays loaded as a dependency.
                _try(lambda: _pm().unloadUserPackage(pkg))
    d = _summary(n)
    d.update(_ports(n))
    hidden = set(x["id"] for x in xml_graphs if x["hidden"])
    others = [_gid(r) for r in graphs if _gid(r) != _gid(res) and _gid(r) not in hidden]
    if others:
        d["other_graphs_in_package"] = others
    return d


def _usage_class():
    for mod in ("sdusage", "sdvalueusage"):
        cls = _try(lambda m=mod: _api(m, "SDUsage"))
        if cls is not None:
            return cls
    raise RuntimeError("SDUsage not found in this Designer build")


def cmd_create_output(args):
    g = _graph(args.get("graph"))
    ident = str(args["identifier"]).strip()
    usage = args.get("usage")
    label = args.get("label") or ident
    warnings = []
    pos = _auto_pos(g, args.get("x"), args.get("y"))
    with _undo("create output " + ident):
        n = _try(lambda: g.newNode("sbs::compositing::output"))
        if n is None:
            raise RuntimeError("Output nodes can only be created in a Substance compositing graph")
        _set_pos(n, pos)
        SDValueString = _api("sdvaluestring", "SDValueString")
        for key, val in (("identifier", ident), ("label", label)):
            try:
                n.setAnnotationPropertyValueFromId(key, SDValueString.sNew(val))
            except ERRORS as e:
                warnings.append("could not set %s: %s" % (key, e))
        if usage:
            try:
                SDValueArray = _api("sdvaluearray", "SDValueArray")
                SDTypeUsage = _api("sdtypeusage", "SDTypeUsage")
                SDValueUsage = _api("sdvalueusage", "SDValueUsage")
                SDUsage = _usage_class()
                srgb = ("basecolor", "diffuse", "emissive", "specular", "specularcolor")
                cs = args.get("colorspace") or ("sRGB" if str(usage).lower() in srgb else "Linear")
                arr = SDValueArray.sNew(SDTypeUsage.sNew(), 0)
                arr.pushBack(SDValueUsage.sNew(SDUsage.sNew(str(usage), "RGBA", cs)))
                n.setAnnotationPropertyValueFromId("usages", arr)
            except ERRORS as e:
                warnings.append("could not set usage: %s" % e)
    d = _summary(n)
    d.update(_ports(n))
    if warnings:
        d["warnings"] = warnings
    return d


def _feeds(graph, start, target_id):
    """True when node target_id is downstream of start."""
    seen, todo = set(), [start]
    while todo:
        nxt = []
        for t in _connections(todo):
            if t[2] == target_id:
                return True
            if t[2] not in seen:
                seen.add(t[2])
                n = _try(lambda i=t[2]: graph.getNodeFromId(i))
                if n is not None:
                    nxt.append(n)
        todo = nxt
    return False


def cmd_connect(args):
    g = _graph(args.get("graph"))
    a = _node(g, args["from_node"])
    b = _node(g, args["to_node"])
    outs = _ports(a)["outputs"]
    fo = args.get("from_output")
    if not fo:
        if not outs:
            raise RuntimeError("Node %s has no connectable outputs" % a.getIdentifier())
        fo = outs[0]
    ti = str(args["to_input"])
    if a.getIdentifier() == b.getIdentifier():
        raise RuntimeError("Can't connect node %s to itself." % a.getIdentifier())
    if _feeds(g, b, a.getIdentifier()):
        raise RuntimeError(
            "Connecting %s to %s would make a loop: %s already feeds %s."
            % (a.getIdentifier(), b.getIdentifier(), b.getIdentifier(), a.getIdentifier())
        )
    with _undo("connect"):
        try:
            a.newPropertyConnectionFromId(str(fo), b, ti)
        except ERRORS as e:
            raise RuntimeError(
                "Could not connect %s.%s to %s.%s (%s). %s outputs: %s. %s inputs: %s"
                % (a.getIdentifier(), fo, b.getIdentifier(), ti, e,
                   a.getIdentifier(), outs, b.getIdentifier(), _ports(b)["inputs"])
            )
    res = {"connected": [a.getIdentifier(), fo, b.getIdentifier(), ti]}
    if len(outs) > 1 and not args.get("from_output"):
        res["note"] = "from_output defaulted to %r; node also has %s" % (fo, outs[1:])
    return res


def cmd_disconnect(args):
    g = _graph(args.get("graph"))
    n = _node(g, args["node"])
    pid = str(args["input"])
    p = _try(lambda: n.getPropertyFromId(pid, SDPropertyCategory.Input))
    if p is None:
        raise RuntimeError("No input %r on %s. Inputs: %s" % (pid, n.getIdentifier(), _ports(n)["inputs"]))
    with _undo("disconnect " + pid):
        n.deletePropertyConnections(p)
    return {"disconnected": [n.getIdentifier(), pid]}


def cmd_set_parameter(args):
    g = _graph(args.get("graph"))
    # node "graph" edits the graph's own parameters (get_graph's graph_params), e.g. the
    # $outputsize every node that inherits its size follows. Node ids are numbers.
    on_graph = str(args["node"]).strip().lower() == "graph"
    n = g if on_graph else _node(g, args["node"])
    nid = "graph %s" % _gid(g) if on_graph else n.getIdentifier()
    pid = str(args["property"])
    p = _try(lambda: n.getPropertyFromId(pid, SDPropertyCategory.Input))
    if p is None:
        raise RuntimeError("No parameter %r on %s. Parameters: %s" % (pid, nid, sorted(_params(n))))
    # Image and function slots are connectable and read-only. MDL and Model graph inputs
    # (roughness, width, ...) are connectable too but hold values that can be set.
    if _try(p.isConnectable, False) and _try(lambda: p.isReadOnly(), False):
        raise RuntimeError("%r on %s is an input slot, not a parameter: wire it with connect_nodes." % (pid, nid))
    if _try(lambda: p.isFunctionOnly(), False):
        raise RuntimeError(
            "%r on %s is function-only: a function graph computes it (like a Pixel Processor's "
            "per-pixel function), so there is no value to set. Edit the function with run_python "
            "(node.getPropertyGraph / newPropertyGraph)." % (pid, nid)
        )
    if _try(lambda: p.isReadOnly(), False):
        raise RuntimeError("%r on %s is read-only." % (pid, nid))
    sdtype = p.getType()
    value = args.get("value")
    if not on_graph and isinstance(value, str) and (_try(sdtype.getId, "") or "").lower() == "bool":
        # A library bool shown as two buttons also takes its button labels ("OpenGL").
        labels = (_instance_widgets(n).get(pid) or {}).get("value_labels") or {}
        value = next((k for k, v in labels.items() if v.lower() == value.strip().lower()), value)
    sdv = _make_value(sdtype, value)
    with _undo("set " + pid):
        old_method = None
        if pid.startswith("$"):
            # Base parameters inherit from the input or the parent by default; make the value
            # stick. Nodes and graphs both have setPropertyInheritanceMethod.
            method = _try(lambda: _api("sdproperty", "SDPropertyInheritanceMethod").Absolute)
            if method is not None:
                old_method = _try(lambda: n.getPropertyInheritanceMethod(p))
                _try(lambda: n.setPropertyInheritanceMethod(p, method))
        try:
            n.setInputPropertyValueFromId(pid, sdv)
        except APIException as e:
            if old_method is not None:
                # Don't leave the parameter switched to Absolute when the value wasn't set.
                _try(lambda: n.setPropertyInheritanceMethod(p, old_method))
            raise RuntimeError(
                "Could not set %r on %s (type %s): %s." % (pid, nid, _try(sdtype.getId), _api_reason(e))
            )
    res = {"node": "graph", "graph": _gid(g)} if on_graph else {"node": nid}
    res.update({"property": pid, "type": _try(sdtype.getId), "value": _param_value(n, p)})
    if pid.startswith("$"):
        res["inheritance"] = _inheritance(n, p)
        if res["inheritance"] != "Absolute":
            res["warning"] = (
                "%s is still %s, so the value is an offset or ignored, not absolute."
                % (pid, res["inheritance"] or "of unknown inheritance")
            )
    if not on_graph and _try(lambda: n.getPropertyGraph(p)) is not None:
        res["note"] = "A function graph drives this parameter, so Designer uses its result, not this value."
    return res


def cmd_move_nodes(args):
    g = _graph(args.get("graph"))
    # Resolve every node and position first, so a bad entry moves nothing.
    plan = [(_node(g, m["node"]), [float(m["x"]), float(m["y"])]) for m in args.get("moves") or []]
    moved = []
    with _undo("move nodes"):
        for n, pos in plan:
            _set_pos(n, pos)
            moved.append(n.getIdentifier())
    return {"moved": moved}


def cmd_delete_nodes(args):
    g = _graph(args.get("graph"))
    # A repeated id would delete the node, then fail on its stale handle.
    ids = list(dict.fromkeys(str(i) for i in (args.get("nodes") or [])))
    if not ids:
        raise ValueError("nodes is empty")
    targets = [_node(g, i) for i in ids]  # resolve all first so nothing is half-deleted
    with _undo("delete %d node(s)" % len(targets)):
        for n in targets:
            g.deleteNode(n)
    return {"deleted": ids}


def cmd_create_graph(args):
    ident = str(args["identifier"]).strip()
    path = args.get("package_path")
    clashes = [
        _try(p.getFilePath, "") or "(unsaved package)"
        for p in _all_packages()
        for other in _graphs_in(p)
        if _gid(other) == ident
    ]
    if clashes:
        # Tools find graphs by identifier, and 12.4.1 can't open the new graph in the Graph
        # view, so a second graph with this name would be unreachable (or worse, graph=ident
        # would edit the other one).
        raise RuntimeError(
            "An open package already has a graph named %r (%s). Pick another identifier, or ask "
            "the user to close that package." % (ident, ", ".join(clashes))
        )
    if path:
        pkg = _find_loaded_package(path)
        if pkg is None:
            raise RuntimeError("Package %s is not open in Designer" % path)
    else:
        pkg = _pm().newUserPackage()
    SDSBSCompGraph = getattr(importlib.import_module("sd.api.sbs.sdsbscompgraph"), "SDSBSCompGraph")
    g = SDSBSCompGraph.sNew(pkg)
    g.setIdentifier(ident)
    opened = False
    fn = getattr(_ui(), "openResourceInEditor", None)
    if fn is not None:
        opened = _try(lambda: (fn(g), True)[1], False)
    return {
        "graph": _gid(g),
        "package": _try(pkg.getFilePath) or "(new unsaved package)",
        "opened_in_editor": opened,
        "hint": None if opened else "Double-click the new graph in Designer's Explorer to open it, or pass graph=%r to tools." % ident,
    }


def _same_file(a, b):
    try:
        return os.path.samefile(a, b)  # also right for another case or a link on macOS/Windows
    except OSError:
        return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def cmd_save_package(args):
    save_as = args.get("save_as")
    if save_as is not None and not (isinstance(save_as, str) and save_as.strip()):
        # A blank (or non-string) save_as must not fall through to overwriting the package's file.
        raise ValueError("save_as must be a full .sbs path. Leave it out to overwrite the package.")
    g = _graph(args.get("graph"))
    pkg = g.getPackage()
    own = _try(pkg.getFilePath)
    path = save_as if save_as is not None else own
    if not path:
        raise RuntimeError("This package has never been saved. Pass save_as with a full .sbs path.")
    path = str(path)
    if "\x00" in path:
        # Designer's C side would stop at the NUL and write to a different file.
        raise ValueError("save path contains a NUL character")
    path = os.path.normpath(path)
    if not path.lower().endswith(".sbs"):
        raise ValueError("save path must end in .sbs")
    if not os.path.isabs(path):
        raise ValueError("save path must be a full path, not %r" % path)
    if not os.path.isdir(os.path.dirname(path)):
        raise ValueError("folder does not exist: %s" % os.path.dirname(path))
    res_dir = _try(lambda: _app().getPath(_api("sdapplication", "SDApplicationPath").DefaultResourcesDir))
    if res_dir:
        lib = os.path.normcase(os.path.normpath(os.path.join(res_dir, "packages"))) + os.sep
        if os.path.normcase(path).startswith(lib):
            raise ValueError(
                "%s is in Designer's own library folder, which this won't write to. Pass save_as "
                "with a path outside it." % path
            )
    if os.path.exists(path) and not (own and _same_file(path, str(own))) and args.get("overwrite") is not True:
        # Another package's file, maybe open in Designer too: replace it only when asked to.
        raise ValueError(
            "%s already exists and isn't this package's file. Pass overwrite=true to replace it, "
            "or pick another path." % path
        )
    _pm().savePackageAs(pkg, path)
    return {"saved": path}


def _texture(node, output_id=None):
    """The computed texture of a node's output (its first one by default), else None."""
    for p in _props(node, SDPropertyCategory.Output):
        if output_id and p.getId() != output_id:
            continue
        val = _try(lambda: node.getPropertyValue(p))
        tex = _try(val.get) if val is not None else None
        return tex if tex is not None and hasattr(tex, "save") else None
    return None


def _pixel_kind(tex):
    """("grayscale" or "color", pixel format name) of a texture, or (None, None)."""
    fmt = _try(lambda: tex.getPixelFormat()) if tex is not None else None
    name = getattr(fmt, "name", None)
    if not name or name == "Unknown":
        return None, None
    return ("grayscale" if name.startswith("LUM") else "color"), name


def _blend_notes(graph):
    """Notes for Blends whose `source` is the other kind (grayscale vs color) than the Blend
    itself. On 12.4.1 a color Blend skips a grayscale source (the output is the destination)
    and a grayscale Blend reads a color source as black. A grayscale opacity mask is fine."""
    notes = []
    for n in _items(_try(graph.getNodes)):
        if _try(lambda: n.getDefinition().getId()) != "sbs::compositing::blend":
            continue
        nid = n.getIdentifier()
        kind, fmt = _pixel_kind(_texture(n))
        src = _try(lambda: n.getPropertyFromId("source", SDPropertyCategory.Input))
        if kind is None or src is None:
            continue  # not computed: nothing downstream of it is an Output node
        for c in _items(_try(lambda: n.getPropertyConnections(src))):
            far = _far_end(c, (nid, "source"))
            up = _try(lambda: graph.getNodeFromId(far[0])) if far else None
            src_kind, src_fmt = _pixel_kind(_texture(up, far[1])) if up is not None else (None, None)
            if src_kind is None or src_kind == kind:
                continue
            if src_kind == "grayscale":
                effect = "Designer skips it and the Blend outputs its destination unchanged"
                fix = "Colorize it first (Gradient Map), or use it as the `opacity` mask instead"
            else:
                effect = "Designer reads it as black"
                fix = "Convert it first (Grayscale Conversion), or feed a color `destination`"
            notes.append(
                "Blend %s: source %s.%s is %s (%s) but the Blend is %s (%s, set by its destination), "
                "so %s (red dotted link). %s."
                % (nid, far[0], far[1], src_kind, src_fmt, kind, fmt, effect, fix)
            )
    return notes


def cmd_render(args):
    g = _graph(args.get("graph"))
    out_dir = os.path.join(tempfile.gettempdir(), "sd_claude_bridge", "previews")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    g.compute()
    if args.get("node"):
        targets = [_node(g, args["node"])]
    else:
        targets = _items(_try(lambda: g.getOutputNodes()))
        if not targets:
            raise RuntimeError("Graph has no Output nodes. Add one, or pass `node`.")
    images, notes = [], []
    for n in targets:
        nid = n.getIdentifier()
        ident = _js(_try(lambda: n.getAnnotationPropertyValueFromId("identifier")))
        label = ident or _summary(n).get("label") or nid
        for p in _props(n, SDPropertyCategory.Output):
            val = _try(lambda: n.getPropertyValue(p))
            tex = _try(val.get) if val is not None else None
            if tex is None or not hasattr(tex, "save"):
                notes.append(
                    "%s.%s: no texture. Designer only computes nodes that feed an Output node; "
                    "connect it to one, or preview a node downstream of it." % (nid, p.getId())
                )
                continue
            fname = re.sub(r"[^A-Za-z0-9_.-]+", "_", "%s_%s_%s.png" % (_gid(g), ident or nid, p.getId()))
            path = os.path.join(out_dir, fname)
            tex.save(path)
            image = {"node": nid, "output": p.getId(), "label": str(label), "path": path}
            size = _try(lambda: tex.getSize())
            if size is not None:
                image["size"] = [size.x, size.y]  # computed size; the PNG Claude sees is scaled
            images.append(image)
    notes.extend(_blend_notes(g))
    return {"graph": _gid(g), "images": images, "notes": notes}


def cmd_run_python(args):
    if not ALLOW_PYTHON:
        raise PermissionError("run_python is disabled (SD_CLAUDE_BRIDGE_ALLOW_PYTHON=%s)" % ALLOW_PYTHON_SETTING)
    code = str(args.get("code") or "")
    buf = io.StringIO()
    ns = {
        "__name__": "__claude__",
        "sd": sd,
        "app": _app(),
        "ui": _ui(),
        "pkg_mgr": _pm(),
        "graph": _try(lambda: _ui().getCurrentGraph()),
        "SDPropertyCategory": SDPropertyCategory,
        "result": None,
    }
    err = None
    with _undo("run_python"):
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                exec(compile(code, "<claude>", "exec"), ns)
            except BaseException:
                # Includes SystemExit and KeyboardInterrupt, so the captured output still comes back.
                err = traceback.format_exc()
    out = {"stdout": _tail(buf.getvalue())}
    if err:
        out["error"] = _tail(err, 8000)
    else:
        out["result"] = _js(ns.get("result"))
    return out


COMMANDS = {
    "ping": cmd_ping,
    "info": cmd_info,
    "list_packages": cmd_list_packages,
    "get_graph": cmd_get_graph,
    "get_node": cmd_get_node,
    "get_selection": cmd_get_selection,
    "list_node_definitions": cmd_list_node_definitions,
    "search_library": cmd_search_library,
    "create_node": cmd_create_node,
    "create_library_node": cmd_create_library_node,
    "create_output": cmd_create_output,
    "connect": cmd_connect,
    "disconnect": cmd_disconnect,
    "set_parameter": cmd_set_parameter,
    "move_nodes": cmd_move_nodes,
    "delete_nodes": cmd_delete_nodes,
    "create_graph": cmd_create_graph,
    "save_package": cmd_save_package,
    "render": cmd_render,
    "run_python": cmd_run_python,
}


def dispatch(cmd, args):
    fn = COMMANDS.get(cmd)
    if fn is None:
        raise ValueError("unknown command %r" % (cmd,))
    if not isinstance(args, dict):
        raise TypeError("args must be an object")
    return fn(args)
