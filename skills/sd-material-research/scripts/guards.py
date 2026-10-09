#!/usr/bin/env python3
"""Add the standard guard checks to the checks configs, and bound their values in a fix ledger (R-13).
A guard check reports a map's tile-period stripe or low-frequency std. Its pre-batch value becomes a ledger guard row
with an upper bound, so a fix that adds either defect breaks the bound and fixcheck.py flags guard_broken. This
docstring is the reference.

Usage:
    python guards.py configs --checks-dir T/checks [--maps MAP [MAP ...]] [--dry-run]
    python guards.py rows    --ledger L --item ID --scorecards DIR [--variants V [V ...]] [--factor 1.25]
                             [--floor-harm 0.25] [--floor-lowfreq 0.005]

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
Standard library only (it reads the scorecards' JSON; no numpy), Python 3.9 or newer, no shell: it works on Windows.
Exit code: 0 ok (warnings included); 2 a usage or input error (the message says which; nothing written).
"""
import argparse
import json
import math
import os
import re
import sys

if sys.version_info < (3, 9):
    sys.stderr.write("guards.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

NOTE_STANDARD = "standard guard (R-13c)"
NOTE_EXEMPT = "intended_lowfreq: exempt"
DEFAULT_MAPS = ["height", "basecolor"]
HARM, LOWF = "tile_harmonic", "lowfreq"
BOM = b"\xef\xbb\xbf"


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
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        {"configs": cmd_configs, "rows": cmd_rows}[a.cmd](a)
    except Fail as e:
        sys.stderr.write("guards.py: %s\n" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
