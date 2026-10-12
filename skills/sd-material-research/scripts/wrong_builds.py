#!/usr/bin/env python3
"""Replay each hard check against its named wrong build: the check must pass the real maps and fail the wrong build
(references/checks.md, "Hard checks that can fail").

Usage:
    python wrong_builds.py --cases checks/wrong_build_cases.py --checks-dir checks --out review [--only id1,id2]
    python wrong_builds.py --cases checks/wrong_build_cases.py --list
    python wrong_builds.py --merge review/wb/classic review/wb/weathered ... --out review
    python wrong_builds.py --cases checks/wrong_build_cases.py --checks-dir checks --steer [--only id1,id2]
                           [--steer-out checks/steer_tests.json]

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

--list also prints "steer": [keys] (the STEER cases, "<check or name>@<config>").

STEER: may a measure steer a decision? The cases module may define STEER = [dict, ...]. A check may pick a seed, set a
calibration, decide a design option or gate an acceptance only after three tests (the --steer run makes them):
    null   on a control build that lacks the feature (the nowear compare render, an unworn preset, a no-op or pre-fix
           build) the check reads "feature absent" (a defect check passes, a check that asks for the feature misses),
           and the target is reachable (the clean build or a `reach` surrogate meets it);
    tell   a surrogate of the clean build with the fix's tell painted in scores worse (further from the target) than
           the clean build; both inside the target = the check cannot see the tell = fail;
    power  n >= 20 measured units, or a bootstrap 90 % interval of the stat narrower than the target band; a pixel
           statistic (no units) is "n/a" and passes.
One STEER case:
    {"config": <config name>, "check": <check id in that config>}                              a config check, or
    {"config": ..., "name": <id>, "measure": fn(ctx) -> {"value": float, "target": [lo, hi] (None = open end),
        "n": int|None, "samples": list|None, "stat": "median"|"mean"|"min"|"max"|"pNN"|None}}   a custom measure
    (a ladder stat, a seed-screen stat; it reads maps through `ctx`, so edits apply to it; call no wb.once() in it),
    plus  "tell": the tell in words,  "tell_edit": fn(ctx) -> edits (same shape as a wrong-build edit),
          "control": {"render": <compare render name>} (that render stands in as the main render) or
                     {"edit": fn(ctx) -> edits},   "expect_control": "pass" | "miss",
          optional "reach_edit": fn(ctx) -> edits, a surrogate that should meet a target the clean build misses.
A config check takes value, target and pass from matcheck's own check functions, as a wrong build does. Its n is the
unit count matcheck reports: components (components), per_element (elements), run_length (runs), height_diff with
local_mm (blocks), edge_profile (profiles), dispersion (features); every other type measures pixels (n None, "n/a").
Samples: a components check with a shape metric (aspect, fill, the outline metrics) reports its per-component values, and
its stat (config "stat", default median) is the bootstrap stat; every other type has none, so below 20 units it fails power.
A reading that is not a measurement is never evidence: a check that errors (a map that does not load, a bad config), a
vacuous one (matcheck's min_px: too few pixels or units) and a custom measure that raises or returns a wrong type (value,
n, samples, stat) make that build "failed" (value None). A failed control, tell or reach build fails its test; a failed
clean build fails null, tell and power. A NaN value stays a measurement: infinite distance. One exception: on the
control build a vacuous reading whose key set is empty (n_key 0, e.g. a lowfreq or shape-metric check keyed on the
feature, read on a build without it) means "feature absent": no value, infinite distance, a miss (not failed). A target
bound of +/-inf is an open end (None); a NaN bound or lo > hi is a bad measure; samples=[] with n None is n 0. Distance to target d(v) = 0 inside [lo, hi], else
the distance to the nearest bound (NaN or no value = infinite). Tests: clean value v0, d0; null.ok = (expect pass:
d(control) == 0; expect miss: d(control) > 0) and reachable (d0 == 0, or the reach build has d == 0); tell.ok =
d(tell build) > d0; power: n >= 20 ok, else with 8 or more samples (fewer: no evidence), a stat and a two-sided target the bootstrap (2000
resamples, numpy default_rng(0)) 90 % interval of the stat must be narrower than hi - lo (n None with samples counts
len(samples), so an empty list is 0 and fails), else n None and no samples is "n/a", anything else fails. Every test restores the maps first.
--steer runs only the STEER cases (--only filters by config or check/name) and writes --steer-out (default
<checks-dir>/steer_tests.json): {"utc", "cases": {"<check or name>@<config>": {tell, null, tell_test, power, ok, utc}}},
merged into an existing file (other keys kept; re-read and written under a lock file so parallel --only jobs lose nothing;
atomic write; a lock older than 30 s is taken over atomically, and a lock still held after 120 s is stolen with a
warning rather than the results being thrown away), and steer.md beside it. Exit 0 all ok, 1 any test not ok, 2 a config or cases module error, an unreadable
steer file, or an --only that matches no STEER case (or has any token that matches no STEER config or id). A plain run ignores STEER (suite.py is unchanged).

Cases modules `import wrong_builds as wb` for the edit helpers (paint, luma_shift, height_units, normal_from, stepped,
column_band, once) and `import matcheck as mc` for the region tools (mc.dilate, mc.erode, ...).
"""
import argparse
import importlib.util
import json
import math
import os
import sys
import time
import uuid

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


def column_band(a, amp=None, k=1):
    """The map with a cosine of k cycles per tile across U added to every row: a column band, the stripe that repeats
    with every tile (what a tile_harmonic check names as its wrong build). amp is in the map's own units; default 15 %
    of the map's p5-p95 range (all colour channels pooled), plainly visible. Clipped to 0-1 on a 0-1 map."""
    if amp is None:
        lo, hi = np.percentile(a[..., :3] if a.ndim == 3 else a, [5, 95])
        amp = 0.15 * float(hi - lo)
    band = amp * np.cos(2.0 * np.pi * k * np.arange(a.shape[1]) / a.shape[1])[None, :]
    band = band[..., None] if a.ndim == 3 else band
    out = a + band.astype(a.dtype)
    if a.ndim == 3 and a.shape[2] == 4:
        out[..., 3] = a[..., 3]                                   # alpha stays
    return np.clip(out, 0.0, 1.0) if a.max() <= 1.0 else out


def once(ctx, key, fn):
    """fn() computed once per loaded config, for inputs several edits share (distance maps, region medians)."""
    memo = ctx.__dict__.setdefault("_wb_once", {})
    if key not in memo:
        memo[key] = fn()
    return memo[key]


# ----------------------------------------------------------------------------- harness

def units_of(c, det):
    """The number of measured units behind a config check's value, from matcheck's own result: components (components),
    per_element (elements), run_length (runs), height_diff with local_mm (blocks), and any check that reports
    n_key_unit (edge_profile profiles, dispersion features). None for the rest: they measure pixels."""
    det = det or {}
    t = c.get("type")
    n = None
    if t == "components":
        n = det.get("components")
    elif t == "per_element":
        n = det.get("elements")
    elif t == "run_length":
        n = (det.get("runs_mm") or {}).get("n")
    elif t == "height_diff":
        n = (det.get("local_diff_mm") or {}).get("n") if c.get("local_mm") else None
    elif det.get("n_key_unit") and det.get("n_key_unit") != "px":
        n = det.get("n_key")
    return int(n) if n is not None else None


STEER_STATS = ("median", "mean", "min", "max")


def valid_stat(s):
    return isinstance(s, str) and (s in STEER_STATS or (s.startswith("p") and s[1:].replace(".", "", 1).isdigit()))


def steer_stat(c, default=None):
    s = c.get("stat", default)
    return s if valid_stat(s) else None


def measure_check(ctx, c):
    """One config check through matcheck's own functions: the helper wrong builds and STEER tests share."""
    r = mc.run_check(ctx, c)
    t = r.get("target")
    det = r.get("details") or {}
    note = r.get("note")
    samples, stat = None, steer_stat(c)
    if c.get("type") == "components" and det.get("samples") is not None:     # the only type that reports its units' values
        samples, stat = list(det["samples"]), steer_stat(c, "median")
    return {"value": r.get("value"), "target": list(t) if t is not None else None, "passed": r.get("passed"),
            "note": note or r.get("error"), "error": r.get("error"),
            "vacuous": isinstance(note, str) and note.startswith("vacuous"), "n_key": det.get("n_key"),
            "n": units_of(c, det),
            "samples": samples, "stat": stat}


def run(ctx, c):
    m = measure_check(ctx, c)
    v = m["value"]
    return m["passed"], (round(v, 6) if isinstance(v, float) and math.isfinite(v) else v), m["note"]


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


# ----------------------------------------------------------------------------- STEER: may a measure steer a decision?

STEER_MIN_N = 20
STEER_MIN_BOOT = 8   # (est.) below this a bootstrap interval has almost no width whatever the spread: no evidence
STEER_BOOT = 2000


class MainAs:
    """Temporarily make a comparison render the main render (a control build read through the same check)."""

    def __init__(self, ctx, name):
        self.ctx, self.name, self.saved = ctx, name, None

    def __enter__(self):
        R = self.ctx.render(self.name)
        self.saved, self.ctx.main = self.ctx.main, R
        flush(self.ctx)
        return self

    def __exit__(self, *a):
        if self.saved is not None:
            self.ctx.main = self.saved
        flush(self.ctx)


class Isolated:
    """Whatever a measure memoises with once() under an edit must not outlive it."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.keys = set()

    def __enter__(self):
        self.keys = set(self.ctx.__dict__.get("_wb_once", {}))
        return self

    def __exit__(self, *a):
        memo = self.ctx.__dict__.get("_wb_once")
        if memo:
            for k in [k for k in memo if k not in self.keys]:
                del memo[k]


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def num(v):
    """JSON-safe number: numpy scalars to Python, NaN and inf to None."""
    if isinstance(v, (np.floating, np.integer)):
        v = v.item()
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def distance(v, target):
    """0 inside [lo, hi] (None = open end), else the distance to the nearest bound; no value or NaN = infinite."""
    if v is None or target is None:
        return float("inf")
    v = float(v)
    if math.isnan(v):
        return float("inf")
    lo, hi = target
    if lo is not None and v < lo:
        return float(lo) - v
    if hi is not None and v > hi:
        return v - float(hi)
    return 0.0


def stat_rows(S, stat):
    """The stat of every row of S (resamples x n)."""
    if stat == "median":
        return np.median(S, axis=1)
    if stat == "mean":
        return S.mean(axis=1)
    if stat == "min":
        return S.min(axis=1)
    if stat == "max":
        return S.max(axis=1)
    if stat.startswith("p"):
        return np.percentile(S, float(stat[1:]), axis=1)
    raise ValueError("unknown stat '%s'" % stat)


def bootstrap_interval(samples, stat, resamples=STEER_BOOT, level=90.0):
    """Percentile bootstrap interval (numpy default_rng(0)) of the stat of the samples."""
    x = np.asarray(samples, dtype=np.float64).ravel()
    x = x[np.isfinite(x)]
    if x.size < 2:
        raise ValueError("fewer than 2 finite samples")
    idx = np.random.default_rng(0).integers(0, x.size, size=(resamples, x.size))
    st = stat_rows(x[idx], stat)
    tail = (100.0 - level) / 2.0
    return float(np.percentile(st, tail)), float(np.percentile(st, 100.0 - tail))


def steer_id(s):
    return s.get("check") if s.get("check") is not None else s.get("name")


def steer_key(s):
    return "%s@%s" % (steer_id(s), s.get("config"))


def validate_steer(steer):
    """-> list of case dicts; ValueError names the first malformed one."""
    out, seen = [], set()
    for i, s in enumerate(steer):
        if not isinstance(s, dict):
            raise ValueError("STEER[%d] is not a dict" % i)
        for k in ("config", "tell", "tell_edit", "control", "expect_control"):
            if k not in s:
                raise ValueError("STEER[%d] has no '%s'" % (i, k))
        if not isinstance(s["config"], str):
            raise ValueError("STEER[%d]: config must be a string" % i)
        if ("check" in s) == ("measure" in s):
            raise ValueError("STEER[%d]: give either check (a config check) or name and measure (a custom measure)" % i)
        if "check" in s:
            if not isinstance(s["check"], str) or "name" in s:
                raise ValueError("STEER[%d]: check must be a check id string, with no name" % i)
        elif not isinstance(s.get("name"), str) or not callable(s["measure"]):
            raise ValueError("STEER[%d]: a custom measure needs name (string) and measure fn(ctx)" % i)
        if not callable(s["tell_edit"]):
            raise ValueError("STEER[%d]: tell_edit must be fn(ctx) -> edits" % i)
        if s.get("reach_edit") is not None and not callable(s["reach_edit"]):
            raise ValueError("STEER[%d]: reach_edit must be fn(ctx) -> edits" % i)
        if s["expect_control"] not in ("pass", "miss"):
            raise ValueError("STEER[%d]: expect_control must be 'pass' or 'miss'" % i)
        ctl = s["control"]
        if (not isinstance(ctl, dict) or ("render" in ctl) == ("edit" in ctl)
                or ("render" in ctl and not isinstance(ctl["render"], str))
                or ("edit" in ctl and not callable(ctl["edit"]))):
            raise ValueError("STEER[%d]: control is {\"render\": name} or {\"edit\": fn(ctx) -> edits}" % i)
        key = steer_key(s)
        if key in seen:
            raise ValueError("STEER[%d]: duplicate case %s" % (i, key))
        seen.add(key)
        out.append(s)
    return out


def is_real(x):
    return isinstance(x, (int, float, np.integer, np.floating)) and not isinstance(x, (bool, np.bool_))


def clean_measure(m):
    """A custom measure's output, type-checked and normalised (Python floats and ints): ValueError names the problem."""
    if not isinstance(m, dict) or "value" not in m or "target" not in m:
        raise ValueError("measure(ctx) must return a dict with value and target")
    v = m["value"]
    if v is not None and not is_real(v):
        raise ValueError("measure value must be a number or None, got %s" % type(v).__name__)
    t = m["target"]
    if t is not None:
        if not isinstance(t, (list, tuple)) or len(t) != 2 or any(x is not None and not is_real(x) for x in t):
            raise ValueError("measure target must be [lo, hi] (numbers, None = open end)")
        t = [None if x is None else float(x) for x in t]
        if any(x is not None and math.isnan(x) for x in t):
            raise ValueError("measure target must not have a NaN bound (None = open end)")
        t = [None if x is not None and math.isinf(x) else x for x in t]       # +/-inf is an open end
        if t[0] is not None and t[1] is not None and t[0] > t[1]:
            raise ValueError("measure target must have lo <= hi, got [%s, %s]" % (t[0], t[1]))
    n = m.get("n")
    if n is not None and (not isinstance(n, (int, np.integer)) or isinstance(n, (bool, np.bool_)) or n < 0):
        raise ValueError("measure n must be a non-negative integer or None, got %r" % (n,))
    samples = m.get("samples")
    if samples is not None:
        flat = list(np.asarray(samples, dtype=object).ravel()) if hasattr(samples, "__len__") and not isinstance(
            samples, (str, bytes, dict)) else None
        if flat is None or not all(is_real(x) for x in flat):
            raise ValueError("measure samples must be a list of numbers or None")
        samples = [float(x) for x in flat]
        if not samples and n is None:
            n = 0                       # an empty samples list is zero units, not a pixel statistic
    stat = m.get("stat")
    if stat is not None and not valid_stat(stat):
        raise ValueError("measure stat must be median, mean, min, max, pNN or None, got %r" % (stat,))
    return {"value": None if v is None else float(v), "target": t, "n": None if n is None else int(n),
            "samples": samples, "stat": stat, "error": None}


def steer_measure(ctx, s, c, control=False):
    """The case's measurement on the maps as they stand: {value, target, n, samples, stat, error}. An error, an
    exception or a vacuous reading (matcheck's min_px) is never a measurement: failed True, value None, error says why
    (a NaN value is a measurement, of infinite distance). One exception, on the control build only (control True): a
    vacuous reading whose key set is empty (n_key 0) is the feature being absent, which is what a control is for: no
    value (infinite distance, a miss), absent True, not failed."""
    try:
        if "measure" in s:
            return clean_measure(s["measure"](ctx))
        m = measure_check(ctx, c)
        if m["vacuous"] and control and not m["error"] and m.get("n_key") == 0:
            m.update(failed=False, absent=True, error=None, raw_value=m["value"], value=None)
            return m
        rv = m["value"]
        clause = ("the value %s rests on" % fv(rv)) if (rv is not None and not (isinstance(rv, float) and math.isnan(rv))) \
            else "no measurement rests on"
        why = m["error"] or (("vacuous reading (%s): %s too few pixels or units to be a measurement" % (m["note"], clause))
                             if m["vacuous"] else None)
        if why:
            m.update(failed=True, error=why, raw_value=m["value"], value=None)
        return m
    except Exception as e:
        return {"value": None, "target": None, "n": None, "samples": None, "stat": None, "failed": True,
                "error": "%s: %s" % (type(e).__name__, e)}


def build_value(ctx, s, c, fn=None, render=None, control=False):
    """Measure a build made by edit function fn (called on the clean maps) or by comparison render `render`; the
    maps are back as they were afterwards. -> measurement dict (failed True and error set when the edit or the measure
    raised: a failed build is never evidence either way)."""
    try:
        edits = []
        if render is None:
            edits = list(fn(ctx))
    except Exception as e:
        return {"value": None, "failed": True, "error": "edit failed: %s: %s" % (type(e).__name__, e)}
    try:
        with Isolated(ctx):
            if render is not None:
                with MainAs(ctx, render):
                    return steer_measure(ctx, s, c, control)
            with Swap(ctx, edits):
                return steer_measure(ctx, s, c, control)
    except Exception as e:
        return {"value": None, "failed": True, "error": "%s: %s" % (type(e).__name__, e)}


def fv(v):
    return "no value" if v is None or (isinstance(v, float) and math.isnan(v)) else "%.4g" % v


def ft(t):
    return "no target" if t is None else "[%s, %s]" % tuple("-" if x is None else "%.4g" % x for x in t)


def power_test(m):
    n, samples, stat, target = m.get("n"), m.get("samples"), m.get("stat"), m.get("target")
    if n is None and samples is not None:
        n = len(samples)
    out = {"n": n, "stat": stat}
    if n is not None and n >= STEER_MIN_N:
        out.update(ok=True, reason="n = %d >= %d units" % (n, STEER_MIN_N))
        return out
    if n is None:
        out.update(ok=True, reason="n/a: a pixel statistic (no units)")
        return out
    have = samples is not None and len(samples) > 0
    two_sided = target is not None and target[0] is not None and target[1] is not None
    if not have or not stat:
        out.update(ok=False, reason="n = %s < %d units and %s to bootstrap" % (
            n, STEER_MIN_N, "no samples" if not have else "no stat"))
    elif not two_sided:
        out.update(ok=False, reason="n = %s < %d units; a one-sided target has no band to bootstrap against"
                   % (n, STEER_MIN_N))
    elif len(samples) < STEER_MIN_BOOT:
        out.update(ok=False, reason="n = %s < %d units and %d samples < %d: too few to bootstrap" % (
            n, STEER_MIN_N, len(samples), STEER_MIN_BOOT))
    else:
        try:
            lo, hi = bootstrap_interval(samples, stat)
        except ValueError as e:
            out.update(ok=False, reason="n = %s < %d units; bootstrap: %s" % (n, STEER_MIN_N, e))
            return out
        width, band = hi - lo, float(target[1]) - float(target[0])
        out.update(ci=[lo, hi], width=width, band=band, ok=bool(width < band))
        out["reason"] = "n = %s < %d units; bootstrap 90%% interval of the %s [%.4g, %.4g] is %s the %.4g target band" % (
            n, STEER_MIN_N, stat, lo, hi, "narrower than" if width < band else "not narrower than", band)
    return out


def steer_case(ctx, s, c):
    """The three tests for one case -> the report entry."""
    m0 = steer_measure(ctx, s, c)
    target, v0 = m0["target"], m0["value"]
    d0 = distance(v0, target)
    entry = {"tell": s["tell"], "config": s["config"], "check": steer_id(s), "target": target, "stat": m0.get("stat")}
    # null: the control reads "feature absent", and the target is reachable
    ctl, exp = s["control"], s["expect_control"]
    mc_ = build_value(ctx, s, c, ctl.get("edit"), render=ctl.get("render"), control=True)
    vc = mc_["value"]
    dc = distance(vc, target)
    ctl_ok = ((dc == 0.0) if exp == "pass" else (dc > 0.0)) and not mc_.get("failed")
    reasons, reach_d, reach_v = [], None, None
    if m0.get("failed"):
        reasons.append("clean build measurement failed: %s" % m0["error"])
    elif target is None:
        reasons.append("no target to test: the measure gave none")
    if mc_.get("failed"):
        reasons.append("control build failed: %s" % mc_["error"])
    if not ctl_ok and not mc_.get("failed"):
        reasons.append("control %s the target (%s against %s) but should %s" % (
            "misses" if exp == "pass" else "meets", fv(vc), ft(target),
            "meet it (a defect check passes on a build without the feature)" if exp == "pass"
            else "miss it (a check that asks for the feature misses on a build without it)"))
    reachable = d0 == 0.0 and not m0.get("failed")
    if not reachable and not m0.get("failed") and s.get("reach_edit") is not None:
        mr = build_value(ctx, s, c, s["reach_edit"])
        reach_v, reach_d = mr["value"], distance(mr["value"], target)
        reachable = reach_d == 0.0 and not mr.get("failed")
        if mr.get("failed"):
            reasons.append("reach build failed: %s" % mr["error"])
    if not reachable and not m0.get("failed"):
        reasons.append("unreachable: the clean build reads %s against %s%s" % (
            fv(v0), ft(target), (" and the reach build %s" % fv(reach_v)) if reach_d is not None else ""))
    null_ok = ctl_ok and reachable and target is not None
    entry["null"] = {
        "ok": bool(null_ok), "expect_control": exp, "v0": num(v0), "d0": num(d0), "control": num(vc),
        "d_control": num(dc), "reachable": bool(reachable), "reach_value": num(reach_v), "reach_d": num(reach_d),
        "reason": "; ".join(reasons) if reasons else "control %s (%s against %s); target %s" % (
            "passes" if exp == "pass" else "misses", fv(vc), ft(target),
            "met by the clean build" if d0 == 0.0 else "met by the reach build") + (
            "; the control's key set is empty (%s): the feature is absent" % mc_["note"] if mc_.get("absent") else "")}
    # tell: the build with the fix's tell scores worse than the clean build
    mt = build_value(ctx, s, c, s["tell_edit"])
    vt = mt["value"]
    dt = distance(vt, target)
    if mt.get("failed"):
        why = "tell build failed: %s" % mt["error"]
    elif dt > d0:
        why = "tell build reads %s, further from %s than the clean build (%s)" % (fv(vt), ft(target), fv(v0))
    elif d0 == 0.0 and dt == 0.0:
        why = "the check cannot see the tell: both inside %s (clean %s, tell build %s)" % (ft(target), fv(v0), fv(vt))
    else:
        why = "the tell build scores no worse than the clean build: %s against %s, clean %s" % (fv(vt), ft(target), fv(v0))
    entry["tell_test"] = {"ok": bool(dt > d0 and not mt.get("failed") and not m0.get("failed")), "v0": num(v0),
                          "d0": num(d0), "tell_value": num(vt), "d_tell": num(dt), "reason": why}
    entry["power"] = power_test(m0) if not m0.get("failed") else {
        "n": None, "stat": m0.get("stat"), "ok": False, "reason": "the clean build's measurement failed: %s" % m0["error"]}
    entry["ok"] = bool(entry["null"]["ok"] and entry["tell_test"]["ok"] and entry["power"]["ok"])
    entry["utc"] = utc_now()
    return entry


STEER_TESTS = (("null", "null"), ("tell_test", "tell"), ("power", "power"))


def write_atomic(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = "%s.tmp%d" % (path, os.getpid())
    with open(tmp, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def json_safe(o):
    """The document with every NaN or infinite number as None and numpy scalars as Python ones (valid JSON)."""
    if isinstance(o, dict):
        return {k: json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v) for v in o]
    if isinstance(o, np.ndarray):
        return json_safe(o.tolist())
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        o = o.item()
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def json_default(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if not math.isfinite(float(o)) else float(o)
    return str(o)


class FileLock:
    """Exclusive lock file (O_EXCL, portable). The hold time is milliseconds, so a lock older than `stale` seconds belongs
    to a dead process: it is taken over atomically (renamed to a unique name, which one waiter wins; a rename that caught
    a lock created meanwhile by another is put back). A lock still held after `timeout` seconds is stolen when `steal`
    (self.stolen True) so a caller's results are never discarded, else OSError. The lock holds a token of its owner, and
    __exit__ removes only a lock that still carries it."""

    def __init__(self, path, timeout=120.0, stale=30.0, steal=True):
        self.path, self.timeout, self.stale, self.steal = path, timeout, stale, steal
        self.token = "%d.%s" % (os.getpid(), uuid.uuid4().hex)
        self.stolen = False

    def _read(self):
        try:
            with open(self.path) as fh:
                return fh.read()
        except OSError:
            return None

    def _take_over(self, seen):
        """Remove the lock whose content was `seen` (None = whatever is there, forced); True if that lock was removed."""
        grave = "%s.dead.%s" % (self.path, self.token)
        try:
            os.rename(self.path, grave)
        except OSError:
            return False                                  # someone else removed it first
        try:
            with open(grave) as fh:
                got = fh.read()
        except OSError:
            got = None
        if seen is not None and got != seen:              # we caught a fresh lock another waiter just made: put it back
            try:
                os.link(grave, self.path)
            except OSError:
                pass
            got = None
        try:
            os.remove(grave)
        except OSError:
            pass
        return got is not None or seen is None

    def __enter__(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        t0 = time.time()
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, self.token.encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    seen = self._read()
                    if seen is not None and time.time() - os.path.getmtime(self.path) > self.stale:
                        self._take_over(seen)
                        continue
                except OSError:
                    continue
                if time.time() - t0 > self.timeout:
                    if not self.steal:
                        raise OSError("timed out waiting for %s (another --steer run holds it)" % self.path)
                    self.stolen = True
                    self._take_over(None)
                    t0 = time.time()
                    continue
                time.sleep(0.05)

    def __exit__(self, *a):
        if self._read() == self.token:
            try:
                os.remove(self.path)
            except OSError:
                pass


def steer_markdown(cases):
    bad = [k for k, v in cases.items() if not v.get("ok")]
    lines = ["# Steer tests: may the measure steer a decision?", "",
             "%d cases, %d not ok. A measure may pick a seed, set a calibration, decide a design option or gate an "
             "acceptance only when null, tell and power all pass." % (len(cases), len(bad)), "",
             "| case | tell | null | tell test | power | ok |", "|---|---|---|---|---|---|"]
    for k, v in cases.items():
        cell = lambda t, v=v: "ok" if (v.get(t) or {}).get("ok") else "FAIL"
        lines.append("| %s | %s | %s | %s | %s | %s |" % (k, str(v.get("tell", "")).replace("|", "/"), cell("null"),
                                                           cell("tell_test"), cell("power"), "ok" if v.get("ok") else "FAIL"))
    for k, v in cases.items():
        lines += ["", "## %s" % k, "", "- tell: %s" % v.get("tell", ""),
                  "- target: %s, stat: %s" % (ft(v.get("target")), v.get("stat") or "-")]
        for t, label in STEER_TESTS:
            r = v.get(t) or {}
            lines.append("- %s: %s. %s" % (label, "ok" if r.get("ok") else "FAIL", r.get("reason", "")))
        lines.append("- run: %s" % v.get("utc", ""))
    return "\n".join(lines) + "\n"


def read_steer_file(path):
    """-> dict (empty when the file is absent); ValueError when it exists but is not a steer file."""
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        d = json.load(fh)
    if not isinstance(d, dict) or not isinstance(d.get("cases", {}), dict):
        raise ValueError("%s is not a steer_tests.json (an object with a cases object)" % path)
    return d


def steer_run(a, mod, want):
    """--steer: run the STEER cases, merge them into --steer-out. Exit code."""
    t0 = time.time()
    try:
        cases = validated = validate_steer(list(getattr(mod, "STEER", [])))
    except Exception as e:
        print("cases error: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    cases = [s for s in cases if want(s["config"], steer_id(s))]
    if not cases:
        print("no STEER case matches%s (--list shows the keys)" % (" --only %s" % a.only if a.only else ""), file=sys.stderr)
        return 2
    if a.only:
        known = {s["config"] for s in validated} | {steer_id(s) for s in validated}
        unmatched = [t for t in a.only.split(",") if t not in known]
        if unmatched:
            print("--only %s matches no STEER config or id (--list shows the keys); nothing run"
                  % ", ".join(repr(t) for t in unmatched), file=sys.stderr)
            return 2
    out_path = a.steer_out or os.path.join(a.checks_dir, "steer_tests.json")
    try:
        existing = read_steer_file(out_path)
    except (OSError, ValueError) as e:
        print("steer file error: %s" % e, file=sys.stderr)
        return 2
    cfgs, order = {}, []
    for s in cases:
        if s["config"] not in cfgs:
            try:
                cfgs[s["config"]] = read_config(a.checks_dir, s["config"])
            except (KeyError, ValueError, OSError) as e:
                print("config error: %s: %s" % (s["config"], e), file=sys.stderr)
                return 2
            order.append(s["config"])
        if "check" in s and s["check"] not in {c.get("id") for c in cfgs[s["config"]].get("checks", [])}:
            print("config error: %s has no check '%s'" % (s["config"], s["check"]), file=sys.stderr)
            return 2
    results = {}
    for config in order:
        cfg = cfgs[config]
        try:
            ctx = mc.Ctx(cfg, os.path.dirname(os.path.abspath(config_path(a.checks_dir, config))))
        except (mc.ConfigError, KeyError, ValueError, OSError) as e:
            print("config error: %s: %s" % (config, e), file=sys.stderr)
            return 2
        checks = {c.get("id"): c for c in cfg.get("checks", [])}
        for s in cases:
            if s["config"] != config:
                continue
            try:
                entry = steer_case(ctx, s, checks.get(s.get("check")))
            except Exception as e:      # a case that crashes is a case that is not ok, not a run without a report
                why = "steer case crashed: %s: %s" % (type(e).__name__, e)
                entry = {"tell": s["tell"], "config": s["config"], "check": steer_id(s), "target": None, "stat": None,
                         "null": {"ok": False, "reason": why}, "tell_test": {"ok": False, "reason": why},
                         "power": {"ok": False, "n": None, "stat": None, "reason": why}, "ok": False, "utc": utc_now()}
            results[steer_key(s)] = entry
            print("%-40s %-4s null %-4s tell %-4s power %-4s %s" % (
                steer_key(s), "OK" if entry["ok"] else "BAD", "ok" if entry["null"]["ok"] else "FAIL",
                "ok" if entry["tell_test"]["ok"] else "FAIL", "ok" if entry["power"]["ok"] else "FAIL", s["tell"]))
            sys.stdout.flush()
        del ctx
    try:
        with FileLock(out_path + ".lock") as lock:      # parallel --only jobs share one file: read, merge and write under the lock
            if lock.stolen:
                print("warning: the lock %s.lock was still held after %.0f s and was taken over" % (out_path, lock.timeout),
                      file=sys.stderr)
            doc = dict(read_steer_file(out_path))
            merged = dict(doc.get("cases", {}))
            merged.update(results)
            doc["utc"] = utc_now()
            doc["cases"] = merged
            write_atomic(out_path, json.dumps(json_safe(doc), indent=1, default=json_default, allow_nan=False) + "\n")
            write_atomic(os.path.join(os.path.dirname(os.path.abspath(out_path)), "steer.md"), steer_markdown(merged))
    except (OSError, ValueError) as e:
        print("steer file error: %s" % e, file=sys.stderr)
        return 2
    bad = [k for k, v in results.items() if not v["ok"]]
    print("\n%d steer cases, %d not ok (%.1f s) -> %s" % (len(results), len(bad), time.time() - t0, out_path))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cases", help="cases module (.py) defining CASES")
    ap.add_argument("--checks-dir", help="folder of the <config>.json files")
    ap.add_argument("--out", help="folder for wrong_builds.md and .json")
    ap.add_argument("--only", help="comma-separated configs, cross-case groups or check ids")
    ap.add_argument("--list", action="store_true", help="print the cases module's configs, groups and case count")
    ap.add_argument("--merge", nargs="+", metavar="DIR", help="merge the wrong_builds.json in these folders into --out")
    ap.add_argument("--steer", action="store_true", help="run only the cases module's STEER cases (null, tell, power)")
    ap.add_argument("--steer-out", help="steer_tests.json to merge the results into (default <checks-dir>/steer_tests.json)")
    a = ap.parse_args(argv)
    if a.merge:
        if a.cases or a.list or a.only or a.steer or a.steer_out or not a.out:
            ap.error("--merge takes part folders and --out only")
        return merge(a.merge, a.out)
    if not a.cases:
        ap.error("the following arguments are required: --cases")
    if a.steer_out and not a.steer:
        ap.error("--steer-out needs --steer")
    if a.steer and (a.list or a.out):
        ap.error("--steer takes --checks-dir, --only and --steer-out (not --list or --out)")
    if a.steer and not a.checks_dir:
        ap.error("the following arguments are required: --checks-dir")
    if not a.list and not a.steer and not (a.checks_dir and a.out):
        ap.error("the following arguments are required: --checks-dir, --out")
    t0 = time.time()
    sys.modules.setdefault("wrong_builds", sys.modules[__name__])   # `import wrong_builds` in a cases module = this file
    try:
        mod = load_cases(a.cases)
        if not hasattr(mod, "CASES") and not (hasattr(mod, "STEER") and (a.steer or a.list)):
            raise AttributeError("the cases module defines no CASES")
        cases = [tuple(c) for c in getattr(mod, "CASES", [])]
        for i, c in enumerate(cases):
            if len(c) != 4 or not callable(c[3]):
                raise ValueError("CASES[%d] is not (config, check_id, wrong_build, edit)" % i)
        cross = dict(getattr(mod, "CROSS_CASES", {}))
        if not all(callable(f) for f in cross.values()):
            raise ValueError("CROSS_CASES maps a group name to fn(load)")
        extra = list(getattr(mod, "CONFIGS", []))
        steer = validate_steer(list(getattr(mod, "STEER", []))) if (a.list or a.steer) else []
    except Exception as e:
        print("cases error: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    only = set(a.only.split(",")) if a.only else None
    want = lambda cfg, cid: only is None or cfg in only or cid in only
    if a.steer:
        return steer_run(a, mod, want)
    configs = list(dict.fromkeys(extra + [c[0] for c in cases]))
    if a.list:
        try:
            print(json.dumps({"configs": configs, "groups": list(cross), "cases": len(cases),
                              "ids": sorted({c[1] for c in cases if isinstance(c[1], str)}),
                              "steer": [steer_key(s) for s in steer]}))
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
