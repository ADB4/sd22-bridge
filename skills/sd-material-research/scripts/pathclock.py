#!/usr/bin/env python3
"""Report where a material run's wall time went, from its stamps and its sessions' workflow records.
The run stamps <tools>/stages.jsonl (SKILL.md stage 0); pathclock reads them and says, per step on the run's path,
the wall minutes against the Target and Expect of the SKILL.md stage table, the waits, the user touches and every
delegated run over 10 minutes. This docstring is the reference.

Usage:
    python pathclock.py STAGES_JSONL [--workflows PATH ...] [--json OUT] [--check-skill]
    python pathclock.py --check-skill

Options:
    STAGES_JSONL   the stamps, one JSON object per line: stage, event, utc, note, and optionally session and effort.
                   `stage` may be missing or null. Touch rows (event touch) have kind (question, restart, paste,
                   approval, commit, other), asked_utc, answered_utc and recommended_taken; they are listed, not timed.
    --workflows    workflow records: files or globs, each file one record (a dict) or a list of them (the shape of
                   the retro's workflows_<id8>.json). Fields used: runId, workflowName, status, startTime (ms since
                   the epoch), durationMs, agentCount, summary. An empty or invalid file is skipped with a note.
                   Default: the distinct `session` values of the stamps (an 8-character prefix or a full id), each
                   globbed as ~/.claude/projects/*/<session>*/workflows/wf_*.json.
    --json         write the same data as JSON to this file
    --check-skill  parse the stage table and the paragraph after it in ../SKILL.md (relative to this script) and
                   compare with TARGETS; print each mismatch; exit 0 if equal, 1 if not. STAGES_JSONL is then optional.
Output: a markdown report on stdout: '## Path clock' (first and last stamp, wall, a Step | Actual | Target | Expect |
vs Expect table in path order, the on-path, wait and unassigned totals and the sum check), then Waits, Overlapped
waits, Unassigned, Touches, Delegated runs over 10 min and Background (docs).

How the clock is read. The rows are sorted by utc (stable) and walked with a current step; each row's effect applies
from its own time on:
    start of S0..S5 sets the step; end of the current stage clears it
    readiness_start / readiness_end   the step 'readiness', then back to the step before it
    panel_launch                      round k += 1, step 'panel R<k>'
    lead_json                         'gate R<k>'
    gate, plan_gate                   'apply R<k>' (plan_gate_ready changes nothing)
    apply_end                         'final gate R<k>' when a final_gate row follows before the next panel_launch
                                      or report_start, else 'boundary R<k>' (and 'final gate R<k>' is not stamped)
    final_gate                        'boundary R<k>' when a panel_launch follows, else no step
    report_start / report_end         'report', then no step
    docs_start / docs_end             no change; docs is background, off the path
    any other event                   no change
Each interval between two consecutive rows goes to the step in force after the first row, except:
    a panel step keeps the interval (the workflow runs on); a pause or resume edge inside it is also listed as an
        overlapped wait. A pause edge is a first row with event handoff, pause or overnight_end or 'pause' in it; a
        resume edge is a second row with event up, resume, new_session or machine or 'resume' in it.
    a pause or resume edge elsewhere is a wait: 'hand-off' up to 30 min, 'stall' beyond
    no step in force: unassigned, labelled by the two rows
The on-path steps, the waits and the unassigned time add up to the wall (last utc minus first utc); the report
prints the check. A step still in force after the last row is marked open.
Delegated runs: every workflow record with durationMs over 600000, with the buckets (steps, waits, unassigned) its
[start, start + duration] overlaps and the minutes in each.
Targets: TARGETS holds the SKILL.md stage table (minutes; Expect is an estimate where `est`); --check-skill keeps the
two in step. Standard library only, Python 3.9 or newer.
Exit code: 0 ok; 1 --check-skill found a mismatch; 2 a usage or input error.
"""
import argparse
import calendar
import glob
import json
import os
import re
import sys
import time

if sys.version_info < (3, 9):
    sys.stderr.write("pathclock.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_MD = os.path.join(HERE, "..", "SKILL.md")

# minutes: (target, expect, expect_is_est), the SKILL.md stage table
TARGETS = {
    "S0": (4, 4, False), "S1": (5, 4, False), "S2": (22, 24, False), "S3": (5, 5, False),
    "readiness": (5, 8, True), "S4": (45, 55, False), "S5": (3, 2, False),
    "panel R1": (42, 47, False), "panel R2": (42, 50, True), "gate": (2, 2, True),
    "apply R1": (85, 115, True), "apply R2": (70, 130, True), "boundary": (3, 4, False),
    "final gate": (6, 6, False), "report": (5, 5, True), "hand-off": (6, 6, True), "docs": (55, 55, False),
}
STAGES = ("S0", "S1", "S2", "S3", "S4", "S5")
PAUSE_EVENTS = ("handoff", "pause", "overnight_end")
RESUME_EVENTS = ("up", "resume", "new_session", "machine")
HANDOFF_MAX = 30.0  # minutes; a longer wait is a stall
LONG_RUN_MS = 600000
SUM_TOLERANCE = 0.05


def parse_utc(s):
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d):(\d\d)(\.\d+)?", str(s))
    if not m:
        raise ValueError("bad utc %r" % (s,))
    parts = [int(g) for g in m.groups()[:6]]
    return calendar.timegm(tuple(parts) + (0, 0, 0)) + (float(m.group(7)) if m.group(7) else 0.0)


def fmt_utc(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def load_rows(path):
    """(rows sorted by time, touch rows, notes). Each row gets `t`, epoch seconds."""
    rows, touches, notes = [], [], []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                r["t"] = parse_utc(r["utc"])
                r["event"] = r.get("event") or ""
            except (ValueError, KeyError, TypeError, AttributeError):
                notes.append("%s line %d skipped (not a stamp)" % (os.path.basename(path), n))
                continue
            (touches if r["event"] == "touch" else rows).append(r)
    rows.sort(key=lambda r: r["t"])
    return rows, touches, notes


def is_pause(a):
    return a["event"] in PAUSE_EVENTS or "pause" in a["event"]


def is_resume(b):
    return b["event"] in RESUME_EVENTS or "resume" in b["event"]


def later(rows, i, events, stop=()):
    """True when a row in `events` comes after row i, before any row in `stop`."""
    for r in rows[i + 1:]:
        if r["event"] in events:
            return True
        if r["event"] in stop:
            return False
    return False


def walk(rows):
    """The step in force after each row, the steps in path order and the final gates left unstamped."""
    step, k, saved = None, 0, None
    after, order, unstamped = [], [], []

    def note(name):
        if name and name not in order:
            order.append(name)

    for i, r in enumerate(rows):
        ev, st = r["event"], r.get("stage")
        if ev == "start" and st in STAGES:
            step = st
        elif ev == "end" and st == step and step is not None:
            step = None
        elif ev == "readiness_start":
            saved, step = step, "readiness"
        elif ev == "readiness_end":
            step = saved
        elif ev == "panel_launch":
            k += 1
            step = "panel R%d" % k
        elif ev == "lead_json":
            step = "gate R%d" % k
        elif ev in ("gate", "plan_gate"):
            step = "apply R%d" % k
        elif ev == "apply_end":
            if later(rows, i, ("final_gate",), ("panel_launch", "report_start")):
                step = "final gate R%d" % k
            else:
                step = "boundary R%d" % k
                unstamped.append("final gate R%d" % k)
                note("final gate R%d" % k)
        elif ev == "final_gate":
            step = "boundary R%d" % k if later(rows, i, ("panel_launch",)) else None
        elif ev == "report_start":
            step = "report"
        elif ev == "report_end":
            step = None
        note(step)
        after.append(step)
    return after, order, unstamped


def target_key(step):
    m = re.match(r"(panel|gate|apply|final gate|boundary) R(\d+)$", step)
    if m:
        kind, k = m.group(1), int(m.group(2))
        if kind in ("panel", "apply"):
            return "%s R%d" % (kind, 1 if k == 1 else 2)
        return kind
    return step if step in TARGETS else None


def load_workflows(specs):
    """(records, notes) from files or globs; each file is a record or a list of records."""
    records, notes, seen = [], [], set()
    for spec in specs:
        paths = sorted(glob.glob(os.path.expanduser(spec))) or [spec]
        for p in paths:
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError) as e:
                notes.append("%s skipped (%s)" % (p, "empty or invalid" if isinstance(e, ValueError) else e))
                continue
            for rec in data if isinstance(data, list) else [data]:
                if not isinstance(rec, dict) or "durationMs" not in rec or "startTime" not in rec:
                    notes.append("%s: a record without startTime and durationMs skipped" % p)
                    continue
                key = rec.get("runId") or id(rec)
                if key not in seen:
                    seen.add(key)
                    records.append(rec)
    return records, notes


def sessions_of(rows, touches):
    out = []
    for r in rows + touches:
        s = r.get("session")
        if s and s not in out:
            out.append(s)
    return out


def default_workflow_specs(sessions):
    root = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    return [os.path.join(root, "*", s + "*", "workflows", "wf_*.json") for s in sessions]


def analyze(stages_path, workflow_specs=None):
    rows, touches, notes = load_rows(stages_path)
    if not rows:
        raise ValueError("no stamps in %s" % stages_path)
    after, order, unstamped = walk(rows)
    minutes, open_steps, waits, overlapped, unassigned, intervals = {}, [], [], [], [], []
    for i in range(len(rows) - 1):
        a, b, step = rows[i], rows[i + 1], after[i]
        m = (b["t"] - a["t"]) / 60.0
        if m <= 0:
            continue
        edge = is_pause(a) or is_resume(b)
        lab = "%s %s -> %s %s" % (a.get("stage") or "-", a["event"], b.get("stage") or "-", b["event"])
        item = {"from_stage": a.get("stage"), "from_event": a["event"], "from_utc": fmt_utc(a["t"]),
                "to_stage": b.get("stage"), "to_event": b["event"], "to_utc": fmt_utc(b["t"]), "minutes": m}
        if step and step.startswith("panel"):
            minutes[step] = minutes.get(step, 0.0) + m
            bucket = step
            if edge:
                overlapped.append(dict(item, step=step))
        elif edge:
            waits.append(dict(item, kind="hand-off" if m <= HANDOFF_MAX else "stall"))
            bucket = "wait " + lab
        elif step is None:
            unassigned.append(dict(item, label=lab))
            bucket = "unassigned " + lab
        else:
            minutes[step] = minutes.get(step, 0.0) + m
            bucket = step
        intervals.append((a["t"], b["t"], bucket))
    if after[-1]:
        open_steps.append(after[-1])
    first, last = rows[0]["t"], rows[-1]["t"]
    wall = (last - first) / 60.0
    on_path = sum(minutes.values())
    wsum = sum(w["minutes"] for w in waits)
    usum = sum(u["minutes"] for u in unassigned)
    steps = []
    for name in order:
        key = target_key(name)
        tgt = TARGETS.get(key) if key else None
        entry = {"name": name, "minutes": minutes.get(name), "open": name in open_steps,
                 "not_stamped": name in unstamped,
                 "target": tgt[0] if tgt else None, "expect": tgt[1] if tgt else None,
                 "expect_is_est": tgt[2] if tgt else None, "vs_expect_pct": None}
        if entry["minutes"] is not None and tgt and tgt[1]:
            entry["vs_expect_pct"] = 100.0 * entry["minutes"] / tgt[1]
        steps.append(entry)
    docs = None
    starts = [r["t"] for r in rows if r["event"] == "docs_start"]
    ends = [r["t"] for r in rows if r["event"] == "docs_end"]
    if starts:
        docs = {"start_utc": fmt_utc(starts[0]), "end_utc": fmt_utc(ends[-1]) if ends else None,
                "minutes": (ends[-1] - starts[0]) / 60.0 if ends else None,
                "target": TARGETS["docs"][0], "expect": TARGETS["docs"][1]}
    tlist = []
    for t in touches:
        w = None
        if t.get("asked_utc") and t.get("answered_utc"):
            try:
                w = (parse_utc(t["answered_utc"]) - parse_utc(t["asked_utc"])) / 60.0
            except ValueError:
                pass
        tlist.append({"stage": t.get("stage"), "kind": t.get("kind") or "other", "utc": fmt_utc(t["t"]),
                      "asked_utc": t.get("asked_utc"), "answered_utc": t.get("answered_utc"), "wait_min": w,
                      "recommended_taken": t.get("recommended_taken")})
    kinds = {}
    for t in tlist:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    questions = [t for t in tlist if t["kind"] == "question"]
    touch_data = {"rows": tlist, "counts": kinds, "total": len(tlist), "questions": len(questions),
                  "recommended_taken": sum(1 for t in questions if t["recommended_taken"])}
    if workflow_specs is None:
        workflow_specs = default_workflow_specs(sessions_of(rows, touches))
    records, wnotes = load_workflows(workflow_specs)
    notes += wnotes
    delegated = []
    for rec in records:
        if rec["durationMs"] <= LONG_RUN_MS:
            continue
        s, e = rec["startTime"] / 1000.0, (rec["startTime"] + rec["durationMs"]) / 1000.0
        during = {}
        for a, b, bucket in intervals:
            ov = min(e, b) - max(s, a)
            if ov > 0:
                during[bucket] = during.get(bucket, 0.0) + ov / 60.0
        delegated.append({"runId": rec.get("runId"), "name": rec.get("workflowName"), "status": rec.get("status"),
                          "agents": rec.get("agentCount"), "start_utc": fmt_utc(s), "start_t": s,
                          "minutes": rec["durationMs"] / 60000.0,
                          "during": [{"bucket": k, "minutes": v} for k, v in during.items()]})
    delegated.sort(key=lambda d: d["start_t"])
    return {"stages": os.path.abspath(stages_path), "rows": len(rows), "sessions": sessions_of(rows, touches),
            "first_utc": fmt_utc(first), "last_utc": fmt_utc(last), "wall_min": wall,
            "steps": steps, "on_path_min": on_path, "waits_min": wsum, "unassigned_min": usum,
            "sum_check": {"sum": on_path + wsum + usum, "wall": wall,
                          "ok": abs(on_path + wsum + usum - wall) <= SUM_TOLERANCE},
            "waits": waits, "overlapped_waits": overlapped, "unassigned": unassigned,
            "touches": touch_data, "delegated": delegated, "docs": docs, "notes": notes}


def f1(x):
    return "%.1f" % x


def render(d):
    out = ["## Path clock", "",
           "First stamp %s, last %s, wall %s min (%s h). %d stamp rows." % (
               d["first_utc"], d["last_utc"], f1(d["wall_min"]), "%.1f" % (d["wall_min"] / 60.0), d["rows"]),
           "", "| Step | Actual | Target | Expect | vs Expect |", "|---|---|---|---|---|"]
    for s in d["steps"]:
        if s["not_stamped"]:
            actual = "not stamped"
        else:
            actual = f1(s["minutes"]) if s["minutes"] is not None else "0.0"
            if s["open"]:
                actual += " (open, in progress at the last stamp)"
        tgt = "-" if s["target"] is None else str(s["target"])
        exp = "-" if s["expect"] is None else str(s["expect"]) + (" est" if s["expect_is_est"] else "")
        vs = "-" if s["vs_expect_pct"] is None or s["not_stamped"] else "%.0f %%%s" % (
            s["vs_expect_pct"], " (est)" if s["expect_is_est"] else "")
        out.append("| %s | %s | %s | %s | %s |" % (s["name"], actual, tgt, exp, vs))
    sc = d["sum_check"]
    out += ["", "On path %s min, waits %s min, unassigned %s min." % (
        f1(d["on_path_min"]), f1(d["waits_min"]), f1(d["unassigned_min"])),
        "Sum check: %s + %s + %s = %s against wall %s: %s." % (
            f1(d["on_path_min"]), f1(d["waits_min"]), f1(d["unassigned_min"]), f1(sc["sum"]), f1(sc["wall"]),
            "ok" if sc["ok"] else "MISMATCH"), "", "### Waits", ""]
    if d["waits"]:
        ho = TARGETS["hand-off"]
        out += ["| From | To | Minutes | Kind | Hand-off target / expect |", "|---|---|---|---|---|"]
        for w in d["waits"]:
            ref = "%d / %d est" % (ho[0], ho[1]) if w["kind"] == "hand-off" else "-"
            out.append("| %s %s %s | %s %s %s | %s | %s | %s |" % (
                w["from_stage"] or "-", w["from_event"], w["from_utc"], w["to_stage"] or "-", w["to_event"],
                w["to_utc"], f1(w["minutes"]), w["kind"], ref))
    else:
        out.append("None.")
    out += ["", "### Overlapped waits", "", "Pause and resume edges inside a panel step; the panel keeps the time.", ""]
    if d["overlapped_waits"]:
        for w in d["overlapped_waits"]:
            out.append("- %s: %s -> %s, %s min (%s -> %s)" % (
                w["step"], w["from_event"], w["to_event"], f1(w["minutes"]), w["from_utc"], w["to_utc"]))
    else:
        out.append("None.")
    out += ["", "### Unassigned", ""]
    if d["unassigned"]:
        for u in d["unassigned"]:
            out.append("- %s: %s min (%s -> %s)" % (u["label"], f1(u["minutes"]), u["from_utc"], u["to_utc"]))
    else:
        out.append("None.")
    t = d["touches"]
    out += ["", "### Touches", ""]
    if t["rows"]:
        out += ["| Stage | Kind | Asked | Answered | Wait min | Recommended taken |", "|---|---|---|---|---|---|"]
        for r in t["rows"]:
            out.append("| %s | %s | %s | %s | %s | %s |" % (
                r["stage"] or "-", r["kind"], r["asked_utc"] or "-", r["answered_utc"] or "-",
                "-" if r["wait_min"] is None else f1(r["wait_min"]),
                "-" if r["recommended_taken"] is None else r["recommended_taken"]))
        out += ["", "Per kind: %s. Total %d. Recommended taken %d of %d questions." % (
            ", ".join("%s %d" % kv for kv in sorted(t["counts"].items())), t["total"], t["recommended_taken"],
            t["questions"])]
    else:
        out.append("No touch rows.")
    out += ["", "### Delegated runs over 10 min", ""]
    if d["delegated"]:
        out += ["| Run | Name | Status | Agents | Start | Minutes | During |", "|---|---|---|---|---|---|---|"]
        for r in d["delegated"]:
            during = "; ".join("%s %s" % (b["bucket"], f1(b["minutes"])) for b in r["during"]) or "-"
            out.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                r["runId"], r["name"], r["status"], r["agents"], r["start_utc"], f1(r["minutes"]), during))
    else:
        out.append("None.")
    out += ["", "### Background", ""]
    dc = d["docs"]
    if dc and dc["minutes"] is not None:
        out.append("Docs (%s -> %s): %s min against target %d, expect %d. Off the path." % (
            dc["start_utc"], dc["end_utc"], f1(dc["minutes"]), dc["target"], dc["expect"]))
    elif dc:
        out.append("Docs started %s and has no docs_end. Off the path." % dc["start_utc"])
    else:
        out.append("No docs stamps.")
    if d["notes"]:
        out += ["", "Notes:"] + ["- " + n for n in d["notes"]]
    return "\n".join(out) + "\n"


def num_est(cell):
    """(number, est) from a table cell like '115 est'."""
    m = re.match(r"\s*(\d+)(\s+est)?\s*$", cell)
    return (int(m.group(1)), bool(m.group(2))) if m else None


def parse_skill(path):
    """{target key: (target, expect, expect_is_est)} read from SKILL.md; {} + a missing list on failure."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    head = next((i for i, ln in enumerate(lines) if ln.startswith("| # | Stage")), None)
    if head is None:
        return {}, ["stage table not found (a header line starting '| # | Stage')"]
    cols = [c.strip() for c in lines[head].strip().strip("|").split("|")]
    if "Target" not in cols or "Expect" not in cols:
        return {}, ["the stage table has no Target and Expect columns"]
    ti, ei = cols.index("Target"), cols.index("Expect")
    found, problems = {}, []
    i = head + 2
    while i < len(lines) and lines[i].startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        i += 1
        if len(cells) <= max(ti, ei) or not cells[0].isdigit():
            continue
        row = int(cells[0])
        if row <= 5:
            t, e = num_est(cells[ti]), num_est(cells[ei])
            if t and e:
                found["S%d" % row] = (t[0], e[0], e[1])
            else:
                problems.append("row %d: cannot read Target / Expect" % row)
        elif row in (6, 7):
            name = "panel" if row == 6 else "apply"
            tv = dict((int(k), int(v)) for k, v, _ in re.findall(r"R(\d+)\s+(\d+)(\s+est)?", cells[ti]))
            ev = dict((int(k), (int(v), bool(est))) for k, v, est in re.findall(r"R(\d+)\s+(\d+)(\s+est)?", cells[ei]))
            for k in (1, 2):
                if k in tv and k in ev:
                    found["%s R%d" % (name, k)] = (tv[k], ev[k][0], ev[k][1])
                else:
                    problems.append("row %d: no R%d in Target / Expect" % (row, k))
    while i < len(lines) and not lines[i].strip():
        i += 1
    para = []
    while i < len(lines) and lines[i].strip():
        para.append(lines[i].strip())
        i += 1
    text = " ".join(para)
    for key, phrase in (("readiness", "readiness and probes"), ("gate", "each auto gate"),
                        ("boundary", "round boundary"), ("final gate", "each final gate"), ("report", "report"),
                        ("hand-off", "each leg hand-off"), ("docs", "docs at the end")):
        m = re.search(phrase + r" (\d+) / (\d+)( est)?", text)
        if m:
            found[key] = (int(m.group(1)), int(m.group(2)), bool(m.group(3)))
        else:
            problems.append("paragraph after the table: '%s T / E' not found" % phrase)
    return found, problems


def check_skill(path=SKILL_MD):
    """Mismatch lines between the SKILL.md table and TARGETS; empty when they agree."""
    found, problems = parse_skill(path)
    out = list(problems)
    for key, want in TARGETS.items():
        got = found.get(key)
        if got is None:
            if not any(key in p for p in problems):
                out.append("%s: not in SKILL.md" % key)
        elif tuple(got) != tuple(want):
            out.append("%s: SKILL.md has target %s, expect %s%s; TARGETS has %s, %s%s" % (
                key, got[0], got[1], " est" if got[2] else "", want[0], want[1], " est" if want[2] else ""))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Per-step wall minutes of a material run against Target and Expect.")
    ap.add_argument("stages", nargs="?", help="the run's stages.jsonl")
    ap.add_argument("--workflows", nargs="+", metavar="PATH", help="workflow record files or globs")
    ap.add_argument("--json", metavar="OUT", help="write the data as JSON here")
    ap.add_argument("--check-skill", action="store_true", help="compare TARGETS with ../SKILL.md")
    args = ap.parse_args(argv)
    if not args.stages and not args.check_skill:
        ap.error("STAGES_JSONL is required unless --check-skill is given")
    if args.stages:
        try:
            data = analyze(args.stages, args.workflows)
        except (OSError, ValueError) as e:
            sys.stderr.write("pathclock: %s\n" % e)
            return 2
        sys.stdout.write(render(data))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1)
    rc = 0
    if args.check_skill:
        bad = check_skill()
        if bad:
            print("SKILL.md and TARGETS differ:")
            for line in bad:
                print("  " + line)
            rc = 1
        else:
            print("SKILL.md and TARGETS agree.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
