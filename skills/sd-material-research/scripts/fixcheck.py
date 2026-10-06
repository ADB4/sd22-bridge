#!/usr/bin/env python3
"""Re-measure every acceptance check in a fix ledger and say which fixes landed (references/review.md §1 step 4).
How to use it: references/checks.md, "Fixcheck". This docstring is the reference.

Usage:
    python fixcheck.py --ledger <tools>/review/round<N>/ledger.json [--scorecards DIR] [--checks-dir DIR] [--out DIR]
                       [--rerun] [--python PY]

Options:
    --ledger      the fix ledger (review.md §1 step 4): items[].id, status (done, partial, not_done), title and
                  acceptance[].check, variant, target ([lo, hi], null = an open end), before, after
    --scorecards  folder of scorecard_<variant>.json (default: the ledger's folder, where the suite writes them)
    --checks-dir  folder of the checks configs (default: <tools>/checks, tools = the ledger's ../..)
    --out         fixcheck/ is written here (default: the ledger's folder)
    --rerun       re-run matcheck for every variant, fresh scorecard or not
    --python      the python matcheck runs under (default: this one; it needs numpy, so start fixcheck with $PY)
The configs are <checks-dir>/*.json with a `checks` list, each named by its `variant` (else its file stem); two
configs with a variant the ledger names are an error. For each variant a ledger row names, the values come from
<scorecards>/scorecard_<variant>.json when it is fresh: its manifest `exported_at` equals the config's current export
manifest, it is newer than that manifest, than each `compare` render's manifest and than the config, and it has a row
for every id. Otherwise (or with --rerun) fixcheck runs `matcheck.py <config> --only <the ledger's ids for that
variant>` into <out>/fixcheck/<variant>/ and reads that; matcheck's exit 0, 1 or 3 with a scorecard is a measure.
Row status:
    holds        meets the target
    drifted      meets it, but the ledger's `after` is off by more than max(half a unit of its last recorded digit,
                 1 % of |after|): the ledger number is stale
    misses       fails the target
    no_after     the ledger has no measured `after` (not landed, review.md §1); the re-measure is still reported
    no_target    neither the row nor the check has a target, so nothing can judge the value
    no_check     the id is not a check in that variant's config, or the check is skipped: it cannot be re-measured
    unmeasured   the check errored or was vacuous, matcheck wrote no scorecard, or the value is NaN or not a number
    no_variant   no config has that variant (or the row names none)
The target is the row's [lo, hi] (null = an open end); without one, the check's own pass/fail. An item landed when it
has rows and every row holds or drifted. Flags, per item and listed at the top of fixcheck.json:
    done_not_landed     status done, but the item did not land
    claim_contradicted  the ledger's `after` meets the target, the re-measure misses it
    measure_failed      a variant the item's rows read could not be re-measured: matcheck did not start, crashed,
                        timed out (900 s), exited 2 (config error) or another code without a scorecard, or wrote none
                        or an unreadable one. Its rows are unmeasured; fix the config or the export and run again.
partial and not_done items are reported, not failed (unless measure_failed).
Writes fixcheck.json and fixcheck.md in <out>/fixcheck/ (a folder of its own: a panel lens keyed fixcheck writes
round<N>/fixcheck.json); both are deleted first, so a failed run leaves none. fixcheck.json: rc, counts {status: n},
landed, not_landed, done_not_landed [item ids], claim_contradicted [{item, check, variant}], measure_failed [{variant,
error}], measured {variant: {source scorecard or rerun, scorecard, config, why, rc, argv, seconds, error}}, warnings,
items [{id, title, status, verdict landed or not_landed, flags, note, rows [{check, variant, target, target_from,
before, after, value, meets, after_meets, tolerance, status, note, claim_contradicted}]}], plus ledger, checks_dir,
scorecards, out, rerun, python, started, seconds. Standard library only, Python 3.7 or newer: matcheck runs in a
subprocess under --python, which needs numpy (the analysis venv).
Exit code: 0 no flag; 1 a done_not_landed, claim_contradicted or measure_failed; 2 a usage, checks-dir or ledger error
(nothing written).
"""
import argparse
import datetime
import json
import math
import os
import re
import subprocess
import sys
import time

if sys.version_info < (3, 7):  # before anything an older Python cannot run; the file parses on 3.5 or newer
    sys.stderr.write("fixcheck.py needs Python 3.7 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
MATCHECK = os.path.join(HERE, "matcheck.py")
STATUSES = ("holds", "drifted", "misses", "no_after", "no_target", "no_check", "unmeasured", "no_variant")
ITEM_STATUSES = ("done", "partial", "not_done")
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS")
TIMEOUT = 900  # seconds per matcheck run
SLACK = 1e-12  # matcheck.evaluate's


class Fail(Exception):
    pass


class Num(float):
    """A ledger number that keeps its text: the drift tolerance needs the last recorded digit."""

    def __new__(cls, text):
        x = float.__new__(cls, text)
        x.text = text
        return x


# ----------------------------------------------------------------------------- small helpers


def load_json(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def plain(v):
    """Ledger values back to plain JSON types (no NaN: it is not JSON)."""
    if isinstance(v, Num):
        return int(v) if re.fullmatch(r"-?\d+", v.text) else float(v) if math.isfinite(v) else v.text
    if isinstance(v, float) and not math.isfinite(v):
        return str(v)
    if isinstance(v, list):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    return v


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, Num):
        return v.text
    if isinstance(v, float):
        return "%g" % v
    if isinstance(v, (list, dict)):
        return json.dumps(plain(v))
    return str(v)


def fmt_target(t):
    lo, hi = t
    if lo is None and hi is None:
        return "open"
    if lo is None:
        return "<= %s" % fmt(hi)
    if hi is None:
        return ">= %s" % fmt(lo)
    return "%s .. %s" % (fmt(lo), fmt(hi))


def cell(s):
    return " ".join(str(s).split()).replace("|", "/")


def rel(path, base):
    path = os.path.abspath(path)
    r = os.path.relpath(path, base)
    return path if r.startswith("..") else r


def safe(name):
    s = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return "_" + s if s in ("", ".", "..") else s


def remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def is_target(t):
    return (isinstance(t, (list, tuple)) and len(t) == 2 and all(v is None or number(v) for v in t)
            and (t[0] is None or t[1] is None or t[0] <= t[1]))


def meets(value, target):
    lo, hi = target
    return (lo is None or value >= lo - SLACK) and (hi is None or value <= hi + SLACK)


def half_unit(v):
    """Half a unit of the last digit as the number was written (0.40 -> 0.005, 12 -> 0.5, 1.5e-05 -> 5e-07)."""
    m = re.fullmatch(r"-?\d*(?:\.(\d*))?(?:[eE]([+-]?\d+))?", getattr(v, "text", None) or repr(float(v)))
    return 0.5 * 10.0 ** (int(m.group(2) or 0) - len(m.group(1) or "")) if m else 0.0


# ----------------------------------------------------------------------------- inputs


def read_ledger(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            led = json.load(fh, parse_float=Num, parse_int=Num)
    except OSError as e:
        raise Fail("%s: %s" % (path, e.strerror or e))
    except ValueError as e:
        raise Fail("%s: invalid JSON: %s" % (path, e))
    if not isinstance(led, dict) or not isinstance(led.get("items"), list):
        raise Fail("%s: not an object with an items list (review.md §1 step 4)" % path)
    errs, ids = [], set()
    for i, it in enumerate(led["items"]):
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            errs.append("item %d: needs a string id" % (i + 1))
            continue
        iid = it["id"]
        if iid in ids:
            errs.append("item id %s appears twice" % iid)
        ids.add(iid)
        if it.get("status") not in ITEM_STATUSES:
            errs.append("item %s: status must be done, partial or not_done, not %s"
                        % (iid, json.dumps(plain(it.get("status")))))
        acc = it.get("acceptance", [])
        if not isinstance(acc, list) or not all(isinstance(a, dict) for a in acc):
            errs.append("item %s: acceptance must be a list of {check, variant, target, before, after}" % iid)
            continue
        for k, a in enumerate(acc):
            t = a.get("target")
            if t is not None and not is_target(t):
                errs.append("item %s row %d (%s): a target is [low, high] with null for an open end, not %s"
                            % (iid, k + 1, fmt(a.get("check")), json.dumps(plain(t))))
    if errs:
        raise Fail("; ".join("%s: %s" % (path, e) for e in errs))
    return led


def read_configs(checks_dir, warns):
    """{variant: [(path, cfg), ...]} for every checks config in the folder."""
    out = {}
    for name in sorted(os.listdir(checks_dir)):
        p = os.path.join(checks_dir, name)
        if not name.endswith(".json") or not os.path.isfile(p):
            continue
        try:
            cfg = load_json(p)
        except (OSError, ValueError) as e:
            warns.append("%s: unreadable (%s): skipped" % (p, e))
            continue
        if isinstance(cfg, dict) and isinstance(cfg.get("checks"), list):
            out.setdefault(cfg.get("variant") or name[:-5], []).append((p, cfg))
    return out


def manifest_path(cp, maps):
    """<dir>/<prefix>manifest.json of one render's maps block (`maps`, or a `compare` entry), as matcheck reads it."""
    maps = maps if isinstance(maps, dict) else {}
    d = maps.get("dir") or "."
    d = d if os.path.isabs(d) else os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(cp)), d))
    return os.path.join(d, (maps.get("prefix") or "") + "manifest.json")


def result_rows(card):
    rows = card.get("results") if isinstance(card, dict) else None
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def fresh(sp, cp, cfg, ids):
    """(None, card) when the scorecard is fresh, else (why, None)."""
    if not os.path.isfile(sp):
        return "no %s" % os.path.basename(sp), None
    try:
        card = load_json(sp)
    except (OSError, ValueError) as e:
        return "unreadable scorecard (%s)" % e, None
    mp = manifest_path(cp, cfg.get("maps"))
    if not os.path.isfile(mp):
        return "no export manifest %s: freshness unknown" % mp, None
    try:
        m = load_json(mp)
        now = m.get("exported_at", m.get("export_time"))
    except (OSError, ValueError, AttributeError) as e:
        return "unreadable manifest %s (%s)" % (mp, e), None
    was = card.get("manifest").get("exported_at") if isinstance(card.get("manifest"), dict) else None
    if not now:
        return "manifest %s has no exported_at" % mp, None
    if was != now:
        return "scorecard export %s, current export %s" % (was, now), None
    t = os.path.getmtime(sp)
    if t <= os.path.getmtime(mp):
        return "scorecard older than its export manifest", None
    if t <= os.path.getmtime(cp):
        return "scorecard older than its config", None
    compare = cfg.get("compare") if isinstance(cfg.get("compare"), dict) else {}
    for name, mc in sorted(compare.items()):  # a re-exported comparison render (nowear) changes the checks reading it
        cm = manifest_path(cp, mc)
        if isinstance(mc, dict) and os.path.isfile(cm) and t <= os.path.getmtime(cm):
            return "scorecard older than the %s export manifest" % name, None
    have = {r.get("id") for r in result_rows(card)}
    lack = [i for i in ids if i not in have]
    if lack:
        return "scorecard has no row for %s" % ", ".join(lack), None
    return None, card


def remeasure(py, cp, variant, ids, fdir):
    """Run matcheck --only ids into <fdir>/<variant>/ (main deleted its scorecard first)."""
    d = os.path.join(fdir, safe(variant))
    os.makedirs(d, exist_ok=True)
    sp = os.path.join(d, "scorecard_%s.json" % variant)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **{k: "2" for k in THREADS})
    argv = [py, MATCHECK, cp, "--only", ",".join(ids), "--out", d, "--quiet"]
    info = {"source": "rerun", "scorecard": sp, "argv": argv, "rc": None, "seconds": None, "error": None}
    t0 = time.time()
    try:
        r = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env,
                           timeout=TIMEOUT)
        info["rc"], said = r.returncode, (r.stderr or r.stdout or "").strip()
    except subprocess.TimeoutExpired:
        said = "timed out after %d s" % TIMEOUT
    except OSError as e:
        said = "cannot run %s: %s" % (py, e)
    info["seconds"] = round(time.time() - t0, 2)
    card, why = None, "matcheck rc %s" % info["rc"]
    if info["rc"] in (0, 1, 3):  # matcheck's exit codes that come with a scorecard (deleted before the run)
        if not os.path.isfile(sp):
            why += " wrote no scorecard"
        else:
            try:
                card = load_json(sp)
            except (OSError, ValueError) as e:
                why += ", unreadable scorecard (%s)" % e
    if card is None:
        last = said.splitlines()[-1] if said else ""
        info["error"] = why + (": " + last if last else "")
    return info, card


# ----------------------------------------------------------------------------- judging


def judge(a, vi, card, err):
    """One acceptance row -> its report row. vi = (config name, {id: check}, {id: count}), or None when no config has
    the variant; err says why (no config, or no scorecard)."""
    after = a.get("after")
    row = {"check": a.get("check"), "variant": a.get("variant"), "target": plain(a.get("target")),
           "target_from": None, "before": plain(a.get("before")), "after": plain(after), "value": None,
           "meets": None, "after_meets": None, "tolerance": None, "status": None, "note": "",
           "claim_contradicted": False}
    if vi is None:
        row.update(status="no_variant", note=err)
        return row
    where, checks, seen = vi
    cid = a.get("check")
    if not isinstance(cid, str) or not cid:
        row.update(status="no_check", note="the row names no check")
        return row
    if cid not in checks:
        row.update(status="no_check", note="not a check id in %s" % where)
        return row
    if checks[cid].get("skip"):
        row.update(status="no_check", note="skipped (skip: true) in %s" % where)
        return row
    if seen[cid] > 1:
        row.update(status="unmeasured", note="%d checks share this id in %s" % (seen[cid], where))
        return row
    if card is None:
        row.update(status="unmeasured", note=err)
        return row
    hits = [r for r in result_rows(card) if r.get("id") == cid]
    if len(hits) != 1:
        row.update(status="unmeasured", note="%d scorecard rows for this id" % len(hits))
        return row
    r = hits[0]
    v = r.get("value")
    row["value"] = plain(v)
    if r.get("error"):
        row.update(status="unmeasured", note="error: %s" % r["error"])
        return row
    if str(r.get("note") or "").startswith("vacuous"):
        row.update(status="unmeasured", note=r["note"])
        return row
    if not number(v):
        row.update(status="unmeasured", note="no value" if v is None else "value is NaN" if v != v else
                   "value %s is not a number" % json.dumps(plain(v))[:80])
        return row
    t = a.get("target")
    if t is not None and t != [None, None]:
        target, row["target_from"] = t, "ledger"
        ok = meets(v, t)
    elif is_target(r.get("target")) and r["target"] != [None, None]:
        target, row["target_from"] = r["target"], "check"
        ok = r["passed"] if isinstance(r.get("passed"), bool) else meets(v, target)
    else:
        row.update(status="no_target", note="neither the row nor the check has a target")
        return row
    row["meets"] = ok
    if not number(after):
        row.update(status="no_after", note="no measured after in the ledger; the re-measure %s the target"
                   % ("meets" if ok else "misses"))
        return row
    row["after_meets"] = meets(after, target)
    if not ok:
        row["status"] = "misses"
        if row["after_meets"]:
            row.update(claim_contradicted=True, note="the ledger's after %s meets the target" % fmt(after))
        return row
    row["tolerance"] = tol = max(half_unit(after), 0.01 * abs(after))
    if abs(v - after) > tol * (1 + 1e-9) + SLACK:
        row.update(status="drifted", note="the ledger's after is %s: update it" % fmt(after))
    else:
        row["status"] = "holds"
    return row


# ----------------------------------------------------------------------------- report


def write_md(path, rep, tools):
    c = rep["counts"]
    lines = ["# Fixcheck: %s" % rel(rep["ledger"], tools), "",
             "%d items: %d landed, %d not landed. Done but not landed: %s. Claims contradicted: %s. "
             "Measure failed: %s. Exit code %d."
             % (len(rep["items"]), len(rep["landed"]), len(rep["not_landed"]),
                ", ".join(rep["done_not_landed"]) or "none",
                ", ".join("%s %s (%s)" % (x["item"], x["check"], x["variant"]) for x in rep["claim_contradicted"])
                or "none", ", ".join(x["variant"] for x in rep["measure_failed"]) or "none", rep["rc"]),
             "Rows: %s." % ", ".join("%s %d" % (s, c[s]) for s in STATUSES), ""]
    for v, m in sorted(rep["measured"].items()):
        if m["source"] == "scorecard":
            lines.append("- %s: %s" % (v, rel(m["scorecard"], tools)))
        else:
            lines.append("- %s: re-run (%s), rc %s, %s s: %s" % (v, m["why"], m["rc"], m["seconds"],
                                                               m["error"] or rel(m["scorecard"], tools)))
    lines += ["- **Warning**: %s" % w for w in rep["warnings"]]
    if rep["measured"] or rep["warnings"]:
        lines.append("")
    lines += ["| item | status | verdict | flags | rows | title |", "|---|---|---|---|---|---|"]
    for it in rep["items"]:
        n = {}
        for r in it["rows"]:
            n[r["status"]] = n.get(r["status"], 0) + 1
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            cell(it["id"]), it["status"], it["verdict"], ", ".join(it["flags"]) or "-",
            ", ".join("%s %d" % (s, n[s]) for s in STATUSES if s in n) or "none", cell(fmt(it["title"]))))
    lines += ["", "| item | check | variant | target | before | after | now | status | note |",
              "|---|---|---|---|---|---|---|---|---|"]
    for it in rep["items"]:
        for r in it["rows"]:
            t = r["target"] if r["target_from"] != "check" else None
            t = fmt_target(t) if t else "check's" if r["target_from"] else "-"
            st = r["status"] + (" (contradicted)" if r["claim_contradicted"] else "")
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                cell(it["id"]), cell(fmt(r["check"])), cell(fmt(r["variant"])), t, cell(fmt(r["before"])),
                cell(fmt(r["after"])), cell(fmt(r["value"])), st, cell(r["note"])))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ledger", required=True, help="review/round<N>/ledger.json")
    ap.add_argument("--scorecards", help="folder of scorecard_<variant>.json (default: the ledger's folder)")
    ap.add_argument("--checks-dir", help="folder of the checks configs (default: <tools>/checks)")
    ap.add_argument("--out", help="fixcheck/ is written here (default: the ledger's folder)")
    ap.add_argument("--rerun", action="store_true", help="re-run matcheck for every variant, fresh or not")
    ap.add_argument("--python", default=sys.executable, help="python for matcheck (default: this one)")
    a = ap.parse_args(argv)
    t0 = time.time()
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ledger = os.path.abspath(a.ledger)
    here = os.path.dirname(ledger)
    tools = os.path.normpath(os.path.join(here, "..", ".."))
    scdir = os.path.abspath(a.scorecards or here)
    checks_dir = os.path.abspath(a.checks_dir or os.path.join(tools, "checks"))
    fdir = os.path.join(os.path.abspath(a.out or here), "fixcheck")
    jp, mdp = os.path.join(fdir, "fixcheck.json"), os.path.join(fdir, "fixcheck.md")
    remove(jp)
    remove(mdp)
    warns = []
    try:
        if not os.path.isdir(checks_dir):
            raise Fail("no checks folder %s (pass --checks-dir)" % checks_dir)
        led = read_ledger(ledger)
        configs = read_configs(checks_dir, warns)
        rows = [x for it in led["items"] for x in it.get("acceptance", [])]
        named = sorted({x.get("variant") for x in rows if isinstance(x.get("variant"), str)} & set(configs))
        dup = ["%s (%s)" % (v, ", ".join(os.path.basename(p) for p, _ in configs[v]))
               for v in named if len(configs[v]) > 1]
        if dup:
            raise Fail("more than one config has variant %s: the ledger cannot say which" % "; ".join(dup))
    except Fail as e:
        print("fixcheck: %s" % e, file=sys.stderr)
        return 2
    vinfo, want = {}, {}  # variant -> (config name, {id: check}, {id: count}); variant -> ids to measure
    for v in named:
        cp, cfg = configs[v][0]
        checks = [c for c in cfg["checks"] if isinstance(c, dict)]
        seen = {}
        for c in checks:
            seen[c.get("id")] = seen.get(c.get("id"), 0) + 1
        vinfo[v] = (os.path.basename(cp), {c.get("id"): c for c in checks}, seen)
    for x in rows:
        v, cid = x.get("variant"), x.get("check")
        if (isinstance(v, str) and v in vinfo and isinstance(cid, str) and vinfo[v][2].get(cid) == 1
                and not vinfo[v][1][cid].get("skip")):
            want.setdefault(v, [])
            if cid not in want[v]:
                want[v].append(cid)
    for v in want:
        remove(os.path.join(fdir, safe(v), "scorecard_%s.json" % v))
        remove(os.path.join(fdir, safe(v), "scorecard_%s.md" % v))
    measured, cards = {}, {}
    for v, ids in want.items():
        cp, cfg = configs[v][0]
        sp = os.path.join(scdir, "scorecard_%s.json" % v)
        why, card = ("--rerun", None) if a.rerun else fresh(sp, cp, cfg, ids)
        if card is not None:
            measured[v] = {"source": "scorecard", "scorecard": sp, "config": cp, "why": None, "rc": None,
                           "seconds": None, "error": None}
        else:
            info, card = remeasure(a.python, cp, v, ids, fdir)
            info.update(config=cp, why=why)
            measured[v] = info
            print("%s: re-run (%s): rc %s, %s s%s" % (v, why, info["rc"], info["seconds"],
                                                     ": " + info["error"] if info["error"] else ""), flush=True)
        cards[v] = card
    items, counts = [], {s: 0 for s in STATUSES}
    for it in led["items"]:
        out_rows = []
        for x in it.get("acceptance", []):
            v = x.get("variant")
            if not isinstance(v, str) or not v:
                r = judge(x, None, None, "the row names no variant")
            elif v not in vinfo:
                r = judge(x, None, None, "no config in %s has variant %s" % (checks_dir, v))
            else:
                r = judge(x, vinfo[v], cards.get(v), (measured.get(v) or {}).get("error"))
            counts[r["status"]] += 1
            out_rows.append(r)
        landed = bool(out_rows) and all(r["status"] in ("holds", "drifted") for r in out_rows)
        flags = (["done_not_landed"] if it["status"] == "done" and not landed else []) + \
                (["claim_contradicted"] if any(r["claim_contradicted"] for r in out_rows) else []) + \
                (["measure_failed"] if any((measured.get(r["variant"]) or {}).get("error") for r in out_rows
                                           if isinstance(r["variant"], str)) else [])
        items.append({"id": it["id"], "title": plain(it.get("title", "")), "status": it["status"],
                      "verdict": "landed" if landed else "not_landed", "flags": flags,
                      "note": "" if out_rows else "no acceptance rows: nothing re-measured", "rows": out_rows})
    dnl = [i["id"] for i in items if "done_not_landed" in i["flags"]]
    cc = [{"item": i["id"], "check": r["check"], "variant": r["variant"]} for i in items for r in i["rows"]
          if r["claim_contradicted"]]
    mf = [{"variant": v, "error": m["error"]} for v, m in sorted(measured.items()) if m.get("error")]
    rc = 1 if dnl or cc or mf else 0  # a re-measure that could not run never reads as exit 0
    rep = {"ledger": ledger, "checks_dir": checks_dir, "scorecards": scdir, "out": fdir, "rerun": a.rerun,
           "python": a.python, "started": started, "seconds": None, "rc": rc, "counts": counts,
           "landed": [i["id"] for i in items if i["verdict"] == "landed"],
           "not_landed": [i["id"] for i in items if i["verdict"] != "landed"],
           "done_not_landed": dnl, "claim_contradicted": cc, "measure_failed": mf, "measured": measured,
           "warnings": warns, "items": items}
    os.makedirs(fdir, exist_ok=True)
    rep["seconds"] = round(time.time() - t0, 2)
    write_md(mdp, rep, tools)
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print("%d items: %d landed, %d not landed; done but not landed: %s; claims contradicted: %s; measure failed: %s"
          % (len(items), len(rep["landed"]), len(rep["not_landed"]), ", ".join(dnl) or "none",
             ", ".join("%s %s (%s)" % (x["item"], x["check"], x["variant"]) for x in cc) or "none",
             ", ".join(x["variant"] for x in mf) or "none"))
    print("rows: %s" % ", ".join("%s %d" % (s, counts[s]) for s in STATUSES))
    for w in warns:
        print("warning: %s" % w)
    print("wrote %s/fixcheck.{json,md} in %.2f s, exit %d" % (fdir, rep["seconds"], rc))
    return rc


if __name__ == "__main__":
    sys.exit(main())
