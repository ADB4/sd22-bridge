#!/usr/bin/env python3
"""Write a review round's delta brief and the panel's args from REFERENCE.md, the lens table, the ledger and the
last round's files.

Usage:
    python3 make_brief.py --review-dir <tools>/review --round N [--lenses round<N>/lenses.json] [--checks CFG ...]
                          [--max-lines 250] [--python <venv python>] [--skill-dir <skill>]

Reads review/REFERENCE.md (sections headed `## R<k> <title>`), review/round<N>/lenses.json, review/round<N>/ledger.json
(required from round 2), review/round<N-1>/review_result.json, lead.json, panel_args.json, ledger.json and its lens
files' `started` stamps, the file times under <tools>/build/, and the scorecard of each checks config (default
<tools>/checks/*.json). Writes review/round<N>/BRIEF.md, which every panel agent reads in full (rules, REFERENCE R1,
R5 and R9, decisions, scorecard, ledger, carried items, lens table), and review/round<N>/panel_args.json, the args for
assets/workflows/review_round.js. Prints lines per section, lines to read per lens, seconds, warnings. Each carried item
(ledger ids, the last round's unverified and deferred items, open entries) needs exactly one owner; a lens keyed
`fixcheck` owns every ledger id no other lens names. Documented in references/review.md §1-§3.
Exit code: 0 written (warnings allowed); 1 an ownership error, a round 2+ without a ledger, or an invalid ledger;
2 a usage or REFERENCE error (missing or unreadable file, R1/R5/R9 missing, R5 or R9 still the template's text, a lens
naming a section REFERENCE lacks, a bad lens key). Nothing is written unless it exits 0. Standard library only: it
runs with any python3, no venv.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys
import time

EVERYONE = ("R1", "R5", "R9")  # requirements, node cheat sheet, rubric + verifier checklist: in every delta
RESERVED = ("lead", "reverify", "ledger", "review_result", "lenses", "panel_args")  # <name>.json in round<N>/
KEY_RE = re.compile(r"[A-Za-z0-9_-]+")  # used with fullmatch: `$` would pass a trailing newline
SID_RE = re.compile(r"R[1-9][0-9]*")
PREV_KEYS = ("keep_as_is", "deferred", "premises_corrected")
HEAD_RE = re.compile(r"^## (R[1-9][0-9]*)(?: |$)")
TIME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")
THREADS = "OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2"
CUT = 100


class Fail(Exception):
    def __init__(self, code, msgs):
        Exception.__init__(self, "; ".join(msgs))
        self.code, self.msgs = code, list(msgs)


# ----------------------------------------------------------------------------- small helpers


def read_text(path):
    with open(path, encoding="utf-8-sig") as fh:  # -sig: a BOM (Windows Notepad) would hide a leading `## R1`
        return fh.read()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def flat(s):
    return " ".join(str(s).split())


def cut(s, n=CUT):
    s = flat(s)
    return s if len(s) <= n else s[:n - 3].rstrip() + "..."


def cell(s, n=CUT):
    return cut(s, n).replace("|", "/")


def first_sentence(s, n=90):
    s = " ".join(str(s).split())
    return cut(re.split(r"(?<=[.!?])\s", s, maxsplit=1)[0], n)


def fmt(v):
    if v is None or v == "":
        return "?"
    if isinstance(v, float):
        return "%g" % v
    if isinstance(v, (list, dict)):
        return json.dumps(v)
    return str(v)


def names(xs, n=60):
    return cell(", ".join(map(str, xs)), n) if xs else "none"


def rel(path, base):
    path = os.path.abspath(path)
    r = os.path.relpath(path, base)
    return path if r.startswith("..") else r


def times_in(s):
    """Datetimes in a text; a time without seconds stands for its whole minute. Zone suffixes are ignored: every time
    is read as UTC."""
    return [datetime.datetime.strptime("%s %s:%s:%s" % (m.group(1), m.group(2), m.group(3), m.group(4) or "59"),
                                       "%Y-%m-%d %H:%M:%S") for m in TIME_RE.finditer(s or "")]


def epoch(t):
    return t.replace(tzinfo=datetime.timezone.utc).timestamp()


def measured(v):
    return v is not None and v != "" and v != []


# ----------------------------------------------------------------------------- inputs


def read_reference(path):
    if not os.path.isfile(path):
        raise Fail(2, ["no REFERENCE.md at %s: write it from <skill>/assets/reference_template.md (review.md §2)"
                       % path])
    try:
        lines = read_text(path).rstrip("\n").split("\n")
    except (OSError, UnicodeDecodeError) as e:
        raise Fail(2, ["%s: unreadable or not UTF-8 text (%s): re-save it as UTF-8" % (path, e)])
    header, sections, order, cur = [], {}, [], None
    for ln in lines:
        m = HEAD_RE.match(ln)
        if m:
            cur = m.group(1)
            if cur in sections:
                raise Fail(2, ["%s: section %s appears twice" % (path, cur)])
            sections[cur] = [ln]
            order.append(cur)
        elif cur:
            sections[cur].append(ln)
        else:
            header.append(ln)
    for sid in order:
        while len(sections[sid]) > 1 and not sections[sid][-1].strip():
            sections[sid].pop()
    missing = [s for s in EVERYONE if s not in sections]
    if missing:
        hint = ""
        if any(re.match(r"^## R[0-9]+\.", ln) for ln in lines):
            hint = " (headings must read `## R<k> <title>`, no dot)"
        raise Fail(2, ["%s lacks %s, which every delta brief copies%s" % (path, ", ".join(missing), hint)])
    body = lambda sid: "\n".join(sections[sid][1:])
    unfilled = []
    if not re.search(r"^\|\s*Histogram Scan\s*\|", body("R5"), re.M):
        unfilled.append("R5 has no `| Histogram Scan |` row: copy `references/sd_craft.md` §5 there, verbatim")
    if "Reproduce independently" not in body("R9") or "**high:**" not in body("R9"):
        unfilled.append("R9 lacks the severity rubric (`**high:**`) or the verifier checklist (`Reproduce "
                        "independently`): copy `references/review.md` §2 rubric and target rules and §4 there, verbatim")
    if unfilled:
        raise Fail(2, ["%s: %s (the template's pointer text is not the content)" % (path, u) for u in unfilled])
    pick =lambda tag: next((ln[len(tag):].strip() for ln in header if ln.startswith(tag)), None)
    return {"path": path, "sections": sections, "order": order, "lines": len(lines),
            "valid": pick("Valid for:"), "changed": pick("Changed in the last update:")}


def drift_r5(ref, skill):
    """The path of <skill>/references/sd_craft.md when its §5 differs from REFERENCE R5 (blank lines ignored)."""
    craft = os.path.join(skill, "references", "sd_craft.md")
    try:
        m = re.search(r"^## 5\. [^\n]*\n(.*?)(?=^## \d|\Z)", read_text(craft), re.M | re.S)
    except (OSError, UnicodeDecodeError):
        return None
    norm = lambda s: [ln.rstrip() for ln in s.split("\n") if ln.strip()]
    return craft if m and norm(m.group(1)) != norm("\n".join(ref["sections"]["R5"][1:])) else None


def read_lenses(path, ref):
    if not os.path.isfile(path):
        raise Fail(2, ["no lens table at %s: write round<N>/lenses.json (review.md §3)" % path])
    try:
        data = load_json(path)
    except ValueError as e:
        raise Fail(2, ["%s: invalid JSON: %s" % (path, e)])
    lenses, open_ = (data, []) if isinstance(data, list) else \
        (data.get("lenses"), data.get("open") or []) if isinstance(data, dict) else (None, None)
    if not isinstance(lenses, list) or not lenses:
        raise Fail(2, ["%s: needs a non-empty list of lenses, as {\"lenses\": [...]} or a bare list" % path])
    errs, seen = [], set()
    for i, l in enumerate(lenses):
        if not isinstance(l, dict):
            errs.append("lens %d: not an object" % (i + 1))
            continue
        k = l.get("key")
        kk = str(k or "").lower()
        if not isinstance(k, str) or not KEY_RE.fullmatch(k) or kk in RESERVED or kk in seen \
                or not isinstance(l.get("prompt"), str) or not l["prompt"].strip():
            errs.append("lens %s: needs a prompt and a key of letters, digits, _ or -, unique ignoring case, not %s "
                        "in any case" % (json.dumps(k), ", ".join(RESERVED)))
        seen.add(kk)
        secs = l.get("sections")
        if secs is not None:
            if not isinstance(secs, list) or not all(isinstance(s, str) and SID_RE.fullmatch(s) for s in secs):
                errs.append("lens %s: sections must be a list of REFERENCE ids (R1, R2, ...)" % json.dumps(k))
            else:
                lack = [s for s in secs if s not in ref["sections"]]
                if lack:
                    errs.append("lens %s: names %s, which %s lacks" % (json.dumps(k), ", ".join(lack), ref["path"]))
        owns = l.get("owns")
        if owns is not None and (not isinstance(owns, list) or not all(isinstance(o, str) for o in owns)):
            errs.append("lens %s: owns must be a list of item ids" % json.dumps(k))
    if not isinstance(open_, list) or not all(isinstance(o, dict) and isinstance(o.get("id"), str) and o["id"]
                                              for o in open_):
        errs.append("%s: open must be a list of {\"id\", \"text\"}" % path)
    if errs:
        raise Fail(2, errs)
    for l in lenses:  # a lens without sections (or with an empty list) reads all of REFERENCE.md
        l["sections"] = list(dict.fromkeys(l.get("sections") or []))
        l["owns"] = list(dict.fromkeys(l.get("owns") or []))
    return lenses, open_


def read_ledger(path, rnd):
    if not os.path.isfile(path):
        if rnd >= 2:
            raise Fail(1, ["round %d has no ledger at %s: fill it before the round (review.md §1)" % (rnd, path)])
        return None
    try:
        led = load_json(path)
    except ValueError as e:
        raise Fail(1, ["%s: invalid JSON: %s" % (path, e)])
    errs = []
    if not isinstance(led, dict):
        raise Fail(1, ["%s: not an object with apply, decisions and items (review.md §1)" % path])
    items = led.get("items")
    if not isinstance(items, list):
        errs.append("items must be a list")
        items = []
    ids = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            errs.append("item %d: needs a string id" % (i + 1))
            continue
        if it["id"] in ids:
            errs.append("item id %s appears twice" % it["id"])
        ids.add(it["id"])
        acc = it.get("acceptance", [])
        if not isinstance(acc, list) or not all(isinstance(a, dict) for a in acc):
            errs.append("item %s: acceptance must be a list of {check, variant, target, before, after}" % it["id"])
    dec = led.get("decisions", [])
    if not isinstance(dec, list) or not all(isinstance(d, dict) for d in dec):
        errs.append("decisions must be a list of {question, answer}")
    if not isinstance(led.get("apply", {}), dict):
        errs.append("apply must be an object {started, ended, stall_min}")
    if errs:
        raise Fail(1, ["%s: %s" % (path, e) for e in errs])
    return led


def read_previous(review_dir, rnd, warns):
    """The last round's review_result.json and lead.json (either may be missing). Keep-as-is, deferred and premises
    come from the result's plan (the runner checked it against PLAN), else from lead.json (a dead lead's file)."""
    prev = {"round": rnd - 1, "lead": None, "result": None, "missing": []}
    if rnd < 2:
        return prev
    pd = os.path.join(review_dir, "round%d" % (rnd - 1))
    for key, name in (("lead", "lead.json"), ("result", "review_result.json")):
        p = os.path.join(pd, name)
        if not os.path.isfile(p):
            prev["missing"].append(name)
            continue
        try:
            d = load_json(p)
        except ValueError as e:
            warns.append("round%d/%s: invalid JSON (%s): its items are not carried" % (rnd - 1, name, e))
            prev["missing"].append(name)
            continue
        prev[key] = d if isinstance(d, dict) else None
    plan, src = (prev["result"] or {}).get("plan"), "round%d/lead.json" % (rnd - 1)
    if isinstance(plan, dict):
        if prev["lead"] is not None and (prev["lead"].get("deferred") or []) != (plan.get("deferred") or []):
            warns.append("round%d/lead.json and review_result.json's plan list different deferred items: the plan's "
                         "are carried (r%d:deferred:<k> counts its list)" % (rnd - 1, rnd - 1))
        prev["lead"], src = plan, "round%d/review_result.json's plan" % (rnd - 1)
    lack = [k for k in PREV_KEYS if prev["lead"] is not None and not isinstance(prev["lead"].get(k), list)]
    if lack:
        warns.append("%s has no %s list: none carried from it" % (src, ", ".join(lack)))
    why = {"review_result.json": "its unverified and rejected items are not carried",
           "lead.json": "keep-as-is, deferred and premises come from review_result.json's plan" if prev["lead"]
           else "its keep-as-is, deferred and premises are not carried"}
    for name in prev["missing"]:
        warns.append("round%d/%s is missing: %s" % (rnd - 1, name, why[name]))
    left = left_open(pd, prev["lead"])
    if left:
        warns.append("round%d's lead did not plan, re-defer or close %s, carried and owned that round: add each "
                     "still open to this round's `open` (review.md §3)" % (rnd - 1, cut(", ".join(left), 200)))
    return prev


def left_open(pd, lead):
    """Non-ledger items a lens owned in round<N-1>/panel_args.json that its lead's fixes, deferred, keep_as_is and
    conflicts_resolved never name."""
    try:
        owned = [o for l in load_json(os.path.join(pd, "panel_args.json"))["lenses"] for o in l.get("owns") or []
                 if isinstance(o, str)]
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return []  # a round run before make_brief
    if not owned or not isinstance(lead, dict):
        return []
    try:
        led = {it.get("id") for it in load_json(os.path.join(pd, "ledger.json")).get("items") or []
               if isinstance(it, dict)}
    except (OSError, ValueError, AttributeError):
        led = set()
    text = json.dumps([lead.get(k) for k in ("fixes", "deferred", "keep_as_is", "conflicts_resolved")],
                      ensure_ascii=False)
    return [o for o in dict.fromkeys(owned) if o not in led and not re.search(r"(?<![\w:/-])%s(?![\w/-])" % re.escape(o), text)]


def edited_before_gate(tools, review_dir, rnd, ledger):
    """(round N-1's first lens start, round N's apply start, <tools>/build/ files modified between them). An apply edit
    after the gate moves a file's mtime past the window, so this sees only the edits the apply did not redo."""
    gate = times_in(str(((ledger or {}).get("apply") or {}).get("started") or ""))
    bd = os.path.join(tools, "build")
    if rnd < 2 or not gate or not os.path.isdir(bd):
        return None
    starts = []
    for p in glob.glob(os.path.join(review_dir, "round%d" % (rnd - 1), "*.json")):
        stem = os.path.basename(p)[:-5]
        if stem.lower() in RESERVED or "." in stem:  # <lens>.verdicts.json, lead.json, ledger.json, ...
            continue
        try:
            d = load_json(p)
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and "findings" in d:
            starts += times_in(str(d.get("started") or ""))[:1]
    if not starts:
        return None
    t0, t1 = epoch(min(starts)), epoch(gate[0])
    hits = []
    for root, dirs, files in os.walk(bd):
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
        hits += [rel(os.path.join(root, f), tools) for f in files
                 if not f.startswith(".") and t0 < os.path.getmtime(os.path.join(root, f)) < t1]
    return min(starts), gate[0], sorted(hits)


def carried_items(ledger, prev, open_):
    """Ordered {id: (kind, text)} of every item that needs one owner."""
    out, dup = {}, []

    def add(cid, kind, text):
        if cid in out:
            dup.append(cid)
        else:
            out[cid] = (kind, text)
    for it in (ledger or {}).get("items", []):
        add(it["id"], "ledger", it.get("title", ""))
    r = prev["round"]
    for m in ((prev["result"] or {}).get("unverified") or []):
        if isinstance(m, dict) and m.get("id"):
            add("r%d:%s/%s" % (r, m.get("lens", "?"), m["id"]), "unverified",
                "%s (%s)" % (m.get("title", ""), m.get("why_unverified", "no verdict")))
    for k, d in enumerate((prev["lead"] or {}).get("deferred") or [], 1):
        add("r%d:deferred:%d" % (r, k), "deferred", d if isinstance(d, str) else json.dumps(d))
    for o in open_:
        add(o["id"], "open", o.get("text", ""))
    return out, dup


def assign_owners(lenses, carried, ledger_ids):
    owners = {cid: [] for cid in carried}
    errs = []
    for l in lenses:
        for o in l["owns"]:
            if o in owners:
                owners[o].append(l["key"])
            else:
                errs.append("lens %s owns %r, which is no carried item" % (l["key"], o))
    fix = next((l for l in lenses if l["key"].lower() == "fixcheck"), None)
    defaulted = []
    if fix:
        for cid in ledger_ids:
            if not owners[cid]:
                owners[cid].append(fix["key"])
                defaulted.append(cid)
        fix["owns"] = fix["owns"] + defaulted
    for cid, who in owners.items():
        kind, text = carried[cid]
        what = "%s: %s" % (kind, cut(text, 60)) if cut(text) else kind
        if not who:
            errs.append("%s (%s) has no owner" % (cid, what))
        elif len(who) > 1:
            errs.append("%s (%s) has %d owners: %s" % (cid, what, len(who), ", ".join(who)))
    if errs:
        errs.append("carried items: %s" % (cut(", ".join(carried), 300) if carried else "none this round"))
    return {cid: who[0] for cid, who in owners.items() if who}, defaulted, errs


def scorecards(cfgs, tools, review_dir, rnd, ref):
    """One row per checks config, plus the stale and missing warnings (they also go into §4)."""
    rows, read, warns, newer = [], 0, [], []
    valid = times_in(ref["valid"])
    newest_export = None
    for cp in cfgs:
        try:
            cfg = load_json(cp)
        except (OSError, ValueError) as e:
            warns.append("%s: unreadable config (%s)" % (rel(cp, tools), e))
            continue
        if not isinstance(cfg, dict) or not isinstance(cfg.get("checks"), list):
            continue  # not a checks config
        read += 1
        base = os.path.dirname(os.path.abspath(cp))
        variant = cfg.get("variant") or os.path.splitext(os.path.basename(cp))[0]
        out = cfg.get("out_dir") or base
        out = out if os.path.isabs(out) else os.path.normpath(os.path.join(base, out))
        name = "scorecard_%s.json" % variant
        cands = [p for p in (os.path.join(out, name), os.path.join(review_dir, "round%d" % rnd, name))
                 if os.path.isfile(p)]
        maps = cfg.get("maps") or {}
        mdir = maps.get("dir") or "."
        mdir = mdir if os.path.isabs(mdir) else os.path.normpath(os.path.join(base, mdir))
        mp = os.path.join(mdir, (maps.get("prefix") or "") + "manifest.json")
        exported = None
        if os.path.isfile(mp):
            try:
                exported = load_json(mp).get("exported_at")
            except (OSError, ValueError, AttributeError):
                warns.append("%s: unreadable manifest" % rel(mp, tools))
        if exported and times_in(exported):
            t = times_in(exported)[0]
            newest_export = max(newest_export or t, t)
            if valid and t > max(valid):
                newer.append("%s %s" % (variant, exported))
        if not cands:
            warns.append("%s: no %s next to its config's out_dir: run matcheck before the round" % (variant, name))
            rows.append((variant, "no scorecard", "", "", "", "", rel(cp, tools)))
            continue
        sp = max(cands, key=os.path.getmtime)
        try:
            card = load_json(sp)
        except (OSError, ValueError) as e:
            warns.append("%s: unreadable scorecard (%s)" % (rel(sp, tools), e))
            rows.append((variant, "unreadable", "", "", "", "", rel(sp, tools)))
            continue
        stale = os.path.isfile(mp) and os.path.getmtime(sp) < os.path.getmtime(mp)
        was = ((card.get("manifest") or {}).get("exported_at")) if isinstance(card.get("manifest"), dict) else None
        if stale or (exported and was and was != exported):
            warns.append("%s (%s): %s is older than its export (%s): re-run matcheck"
                         % (variant, rel(cp, tools), rel(sp, tools), exported or "manifest"))
        hf = card.get("hard_failed") or []
        if hf:
            warns.append("%s: hard checks failed (%s): fix every hard failure before a round (review.md §1)"
                         % (variant, ", ".join(hf)))
        hu = names(card["hard_unmeasured"]) if "hard_unmeasured" in card else "n/a"
        rows.append((variant, names(hf), hu, str(len(card.get("soft_failed") or [])), names(card.get("vacuous")),
                     names(card.get("errors")), rel(sp, tools)))
    if newer:
        warns.append("%d export%s newer than every time in REFERENCE `Valid for:` (%s): after the preflight export, "
                     "set Valid for to each manifest's exported_at (review.md §1 step 5)"
                     % (len(newer), "s are" if len(newer) > 1 else " is", cut(", ".join(newer), 120)))
    if newest_export and not valid:
        warns.append("REFERENCE `Valid for:` names no export time: write the exported_at of each manifest there")
    return rows, read, warns


# ----------------------------------------------------------------------------- the brief


def acc_text(a):
    s = a.get("check", "?")
    if a.get("variant"):
        s += " (%s)" % a["variant"]
    s += ": %s -> %s" % (fmt(a.get("before")), fmt(a.get("after")))
    if a.get("target") is not None:
        s += " %s" % fmt(a["target"] if isinstance(a["target"], list) else [a["target"]])
    return s


def build(a, ref, lenses, ledger, prev, carried, owner, defaulted, sc_rows, n_cfg, sc_warns):
    R, RD, DIR = a.round, a.round_dir, a.review_dir
    tools = os.path.dirname(DIR)
    py = '"%s"' % a.python if a.python else '"$(bash "%s/scripts/setup_env.sh")"' % a.skill
    S = []  # (name, lines)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pr = "round%d/" % (R - 1)
    prd = rel(os.path.join(DIR, pr), tools)
    head = ["# Round %d delta brief (%s)" % (R, now), "",
            "Made by `make_brief.py`. Tools folder: `%s`; paths below are relative to it." % tools,
            "- REFERENCE: `%s`. Valid for: %s. Changed in the last update: %s." % (
                rel(ref["path"], tools), (ref["valid"] or "?").rstrip("."), (ref["changed"] or "?").rstrip(".")),
            "- Ledger: %s." % ("`%s` (%d items)" % (rel(a.ledger_path, tools), len(ledger.get("items", [])))
                               if ledger else "none (round 1)"),
            "- Last round: %s." % ("none (round 1)" if R < 2 else ", ".join(
                "`%s/%s`%s" % (prd, f, " missing" if f in prev["missing"] else "")
                for f in ("lead.json", "review_result.json"))),
            "- Scorecards: one per checks config, %d configs (§4)." % n_cfg, "",
            "Read this file in full, then the REFERENCE sections your row in §8 names (verifiers, the re-verify agent "
            "and the lead: all of it)."]
    S.append(("header", head))
    S.append(("1. Rules", [
        "## 1. Rules", "",
        "- Never call substance-designer tools: Designer is single-threaded and reserved for the builder.",
        "- Inputs are read-only. Helper scripts and images only under `%s/agents/round%d/<your label>/`; your result"
        " file is the one other write." % (DIR, R),
        "- Python: `%s` (numpy, scipy, Pillow, OpenCV). Load maps, regions and labels with `%s/scripts/matcheck.py`"
        " (`load_image`, `Ctx`, `label_wrap`); don't write decoders. Maps and loading: REFERENCE R7." % (py, a.skill),
        "- Threads: run Python as `%s <python> ...`, call `cv2.setNumThreads(2)`, one Python process at a time."
        % THREADS,
        "- Time boxes and the finding cap are in your prompt (review_round.js).",
        "- A REFERENCE section: `sed -n '/^## R4 /,/^## R5 /p' \"%s\"` prints R4 (up to the R5 heading)."
        % ref["path"]]))
    body = ["## 2. Read by everyone: REFERENCE R1, R5 and R9", ""]
    for sid in EVERYONE:
        sec = ref["sections"][sid]
        body += ["#" + sec[0]] + sec[1:] + [""]
    S.append(("2. Read by everyone", body[:-1]))
    dec = ["## 3. Decisions at the last gate", ""]
    if R < 2 and not ledger:
        dec.append("None (round 1).")
    elif not (ledger or {}).get("decisions"):
        dec.append("None recorded in the ledger.")
    else:
        for d in ledger["decisions"]:
            dec.append("- Q: %s -> A: %s" % (" ".join(str(d.get("question", "?")).split()),
                                             " ".join(str(d.get("answer", "?")).split())))
    S.append(("3. Decisions", dec))
    sc = ["## 4. Scorecard", ""]
    if sc_rows:
        sc += ["| variant | hard failed | hard unmeasured | soft misses | vacuous | errors | scorecard |",
               "|---|---|---|---|---|---|---|"]
        sc += ["| %s |" % " | ".join(r) for r in sc_rows]
        if any(r[2] == "n/a" for r in sc_rows):
            sc.append("Hard unmeasured `n/a`: a scorecard from a matcheck without that field.")
    else:
        sc.append("No checks configs found.")
    if sc_warns:
        sc += ["", "Warnings:"] + ["- " + w for w in sc_warns]
    S.append(("4. Scorecard", sc))
    lg = ["## 5. Ledger", ""]
    if not ledger:
        lg.append("None (round 1).")
    else:
        ap = ledger.get("apply") or {}
        if ap:
            lg.append("Apply: started %s, ended %s, stall %s min." % (fmt(ap.get("started")), fmt(ap.get("ended")),
                                                                     fmt(ap.get("stall_min"))))
        lg.append("One line per item: status; each acceptance check before -> after [target]; owner. No measured after"
                  " = not_landed.")
        for it in ledger.get("items", []):
            acc = it.get("acceptance") or []
            st = str(it.get("status") or "?")
            if not any(measured(x.get("after")) for x in acc):
                st = "not_landed (builder: %s, no measured after)" % st
            parts = ["- %s %s: %s" % (it["id"], cut(it.get("title", ""), 70), st)]
            parts += [acc_text(x) for x in acc]
            if it.get("note") and it.get("status") != "done":
                parts.append("note: %s" % cut(it["note"], 80))
            lg.append("; ".join(parts) + " (owner: %s)" % owner.get(it["id"], "?"))
    S.append(("5. Ledger", lg))
    ca = ["## 6. Keep-as-is, rejected, deferred, unverified", ""]
    if R < 2:
        ca.append("None (round 1).")
    else:
        fm = os.path.join(DIR, pr, "findings.md")
        ca.append("From round %d; its findings: `%s`%s." % (R - 1, rel(fm, tools), "" if os.path.isfile(fm)
                                                              else " (missing)"))
        lead, res = prev["lead"] or {}, prev["result"] or {}
        # in full, one line each: a 100-char cut once dropped half a Histogram Scan correction and the error came back
        groups = [("Keep-as-is (the regression contract)", [flat(k) for k in lead.get("keep_as_is") or []]),
                  ("Rejected (don't re-report unless it regressed)",
                   [flat("%s/%s %s" % (m.get("lens", "?"), m.get("id", "?"), m.get("title", "")))
                    for m in res.get("rejected") or [] if isinstance(m, dict)]),
                  ("Deferred", [flat("%s %s" % (cid, t)) + " (owner: %s)" % owner.get(cid, "?")
                                for cid, (k, t) in carried.items() if k == "deferred"]),
                  ("Unverified (no verdict last round)", [flat("%s %s" % (cid, t)) + " (owner: %s)" % owner.get(cid, "?")
                                                          for cid, (k, t) in carried.items() if k == "unverified"]),
                  ("Premises the lead corrected", [flat(p) for p in lead.get("premises_corrected") or []])]
        for title, xs in groups:
            ca.append("%s:%s" % (title, "" if xs else " none"))
            ca += ["- " + x for x in xs]
        if prev["missing"]:
            ca.append("Missing: %s." % ", ".join("%s/%s" % (prd, m) for m in prev["missing"]))
    S.append(("6. Carried", ca))
    S.append(("7. Output", [
        "## 7. Output", "",
        "Write your result to `%s/` with json.dump, `started` and `ended` first (schemas in review_round.js):" % RD,
        "- lens `<key>`: `<key>.json` (FINDINGS); a lens cut by its time box sets `box` and lists what it skipped in"
        " `not_reached`",
        "- verifier of `<key>`: `<key>.verdicts.json` (VERDICTS); a finding not re-measured with your own script goes"
        " in `not_checked`, with no verdict",
        "- re-verify agent: `reverify.verdicts.json` (VERDICTS); lead: `lead.json` (PLAN)"]))
    tb = ["## 8. Lenses and owners", "",
          "Each carried item has one owner; other lenses skip it. R1, R5 and R9 are in §2.", "",
          "| lens | scope | owns | REFERENCE sections | lines to read |", "|---|---|---|---|---|"]
    extra = lambda secs: sum(len(ref["sections"][s]) for s in secs if s not in EVERYONE)
    for l in lenses:
        own = ", ".join(l["owns"]) or "none"
        if defaulted and l["key"].lower() == "fixcheck":
            own += " (ledger ids by default)"
        secs = " ".join(l["sections"]) if l["sections"] else "all"
        tb.append("| %s | %s | %s | %s | \0%s\0 |" % (l["key"], cell(first_sentence(l["prompt"])), own, secs, l["key"]))
    tb.append("| verifiers, re-verify, lead | every lens | none | all | \0*\0 |")
    opens = [(cid, t) for cid, (k, t) in carried.items() if k == "open"]
    if opens:
        tb += ["", "Open questions and hypotheses:"]
        tb += ["- %s %s (owner: %s)" % (cid, flat(t), owner.get(cid, "?")) for cid, t in opens]
    S.append(("8. Lenses", tb))
    total = sum(len(x[1]) for x in S) + len(S) - 1  # one blank line between sections
    reads = {l["key"]: (total, extra(l["sections"]) if l["sections"] else ref["lines"]) for l in lenses}
    reads["*"] = (total, ref["lines"])
    text = "\n\n".join("\n".join(x[1]) for x in S) + "\n"
    for k, (d, e) in reads.items():
        text = text.replace("\0%s\0" % k, "%d + %d = %d" % (d, e, d + e), 1)
    return text, [(n, len(x)) for n, x in S], total, reads


# ----------------------------------------------------------------------------- main


def main(argv=None):
    t0 = time.time()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--review-dir", required=True, help="<tools>/review")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--lenses", help="lens table (default round<N>/lenses.json in the review dir)")
    ap.add_argument("--checks", nargs="+", action="append", help="checks configs (default <tools>/checks/*.json)")
    ap.add_argument("--max-lines", type=int, default=250, help="warn above this many brief lines (default 250)")
    ap.add_argument("--python", help="the venv python agents use (default: $(bash <skill>/scripts/setup_env.sh))")
    ap.add_argument("--skill-dir", help="the skill folder (default: this script's)")
    a = ap.parse_args(argv)
    warns = []
    try:
        if a.round < 1:
            raise Fail(2, ["--round must be 1 or more"])
        a.review_dir = os.path.abspath(a.review_dir)
        if not os.path.isdir(a.review_dir):
            raise Fail(2, ["no review dir %s" % a.review_dir])
        a.skill = os.path.abspath(a.skill_dir) if a.skill_dir else \
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        a.round_dir = os.path.join(a.review_dir, "round%d" % a.round)
        tools = os.path.dirname(a.review_dir)
        ref = read_reference(os.path.join(a.review_dir, "REFERENCE.md"))
        lp = a.lenses or os.path.join(a.round_dir, "lenses.json")
        if a.lenses and not os.path.isabs(lp) and not os.path.exists(lp):
            lp = os.path.join(a.review_dir, lp)
        lenses, open_ = read_lenses(lp, ref)
        craft = drift_r5(ref, a.skill)
        if craft:
            warns.append("REFERENCE R5 differs from %s §5: if the skill changed, copy it again, verbatim, keeping the "
                         "node-semantics corrections it lacks (review.md §2)" % craft)
        a.ledger_path = os.path.join(a.round_dir, "ledger.json")
        ledger = read_ledger(a.ledger_path, a.round)
        end = times_in(str(((ledger or {}).get("apply") or {}).get("ended") or ""))
        if end and os.path.getmtime(ref["path"]) < epoch(end[0]):
            warns.append("REFERENCE.md was last written before the apply ended (%s): bring the sections the apply "
                         "changed up to date, then set Valid for (review.md §1 step 5)" % ledger["apply"]["ended"])
        valid = times_in(ref["valid"])
        if end and valid and max(valid) < end[0]:
            warns.append("REFERENCE `Valid for:` names no export after the apply ended (%s; latest %s): export every "
                         "variant (review.md §1 step 1), then set Valid for to the new exported_at (step 5)"
                         % (ledger["apply"]["ended"], max(valid).strftime("%Y-%m-%dT%H:%M:%S")))
        early = edited_before_gate(tools, a.review_dir, a.round, ledger)
        if early and early[2]:
            warns.append("%d build/ file%s edited before the plan gate (after round %d's first lens started %s, before "
                         "the apply started %s): %s. Fix drafts stay in review/drafts/round<N>/ until the gate "
                         "(review.md §6)" % (len(early[2]), "s" if len(early[2]) > 1 else "", a.round - 1,
                                             early[0].strftime("%Y-%m-%dT%H:%M:%S"),
                                             early[1].strftime("%Y-%m-%dT%H:%M:%S"), cut(", ".join(early[2]), 300)))
        prev = read_previous(a.review_dir, a.round, warns)
        carried, dup = carried_items(ledger, prev, open_)
        if dup:
            raise Fail(1, ["carried id %s appears twice (ledger, last round or open): rename the open entry" % d
                           for d in dup])
        ledger_ids = [cid for cid, (k, _) in carried.items() if k == "ledger"]
        owner, defaulted, errs = assign_owners(lenses, carried, ledger_ids)
        if errs:
            raise Fail(1, errs)
        if a.checks:
            cfgs = []
            for c in (c for grp in a.checks for c in grp):
                cfgs += sorted(glob.glob(c)) if any(ch in c for ch in "*?[") else [c]
        else:
            cfgs = sorted(glob.glob(os.path.join(tools, "checks", "*.json")))
        for c in cfgs:
            if not os.path.isfile(c):
                raise Fail(2, ["no checks config %s" % c])
        sc_rows, n_cfg, sc_warns = scorecards(cfgs, tools, a.review_dir, a.round, ref)
        warns += sc_warns
        if not n_cfg:
            warns.append("no checks configs found (%s)" % (", ".join(cfgs) or os.path.join(tools, "checks", "*.json")))
        for l in lenses:
            if not l["sections"]:
                warns.append("lens %s names no REFERENCE sections: it reads all of REFERENCE.md" % l["key"])
        text, sizes, total, reads = build(a, ref, lenses, ledger, prev, carried, owner, defaulted, sc_rows,
                                          n_cfg, sc_warns)
    except Fail as e:
        print("make_brief: nothing written (exit %d)" % e.code, file=sys.stderr)
        for m in e.msgs:
            print("  - %s" % m, file=sys.stderr)
        return e.code
    if total > a.max_lines:
        big = sorted(sizes, key=lambda x: -x[1])[:3]
        warns.append("BRIEF.md has %d lines, over the %d budget; largest sections: %s. Shorten their sources "
                     "(REFERENCE R1/R5/R9, the ledger, the last round's lists), not the copy"
                     % (total, a.max_lines, ", ".join("%s %d" % s for s in big)))
    os.makedirs(a.round_dir, exist_ok=True)
    with open(os.path.join(a.round_dir, "BRIEF.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    args = {"review_dir": a.review_dir, "round": a.round, "lenses": []}
    for l in lenses:
        row = {"key": l["key"], "prompt": l["prompt"]}
        if l["sections"]:
            row["sections"] = l["sections"]
        row["owns"] = l["owns"]
        args["lenses"].append(row)
    if a.python:
        args["python"] = a.python
    args["skill_dir"] = a.skill  # the brief names this skill's matcheck too: the prompts must not fall back elsewhere
    with open(os.path.join(a.round_dir, "panel_args.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(args, fh, indent=1)
        fh.write("\n")
    print("make_brief: round %d -> %s/BRIEF.md, panel_args.json" % (a.round, a.round_dir))
    print("  lines: %s; total %d (budget %d)" % (", ".join("%s %d" % s for s in sizes), total, a.max_lines))
    print("  lines to read: %s; verifiers, re-verify and lead %d + %d = %d" % (
        "; ".join("%s %d + %d = %d" % (k, d, e, d + e) for k, (d, e) in reads.items() if k != "*"),
        reads["*"][0], reads["*"][1], sum(reads["*"])))
    print("  carried items: %d (%s)" % (len(carried), ", ".join("%s %s" % (cid, owner[cid]) for cid in carried)
                                        or "none"))
    print("  %.2f s" % (time.time() - t0))
    for w in warns:
        print("  warning: %s" % w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
