#!/usr/bin/env python3
"""Count saturated pixels in the textures sk.clamp_probe() saved, to catch a 16-bit Blend add or Levels that clamps at 1
(R-19). This docstring is the reference.

Why: a 16-bit (fixed-point) Blend add or a Levels node clamps its result at 1.0. Input ranges cannot be read from the
graph, so sk.clamp_candidates() lists the nodes where it could happen (sk.lint() prints a count) and this check measures
them after the rebuild. M8 met the clamp twice (round 2 fix P5; round 3's D-shaped spall high, where the spall floors
flattened as the add saturated). Fix a failure by scaling the terms down before the add (see sd_craft.md).

Usage (two steps, after the rebuild):
    1. in Designer:  sk.clamp_probe(output="height", exempt={"node_name": "reason"})
       -> <tools>/dump/clamp_probe/<node>.png and clamp_probe.json (one compute; the temporary outputs are removed)
    2. in a shell:   python clampcheck.py <tools>/dump/clamp_probe [--limit 0.005] [--out PATH]
Input: the folder written by clamp_probe, or its clamp_probe.json. A row's `path` is read as written; when that file is
not there (the folder was moved) the same file name beside the JSON is used.

Reads: clamp_probe.json {graph, output, utc, size, outputs_found, exempt {name: reason}, rows [{name, def, mode, path,
format, size, exempt?, error?}]}; each PNG through matcheck.load_image (16-bit kept; this needs numpy, Pillow and scipy: use the
skill's environment, scripts/setup_env.sh).

Rule: share_at_1 is the share of pixels at the top code (65535 of 65535 in a 16-bit file, 255 of 255 in an 8-bit file;
for a colour file, pixels with every colour channel at the top). share_at_0 is the share at code 0 (reported only). A
row FAILS when share_at_1 > --limit (a fraction, default 0.005 = 0.5 %, an estimate: a clean height keeps a few
pixels at white where the material truly peaks, a saturated add holds whole areas at 1) and the node is not exempt.
Exempt: a node named in the JSON's `exempt` dict or marked `exempt` on its row (a node meant to saturate, for example a
mask built by an add; the reason is kept); it is measured and printed but never fails. Skipped, not failed: a row whose
format names a float type (LUM16F, RGBA32F ...: "float: no clamp"). A row with `error` (the node could not be probed)
is printed as ERROR and listed in `errors`: the node was NOT measured, so unless it is exempt this is a failing gate
(exit 1) like a measured failure. An exempt reason, even an empty one, makes a node exempt.
If `outputs_found` is 0 the output name matched no Output node (a mistyped name, Height for height): with no rows that
is a usage error (exit 2, nothing was checked); with rows (explicit names) it is a WARN line.

Writes clamp_check.json beside the input (or at --out): {limit, source, rows [{name, share_at_1, share_at_0, fail,
format, skipped?, exempt?, error?}], failed [names], errors [names]}. Prints one line per row and a summary line.
Exit codes: 0 none failed and none unmeasured, 1 any failed or any non-exempt node not measured (probe error), 2 usage
error, unreadable JSON, a missing image, or an output name that matched nothing (outputs_found 0, no rows).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

DEFAULT_LIMIT = 0.005


def is_float_format(fmt):
    """True when a pixel format name ("SBSPixelFormat.LUM16F", "RGBA32F") is a float type."""
    base = str(fmt or "").split(".")[-1]
    return bool(re.search(r"\d+F$", base, re.I)) or "FLOAT" in base.upper()


def shares(a):
    """(share at the top code, share at 0) of a float image in 0-1 as read by matcheck.load_image. 16-bit 65535 and
    8-bit 255 both read as exactly 1.0; the next code down is below 0.997."""
    import numpy as np
    if a.ndim == 3:
        rgb = a[..., :3]
        top = np.all(rgb >= 1.0, axis=-1)
        zero = np.all(rgb <= 0.0, axis=-1)
    else:
        top, zero = a >= 1.0, a <= 0.0
    n = float(top.size) or 1.0
    return float(top.sum()) / n, float(zero.sum()) / n


def find_png(path, base):
    """The row's file as written, else its name beside the JSON."""
    if path and os.path.isfile(path):
        return path
    alt = os.path.join(base, os.path.basename(path or ""))
    return alt if path and os.path.isfile(alt) else None


def run(src, limit, out=None, load=None, write=print):
    """Check a clamp_probe folder or json. Returns (exit code, result dict or None)."""
    js = os.path.join(src, "clamp_probe.json") if os.path.isdir(src) else src
    if not os.path.isfile(js):
        write("clampcheck: no clamp_probe.json at %s" % js)
        return 2, None
    base = os.path.dirname(os.path.abspath(js))
    try:
        with open(js, encoding="utf-8") as fh:
            probe = json.load(fh)
        rows_in = list(probe["rows"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        write("clampcheck: cannot read %s: %s" % (js, e))
        return 2, None
    exempt = probe.get("exempt") if isinstance(probe.get("exempt"), dict) else {}
    if load is None:
        try:
            import matcheck
        except ImportError as e:  # numpy, Pillow or scipy missing
            write("clampcheck: cannot import matcheck (%s); use the skill's environment (scripts/setup_env.sh)" % e)
            return 2, None
        load = matcheck.load_image
    found = probe.get("outputs_found")
    if found == 0:
        write("clampcheck: WARN output %r matched no Output node in %s (identifier or usage): check the name"
              % (probe.get("output"), probe.get("graph")))
        if not rows_in:
            write("clampcheck: nothing was checked")
            return 2, None
    rows, failed, errors, unmeasured = [], [], [], []
    for r in rows_in:
        name = r.get("name")
        row = {"name": name, "share_at_1": None, "share_at_0": None, "fail": False, "format": r.get("format")}
        why = r["exempt"] if r.get("exempt") is not None else exempt.get(name)
        if why is not None:
            row["exempt"] = str(why) or "exempt"
            why = row["exempt"]
        if r.get("error"):
            row["error"] = r["error"]
            row["skipped"] = "probe error: not measured"
            errors.append(name)
            if not why:
                unmeasured.append(name)
        elif is_float_format(r.get("format")):
            row["skipped"] = "float: no clamp"
        else:
            png = find_png(r.get("path"), base)
            if png is None:
                write("clampcheck: image for %s is missing: %s" % (name, r.get("path")))
                return 2, None
            try:
                row["share_at_1"], row["share_at_0"] = shares(load(png))
            except Exception as e:  # noqa: BLE001 - any reader failure is a missing/unreadable image
                write("clampcheck: cannot read %s: %s" % (png, e))
                return 2, None
            row["fail"] = row["share_at_1"] > limit and not why
            if row["fail"]:
                failed.append(name)
        rows.append(row)
        if row.get("error"):
            line = "ERROR %-24s not measured: %s" % (name, row["error"])
        elif row.get("skipped"):
            line = "SKIP  %-24s %s" % (name, row["skipped"])
        else:
            tag = "FAIL" if row["fail"] else ("EXEMPT" if why and row["share_at_1"] > limit else "OK")
            line = "%-5s %-24s at_1 %6.2f %%  at_0 %6.2f %%" % (tag, name, 100 * row["share_at_1"], 100 * row["share_at_0"])
            if why:
                line += "  (exempt: %s)" % why
        write(line)
    result = {"limit": limit, "source": js, "outputs_found": found, "rows": rows, "failed": failed, "errors": errors}
    out = out or os.path.join(base, "clamp_check.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    os.replace(out + ".tmp", out)
    write("clampcheck: %d rows, %d failed%s%s, limit %.3g %%"
          % (len(rows), len(failed), " (%s)" % ", ".join(map(str, failed)) if failed else "",
             ", %d NOT measured (%s)" % (len(errors), ", ".join(map(str, errors))) if errors else "", 100 * limit))
    return (1 if failed or unmeasured else 0), result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Share of pixels at the top code in clamp_probe textures (R-19).")
    ap.add_argument("source", help="the clamp_probe folder or its clamp_probe.json")
    ap.add_argument("--limit", type=float, default=DEFAULT_LIMIT, help="largest allowed share at 1 as a fraction (0.005)")
    ap.add_argument("--out", default=None, help="where to write clamp_check.json (default: beside the input)")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if not 0 <= a.limit <= 1:
        print("clampcheck: --limit is a fraction between 0 and 1 (0.005 = 0.5 %%), got %s" % a.limit)
        return 2
    return run(a.source, a.limit, a.out)[0]


if __name__ == "__main__":
    sys.exit(main())
