#!/usr/bin/env python3
"""Write a review round's findings.md from the panel's own files, in seconds, without the Workflow runner's result.
The lead's plan and the lens, verdict and re-verify files are all in the round folder as soon as each agent ends
(references/review.md, section 6, "Files and stamps"); the runner's review_result.json only adds the split of findings
into confirmed, rejected and unverified, and it lands later or never. This script does that split itself, so findings.md
never gates the apply for more than seconds. This docstring is the reference.

Usage:
    python findings.py --round-dir <tools>/review/round<N> [--out FILE] [--force]

Inputs, all in the round folder (a missing or unreadable file is reported, never fatal, except lead.json):
    lead.json                    the plan, design calls, scorecard, invariants, deferred, residuals, premises (required)
    panel_args.json, lenses.json the lens keys, in this order of preference; without both, every <key>.json that holds a
                                 "findings" list is a lens
    <lens>.json                  the lens's findings, fix_status, box and stamps; missing or without a findings list:
                                 the lens is dead (review:<lens>), its area is unreviewed
    <lens>.verdicts.json         the lens verifier's verdicts and not_checked ids; missing for a lens with findings:
                                 verify:<lens> is dead
    reverify.verdicts.json       the re-verify agent's verdicts, matched by "<lens>/<id>" or by a bare id that no other
                                 sent finding shares
    review_result.json           when it exists and parses, its confirmed, rejected, unverified, fixStatus, stats,
                                 timing, panel_min and dead are used as they are; otherwise the Status rules of
                                 review.md section 6 are applied here, the same way the runner does
    ledger.json                  this round's apply (the apply the panel reviewed) for TIMING
    ../round<N+1>/ledger.json    this round's panel stamps (apply.split) for TIMING

Status rules (without review_result.json):
    confirmed    a verdict exists and says real true with a severity other than none
    rejected     a verdict says real false or severity none; "artifact" alone never rejects
    unverified   no verdict: the verifier died or listed the id in not_checked, and no re-verify verdict took it. A
                 high or medium without a verdict counts as sent to the re-verify agent; a low is not re-verified

Output (default <round-dir>/findings.md, written to a temporary file and moved into place): the format of review.md
section 5, wrapped at 120 columns:
    # Round N findings; OVERALL (the lead's assessment, then one panel paragraph); Confirmed findings (index, with the
    plan fixes each feeds); Scorecard (SC lines, then INV lines); Plan (=== P<n> title [variants], then sources, WHY,
    CHANGE, ACCEPT, GUARD, TELL, GUARDS); Design calls; FIXSTATUS; SPOT CHECKS; UNVERIFIED; REJECTED; DEFERRED;
    RESIDUALS (only when lead.json has the key); KEEP AS IS; CONFLICTS RESOLVED; PREMISES; TIMING (per-agent table,
    panel_min, dead, stats, the apply this round reviewed and this round's stamps).

Refusal: an existing output file newer than lead.json is not overwritten (someone has added to it since): exit 1, and
nothing is written. --force overwrites it. An older file, or none, is replaced.

Prints one summary line (the path, the counts, the dead agents) and a line per problem input.
Standard library only, Python 3.9 or newer; os.path and UTF-8 throughout, so it runs on Windows.
Exit code: 0 written; 1 refused (findings.md newer than lead.json, no --force); 2 usage error, or the round folder or
lead.json is missing or unreadable.
"""
import argparse
import calendar
import json
import os
import re
import sys
import textwrap
import time

if sys.version_info < (3, 9):
    sys.stderr.write("findings.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

WIDTH = 120
RESERVED = ("lead", "reverify", "ledger", "review_result", "lenses", "panel_args")
SEVERITIES = ("high", "medium", "low")


def load(path):
    """(object, None) for a readable JSON file, else (None, why)."""
    if not os.path.isfile(path):
        return None, "missing"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except (OSError, ValueError) as e:
        return None, "unreadable (%s)" % str(e).splitlines()[0]


def parse_utc(s):
    try:
        return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None


def minutes(t0, t1):
    """One decimal, half up, like the runner's Math.round(ms / 6000) / 10."""
    return int((t1 - t0) * 1000 / 6000.0 + 0.5) / 10.0


def is_hm(f):
    return f.get("severity") in ("high", "medium")


def lens_keys(rd):
    """The lens keys in panel order, and the file they came from."""
    for name in ("panel_args.json", "lenses.json"):
        d, _ = load(os.path.join(rd, name))
        if isinstance(d, dict) and isinstance(d.get("lenses"), list):
            keys = [l["key"] for l in d["lenses"] if isinstance(l, dict) and isinstance(l.get("key"), str)]
            if keys:
                return keys, name
    keys = []
    for name in sorted(os.listdir(rd)):
        if not name.endswith(".json") or name.endswith(".verdicts.json") or name.endswith(".rerun.json"):
            continue
        key = name[:-5]
        if key.lower() in RESERVED:
            continue
        d, _ = load(os.path.join(rd, name))
        if isinstance(d, dict) and isinstance(d.get("findings"), list):
            keys.append(key)
    return keys, "the lens files"


def split_from_files(rd, keys, lead, notes):
    """Apply the Status rules: merge, re-verify matching, split. Returns the same dict shape as the runner's result."""
    merged, fix_status, dead, redo, cut = [], [], [], [], []
    revs, vfiles = {}, {}
    for key in keys:
        rev, why = load(os.path.join(rd, key + ".json"))
        if not (isinstance(rev, dict) and isinstance(rev.get("findings"), list)):
            if why is None:
                why = "no findings list"
            notes.append("lens %s: %s %s; its area is unreviewed" % (key, key + ".json", why))
            revs[key] = None
            dead.append("review:" + key)
            continue
        revs[key] = rev
        sent = [f for f in rev["findings"] if isinstance(f, dict)]
        v, vwhy = load(os.path.join(rd, key + ".verdicts.json"))
        if not (isinstance(v, dict) and isinstance(v.get("verdicts"), list)):
            v = None
            if sent:
                notes.append("verifier %s: %s.verdicts.json %s" % (key, key, vwhy or "has no verdicts list"))
                dead.append("verify:" + key)
        vfiles[key] = v
        nr = rev.get("not_reached") or []
        if (rev.get("box") and rev["box"] != "not_hit") or nr:
            cut.append(key)
        for s in rev.get("fix_status") or []:
            if isinstance(s, dict):
                row = {"lens": key}
                row.update(s)
                fix_status.append(row)
        skipped = set((v or {}).get("not_checked") or [])
        for f in sent:
            m = dict(f)
            m["lens"] = key
            m["status"] = "unverified"
            m["verdict"] = None
            verdict = None
            if v:
                verdict = next((x for x in v["verdicts"] if isinstance(x, dict) and x.get("id") == f.get("id")), None)
            if verdict and f.get("id") not in skipped:
                m["verdict"] = verdict
                m["verified_by"] = "verifier"
            else:
                m["why_unverified"] = ("verifier died" if not v else "verifier not_checked (box)"
                                       if f.get("id") in skipped else "verifier gave no verdict")
                if verdict:
                    m["partial_verdict"] = verdict
                if is_hm(f):
                    redo.append(m)
                else:
                    m["why_unverified"] += "; lows are not re-verified"
            merged.append(m)
    reverify = None
    if redo:
        r, rwhy = load(os.path.join(rd, "reverify.verdicts.json"))
        if isinstance(r, dict) and isinstance(r.get("verdicts"), list):
            reverify = r
        else:
            notes.append("re-verify: reverify.verdicts.json %s" % (rwhy or "has no verdicts list"))
            dead.append("reverify")

        def qid(m):
            return "%s/%s" % (m["lens"], m.get("id"))

        def names(m):
            bare_ok = (len([o for o in redo if o.get("id") == m.get("id")]) == 1
                       and not any(qid(o) == m.get("id") for o in redo))
            return [qid(m), m.get("id")] if bare_ok else [qid(m)]

        skipped = set((reverify or {}).get("not_checked") or [])
        for m in redo:
            vs = (reverify or {}).get("verdicts") or []
            v = None
            for n in names(m):
                v = next((x for x in vs if isinstance(x, dict) and x.get("id") == n), None)
                if v:
                    break
            if v and not any(n in skipped for n in names(m)):
                m["verdict"] = dict(v)
                m["verdict"]["id"] = m.get("id")
                m["verified_by"] = "reverify"
                m.pop("why_unverified", None)
                m.pop("partial_verdict", None)
            else:
                m["why_unverified"] += "; re-verify died" if not reverify else "; re-verify did not check it"
    confirmed, unverified, rejected = [], [], []
    for m in merged:
        v = m["verdict"]
        if v:
            refuted = v.get("real") is False or v.get("severity_adjusted") == "none"
            m["status"] = "rejected" if refuted else "confirmed"
        if m["status"] == "confirmed":
            confirmed.append(m)
        elif m["status"] == "unverified":
            unverified.append(m)
        else:
            rejected.append({"id": m.get("id"), "lens": m["lens"], "title": m.get("title"),
                             "why": m["verdict"].get("reasoning")})
    verified_hm = [m for m in merged if is_hm(m) and m["verdict"]]
    unverified_hm = [m for m in unverified if is_hm(m)]
    stats = {
        "findings": len(merged), "high_medium": len([m for m in merged if is_hm(m)]),
        "confirmed": len(confirmed), "rejected": len(rejected), "unverified": len(unverified),
        "unverified_high_medium": len(unverified_hm), "sent_to_reverify": len(redo),
        "reverified": len([m for m in merged if m.get("verified_by") == "reverify"]),
        "verified_high_medium": len(verified_hm),
        "severity_changed": len([m for m in verified_hm if m["verdict"].get("severity_adjusted") != m.get("severity")]),
        "lenses_boxed": len(cut),
        "premises_corrected": len(lead.get("premises_corrected") or []),
    }
    # the timing table from each agent's own stamps
    timing = []

    def row(agent, o, box=None, with_box=False):
        o = o or {}
        t0, t1 = parse_utc(o.get("started")), parse_utc(o.get("ended"))
        r = {"agent": agent, "started": o.get("started"), "ended": o.get("ended"),
             "min": minutes(t0, t1) if t0 is not None and t1 is not None else None}
        if with_box:
            r["box"] = box
        timing.append(r)

    for key in keys:
        rev = revs.get(key)
        row("review:" + key, rev, (rev or {}).get("box"), True)
        if rev and [f for f in rev["findings"] if isinstance(f, dict)]:
            row("verify:" + key, vfiles.get(key))
    if redo:
        row("reverify", reverify)
    row("synthesize", lead)
    starts = [parse_utc(t["started"]) for t in timing if parse_utc(t["started"]) is not None]
    ends = [parse_utc(t["ended"]) for t in timing if parse_utc(t["ended"]) is not None]
    panel_min = minutes(min(starts), max(ends)) if starts and ends else None
    return {"confirmed": confirmed, "unverified": unverified, "rejected": rejected, "fixStatus": fix_status,
            "stats": stats, "timing": timing, "panel_min": panel_min, "dead": dead}


def sev_of(m):
    """The severity after verification: the verdict's when it names one."""
    v = m.get("verdict") or {}
    s = v.get("severity_adjusted")
    return s if s in SEVERITIES else m.get("severity")


class Out(object):
    def __init__(self):
        self.lines = []

    def raw(self, text=""):
        self.lines.append(text)

    def para(self, text, first="", rest=""):
        """Wrap text at WIDTH. A newline in text starts a new line; first and rest are the indents."""
        text = "" if text is None else str(text)
        for i, ln in enumerate(text.split("\n")):
            ind = first if i == 0 else rest
            if not ln.strip():
                self.lines.append(ind.rstrip() if i == 0 and ind.strip() else "")
                continue
            self.lines.extend(textwrap.wrap(ln, WIDTH, initial_indent=ind, subsequent_indent=rest,
                                            break_long_words=False, break_on_hyphens=False) or [ind.rstrip()])


def paragraphs(text):
    """The lead's assessment as 2 to 6 paragraphs: its own breaks, else sentences grouped to about 900 characters."""
    text = (text or "").strip()
    if not text:
        return []
    if "\n" in text:
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    out, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) > 900:
            out.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        out.append(cur)
    return out


def join_names(xs):
    return ", ".join(xs) if xs else "none"


def ledger_apply(path):
    d, _ = load(path)
    a = d.get("apply") if isinstance(d, dict) else None
    return a if isinstance(a, dict) else None


def render(rd, rnd, keys, lead, res, notes):
    o = Out()
    label = "Round %s findings" % (rnd if rnd is not None else "?")
    review = os.path.basename(os.path.dirname(os.path.abspath(rd))) or "review"
    here = "%s/%s" % (review, os.path.basename(os.path.abspath(rd)))
    fixes = [f for f in lead.get("fixes") or [] if isinstance(f, dict)]
    stats, dead = res["stats"], res["dead"]
    dead_lenses = [d[7:] for d in dead if d.startswith("review:")]

    def plan_of(m):
        ps = ["P%s" % f.get("priority") for f in fixes if m.get("id") in (f.get("source_ids") or [])]
        if ps:
            return "plan " + ", ".join(ps)
        for r in lead.get("residuals") or []:
            if isinstance(r, dict) and r.get("id") == m.get("id"):
                return "residual"
        if any(m.get("id") and m["id"] in str(d) for d in lead.get("deferred") or []):
            return "deferred"
        return "not in the plan"

    o.raw("# " + label)
    o.raw()
    o.raw("## OVERALL")
    for p in paragraphs(lead.get("overall_assessment")):
        o.para(p)
        o.raw()
    panel = ["Panel: %d lens%s (%s). %d finding%s: %d confirmed, %d rejected, %d unverified (%d high or medium)." % (
        len(keys), "" if len(keys) == 1 else "es", ", ".join(keys), stats.get("findings", 0),
        "" if stats.get("findings") == 1 else "s", stats.get("confirmed", 0), stats.get("rejected", 0),
        stats.get("unverified", 0), stats.get("unverified_high_medium", 0))]
    panel.append("Severity changed on %s of %s verified high or medium findings." % (
        stats.get("severity_changed", 0), stats.get("verified_high_medium", 0)))
    boxed = stats.get("lenses_boxed")
    panel.append("%s hit its box." % ("%s lens(es)" % boxed if boxed else "No lens"))
    if dead_lenses:
        panel.append("Returned nothing: %s. Their areas are unreviewed this round." % ", ".join(dead_lenses))
    other_dead = [d for d in dead if not d.startswith("review:")]
    if other_dead:
        panel.append("Also dead: %s." % ", ".join(other_dead))
    o.para(" ".join(panel))
    o.raw()

    o.raw("## Confirmed findings (index)")
    o.para("Severity after verification ('was' gives the lens's severity). The arrow names this round's plan fixes.")
    if not res["confirmed"]:
        o.raw("none")
    for m in res["confirmed"]:
        sev = sev_of(m)
        sevtxt = sev if sev == m.get("severity") else "%s, was %s" % (sev, m.get("severity"))
        o.para("- %s (%s, %s; %s): %s -> %s" % (m.get("id"), m.get("lens"), sevtxt, ", ".join(m.get("variants") or []),
                                                 m.get("title"), plan_of(m)))
    o.raw()

    o.raw("## Scorecard")
    for r in lead.get("requirements_scorecard") or []:
        o.para("SC: %s | %s (%s) | %s" % (r.get("verdict"), r.get("requirement"), r.get("variant"), r.get("evidence")))
    o.raw()
    for r in lead.get("invariants") or []:
        o.para("INV: %s | %s (%s) | %s" % ("pass" if r.get("pass") else "fail", r.get("id"), r.get("variant"),
                                          r.get("value")))
    o.raw()

    o.raw("## Plan")
    if not fixes:
        o.raw("none")
    for f in sorted(fixes, key=lambda x: x.get("priority") or 0):
        # the heading stays on one line, so a reader can grep it
        o.raw("=== P%s %s [%s]" % (f.get("priority"), f.get("title"), ", ".join(f.get("variants") or [])))
        deps = ", ".join("P%s" % d for d in f.get("depends_on") or []) or "none"
        o.para("sources: %s; depends on: %s" % (", ".join(f.get("source_ids") or []) or "none", deps))
        for tag, key in (("WHY", "why"), ("CHANGE", "change"), ("ACCEPT", "acceptance"), ("GUARD", "guard_rails"),
                         ("TELL", "tell")):
            if f.get(key):
                o.para("%s: %s" % (tag, f[key]))
        gs = ["%s@%s [%s, %s]" % (g.get("check"), g.get("variant"),
                                  "open" if (g.get("bound") or [None])[0] is None else g["bound"][0],
                                  "open" if len(g.get("bound") or []) < 2 or g["bound"][1] is None else g["bound"][1])
              for g in f.get("guards") or [] if isinstance(g, dict)]
        if gs:
            o.para("GUARDS: " + "; ".join(gs))
        if f.get("intended_lowfreq"):
            o.para("INTENDED LOWFREQ: " + ", ".join(f["intended_lowfreq"]))
        o.raw()

    o.raw("## Design calls")
    calls = [c for c in lead.get("design_calls") or [] if isinstance(c, dict)]
    if not calls:
        o.raw("none")
    for i, c in enumerate(calls, 1):
        head = "D%d %s" % (i, c.get("question"))
        tail = ["recommended: %s" % c.get("recommended")]
        if c.get("settled"):
            tail.append("settled: %s%s" % (c["settled"], " (%s)" % c["rule"] if c.get("rule") else ""))
        if c.get("changes_spec"):
            tail.append("changes a spec value, a requirement reading or a check target")
        tail.append("affects %s" % c.get("affects"))
        o.para("%s (%s)" % (head, "; ".join(tail)))
        for opt in c.get("options") or []:
            mark = " [recommended]" if opt.get("label") == c.get("recommended") else ""
            o.para("- %s%s: %s" % (opt.get("label"), mark, opt.get("consequence")), first="  ", rest="    ")
            if opt.get("adds_pattern"):
                o.para("adds_pattern %s: %s" % (opt["adds_pattern"], opt.get("pattern_evidence")), first="    ",
                       rest="    ")
    o.raw()

    o.raw("## FIXSTATUS")
    if not res["fixStatus"]:
        o.raw("none")
    for s in res["fixStatus"]:
        o.para("- %s (%s): %s. %s" % (s.get("fix"), s.get("lens"), s.get("status"), s.get("note") or ""))
    o.raw()

    o.raw("## SPOT CHECKS")
    sc = [s for s in lead.get("spot_checks") or [] if isinstance(s, dict)]
    if not sc:
        o.raw("none")
    for s in sc:
        o.para("%s (%s): %s | %s" % (s.get("id"), s.get("lens"), s.get("outcome"), s.get("numbers")))
    o.raw()

    o.raw("## UNVERIFIED")
    if not res["unverified"]:
        o.raw("none (stats: unverified %s, unverified_high_medium %s, sent_to_reverify %s)" % (
            stats.get("unverified", 0), stats.get("unverified_high_medium", 0), stats.get("sent_to_reverify", 0)))
    for m in res["unverified"]:
        o.para("- %s/%s (%s): %s. Why: %s" % (m.get("lens"), m.get("id"), m.get("severity"), m.get("title"),
                                              m.get("why_unverified")))
    o.raw()

    o.raw("## REJECTED")
    if not res["rejected"]:
        o.raw("none (stats: rejected %s)" % stats.get("rejected", 0))
    for m in res["rejected"]:
        o.para("- %s/%s: %s. Why: %s" % (m.get("lens"), m.get("id"), m.get("title"), m.get("why")))
    o.raw()

    o.raw("## DEFERRED")
    if not lead.get("deferred"):
        o.raw("none")
    for i, t in enumerate(lead.get("deferred") or [], 1):
        o.para("%d. %s" % (i, t))
    o.raw()

    if "residuals" in lead:
        o.raw("## RESIDUALS")
        rs = [r for r in lead.get("residuals") or [] if isinstance(r, dict)]
        if not rs:
            o.raw("none")
        for r in rs:
            o.para("- %s (%s, %s; %s; visible at %s): %s Open: %s Next: %s" % (
                r.get("id"), r.get("family"), r.get("severity"), ", ".join(r.get("variants") or []),
                r.get("visible_at"), r.get("numbers"), r.get("why_open"), r.get("next_lever")))
        o.raw()

    for title, key in (("KEEP AS IS", "keep_as_is"), ("CONFLICTS RESOLVED", "conflicts_resolved")):
        o.raw("## " + title)
        xs = lead.get(key) or []
        if not xs:
            o.raw("none")
        for i, t in enumerate(xs, 1):
            o.para("%d. %s" % (i, t))
        o.raw()

    o.raw("## PREMISES")
    if not lead.get("premises_corrected"):
        o.raw("none")
    for t in lead.get("premises_corrected") or []:
        o.para("- " + str(t))
    o.raw()

    o.raw("## TIMING")
    o.raw("| agent | started | ended | min | box |")
    o.raw("|---|---|---|---|---|")
    for t in res["timing"]:
        o.raw("| %s | %s | %s | %s | %s |" % (
            t.get("agent"), t.get("started") or "-", t.get("ended") or "-",
            "-" if t.get("min") is None else "%.1f" % t["min"], t.get("box") or "-"))
    o.raw()
    o.para("panel_min: %s; dead: %s" % ("?" if res["panel_min"] is None else "%.1f" % res["panel_min"],
                                         join_names(dead)))
    o.para("stats: " + json.dumps(stats))
    o.raw()
    prev = ledger_apply(os.path.join(rd, "ledger.json"))
    pn = "round %d's" % (rnd - 1) if rnd and rnd > 1 else "the"
    if prev:
        o.para("apply reviewed by this round (%s apply, %s/ledger.json): started %s, ended %s, stall_min %s." % (
            pn, here, prev.get("started"), prev.get("ended"), prev.get("stall_min")))
        sp = prev.get("split") or {}
        stamps = ", ".join("%s %s" % (k, v) for k, v in sp.items() if k != "note" and v)
        if stamps:
            o.para("Split stamps (%s): %s." % (pn.replace("'s", ""), stamps))
        for k in ("note",):
            if prev.get(k):
                o.para("note: %s" % prev[k])
        for k in ("pause", "resume"):
            if isinstance(prev.get(k), dict):
                p = prev[k]
                o.para("%s %s: %s" % (k, p.get("utc"), p.get("note") or ""))
    elif rnd == 1:
        o.para("apply reviewed by this round: none (round 1 reviews the first build).")
    else:
        o.para("apply reviewed by this round: no apply recorded in %s/ledger.json." % here)
    o.raw()
    nxt = os.path.join(os.path.dirname(os.path.abspath(rd)), "round%d" % (rnd + 1)) if rnd else None
    na = ledger_apply(os.path.join(nxt, "ledger.json")) if nxt else None
    nsp = (na or {}).get("split") or {}
    nstamps = ", ".join("%s %s" % (k, v) for k, v in nsp.items() if k != "note" and v)
    if nstamps:
        o.para("This round's stamps (%s/round%d/ledger.json apply.split): %s." % (review, rnd + 1, nstamps))
    else:
        o.para("This round's stamps: none recorded yet in %s/round%s/ledger.json apply.split." % (
            review, "?" if not rnd else rnd + 1))
    for n in notes:
        o.para("input problem: " + n)
    return o.lines


def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write a review round's findings.md from the panel's files.")
    ap.add_argument("--round-dir", required=True, help="<tools>/review/round<N>")
    ap.add_argument("--out", help="output file (default <round-dir>/findings.md)")
    ap.add_argument("--force", action="store_true", help="overwrite an output newer than lead.json")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    rd = a.round_dir
    if not os.path.isdir(rd):
        sys.stderr.write("findings.py: no round folder %s\n" % rd)
        return 2
    lead_path = os.path.join(rd, "lead.json")
    lead, why = load(lead_path)
    if not isinstance(lead, dict):
        sys.stderr.write("findings.py: lead.json in %s is %s: the lead has not landed, or died\n" % (
            rd, why or "not an object"))
        return 2
    out = a.out or os.path.join(rd, "findings.md")
    if os.path.isfile(out) and not a.force and os.path.getmtime(out) > os.path.getmtime(lead_path):
        sys.stderr.write("findings.py: %s is newer than lead.json; not overwritten (use --force)\n" % out)
        return 1
    m = re.match(r"^round(\d+)$", os.path.basename(os.path.abspath(rd)))
    rnd = int(m.group(1)) if m else None
    result, rwhy = load(os.path.join(rd, "review_result.json"))
    notes = []
    keys, _ = lens_keys(rd)
    if isinstance(result, dict) and isinstance(result.get("confirmed"), list):
        if rnd is None and isinstance(result.get("round"), int):
            rnd = result["round"]
        res = {"confirmed": result["confirmed"], "unverified": result.get("unverified") or [],
               "rejected": result.get("rejected") or [], "fixStatus": result.get("fixStatus") or [],
               "stats": result.get("stats") or {}, "timing": result.get("timing") or [],
               "panel_min": result.get("panel_min"), "dead": result.get("dead") or []}
        res["stats"].setdefault("premises_corrected", len(lead.get("premises_corrected") or []))
        if not keys:
            keys = sorted(set(c.get("lens") for c in res["confirmed"] if c.get("lens")))
        split_from = "review_result.json"
    else:
        if result is not None or rwhy != "missing":
            notes.append("review_result.json %s: using the lens and verdict files" % (rwhy or "has no confirmed list"))
        if not keys:
            sys.stderr.write("findings.py: no lenses in %s (no panel_args.json, lenses.json or lens file)\n" % rd)
            return 2
        res = split_from_files(rd, keys, lead, notes)
        split_from = "the lens and verdict files"
    text = "\n".join(render(rd, rnd, keys, lead, res, notes)).rstrip("\n") + "\n"
    out_dir = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    atomic_write(out, text)
    st = res["stats"]
    print("wrote %s: %d lines from %s; %s confirmed, %s rejected, %s unverified; dead: %s" % (
        out, text.count("\n"), split_from, st.get("confirmed", 0), st.get("rejected", 0), st.get("unverified", 0),
        join_names(res["dead"])))
    for n in notes:
        print("note: " + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
