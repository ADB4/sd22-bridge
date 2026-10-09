#!/usr/bin/env python3
"""Add the standard guard checks to the checks configs, bound their values in a fix ledger (R-13), and write a user
edit's ledger against the last green state (I-1).
A guard check reports a map's tile-period stripe or low-frequency std. Its pre-batch value becomes a ledger guard row
with an upper bound, so a fix that adds either defect breaks the bound and fixcheck.py flags guard_broken. This
docstring is the reference.

Usage:
    python guards.py configs --checks-dir T/checks [--maps MAP [MAP ...]] [--dry-run]
    python guards.py rows    --ledger L --item ID --scorecards DIR [--variants V [V ...]] [--factor 1.25]
                             [--floor-harm 0.25] [--floor-lowfreq 0.005]
    python guards.py baseline --tools T --edit K --variants V [V ...] [--green DIR] [--title TEXT]
                              [--factor 1.25] [--floor-harm 0.25] [--floor-lowfreq 0.005]

configs  For every <checks-dir>/*.json with a `checks` list (a JSON file without one is skipped, and named), add these
         soft checks for each map, unless a check with that id is already there (it is left as it is, whatever it holds):
             guard_harm_<map>     {"id", "type": "tile_harmonic", "map": <map>, "stat": "max_amp", "severity": "soft",
                                   "guard": true, "why": "R-13 standard guard: tile-period stripe"}
             guard_lowfreq_<map>  {"id", "type": "lowfreq", "map": <map>, "stat": "std_over_mean", "severity": "soft",
                                   "guard": true, "why": "R-13 standard guard: low-frequency std"}
         They have no target: they report values (matcheck ignores `guard`; it marks a check the run may not demote,
         skip, retarget or delete). The maps are --maps, else the maps of the config's own seam checks (every seam
         check not skipped, the union in order of appearance; one with no `maps` reads height and basecolor, as
         matcheck does), else height and basecolor. Idempotent: a second run adds nothing.
         A file is rewritten with its key order, number text (1.0, 1e-06), indentation (the first indented line's),
         line ends, BOM, ASCII escapes and final newline kept; a file whose layout JSON cannot reproduce (items written
         inline on one line, say) comes out in the standard layout and the line says "reformatted". Each file is written
         atomically (tmp + os.replace). --dry-run prints the same lines and writes nothing. One line per file.
rows     Append guard rows to the acceptance list of ledger item ID (review.md §1 step 4), one for each guard_* check
         (a scorecard row whose id starts with guard_) in <DIR>/scorecard_<variant>.json, for each variant of --variants,
         else of the item's `variants` list (neither: exit 2). DIR holds the scorecards measured just before the item's
         batch. The row is
             {"check", "variant", "role": "guard", "before": <the scorecard value>, "bound": [null, hi],
              "note": "standard guard (R-13c)"}
         with hi = max(factor * before, before + floor), rounded to 6 significant digits. The floor is --floor-harm
         (0.25, in % of the map's mean) for a tile_harmonic check and --floor-lowfreq (0.005, a std over the mean) for a
         lowfreq one; another type, or a value that is not a number (an error or a vacuous check), gets a warning and no
         row. A check named in the item's `intended_lowfreq` (<check> or <check>@<variant>, declared before the build)
         gets "bound": [null, null], which nothing breaks (fixcheck rejects a guard row with no bound at all), and the
         note "intended_lowfreq: exempt". A row for the same check and variant that the acceptance list already has is
         replaced in place (any others of that pair are dropped), never duplicated. A variant whose scorecard has no
         guard_* check gets a warning and no row; a scorecard that is missing or unreadable is an input error (exit 2,
         nothing written). The ledger is written atomically; everything else in it, number text included (fixcheck
         reads the last digit of an `after` for its drift tolerance), layout, line ends and BOM stay as they were.
         Nothing is written when no row came out.
baseline Write the ledger of a user's edit of a finished material (SKILL.md, "Iterate on a finished material"): the
         edit's targeted suite ran into E = T/review/edit<K>/ (K an integer of 1 or more), and this measures it against
         the last green state. E must hold scorecard_<v>.json for every --variants v (de-duplicated in order); any
         missing is an input error naming them all. Each v must be the variant of exactly one T/checks/*.json (its
         `variant`, else its file stem; none, or two or more, is an error). E's suite report is E/suite.json, else
         E/suite_partial.json; the ledger records {file, green, rc} of it (`suite` null and a warning when neither
         exists), and a red one only warns: the ledger is still written.
         The green folder of a variant, unless --green DIR names one for all of them (then its scorecard must exist, with
         a warning when DIR has no green report): the folders T/review/round<N> and T/review/edit<j> other than E whose
         report is green. A round counts by suite.json (green true, rc 0, full true); an edit by suite.json likewise,
         else by suite_partial.json (green true, rc 0). Its scorecard_<v>.json must exist and be no older than the
         report's `started` minus 2 s (a scorecard left from an older run is not green). A stamp ending in Z is UTC; one
         without a zone is this machine's local time; a report whose started or ended cannot be read is not a candidate
         (a warning names it). The latest `ended` wins, on a tie the edit with the highest j, else the round with the
         highest N. No candidate is an input error (pass --green).
         Rows, from the green scorecard G and the edit's scorecard A of each variant, in G's order. A guard_* result of G
         becomes the guard row `rows` makes (bound by the guard's type, factor and floors, note "standard guard (R-13c)";
         the new item has no intended_lowfreq). Another result of G with no skip and no error, a note that does not start
         "vacuous", a numeric value and a [lo, hi] target that is not [null, null] becomes a target row
             {"check", "variant", "role": "target", "target", "before": <G's value>, "severity"}
         Any other result is report-only: no row, its id on the variant's output line. Every row gets "after" from A's
         value for that id; when A has none (no row, an error, a non-number) the row has no `after` and a warning says
         "<id>@<v>: not measured in the edit (<why>)". Ids of A that G lacks get one warning per variant. A repeated
         id in A or G warns, and the first is used.
         E/ledger.json is written atomically, replacing an old one ("replaced" on the last line):
             {"kind": "user_edit", "edit": K, "written": <UTC>, "baseline": {<v>: <green folder relative to T>},
              "suite": {file, green, rc} or null, "items": [{"id": "U<K>", "status": "user_edit", "title": --title
              (default "user edit <K>"), "variants", "acceptance": [rows]}]}
         It has no `apply` key, so no decision row can exempt a row of a user edit; nothing in it is reverted, the edit
         is the user's. Nothing is written when there is no row (exit 2). Output, per variant: its baseline, the row
         counts, the report-only ids, then "now outside target" (a target row whose after misses it while its before met
         it) and "guard over bound" lines; then the warnings and the wrote line. This is a preview: fixcheck.py makes the
         judgement (fixcheck.py --ledger E/ledger.json; its tools default is T, the status user_edit is accepted).
Standard library only (it reads the scorecards' JSON; no numpy), Python 3.9 or newer, no shell: it works on Windows.
Exit code: 0 ok (warnings included); 2 a usage or input error (the message says which; nothing written).
"""
import argparse
import calendar
import datetime
import json
import math
import os
import re
import sys
import time

if sys.version_info < (3, 9):
    sys.stderr.write("guards.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

NOTE_STANDARD = "standard guard (R-13c)"
NOTE_EXEMPT = "intended_lowfreq: exempt"
DEFAULT_MAPS = ["height", "basecolor"]
HARM, LOWF = "tile_harmonic", "lowfreq"
BOM = b"\xef\xbb\xbf"
SLACK = 1e-12  # fixcheck's
STAMP = re.compile(r"^(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d):(\d\d)(?:\.\d+)?(Z|[+-]\d\d:?\d\d)?$")


class Fail(Exception):
    pass


class Num(float):
    """A JSON number that keeps its text, so a rewritten file shows the digits it was written with."""

    def __new__(cls, text):
        x = float.__new__(cls, text)
        x.text = text
        return x


# ----------------------------------------------------------------------------- JSON files that keep their layout


def read_doc(path):
    """(data, layout, text) of a JSON file. layout: how the file was written, which write_doc reproduces."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        raise Fail("%s: %s" % (path, e.strerror or e))
    try:
        text = raw.decode("utf-8-sig")
        data = json.loads(text, parse_float=Num, parse_int=Num)
    except ValueError as e:
        raise Fail("%s: invalid JSON: %s" % (path, e))
    m = re.search(r"^([ \t]+)\S", text, re.M)
    lay = {"bom": raw.startswith(BOM), "eol": "\r\n" if "\r\n" in text else "\n", "step": m.group(1) if m else None,
           "final_nl": text.endswith("\n"), "ascii": not any(ord(ch) > 127 for ch in text)}
    return data, lay, text


def render(v, lay, lvl=0):
    """json.dumps(indent=step) of v, but a Num is written as the text it was read from."""
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


def dump_text(data, lay):
    text = render(data, lay) + ("\n" if lay["final_nl"] else "")
    return text.replace("\n", lay["eol"])  # a JSON string holds no raw newline, so only the layout changes


def write_doc(path, data, lay):
    out = dump_text(data, lay).encode("utf-8")
    tmp = "%s.%d.tmp" % (path, os.getpid())
    try:
        with open(tmp, "wb") as fh:
            fh.write((BOM if lay["bom"] else b"") + out)
        os.replace(tmp, path)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise Fail("%s: cannot write: %s" % (path, e.strerror or e))


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def names_check(entries, cid, variant):
    """True when a list of "<check>@<variant>" or "<check>" strings names this row (fixcheck's rule)."""
    return isinstance(entries, list) and any(isinstance(e, str) and e.strip() in (cid, "%s@%s" % (cid, variant))
                                             for e in entries)


# ----------------------------------------------------------------------------- configs


def guard_checks(m):
    return [{"id": "guard_harm_%s" % m, "type": HARM, "map": m, "stat": "max_amp", "severity": "soft", "guard": True,
             "why": "R-13 standard guard: tile-period stripe"},
            {"id": "guard_lowfreq_%s" % m, "type": LOWF, "map": m, "stat": "std_over_mean", "severity": "soft",
             "guard": True, "why": "R-13 standard guard: low-frequency std"}]


def seam_maps(checks):
    """The maps of every seam check that is not skipped, in order of appearance (matcheck's default: height, basecolor)."""
    out = []
    for c in checks:
        if isinstance(c, dict) and c.get("type") == "seam" and not c.get("skip"):
            maps = c.get("maps", DEFAULT_MAPS)
            for m in maps if isinstance(maps, list) else [maps]:
                if isinstance(m, str) and m and m not in out:
                    out.append(m)
    return out


def cmd_configs(a):
    d = os.path.abspath(a.checks_dir)
    if not os.path.isdir(d):
        raise Fail("no checks folder %s" % d)
    forced = list(dict.fromkeys(a.maps)) if a.maps else None
    todo, lines, added = [], [], 0
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if not name.endswith(".json") or not os.path.isfile(p):
            continue
        cfg, lay, text = read_doc(p)  # an unreadable file stops the run before anything is written
        if not isinstance(cfg, dict) or not isinstance(cfg.get("checks"), list):
            lines.append("%s: skipped, no checks list" % name)
            continue
        have = {c.get("id") for c in cfg["checks"] if isinstance(c, dict)}
        maps = forced or seam_maps(cfg["checks"]) or DEFAULT_MAPS
        new = [c for m in maps for c in guard_checks(m) if c["id"] not in have]
        if not new:
            lines.append("%s: nothing to add (%s already there)" % (name, ", ".join(
                c["id"] for m in maps for c in guard_checks(m))))
            continue
        reformatted = dump_text(cfg, lay) != text.replace("\r\n", "\n").replace("\n", lay["eol"])
        cfg["checks"].extend(new)
        added += len(new)
        todo.append((p, cfg, lay))
        lines.append("%s: %s %s (maps: %s)%s" % (name, "would add" if a.dry_run else "added",
                                                   ", ".join(c["id"] for c in new), ", ".join(maps),
                                                   ", reformatted" if reformatted else ""))
    if not a.dry_run:
        for p, cfg, lay in todo:
            write_doc(p, cfg, lay)
    if lines:
        print("\n".join(lines))
    print("%s %d checks in %d configs%s" % ("would add" if a.dry_run else "added", added, len(todo),
                                            " (dry run, nothing written)" if a.dry_run else ""))


# ----------------------------------------------------------------------------- rows


def read_scorecard(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            card = json.load(fh)
    except OSError as e:
        raise Fail("%s: %s" % (path, e.strerror or e))
    except ValueError as e:
        raise Fail("%s: invalid JSON: %s" % (path, e))
    if not isinstance(card, dict) or not isinstance(card.get("results"), list):
        raise Fail("%s: not a matcheck scorecard (no results list)" % path)
    return card


def bound_hi(before, factor, floor):
    return float("%.6g" % max(factor * before, before + floor))


def guard_rows(card, variant, item, a, warns):
    """The guard rows of one variant's pre-batch scorecard ([] and a warning when it has none)."""
    out, found = [], False
    for r in card["results"]:
        cid = r.get("id") if isinstance(r, dict) else None
        if not (isinstance(cid, str) and cid.startswith("guard_")):
            continue
        found = True
        kind = r.get("type")
        floor = {HARM: a.floor_harm, LOWF: a.floor_lowfreq}.get(kind) if isinstance(kind, str) else None
        where = "%s@%s" % (cid, variant)
        if floor is None:
            warns.append("%s: type %s has no floor (use tile_harmonic or lowfreq): no row" % (where, kind))
            continue
        before = r.get("value")
        if not number(before):
            warns.append("%s: no numeric value in the scorecard (%s): no row" % (
                where, r.get("error") or r.get("note") or json.dumps(before)))
            continue
        row = {"check": cid, "variant": variant, "role": "guard", "before": before}
        if names_check(item.get("intended_lowfreq"), cid, variant):
            row.update(bound=[None, None], note=NOTE_EXEMPT)
        else:
            row.update(bound=[None, bound_hi(before, a.factor, floor)], note=NOTE_STANDARD)
        out.append(row)
    if not found:
        warns.append("%s: scorecard_%s.json has no guard_* check: no guard row for it (run guards.py configs, then the "
                     "suite, before the batch)" % (variant, variant))
    return out


def cmd_rows(a):
    for name, v, lo in (("--factor", a.factor, 1.0), ("--floor-harm", a.floor_harm, 0.0),
                        ("--floor-lowfreq", a.floor_lowfreq, 0.0)):
        if not (math.isfinite(v) and v >= lo):
            raise Fail("%s must be a number of %g or more" % (name, lo))
    path = os.path.abspath(a.ledger)
    led, lay, _ = read_doc(path)
    if not isinstance(led, dict) or not isinstance(led.get("items"), list):
        raise Fail("%s: not an object with an items list (review.md §1 step 4)" % path)
    hits = [it for it in led["items"] if isinstance(it, dict) and it.get("id") == a.item]
    if len(hits) != 1:
        raise Fail("%s: %s" % (path, "no item with id %s" % a.item if not hits else "item id %s appears twice" % a.item))
    item = hits[0]
    acc = item.setdefault("acceptance", [])
    if not isinstance(acc, list) or not all(isinstance(x, dict) for x in acc):
        raise Fail("item %s: acceptance must be a list of rows" % a.item)
    variants = a.variants if a.variants else item.get("variants")
    if not (isinstance(variants, list) and variants and all(isinstance(v, str) and v for v in variants)):
        raise Fail("item %s has no variants list: pass --variants" % a.item if variants is None or variants == [] else
                   "item %s: variants must be a list of variant names" % a.item)
    variants = list(dict.fromkeys(variants))
    cards = {v: read_scorecard(os.path.join(os.path.abspath(a.scorecards), "scorecard_%s.json" % v))
             for v in variants}  # every scorecard is read before any row is made
    warns, new = [], []
    for v in variants:
        new += guard_rows(cards[v], v, item, a, warns)
    added = replaced = 0
    for r in new:
        same = [i for i, x in enumerate(acc) if x.get("check") == r["check"] and x.get("variant") == r["variant"]]
        if same:
            acc[same[0]] = r
            for i in reversed(same[1:]):
                del acc[i]
            replaced += 1
        else:
            acc.append(r)
            added += 1
        bound = r["bound"][1]
        print("%s@%s: before %s, %s" % (r["check"], r["variant"], r["before"],
                                        "bound <= %s" % bound if bound is not None else r["note"]))
    for w in warns:
        print("warning: %s" % w)
    if new:
        write_doc(path, led, lay)
    print("%s: %d guard rows added, %d replaced%s" % (a.item, added, replaced, "" if new else "; ledger not written"))


# ----------------------------------------------------------------------------- baseline


def stamp_epoch(text):
    """Seconds since the epoch of a suite stamp: Z (or an offset) is UTC, no zone is this machine's local time. None
    when it is not a stamp."""
    m = STAMP.match(text.strip()) if isinstance(text, str) else None
    if not m:
        return None
    y, mo, d, h, mi, sec = (int(x) for x in m.groups()[:6])
    zone = m.group(7)
    try:
        if zone is None:
            return time.mktime((y, mo, d, h, mi, sec, 0, 0, -1))
        t = calendar.timegm((y, mo, d, h, mi, sec, 0, 0, 0))
    except (ValueError, OverflowError):
        return None
    if zone != "Z":
        off = (int(zone[1:3]) * 60 + int(zone[-2:])) * 60
        t -= off if zone[0] == "+" else -off
    return t


def read_report(path):
    """The suite report (a dict) or None when the file is absent, unreadable or not an object."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            rep = json.load(fh)
    except (OSError, ValueError):
        return None
    return rep if isinstance(rep, dict) else None


def is_green(rep, need_full):
    rc = rep.get("rc")
    return rep.get("green") is True and type(rc) is int and rc == 0 and (not need_full or rep.get("full") is True)


def green_report(folder, edit):
    """(file name, report) of the report that makes this folder a green state, else None. A round counts by suite.json
    (green, rc 0, full); an edit also by suite_partial.json (green, rc 0)."""
    for name, need_full in (("suite.json", True), ("suite_partial.json", False)):
        if name == "suite_partial.json" and not edit:
            break
        rep = read_report(os.path.join(folder, name))
        if rep is not None and is_green(rep, need_full):
            return name, rep
    return None


def rel_slash(path, base):
    try:
        r = os.path.relpath(path, base)
    except ValueError:
        r = os.path.abspath(path)
    return r.replace(os.sep, "/")


def variant_configs(checks_dir):
    """{variant: [config file names]} of the checks configs (a JSON object with a checks list)."""
    out = {}
    for name in sorted(os.listdir(checks_dir)):
        p = os.path.join(checks_dir, name)
        if not name.endswith(".json") or not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8-sig") as fh:
                c = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(c, dict) and isinstance(c.get("checks"), list):
            out.setdefault(c.get("variant") or name[:-5], []).append(name)
    return out


def green_candidates(review, edit_dir, warns):
    """[(sort key, folder, report name, started epoch)] of the green round and edit folders other than the edit's own."""
    out = []
    try:
        names = sorted(os.listdir(review))
    except OSError:
        return out
    for name in names:
        m = re.fullmatch(r"(round|edit)(\d+)", name)
        folder = os.path.join(review, name)
        if not m or not os.path.isdir(folder) or os.path.realpath(folder) == os.path.realpath(edit_dir):
            continue
        hit = green_report(folder, m.group(1) == "edit")
        if hit is None:
            continue
        rname, rep = hit
        started, ended = stamp_epoch(rep.get("started")), stamp_epoch(rep.get("ended"))
        if started is None or ended is None:
            warns.append("review/%s/%s: started or ended is not a readable stamp (%s, %s): not a green candidate" % (
                name, rname, json.dumps(rep.get("started")), json.dumps(rep.get("ended"))))
            continue
        out.append(((ended, 1 if m.group(1) == "edit" else 0, int(m.group(2))), folder, rname, started))
    return out


def pick_green(cands, v):
    best = None
    for key, folder, rname, started in cands:
        sp = os.path.join(folder, "scorecard_%s.json" % v)
        try:
            fresh = os.path.getmtime(sp) >= started - 2
        except OSError:
            continue
        if fresh and (best is None or key > best[0]):
            best = (key, folder)
    return best[1] if best else None


def target_pair(t):
    return (isinstance(t, (list, tuple)) and len(t) == 2 and all(x is None or number(x) for x in t)
            and list(t) != [None, None] and (t[0] is None or t[1] is None or t[0] <= t[1]))


def scored(r):
    """True when a scorecard result of the green state is a check with a target and a value (a target row)."""
    return (not r.get("skip") and not r.get("error") and not str(r.get("note") or "").startswith("vacuous")
            and number(r.get("value")) and target_pair(r.get("target")))


def first_by_id(card, label, warns):
    """{id: result} of a card's results (the first of a repeated id; a warning), plus the ids in order."""
    out, order = {}, []
    for r in card["results"]:
        cid = r.get("id") if isinstance(r, dict) else None
        if not (isinstance(cid, str) and cid):
            continue
        if cid in out:
            warns.append("%s: id %s appears twice: the first is used" % (label, cid))
            continue
        out[cid] = r
        order.append(cid)
    return out, order


def n6(x):
    return "%.6g" % x


def cmd_baseline(a):
    for name, v, lo in (("--factor", a.factor, 1.0), ("--floor-harm", a.floor_harm, 0.0),
                        ("--floor-lowfreq", a.floor_lowfreq, 0.0)):
        if not (math.isfinite(v) and v >= lo):
            raise Fail("%s must be a number of %g or more" % (name, lo))
    if not re.fullmatch(r"[0-9]+", a.edit) or int(a.edit) < 1:
        raise Fail("--edit must be an integer of 1 or more, not %s" % a.edit)
    k = int(a.edit)
    tools = os.path.abspath(a.tools)
    review = os.path.join(tools, "review")
    edit_dir = os.path.join(review, "edit%d" % k)
    if not os.path.isdir(edit_dir):
        raise Fail("no edit folder %s (the edit's targeted suite writes it)" % edit_dir)
    variants = list(dict.fromkeys(a.variants))
    lack = [v for v in variants if not os.path.isfile(os.path.join(edit_dir, "scorecard_%s.json" % v))]
    if lack:
        raise Fail("%s holds no %s" % (edit_dir, ", ".join("scorecard_%s.json" % v for v in lack)))
    checks_dir = os.path.join(tools, "checks")
    if not os.path.isdir(checks_dir):
        raise Fail("no checks folder %s" % checks_dir)
    cfgs = variant_configs(checks_dir)
    for v in variants:
        n = len(cfgs.get(v, []))
        if n != 1:
            raise Fail("variant %s: %s in %s" % (v, "no checks config has it" if n == 0 else
                                                  "%d configs have it (%s); the ledger cannot say which" % (
                                                      n, ", ".join(cfgs[v])), checks_dir))
    warns = []
    suite = None
    for name in ("suite.json", "suite_partial.json"):
        if os.path.isfile(os.path.join(edit_dir, name)):
            rep = read_report(os.path.join(edit_dir, name))
            rc = rep.get("rc") if rep else None
            suite = {"file": name, "green": bool(rep and rep.get("green") is True),
                     "rc": rc if type(rc) is int else None}
            if rep is None:
                warns.append("review/edit%d/%s is unreadable: counted as red" % (k, name))
            if not suite["green"]:
                warns.append("the edit's suite is red: hard checks failed or measured nothing; see %s" % name)
            break
    if suite is None:
        warns.append("review/edit%d has no suite.json or suite_partial.json: the ledger records no suite" % k)
    greens = {}
    if a.green:
        gdir = os.path.abspath(a.green)
        for v in variants:
            if not os.path.isfile(os.path.join(gdir, "scorecard_%s.json" % v)):
                raise Fail("--green %s holds no scorecard_%s.json" % (gdir, v))
            greens[v] = gdir
        if not green_report(gdir, True):
            warns.append("--green %s has no green report (suite.json green and full, or suite_partial.json green): "
                         "the baseline is taken as given" % gdir)
    else:
        cands = green_candidates(review, edit_dir, warns)
        for v in variants:
            g = pick_green(cands, v)
            if g is None:
                raise Fail("no green scorecard_%s.json in review/round*/ or review/edit*/: pass --green DIR" % v)
            greens[v] = g
    rows, lines, per, rep_only = [], [], {}, {}
    for v in variants:
        g = read_scorecard(os.path.join(greens[v], "scorecard_%s.json" % v))
        e = read_scorecard(os.path.join(edit_dir, "scorecard_%s.json" % v))
        gres, gorder = first_by_id(g, "%s: green scorecard_%s.json" % (v, v), warns)
        eres, eorder = first_by_id(e, "%s: edit scorecard_%s.json" % (v, v), warns)
        vrows, only = [], []
        for cid in gorder:
            r = gres[cid]
            if cid.startswith("guard_"):
                made = guard_rows({"results": [r]}, v, {}, a, warns)
            elif scored(r):
                made = [{"check": cid, "variant": v, "role": "target", "target": list(r["target"]),
                         "before": r["value"], "severity": r.get("severity")}]
            else:
                only.append(cid)
                continue
            for row in made:
                er = eres.get(cid)
                if er is not None and number(er.get("value")):
                    row["after"] = er["value"]
                else:
                    why = ("no row in the edit's scorecard" if er is None else
                           er.get("error") or er.get("note") or "value %s" % json.dumps(er.get("value")))
                    warns.append("%s@%s: not measured in the edit (%s)" % (cid, v, why))
                vrows.append(row)
        new = [cid for cid in eorder if cid not in gres]
        if new:
            warns.append("%s: new since the green state, no before: %s" % (v, ", ".join(new)))
        tr = [r for r in vrows if r["role"] == "target"]
        gr = [r for r in vrows if r["role"] == "guard"]
        lines.append("%s: baseline %s, %d target rows, %d guard rows, %d report-only (%s)" % (
            v, rel_slash(greens[v], tools), len(tr), len(gr), len(only), ", ".join(only) or "none"))
        out_t = []
        for r in tr:
            lo, hi = r["target"]
            if "after" in r and number(r["before"]):
                met = (lo is None or r["before"] >= lo - SLACK) and (hi is None or r["before"] <= hi + SLACK)
                now = (lo is None or r["after"] >= lo - SLACK) and (hi is None or r["after"] <= hi + SLACK)
                if met and not now:
                    out_t.append("%s %s -> %s" % (r["check"], n6(r["before"]), n6(r["after"])))
        if out_t:
            lines.append("%s: now outside target: %s" % (v, ", ".join(out_t)))
        over = ["%s %s -> %s (bound <= %s)" % (r["check"], n6(r["before"]), n6(r["after"]), n6(r["bound"][1]))
                for r in gr if "after" in r and r["bound"][1] is not None and r["after"] > r["bound"][1] + SLACK]
        if over:
            lines.append("%s: guard over bound: %s" % (v, ", ".join(over)))
        rows += vrows
    if not rows:
        raise Fail("no row: the green scorecards hold no scored or guard check for %s" % ", ".join(variants))
    led = {"kind": "user_edit", "edit": k,
           "written": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "baseline": {v: rel_slash(greens[v], tools) for v in variants}, "suite": suite,
           "items": [{"id": "U%d" % k, "status": "user_edit", "title": a.title or "user edit %d" % k,
                      "variants": variants, "acceptance": rows}]}
    path = os.path.join(edit_dir, "ledger.json")
    replaced = os.path.isfile(path)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(led, indent=1) + "\n")
        os.replace(tmp, path)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise Fail("%s: cannot write: %s" % (path, e.strerror or e))
    print("\n".join(lines))
    for w in warns:
        print("warning: %s" % w)
    print("wrote %s: item U%d, %d rows%s; next: fixcheck.py --ledger %s" % (
        path, k, len(rows), ", replaced" if replaced else "", path))


# ----------------------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("configs")
    p.add_argument("--checks-dir", required=True, help="folder of the checks configs, <tools>/checks")
    p.add_argument("--maps", nargs="+", help="maps to guard (default: the maps of the config's seam checks, else "
                                              "height and basecolor)")
    p.add_argument("--dry-run", action="store_true", help="print what would be added, write nothing")
    p = sub.add_parser("rows")
    p.add_argument("--ledger", required=True, help="review/round<N>/ledger.json")
    p.add_argument("--item", required=True, help="ledger item id, e.g. P3")
    p.add_argument("--scorecards", required=True, help="folder of the scorecards measured just before the item's batch")
    p.add_argument("--variants", nargs="+", help="variants to guard (default: the item's variants list)")
    p.add_argument("--factor", type=float, default=1.25, help="bound = max(factor * before, before + floor)")
    p.add_argument("--floor-harm", type=float, default=0.25, help="floor for a tile_harmonic check (default 0.25)")
    p.add_argument("--floor-lowfreq", type=float, default=0.005, help="floor for a lowfreq check (default 0.005)")
    p = sub.add_parser("baseline")
    p.add_argument("--tools", required=True, help="the material's tools folder, T")
    p.add_argument("--edit", required=True, help="K: the edit's suite is in T/review/edit<K>/")
    p.add_argument("--variants", nargs="+", required=True, help="variants the edit touched")
    p.add_argument("--green", help="folder of the green scorecards (default: the latest green round or edit folder)")
    p.add_argument("--title", help="title of the ledger item (default 'user edit K')")
    p.add_argument("--factor", type=float, default=1.25, help="guard bound = max(factor * before, before + floor)")
    p.add_argument("--floor-harm", type=float, default=0.25, help="floor for a tile_harmonic check (default 0.25)")
    p.add_argument("--floor-lowfreq", type=float, default=0.005, help="floor for a lowfreq check (default 0.005)")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        {"configs": cmd_configs, "rows": cmd_rows, "baseline": cmd_baseline}[a.cmd](a)
    except Fail as e:
        sys.stderr.write("guards.py: %s\n" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
