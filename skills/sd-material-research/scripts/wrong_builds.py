#!/usr/bin/env python3
"""Replay each hard check against its named wrong build: the check must pass the real maps and fail the wrong build
(references/checks.md, "Hard checks that can fail").

Usage:
    python wrong_builds.py --cases checks/wrong_build_cases.py --checks-dir checks --out review [--only id1,id2]
    python wrong_builds.py --cases checks/wrong_build_cases.py --list
    python wrong_builds.py --merge review/wb/classic review/wb/weathered ... --out review

The cases module defines CASES = [(config, check_id, wrong_build, edit), ...]: `config` names <checks-dir>/<config>.json,
`check_id` a hard check in it, `wrong_build` the mistake in words, and edit(ctx) returns the wrong build as a list of
(render, map, array) with render "" for the main render or a comparison render's name (a drift that nowear shares).
Edits return new arrays: an edit that hands back a loaded map changed in place misbehaves (the map reloads).
The arrays replace those maps in memory, the check runs through matcheck's own check functions, and the case behaves
when the check passes the real maps and fails the edited ones. Cases on a check that is not hard in that config are
skipped (so one loop can cover many configs). Optional hooks in the cases module:
    CONFIGS = [...]             configs whose hard checks must all be covered (default: the configs named in CASES)
    CROSS_CASES = {group: fn}   hard checks across variants that no single config holds (e.g. a ladder): fn(load)
                                yields (check_id, wrong_build, real_pass, wrong_pass, real_value, wrong_value);
                                load(config) returns (cfg, ctx)
--only takes configs, cross-case groups or check ids (a group runs only when named or when --only is absent).
Writes wrong_builds.md and .json in --out. Exit code: 0 when every case behaves and every hard check has a case, 1 when
a case misbehaves or a hard check has none, 2 on a config error or a cases module that does not load.
--list prints {"configs": [...], "groups": [...], "cases": N, "ids": [...]} as JSON, configs and groups in the order a
run takes them, ids the cases' check ids (exit 0, or 2 when the module does not load). --merge reads the
wrong_builds.json of each folder, in the order given, and writes the merged report to --out with the same exit code
(seconds = their sum); suite.py runs one --only job per config and per group, then merges them in --list order, which
equals one serial run.

Cases modules `import wrong_builds as wb` for the edit helpers (paint, luma_shift, height_units, normal_from, stepped,
once) and `import matcheck as mc` for the region tools (mc.dilate, mc.erode, ...).
"""
import argparse
import importlib.util
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import matcheck as mc  # noqa: E402

# ----------------------------------------------------------------------------- maps edited in memory


def flush(ctx):
    """Forget everything derived from the maps (grey views, regions, elements) so the next check recomputes it."""
    for R in [ctx.main] + list(ctx.compare.values()):
        R._gray.clear()
        R._views.clear()
        R._regions.clear()
    ctx._elements.clear()


class Swap:
    """Temporarily replace maps with edited arrays: edits = [(render, map, array)], render "" = main."""

    def __init__(self, ctx, edits):
        self.ctx, self.edits, self.saved = ctx, edits, []

    def __enter__(self):
        try:
            for rn, mn, arr in self.edits:
                R = self.ctx.render(rn or None)
                old = R.map(mn)
                if np.may_share_memory(arr, old):     # changed in place: reload the real map, or later cases read the edit
                    R.drop(mn)
                    raise ValueError("edit returned the loaded '%s' map itself (changed in place?): edit a copy" % mn)
                self.saved.append((R, mn, old))
                R._maps[mn] = np.ascontiguousarray(arr, dtype=np.float32)
        except Exception:
            self.__exit__()
            raise
        flush(self.ctx)
        return self

    def __exit__(self, *a):
        for R, mn, arr in reversed(self.saved):
            R._maps[mn] = arr
        self.saved = []
        flush(self.ctx)


# ----------------------------------------------------------------------------- edit helpers for cases modules

def paint(bc, m, rgb255):
    """basecolor with the pixels of mask m set to an sRGB colour (0-255)."""
    o = bc.copy()
    for i in range(3):
        o[..., i][m] = rgb255[i] / 255.0
    return o


def luma_shift(bc, m, d255):
    """basecolor with d255 (0-255 units) added to every channel inside mask m."""
    o = bc.copy()
    o[..., :3][m] = np.clip(o[..., :3][m] + d255 / 255.0, 0, 1)
    return o


def height_units(ctx, mm):
    """mm as height-map units (0-1 spans height_depth_mm)."""
    return mm / ctx.depth_mm


def normal_from(ctx, h_units, green=-1.0):
    """DirectX (green -1) or OpenGL (+1) normal of a height map, backward differences, RGB in 0-1."""
    h = h_units.astype(np.float64) * ctx.depth_mm
    gx = (h - np.roll(h, 1, 1)) / ctx.mmx
    gy = (h - np.roll(h, 1, 0)) / ctx.mmy
    n = np.stack([-gx, green * gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5).astype(np.float32)


def stepped(a, step):
    """The map with a linear ramp along U that ends in a step of `step` at the wrapped U border (what a coordinate that
    does not wrap, or a non-tiling noise, leaves). Sign chosen away from the nearer end of 0-1, so a mask sitting at 0
    or 1 keeps the step after clamping."""
    ramp = (np.arange(a.shape[1]) / float(a.shape[1] - 1))[None, :]
    ramp = ramp[..., None] if a.ndim == 3 else ramp
    edge = np.concatenate([a[:, :8], a[:, -8:]], axis=1)
    sign = -1.0 if float(np.mean(edge)) > 0.5 else 1.0          # away from the end the border columns sit near
    return np.clip(a + sign * ramp * step, 0.0, 1.0) if a.max() <= 1.0 else a + sign * ramp * step


def once(ctx, key, fn):
    """fn() computed once per loaded config, for inputs several edits share (distance maps, region medians)."""
    memo = ctx.__dict__.setdefault("_wb_once", {})
    if key not in memo:
        memo[key] = fn()
    return memo[key]


# ----------------------------------------------------------------------------- harness

def run(ctx, c):
    r = mc.run_check(ctx, c)
    v = r.get("value")
    return r.get("passed"), (round(v, 6) if isinstance(v, float) and math.isfinite(v) else v), r.get("note") or r.get("error")


def record(rows, config, cid, wrong, p0, v0, p1, v1, note):
    ok = p0 is not None and bool(p0) and p1 is not None and not bool(p1)     # vacuous (None) never behaves
    rows.append({"config": config, "check": cid, "wrong_build": wrong, "real": v0, "real_pass": p0, "wrong": v1,
                 "wrong_pass": p1, "behaves": ok, "note": note or ""})
    print("%-14s %-30s %-5s real %-12s wrong %-12s %s" % (config, cid, "OK" if ok else "BAD", v0, v1, wrong))
    sys.stdout.flush()


def config_path(checks_dir, config):
    return os.path.join(checks_dir, config if config.endswith(".json") else config + ".json")


def read_config(checks_dir, config):
    with open(config_path(checks_dir, config)) as fh:
        return json.load(fh)


def loader(checks_dir):
    def load(config):
        cfg = read_config(checks_dir, config)
        return cfg, mc.Ctx(cfg, os.path.dirname(os.path.abspath(config_path(checks_dir, config))))
    return load


def hard_ids(cfg):
    return [c.get("id") for c in cfg.get("checks", []) if c.get("severity") == "hard" and not c.get("skip")]


def load_cases(path):
    """Import the cases module; its folder goes on sys.path so it can import the material's own scripts."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec = importlib.util.spec_from_file_location("_wrong_build_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_report(out, rows, missing, not_hard, seconds):
    bad = [r for r in rows if not r["behaves"]]
    unc = {k: v for k, v in missing.items() if v}
    os.makedirs(out, exist_ok=True)
    lines = ["# Wrong builds: every hard check against its named wrong build", "",
             "%d cases, %d misbehave. Not covered: %s" % (len(rows), len(bad), json.dumps(unc) if unc else "none"), ""]
    if not_hard:
        lines += ["Skipped (check not hard in that config): %s" % ", ".join("%s/%s" % tuple(x) for x in not_hard), ""]
    lines += ["| config | hard check | wrong build | real | wrong | result |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s (%s) | %s (%s) | %s |" % (
            r["config"], r["check"], r["wrong_build"].replace("|", "/"), r["real"],
            "pass" if r["real_pass"] else ("FAIL" if r["real_pass"] is False else "vacuous"), r["wrong"],
            "pass" if r["wrong_pass"] else ("fail" if r["wrong_pass"] is False else "vacuous"),
            "OK" if r["behaves"] else "BAD"))
    with open(os.path.join(out, "wrong_builds.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(out, "wrong_builds.json"), "w") as fh:
        json.dump({"rows": rows, "missing": missing, "not_hard": not_hard, "seconds": seconds}, fh, indent=1,
                  default=lambda o: float(o) if isinstance(o, np.floating) else (bool(o) if isinstance(o, np.bool_) else str(o)))
    print("\n%d cases, %d misbehave; uncovered hard checks: %s" % (len(rows), len(bad), unc or "none"))
    return 1 if bad or unc else 0


def merge(parts, out):
    """--merge: one report from several --out folders, rows in the order given."""
    rows, missing, not_hard, seconds = [], {}, [], 0.0
    for d in parts:
        p = os.path.join(d, "wrong_builds.json")
        try:
            with open(p) as fh:
                r = json.load(fh)
            rows += list(r["rows"])
            for k, v in r["missing"].items():
                missing[k] = sorted(set(missing[k]) | set(v)) if k in missing else list(v)
            not_hard += list(r["not_hard"])
            seconds += float(r.get("seconds") or 0.0)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
            print("merge error: %s: %s" % (p, e), file=sys.stderr)
            return 2
    return write_report(out, rows, missing, not_hard, round(seconds, 1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cases", help="cases module (.py) defining CASES")
    ap.add_argument("--checks-dir", help="folder of the <config>.json files")
    ap.add_argument("--out", help="folder for wrong_builds.md and .json")
    ap.add_argument("--only", help="comma-separated configs, cross-case groups or check ids")
    ap.add_argument("--list", action="store_true", help="print the cases module's configs, groups and case count")
    ap.add_argument("--merge", nargs="+", metavar="DIR", help="merge the wrong_builds.json in these folders into --out")
    a = ap.parse_args(argv)
    if a.merge:
        if a.cases or a.list or a.only or not a.out:
            ap.error("--merge takes part folders and --out only")
        return merge(a.merge, a.out)
    if not a.cases:
        ap.error("the following arguments are required: --cases")
    if not a.list and not (a.checks_dir and a.out):
        ap.error("the following arguments are required: --checks-dir, --out")
    t0 = time.time()
    sys.modules.setdefault("wrong_builds", sys.modules[__name__])   # `import wrong_builds` in a cases module = this file
    try:
        mod = load_cases(a.cases)
        cases = [tuple(c) for c in mod.CASES]
        for i, c in enumerate(cases):
            if len(c) != 4 or not callable(c[3]):
                raise ValueError("CASES[%d] is not (config, check_id, wrong_build, edit)" % i)
        cross = dict(getattr(mod, "CROSS_CASES", {}))
        if not all(callable(f) for f in cross.values()):
            raise ValueError("CROSS_CASES maps a group name to fn(load)")
        extra = list(getattr(mod, "CONFIGS", []))
    except Exception as e:
        print("cases error: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    only = set(a.only.split(",")) if a.only else None
    want = lambda cfg, cid: only is None or cfg in only or cid in only
    configs = list(dict.fromkeys(extra + [c[0] for c in cases]))
    if a.list:
        try:
            print(json.dumps({"configs": configs, "groups": list(cross), "cases": len(cases),
                              "ids": sorted({c[1] for c in cases if isinstance(c[1], str)})}))
        except TypeError as e:  # a config or group name JSON cannot hold
            print("cases error: %s" % e, file=sys.stderr)
            return 2
        return 0
    load = loader(a.checks_dir)
    rows, missing, not_hard = [], {}, []
    for config in configs:
        try:
            cfg = read_config(a.checks_dir, config)
            checks = {c.get("id"): c for c in cfg.get("checks", [])}
        except (KeyError, ValueError, OSError) as e:
            print("config error: %s: %s" % (config, e), file=sys.stderr)
            return 2
        hard = [h for h in hard_ids(cfg) if want(config, h)]
        mine = [(cid, wrong, fn) for cf, cid, wrong, fn in cases if cf == config and want(config, cid)]
        if not hard and not mine:
            continue
        not_hard += [[config, cid] for cid, _, _ in mine if cid not in hard]
        mine = [m for m in mine if m[0] in hard]
        missing[config] = sorted(set(hard) - {m[0] for m in mine})
        if not mine:
            continue
        try:
            ctx = mc.Ctx(cfg, os.path.dirname(os.path.abspath(config_path(a.checks_dir, config))))
        except (mc.ConfigError, KeyError, ValueError, OSError) as e:
            print("config error: %s: %s" % (config, e), file=sys.stderr)
            return 2
        real = {}
        for cid, wrong, fn in mine:
            if cid not in real:
                real[cid] = run(ctx, checks[cid])
            p0, v0, n0 = real[cid]
            try:
                with Swap(ctx, fn(ctx)):
                    p1, v1, n1 = run(ctx, checks[cid])
            except Exception as e:  # a broken edit misbehaves; keep going
                p1, v1, n1 = None, None, "edit failed: %s: %s" % (type(e).__name__, e)
            record(rows, config, cid, wrong, p0, v0, p1, v1, n1 or n0)
        del ctx
    for group, fn in cross.items():
        if only is not None and group not in only:
            continue
        try:
            for cid, wrong, p0, p1, v0, v1 in fn(load):
                record(rows, group, cid, wrong, bool(p0), v0, bool(p1), v1, "")
        except Exception as e:
            record(rows, group, "(cross cases)", "", None, None, None, None, "failed: %s: %s" % (type(e).__name__, e))
    return write_report(a.out, rows, missing, not_hard, round(time.time() - t0, 1))


if __name__ == "__main__":
    sys.exit(main())
