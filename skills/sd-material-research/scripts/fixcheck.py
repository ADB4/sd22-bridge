#!/usr/bin/env python3
"""Re-measure every acceptance check in a fix ledger and say which fixes landed (references/review.md §1 step 4).
How to use it: references/checks.md, "Fixcheck". This docstring is the reference.

Usage:
    python fixcheck.py --ledger <tools>/review/round<N>/ledger.json [--scorecards DIR] [--checks-dir DIR] [--out DIR]
                       [--decisions FILE] [--rerun] [--python PY]
    python fixcheck.py --ledger L --fill before --item ID [--item ID ...] --scorecards DIR [--force] [--checks-dir DIR]
    python fixcheck.py --ledger L --fill after [--item ID ...] [--scorecards DIR] [--checks-dir DIR] [--out DIR]
                       [--rerun] [--python PY]

Options:
    --ledger      the fix ledger (review.md §1 step 4): items[].id, status (done, partial, not_done; user_edit in a
                  ledger from guards.py baseline), title and acceptance[].check, variant, target ([lo, hi], null = an
                  open end), before, after. A ledger at <tools>/review/edit<K>/ledger.json needs no other flag.
    --scorecards  folder of scorecard_<variant>.json (default: the ledger's folder, where the suite writes them)
    --checks-dir  folder of the checks configs (default: <tools>/checks, tools = the ledger's ../..)
    --out         fixcheck/ is written here (default: the ledger's folder)
    --decisions   the decision log read for exemptions (default: <tools>/review/decisions.json, none when absent)
    --rerun       re-run matcheck for every variant, fresh scorecard or not
    --python      the python matcheck runs under (default: this one; it needs numpy, so start fixcheck with $PY)
    --fill        write the ledger's numbers instead of judging them: before or after (Fill mode, below)
    --item        with --fill: an item id (repeatable, or several after one --item); after without it: every item
    --force       with --fill before: overwrite a before that is set
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
partial, not_done and user_edit items are reported, not failed (unless measure_failed or a regression flag, below).
Regression flags, from the ledger's before and the re-measured value (the ledger's after when there is none, so every
item of every status, done and partial alike, is checked). Row distance: for a target [lo, hi] (null = an open end), dist(v) is 0 inside it,
else the distance to the nearest bound. Row roles: an acceptance row has "role": "target" (default) or "guard"; a guard
row has "bound": [lo, hi] (null = an open end) instead of, or besides, a "target"; "bound" on a target row, or a guard
row with neither, is a ledger error. Its target judgement (statuses above) is unchanged; a guard row with no target
(bound only) does not count toward landed.
    regressed     before and after are numbers, the row has a target, and dist(after) > dist(before) +
                  max(0.05 * |before|, tol), tol = the row's "tolerance" if it has one, else the check's "tolerance"
                  in its config, else 0 (a zero before therefore allows only tol). No numeric before: never regressed.
                  The row also gets dist_before, dist_after, regress_allowed (the max above) and regress_excess.
    guard_broken  a guard row whose numeric `after` is outside its bound (SLACK as in meets)
Exemptions, declared before the build only. A row is exempt from both flags when its check id is in the item's
"intended_lowfreq" list, or the item's "trades" list (strings "<check>@<variant>" or "<check>"; intended_lowfreq takes
both forms too), or when a row of the decision log names the item in its `items` and the check (its id as a whole word
in `question`, `chosen`, `gave_up` or `note`, or in an optional `checks` list) with a `utc` earlier than the ledger's
apply.started (review.md §1 step 4; with no stamp no decision row counts as declared before; a user edit's ledger, kind
user_edit, has no apply stamp and no warning about it). A not_made_needs_user row
decides nothing and never exempts. Exempt rows keep the flag on the row and are reported as exempt with the reason.
Writes fixcheck.json and fixcheck.md in <out>/fixcheck/ (a folder of its own: a panel lens keyed fixcheck writes
round<N>/fixcheck.json); both are deleted first, so a failed run leaves none. fixcheck.json: rc, counts {status: n},
landed, not_landed, done_not_landed [item ids], claim_contradicted [{item, check, variant}], measure_failed [{variant,
error}], regression_counts {regressed, guard_broken, exempt} (non-exempt rows with each flag; rows exempt from one),
measured {variant: {source scorecard or rerun, scorecard, config, why, rc, argv, seconds, error}}, warnings,
items [{id, title, status, verdict landed or not_landed, flags, note, regressed [row ids check@variant], guard_broken
[row ids], exempt [{row, flag, reason}], rows [{check, variant, role, target, bound, target_from, before, after, value,
meets, after_meets, tolerance, status, note, claim_contradicted, dist_before, dist_after, regress_allowed,
regress_excess, regressed, guard_broken, exempt (the reason or null)}]}], plus ledger, checks_dir,
scorecards, out, rerun, python, started, seconds. Standard library only, Python 3.7 or newer: matcheck runs in a
subprocess under --python, which needs numpy (the analysis venv).
fixcheck.md shows a short Regressions table (every regressed, guard_broken or exempt row) before the item tables. An
item's flags also name regressed and guard_broken when it has a non-exempt row.
Promotions: an acceptance row may carry "promote_hard": true, the fix's promise to make that check a hard one (a bool
when present; anything else is a ledger error naming the item and row). fixcheck reads the check's `severity` in the
variant's config (the one it re-measures with); when it is not `hard` (missing = soft) the row is flagged
promotion_missing: the fix did not do what it promised, so the item has not landed (a done item is also
done_not_landed) and the exit code is 1, whatever the item's status. A check id the config lacks keeps its no_check
status and no promotion flag. The row then has promote_hard, severity and promotion_missing, the item a
promotion_missing list [row ids], and fixcheck.json a top-level promotion_missing [{item, check, variant}], all only
when the ledger has a promote_hard row anywhere (a ledger without one writes the same files as before); fixcheck.md and
the printed summary add a Promotions line then.
Exit code: 0 no flag; 1 a done_not_landed, claim_contradicted, measure_failed or promotion_missing item, or a
non-exempt regressed or guard_broken row; 2 a usage, checks-dir or ledger error (nothing written).

Fill mode (the apply, SKILL.md stage 7): --fill writes the measured numbers into the ledger so that no one types them.
It never judges and never flags (exit 0, or 2 on a usage or ledger error, nothing written); run the normal mode after it.
    --fill before --item ID ... --scorecards DIR
        For each named item (--item and --scorecards are required), for every acceptance row, target and guard alike:
        `before` = the `value` of the check's row in DIR/scorecard_<variant>.json, DIR being the scorecards measured
        just before the item's batch (the caller passes the ones it measured last, as for `guards.py rows`). DIR needs
        no freshness: it is the last export. A `before` that is set (not null) is never overwritten unless --force
        says so (guards.py rows sets the guard rows' before; those stay). A missing scorecard, a check the scorecard
        lacks, or a value that is an error, vacuous or not a number leaves `before` as it is and is reported.
    --fill after [--item ID ...]
        For the named items (default every item), every row's `after` = the check's value from the scorecards beside
        the ledger (--scorecards: elsewhere), under the freshness rule above: a stale or missing scorecard is
        re-measured with matcheck into <out>/fixcheck/<variant>/ (--rerun: always), as the normal mode does. A row
        whose value cannot be read keeps its `after` and is reported. Then each named item's `status` follows its
        target rows (a guard row with no target aims at nothing): `done` when all of them meet their target, `partial`
        when some do, `not_done` when none does (a measured row without a target does not meet).
        Kept as they are: the status of a user_edit item, of a not_done item whose note starts "reverted:", of an
        item with no aiming row, and of an item with an aiming row that could not be measured in this run (listed).
    Both modes: numbers are written to 4 significant digits (more only when that would change whether the value meets
    the row's target), which is the ledger's convention. A row with no target (and not a bound-only guard row) takes
    the check's own target from its variant's config (`target`, `target_mm`, `target_deg` or a max_*_frac shortcut),
    marked "target_from": "config"; nothing else of a row changes (promote_hard, role, bound, tolerance stay). Each
    row a number was written to records `"fill": {"before": <DIR relative to the tools folder>, "after": <scorecard
    path relative to it>, "utc": <stamp ending in Z>}` (the keys the fill wrote or kept). The ledger is written with
    the layout it had (indent, line ends, number text) through a temporary file and an atomic replace, the old file
    kept as ledger.json.bak; a fill that changes nothing (no number, target or status differs, so also a second fill
    after from the same scorecards) writes nothing and keeps the old provenance stamp; a symlinked ledger is written
    where it points and keeps its mode. An item with no status that cannot be set from a measure (no aiming row, or one
    that could not be measured) becomes not_done and is listed, because the normal mode rejects an item with none.
    The configs are read from --checks-dir (default <tools>/checks; --fill after needs it, --fill before only for the
    targets). A summary lists what was filled and every row left unfilled with the reason.
"""
import argparse
import datetime
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

if sys.version_info < (3, 7):  # before anything an older Python cannot run; the file parses on 3.5 or newer
    sys.stderr.write("fixcheck.py needs Python 3.7 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
MATCHECK = os.path.join(HERE, "matcheck.py")
STATUSES = ("holds", "drifted", "misses", "no_after", "no_target", "no_check", "unmeasured", "no_variant")
ITEM_STATUSES = ("done", "partial", "not_done", "user_edit")
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS")
TIMEOUT = 900  # seconds per matcheck run
SLACK = 1e-12  # matcheck.evaluate's
REGRESS_FRAC = 0.05  # a row may move this share of |before| farther from its target before it is regressed
ROLES = ("target", "guard")
BOM = b"\xef\xbb\xbf"
SIG_DIGITS = (4, 6, 9, 17)  # fill: the ledger's numbers have 4 significant digits; more only to keep a verdict
TARGET_SHORTCUTS = ("max_violation_frac", "max_changed_frac", "max_frac")  # matcheck.TARGET_KEYS


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


def dist(v, target):
    """0 inside [lo, hi] (null = an open end), else the distance to the nearest bound."""
    lo, hi = target
    return lo - v if lo is not None and v < lo else v - hi if hi is not None and v > hi else 0.0


def row_id(check, variant):
    return "%s@%s" % (fmt(check), fmt(variant))


def parse_utc(text):
    """A datetime (aware, UTC) from a stamp like 2026-10-05T01:00:00Z, else None."""
    if not isinstance(text, str):
        return None
    try:
        d = datetime.datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


def names_check(entries, cid, variant):
    """True when a list of "<check>@<variant>" or "<check>" strings names this row."""
    return isinstance(entries, list) and any(isinstance(e, str) and e.strip() in (cid, "%s@%s" % (cid, variant))
                                             for e in entries)


def half_unit(v):
    """Half a unit of the last digit as the number was written (0.40 -> 0.005, 12 -> 0.5, 1.5e-05 -> 5e-07)."""
    m = re.fullmatch(r"-?\d*(?:\.(\d*))?(?:[eE]([+-]?\d+))?", getattr(v, "text", None) or repr(float(v)))
    return 0.5 * 10.0 ** (int(m.group(2) or 0) - len(m.group(1) or "")) if m else 0.0


# ----------------------------------------------------------------------------- inputs


def read_ledger(path, fill=False):
    """The ledger (numbers as Num). fill: (ledger, layout, raw bytes) for the fill modes, which also accept an item
    that has no status yet (none, or null: the fill sets it) and keep the file's layout."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8-sig")
        led = json.loads(text, parse_float=Num, parse_int=Num)
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
        if it.get("status") not in ITEM_STATUSES and not (fill and it.get("status") is None):
            errs.append("item %s: status must be done, partial, not_done or user_edit, not %s"
                        % (iid, json.dumps(plain(it.get("status")))))
        acc = it.get("acceptance", [])
        if not isinstance(acc, list) or not all(isinstance(a, dict) for a in acc):
            errs.append("item %s: acceptance must be a list of {check, variant, target, before, after}" % iid)
            continue
        for k, a in enumerate(acc):
            t, b, role, tol = a.get("target"), a.get("bound"), a.get("role", "target"), a.get("tolerance")
            where = "item %s row %d (%s)" % (iid, k + 1, fmt(a.get("check")))
            if t is not None and not is_target(t):
                errs.append("%s: a target is [low, high] with null for an open end, not %s"
                            % (where, json.dumps(plain(t))))
            if role not in ROLES:
                errs.append("%s: role must be target or guard, not %s" % (where, json.dumps(plain(role))))
            elif b is not None and not is_target(b):
                errs.append("%s: a bound is [low, high] with null for an open end, not %s"
                            % (where, json.dumps(plain(b))))
            elif b is not None and role != "guard":
                errs.append("%s: a bound belongs to a row with role guard" % where)
            elif role == "guard" and b is None and t is None:
                errs.append("%s: a guard row needs a bound (or a target)" % where)
            if tol is not None and not (number(tol) and tol >= 0):
                errs.append("%s: tolerance must be a number of 0 or more, not %s" % (where, json.dumps(plain(tol))))
            if "promote_hard" in a and not isinstance(a["promote_hard"], bool):
                errs.append("%s: promote_hard must be true or false, not %s"
                            % (where, json.dumps(plain(a["promote_hard"]))))
        for key in ("intended_lowfreq", "trades"):
            v = it.get(key)
            if v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
                errs.append("item %s: %s must be a list of strings (<check> or <check>@<variant>)" % (iid, key))
    if errs:
        raise Fail("; ".join("%s: %s" % (path, e) for e in errs))
    if fill:
        m = re.search(r"^([ \t]+)\S", text, re.M)
        lay = {"bom": raw.startswith(BOM), "eol": "\r\n" if "\r\n" in text else "\n", "step": m.group(1) if m else None,
               "final_nl": text.endswith("\n"), "ascii": not any(ord(ch) > 127 for ch in text)}
        return led, lay, raw
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


def plan_variants(configs, rows):
    """(vinfo, want) for a list of acceptance rows: vinfo {variant: (config name, {id: check}, {id: count})} for the
    variants the rows name that have a config, want {variant: ids to measure}. Two configs of a variant: Fail."""
    named = sorted({x.get("variant") for x in rows if isinstance(x.get("variant"), str)} & set(configs))
    dup = ["%s (%s)" % (v, ", ".join(os.path.basename(p) for p, _ in configs[v])) for v in named
           if len(configs[v]) > 1]
    if dup:
        raise Fail("more than one config has variant %s: the ledger cannot say which" % "; ".join(dup))
    vinfo, want = {}, {}
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
    return vinfo, want


def collect_cards(want, configs, scdir, fdir, rerun, python):
    """({variant: how it was measured}, {variant: scorecard or None}): the fresh scorecard in scdir, else a matcheck
    re-run into fdir/<variant>/ (always with rerun)."""
    for v in want:
        remove(os.path.join(fdir, safe(v), "scorecard_%s.json" % v))
        remove(os.path.join(fdir, safe(v), "scorecard_%s.md" % v))
    measured, cards = {}, {}
    for v, ids in want.items():
        cp, cfg = configs[v][0]
        sp = os.path.join(scdir, "scorecard_%s.json" % v)
        why, card = ("--rerun", None) if rerun else fresh(sp, cp, cfg, ids)
        if card is not None:
            measured[v] = {"source": "scorecard", "scorecard": sp, "config": cp, "why": None, "rc": None,
                           "seconds": None, "error": None}
        else:
            info, card = remeasure(python, cp, v, ids, fdir)
            info.update(config=cp, why=why)
            measured[v] = info
            print("%s: re-run (%s): rc %s, %s s%s" % (v, why, info["rc"], info["seconds"],
                                                     ": " + info["error"] if info["error"] else ""), flush=True)
        cards[v] = card
    return measured, cards


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


# ----------------------------------------------------------------------------- regressions


def read_decisions(path, warns):
    """The decision log's rows ([] when the file is absent or unreadable: a warning says so)."""
    if not os.path.isfile(path):
        return []
    try:
        rows = load_json(path)["rows"]
        if not isinstance(rows, list):
            raise TypeError("rows is not a list")
    except (OSError, ValueError, KeyError, TypeError) as e:
        warns.append("%s: unreadable (%s): no decision row can exempt a row" % (path, e))
        return []
    return [r for r in rows if isinstance(r, dict)]


def declared_before(decs, apply_start, item_id, cid, variant):
    """The id of a decision row that names this item and check and was logged before the apply began, else None."""
    if apply_start is None:
        return None
    pat = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(cid))
    for d in decs:
        when = parse_utc(d.get("utc"))
        if (d.get("kind") == "not_made_needs_user" or when is None or when >= apply_start
                or item_id not in (d.get("items") or [])):
            continue
        if names_check(d.get("checks"), cid, variant) or any(isinstance(d.get(k), str) and pat.search(d[k])
                                                          for k in ("question", "chosen", "gave_up", "note")):
            return str(d.get("id") or "?")
    return None


def regression(a, it, check, decs, apply_start, value=None):
    """The regression fields of one acceptance row (check: its config entry or None). after is the re-measured value
    when there is one, else the ledger's own after, so a later batch that undid a fix shows at the final gate."""
    cid, variant, before = a.get("check"), a.get("variant"), a.get("before")
    after = value if number(value) else a.get("after")
    t, b = a.get("target"), a.get("bound")
    t = t if t is not None and t != [None, None] else None
    out = {"role": a.get("role", "target"), "bound": plain(b), "dist_before": None, "dist_after": None,
           "regress_allowed": None, "regress_excess": None, "regressed": False, "guard_broken": False, "exempt": None}
    if t is not None and number(before) and number(after):
        tol = next((x for x in (a.get("tolerance"), (check or {}).get("tolerance")) if number(x) and x >= 0), 0.0)
        db, da = dist(before, t), dist(after, t)
        allowed = max(REGRESS_FRAC * abs(before), tol)
        out.update(dist_before=db, dist_after=da, regress_allowed=allowed, regress_excess=da - db - allowed,
                   regressed=da > db + allowed + SLACK)
    out["guard_broken"] = b is not None and number(after) and not meets(after, b)
    if out["regressed"] or out["guard_broken"]:
        c = cid if isinstance(cid, str) else ""
        if names_check(it.get("intended_lowfreq"), c, variant):
            out["exempt"] = "intended_lowfreq"
        elif names_check(it.get("trades"), c, variant):
            out["exempt"] = "trades"
        else:
            d = declared_before(decs, apply_start, it["id"], c, variant) if c else None
            if d:
                out["exempt"] = "decision %s, logged before the apply" % d
    for k in ("dist_before", "dist_after", "regress_allowed", "regress_excess"):
        out[k] = round(out[k], 9) if out[k] is not None else None
    return out


def promotion(a, check, where):
    """The promote_hard fields of one acceptance row that carries promote_hard (else {}): check is its config entry or
    None (a missing or skipped check keeps its no_check status and gets no flag)."""
    if not a.get("promote_hard"):
        return {}
    sev = (check or {}).get("severity", "soft")
    miss = check is not None and not check.get("skip") and sev != "hard"
    return {"promote_hard": True, "severity": sev if check is not None else None, "promotion_missing": miss,
            "_note": "promote_hard: the check is %s in %s; the fix promised severity hard" % (
                "soft" if sev in ("soft", None) else fmt(sev), where) if miss else ""}


# ----------------------------------------------------------------------------- fill mode


def render(v, lay, lvl=0):
    """json.dumps(indent=step) of v, but a Num is written as the text it was read from (the ledger keeps its layout)."""
    if isinstance(v, Num):
        return v.text
    if isinstance(v, dict):
        if not v:
            return "{}"
        parts, brackets = ["%s: %s" % (json.dumps(k, ensure_ascii=lay["ascii"]), render(x, lay, lvl + 1))
                           for k, x in v.items()], "{}"
    elif isinstance(v, list):
        if not v:
            return "[]"
        parts, brackets = [render(x, lay, lvl + 1) for x in v], "[]"
    else:
        return json.dumps(v, ensure_ascii=lay["ascii"])
    step = lay["step"]
    if step is None:
        return brackets[0] + ", ".join(parts) + brackets[1]
    pad = step * (lvl + 1)
    return brackets[0] + "\n" + ",\n".join(pad + p for p in parts) + "\n" + step * lvl + brackets[1]


def write_ledger(path, led, lay, raw):
    """The ledger in its own layout through a temporary file and an atomic replace, the old bytes in <path>.bak. A
    symlinked ledger is written where it points (the link stays a link) and the file keeps its mode."""
    path = os.path.realpath(path)
    out = (render(led, lay) + ("\n" if lay["final_nl"] else "")).replace("\n", lay["eol"]).encode("utf-8")
    tmp = "%s.%d.tmp" % (path, os.getpid())
    try:
        with open(path + ".bak", "wb") as fh:
            fh.write(raw)
        with open(tmp, "wb") as fh:
            fh.write((BOM if lay["bom"] else b"") + out)
        try:
            shutil.copymode(path, tmp)
        except OSError:
            pass
        os.replace(tmp, path)
    except OSError as e:
        remove(tmp)
        raise Fail("%s: cannot write: %s" % (path, e.strerror or e))


def ledger_number(v, target=None):
    """A ledger Num for a measured value: 4 significant digits, more only while that changes whether the value meets
    the target (so a rounded after never contradicts the re-measure)."""
    want = meets(v, target) if target else None
    for n in SIG_DIGITS:
        x = float("%.*e" % (n - 1, v))
        if not target or meets(x, target) == want:
            break
    if x == 0:
        return Num("0")
    return Num(str(int(x)) if x == int(x) and abs(x) < 1e15 else repr(x))


def config_target(check):
    """The target a config check carries (matcheck.target_of), else None."""
    for k in ("target", "target_mm", "target_deg"):
        if k in check:
            t = check[k]
            break
    else:
        t = next(([None, check[k]] for k in TARGET_SHORTCUTS if k in check), None)
        if t is None and check.get("type") in ("value_order", "normal_valid"):
            t = [1, None]
    return t if is_target(t) and t != [None, None] else None


def card_value(card, cid):
    """(value, None) of a check in a scorecard, else (None, why it has none)."""
    hits = [r for r in result_rows(card) if r.get("id") == cid]
    if len(hits) != 1:
        return None, "%d scorecard rows for this id" % len(hits)
    r = hits[0]
    v = r.get("value")
    if r.get("error"):
        return None, "error: %s" % r["error"]
    if str(r.get("note") or "").startswith("vacuous"):
        return None, str(r["note"])
    if not number(v):
        return None, "no value" if v is None else "value is NaN" if v != v else "value %s is not a number" % (
            json.dumps(plain(v))[:80])
    return v, None


def slash(path):
    return path.replace(os.sep, "/")


def mark_fill(row, key, where, utc):
    """row["fill"] = {before, after, utc}: the keys the fill wrote now or an earlier fill wrote, and the stamp."""
    old = row.get("fill") if isinstance(row.get("fill"), dict) else {}
    new = {k: (where if k == key else old[k]) for k in ("before", "after") if k == key or k in old}
    new["utc"] = utc
    row["fill"] = new


def put_num(row, key, num, where, utc):
    """row[key] = num with its provenance. False, the row untouched (the old stamp stays), when the row already holds
    this number from this place: a repeated fill then changes nothing and the ledger is not rewritten."""
    old, fill = row.get(key), row.get("fill")
    if number(old) and old == num and isinstance(fill, dict) and fill.get(key) == where:
        return False
    row[key] = num
    mark_fill(row, key, where, utc)
    return True


def cmd_fill(a):
    """--fill before|after: see the docstring. Returns the exit code; Fail is the caller's exit 2."""
    mode = a.fill
    ids = list(dict.fromkeys(x for group in (a.item or []) for x in group))
    if mode == "before" and not ids:
        raise Fail("--fill before needs --item ID: the items whose batch comes next")
    if mode == "before" and not a.scorecards:
        raise Fail("--fill before needs --scorecards DIR: the scorecards measured just before the batch")
    if a.force and mode != "before":
        raise Fail("--force belongs to --fill before")
    if mode == "before" and (a.rerun or a.out or a.decisions):
        raise Fail("--fill before reads scorecards only: --rerun, --out and --decisions belong to the other modes")
    ledger = os.path.abspath(a.ledger)
    here = os.path.dirname(ledger)
    tools = os.path.normpath(os.path.join(here, "..", ".."))
    scdir = os.path.abspath(a.scorecards or here)
    checks_dir = os.path.abspath(a.checks_dir or os.path.join(tools, "checks"))
    fdir = os.path.join(os.path.abspath(a.out or here), "fixcheck")
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    led, lay, raw = read_ledger(ledger, fill=True)
    have = [it["id"] for it in led["items"]]
    lack = [i for i in ids if i not in have]
    if lack:
        raise Fail("%s: no item %s" % (ledger, ", ".join(lack)))
    items = [it for it in led["items"] if not ids or it["id"] in ids]
    rows = [(it, x) for it in items for x in it.get("acceptance", [])]
    warns, vinfo, configs = [], {}, {}
    if os.path.isdir(checks_dir):
        configs = read_configs(checks_dir, warns)
    elif mode == "after":
        raise Fail("no checks folder %s (pass --checks-dir)" % checks_dir)
    else:
        warns.append("no checks folder %s: no row gets the check's target" % checks_dir)
    vinfo, want = plan_variants(configs, [x for _, x in rows])
    left, changed = [], False  # (item id, row id, why)
    counts = {"target": 0, "kept": 0, "filled": 0, "same": 0, "left": 0}

    def row_where(it, x):
        return "%s %s" % (it["id"], row_id(x.get("check"), x.get("variant")))

    # a row without a target takes the config's; a guard row that has only a bound aims at nothing and stays so
    for it, x in rows:
        t, v, cid = x.get("target"), x.get("variant"), x.get("check")
        if (t is None or t == [None, None]) and x.get("role", "target") != "guard" and isinstance(v, str) \
                and v in vinfo and isinstance(cid, str):
            check, seen = vinfo[v][1].get(cid), vinfo[v][2].get(cid)
            t = config_target(check) if check is not None and seen == 1 and not check.get("skip") else None
            if t is not None:
                x["target"], x["target_from"] = t, "config"
                counts["target"] += 1
                changed = True

    if mode == "before":
        cards = {}
        for it, x in rows:
            v, cid = x.get("variant"), x.get("check")
            if x.get("before") is not None and not a.force:
                counts["kept"] += 1
                continue
            if not (isinstance(v, str) and v and not re.search(r"[\\/]", v)) or not (isinstance(cid, str) and cid):
                left.append((row_where(it, x), "the row names no variant or check"))
                continue
            if v not in cards:
                sp = os.path.join(scdir, "scorecard_%s.json" % v)
                try:
                    cards[v] = (load_json(sp), None)
                except OSError:
                    cards[v] = (None, "no scorecard_%s.json in %s" % (v, scdir))
                except ValueError as e:
                    cards[v] = (None, "scorecard_%s.json is unreadable (%s)" % (v, e))
            card, err = cards[v]
            value, why = (None, err) if card is None else card_value(card, cid)
            if value is None:
                left.append((row_where(it, x), why))
                continue
            if put_num(x, "before", ledger_number(value), slash(rel(scdir, tools)), utc):
                counts["filled"] += 1
                changed = True
            else:
                counts["same"] += 1
    else:
        measured, cards = collect_cards(want, configs, scdir, fdir, a.rerun, a.python)
        done_rows = set()  # the rows an after was written to in this run
        for it, x in rows:
            v, cid = x.get("variant"), x.get("check")
            if not isinstance(v, str) or not v:
                why = "the row names no variant"
            elif v not in vinfo:
                why = "no config in %s has variant %s" % (checks_dir, v)
            elif not isinstance(cid, str) or cid not in vinfo[v][1]:
                why = "not a check id in %s" % vinfo[v][0]
            elif vinfo[v][1][cid].get("skip"):
                why = "skipped (skip: true) in %s" % vinfo[v][0]
            elif vinfo[v][2][cid] > 1:
                why = "%d checks share this id in %s" % (vinfo[v][2][cid], vinfo[v][0])
            elif cards.get(v) is None:
                why = (measured[v].get("error") or "no scorecard") if v in measured else "no scorecard"
            else:
                value, why = card_value(cards[v], cid)
                if value is not None:
                    t = x.get("target")
                    done_rows.add(id(x))
                    if put_num(x, "after", ledger_number(value, t if t and t != [None, None] else None),
                               slash(rel(measured[v]["scorecard"], tools)), utc):
                        counts["filled"] += 1
                        changed = True
                    else:
                        counts["same"] += 1
                    continue
            left.append((row_where(it, x), why))
        statuses = []
        for it in items:
            if it.get("status") == "user_edit" or (it.get("status") == "not_done"
                                                   and str(it.get("note") or "").startswith("reverted:")):
                continue
            aims = [x for x in it.get("acceptance", []) if x.get("role", "target") != "guard" or x.get("target")]
            unread = [x for x in aims if id(x) not in done_rows]
            if not aims or unread:  # a status from numbers that were not just measured would be a guess
                if it.get("status") is None:  # but the next step rejects an item with none: not_done, never a guess up
                    it["status"] = "not_done"
                    changed = True
                    statuses.append("%s none -> not_done (no status yet and %s)" % (
                        it["id"], "no aiming row" if not aims else "%d of %d aiming rows were not measured" % (
                            len(unread), len(aims))))
                elif aims:
                    statuses.append("%s %s kept: %d of %d aiming rows were not measured" % (
                        it["id"], it["status"], len(unread), len(aims)))
                continue
            met = 0
            for x in aims:
                t = x.get("target")
                met += bool(t and t != [None, None] and number(x.get("after")) and meets(x["after"], t))
            new = "done" if met == len(aims) else "partial" if met else "not_done"
            statuses.append("%s %s -> %s (%d of %d target rows meet)" % (it["id"], it.get("status", "none"), new, met,
                                                                       len(aims)))
            if it.get("status") != new:
                it["status"] = new
                changed = True
    counts["left"] = len(left)
    if changed:
        write_ledger(ledger, led, lay, raw)
    print("fill %s %s: %d items, %d rows: %d numbers written, %d targets taken from the config%s%s, %d rows left"
          % (mode, rel(ledger, tools), len(items), len(rows), counts["filled"], counts["target"],
             ", %d before kept" % counts["kept"] if mode == "before" else "",
             ", %d numbers already as measured" % counts["same"] if counts["same"] else "", counts["left"]))
    if mode == "after":
        for line in statuses:
            print("status: " + line)
    for where, why in left:
        print("left: %s: %s" % (where, why))
    for w in warns:
        print("warning: %s" % w)
    print("ledger %s" % ("written (old file: %s.bak)" % rel(ledger, tools) if changed else "not written: nothing to fill"))
    return 0


# ----------------------------------------------------------------------------- report


def write_md(path, rep, tools):
    c, rc_ = rep["counts"], rep["regression_counts"]
    lines = ["# Fixcheck: %s" % rel(rep["ledger"], tools), "",
             "%d items: %d landed, %d not landed. Done but not landed: %s. Claims contradicted: %s. "
             "Measure failed: %s. Exit code %d."
             % (len(rep["items"]), len(rep["landed"]), len(rep["not_landed"]),
                ", ".join(rep["done_not_landed"]) or "none",
                ", ".join("%s %s (%s)" % (x["item"], x["check"], x["variant"]) for x in rep["claim_contradicted"])
                or "none", ", ".join(x["variant"] for x in rep["measure_failed"]) or "none", rep["rc"]),
             "Rows: %s." % ", ".join("%s %d" % (s, c[s]) for s in STATUSES),
             "Regressions: %d regressed, %d guard broken, %d exempt." % (
                 rc_["regressed"], rc_["guard_broken"], rc_["exempt"])]
    if "promotion_missing" in rep:
        lines.append("Promotion missing: %s." % (", ".join("%s %s (%s)" % (x["item"], x["check"], x["variant"])
                                                          for x in rep["promotion_missing"]) or "none"))
    lines.append("")
    for v, m in sorted(rep["measured"].items()):
        if m["source"] == "scorecard":
            lines.append("- %s: %s" % (v, rel(m["scorecard"], tools)))
        else:
            lines.append("- %s: re-run (%s), rc %s, %s s: %s" % (v, m["why"], m["rc"], m["seconds"],
                                                               m["error"] or rel(m["scorecard"], tools)))
    lines += ["- **Warning**: %s" % w for w in rep["warnings"]]
    if rep["measured"] or rep["warnings"]:
        lines.append("")
    flagged = [(it, r) for it in rep["items"] for r in it["rows"] if r["regressed"] or r["guard_broken"]]
    if flagged:
        lines += ["## Regressions", "",
                  "| item | status | check | variant | flag | target | bound | before | after | allowed | exempt |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for it, r in flagged:
            flag = " + ".join(f for f in ("regressed" if r["regressed"] else "", "guard_broken" if r["guard_broken"]
                                          else "") if f)
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                cell(it["id"]), it["status"], cell(fmt(r["check"])), cell(fmt(r["variant"])), flag,
                fmt_target(r["target"]) if r["target"] else "-", fmt_target(r["bound"]) if r["bound"] else "-",
                cell(fmt(r["before"])), cell(fmt(r["after"])), cell(fmt(r["regress_allowed"])),
                cell(r["exempt"] or "no")))
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
    ap.add_argument("--decisions", help="decision log for exemptions (default: <tools>/review/decisions.json)")
    ap.add_argument("--rerun", action="store_true", help="re-run matcheck for every variant, fresh or not")
    ap.add_argument("--python", default=sys.executable, help="python for matcheck (default: this one)")
    ap.add_argument("--fill", choices=("before", "after"), help="write the ledger's before or after numbers")
    ap.add_argument("--item", action="append", nargs="+", metavar="ID", help="with --fill: an item id (repeatable)")
    ap.add_argument("--force", action="store_true", help="with --fill before: overwrite a before that is set")
    a = ap.parse_args(argv)
    if a.fill:
        try:
            return cmd_fill(a)
        except Fail as e:
            print("fixcheck: %s" % e, file=sys.stderr)
            return 2
    if a.item or a.force:
        print("fixcheck: --item and --force belong to --fill", file=sys.stderr)
        return 2
    t0 = time.time()
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ledger = os.path.abspath(a.ledger)
    here = os.path.dirname(ledger)
    tools = os.path.normpath(os.path.join(here, "..", ".."))
    scdir = os.path.abspath(a.scorecards or here)
    checks_dir = os.path.abspath(a.checks_dir or os.path.join(tools, "checks"))
    decpath = os.path.abspath(a.decisions or os.path.join(tools, "review", "decisions.json"))
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
        vinfo, want = plan_variants(configs, rows)
    except Fail as e:
        print("fixcheck: %s" % e, file=sys.stderr)
        return 2
    measured, cards = collect_cards(want, configs, scdir, fdir, a.rerun, a.python)
    decs = read_decisions(decpath, warns)
    apply_start = parse_utc((led.get("apply") or {}).get("started") if isinstance(led.get("apply"), dict) else None)
    if decs and apply_start is None and led.get("kind") != "user_edit":
        warns.append("the ledger has no readable apply.started: no decision row counts as declared before the build")
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
            cid = x.get("check")
            cfgc = vinfo[v][1].get(cid) if isinstance(v, str) and v in vinfo and isinstance(cid, str) else None
            r.update(regression(x, it, cfgc, decs, apply_start, r.get("value")))
            pr = promotion(x, cfgc, vinfo[v][0] if cfgc is not None and v in vinfo else None)
            if pr:
                r["note"] = "; ".join(n for n in (r["note"], pr.pop("_note")) if n)
                r.update(pr)
            counts[r["status"]] += 1
            out_rows.append(r)
        aims = [r for r in out_rows if r["role"] != "guard" or r["target"]]   # a bound-only guard row aims at nothing
        pm = [r for r in out_rows if r.get("promotion_missing")]
        landed = bool(aims) and all(r["status"] in ("holds", "drifted") for r in aims) and not pm
        flags = (["done_not_landed"] if it["status"] == "done" and not landed else []) + \
                (["claim_contradicted"] if any(r["claim_contradicted"] for r in out_rows) else []) + \
                (["measure_failed"] if any((measured.get(r["variant"]) or {}).get("error") for r in out_rows
                                           if isinstance(r["variant"], str)) else [])
        reg = [r for r in out_rows if r["regressed"] and not r["exempt"]]
        gb = [r for r in out_rows if r["guard_broken"] and not r["exempt"]]
        flags += (["regressed"] if reg else []) + (["guard_broken"] if gb else []) + \
                 (["promotion_missing"] if pm else [])
        items.append({"id": it["id"], "title": plain(it.get("title", "")), "status": it["status"],
                      "verdict": "landed" if landed else "not_landed", "flags": flags,
                      "note": "" if out_rows else "no acceptance rows: nothing re-measured",
                      "regressed": [row_id(r["check"], r["variant"]) for r in reg],
                      "guard_broken": [row_id(r["check"], r["variant"]) for r in gb],
                      "exempt": [{"row": row_id(r["check"], r["variant"]), "flag": f, "reason": r["exempt"]}
                                 for r in out_rows if r["exempt"] for f in ("regressed", "guard_broken") if r[f]],
                      "rows": out_rows})
        if any(r.get("promote_hard") for r in out_rows):
            items[-1]["promotion_missing"] = [row_id(r["check"], r["variant"]) for r in pm]
    dnl = [i["id"] for i in items if "done_not_landed" in i["flags"]]
    cc = [{"item": i["id"], "check": r["check"], "variant": r["variant"]} for i in items for r in i["rows"]
          if r["claim_contradicted"]]
    mf = [{"variant": v, "error": m["error"]} for v, m in sorted(measured.items()) if m.get("error")]
    rcount = {"regressed": sum(len(i["regressed"]) for i in items),
              "guard_broken": sum(len(i["guard_broken"]) for i in items),
              "exempt": sum(1 for i in items for r in i["rows"] if r["exempt"])}
    pmiss = [{"item": i["id"], "check": r["check"], "variant": r["variant"]} for i in items for r in i["rows"]
             if r.get("promotion_missing")]
    # a re-measure that could not run never reads as exit 0
    rc = 1 if dnl or cc or mf or pmiss or rcount["regressed"] or rcount["guard_broken"] else 0
    rep = {"ledger": ledger, "checks_dir": checks_dir, "scorecards": scdir, "out": fdir, "rerun": a.rerun,
           "python": a.python, "started": started, "seconds": None, "rc": rc, "counts": counts,
           "regression_counts": rcount, "landed": [i["id"] for i in items if i["verdict"] == "landed"],
           "not_landed": [i["id"] for i in items if i["verdict"] != "landed"],
           "done_not_landed": dnl, "claim_contradicted": cc, "measure_failed": mf, "measured": measured,
           "warnings": warns, "items": items}
    if any(r.get("promote_hard") for i in items for r in i["rows"]):
        rep["promotion_missing"] = pmiss
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
    print("regressions: %d regressed, %d guard broken, %d exempt%s"
          % (rcount["regressed"], rcount["guard_broken"], rcount["exempt"],
             "".join("; %s: %s" % (i["id"], ", ".join(i["regressed"] + i["guard_broken"])) for i in items
                     if i["regressed"] or i["guard_broken"])))
    if "promotion_missing" in rep:
        print("promotion missing: %s" % (", ".join("%s %s (%s)" % (x["item"], x["check"], x["variant"])
                                                   for x in pmiss) or "none"))
    for w in warns:
        print("warning: %s" % w)
    print("wrote %s/fixcheck.{json,md} in %.2f s, exit %d" % (fdir, rep["seconds"], rc))
    return rc


if __name__ == "__main__":
    sys.exit(main())
