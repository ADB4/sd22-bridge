"""sdkit: Designer-side build helpers for the sd-material-research skill. Run inside Designer through run_python.

    import sys, importlib
    K = "/Users/<you>/.claude/skills/sd-material-research/scripts"
    if K not in sys.path: sys.path.insert(0, K)
    import sdkit as sk; importlib.reload(sk)
    sk.configure("<tools folder>")              # registry.json and dump/ live there
    sk.use("concrete.sbs::concrete_core")       # "<package file>::<graph id>" or a bare graph id

- Nodes get short names ("tg", "ff_rg3", "dmg_rake"), mapped to node uids per graph.
- The map lives on the sd module (it survives importlib.reload). save_registry() writes it to <tools>/registry.json.
  Uids are stored in the .sbs, so the map stays valid across sessions.
- Designer is single-threaded: one run_python at a time. Keep each call under ~45 s. The MCP client gives up at ~60 s
  while Designer keeps working, so never retry a call that timed out. For long jobs use scripts/sdcall.py from a shell.
"""
import contextlib
import json
import os
import re
import time
import zlib
import importlib

import sd
import sd_claude_bridge.commands as C
from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod
from sd.api.sdvaluestring import SDValueString
from sd.api.sdvaluefloat import SDValueFloat
from sd.api.sdvaluebool import SDValueBool
from sd.api.sdvalueint import SDValueInt
from sd.api.sdvalueint2 import SDValueInt2
from sd.api.sdbasetypes import int2, float2, ColorRGBA

if not hasattr(sd, "_sdk"):
    sd._sdk = {"tools": None, "reg": {}, "graph": None, "sections": {}}
S = sd._sdk

PBR = [("basecolor", "baseColor"), ("normal", "normal"), ("roughness", "roughness"), ("metallic", "metallic"),
       ("height", "height"), ("ambientocclusion", "ambientOcclusion")]

# FX-map noises that stall the GL engine above these scales (Designer 12.4.1, measured in the brick build).
HEAVY = {"noise_gaussian_noise": 200, "noise_bnw_spots_3": 90, "noise_cells_4": 100}

BLEND_MODES = {"copy": "copy", "add": "add", "subtract": "substract", "substract": "substract",
               "multiply": "multiply", "addsub": "addsub", "max": "max", "min": "min", "divide": "divide"}


# ----------------------------------------------------------------------------- config, registry, handles

def configure(tools_dir, registry="registry.json", dump="dump"):
    """Point sdkit at a material's tools folder and load its registry (merged into memory)."""
    tools_dir = os.path.abspath(os.path.expanduser(tools_dir))
    os.makedirs(tools_dir, exist_ok=True)
    S["tools"] = tools_dir
    S["registry_path"] = os.path.join(tools_dir, registry)
    S["dump"] = os.path.join(tools_dir, dump)
    if os.path.isfile(S["registry_path"]):
        with open(S["registry_path"]) as fh:
            data = json.load(fh)
        for g, m in data.get("graphs", data).items():
            S["reg"].setdefault(g, {}).update(m)
        S["sections"].update(data.get("sections", {}))
    return {"tools": tools_dir, "graphs": {g: len(m) for g, m in S["reg"].items()}}


def save_registry():
    """Write the name -> uid maps to registry.json. Prunes deleted nodes; keeps graphs that aren't open."""
    out = {}
    for key, m in S["reg"].items():
        g = C._try(lambda: C._graph(key))
        if g is None:
            out[key] = dict(m)
            continue
        alive = {k: v for k, v in m.items() if C._try(lambda v=v: g.getNodeFromId(v)) is not None}
        S["reg"][key] = alive
        out[key] = alive
    data = {"graphs": out, "sections": S["sections"]}
    tmp = S["registry_path"] + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    os.replace(tmp, S["registry_path"])
    return {k: len(v) for k, v in out.items()}


def use(graph_key):
    """Select the graph later calls act on. Accepts "file.sbs::id", a full path "::id", or a bare id."""
    g = C._graph(graph_key)
    S["graph"] = graph_key
    S["reg"].setdefault(graph_key, {})
    S["sections"].setdefault(graph_key, {})
    return C._gid(g)


def graph(key=None):
    return C._graph(key or S["graph"])


def reg(key=None):
    return S["reg"].setdefault(key or S["graph"], {})


def uid(name):
    r = reg()
    if name not in r:
        raise KeyError("%r is not a registered node name in %s" % (name, S["graph"]))
    return r[name]


def node(name):
    n = C._try(lambda: graph().getNodeFromId(uid(name)))
    if n is None:
        raise LookupError("node %r (uid %s) no longer exists in %s" % (name, uid(name), S["graph"]))
    return n


def names():
    return sorted(reg())


def _register(name, nid, replace):
    r = reg()
    if name in r and not replace:
        old = C._try(lambda: graph().getNodeFromId(r[name]))
        if old is not None:
            raise ValueError("name %r is already used in %s; pass replace=True or delete() it first" % (name, S["graph"]))
    if name in r and replace:
        old = C._try(lambda: graph().getNodeFromId(r[name]))
        if old is not None:
            graph().deleteNode(old)
    r[name] = nid
    sec = S.get("_section")
    if sec:
        S["sections"].setdefault(S["graph"], {})[name] = sec


@contextlib.contextmanager
def section(title, rgba=(0.45, 0.45, 0.45, 0.25)):
    """Nodes created inside `with section(...)` are framed together by layout()."""
    S.setdefault("section_colors", {})[title] = list(rgba)
    prev = S.get("_section")
    S["_section"] = title
    try:
        yield
    finally:
        S["_section"] = prev


# ----------------------------------------------------------------------------- packages and graphs

def app():
    return sd.getContext().getSDApplication()


def lib_dir():
    from sd.api.sdapplication import SDApplicationPath
    return os.path.join(app().getPath(SDApplicationPath.DefaultResourcesDir), "packages")


def find_lib(package):
    """Graphs inside a library package (instant, unlike search_library): [{"id", "label", "hidden"}]."""
    path = package if package.endswith(".sbs") else os.path.join(lib_dir(), package + ".sbs")
    return [{"id": g["id"], "label": g["label"], "hidden": g["hidden"]} for g in C._library_graphs(path)]


def open_package(path):
    pm = app().getPackageMgr()
    path = os.path.abspath(os.path.expanduser(path))
    return C._find_loaded_package(path) or pm.loadUserPackage(path)


def new_package(path):
    """Create and save an empty package (refuses to overwrite an existing file)."""
    path = os.path.abspath(os.path.expanduser(path))
    if os.path.exists(path):
        raise FileExistsError(path)
    pm = app().getPackageMgr()
    pkg = pm.newUserPackage()
    pm.savePackageAs(pkg, path)
    return pkg


def save(key=None):
    """Save the package of the current (or given) graph to its own path."""
    g = graph(key)
    pkg = g.getPackage()
    path = pkg.getFilePath()
    if not path:
        raise RuntimeError("package was never saved; use new_package(path) first")
    app().getPackageMgr().savePackageAs(pkg, path)
    return path


def snapshot(tag=None, key=None):
    """Save a copy of the package next to it (<name>.<tag>.sbs) as a checkpoint; Ctrl+Z is unreliable for big scripts."""
    pkg = graph(key).getPackage()
    path = pkg.getFilePath()
    stem = os.path.splitext(path)[0]
    out = "%s.%s.sbs" % (stem, tag or time.strftime("%H%M%S"))
    app().getPackageMgr().saveCopyOfPackageAs(pkg, out)
    return out


def new_graph(ident, package_path, size_log2=11, relative=False, fmt="16_bits_per_channel"):
    """Create a graph in an open package, with a 16-bit format and an absolute (or parent-relative) size."""
    C.cmd_create_graph({"identifier": ident, "package_path": os.path.abspath(os.path.expanduser(package_path))})
    key = os.path.basename(package_path) + "::" + ident
    C.cmd_set_parameter({"graph": key, "node": "graph", "property": "$format", "value": fmt})
    set_size(None if relative else size_log2, key)
    use(key)
    return key


def set_size(size_log2=None, key=None):
    """Absolute [n, n] (log2: 11 = 2048), or None for RelativeToParent [0, 0] (a core graph driven by wrappers)."""
    g = graph(key)
    p = g.getPropertyFromId("$outputsize", SDPropertyCategory.Input)
    if size_log2 is None:
        g.setPropertyInheritanceMethod(p, SDPropertyInheritanceMethod.RelativeToParent)
        g.setPropertyValue(p, SDValueInt2.sNew(int2(0, 0)))
    else:
        g.setPropertyInheritanceMethod(p, SDPropertyInheritanceMethod.Absolute)
        g.setPropertyValue(p, SDValueInt2.sNew(int2(int(size_log2), int(size_log2))))


@contextlib.contextmanager
def temp_size(g, size_log2):
    """Temporarily force a graph's output size; restores inheritance and value afterwards."""
    if size_log2 is None:
        yield
        return
    p = g.getPropertyFromId("$outputsize", SDPropertyCategory.Input)
    old_m = g.getPropertyInheritanceMethod(p)
    old_v = g.getPropertyValue(p)
    g.setPropertyInheritanceMethod(p, SDPropertyInheritanceMethod.Absolute)
    g.setPropertyValue(p, SDValueInt2.sNew(int2(int(size_log2), int(size_log2))))
    try:
        yield
    finally:
        g.setPropertyInheritanceMethod(p, old_m)
        if old_v is not None:
            g.setPropertyValue(p, old_v)


def set_meta(label=None, description=None, category=None, author=None, key=None):
    g = graph(key)
    for k, v in (("label", label), ("description", description), ("category", category), ("author", author)):
        if v:
            g.setAnnotationPropertyValueFromId(k, SDValueString.sNew(v))


# ----------------------------------------------------------------------------- nodes

def _auto_seed(name):
    return zlib.crc32(name.encode()) % 997 + 1


def lib(name, package, graph_id=None, x=None, y=None, seed=None, replace=False, **params):
    """Instance a library graph: package is a bare name ("noise_perlin_noise") or a .sbs path.
    seed="auto" gives a stable per-name seed that stays relative to the graph seed."""
    path = package if package.endswith(".sbs") else os.path.join(lib_dir(), package + ".sbs")
    base = os.path.splitext(os.path.basename(path))[0]
    lim = HEAVY.get(base)
    sc = params.get("scale")
    if lim is not None and isinstance(sc, (int, float)) and sc > lim:
        raise ValueError("%s at scale %s stalls Designer's GL engine for minutes; use fractal_sum_base_2 levels "
                         "(level ~ log2(tile_mm / feature_mm)) or keep scale <= %s" % (base, sc, lim))
    d = C.cmd_create_library_node({"graph": S["graph"], "package_path": path, "graph_identifier": graph_id,
                                   "x": 0 if x is None else x, "y": 0 if y is None else y})
    _register(name, d["id"], replace)
    if seed is not None:
        set_seed(name, _auto_seed(name) if seed == "auto" else seed)
    if params:
        P(name, params)
    return d


def atom(name, definition, x=None, y=None, replace=False, **params):
    """Atomic node: "blend", "levels", "hsl", "uniform", "gradient", "warp", "transformation", "distance", ..."""
    d = C.cmd_create_node({"graph": S["graph"], "definition": definition,
                           "x": 0 if x is None else x, "y": 0 if y is None else y})
    _register(name, d["id"], replace)
    if params:
        P(name, params)
    return d


def output(name, ident, src=None, src_port=None, usage=None, label=None, group=None, replace=False):
    """Output node; masks and IDs get no usage (engines ignore them) but a stable identifier for checks.json."""
    d = C.cmd_create_output({"graph": S["graph"], "identifier": ident, "usage": usage, "x": 0, "y": 0,
                             "label": label or ident})
    _register(name, d["id"], replace)
    if group:
        C._try(lambda: node(name).setAnnotationPropertyValueFromId("group", SDValueString.sNew(group)))
    if src:
        wire(src, name, "inputNodeOutput", src_port)
    return d


def _prop(n, pid):
    p = n.getPropertyFromId(pid, SDPropertyCategory.Input)
    if p is None:
        raise KeyError("no parameter %r; parameters: %s" % (pid, sorted(C._params(n))))
    return p


def P(name, params):
    """Set parameters by id. '#rrggbb' works on colour (float4) parameters. Seeds: use set_seed()."""
    n = node(name)
    out = []
    for pid, v in params.items():
        if pid == "$randomseed":
            set_seed(name, v)
            out.append((pid, v))
            continue
        if pid.startswith("$"):
            raise ValueError("%s: set base parameters with set_seed()/set_size(); set_parameter would make them Absolute" % pid)
        p = _prop(n, pid)
        if isinstance(v, str) and v.startswith("#") and (C._try(p.getType().getId, "") or "").lower() in ("float4", "colorrgba"):
            v = C._color(v)
        r = C.cmd_set_parameter({"graph": S["graph"], "node": uid(name), "property": pid, "value": v})
        if r.get("note"):
            out.append((pid, r.get("value"), r["note"]))
        else:
            out.append((pid, r.get("value")))
    return out


def set_seed(name, s):
    """Set $randomseed while keeping its default inheritance (an offset from the graph seed), so a wrapper's seed still
    reseeds every node. Setting it through set_parameter would make it Absolute."""
    node(name).setInputPropertyValueFromId("$randomseed", SDValueInt.sNew(int(s)))


def wire(src, dst, port, out=None):
    """Connect src[out] -> dst[port], replacing whatever fed dst[port]."""
    disconnect(dst, port)
    return C.cmd_connect({"graph": S["graph"], "from_node": uid(src), "from_output": out,
                          "to_node": uid(dst), "to_input": port})


def disconnect(name, port):
    n = node(name)
    p = n.getPropertyFromId(port, SDPropertyCategory.Input)
    if p is not None:
        C._try(lambda: n.deletePropertyConnections(p))


def delete(*names_):
    g = graph()
    for nm in names_:
        n = C._try(lambda nm=nm: g.getNodeFromId(reg()[nm]))
        if n is not None:
            g.deleteNode(n)
        reg().pop(nm, None)


def source_of(name, port):
    """(name or uid, output port) feeding name[port], or None."""
    n = node(name)
    p = n.getPropertyFromId(port, SDPropertyCategory.Input)
    inv = {v: k for k, v in reg().items()}
    for c in C._items(C._try(lambda: n.getPropertyConnections(p))):
        far = C._far_end(c, (n.getIdentifier(), port))
        if far:
            return inv.get(far[0], far[0]), far[1]
    return None


def consumers(name):
    """[(consumer name or uid, input port, our output port)]."""
    inv = {v: k for k, v in reg().items()}
    return [(inv.get(t[2], t[2]), t[3], t[1]) for t in C._connections([node(name)])]


def move_consumers(old, new, new_out=None):
    """Re-point every consumer of old (except new itself) to new[new_out]. Use after inserting a node."""
    moved = []
    new_uid = uid(new)
    for t in C._connections([node(old)]):
        cuid, cport = t[2], t[3]
        if cuid == new_uid:
            continue
        C.cmd_disconnect({"graph": S["graph"], "node": cuid, "input": cport})
        C.cmd_connect({"graph": S["graph"], "from_node": new_uid, "from_output": new_out,
                       "to_node": cuid, "to_input": cport})
        moved.append((cuid, cport))
    return moved


def info(name, all_params=False):
    """Readable summary: ports, parameters (value, options), driven parameters."""
    d = C.cmd_get_node({"graph": S["graph"], "node": uid(name), "all_params": all_params})
    lines = ["%s [%s]" % (name, d.get("label") or d.get("definition"))]
    for k in ("inputs", "outputs"):
        v = d.get(k)
        if v:
            lines.append("  %s: %s" % (k, [x if isinstance(x, str) else x.get("id") for x in v]))
    n = node(name)
    for p in d.get("params") or []:
        extra = ""
        for key in ("options", "components", "value_labels"):
            if p.get(key):
                extra += " %s=%s" % (key, p[key])
        prop = n.getPropertyFromId(p.get("id"), SDPropertyCategory.Input)
        if prop is not None and C._try(lambda: n.getPropertyGraph(prop)) is not None:
            extra += " DRIVEN"
        lines.append("  %s (%s) [%s] = %s%s" % (p.get("id"), (p.get("label") or "").strip(), p.get("type"), p.get("value"), extra))
    return "\n".join(lines)


# ----------------------------------------------------------------------------- exposed inputs and function graphs

def _type(kind):
    m = {"float": ("sdtypefloat", "SDTypeFloat"), "float2": ("sdtypefloat2", "SDTypeFloat2"),
         "float4": ("sdtypefloat4", "SDTypeFloat4"), "color": ("sdtypecolorrgba", "SDTypeColorRGBA"),
         "bool": ("sdtypebool", "SDTypeBool"), "int": ("sdtypeint", "SDTypeInt")}[kind]
    return getattr(importlib.import_module("sd.api." + m[0]), m[1]).sNew()


def expose(ident, kind, default, label=None, group=None, desc=None, vmin=None, vmax=None, options=None, key=None):
    """Create or update a graph input. kind: float, float2, float4, color, bool, int.
    options=["DirectX", "OpenGL"] makes an int dropdown. Read it in nodes through drive(..., ("get", ident))."""
    g = graph(key)
    p = g.getPropertyFromId(ident, SDPropertyCategory.Input)
    if p is None:
        p = g.newProperty(ident, _type(kind), SDPropertyCategory.Input)
    if kind == "color" and isinstance(default, str):
        default = C._color(default)
    g.setPropertyValue(p, C._make_value(p.getType(), default))
    notes = []

    def ann(k, v):
        try:
            g.setPropertyAnnotationValueFromId(p, k, v)
        except C.ERRORS as e:
            notes.append("%s: %s" % (k, e))

    for k, v in (("label", label), ("group", group), ("description", desc)):
        if v:
            ann(k, SDValueString.sNew(v))
    num = (lambda v: SDValueInt.sNew(int(v))) if kind == "int" else (lambda v: SDValueFloat.sNew(float(v)))
    if options:
        vmin, vmax = 0, len(options) - 1
        ann("editor", SDValueString.sNew("dropdownlist"))
        for i, o in enumerate(options):
            ann("label_%d" % i, SDValueString.sNew(o))
    if kind == "color":
        ann("editor", SDValueString.sNew("color"))
    for k, v in (("min", vmin), ("max", vmax)):
        if v is not None:
            ann(k, num(v))
    return notes


def list_inputs(key=None):
    g = graph(key)
    rows = []
    for p in C._items(g.getProperties(SDPropertyCategory.Input)):
        pid = p.getId()
        if pid.startswith("$"):
            continue
        a = lambda k: C._js(C._try(lambda: g.getPropertyAnnotationValueFromId(p, k)))
        rows.append({"id": pid, "type": C._try(p.getType().getId), "value": C._js(C._try(lambda: g.getPropertyValue(p))),
                     "label": a("label"), "group": a("group"), "min": a("min"), "max": a("max")})
    return rows


_GET = {"float": "get_float1", "float2": "get_float2", "float4": "get_float4", "color": "get_float4",
        "bool": "get_bool", "int": "get_integer1"}


def _expand(spec):
    """Sugar: clamp, neg, mm (mm -> height units through the graph's height_depth_mm input)."""
    if isinstance(spec, tuple) and spec:
        op = spec[0]
        if op == "clamp":
            return ("min", ("max", spec[1], spec[2]), spec[3])
        if op == "neg":
            return ("sub", 0.0, spec[1])
        if op == "mm":
            return ("div", spec[1], ("get", spec[2] if len(spec) > 2 else "height_depth_mm"))
    return spec


def _fn_node(fg, spec, depth, row):
    spec = _expand(spec)
    if isinstance(spec, bool):
        n = fg.newNode("sbs::function::const_bool")
        n.setInputPropertyValueFromId("__constant__", SDValueBool.sNew(spec))
    elif isinstance(spec, (int, float)):
        n = fg.newNode("sbs::function::const_float1")
        n.setInputPropertyValueFromId("__constant__", SDValueFloat.sNew(float(spec)))
    elif spec[0] == "get":
        n = fg.newNode("sbs::function::" + _GET[spec[2] if len(spec) > 2 else "float"])
        n.setInputPropertyValueFromId("__constant__", SDValueString.sNew(spec[1]))
    elif spec[0] in _FN_EXTRA:
        n = _fn_extra(fg, spec, depth, row)
    else:
        op, args = spec[0], spec[1:]
        table = {"vec2": ("vector2", ["componentsin", "componentslast"]),
                 "vec3": ("vector3", ["componentsin", "componentslast"]),
                 "vec4": ("vector4", ["componentsin", "componentslast"]),
                 "lerp": ("lerp", ["a", "b", "x"])}
        defn, ports = table.get(op, (op, ["a", "b"]))
        if op in ("pow", "clamp"):
            raise ValueError("Designer 12.4.1 function graphs have no %s node; use min/max of lines" % op)
        n = fg.newNode("sbs::function::" + defn)
        if len(args) > len(ports):
            ports = [p.getId() for p in n.getProperties(SDPropertyCategory.Input) if p.isConnectable()]
        for port, a in zip(ports, args):
            _fn_node(fg, a, depth + 1, row).newPropertyConnectionFromId("unique_filter_output", n, port)
    row[0] += 1
    C._try(lambda: n.setPosition(float2(-170.0 * depth, 70.0 * row[0])))
    return n


_FN_EXTRA = ("int", "tofloat", "swz")


def _fn_extra(fg, spec, depth, row):
    """("int", n) an int constant, ("tofloat", x) int -> float, ("swz", vec, i) component i of a vector (from the
    asphalt build: int seeds, int dropdowns as floats, $pos components)."""
    if spec[0] == "int":
        n = fg.newNode("sbs::function::const_int1")
        n.setInputPropertyValueFromId("__constant__", SDValueInt.sNew(int(spec[1])))
    elif spec[0] == "tofloat":
        n = fg.newNode("sbs::function::tofloat")
        _fn_node(fg, spec[1], depth + 1, row).newPropertyConnectionFromId("unique_filter_output", n, "value")
    else:
        n = fg.newNode("sbs::function::swizzle1")
        n.setInputPropertyValueFromId("__constant__", SDValueInt.sNew(int(spec[2])))
        _fn_node(fg, spec[1], depth + 1, row).newPropertyConnectionFromId("unique_filter_output", n, "vector")
    return n


def drive(name, pid, spec):
    """Drive a parameter with a function graph. spec: numbers, ("get", input_id[, kind]), ("add"|"sub"|"mul"|"div"|
    "min"|"max", a, b), ("lerp", a, b, x), ("vec2", a, b), ("clamp", x, lo, hi), ("neg", a), ("mm", mm_spec)."""
    n = node(name)
    p = _prop(n, pid)
    if n.getPropertyGraph(p) is not None:
        n.deletePropertyGraph(p)
    fg = n.newPropertyGraph(p, "SDSBSFunctionGraph")
    fg.setOutputNode(_fn_node(fg, spec, 0, [0]), True)
    return pid


def undrive(name, pid):
    n = node(name)
    p = _prop(n, pid)
    if n.getPropertyGraph(p) is not None:
        n.deletePropertyGraph(p)


def _value(name, pid, spec):
    """Set a constant or drive a function, whichever spec is."""
    if isinstance(spec, tuple):
        drive(name, pid, spec)
    else:
        P(name, {pid: spec})


# ----------------------------------------------------------------------------- recipes (see references/sd_craft.md)

def blend(name, mode, src, dst, opacity=None, mult=None, src_out=None, dst_out=None, opa_out=None):
    """Blend src over dst. mode: copy (lerp by opacity), add, subtract, multiply, addsub (dst + 2*(src-0.5)), max, min,
    divide (dst / src). mult may be a number or a function spec."""
    atom(name, "blend")
    P(name, {"blendingmode": BLEND_MODES[mode]})
    wire(src, name, "source", src_out)
    wire(dst, name, "destination", dst_out)
    if opacity:
        wire(opacity, name, "opacity", opa_out)
    if mult is not None:
        _value(name, "opacitymult", mult)
    return name


def levels(name, inp, in_lo=0.0, in_hi=1.0, out_lo=0.0, out_hi=1.0, mid=0.5, inp_out=None):
    atom(name, "levels")
    P(name, {"levelinlow": [in_lo] * 4, "levelinhigh": [in_hi] * 4, "leveloutlow": [out_lo] * 4,
             "levelouthigh": [out_hi] * 4, "levelinmid": [mid] * 4})
    wire(inp, name, "input1", inp_out)
    return name


def hscan(name, inp, position, contrast=1.0, inp_out=None):
    """Histogram Scan: threshold centre = 1 - Position (a higher Position gives MORE white). Calibrate Position from
    measured quantiles of the input (scripts/calibrate.py), never by intuition."""
    lib(name, "histogram_scan")
    wire(inp, name, "Input_1", inp_out)
    _value(name, "Position", position)
    P(name, {"Contrast": contrast})
    return name


def blur(name, inp, intensity, color=False, inp_out=None):
    """Blur HQ. Half-ramp ~11-12 px per unit of Intensity at 2048 (default Intensity is 10: always set it)."""
    lib(name, "blur_hq", "blur_hq" if color else "blur_hq_grayscale")
    wire(inp, name, "Source", inp_out)
    _value(name, "Intensity", intensity)
    return name


def nblur(prefix, inp, mask, intensity, inp_out=None, mask_out=None):
    """Edge-correct blur inside a footprint: blur(D*m) / blur(m). Apply the hard mask afterwards, never before."""
    blend(prefix + "_m", "multiply", mask, inp, src_out=mask_out, dst_out=inp_out)
    blur(prefix + "_b", prefix + "_m", intensity)
    blur(prefix + "_w", mask, intensity, inp_out=mask_out)
    blend(prefix, "divide", prefix + "_w", prefix + "_b", src_out="Blur_HQ", dst_out="Blur_HQ")
    return prefix


def gconst(name, value):
    """A grayscale constant from a number or function spec (Blend copy of white over black, opacitymult = value)."""
    for nm, col in (("__white", 1.0), ("__black", 0.0)):
        if nm not in reg():
            atom(nm, "uniform", colorswitch=False)
            C._try(lambda nm=nm, col=col: P(nm, {"outputcolor": [col, col, col, 1.0]}))
    return blend(name, "copy", "__white", "__black", mult=value)


def flood_random(name, ff, seed="auto", kind="grayscale", ff_out="output"):
    """One random value per unit from a Flood Fill. Use ONE per visual feature: shared randoms make hero units."""
    graph_id = {"grayscale": "flood_fill_to_random_grayscale", "color": "flood_fill_to_random_color",
                "gradient": "flood_fill_to_gradient_2", "bbox": "flood_fill_to_bbox_size"}[kind]
    lib(name, "flood_fill_2", graph_id, seed=seed)
    wire(ff, name, "input", ff_out)
    return name


def fractal(name, min_level, max_level, roughness=0.6, seed="auto"):
    """Fractal Sum Base: cell size = tile_mm / 2**level. The safe fine noise (FX-map noises stall at high scale)."""
    lib(name, "noise_fractal_sum_base", "fractal_sum_base_2", seed=seed,
        MinLevel=int(min_level), MaxLevel=int(max_level), Roughness=float(roughness))
    return name


def level_for(tile_mm, feature_mm):
    """Fractal Sum Base level whose cells are about feature_mm wide on a tile_mm tile."""
    import math
    return int(round(math.log2(tile_mm / float(feature_mm))))


# ----------------------------------------------------------------------------- more recipes (from the asphalt build)

def _add(a, b):
    """a + b: a number when both are numbers, else a function spec."""
    return a + b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else ("add", a, b)


def _sub(a, b):
    return a - b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else ("sub", a, b)


def _v4(a):
    return ("vec4", ("vec3", ("vec2", a, a), a), a)


def pos_coord(name, axis=0):
    """Exact pixel-centre coordinate (i + 0.5) / N along x (axis 0) or y (axis 1): a grayscale Pixel Processor reading
    $pos. Gradient Linear 1 is a 256-px ramp upsampled with clamped edges (0.5/256 .. 1 - 0.5/256 within 4 px of the
    border at 2048), so anything built from it steps at the wrap (asphalt: a line in the normal at U = 0)."""
    atom(name, "pixelprocessor", colorswitch=False)
    drive(name, "perpixel", ("swz", ("get", "$pos", "float2"), int(axis)))
    return name


def levels_fn(name, inp, in_lo=0.0, in_hi=1.0, out_lo=0.0, out_hi=1.0, mid=0.5, inp_out=None):
    """levels() whose points may also be function specs (a spec drives that float4)."""
    num = lambda v, d: v if isinstance(v, (int, float)) else d
    levels(name, inp, num(in_lo, 0.0), num(in_hi, 1.0), num(out_lo, 0.0), num(out_hi, 1.0), num(mid, 0.5), inp_out)
    for pid, v in (("levelinlow", in_lo), ("levelinhigh", in_hi), ("leveloutlow", out_lo), ("levelouthigh", out_hi),
                   ("levelinmid", mid)):
        if isinstance(v, tuple):
            drive(name, pid, _v4(v))
    return name


def band(name, src, lo, hi, soft_lo=None, soft_hi=None, res=2048, inp_out=None):
    """1 where lo <= src <= hi (coordinate units, numbers or specs), with 1-px AA edges at res px per tile or linear
    ramps soft_lo / soft_hi wide outside. min() of a rising and a falling Levels: name_r, name_f, name."""
    hp = 0.5 / res
    a = (_sub(lo, soft_lo), lo) if soft_lo else (_sub(lo, hp), _add(lo, hp))
    b = (hi, _add(hi, soft_hi)) if soft_hi else (_sub(hi, hp), _add(hi, hp))
    levels_fn(name + "_r", src, a[0], a[1], inp_out=inp_out)
    levels_fn(name + "_f", src, b[0], b[1], 1.0, 0.0, inp_out=inp_out)
    return blend(name, "min", name + "_r", name + "_f")


def tri(name, src, centre, half, inp_out=None):
    """Triangle profile: 1 at src == centre, 0 at |src - centre| >= half (numbers or specs)."""
    levels_fn(name + "_r", src, _sub(centre, half), centre, inp_out=inp_out)
    levels_fn(name + "_f", src, centre, _add(centre, half), 1.0, 0.0, inp_out=inp_out)
    return blend(name, "min", name + "_r", name + "_f")


def piecewise(x, pts):
    """Piecewise-linear f(x) through [(x0, y0), (x1, y1), ...] (x_i rising, flat beyond the ends), written as
    y0 + sum k_i * clamp(x - x_i, 0, dx_i): a function spec, or a float when x is a number (same table, both sides)."""
    if any(b[0] <= a[0] for a, b in zip(pts[:-1], pts[1:])):
        raise ValueError("piecewise needs strictly rising x, got %s" % [p[0] for p in pts])
    if isinstance(x, (int, float)):
        y = float(pts[0][1])
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            y += (y1 - y0) / (x1 - x0) * min(max(x - x0, 0.0), x1 - x0)
        return y
    expr = float(pts[0][1])
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        k = (y1 - y0) / (x1 - x0)
        expr = ("add", expr, ("mul", k, ("clamp", ("sub", x, float(x0)), 0.0, float(x1 - x0))))
    return expr


def seeded(name, ident, k=0):
    """Drive name's $randomseed from the int graph input ident (+ k), so one input re-rolls a whole set of nodes."""
    drive(name, "$randomseed", ("add", ("get", ident, "int"), ("int", k)))
    return name


def gmap(name, gray, keys, gray_out=None):
    """Gradient Map: grayscale -> colour through keys [[pos, "#rrggbb"], ...]."""
    atom(name, "gradient")
    wire(gray, name, "input1", gray_out)
    P(name, {"gradientrgba": keys})
    return name


def to_color(name, gray, gray_out=None):
    """Grayscale -> colour, black..white, so a colour Blend can take it as source (it skips a grayscale one)."""
    return gmap(name, gray, [[0.0, "#000000"], [1.0, "#ffffff"]], gray_out)


def flat(name, hexcol):
    """Flat colour (Uniform Color in colour mode)."""
    atom(name, "uniform", colorswitch=True)
    P(name, {"outputcolor": hexcol})
    return name


def ensure_output(ident, src, group=None, usage=None, src_port=None, label=None, prefix="o_"):
    """Output <prefix><ident>: created on the first run, only re-wired to src afterwards, so a re-run stage script keeps
    the Output node (and whatever links to it)."""
    name = prefix + ident
    if name in reg():
        try:
            node(name)
            wire(src, name, "inputNodeOutput", src_port)
            return name
        except LookupError:
            reg().pop(name, None)
    output(name, ident, src=src, src_port=src_port, usage=usage, label=label, group=group)
    return name


def reset(*prefixes):
    """Delete the registered nodes whose names start with one of prefixes (a stage's own), so the stage script can be
    re-run from scratch. Returns how many went."""
    if "" in prefixes:
        raise ValueError("an empty prefix would delete every registered node")
    gone = [n for n in list(reg()) if n.startswith(prefixes)]
    delete(*gone)
    return len(gone)


# ----------------------------------------------------------------------------- probing and export

def _tex(n, port):
    p = n.getPropertyFromId(port, SDPropertyCategory.Output)
    v = n.getPropertyValue(p)
    return v.get() if v is not None else None


def probe(names_, port=None, out_dir=None, tag="", size=None):
    """Compute the graph with temporary outputs on the named nodes; save each texture (native size and depth)."""
    if isinstance(names_, str):
        names_ = [names_]
    out_dir = out_dir or S["dump"]
    os.makedirs(out_dir, exist_ok=True)
    g = graph()
    temps, rows = [], []
    for nm in names_:
        src = node(nm)
        o = g.newNode("sbs::compositing::output")
        o.setAnnotationPropertyValueFromId("identifier", SDValueString.sNew("__sdk_probe_" + nm))
        pt = port or [p.getId() for p in src.getProperties(SDPropertyCategory.Output) if p.isConnectable()][0]
        src.newPropertyConnectionFromId(pt, o, "inputNodeOutput")
        temps.append((nm, src, pt, o))
    try:
        t0 = time.time()
        with temp_size(g, size):
            g.compute()
            for nm, src, pt, o in temps:
                tex = _tex(src, pt)
                path = os.path.join(out_dir, "%s%s.png" % (nm, tag))
                tex.save(path)
                sz = tex.getSize()
                rows.append({"name": nm, "path": path, "size": [sz.x, sz.y], "format": str(tex.getPixelFormat())})
        secs = round(time.time() - t0, 2)
    finally:
        for _, _, _, o in temps:
            g.deleteNode(o)
    for r in rows:
        r["seconds"] = secs
        if "8" in r["format"] and "16" not in r["format"]:
            r["warning"] = "8-bit texture: set the graph $format to 16_bits_per_channel"
    return rows


def _usage(o):
    v = C._try(lambda: o.getAnnotationPropertyValueFromId("usages"))
    return C._js(v) if v is not None else None


def export_outputs(key=None, out_dir=None, prefix=None, size=None, only=None, note=None):
    """Compute a graph and save every Output to <out_dir>/<prefix><identifier>.png plus <prefix>manifest.json.
    Read-only on the graph (size is restored). This is the measurement contract with matcheck.py."""
    g = graph(key)
    gid = C._gid(g)
    prefix = gid + "_" if prefix is None else prefix
    out_dir = out_dir or S["dump"]
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    t0 = time.time()
    with temp_size(g, size):
        g.compute()
        tc = time.time() - t0
        for o in g.getOutputNodes():
            ident = C._js(o.getAnnotationPropertyValueFromId("identifier"))
            if only and ident not in only:
                continue
            prop = [p for p in o.getProperties(SDPropertyCategory.Output)][0]
            v = o.getPropertyValue(prop)
            tex = v.get() if v is not None else None
            if tex is None:
                continue
            path = os.path.join(out_dir, prefix + ident + ".png")
            tex.save(path)
            sz = tex.getSize()
            rows.append({"output": ident, "path": path, "size": [sz.x, sz.y], "format": str(tex.getPixelFormat()),
                         "usage": _usage(o)})
    inst = {}
    for n in C._items(g.getNodes()):
        if C._try(n.getReferencedResource) is not None:
            ref = n.getReferencedResource()
            if C._try(lambda: os.path.dirname(ref.getPackage().getFilePath())) != lib_dir():
                inst[n.getIdentifier()] = {"of": C._gid(ref), "params": get_params(n)}
    manifest = {"graph": gid, "package": C._try(g.getPackage().getFilePath), "prefix": prefix, "out_dir": out_dir,
                "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "compute_s": round(tc, 2),
                "total_s": round(time.time() - t0, 2), "outputs": rows, "instances": inst,
                "graph_params": C._js(C._try(lambda: C._graph_params(g))), "note": note}
    with open(os.path.join(out_dir, prefix + "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1, default=str)
    eight = [r["output"] for r in rows if r["output"] in ("height", "normal") and "16" not in r["format"]]
    if eight:
        manifest["warning"] = "8-bit %s: set the graph $format to 16_bits_per_channel" % eight
    return manifest


# ----------------------------------------------------------------------------- variants

def instance(core_id, key=None):
    """The instance node of graph core_id inside a wrapper graph, found by reference (not by registry)."""
    for n in C._items(graph(key).getNodes()):
        r = C._try(n.getReferencedResource)
        if r is not None and C._gid(r) == core_id:
            return n
    return None


def get_params(n):
    out = {}
    for p in C._items(n.getProperties(SDPropertyCategory.Input)):
        if C._try(p.isConnectable, False):
            continue
        out[p.getId()] = C._js(C._try(lambda: C._param_value(n, p)))
    return out


def _set_on(n, key, pid, v):
    p = n.getPropertyFromId(pid, SDPropertyCategory.Input)
    if p is None:
        raise KeyError("instance has no parameter %r" % pid)
    if isinstance(v, str) and v.startswith("#"):
        v = C._color(v)
    C.cmd_set_parameter({"graph": key, "node": n.getIdentifier(), "property": pid, "value": v})


def make_variant(core_key, variant_id, preset, outputs=None, size_log2=11):
    """Create or update a wrapper graph that instances the core with a preset (one source of truth: re-run to update).
    outputs: [(identifier, usage or None[, label])]; defaults to PBR. preset may hold "seed"."""
    core = C._graph(core_key)
    pkg = core.getPackage()
    pkg_file = os.path.basename(pkg.getFilePath())
    key = pkg_file + "::" + variant_id
    existing = {C._gid(r) for r in C._graphs_in(pkg)}
    if variant_id not in existing:
        from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph
        w = SDSBSCompGraph.sNew(pkg)
        w.setIdentifier(variant_id)
    use(key)
    set_size(size_log2, key)
    w = graph()
    inst = instance(C._gid(core), key)
    if inst is None:
        inst = w.newInstanceNode(core)
        C._set_pos(inst, [0, 0])
    reg()["core"] = inst.getIdentifier()
    params = dict(preset)
    seed = params.pop("seed", None)
    if seed is not None:
        C.cmd_set_parameter({"graph": key, "node": inst.getIdentifier(), "property": "$randomseed", "value": int(seed)})
    for pid, v in params.items():
        _set_on(inst, key, pid, v)
    have = {C._js(o.getAnnotationPropertyValueFromId("identifier")) for o in w.getOutputNodes()}
    for i, spec in enumerate(outputs or PBR):
        ident, usage = spec[0], spec[1]
        if ident in have:
            continue
        d = C.cmd_create_output({"graph": key, "identifier": ident, "usage": usage, "x": 320, "y": -320 + i * 130,
                                 "label": spec[2] if len(spec) > 2 else ident})
        reg()["o_" + ident] = d["id"]
        C.cmd_connect({"graph": key, "from_node": inst.getIdentifier(), "from_output": ident,
                       "to_node": d["id"], "to_input": "inputNodeOutput"})
    return key


def render_variant(key, overrides, prefix, out_dir=None, size=None, only=None, instance_of=None):
    """Export with temporary parameter overrides on the wrapper's core instance (or on the graph's own inputs when
    instance_of is None and the graph has no instance); always restores the old values."""
    g = graph(key)
    target = None
    if instance_of:
        target = instance(instance_of, key)
    else:
        nodes = [n for n in C._items(g.getNodes()) if C._try(n.getReferencedResource) is not None
                 and C._try(lambda n=n: os.path.dirname(n.getReferencedResource().getPackage().getFilePath())) != lib_dir()]
        target = nodes[0] if len(nodes) == 1 else None
    owner = target if target is not None else g
    saved = []
    try:
        for pid, v in overrides.items():
            p = owner.getPropertyFromId(pid, SDPropertyCategory.Input)
            if p is None:
                raise KeyError("no parameter %r on %s" % (pid, "instance" if target else "graph"))
            if target is not None and target.getPropertyGraph(p) is not None:
                raise RuntimeError("%s is function-driven on the instance; an override would have no effect" % pid)
            saved.append((p, owner.getPropertyValue(p)))
            if isinstance(v, str) and v.startswith("#"):
                v = C._color(v)
            owner.setPropertyValue(p, C._make_value(p.getType(), v))
        return export_outputs(key, out_dir, prefix, size, only, note={"overrides": overrides})
    finally:
        for p, old in reversed(saved):
            owner.setPropertyValue(p, old)


def nowear(key, wear_params, prefix=None, **kw):
    """Export the as-built reference: same graph and seeds with every wear/damage/deposit parameter at its 'off' value.
    wear_params: list of ids (set to 0) or {id: off_value}. Compare with mask_invariance / envelope checks."""
    ov = wear_params if isinstance(wear_params, dict) else {p: 0.0 for p in wear_params}
    return render_variant(key, ov, prefix or C._gid(graph(key)) + "_nowear_", **kw)


# ----------------------------------------------------------------------------- hygiene

def _upstream(g):
    nodes = {n.getIdentifier(): n for n in C._items(g.getNodes())}
    up = {nid: set() for nid in nodes}
    for nid, n in nodes.items():
        for p in C._items(n.getProperties(SDPropertyCategory.Input)):
            for c in C._items(C._try(lambda: n.getPropertyConnections(p))):
                far = C._far_end(c, (nid, p.getId()))
                if far and far[0] in nodes:
                    up[nid].add(far[0])
    return nodes, up


def prune_dead(dry_run=True):
    """Nodes that feed no Output (Designer never computes them). Deletes them unless dry_run."""
    g = graph()
    nodes, up = _upstream(g)
    keep, stack = set(), [o.getIdentifier() for o in C._items(g.getOutputNodes())]
    while stack:
        n = stack.pop()
        if n not in keep:
            keep.add(n)
            stack.extend(up.get(n, ()))
    inv = {v: k for k, v in reg().items()}
    dead = [nid for nid in nodes if nid not in keep]
    if not dry_run:
        for nid in dead:
            g.deleteNode(nodes[nid])
            if nid in inv:
                reg().pop(inv[nid], None)
    return [inv.get(n, n) for n in dead]


def layout(dx=190.0, dy=125.0, pad=90.0, frame_tag="sdkit"):
    """Layered layout: x = longest path from sources, one horizontal band (and frame) per section().
    Only frames sdkit made (description == frame_tag) are replaced."""
    from sd.api.sdgraphobjectframe import SDGraphObjectFrame
    g = graph()
    nodes, up = _upstream(g)
    inv = {v: k for k, v in reg().items()}
    secs = S["sections"].get(S["graph"], {})
    depth = {}

    def d(nid, stack=()):
        if nid in depth:
            return depth[nid]
        if nid in stack:
            return 0
        v = 0 if not up[nid] else 1 + max(d(u, stack + (nid,)) for u in up[nid])
        depth[nid] = v
        return v

    for nid in nodes:
        d(nid)
    maxd = max(depth.values()) if depth else 0
    outs = {o.getIdentifier() for o in C._items(g.getOutputNodes())}
    order, members = [], {}
    for nid in nodes:
        title = "Outputs" if nid in outs else secs.get(inv.get(nid, ""), "Unsorted")
        if nid in outs:
            depth[nid] = maxd + 1
        if title not in members:
            members[title] = []
            order.append(title)
        members[title].append(nid)
    order = [t for t in order if t not in ("Unsorted", "Outputs")] + [t for t in ("Unsorted", "Outputs") if t in members]
    for o in C._items(C._try(g.getGraphObjects)):
        if "Frame" in C._cls(o) and C._try(o.getDescription) == frame_tag:
            g.deleteGraphObject(o)
    y0 = 0.0
    for title in order:
        ids = members[title]
        by = {}
        for nid in sorted(ids, key=lambda k: (depth[k], inv.get(k, k))):
            by.setdefault(depth[nid], []).append(nid)
        rows = max(len(v) for v in by.values())
        for layer, lst in by.items():
            for i, nid in enumerate(lst):
                nodes[nid].setPosition(float2(layer * dx, y0 + pad + i * dy))
        xs = [depth[n] * dx for n in ids]
        f = SDGraphObjectFrame.sNew(g)
        f.setTitle(title)
        f.setDescription(frame_tag)
        f.setPosition(float2(min(xs) - 80, y0))
        f.setSize(float2(max(xs) - min(xs) + 240, rows * dy + pad + 20))
        col = S.get("section_colors", {}).get(title, (0.3, 0.3, 0.3, 0.25))
        f.setColor(ColorRGBA(*col))
        y0 += rows * dy + pad + 120
    return {"nodes": len(nodes), "depth": maxd, "frames": len(order)}


def lint():
    """Cheap static checks: heavy noises, 8-bit format, unnamed nodes, outputs without identifier, Blend kind mismatches
    (needs a previous compute)."""
    g = graph()
    msgs = []
    for n in C._items(g.getNodes()):
        r = C._try(n.getReferencedResource)
        if r is None:
            continue
        base = os.path.splitext(os.path.basename(C._try(lambda: r.getPackage().getFilePath(), "") or ""))[0]
        lim = HEAVY.get(base)
        if lim is not None:
            p = n.getPropertyFromId("scale", SDPropertyCategory.Input)
            v = C._try(lambda: n.getPropertyValue(p).get()) if p is not None else None
            if isinstance(v, (int, float)) and v > lim:
                msgs.append("heavy noise %s at scale %s (> %s) on node %s" % (base, v, lim, n.getIdentifier()))
    fmt = C._try(lambda: C._param_value(g, g.getPropertyFromId("$format", SDPropertyCategory.Input)))
    if fmt is not None and str(fmt).startswith("8"):
        msgs.append("graph $format is %s: set 16_bits_per_channel for height work" % fmt)
    inv = set(reg().values())
    unnamed = [n.getIdentifier() for n in C._items(g.getNodes()) if n.getIdentifier() not in inv]
    if unnamed:
        msgs.append("%d nodes without a registry name" % len(unnamed))
    for o in C._items(g.getOutputNodes()):
        if not C._js(C._try(lambda: o.getAnnotationPropertyValueFromId("identifier"))):
            msgs.append("output node %s without identifier" % o.getIdentifier())
    notes = C._try(lambda: C._blend_notes(g))
    if notes:
        msgs.extend(notes if isinstance(notes, list) else [str(notes)])
    return msgs


def status():
    pm = app().getPackageMgr()
    pk = [{"file": C._try(p.getFilePath), "modified": C._try(p.isModified)} for p in C._items(pm.getUserPackages())]
    return {"tools": S["tools"], "graph": S["graph"], "registered": {k: len(v) for k, v in S["reg"].items()}, "packages": pk}
