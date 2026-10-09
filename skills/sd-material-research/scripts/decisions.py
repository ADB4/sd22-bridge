#!/usr/bin/env python3
"""Log the calls an unattended material run settles without the user, and keep a patch per applied plan item.
Design calls, look trades, draft questions and technical choices are logged so the user can reverse one the next day;
each applied plan item keeps its own patch so one fix can be reverted while the later fixes stay. This docstring is
the reference.

Usage:
    python decisions.py add         --tools T --round N --row JSON|@FILE
    python decisions.py list        --tools T [--kind K] [--json]
    python decisions.py snap        --tools T --round N --item P --files F [F ...]
    python decisions.py patch       --tools T --round N --item P
    python decisions.py revert-plan --tools T (--id D<n>-<k> | --round N --item P)
    python decisions.py revert      --tools T --round N --item P [--dry-run]

T is the material's tools folder; F is relative to T (an absolute path under T is accepted). Files under T/review:
    decisions.json  {"rows": [...]}, append-only. Row: id "D<round>-<k>" (round 0 = before the first review; k counts
                    per round from 1), utc, kind, question, options [str], recommended (str or null), chosen, rule,
                    gave_up (the target given up and why, one line, may be ""), items [plan item ids], scripts
                    [stage-script paths relative to T], revert {alternative: the lead's option text plus the
                    draft's alternative section, else "draft at reversal", est_min: int or null, graphs: [str]},
                    note (optional). kind: design_call, requirement_trade, look_trade, draft_question, technical,
                    deviation_from_user_answer, not_made_needs_user, user_steer, user_edit. rule: recommended,
                    no_pattern, smallest_pattern, requirement_trade, technical_default, user.
    patches/r<N>/<P>/pre/<F>  copies of the files item P will edit, taken before the edit (snap)
    patches/r<N>/<P>/snap.json  {"files": [...]}: every snapped file, a file with no pre copy did not exist yet
    patches/r<N>/<P>.patch     unified diff (difflib, 3 lines of context, a/<F> b/<F>, /dev/null for an added
                    file) of every snapped file, pre -> current (patch)
    patches/order.jsonl  one line per written patch {utc, round, item, files (those it changed)}, application order
Subcommands:
    add          append a row to round N: --row is a JSON object or @path to a file holding one. Required: kind,
                 question, chosen, rule; the rest default (options [], recommended null, gave_up "", items [],
                 scripts [], revert as above). The script sets id and utc and prints the id.
    list         Markdown table (id, kind, question, chosen, rule, gave_up, items, est_min), requirement_trade rows
                 first, then id order; --kind filters, --json prints the rows instead.
    snap         copy the files before the item edits them; one snap per item (refused once its patch exists).
    patch        write the item's patch after the edit and its order.jsonl line; print the path and the hunk count.
                 A second patch for the same item rewrites the patch and moves its line to the end.
    revert-plan  for a decision id (its items in that round) or one item: the patch, the dependents (items applied
                 later that touched the same files; revert them first, latest first, or the revert may conflict),
                 the graphs to rebuild, est_min and the alternative text from the decision row(s).
    revert       apply the item's patch backwards. Each hunk's "after" lines (context + added) are found in the
                 current file as an exact block; found once, or several times with one starting at the hunk's
                 recorded new-file line, it is replaced by the "before" lines (context + removed). An added file
                 is deleted only if it still holds the added content. If any hunk of any file cannot be placed,
                 nothing is changed and each conflicting hunk is printed. --dry-run checks and writes nothing.
Files are read and written as UTF-8 without newline translation, so CRLF and a missing final newline survive.
Standard library only, Python 3.9 or newer; no patch or git is run, so it works on Windows.
Exit code: 0 ok; 1 conflict, missing patch or refused; 2 usage or validation error (the message names the field).
"""
import argparse
import datetime
import difflib
import json
import os
import re
import shutil
import sys
import time

if sys.version_info < (3, 9):
    sys.stderr.write("decisions.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

KINDS = ("design_call", "requirement_trade", "look_trade", "draft_question", "technical",
         "deviation_from_user_answer", "not_made_needs_user", "user_steer", "user_edit")
RULES = ("recommended", "no_pattern", "smallest_pattern", "requirement_trade", "technical_default", "user")
FIELDS = ("id", "utc", "kind", "question", "options", "recommended", "chosen", "rule", "gave_up", "items", "scripts",
          "revert", "note")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
ID_RE = re.compile(r"^D(\d+)-(\d+)$")
ITEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class Fail(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, msg)
        self.code = code


def read_text(path):
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(text)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def review_path(tools, *parts):
    return os.path.join(tools, "review", *parts)


def item_dir(tools, rnd, item):
    return review_path(tools, "patches", "r%d" % rnd, item)


def patch_path(tools, rnd, item):
    return item_dir(tools, rnd, item) + ".patch"


def check_item(item):
    if not ITEM_RE.match(item):
        raise Fail(2, "--item %r: use letters, digits, '.', '_' and '-' only" % item)
    return item


def rel_of(tools, f):
    full = os.path.abspath(f if os.path.isabs(f) else os.path.join(tools, f))
    try:
        r = os.path.relpath(full, os.path.abspath(tools)).replace(os.sep, "/")
    except ValueError:
        r = ".."
    if r == "." or r.split("/")[0] == "..":
        raise Fail(2, "--files %s: not under the tools folder" % f)
    return r


class Lock:
    """An add reads and rewrites decisions.json; a lock file keeps two parallel adds from losing a row."""

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        end = time.time() + 15
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > 60:
                        os.remove(self.path)  # left by a crashed add
                except OSError:
                    pass
                if time.time() > end:
                    raise Fail(1, "%s is held by another add; remove it if none is running" % self.path)
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            os.remove(self.path)
        except OSError:
            pass


# ---- decisions.json

def load_rows(tools):
    p = review_path(tools, "decisions.json")
    if not os.path.exists(p):
        return []
    try:
        rows = json.loads(read_text(p))["rows"]
    except (ValueError, KeyError, TypeError):
        rows = None
    if not isinstance(rows, list):
        raise Fail(2, '%s is not {"rows": [...]}' % p)
    return rows


def is_strs(v):
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def check_row(row):
    if not isinstance(row, dict):
        raise Fail(2, "row: must be a JSON object")
    for k in row:
        if k not in FIELDS:
            raise Fail(2, "row.%s: unknown field" % k)
    for k in ("kind", "question", "chosen", "rule"):
        if not isinstance(row.get(k), str) or not row[k].strip():
            raise Fail(2, "row.%s: required, a non-empty string" % k)
    for k, enum in (("kind", KINDS), ("rule", RULES)):
        if row[k] not in enum:
            raise Fail(2, "row.%s: %r is not one of %s" % (k, row[k], ", ".join(enum)))

    def get(src, k, default, ok, what, name):
        v = src.get(k, default)
        if not ok(v):
            raise Fail(2, "%s.%s: must be %s" % (name, k, what))
        return v

    out = {"kind": row["kind"], "question": row["question"],
           "options": get(row, "options", [], is_strs, "a list of strings", "row"),
           "recommended": get(row, "recommended", None, lambda v: v is None or isinstance(v, str), "a string or null", "row"),
           "chosen": row["chosen"], "rule": row["rule"],
           "gave_up": get(row, "gave_up", "", lambda v: isinstance(v, str), "a string", "row"),
           "items": get(row, "items", [], is_strs, "a list of strings", "row"),
           "scripts": get(row, "scripts", [], is_strs, "a list of strings", "row")}
    rv = get(row, "revert", {}, lambda v: isinstance(v, dict), "an object", "row")
    for k in rv:
        if k not in ("alternative", "est_min", "graphs"):
            raise Fail(2, "row.revert.%s: unknown field" % k)
    out["revert"] = {
        "alternative": get(rv, "alternative", "draft at reversal", lambda v: isinstance(v, str), "a string", "row.revert"),
        "est_min": get(rv, "est_min", None, lambda v: v is None or (isinstance(v, int) and not isinstance(v, bool)),
                       "an integer or null", "row.revert"),
        "graphs": get(rv, "graphs", [], is_strs, "a list of strings", "row.revert")}
    if "note" in row:
        out["note"] = get(row, "note", "", lambda v: isinstance(v, str), "a string", "row")
    return out


def cmd_add(a):
    raw = a.row
    if raw.startswith("@"):
        try:
            raw = read_text(raw[1:])
        except OSError as e:
            raise Fail(2, "--row: cannot read %s: %s" % (raw[1:], e))
    try:
        row = json.loads(raw.lstrip("﻿"))
    except ValueError as e:
        raise Fail(2, "--row: not valid JSON: %s" % e)
    new = check_row(row)
    path = review_path(a.tools, "decisions.json")
    with Lock(path + ".lock"):
        rows = load_rows(a.tools)
        ks = [int(m.group(2)) for m in (ID_RE.match(str(r.get("id"))) for r in rows) if m and int(m.group(1)) == a.round]
        new = dict([("id", "D%d-%d" % (a.round, max(ks or [0]) + 1)), ("utc", utc())] + list(new.items()))
        write_text(path + ".tmp", json.dumps({"rows": rows + [new]}, indent=1, ensure_ascii=False) + "\n")
        os.replace(path + ".tmp", path)
    print(new["id"])


def id_key(r):
    return tuple(int(x) for x in re.findall(r"\d+", str(r.get("id"))))


def cmd_list(a):
    rows = load_rows(a.tools)
    if a.kind:
        if a.kind not in KINDS:
            raise Fail(2, "--kind: %r is not one of %s" % (a.kind, ", ".join(KINDS)))
        rows = [r for r in rows if r.get("kind") == a.kind]
    rows = sorted(rows, key=lambda r: (r.get("kind") != "requirement_trade", id_key(r)))
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return
    cols = ("id", "kind", "question", "chosen", "rule", "gave_up", "items", "est_min")

    def cell(r, c):
        v = (r.get("revert") or {}).get("est_min") if c == "est_min" else r.get(c, "")
        v = ", ".join(map(str, v)) if isinstance(v, list) else ("" if v is None else str(v))
        return " ".join(v.split()).replace("|", "\\|")

    print("| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in rows:
        print("| " + " | ".join(cell(r, c) for c in cols) + " |")


# ---- patches

def split_lines(text):
    lines = text.split("\n")
    last = lines.pop()
    return [x + "\n" for x in lines] + ([last] if last else [])


def rng(start, stop):
    n = stop - start
    return str(start + 1) if n == 1 else "%d,%d" % (start + 1 - (n == 0), n)


def make_patch(rel, pre, cur):
    """Unified diff of pre -> cur (None = the file does not exist); a line with no final newline gets git's marker."""
    a, b = split_lines(pre or ""), split_lines(cur or "")
    out = ["--- %s\n" % ("a/" + rel if pre is not None else "/dev/null"),
           "+++ %s\n" % ("b/" + rel if cur is not None else "/dev/null")]
    groups = list(difflib.SequenceMatcher(None, a, b, autojunk=False).get_grouped_opcodes(3))

    def emit(sign, seq):
        for ln in seq:
            out.append(sign + ln + ("" if ln.endswith("\n") else "\n\\ No newline at end of file\n"))

    for g in groups:
        out.append("@@ -%s +%s @@\n" % (rng(g[0][1], g[-1][2]), rng(g[0][3], g[-1][4])))
        for tag, i1, i2, j1, j2 in g:
            if tag == "equal":
                emit(" ", a[i1:i2])
            else:
                emit("-", a[i1:i2])
                emit("+", b[j1:j2])
    return "".join(out), len(groups)


def parse_patch(text):
    """-> [{old, new, path, hunks: [{head, os, ol, ns, nl, lines: [[sign, text with its newline]]}]}]"""
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    files, i = [], 0
    while i < len(lines):
        m = HUNK_RE.match(lines[i])
        if lines[i].startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old, new = lines[i][4:], lines[i + 1][4:]
            f = {"old": None if old == "/dev/null" else old[2:], "new": None if new == "/dev/null" else new[2:], "hunks": []}
            f["path"] = f["new"] or f["old"]
            files.append(f)
            i += 2
        elif m and files:
            h = {"head": lines[i], "os": int(m.group(1)), "ol": int(m.group(2) or 1),
                 "ns": int(m.group(3)), "nl": int(m.group(4) or 1), "lines": []}
            i += 1
            need_o, need_n = h["ol"], h["nl"]
            while need_o > 0 or need_n > 0:
                if i >= len(lines) or lines[i][:1] not in (" ", "-", "+"):
                    raise Fail(1, "malformed patch near %s" % h["head"])
                sign = lines[i][0]
                need_o -= int(sign != "+")
                need_n -= int(sign != "-")
                h["lines"].append([sign, lines[i][1:] + "\n"])
                i += 1
                if i < len(lines) and lines[i].startswith("\\"):  # "\ No newline at end of file"
                    h["lines"][-1][1] = h["lines"][-1][1][:-1]
                    i += 1
            files[-1]["hunks"].append(h)
        else:
            i += 1
    return files


def patch_stats(files):
    lines = [s for f in files for h in f["hunks"] for s, _ in h["lines"]]
    return sum(len(f["hunks"]) for f in files), lines.count("+"), lines.count("-")


def read_snap(tools, rnd, item):
    p = os.path.join(item_dir(tools, rnd, item), "snap.json")
    return json.loads(read_text(p))["files"] if os.path.isfile(p) else None


def read_order(tools):
    p = review_path(tools, "patches", "order.jsonl")
    rows = []
    for ln in (read_text(p).split("\n") if os.path.isfile(p) else []):
        try:
            rows.append(json.loads(ln))
        except ValueError:
            pass
    return rows


def cmd_snap(a):
    item = check_item(a.item)
    old = read_snap(a.tools, a.round, item) or []
    rels = [rel_of(a.tools, f) for f in a.files]
    if os.path.exists(patch_path(a.tools, a.round, item)) and any(r in old for r in rels):
        raise Fail(1, "refused: r%d/%s is already snapped and patched (snap once per item)" % (a.round, item))
    for r in rels:
        src, dst = os.path.join(a.tools, r), os.path.join(item_dir(a.tools, a.round, item), "pre", r)
        if os.path.isdir(src):
            raise Fail(2, "--files %s: a folder" % r)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        elif os.path.exists(dst):
            os.remove(dst)  # re-snap of a file that is now absent
        print("snapped r%d/%s %s%s" % (a.round, item, r, "" if os.path.isfile(src) else " (absent: an added file)"))
    write_text(os.path.join(item_dir(a.tools, a.round, item), "snap.json"),
               json.dumps({"files": sorted(set(old) | set(rels))}, indent=1) + "\n")


def cmd_patch(a):
    item = check_item(a.item)
    snapped = read_snap(a.tools, a.round, item)
    if snapped is None:
        raise Fail(1, "r%d/%s: nothing snapped; run snap before the edit" % (a.round, item))
    text, changed = "", []
    for rel in snapped:
        pf, cf = os.path.join(item_dir(a.tools, a.round, item), "pre", rel), os.path.join(a.tools, rel)
        pre = read_text(pf) if os.path.isfile(pf) else None
        cur = read_text(cf) if os.path.isfile(cf) else None
        if pre != cur:
            text += make_patch(rel, pre, cur)[0]
            changed.append(rel)
    pp = patch_path(a.tools, a.round, item)
    write_text(pp, text)
    op = review_path(a.tools, "patches", "order.jsonl")
    line = json.dumps({"utc": utc(), "round": a.round, "item": item, "files": changed}) + "\n"
    prior = read_order(a.tools)
    if any((o.get("round"), o.get("item")) == (a.round, item) for o in prior):  # a second patch moves the item to the end
        write_text(op, "".join(json.dumps(o) + "\n" for o in prior if (o.get("round"), o.get("item")) != (a.round, item)) + line)
    else:
        with open(op, "a", encoding="utf-8", newline="") as f:
            f.write(line)
    nh, plus, minus = patch_stats(parse_patch(text))
    print(pp)
    print("%d hunks, %d files, +%d -%d lines%s" % (nh, len(changed), plus, minus, "" if text else " (no change since the snap: empty patch)"))


def cmd_revert_plan(a):
    rows = load_rows(a.tools)
    if a.id:
        m = ID_RE.match(a.id)
        hit = [r for r in rows if r.get("id") == a.id]
        if a.round is not None or a.item or not m or not hit:
            raise Fail(2, "--id %s: not a decision id in this log, or combined with --round/--item" % a.id)
        rnd, items, drows = int(m.group(1)), list(hit[0].get("items", [])), hit
    else:
        if a.round is None or not a.item:
            raise Fail(2, "give --id, or --round with --item")
        rnd, items = a.round, [check_item(a.item)]
        drows = [r for r in rows if ID_RE.match(str(r.get("id"))) and int(ID_RE.match(r["id"]).group(1)) == rnd
                 and items[0] in r.get("items", [])]
    print("## Revert plan: %s" % (a.id or "r%d/%s" % (rnd, items[0])))
    for r in drows:
        print("Decision %s (%s): %s -> chosen: %s" % (r["id"], r.get("kind"), r.get("question"), r.get("chosen")))
    if not drows:
        print("No decision row names this item.")
    if not items:
        print("The decision names no plan item: nothing to revert.")
    order, missing, targets, deps = read_order(a.tools), False, {(rnd, i) for i in items}, {}
    for i in items:
        pp = patch_path(a.tools, rnd, i)
        if not os.path.isfile(pp):
            print("\nNo patch for r%d/%s (%s)" % (rnd, i, pp))
            missing = True
            continue
        text = read_text(pp)
        print("\n### Patch r%d/%s: %s\n%s" % (rnd, i, pp, text or "(empty patch)"))
        mine = {f["path"] for f in parse_patch(text)}
        pos = max([k for k, o in enumerate(order) if (o.get("round"), o.get("item")) == (rnd, i)] or [-1])
        for k, o in enumerate(order):
            shared = mine & set(o.get("files", []))
            if k > pos >= 0 and (o.get("round"), o.get("item")) not in targets and shared:
                deps.setdefault(k, set()).update(shared)
    print("\n### Dependents: revert these first, latest first, or the revert may conflict")
    for k in sorted(deps, reverse=True):
        print("- r%s/%s touched %s" % (order[k].get("round"), order[k].get("item"), ", ".join(sorted(deps[k]))))
    if not deps:
        print("- none")
    revs = [r.get("revert") or {} for r in drows]
    ests = [v["est_min"] for v in revs if v.get("est_min") is not None]
    print("\n### Rebuild\ngraphs: %s\nest_min: %s" % (", ".join(sorted({g for v in revs for g in v.get("graphs", [])})) or "none",
                                                      sum(ests) if ests else "unknown"))
    for r, v in zip(drows, revs):
        print("\n### Alternative (%s)\n%s" % (r["id"], v.get("alternative", "draft at reversal")))
    return 1 if missing else 0


def locate(lines, h):
    """Index in lines where the hunk's after-block starts, or (None, why)."""
    after = [t for s, t in h["lines"] if s != "-"]
    n = len(after)
    cands = [i for i in range(len(lines) - n + 1) if lines[i:i + n] == after]
    want = h["ns"] - 1 if h["nl"] else h["ns"]
    if len(cands) == 1:
        return cands[0], n
    if want in cands:
        return want, n
    return None, "block not found" if not cands else "ambiguous: %d matches, none at line %d" % (len(cands), h["ns"])


def plan_revert(tools, files):
    """-> (writes {rel: new text, or None to delete}, conflicts [(rel, hunk header, why)]); touches nothing."""
    writes, bad = {}, []
    for f in files:
        rel = f["path"]
        cf = os.path.join(tools, rel)
        cur = read_text(cf) if os.path.isfile(cf) else None
        sel = lambda keep: "".join(t for h in f["hunks"] for s, t in h["lines"] if s != keep)
        if f["old"] is None:  # added file
            if cur == sel("-"):
                writes[rel] = None
            else:
                bad.append((rel, "(added file)", "missing" if cur is None else "content differs from the added content"))
        elif f["new"] is None:  # deleted file
            if cur is None:
                writes[rel] = sel("+")
            elif cur != sel("+"):
                bad.append((rel, "(deleted file)", "exists with other content"))
        elif cur is None:
            bad.append((rel, "", "file is missing"))
        else:
            lines, placed, n_bad = split_lines(cur), [], len(bad)
            for h in f["hunks"]:
                idx, n = locate(lines, h)
                if idx is None:
                    bad.append((rel, h["head"], n))
                else:
                    placed.append((idx, n, [t for s, t in h["lines"] if s != "+"]))
            placed.sort(key=lambda p: p[0])
            if any(p[0] + p[1] > q[0] for p, q in zip(placed, placed[1:])):
                bad.append((rel, "", "two hunks map to overlapping blocks"))
            if len(bad) == n_bad:
                for idx, n, before in reversed(placed):  # from the end, so earlier indices stay valid
                    lines[idx:idx + n] = before
                writes[rel] = "".join(lines)
    return writes, bad


def cmd_revert(a):
    item = check_item(a.item)
    pp = patch_path(a.tools, a.round, item)
    if not os.path.isfile(pp):
        raise Fail(1, "no patch for r%d/%s (%s)" % (a.round, item, pp))
    files = parse_patch(read_text(pp))
    writes, bad = plan_revert(a.tools, files)
    if bad:
        for rel, head, why in bad:
            print("conflict: %s %s: %s" % (rel, head, why))
        raise Fail(1, "r%d/%s cannot be reverted now; nothing changed. Revert the items applied later that touch "
                      "the same files first (revert-plan)" % (a.round, item))
    if not a.dry_run:
        for rel, text in writes.items():
            if text is None:
                os.remove(os.path.join(a.tools, rel))
            else:
                write_text(os.path.join(a.tools, rel), text)
    print("%s r%d/%s: %s" % ("dry-run, would revert" if a.dry_run else "reverted", a.round, item,
                             ", ".join(sorted(writes)) or "nothing (empty patch)"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def sp(name, rnd=False, item=False):
        p = sub.add_parser(name)
        p.add_argument("--tools", required=True, help="the material's tools folder T")
        if rnd:
            p.add_argument("--round", type=int, required=True, help="review round (0 = before the first)")
        if item:
            p.add_argument("--item", required=True, help="plan item id, e.g. P3")
        return p

    p = sp("add", rnd=True)
    p.add_argument("--row", required=True, help="a JSON object, or @path to a file holding one")
    p = sp("list")
    p.add_argument("--kind")
    p.add_argument("--json", action="store_true")
    sp("snap", rnd=True, item=True).add_argument("--files", nargs="+", required=True)
    sp("patch", rnd=True, item=True)
    p = sp("revert-plan")
    p.add_argument("--id")
    p.add_argument("--round", type=int)
    p.add_argument("--item")
    sp("revert", rnd=True, item=True).add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if getattr(a, "round", None) is not None and a.round < 0:
        ap.error("--round must be 0 or more")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        if not os.path.isdir(a.tools):
            raise Fail(2, "--tools %s is not a folder" % a.tools)
        return {"add": cmd_add, "list": cmd_list, "snap": cmd_snap, "patch": cmd_patch,
                "revert-plan": cmd_revert_plan, "revert": cmd_revert}[a.cmd](a) or 0
    except Fail as e:
        sys.stderr.write("decisions.py: %s\n" % e)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
