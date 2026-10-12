#!/usr/bin/env python3
"""Check the numbers a spec states against each other and against the checks configs, at stage 3 while the user is
still there (R-16). This docstring is the reference.

Why: in the M8 concrete run most round-1 design calls repaired spec ambiguities, not builds: per-panel paste keys on a
2 x 2 panel tile printed a checker, a fixed cracked-panel table repeated every tile, `spall_cover_pct` had two readings
2-3x apart, the moss keys fell outside the spec's own sRGB box. Each is visible in the spec's numbers alone.

Usage:
    python speccheck.py --tools T [--spec PATH] [--checks-dir DIR] [--out PATH] [--json]
    from speccheck import read_spec_values, SpecValuesError     # for a material's checks/gen_checks.py

Defaults: --spec T/spec.md, --checks-dir T/checks (a folder that is not there: rule 4 is skipped, with a note in
`skipped`), --out T/review/speccheck.json. `read_spec_values(spec_path)` returns the block as a dict (the same parse
and shape check as the CLI) and raises SpecValuesError, whose message lists every problem.

The block (spec.md §9, written by the spec author): exactly one fenced block whose opening line is exactly
```json spec_values and whose closing line is ```. A fence of another kind (```` or ~~~, or one with another info
string) is skipped whole, so a block shown as an example inside it is not counted. The content is strict JSON (no
comments, no NaN, no repeated key) and an object with these keys, all optional but unknown keys are an error:
    tile_m       number (a square tile) or [x, y], in m, positive
    colour_keys  [{id, section, variant, space, value | values, box | luma_box}]  variant: an optional string (the
                 variant the key belongs to), shown in the message as "variant V: "; value: a list of numbers; values: a list of
                 such lists (a key several presets set); box: per channel [lo, hi], null for an open end, the length
                 of value; luma_box: one [lo, hi] for the key's Rec.709 luma (for a key the spec states as sRGB luma
                 p50 and range, not per channel). Exactly one of box and luma_box.
    per_unit     [{id, section, unit, unit_m, tile_m, kind, what}]  unit_m: number or [x, y], positive; kind: random,
                 table, constant or other; tile_m (optional, like the top-level one): this entry's own tile, for a
                 material with two tiles; the top-level tile_m is the default, and one of the two is required.
    percentages  [{id, section, variant, value, unit, of, checks, config_scale}]  value: a number or [lo, hi] (null
                 for an open end); checks: the check ids that measure it; variant: the config checks/<variant>.json
                 (its `variant` key, else its file stem); config_scale: the factor from the spec's number to the
                 config target's number (0.01 for a percent in the spec and a fraction in the config; default 1)
Every item needs an `id`. A shape-problem message names the vocabulary it expects (the allowed keys, the kinds, the
spaces, "a key needs a value and a range"). A shape problem (unknown key, missing id, box/value length mismatch, a lo above a hi, a
unit_m or tile_m that is not positive, a percentage without a value, a wrong type) is collected with all the others
and ends the run with exit 2.

Rules. A finding is {rule, id, section, message, default, choice}; choice is true when the user may want to make the
call, false for a transcription error the author fixes without asking.
 1 colour_out_of_box   a channel of a key (of every preset of `values`) outside its [lo, hi], edges inclusive; with a
                       luma_box, the key's luma outside it. Luma is matcheck.py's own for channel `luma`: 0.2126 R +
                       0.7152 G + 0.0722 B on the value as given in its `space` (srgb255 0-255, srgb or raw 0-1, linear
                       linear); other spaces (hsv, hsl) need a box. choice false. Default: move the key inside the
                       box (nearest edge).
 2 period_lattice      kind random, with n = tile_m / unit_m (per axis) of 2 or less on one axis AND 8 or less on
                       the other (a 2-D lattice of at most 2 x 8 cells): a per-unit random prints a period-<unit_m>
                       lattice (a checker at 2). 2 or less on one axis with more than 8 on the other is a stripe set
                       by design (a per-track or per-joint-segment random): no finding. n within 1 % of an integer is
                       that integer. choice true. Default: drive it by a field that does not repeat inside the tile, or
                       keep the per-unit amplitude under 2 %.
   units_not_integer   n (kind random or table) is not within 1 % of an integer: the layout does not tile.
                       choice false.
   fixed_table         kind table, any n: a fixed per-unit table repeats every tile. choice true. Default: keep it,
                       state the repeat in §11 and judge it on the tiled sheet.
 3 percentage_checks   a percentage whose `checks` does not hold exactly one id (the message gives the count).
                       choice false. Default: name the one check that measures it.
   percentage_of       a percentage with no non-empty `of` (a percentage of what?). choice false. Default: state the
                       base (tile area, groove length, panel area ...).
 4 config_missing      a percentage with one check id and a `variant`, whose config, check, or target is not there.
   config_contradicts  its spec band times config_scale and the config band are disjoint. When they overlap with the
                       scale 100x or 0.01x off, the message says "unit mismatch (percent vs fraction?)".
   config_looser       the config band is not inside the spec band (looser on either end; relative tolerance 1e-6).
                       All three: choice false. Default: the spec wins, regenerate the config (config_missing:
                       generate the config from the block).
                       The config band is the check's `target` [lo, hi] (a number is a point), else `max_frac` as
                       [0, x] (a fraction is never negative, so the lower end is not open), else `target_mm` /
                       `target_deg` (a list, or a number as a point). null is open.
                       A spec point value v (a number, or [v, v]) is checked only for membership: config_contradicts
                       when v x config_scale is outside the config band, never config_looser (a config band wider
                       than a point is how a point is measured). A band spec value keeps both rules.
                       config_missing is for an absent config file or an absent check id only, except a point
                       value 0 whose check is absent from a config that is there: skipped ("0 preset; the variant
                       has no such check"), the variant simply does not measure it. Listed in `skipped`
                       and not compared: a percentage with no variant or without exactly one check id; a check found
                       in its config with no target / target_mm / target_deg / max_frac ("no comparable target"); a
                       check id with a ":" in it (a prefix, a script-computed row outside the configs, e.g.
                       ladder:wear_lines_path) or a config entry with "compare": false ("custom check"). Such a
                       check still counts as the one check of rule 3.
Messages do not start with the item's id (the summary line has it); percentage and config messages start with
"variant <name>:".
Output: the JSON file {spec, utc, block_ok, counts {rule: n}, findings, skipped}, written atomically (tmp +
os.replace); with a block that does not parse or fit its shape (exit 2) it is written with block_ok false, no
findings and an `errors` list, when the spec file could be read. On stdout a gate summary of at most 5 lines, one per
finding, the ones with choice true first, then the rest, each "<rule> <id>: <message> (default: <default>)"; when
there are more than 5 findings the 5th line is "... N more in <the output file>". `--json` prints the JSON file's
content instead. No findings: one line.
Exit code: 0 no findings; 1 findings; 2 a usage, input, parse, shape or output-write error (the message on stderr
says which). A config is found under its file stem and under its `variant` key.
Standard library only, Python 3.9 or newer, no shell: it works on Windows.
"""
import argparse
import datetime
import json
import math
import os
import re
import sys

if sys.version_info < (3, 9):
    sys.stderr.write("speccheck.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

TOP_KEYS = ("tile_m", "colour_keys", "per_unit", "percentages")
COLOUR_KEYS = ("id", "section", "variant", "space", "value", "values", "box", "luma_box")
UNIT_KEYS = ("id", "section", "unit", "unit_m", "tile_m", "kind", "what")
PCT_KEYS = ("id", "section", "variant", "value", "unit", "of", "checks", "config_scale")
KINDS = ("random", "table", "constant", "other")
OPEN_LINE = "```json spec_values"
CHANNELS = {"srgb255": "RGB", "srgb": "RGB", "rgb": "RGB", "linear": "RGB", "hsv": "HSV", "hsl": "HSL"}
INT_TOL = 0.01
REL_TOL = 1e-6
LATTICE_SMALL = 2
LATTICE_LONG = 8
LUMA = (0.2126, 0.7152, 0.0722)      # Rec.709, the weights matcheck.py applies to R, G, B for channel `luma`
LUMA_SPACES = ("srgb255", "srgb", "linear", "raw", "")
SPACES = ("srgb255", "srgb", "rgb", "linear", "raw", "hsv", "hsl")


class SpecValuesError(Exception):
    """The spec_values block is missing, repeated, not strict JSON, or does not fit its shape."""

    def __init__(self, message, problems=None):
        Exception.__init__(self, message)
        self.problems = list(problems) if problems else [message]


# ----------------------------------------------------------------------------- reading the block


def find_blocks(text):
    """The contents of every ```json spec_values block (top-level fences only), and the unclosed ones' line numbers."""
    blocks, unclosed = [], []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        m = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", raw)
        if not m or (m.group(1)[0] == "`" and "`" in m.group(2)):
            i += 1          # not a fence (CommonMark: a backtick fence's info string has no backtick)
            continue
        fence = m.group(1)
        is_block = raw == OPEN_LINE
        j = i + 1
        while j < len(lines):
            c = "" if lines[j].startswith("    ") else lines[j].strip()     # 4+ spaces of indent cannot close
            if c and set(c) == {fence[0]} and len(c) >= len(fence):
                break
            j += 1
        if j >= len(lines):
            if is_block:
                unclosed.append(i + 1)
            i += 1 if is_block else len(lines)
            continue
        if is_block:
            blocks.append((i + 1, "\n".join(lines[i + 1:j])))
        i = j + 1
    return blocks, unclosed


def _no_const(name):
    raise ValueError("%s is not allowed in strict JSON" % name)


def _no_dups(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("repeated key %r" % k)
        d[k] = v
    return d


def is_num(x):
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return False
    try:
        return math.isfinite(x)
    except OverflowError:       # an integer literal too large for a float
        return False


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def sec_text(item):
    s = item.get("section") if isinstance(item, dict) else None
    return "" if s is None else str(s)


def pair(v, what, problems, positive=False):
    """[x, y] from a number (square) or a 2-list; None and a problem when it is neither."""
    if is_num(v):
        v = [v, v]
    if not (isinstance(v, list) and len(v) == 2 and all(is_num(a) for a in v)):
        problems.append("%s must be a number or [x, y] of numbers" % what)
        return None
    if positive and not all(a > 0 for a in v):
        problems.append("%s must be positive (it is %s)" % (what, json.dumps(v)))
        return None
    return [float(v[0]), float(v[1])]


def band(v, what, problems):
    """(lo, hi) from a number or [lo, hi] with null ends; None and a problem otherwise."""
    if is_num(v):
        return (float(v), float(v))
    if (isinstance(v, list) and len(v) == 2 and all(a is None or is_num(a) for a in v)):
        lo = -math.inf if v[0] is None else float(v[0])
        hi = math.inf if v[1] is None else float(v[1])
        if lo > hi:
            problems.append("%s has lo above hi (%s)" % (what, json.dumps(v)))
            return None
        return (lo, hi)
    problems.append("%s must be a number or [lo, hi] (null for an open end)" % what)
    return None


def check_keys(item, allowed, where, problems):
    for k in item:
        if k not in allowed:
            problems.append("%s: unknown key %r (allowed: %s)" % (where, k, ", ".join(allowed)))
    if not (isinstance(item.get("id"), str) and item["id"].strip()):
        problems.append("%s: missing or empty id" % where)
    for k in ("section", "variant", "unit", "of", "space", "what"):
        if k in item and item[k] is not None and not isinstance(item[k], (str, int, float)):
            problems.append("%s: %s must be a string" % (where, k))


def validate(doc):
    """Every shape problem of a parsed block, as a list of messages (empty when it fits)."""
    problems = []
    if not isinstance(doc, dict):
        return ["the block must be a JSON object"]
    for k in doc:
        if k not in TOP_KEYS:
            problems.append("unknown top-level key %r (allowed: %s)" % (k, ", ".join(TOP_KEYS)))
    if "tile_m" in doc:
        pair(doc["tile_m"], "tile_m", problems, positive=True)
    for key in ("colour_keys", "per_unit", "percentages"):
        if key in doc and not isinstance(doc[key], list):
            problems.append("%s must be a list" % key)
    colours = doc.get("colour_keys") if isinstance(doc.get("colour_keys"), list) else []
    for n, c in enumerate(colours):
        where = "colour_keys[%d]" % n + (" %s" % c["id"] if isinstance(c, dict) and isinstance(c.get("id"), str) else "")
        if not isinstance(c, dict):
            problems.append("%s must be an object" % where)
            continue
        check_keys(c, COLOUR_KEYS, where, problems)
        if ("value" in c) == ("values" in c):
            problems.append("%s: give exactly one of value and values (a key needs a value and a range: value [r, g, b] "
                            "or values [[r, g, b], ...], and box [[lo, hi] per channel] or luma_box [lo, hi])" % where)
        vals = []
        if "value" in c:
            vals = [c["value"]]
        elif isinstance(c.get("values"), list) and c["values"]:
            vals = c["values"]
        elif "values" in c:
            problems.append("%s: values must be a non-empty list of lists" % where)
        for v in vals:
            if not (isinstance(v, list) and v and all(is_num(a) for a in v)):
                problems.append("%s: a value must be a non-empty list of numbers (got %s)" % (where, json.dumps(v)))
        if ("box" in c) == ("luma_box" in c):
            problems.append("%s: give exactly one of box and luma_box (a key needs a value and a range: box is "
                            "[[lo, hi] per channel], luma_box is one [lo, hi])" % where)
        if "luma_box" in c:
            lb = c["luma_box"]
            if not (isinstance(lb, list) and len(lb) == 2):
                problems.append("%s: luma_box must be [lo, hi]" % where)
            else:
                band(lb, "%s luma_box" % where, problems)
            if str(c.get("space") or "").lower() not in LUMA_SPACES:
                problems.append("%s: luma_box needs space %s (got %s; the spaces are %s)" % (
                    where, ", ".join(LUMA_SPACES[:-1]), json.dumps(c.get("space")), ", ".join(SPACES)))
            for v in vals:
                if isinstance(v, list) and len(v) not in (3, 4):
                    problems.append("%s: a luma_box value needs 3 channels (RGB), got %d" % (where, len(v)))
        if "box" not in c:
            continue
        box = c["box"]
        if not (isinstance(box, list) and box):
            problems.append("%s: box must be a non-empty list of [lo, hi]" % where)
            continue
        for ch, b in enumerate(box):
            if isinstance(b, list) and len(b) == 2:
                band(b, "%s box[%d]" % (where, ch), problems)
            else:
                problems.append("%s: box[%d] must be [lo, hi]" % (where, ch))
        for v in vals:
            if isinstance(v, list) and len(v) != len(box):
                problems.append("%s: value has %d channels and box has %d" % (where, len(v), len(box)))
    units = doc.get("per_unit") if isinstance(doc.get("per_unit"), list) else []
    for n, u in enumerate(units):
        where = "per_unit[%d]" % n + (" %s" % u["id"] if isinstance(u, dict) and isinstance(u.get("id"), str) else "")
        if not isinstance(u, dict):
            problems.append("%s must be an object" % where)
            continue
        check_keys(u, UNIT_KEYS, where, problems)
        tl = None
        if "tile_m" in u:
            tl = pair(u["tile_m"], "%s tile_m" % where, problems, positive=True)
        elif "tile_m" in doc:
            tl = pair(doc["tile_m"], "tile_m", [])
        else:
            problems.append("%s: needs tile_m (its own, or the top-level one)" % where)
        if "unit_m" not in u:
            problems.append("%s: missing unit_m" % where)
        else:
            um = pair(u["unit_m"], "%s unit_m" % where, problems, positive=True)
            if um and tl and any(not math.isfinite(tl[a] / um[a]) or tl[a] / um[a] > 1e9 for a in (0, 1)):
                problems.append("%s: tile_m / unit_m is not a usable number of units per tile" % where)
        if u.get("kind") not in KINDS:
            problems.append("%s: kind must be one of %s (got %s)" % (where, ", ".join(KINDS), json.dumps(u.get("kind"))))
    pcts = doc.get("percentages") if isinstance(doc.get("percentages"), list) else []
    for n, p in enumerate(pcts):
        where = "percentages[%d]" % n + (" %s" % p["id"] if isinstance(p, dict) and isinstance(p.get("id"), str) else "")
        if not isinstance(p, dict):
            problems.append("%s must be an object" % where)
            continue
        check_keys(p, PCT_KEYS, where, problems)
        if "value" not in p:
            problems.append("%s: missing value" % where)
        else:
            band(p["value"], "%s value" % where, problems)
        if "checks" in p and not (isinstance(p["checks"], list) and all(isinstance(a, str) for a in p["checks"])):
            problems.append("%s: checks must be a list of check ids" % where)
        if "config_scale" in p and not (is_num(p["config_scale"]) and p["config_scale"] > 0):
            problems.append("%s: config_scale must be a positive number" % where)
    return problems


def parse_text(text):
    """The validated block of a spec's text; SpecValuesError with every problem otherwise."""
    blocks, unclosed = find_blocks(text)
    if unclosed:
        raise SpecValuesError("the ```json spec_values block opened at line %d is never closed" % unclosed[0])
    if not blocks:
        near = [n + 1 for n, ln in enumerate(text.splitlines())
                if re.match(r"^ {0,3}(`{3,}|~{3,})", ln) and "spec_values" in ln]
        hint = (" (line %s looks like an opening fence but is not exactly ```json spec_values)" % near[0]) if near else ""
        raise SpecValuesError("no ```json spec_values block in the spec (§9 of spec_template.md has it)" + hint)
    if len(blocks) > 1:
        raise SpecValuesError("%d ```json spec_values blocks (lines %s): exactly one is allowed" % (
            len(blocks), ", ".join(str(b[0]) for b in blocks)))
    line, body = blocks[0]
    try:
        doc = json.loads(body, parse_constant=_no_const, object_pairs_hook=_no_dups)
    except ValueError as e:
        raise SpecValuesError("the spec_values block (line %d) is not strict JSON: %s" % (line, e))
    problems = validate(doc)
    if problems:
        raise SpecValuesError("the spec_values block (line %d) has %d problem%s: %s" % (
            line, len(problems), "" if len(problems) == 1 else "s", "; ".join(problems)), problems)
    return doc


def read_spec_values(spec_path):
    """The spec_values block of the spec file at spec_path as a dict. Raises SpecValuesError (a bad block) or OSError."""
    with open(spec_path, encoding="utf-8-sig") as fh:
        return parse_text(fh.read())


# ----------------------------------------------------------------------------- rules


def finding(rule, item, message, default, choice):
    return {"rule": rule, "id": item.get("id"), "section": sec_text(item), "message": message,
            "default": default, "choice": choice}


def fmt(x):
    if x is None:
        return "null"
    if isinstance(x, float) and math.isfinite(x) and abs(x) < 1e15 and x == int(x):
        return str(int(x))
    return ("%.6g" % x) if isinstance(x, float) else str(x)


def luma(v):
    """Rec.709 luma of an RGB value in its own space: the weights matcheck.py applies in map_values for channel `luma`
    (srgb255 is the stored sRGB times 255, linear the linearised value, raw the stored value: in each the weights go
    on the three numbers as they are)."""
    return sum(w * x for w, x in zip(LUMA, v[:3]))


def rule_colour(doc):
    out = []
    for c in doc.get("colour_keys") or []:
        vals = c["values"] if "values" in c else [c["value"]]
        names = CHANNELS.get(str(c.get("space", "")).lower(), "")
        if "luma_box" in c:
            boxes = [band(c["luma_box"], "", [])]
            shown = json.dumps(c["luma_box"])
            checks = [[luma(v)] for v in vals]
            label = "luma_box"
        else:
            boxes = [band(b, "", []) for b in c["box"]]
            shown = None
            checks = vals
            label = "box"
        for pi, v in enumerate(checks):
            for ch, x in enumerate(v):
                lo, hi = boxes[ch]
                if lo - slack(lo) <= x <= hi + slack(hi):
                    continue
                if label == "luma_box":
                    name = "luma"
                else:
                    name = names[ch] if len(names) == len(v) else str(ch)
                which = "above" if x > hi else "below"
                bound = hi if x > hi else lo
                preset = "preset %d: " % pi if len(vals) > 1 else ""
                out.append(finding(
                    "colour_out_of_box", c,
                    "%s%schannel %s = %s is %s the %s bound %s (%s %s)" % (
                        vprefix(c), preset, name, fmt(round(x, 4) if label == "luma_box" else x), which,
                        "luma_box" if label == "luma_box" else "box", fmt(bound), label,
                        shown or json.dumps(c["box"][ch])),
                    "move the key inside the %s (nearest edge)" % ("luma box" if label == "luma_box" else "box"), False))
    return out


def axis_n(tile, unit):
    """(n, integer-or-None): the units per tile on one axis and the integer it is within 1 % of."""
    n = tile / unit
    if not math.isfinite(n):
        return n, None
    r = round(n)
    if r >= 1 and abs(n - r) <= INT_TOL * r:
        return float(r), r
    return n, None


def lattice_2d(nx, ny):
    """A per-unit random is a 2-D lattice (at most about 2 x 8 cells) when one axis has 2 units or fewer and the other
    8 or fewer; 2 or fewer on one axis and more than 8 on the other is a stripe set (a per-track or per-joint-segment
    random) by design."""
    return (nx <= LATTICE_SMALL and ny <= LATTICE_LONG) or (ny <= LATTICE_SMALL and nx <= LATTICE_LONG)


def rule_period(doc):
    out = []
    for u in doc.get("per_unit") or []:
        tile = pair(u["tile_m"] if "tile_m" in u else doc["tile_m"], "tile_m", [])
        um = pair(u["unit_m"], "unit_m", [])
        ns = [axis_n(tile[a], um[a]) for a in (0, 1)]
        tile_txt = "%s x %s m" % (fmt(tile[0]), fmt(tile[1]))
        unit_txt = fmt(um[0]) if um[0] == um[1] else "%s x %s" % (fmt(um[0]), fmt(um[1]))
        if u["kind"] in ("random", "table") and any(i is None for _, i in ns):
            out.append(finding(
                "units_not_integer", u,
                "%s x %s %ss per tile (tile %s, %s m each): the layout does not tile" % (
                    fmt(round(ns[0][0], 4)), fmt(round(ns[1][0], 4)), u.get("unit") or "unit", tile_txt, unit_txt),
                "make the tile an integer number of units per axis", False))
        if u["kind"] == "random" and lattice_2d(ns[0][0], ns[1][0]):
            out.append(finding(
                "period_lattice", u,
                "%s x %s units per tile, a per-unit random prints a period-%s m lattice (a checker at 2)" % (
                    fmt(round(ns[0][0], 4)), fmt(round(ns[1][0], 4)), unit_txt),
                "drive it by a field that does not repeat inside the tile (a noise with a period of at least 3 units), "
                "or keep the per-unit amplitude under 2 %", True))
        if u["kind"] == "table":
            out.append(finding(
                "fixed_table", u,
                "a fixed per-unit table repeats every tile (%s)" % tile_txt,
                "keep it, state the repeat in §11 and judge it on the tiled sheet", True))
    return out


def vprefix(p):
    """'variant V: ' for a percentage that names a variant, else ''."""
    return ("variant %s: " % p["variant"]) if p.get("variant") else ""


def rule_percent_shape(doc):
    out = []
    for p in doc.get("percentages") or []:
        n = len(p.get("checks") or [])
        if n != 1:
            out.append(finding(
                "percentage_checks", p,
                "%s%d check%s name it (exactly one is needed)" % (vprefix(p), n, "" if n == 1 else "s"),
                "name the one check that measures it", False))
        if not (isinstance(p.get("of"), str) and p["of"].strip()):
            out.append(finding(
                "percentage_of", p,
                "%s%s of what?" % (vprefix(p), fmt_band(band(p["value"], "", [])) + (" " + str(p["unit"])
                                                                                     if p.get("unit") else "")),
                "state the base (tile area, groove length, panel area ...)", False))
    return out


def fmt_band(b):
    return fmt(b[0]) if b[0] == b[1] else "%s to %s" % (fmt(b[0]) if b[0] != -math.inf else "null",
                                                          fmt(b[1]) if b[1] != math.inf else "null")


def slack(x):
    return REL_TOL * max(abs(x), 1e-12) if math.isfinite(x) else 0.0


def inside(inner, outer):
    return inner[0] >= outer[0] - slack(outer[0]) and inner[1] <= outer[1] + slack(outer[1])


def disjoint(a, b):
    return a[1] < b[0] - slack(b[0]) or b[1] < a[0] - slack(a[0])


def scaled(b, f):
    return (b[0] * f, b[1] * f)


def config_band(chk):
    """(band, key) of a check's target, or (None, None)."""
    for key in ("target", "target_mm", "target_deg"):
        if key in chk and chk[key] is not None:
            b = band(chk[key], "", [])
            if b is not None:
                return b, key
    if is_num(chk.get("max_frac")):
        return (0.0, float(chk["max_frac"])), "max_frac"
    return None, None


def load_configs(checks_dir, notes):
    """{variant: [(path, data)]} of the *.json configs with a checks list."""
    out = {}
    for name in sorted(os.listdir(checks_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(checks_dir, name)
        try:
            with open(path, encoding="utf-8-sig") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as e:
            notes.append({"rule": "config_contradicts", "id": None, "reason": "%s unreadable (%s)" % (name, e)})
            continue
        if not (isinstance(data, dict) and isinstance(data.get("checks"), list)):
            continue
        names = [name[:-5]]
        if isinstance(data.get("variant"), str) and data["variant"] and data["variant"] not in names:
            names.append(data["variant"])
        for var in names:
            out.setdefault(var, []).append((path, data))
    return out


def rule_config(doc, checks_dir, skipped):
    pcts = doc.get("percentages") or []
    if not pcts:
        return []
    if not checks_dir or not os.path.isdir(checks_dir):
        skipped.append({"rule": "config_contradicts", "id": None,
                        "reason": "no checks folder (%s): rule 4 skipped" % (checks_dir or "none")})
        return []
    configs = load_configs(checks_dir, skipped)
    out = []
    for p in pcts:
        checks = p.get("checks") or []
        if len(checks) != 1 or not p.get("variant"):
            skipped.append({"rule": "config_contradicts", "id": p["id"],
                            "reason": "needs exactly one check id and a variant (has %d, variant %s)" % (
                                len(checks), json.dumps(p.get("variant")))})
            continue
        cid, var = checks[0], p["variant"]
        vp = vprefix(p)
        if ":" in cid:
            skipped.append({"rule": "config_contradicts", "id": p["id"],
                            "reason": "custom check %s of variant %s (a script-computed row outside the configs)" % (
                                cid, var)})
            continue
        chk = None
        for _path, data in configs.get(var, []):
            chk = next((c for c in data["checks"] if isinstance(c, dict) and c.get("id") == cid), None)
            if chk is not None:
                break
        if var not in configs:
            why = "no config checks/%s.json (no file with that name or `variant`)" % var
        elif chk is None:
            if band(p["value"], "", []) == (0.0, 0.0):
                skipped.append({"rule": "config_contradicts", "id": p["id"],
                                "reason": "variant %s: 0 preset; the variant has no such check (%s)" % (var, cid)})
                continue
            why = "config has no check %s" % cid
        else:
            why = None
        if why:
            out.append(finding("config_missing", p, vp + why, "generate the config from the block", False))
            continue
        if chk.get("compare") is False:
            skipped.append({"rule": "config_contradicts", "id": p["id"],
                            "reason": "custom check %s of variant %s (compare is false)" % (cid, var)})
            continue
        cb, key = config_band(chk)
        if cb is None:
            skipped.append({"rule": "config_contradicts", "id": p["id"],
                            "reason": "no comparable target: check %s of variant %s has no target, target_mm, "
                                      "target_deg or max_frac" % (cid, var)})
            continue
        scale = float(p.get("config_scale", 1))
        sb = band(p["value"], "", [])
        sv = scaled(sb, scale)
        spec_txt = "%s%s" % (fmt_band(sb), (" " + str(p["unit"])) if p.get("unit") else "")
        point = sb[0] == sb[1]
        if disjoint(sv, cb) or (point and not inside(sv, cb)):
            msg = "%sthe spec says %s (x %s = %s) and check %s targets %s, %s" % (
                vp, spec_txt, fmt(scale), fmt_band(sv), cid, fmt_band(cb),
                "the point is outside that band" if point and not disjoint(sv, cb) else "no overlap")
            if any(not disjoint(scaled(sb, scale * f), cb) for f in (100.0, 0.01)):
                msg += ": unit mismatch (percent vs fraction?)"
            out.append(finding("config_contradicts", p, msg, "the spec wins: regenerate the config", False))
        elif not point and not inside(cb, sv):
            out.append(finding(
                "config_looser", p,
                "%scheck %s targets %s, wider than the spec band %s (x %s = %s)" % (
                    vp, cid, fmt_band(cb), spec_txt, fmt(scale), fmt_band(sv)),
                "the spec wins: regenerate the config", False))
    return out


# ----------------------------------------------------------------------------- command line


def atomic_write(path, text):
    folder = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_rules(doc, checks_dir):
    skipped = []
    found = rule_colour(doc) + rule_period(doc) + rule_percent_shape(doc) + rule_config(doc, checks_dir, skipped)
    return found, skipped


def summary_lines(findings, out_label):
    ordered = [f for f in findings if f["choice"]] + [f for f in findings if not f["choice"]]
    lines = [" ".join(("%s %s: %s (default: %s)" % (f["rule"], f["id"], f["message"], f["default"])).split())
             for f in ordered]
    if len(lines) > 5:
        lines = lines[:4] + ["... %d more in %s" % (len(lines) - 4, out_label)]
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check the numbers of a spec's spec_values block (R-16).")
    ap.add_argument("--tools", required=True, help="the material's tools folder T")
    ap.add_argument("--spec", help="the spec (default T/spec.md)")
    ap.add_argument("--checks-dir", help="the checks configs (default T/checks)")
    ap.add_argument("--out", help="the JSON result (default T/review/speccheck.json)")
    ap.add_argument("--json", action="store_true", help="print the JSON instead of the summary")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    for stream in (sys.stdout, sys.stderr):      # a narrow console codec must not turn a result into a crash
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    tools = a.tools
    spec = a.spec or os.path.join(tools, "spec.md")
    checks_dir = a.checks_dir or os.path.join(tools, "checks")
    out = a.out or os.path.join(tools, "review", "speccheck.json")
    if not os.path.isfile(spec):
        sys.stderr.write("speccheck.py: no spec at %s\n" % spec)
        return 2
    base = {"spec": os.path.abspath(spec), "utc": utc_now()}
    try:
        doc = read_spec_values(spec)
    except SpecValuesError as e:
        for p in e.problems:
            sys.stderr.write("speccheck.py: %s\n" % p)
        data = dict(base, block_ok=False, counts={}, findings=[], skipped=[], errors=e.problems)
        try:
            atomic_write(out, json.dumps(data, indent=1) + "\n")
        except OSError as w:
            sys.stderr.write("speccheck.py: cannot write %s: %s\n" % (out, w))
        return 2
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write("speccheck.py: cannot read %s: %s\n" % (spec, e))
        return 2
    found, skipped = run_rules(doc, checks_dir)
    counts = {}
    for f in found:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    data = dict(base, block_ok=True, counts=counts, findings=found, skipped=skipped)
    text = json.dumps(data, indent=1) + "\n"
    try:
        atomic_write(out, text)
    except OSError as e:
        sys.stderr.write("speccheck.py: cannot write %s: %s\n" % (out, e))
        return 2
    if a.json:
        sys.stdout.write(text)
    else:
        rel = os.path.relpath(out, tools) if os.path.abspath(out).startswith(os.path.abspath(tools) + os.sep) else out
        rel = rel.replace(os.sep, "/")
        lines = summary_lines(found, rel) if found else [
            "speccheck: no findings" + ("; %s" % skipped[0]["reason"] if skipped and skipped[0]["id"] is None else "")]
        sys.stdout.write("\n".join(lines) + "\n")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
