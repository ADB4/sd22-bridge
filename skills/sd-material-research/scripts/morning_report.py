#!/usr/bin/env python3
"""Write the morning report of an unattended material run: one REPORT.md, verdict first, decisions and residuals as
tables, honest severities, and one answer batch that includes the commits. Run at the stop point (SKILL.md, Unattended
run). It reads files only, never calls Designer and never commits. This docstring is the reference.

Usage:
    python morning_report.py --tools T [--out T/REPORT.md] [--rounds N ...] [--stages FILE] [--cap 500]
    python morning_report.py --tools T --addendum --kind user_edit --text "..." [--edit K] [--rows JSON] [--out T/REPORT.md]

T is the material's tools folder. It is only read. The report goes to --out (default T/REPORT.md) and is replaced whole;
stdout gets the report path, the prose word count and the answer batch. --rounds keeps only those review/round<N>
folders (default: all). --stages reads the stamps from another file (default T/stages.jsonl). --cap changes the 500-word
prose cap (the spec value is 500).

Inputs, all optional. A file that is absent or unreadable becomes a "missing: <file>" line in the section that uses it:
    RUN.json                       mode, stop_reason (optional), deadline_local, estimate, incidents [{utc, by, text}],
                                   proposed_commits [{repo, files, message}], eye_requirements ["R13"] (optional),
                                   material (optional name)
    stages.jsonl                   the stamps; pathclock.py reads them (section 9, wall time)
    review/round<N>/suite.json     the newest one is the final gate (green, rc 0 and full)
    review/round<N>/fixcheck/fixcheck.json   the newest one; a round<N>/fixcheck.json is the panel's fixcheck lens file
                                   and is never read as fixcheck output. Per-item "regressed" and "guard_broken" lists and
                                   top-level "regression_counts" are read when present, else "not measured"
    review/round<N>/review_result.json, lead.json   a round with either is a panel round
    review/round<N>/ledger.json    round N's ledger records the apply of panel N-1's plan (review.md section 1)
    review/decisions.json          read with decisions.py's reader (load_rows)
    review/eye*.json               {item, tell_seen, finding_still_visible, files} (an object, or a list of them)
    review/eye_final.json          the final eye pass: a list, or an object holding a list under presets, items,
                                   sightings, rows, findings, results or entries; each entry has item (or preset, variant,
                                   name, id), what it sees (sees, seen, sightings, description, finding, text, note) and files
    review/steer.jsonl             {utc, session, text}
    review/REFERENCE.md            names the requirements judged by eye alone (a "- **R13** ... Eye criteria" line)

Sections, in this order, under "## <n>. <title>" headings (the answer batch closes the file):
    1. Verdict            8 lines or fewer: finished or stopped early and why; final gate with its stamp; rounds run;
                          highs unfixed from the last panel ("R2-panel highs unfixed"); R-13 flags; calls to check; wall
                          time; and the line "hard checks guard against wrong builds; in M8 they caught 0 visible highs".
                          A high is unfixed unless every plan fix naming it (source_ids) is done, landed in fixcheck and
                          not reverted in the ledger of that panel's apply (round N+1); a high with no recorded apply is
                          unfixed.
    2. Look first         3-6 image paths to send with SendUserFile: the compare sheets, the eye agent's flagged sheets
                          and the tiled 3x3 albedo sheets of the flagged variants first, from the final gate's folder.
    3. Decisions made for you   every decisions.json row, requirement_trade rows first, then id order, each with
                          "say reverse <id> (~N min)" from the row's revert.est_min ("~? min" when null).
    4. Needs you          decisions of kind not_made_needs_user; lead design calls over the cap (deferred entries that
                          start "design call"); steer messages after the last apply ended (requested changes).
    5. Open defects by severity   rows tagged "panel R<k>" (a confirmed finding of the last panel that is not fixed, or a
                          residual of any panel) or "not reviewed by a panel (R<k> apply)" (non-exempt regressed and
                          guard_broken rows, exempt ones marked, reverted fixes, eye tells and still-visible findings);
                          sorted high, medium, low, unrated. The severity caveat ("as rated by the R<k> panel before
                          the R<k> apply; in M8 the next panel rated 2 such mediums high", k the last panel) and the
                          status of the requirements judged by eye alone (RUN.json eye_requirements, else REFERENCE.md,
                          else R13) come first. Then the
                          residual table (the leads' residuals; for a lead with no residuals key, the last panel's
                          unplanned findings, marked derived), the rounds table and the fix ledger table (every item).
    6. Final eye pass     eye_final.json and the eye*.json rows, marked not panel-verified.
    7. Incidents and recoveries   RUN.json incidents, and ledger items whose note starts "reverted".
    8. Proposed commits   RUN.json proposed_commits as a table; else "none proposed". None is ever made.
    9. Timing against targets   pathclock.py's report for the stamps (imported; its first heading is dropped, and its
                          sub-sections that only say "None." become one "Nothing to report" line).

Prose and the cap. Prose is every line except table rows (start with "|"), fenced code and lines holding only
backtick-quoted paths; words are whitespace-separated tokens (what wc -w counts, markers included). The script counts
it, prints "prose words: N", and when N is over the cap it shortens: a run of detail lines (the bullets of section 4,
pathclock's prose lines) becomes one line holding the path of the file that carries the detail (a round's findings.md
for panel content, else decisions.json, steer.jsonl or stages.jsonl), largest run first, until N is within the cap.
Table rows, headings, the verdict, the caveat, the "missing:" lines and the answer batch are never touched.

Answer batch, a numbered list at the end of REPORT.md and on stdout, so a typed reply works:
    1. Reverse any decision? say 'reverse <id>'      then the 3 most consequential rows the run decided on its own
       (requirement_trade first, then by revert minutes; user_steer, user_edit and not_made_needs_user rows are not
       offered) and "None (Recommended)"
    2... one item per proposed commit: "commit <n>: <message> - yes/no". Never a push, never an ask to push.

Addendum. --addendum appends "## Addendum <utc> (<kind>)" to the existing report and rewrites nothing before it:
the --text (what changed, and the decisions row id), then --rows: a JSON list of objects (a table), an object (keys
decision or decision_id, suite, guards [objects] become a "Decisions row" line, a "Targeted suite" line and a table; other
keys a one-row table), or a list of scalars. Use it after a user edit: what changed, the targeted suite and guard
results, the decisions row id. Addenda are not counted against the cap. For --kind user_edit on a material with no
report yet, the file is created first ("# <material> report", a line saying no morning report was written for this
material and that the file holds its edit addenda; material = RUN.json `material`, else the tools folder's name without
a trailing _tools) and the line "created <path>" is printed; any other kind still needs the report.
--edit K (an integer of 1 or more; only with --addendum --kind user_edit; <tools>/review/edit<K> must be a folder) builds
the rows from that edit's folder instead of a hand-written --rows: the Decisions row line (the last decisions.json row of
kind user_edit whose items hold U<K>, else "none logged"), the Targeted suite line (edit<K>/suite.json, else
suite_partial.json: green with its rc, or red with each red job and its first reason) and a table of rows row, before,
after, target, flag: first a fixcheck summary (regressed, guard broken, outside target, of n rows, exit rc, from
edit<K>/fixcheck/fixcheck.json), then each fixcheck row that is regressed, guard_broken or misses its target, with the
exempt reason when it has one, then one row per entry of edit<K>/eye.json (new defect or no new defect, with what the eye
agent saw). A file that is absent or unreadable becomes a "missing:" or "unreadable:" cell, never an error. --rows given
as well is rendered after the --edit block.

Standard library only, Python 3.9 or newer; os.path and UTF-8 throughout, so it runs on Windows. pathclock.py and
decisions.py are imported from this script's folder.
Exit code: 0 report written within the cap; 1 written but the prose is still over the cap after shortening; 2 usage
error (no tools folder, no report to append to except for a user_edit addendum, bad --rows, bad --edit:
--edit without --addendum or with another --kind, K below 1, a missing edit folder).
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.dont_write_bytecode = True
if sys.version_info < (3, 9):
    sys.stderr.write("morning_report.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CAP = 500
QUA4 = "hard checks guard against wrong builds; in M8 they caught 0 visible highs"
CAVEAT = "as rated by the R%d panel before the R%d apply; in M8 the next panel rated 2 such mediums high"
SEV_RANK = {"high": 0, "medium": 1, "low": 2, "unrated": 3}
NOT_OWN = ("user_steer", "user_edit", "not_made_needs_user")
SECTIONS = ("1. Verdict", "2. Look first", "3. Decisions made for you", "4. Needs you", "5. Open defects by severity",
            "6. Final eye pass", "7. Incidents and recoveries", "8. Proposed commits", "9. Timing against targets")
EYE_ID_KEYS = ("item", "preset", "variant", "name", "id")
EYE_TEXT_KEYS = ("sees", "seen", "sightings", "description", "finding", "text", "note")
EYE_LIST_KEYS = ("presets", "items", "sightings", "rows", "findings", "results", "entries")
ZONE_RE = re.compile(r"(Z|[+-]\d\d:?\d\d)$")
PATHCLOCK_EMPTY = ("None.", "No touch rows.", "No docs stamps.")
PATH_ONLY_RE = re.compile(r"^\s*(?:[-*]\s+|\d+[.)]\s+)?(?:`[^`]+`[\s,;]*)+$")


# ---- small helpers

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slash(p):
    return p.replace(os.sep, "/")


def rel_path(tools, path):
    try:
        r = os.path.relpath(path, tools)
    except ValueError:
        return slash(path)
    if r.startswith(".."):
        return slash(os.path.abspath(path))
    return slash(r)


def read_json(path):
    """-> (object, None), or (None, 'absent'), or (None, 'unreadable (...)')."""
    if not os.path.isfile(path):
        return None, "absent"
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f), None
    except (OSError, ValueError) as e:
        return None, "unreadable (%s)" % ((str(e).splitlines() or [""])[0][:70])


def read_jsonl(path):
    if not os.path.isfile(path):
        return None, "absent"
    rows = []
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    rows.append(r)
    except OSError as e:
        return None, "unreadable (%s)" % str(e)[:70]
    return rows, None


def one_line(s):
    return " ".join(str(s).split())


def cell(s, n=None):
    t = one_line("" if s is None else s).replace("|", "\\|")
    if n and len(t) > n:
        t = t[:n - 3].rstrip() + "..."
    return t or "-"


def short_words(s, n):
    w = one_line("" if s is None else s).split(" ")
    return " ".join(w[:n]) + ("..." if len(w) > n else "")


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt_num(v):
    if num(v):
        return str(int(v)) if float(v).is_integer() else "%.1f" % v
    return "?"


def plural(n, one, many=None):
    return "%d %s" % (n, one if n == 1 else (many or one + "s"))


def list_of(v):
    return v if isinstance(v, list) else []


def id_key(r):
    return tuple(int(x) for x in re.findall(r"\d+", str(r.get("id"))))


def yn(v):
    if v is True:
        return "yes"
    if v is False:
        return "no"
    return cell(v)


def truthy(v):
    if isinstance(v, str):
        return v.strip().lower() not in ("", "no", "none", "false", "n/a", "0", "not seen", "null")
    return bool(v)


# ---- the document and the prose count

def is_table(line):
    return line.lstrip().startswith("|")


def prose_lines(text):
    fence = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence or not line.strip() or is_table(line) or PATH_ONLY_RE.match(line):
            continue
        yield line


def prose_words(text):
    return sum(len(line.split()) for line in prose_lines(text))


class Doc(object):
    """Lines with a kind: core (never shortened), detail (a shortenable line with the file that holds the full text),
    table."""

    def __init__(self):
        self.items = []

    def add(self, text, kind="core", ref=None):
        self.items.append({"t": text, "k": kind, "ref": ref})

    def blank(self):
        if self.items and self.items[-1]["t"] != "":
            self.add("")

    def h(self, text, level=2):
        self.blank()
        self.add("#" * level + " " + text)
        self.blank()

    def table(self, headers, rows):
        self.blank()
        self.add("| " + " | ".join(headers) + " |", "table")
        self.add("|" + "---|" * len(headers), "table")
        for r in rows:
            self.add("| " + " | ".join(r) + " |", "table")
        self.blank()

    def render(self):
        return "\n".join(i["t"] for i in self.items).rstrip("\n") + "\n"

    def detail_runs(self):
        runs, cur = [], None
        for idx, it in enumerate(self.items):
            if it["k"] == "detail" and cur is not None and self.items[cur[-1]]["ref"] == it["ref"] \
                    and cur[-1] == idx - 1:
                cur.append(idx)
            elif it["k"] == "detail":
                cur = [idx]
                runs.append(cur)
            else:
                cur = None
        return runs

    def collapse(self, run):
        ref = self.items[run[0]]["ref"]
        self.items[run[0]:run[-1] + 1] = [{"t": "- `%s`" % ref, "k": "core", "ref": None}]


def enforce_cap(doc, cap):
    """Collapse detail runs, largest first, until the prose is within the cap. -> number of runs collapsed."""
    moved = 0
    while prose_words(doc.render()) > cap:
        runs = doc.detail_runs()
        if not runs:
            break
        best = max(runs, key=lambda r: sum(len(doc.items[i]["t"].split()) for i in r))
        doc.collapse(best)
        moved += 1
    return moved


# ---- context and loading

class Ctx(object):
    def __init__(self, tools, out, only, stages, cap):
        self.tools = os.path.abspath(tools)
        self.review = os.path.join(self.tools, "review")
        self.out = out or os.path.join(self.tools, "REPORT.md")
        self.only = set(only or [])
        self.stages = stages or os.path.join(self.tools, "stages.jsonl")
        self.cap = cap
        self.missing = {}

    def p(self, *parts):
        return os.path.join(self.tools, *parts)

    def rel(self, path):
        return rel_path(self.tools, path)

    def miss(self, section, path_or_label, why=None):
        label = path_or_label
        if os.path.isabs(str(path_or_label)):
            label = self.rel(path_or_label)
        self.missing.setdefault(section, []).append("missing: %s%s" % (label, " (%s)" % why if why else ""))

    def n_missing(self):
        return sum(len(v) for v in self.missing.values())


def load_fixcheck(round_dir):
    """round<N>/fixcheck/fixcheck.json. round<N>/fixcheck.json is the panel's lens file: read only if it looks like
    fixcheck output."""
    p = os.path.join(round_dir, "fixcheck", "fixcheck.json")
    obj, err = read_json(p)
    if err != "absent":
        return obj, err, p
    p2 = os.path.join(round_dir, "fixcheck.json")
    obj, err = read_json(p2)
    if isinstance(obj, dict) and isinstance(obj.get("items"), list) and isinstance(obj.get("counts"), dict):
        return obj, err, p2
    return None, "absent", p


def load_rounds(ctx):
    rounds = {}
    try:
        names = os.listdir(ctx.review)
    except OSError:
        names = []
    for name in names:
        m = re.match(r"^round(\d+)$", name)
        d = os.path.join(ctx.review, name)
        if not m or not os.path.isdir(d):
            continue
        n = int(m.group(1))
        if ctx.only and n not in ctx.only:
            continue
        R = {"n": n, "dir": d, "rel": ctx.rel(d)}
        for key, fname in (("lead", "lead.json"), ("result", "review_result.json"), ("ledger", "ledger.json"),
                           ("suite", "suite.json")):
            R[key], R[key + "_err"] = read_json(os.path.join(d, fname))
            R[key + "_path"] = os.path.join(d, fname)
        R["fixcheck"], R["fixcheck_err"], R["fixcheck_path"] = load_fixcheck(d)
        R["findings_path"] = os.path.join(d, "findings.md")
        R["panel"] = R["lead_err"] != "absent" or R["result_err"] != "absent"
        plan = R["lead"] if isinstance(R["lead"], dict) else None
        if plan is None and isinstance(R["result"], dict) and isinstance(R["result"].get("plan"), dict):
            plan = R["result"]["plan"]
        R["plan"] = plan
        rounds[n] = R
    return rounds


def detail_ref(ctx, R, fallback="lead_path"):
    """The file that holds a round's detail: findings.md when it exists, else the lead or result file."""
    if os.path.isfile(R["findings_path"]):
        return ctx.rel(R["findings_path"])
    return ctx.rel(R[fallback])


# ---- analysis

def eff_sev(f):
    v = f.get("verdict") if isinstance(f.get("verdict"), dict) else {}
    s = v.get("severity_adjusted") or f.get("severity")
    return s if s in ("high", "medium", "low") else "unrated"


def ledger_lookup(ledger):
    by_id, by_num = {}, {}
    for it in list_of((ledger or {}).get("items")):
        if not isinstance(it, dict):
            continue
        by_id[str(it.get("id"))] = it
        d = re.sub(r"\D", "", str(it.get("id")))
        if d:
            by_num.setdefault(int(d), it)
    return by_id, by_num


def fix_states(plan, ledger, fixcheck):
    """{fix priority: (state, ledger item)}; state is landed, partial, not_landed, not_done, reverted or unrecorded."""
    out = {}
    by_id, by_num = ledger_lookup(ledger)
    fc = {}
    for it in list_of((fixcheck or {}).get("items")):
        if isinstance(it, dict):
            fc[str(it.get("id"))] = it
    for fx in list_of((plan or {}).get("fixes")):
        if not isinstance(fx, dict):
            continue
        prio = fx.get("priority")
        it = by_id.get("P%s" % prio)
        if it is None and num(prio):
            it = by_num.get(int(prio))
        if it is None:
            out[prio] = ("unrecorded", None)
            continue
        status, note = it.get("status"), str(it.get("note") or "")
        verdict = (fc.get(str(it.get("id"))) or {}).get("verdict")
        if re.match(r"\s*reverted\b", note, re.I):
            out[prio] = ("reverted", it)
        elif status == "done":
            out[prio] = ("not_landed" if verdict == "not_landed" else "landed", it)
        elif status == "partial":
            out[prio] = ("partial", it)
        else:
            out[prio] = ("not_done", it)
    return out


def finding_state(f, plan, states):
    """-> (state, ['P3 partial', ...]); state is fixed, partly, unfixed or not_planned."""
    ids = set([str(f.get("id")), "%s/%s" % (f.get("lens"), f.get("id"))])
    linked = []
    for fx in list_of((plan or {}).get("fixes")):
        if isinstance(fx, dict) and ids & set(str(x) for x in list_of(fx.get("source_ids"))):
            st = states.get(fx.get("priority"), ("unrecorded", None))[0]
            linked.append("P%s %s" % (fx.get("priority"), st))
    if not linked:
        return "not_planned", []
    kinds = [x.split(" ", 1)[1] for x in linked]
    if all(k == "landed" for k in kinds):
        return "fixed", linked
    if any(k in ("landed", "partial") for k in kinds):
        return "partly", linked
    return "unfixed", linked


def load_decisions(ctx):
    path = ctx.p("review", "decisions.json")
    if not os.path.isfile(path):
        ctx.miss("decisions", path)
        return None
    try:
        import decisions
        rows = decisions.load_rows(ctx.tools)
    except Exception as e:  # decisions.Fail, ImportError
        ctx.miss("decisions", path, one_line(e)[:90])
        return None
    return [r for r in rows if isinstance(r, dict)]


def est_of(row):
    rv = row.get("revert") if isinstance(row.get("revert"), dict) else {}
    return rv.get("est_min") if num(rv.get("est_min")) else None


def reverse_hint(row):
    return "say reverse %s (~%s min)" % (row.get("id"), fmt_num(est_of(row)))


def eye_rows(ctx):
    """-> (per-item rows, final entries); records missing files."""
    items, final = [], []
    try:
        names = sorted(n for n in os.listdir(ctx.review) if re.match(r"^eye.*\.json$", n))
    except OSError:
        names = []
    for name in names:
        obj, err = read_json(os.path.join(ctx.review, name))
        if name == "eye_final.json":
            final = eye_final_entries(obj)
            continue
        if err:
            ctx.miss("eye", os.path.join(ctx.review, name), err)
            continue
        for r in (obj if isinstance(obj, list) else [obj]):
            if isinstance(r, dict):
                items.append({"item": str(r.get("item", name)), "tell": r.get("tell_seen"),
                              "still": r.get("finding_still_visible"), "files": list_of(r.get("files")),
                              "src": name})
    if not any(n != "eye_final.json" for n in names):
        ctx.miss("eye", "review/eye*.json")
    if "eye_final.json" not in names:
        ctx.miss("eye", ctx.p("review", "eye_final.json"))
    elif not final:
        ctx.miss("eye", ctx.p("review", "eye_final.json"), "no entries")
    return items, final


def eye_final_entries(obj):
    if obj is None:
        return []
    rows = obj
    if isinstance(obj, dict):
        for k in EYE_LIST_KEYS:
            if isinstance(obj.get(k), list):
                rows = obj[k]
                break
        else:
            if any(k in obj for k in EYE_ID_KEYS):
                rows = [obj]
            else:
                rows = [{"item": k, "sees": v} for k, v in obj.items()]
    out = []
    for r in rows if isinstance(rows, list) else []:
        if isinstance(r, str):
            out.append({"item": "-", "text": r, "files": []})
        elif isinstance(r, dict):
            item = next((str(r[k]) for k in EYE_ID_KEYS if r.get(k)), "-")
            texts = []
            for k in EYE_TEXT_KEYS:
                v = r.get(k)
                if isinstance(v, list):
                    texts += [one_line(x) for x in v if isinstance(x, (str, int, float))]
                elif isinstance(v, str) and v.strip():
                    texts.append(one_line(v))
            out.append({"item": item, "text": "; ".join(texts) or "nothing listed", "files": list_of(r.get("files"))})
    return out


def eye_requirement_ids(ctx, run):
    """-> (ids, source): the requirements judged by eye alone."""
    ids = (run or {}).get("eye_requirements")
    if isinstance(ids, list) and ids:
        return [str(i) for i in ids], "RUN.json"
    ref = ctx.p("review", "REFERENCE.md")
    found = []
    try:
        with open(ref, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*[-*]\s+\*\*(R\d+)\*\*(.*)$", line)
                if m and re.search(r"\beye\b", m.group(2), re.I) and m.group(1) not in found:
                    found.append(m.group(1))
    except OSError:
        pass
    if found:
        return found, "REFERENCE.md"
    return ["R13"], "default"


def parse_stamp(s):
    return str(s or "")[:19]


def analyze(ctx):
    A = {}
    run, err = read_json(ctx.p("RUN.json"))
    if err or not isinstance(run, dict):
        ctx.miss("incidents", ctx.p("RUN.json"), None if err == "absent" else (err or "not an object"))
        run = None
    A["run"] = run
    rounds = load_rounds(ctx)
    A["rounds"] = rounds
    ns = sorted(rounds)
    panels = [n for n in ns if rounds[n]["panel"]]
    gates = [n for n in ns if isinstance(rounds[n]["suite"], dict)]
    fcs = [n for n in ns if isinstance(rounds[n]["fixcheck"], dict)]
    g = gates[-1] if gates else None
    A["panels"], A["gate_n"] = panels, g
    if not os.path.isdir(ctx.review):
        ctx.miss("defects", "review/", "no review folder")
    elif not ns:
        ctx.miss("defects", "review/round*", "no round folders")
    for n in ns:
        R = rounds[n]
        if R["panel"]:
            for key, fname in (("lead", "lead.json"), ("result", "review_result.json")):
                if R[key + "_err"]:
                    ctx.miss("defects", R[key + "_path"], None if R[key + "_err"] == "absent" else R[key + "_err"])
        prev = rounds.get(n - 1)
        if prev and prev["panel"] and list_of((prev["plan"] or {}).get("fixes")) and R["ledger_err"]:
            ctx.miss("defects", R["ledger_path"],
                     (None if R["ledger_err"] == "absent" else R["ledger_err"]) or "the apply of round %d" % (n - 1))
        if R["suite_err"] not in (None, "absent"):
            ctx.miss("defects", R["suite_path"], R["suite_err"])
    if g is None and ns:
        ctx.miss("defects", "review/round*/suite.json", "no final gate")
    fc_n = g if g is not None and isinstance(rounds[g]["fixcheck"], dict) else (fcs[-1] if fcs else None)
    A["fc_n"] = fc_n
    if g is not None and fc_n is None:
        ctx.miss("defects", rounds[g]["fixcheck_path"], "fixcheck not run")
    fixcheck = rounds[fc_n]["fixcheck"] if fc_n is not None else None
    A["fixcheck"] = fixcheck

    # the gate
    suite = rounds[g]["suite"] if g is not None else None
    A["suite"] = suite
    suite_green = bool(suite) and bool(suite.get("green")) and suite.get("rc") == 0 and suite.get("full") is True
    fc_rc_ok = fixcheck is None or fixcheck.get("rc") == 0
    A["suite_green"], A["gate_green"] = suite_green, suite_green and fc_rc_ok
    why = []
    if suite is None:
        why.append("no suite.json")
    elif not suite_green:
        red = [one_line(r.get("job")) for r in list_of(suite.get("red")) if isinstance(r, dict)]
        why.append("suite not green" + (" (red: %s)" % ", ".join(red[:4]) if red else ""))
    if not fc_rc_ok:
        why.append("fixcheck exit %s" % fixcheck.get("rc"))
    A["gate_why"] = "; ".join(why)

    # the last panel and its apply
    k = panels[-1] if panels else None
    A["k"] = k
    last = rounds[k] if k is not None else None
    plan = last["plan"] if last else None
    ap_n = k + 1 if k is not None and (k + 1) in rounds else None
    A["apply_n"] = ap_n
    ap = rounds[ap_n] if ap_n is not None else None
    ap_ledger = ap["ledger"] if ap and isinstance(ap["ledger"], dict) else None
    ap_fc = ap["fixcheck"] if ap and isinstance(ap["fixcheck"], dict) else None
    states = fix_states(plan, ap_ledger, ap_fc)
    A["states"], A["ap_ledger"] = states, ap_ledger
    confirmed = [f for f in list_of(last["result"].get("confirmed")) if isinstance(f, dict)] \
        if last and isinstance(last["result"], dict) else []
    residuals = list_of(plan.get("residuals")) if plan else []
    res_ids = set(str(r.get("id")) for r in residuals if isinstance(r, dict))
    highs = []
    for f in confirmed:
        if eff_sev(f) == "high":
            st, linked = finding_state(f, plan, states)
            highs.append({"id": str(f.get("id")), "state": st, "linked": linked})
    seen = set(h["id"] for h in highs)
    for r in residuals:
        if isinstance(r, dict) and r.get("severity") == "high" and str(r.get("id")) not in seen:
            highs.append({"id": str(r.get("id")), "state": "not_planned", "linked": []})
    A["highs"] = highs
    A["findings_state"] = {}
    for f in confirmed:
        A["findings_state"][str(f.get("id"))] = finding_state(f, plan, states)
    A["res_ids"] = res_ids

    # decisions, flags, eye, steer, clock
    A["decisions"] = load_decisions(ctx)
    A["eye_items"], A["eye_final"] = eye_rows(ctx)
    A["eye_tells"] = sum(1 for r in A["eye_items"] if truthy(r["tell"]))
    steer, serr = read_jsonl(ctx.p("review", "steer.jsonl"))
    if serr:
        ctx.miss("needs", ctx.p("review", "steer.jsonl"), None if serr == "absent" else serr)
    A["steer"] = steer or []
    A["eye_reqs"], A["eye_req_src"] = eye_requirement_ids(ctx, run)
    A["flags"] = flag_counts(fixcheck)

    stages = ctx.stages
    A["clock"], A["clock_text"] = None, None
    if not os.path.isfile(stages):
        ctx.miss("clock", stages)
    else:
        try:
            import pathclock
            data = pathclock.analyze(stages, None)
            A["clock"], A["clock_text"] = data, pathclock.render(data)
        except Exception as e:  # ValueError for no stamps, OSError, ImportError
            ctx.miss("clock", stages, one_line(e)[:90])
    return A


def flag_counts(fixcheck):
    """-> {'regressed', 'guard_broken', 'exempt'} (non-exempt rows with each flag) or None when not measured."""
    if not isinstance(fixcheck, dict):
        return None
    rc = fixcheck.get("regression_counts")
    if isinstance(rc, dict) and all(num(rc.get(x)) for x in ("regressed", "guard_broken", "exempt")):
        return {x: int(rc[x]) for x in ("regressed", "guard_broken", "exempt")}
    items = [i for i in list_of(fixcheck.get("items")) if isinstance(i, dict)]
    if items and all("regressed" in i and "guard_broken" in i for i in items):
        return {"regressed": sum(len(list_of(i["regressed"])) for i in items),
                "guard_broken": sum(len(list_of(i["guard_broken"])) for i in items),
                "exempt": sum(len(list_of(i.get("exempt"))) for i in items)}
    return None


# ---- sections

def missing_lines(doc, ctx, section):
    for line in ctx.missing.get(section, []):
        doc.add(line)


def verdict_lines(ctx, A):
    run, rounds, k = A["run"], A["rounds"], A["k"]
    L = []
    mode = (run or {}).get("mode")
    extra = ""
    if ctx.n_missing():
        extra = " %s missing, listed under their sections." % plural(ctx.n_missing(), "input")
    if run is None:
        if A["gate_green"] and (k is None or A["ap_ledger"] is not None):
            L.append("Finished (inferred, RUN.json is missing): the final gate is green.%s" % extra)
        else:
            why = "the final gate is not green" if not A["gate_green"] else "the last panel's apply is not recorded"
            L.append("Stopped early (inferred, RUN.json is missing): %s.%s" % (why, extra))
    elif mode == "done" and A["gate_green"]:
        L.append("Finished: stop point reached (RUN.json mode done).%s" % extra)
    elif mode == "done":
        L.append("Stopped early: mode is done but the final gate is not green (%s).%s" % (A["gate_why"], extra))
    else:
        why = run.get("stop_reason")
        if not why:
            inc = [i for i in list_of(run.get("incidents")) if isinstance(i, dict)]
            why = ("mode is %s; last incident: %s" % (mode, short_words(inc[-1].get("text"), 25))) if inc \
                else "mode is %s, no reason recorded" % (mode,)
        L.append("Stopped early: %s.%s" % (one_line(why).rstrip("."), extra))
    # final gate
    suite, g = A["suite"], A["gate_n"]
    if suite is None:
        L.append("Final gate: no suite.json found, so nothing was verified after the last change.")
    else:
        stamp = str(suite.get("ended") or suite.get("started") or "unknown time")
        if not ZONE_RE.search(stamp):
            stamp += " local"
        fc = A["fixcheck"]
        fc_txt = "fixcheck exit %s" % fc.get("rc") if fc else "fixcheck.json missing"
        if A["gate_green"]:
            L.append("Final gate: green at %s (round%d, %s, full suite, %s)." % (
                stamp, g, plural(len(list_of(suite.get("jobs"))), "job"), fc_txt))
        else:
            L.append("Final gate: NOT green at %s (round%d): %s." % (stamp, g, A["gate_why"] or "see suite.json"))
    # rounds
    panels = A["panels"]
    if panels:
        names = ", ".join("R%d" % n for n in panels)
        applies = sum(1 for n in A["rounds"] if isinstance(A["rounds"][n]["ledger"], dict))
        L.append("Rounds run: %s (%s), %s%s%s." % (
            plural(len(panels), "panel"), names, plural(applies, "apply", "applies"),
            ", final gate in round%d" % g if g is not None else ", no final gate",
            ", over the 2-panel cap" if len(panels) > 2 else ""))
    else:
        L.append("Rounds run: no panel round found%s." % (", final gate in round%d" % g if g is not None else ""))
    # highs
    if k is None or not isinstance(rounds[k]["result"], dict):
        L.append("R2-panel highs unfixed: not measured (no review_result.json for a panel round).")
    else:
        hs = A["highs"]
        bad = [h for h in hs if h["state"] != "fixed"]
        kinds = [("partly", "partly fixed"), ("unfixed", "not landed"), ("not_planned", "not planned")]
        parts = ["%d %s" % (sum(1 for h in bad if h["state"] == st), label) for st, label in kinds
                 if any(h["state"] == st for h in bad)]
        note = " (%s)" % ", ".join(parts) if parts else ""
        if A["ap_ledger"] is None and hs:
            note += "; the apply of round %d is not recorded" % k
        L.append("R%d-panel highs unfixed: %d of %d%s." % (k, len(bad), len(hs), note))
    # R-13
    fl, tells = A["flags"], A["eye_tells"]
    eye_txt = "%s eye %s seen" % (tells, "tell" if tells == 1 else "tells") if A["eye_items"] else "no eye files"
    if fl is None:
        L.append("R-13 flags: not measured (the newest fixcheck.json has no regression counts); %s." % eye_txt)
    else:
        open_n = fl["regressed"] + fl["guard_broken"]
        L.append("R-13 flags: %d regressed, %d guard_broken open, %d exempt%s; %s." % (
            fl["regressed"], fl["guard_broken"], fl["exempt"], ", all resolved" if open_n == 0 else "", eye_txt))
    # calls
    rows = A["decisions"]
    if rows is None:
        L.append("Calls to check: not measured (decisions.json is missing).")
    else:
        own = [r for r in rows if r.get("kind") not in NOT_OWN]
        rt = sum(1 for r in own if r.get("kind") == "requirement_trade")
        needs = sum(1 for r in rows if r.get("kind") == "not_made_needs_user")
        L.append("Calls to check: %d (%s); %d %s you." % (
            len(own), plural(rt, "requirement trade"), needs, "fix needs" if needs == 1 else "fixes need"))
    # wall
    c = A["clock"]
    deadline = (run or {}).get("deadline_local")
    est = (run or {}).get("estimate")
    est_txt = ""
    if isinstance(est, dict):
        bits = ["%s %s" % (kk, vv) for kk, vv in est.items() if isinstance(vv, (str, int, float))]
        est_txt = "; estimate " + ", ".join(bits)[:80] if bits else ""
    if c is None:
        L.append("Wall time: not measured (stages.jsonl is missing or has no stamps)%s." % est_txt)
    else:
        L.append("Wall time: %.1f h (on path %.1f h, waits %.1f h)%s%s." % (
            c["wall_min"] / 60.0, c["on_path_min"] / 60.0, c["waits_min"] / 60.0,
            "; deadline %s local" % deadline if deadline else "", est_txt))
    L.append(QUA4)
    return L


def pick_images(ctx, A):
    """3-6 existing image paths, relative to the tools folder."""
    rounds, g = A["rounds"], A["gate_n"]
    order = ([g] if g is not None else []) + [n for n in sorted(rounds, reverse=True) if n != g]
    weight = {}  # variant -> how much open work names it (high 3, medium 2, low 1, unrated 2)
    for row in A["rows_defects"]:
        for v in row["variants"]:
            weight[v] = weight.get(v, 0) + {"high": 3, "medium": 2, "low": 1}.get(row["sev"], 2)
    for r in A["eye_items"]:
        if truthy(r["tell"]) or truthy(r["still"]):
            weight[r["item"]] = weight.get(r["item"], 0) + 3
    for n in order:
        d = rounds[n]["dir"]
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        compare = [x for x in names if x.startswith("compare") and x.lower().endswith(".png")]
        compare.sort(key=lambda x: (x != "compare_front.png", x))
        tiled = [x for x in names if x.lower().endswith("_tiled3x3_albedo.png")]
        tiled.sort(key=lambda x: (-weight.get(x.replace("_tiled3x3_albedo.png", ""), 0), x))
        if not compare and not tiled:
            continue
        eye_files = []
        for r in A["eye_items"]:
            if truthy(r["tell"]) or truthy(r["still"]):
                for f in r["files"]:
                    for cand in (os.path.join(ctx.tools, str(f)), os.path.join(ctx.review, str(f)), str(f)):
                        if os.path.isfile(cand):
                            eye_files.append(cand)
                            break
        picks = []
        for p in [os.path.join(d, x) for x in compare[:2]] + eye_files[:2] + [os.path.join(d, x) for x in tiled]:
            if p not in picks:
                picks.append(p)
        return [ctx.rel(p) for p in picks[:6]], rounds[n]["rel"]
    return [], None


def sec_look(doc, ctx, A):
    doc.h(SECTIONS[1])
    missing_lines(doc, ctx, "look")
    picks, folder = A["picks"]
    if not picks:
        return
    doc.add("Send these first (SendUserFile), then the rest of the folder:")
    for p in picks:
        doc.add("- `%s`" % p)
    doc.add("- `%s`" % folder)


def sec_decisions(doc, ctx, A):
    doc.h(SECTIONS[2])
    missing_lines(doc, ctx, "decisions")
    rows = A["decisions"]
    if rows is None:
        doc.add("No decision log, so no call can be reversed by id.")
        return
    if not rows:
        doc.add("decisions.json holds no rows: the run settled nothing on its own.")
        return
    rows = sorted(rows, key=lambda r: (r.get("kind") != "requirement_trade", id_key(r)))
    doc.add("%s logged, requirement trades first. Say 'reverse <id>' to undo one; minutes are machine time." % (
        plural(len(rows), "decision")))
    doc.table(["id", "kind", "question", "chosen", "rule", "gave up", "items", "reverse"],
              [[cell(r.get("id")), cell(r.get("kind")), cell(r.get("question"), 260), cell(r.get("chosen"), 200),
                cell(r.get("rule")), cell(r.get("gave_up"), 220), cell(", ".join(map(str, list_of(r.get("items"))))),
                cell(reverse_hint(r))] for r in rows])


def last_apply_end(A):
    led = A["ap_ledger"]
    ap = led.get("apply") if led else None
    return parse_stamp(ap.get("ended")) if isinstance(ap, dict) and ap.get("ended") else None


def sec_needs(doc, ctx, A):
    doc.h(SECTIONS[3])
    missing_lines(doc, ctx, "needs")
    rows = A["decisions"] or []
    undone = [r for r in sorted(rows, key=id_key) if r.get("kind") == "not_made_needs_user"]
    over = []
    for n in A["panels"]:
        R = A["rounds"][n]
        for d in list_of((R["plan"] or {}).get("deferred")):
            if isinstance(d, str) and re.match(r"\s*design call\b", d, re.I):
                over.append((n, d, detail_ref(ctx, R)))
    end = last_apply_end(A)
    steer = [s for s in A["steer"] if isinstance(s.get("text"), str)]
    later = [s for s in steer if end is None or parse_stamp(s.get("utc")) > end]
    earlier = len(steer) - len(later)
    if not (undone or over or later):
        doc.add("Nothing here needs you.")
        if earlier:
            doc.add("%s already used at the gates (user_steer rows in section 3)." % plural(earlier, "steer message"))
        return
    doc.add("Needs you: %s undone, %s over the cap, %s requested." % (
        plural(len(undone), "fix", "fixes"), plural(len(over), "design call"), plural(len(later), "change")))
    for r in undone:
        doc.add("- Undone %s (would change a value you gave or a check's meaning): %s Gave up: %s" % (
            r.get("id"), short_words(r.get("question"), 30), short_words(r.get("gave_up") or "see the row", 25)),
                "detail", "review/decisions.json")
    for n, d, ref in over:
        doc.add("- Over the cap (R%d lead): %s" % (n, short_words(re.sub(r"^\s*design call:?\s*", "", d, flags=re.I), 40)),
                "detail", ref)
    for s in later:
        doc.add("- Requested after the last apply, %s: %s" % (s.get("utc", "?"), short_words(s.get("text"), 40)), "detail",
                "review/steer.jsonl")


def defect_rows(ctx, A):
    """The open-defects rows: dicts with sev, tag, id, defect, variants (list), status."""
    rounds, k = A["rounds"], A["k"]
    tag_np = "not reviewed by a panel (R%d apply)" % k if k is not None else "not reviewed by a panel"
    rows = []
    conf_ids = set()
    last = rounds[k] if k is not None else None
    if last and isinstance(last["result"], dict):
        for f in list_of(last["result"].get("confirmed")):
            if not isinstance(f, dict):
                continue
            fid = str(f.get("id"))
            conf_ids.add(fid)
            st, linked = A["findings_state"].get(fid, ("not_planned", []))
            if st == "fixed":
                continue
            if st == "not_planned":
                status = "not planned" + ("; in the residual table" if fid in A["res_ids"] else "")
            else:
                status = ("partly fixed: " if st == "partly" else "not fixed: ") + ", ".join(linked)
            rows.append({"sev": eff_sev(f), "tag": "panel R%d" % k, "id": fid, "defect": f.get("title"),
                         "variants": [str(v) for v in list_of(f.get("variants"))], "status": status})
    for n in A["panels"]:
        for r in list_of((rounds[n]["plan"] or {}).get("residuals")):
            if isinstance(r, dict) and not (n == k and str(r.get("id")) in conf_ids):
                rows.append({"sev": r.get("severity") if r.get("severity") in ("high", "medium", "low") else "unrated",
                             "tag": "panel R%d" % n, "id": str(r.get("id")),
                             "defect": r.get("family") or r.get("next_lever"),
                             "variants": [str(v) for v in list_of(r.get("variants"))],
                             "status": "residual: " + one_line(r.get("why_open") or "")})
    for it in list_of((A["fixcheck"] or {}).get("items")):
        if not isinstance(it, dict):
            continue
        for flag in ("regressed", "guard_broken"):
            for rid in list_of(it.get(flag)):
                rows.append({"sev": "unrated", "tag": tag_np, "id": "%s %s" % (it.get("id"), rid),
                             "defect": "%s row: %s" % (flag, rid),
                             "variants": [str(rid).split("@", 1)[1]] if "@" in str(rid) else [],
                             "status": "fixcheck flag, not exempt"})
        for ex in list_of(it.get("exempt")):
            if isinstance(ex, dict):
                rid = str(ex.get("row"))
                rows.append({"sev": "unrated", "tag": tag_np, "id": "%s %s" % (it.get("id"), rid),
                             "defect": "%s row: %s" % (ex.get("flag"), rid),
                             "variants": [rid.split("@", 1)[1]] if "@" in rid else [],
                             "status": "exempt: " + one_line(ex.get("reason") or "")})
    for n in sorted(rounds):
        for it in list_of((rounds[n]["ledger"] or {}).get("items")):
            if isinstance(it, dict) and re.match(r"\s*reverted\b", str(it.get("note") or ""), re.I):
                rows.append({"sev": "unrated", "tag": tag_np, "id": "%s (round%d ledger)" % (it.get("id"), n),
                             "defect": it.get("title"), "variants": [], "status": one_line(it.get("note"))[:160]})
    for r in A["eye_items"]:
        if truthy(r["tell"]):
            rows.append({"sev": "unrated", "tag": tag_np, "id": r["item"], "defect": "tell seen: " + one_line("yes" if r["tell"] is True else r["tell"]),
                         "variants": [], "status": "eye agent (%s)" % r["src"]})
        if truthy(r["still"]):
            rows.append({"sev": "unrated", "tag": tag_np, "id": r["item"],
                         "defect": "finding still visible: " + one_line("yes" if r["still"] is True else r["still"]),
                         "variants": [],
                         "status": "eye agent (%s)" % r["src"]})
    rows.sort(key=lambda r: (SEV_RANK.get(r["sev"], 3), r["tag"].startswith("not reviewed"), r["tag"], r["id"]))
    return rows


def eye_requirement_line(ctx, A):
    """R13's status: the verdicts of the requirements judged by eye alone, per variant, from the last lead's scorecard."""
    k, ids = A["k"], A["eye_reqs"]
    src = {"default": "default id", "RUN.json": "named in RUN.json", "REFERENCE.md": "named in REFERENCE.md"}[A["eye_req_src"]]
    head = "%s status (judged by eye alone, never blocks the stop; %s)" % (", ".join(ids), src)
    if k is None or not isinstance(A["rounds"][k]["plan"], dict):
        return head + ": not rated, no lead.json for a panel round."
    sc = [r for r in list_of(A["rounds"][k]["plan"].get("requirements_scorecard")) if isinstance(r, dict)]
    parts = []
    for rid in ids:
        mine = [r for r in sc if str(r.get("requirement")) == rid]
        body = ", ".join("%s %s" % (r.get("variant"), r.get("verdict")) for r in mine) if mine \
            else "not in the scorecard"
        parts.append(body if len(ids) == 1 else "%s %s" % (rid, body))
    return "%s, R%d panel: %s." % (head, k, "; ".join(parts))


def residual_rows(ctx, A):
    out, derived = [], []
    for n in A["panels"]:
        R = A["rounds"][n]
        plan = R["plan"] or {}
        if isinstance(plan.get("residuals"), list):
            for r in plan["residuals"]:
                if isinstance(r, dict):
                    out.append([cell("R%d" % n), cell(r.get("id")), cell(r.get("family")), cell(r.get("severity")),
                                cell(", ".join(map(str, list_of(r.get("variants"))))), cell(r.get("visible_at")),
                                cell(r.get("numbers"), 200), cell(r.get("why_open"), 200), cell(r.get("next_lever"), 200)])
        else:
            derived.append(n)
    k = A["k"]
    if k in derived and isinstance(A["rounds"][k]["result"], dict):
        for f in list_of(A["rounds"][k]["result"].get("confirmed")):
            if isinstance(f, dict) and A["findings_state"].get(str(f.get("id")), ("x",))[0] == "not_planned":
                out.append([cell("R%d" % k), cell(f.get("id")), cell(f.get("category") or f.get("lens")), cell(eff_sev(f)),
                            cell(", ".join(map(str, list_of(f.get("variants"))))), cell(f.get("visible_at")),
                            cell("-"), cell("not in the plan (derived: the lead has no residuals key)"),
                            cell(f.get("proposed_fix"), 160)])
    return out, derived


def count_sev(findings):
    c = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        s = eff_sev(f)
        if s in c:
            c[s] += 1
    return c


def sec_defects(doc, ctx, A):
    rounds, k = A["rounds"], A["k"]
    doc.h(SECTIONS[4])
    missing_lines(doc, ctx, "defects")
    doc.add("Severities are %s." % (CAVEAT % (k, k) if k is not None else CAVEAT.replace("R%d", "last")))
    doc.add(eye_requirement_line(ctx, A))
    rows = A["rows_defects"]
    doc.h("Open defects", 3)
    if rows:
        doc.table(["severity", "tag", "id", "defect", "variants", "status"],
                  [[cell(r["sev"]), cell(r["tag"]), cell(r["id"]), cell(r["defect"], 200),
                    cell(", ".join(r["variants"])), cell(r["status"], 200)] for r in rows])
    else:
        doc.add("None open.")
    doc.h("Residuals (R-05)", 3)
    res, derived = residual_rows(ctx, A)
    if derived and A["panels"]:
        doc.add("No residuals key in the lead of %s (older schema)." % ", ".join("round%d" % n for n in derived))
    if res:
        doc.table(["panel", "id", "family", "severity", "variants", "visible at", "numbers", "why open", "next lever"], res)
    else:
        doc.add("None listed.")
    doc.h("Rounds", 3)
    trows = []
    for n in sorted(rounds):
        R = rounds[n]
        kind = "panel" if R["panel"] else ("final gate" if n == A["gate_n"] else "other")
        res_ = R["result"] if isinstance(R["result"], dict) else None
        if res_:
            c = count_sev([f for f in list_of(res_.get("confirmed")) if isinstance(f, dict)])
            st = res_.get("stats") if isinstance(res_.get("stats"), dict) else {}
            fnd = "%d confirmed (%d high, %d medium, %d low), %s rejected, %s unverified" % (
                sum(c.values()), c["high"], c["medium"], c["low"], st.get("rejected", len(list_of(res_.get("rejected")))),
                st.get("unverified", len(list_of(res_.get("unverified")))))
        else:
            fnd = "-"
        plan = R["plan"]
        pl = "%d fixes, %d design calls, %d residuals" % (
            len(list_of(plan.get("fixes"))), len(list_of(plan.get("design_calls"))),
            len(list_of(plan.get("residuals")))) if plan else "-"
        led = R["ledger"]
        if isinstance(led, dict):
            its = [i for i in list_of(led.get("items")) if isinstance(i, dict)]
            cnt = {}
            for i in its:
                cnt[i.get("status")] = cnt.get(i.get("status"), 0) + 1
            lg = "apply of round %d: %d items (%s)" % (n - 1, len(its), ", ".join("%d %s" % (v, kk) for kk, v in sorted(cnt.items())))
        else:
            lg = "-"
        s = R["suite"]
        if isinstance(s, dict):
            sg = "green" if s.get("green") and s.get("rc") == 0 and s.get("full") is True else "RED"
            sg += " (%s, ended %s)" % (plural(len(list_of(s.get("jobs"))), "job"), s.get("ended") or "?")
        else:
            sg = "-"
        fcx = R["fixcheck"]
        fx = "exit %s" % fcx.get("rc") if isinstance(fcx, dict) else "-"
        trows.append([cell("round%d" % n), cell(kind), cell(fnd), cell(pl), cell(lg), cell(sg), cell(fx),
                      cell(ctx.rel(R["findings_path"]) if os.path.isfile(R["findings_path"]) else "-")])
    if trows:
        doc.table(["round", "kind", "panel findings", "plan", "ledger", "suite", "fixcheck", "findings.md"], trows)
    else:
        doc.add("No round folders.")
    doc.h("Fix ledger", 3)
    lrows = []
    for n in sorted(rounds):
        R = rounds[n]
        led = R["ledger"]
        if not isinstance(led, dict):
            continue
        fcx = R["fixcheck"] if isinstance(R["fixcheck"], dict) else None
        fci = {}
        for i in list_of((fcx or {}).get("items")):
            if isinstance(i, dict):
                fci[str(i.get("id"))] = i
        for it in list_of(led.get("items")):
            if not isinstance(it, dict):
                continue
            f = fci.get(str(it.get("id")))
            if f is None:
                verdict, flags = "-", "-"
            else:
                verdict = f.get("verdict") or "-"
                flags = ", ".join(map(str, list_of(f.get("flags")))) or "-"
            lrows.append([cell("R%d apply (round%d)" % (n - 1, n)), cell(it.get("id")), cell(it.get("status")),
                          cell(verdict), cell(flags), cell(it.get("title"), 110)])
    if lrows:
        doc.table(["apply", "item", "ledger status", "fixcheck", "flags", "title"], lrows)
    else:
        doc.add("No ledger found.")


def sec_eye(doc, ctx, A):
    doc.h(SECTIONS[5])
    missing_lines(doc, ctx, "eye")
    if A["eye_final"] or A["eye_items"]:
        doc.add("Not panel-verified: a background eye agent read the final tiled sheets of every preset.")
    if A["eye_final"]:
        doc.table(["preset", "what it sees", "files"],
                  [[cell(e["item"]), cell(e["text"], 300), cell(", ".join(map(str, e["files"])), 160)] for e in A["eye_final"]])
    if A["eye_items"]:
        doc.h("Per-fix eye checks", 3)
        doc.table(["item", "tell seen", "finding still visible", "files", "file"],
                  [[cell(r["item"]), yn(r["tell"]), yn(r["still"]), cell(", ".join(map(str, r["files"])), 160),
                    cell(r["src"])] for r in A["eye_items"]])


def sec_incidents(doc, ctx, A):
    doc.h(SECTIONS[6])
    missing_lines(doc, ctx, "incidents")
    inc = [i for i in list_of((A["run"] or {}).get("incidents")) if isinstance(i, dict)]
    if inc:
        doc.table(["utc", "by", "incident"], [[cell(i.get("utc")), cell(i.get("by")), cell(i.get("text"), 300)] for i in inc])
    elif A["run"] is not None:
        doc.add("None recorded.")
    rec = []
    for n in sorted(A["rounds"]):
        for it in list_of((A["rounds"][n]["ledger"] or {}).get("items")):
            if isinstance(it, dict) and re.match(r"\s*reverted\b", str(it.get("note") or ""), re.I):
                rec.append([cell("round%d ledger" % n), cell(it.get("id")), cell(it.get("note"), 240)])
    if rec:
        doc.h("Recoveries", 3)
        doc.table(["where", "item", "what happened"], rec)


def commits_of(run):
    out = []
    for c in list_of((run or {}).get("proposed_commits")):
        if isinstance(c, dict) and one_line(c.get("message") or ""):
            files = c.get("files")
            files = [str(x) for x in files] if isinstance(files, list) else ([str(files)] if files else [])
            out.append({"repo": str(c.get("repo") or "-"), "files": files, "message": str(c.get("message")).strip()})
    return out


def sec_commits(doc, ctx, A):
    doc.h(SECTIONS[7])
    cs = commits_of(A["run"])
    if not cs:
        doc.add("none proposed")
        return
    doc.add("No commit is made and nothing is pushed.")
    doc.table(["#", "repo", "files", "message"],
              [[str(i), cell(c["repo"]), cell(", ".join(c["files"][:10]) + (" (+%d more)" % (len(c["files"]) - 10)
                                                                         if len(c["files"]) > 10 else ""), 300),
                cell(c["message"].splitlines()[0], 200)] for i, c in enumerate(cs, 1)])


def sec_clock(doc, ctx, A):
    doc.h(SECTIONS[8])
    missing_lines(doc, ctx, "clock")
    text = A["clock_text"]
    if not text:
        return
    ref = ctx.rel(ctx.stages)
    lines = text.rstrip("\n").split("\n")
    if lines and lines[0].startswith("## "):
        lines = lines[1:]
    blocks, cur = [], None  # a block is a '### ' heading and its lines; the lines before the first heading lead
    for line in lines:
        if line.startswith("### "):
            cur = {"head": line, "body": []}
            blocks.append(cur)
        else:
            if cur is None:
                cur = {"head": None, "body": []}
                blocks.append(cur)
            cur["body"].append(line)
    empty = []
    for b in blocks:
        real = [x.strip() for x in b["body"] if x.strip() and not x.startswith("Pause and resume edges")]
        if b["head"] and len(real) == 1 and real[0] in PATHCLOCK_EMPTY:
            empty.append(b["head"][4:].strip().lower())
            continue
        if b["head"]:
            doc.blank()
            doc.add(b["head"])
        for line in b["body"]:
            if not line.strip():
                doc.blank()
            elif is_table(line):
                doc.add(line, "table")
            else:
                doc.add(line, "detail", ref)
    if empty:
        doc.blank()
        doc.add("Nothing to report: %s." % ", ".join(empty))


def batch_lines(A):
    rows = A["decisions"] or []
    own = [r for r in rows if r.get("kind") not in NOT_OWN]
    own.sort(key=lambda r: (r.get("kind") != "requirement_trade", -(est_of(r) or 0), id_key(r)))
    top = own[:3]
    L = []
    if top:
        L.append("1. Reverse any decision? say 'reverse %s'" % top[0].get("id"))
        for r in top:
            L.append("   - %s (%s, ~%s min): %s" % (r.get("id"), r.get("kind"), fmt_num(est_of(r)),
                                                    short_words(r.get("question"), 14)))
    else:
        L.append("1. Reverse any decision? none logged")
    L.append("   - None (Recommended)")
    for i, c in enumerate(commits_of(A["run"]), 1):
        L.append("%d. commit %d: %s - yes/no" % (i + 1, i, short_words(c["message"].splitlines()[0], 30)))
    return L


def sec_batch(doc, A):
    doc.h("Answer batch")
    doc.add("Reply by number, for example: 1 none, 2 yes.")
    doc.blank()
    for line in batch_lines(A):
        doc.add(line)


def build(ctx):
    A = analyze(ctx)
    A["rows_defects"] = defect_rows(ctx, A)
    A["picks"] = pick_images(ctx, A)
    if not A["picks"][0]:
        ctx.miss("look", "compare and tiled 3x3 sheets under review/round*")
    run = A["run"] or {}
    material = run.get("material") or re.sub(r"_tools$", "", os.path.basename(ctx.tools)) or "material"
    doc = Doc()
    doc.add("# Morning report: %s (%s)" % (material, utc_now()))
    doc.add("`%s`" % slash(ctx.tools))
    doc.h(SECTIONS[0])
    for line in verdict_lines(ctx, A):
        doc.add("- " + line)
    sec_look(doc, ctx, A)
    sec_decisions(doc, ctx, A)
    sec_needs(doc, ctx, A)
    sec_defects(doc, ctx, A)
    sec_eye(doc, ctx, A)
    sec_incidents(doc, ctx, A)
    sec_commits(doc, ctx, A)
    sec_clock(doc, ctx, A)
    sec_batch(doc, A)
    return doc, A


# ---- addendum

def render_rows(rows):
    out = []

    def table(objs):
        cols = []
        for o in objs:
            for kk in o:
                if kk not in cols:
                    cols.append(kk)
        out.append("| " + " | ".join(cell(c) for c in cols) + " |")
        out.append("|" + "---|" * len(cols))
        for o in objs:
            out.append("| " + " | ".join(cell(o.get(c)) if not isinstance(o.get(c), (dict, list))
                                          else cell(json.dumps(o.get(c), ensure_ascii=False)) for c in cols) + " |")

    if isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows):
        table(rows)
    elif isinstance(rows, dict):
        special = ("decision", "decision_id", "suite", "guards")
        dec = rows.get("decision_id", rows.get("decision"))
        if dec:
            out.append("Decisions row: %s" % dec)
        if rows.get("suite") is not None:
            s = rows["suite"]
            out.append("Targeted suite: %s" % (s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)))
        if out:
            out.append("")
        g = rows.get("guards")
        if isinstance(g, list) and g and all(isinstance(x, dict) for x in g):
            table(g)
        elif g is not None:
            out.append("Guards: %s" % json.dumps(g, ensure_ascii=False))
        rest = dict((kk, vv) for kk, vv in rows.items() if kk not in special)
        if rest:
            if out:
                out.append("")
            table([rest])
    elif isinstance(rows, list):
        out += ["- " + one_line(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)) for x in rows]
    else:
        out.append(one_line(rows if isinstance(rows, str) else json.dumps(rows, ensure_ascii=False)))
    return out


def fmt4(v):
    return "%.4g" % v if num(v) else ("-" if v is None else str(v))


def fmt_range(t):
    if isinstance(t, (list, tuple)) and len(t) == 2:
        return "[%s, %s]" % tuple("-" if x is None else fmt4(x) for x in t)
    return "-"


def edit_decision(ctx, k):
    try:
        import decisions
        rows = decisions.load_rows(ctx.tools)
    except decisions.Fail:  # a corrupt log is not the same as no row
        return "unreadable: review/decisions.json"
    except Exception:
        rows = []
    found = [r for r in rows if isinstance(r, dict) and r.get("kind") == "user_edit"
             and "U%d" % k in list_of(r.get("items"))]
    return str(found[-1].get("id")) if found else "none logged"


def edit_suite(ctx, k, ed):
    for name in ("suite.json", "suite_partial.json"):
        path = os.path.join(ed, name)
        if not os.path.isfile(path):
            continue
        rel = ctx.rel(path)
        obj, err = read_json(path)
        if not isinstance(obj, dict):
            return "unreadable: %s" % rel
        rc = obj.get("rc")
        if obj.get("green") is True and type(obj.get("rc")) is int and obj["rc"] == 0:
            return "green (%s, rc %s)" % (rel, rc)
        reds = []
        for r in list_of(obj.get("red")):
            if isinstance(r, dict):
                why = list_of(r.get("reasons"))
                reds.append("%s: %s" % (one_line(r.get("job")), one_line(why[0]) if why else "no reason given"))
        return "red (%s, rc %s)%s" % (rel, rc, ": " + "; ".join(reds) if reds else "")
    return "missing: review/edit%d/suite_partial.json" % k


def edit_guard_rows(ctx, k, ed):
    out = []
    rel = "review/edit%d/fixcheck/fixcheck.json" % k
    path = os.path.join(ed, "fixcheck", "fixcheck.json")

    def row(name, before, after, target, flag):
        return {"row": name, "before": before, "after": after, "target": target, "flag": flag}

    obj, err = read_json(path)
    if not isinstance(obj, dict):
        out.append(row("fixcheck", "-", "-", "-", ("missing: " if err == "absent" else "unreadable: ") + rel))
    else:
        rows = [r for it in list_of(obj.get("items")) if isinstance(it, dict)
                for r in list_of(it.get("rows")) if isinstance(r, dict)]
        rcn = obj.get("regression_counts") if isinstance(obj.get("regression_counts"), dict) else {}
        misses = sum(1 for r in rows if r.get("status") == "misses")
        out.append(row("fixcheck", "-", "-", "-", "%s regressed, %s guard broken, %d outside target, of %d rows (exit %s)"
                       % (rcn.get("regressed", "?"), rcn.get("guard_broken", "?"), misses, len(rows), obj.get("rc"))))
        for r in rows:
            words = [w for w, on in (("regressed", r.get("regressed")), ("guard broken", r.get("guard_broken")),
                                     ("outside target", r.get("status") == "misses")) if on]
            if not words:
                continue
            flag = ", ".join(words)
            if r.get("exempt"):
                flag += " (exempt: %s)" % one_line(r.get("exempt"))
            after = r.get("value") if num(r.get("value")) else r.get("after")
            tgt = r.get("target") if r.get("target") is not None else r.get("bound")
            out.append(row("%s@%s" % (r.get("check"), r.get("variant")), fmt4(r.get("before")), fmt4(after),
                           fmt_range(tgt), flag))
    eye, err = read_json(os.path.join(ed, "eye.json"))
    if err:
        out.append(row("eye", "-", "-", "-", ("missing: review/edit%d/eye.json (not back)" % k) if err == "absent"
                       else "unreadable: review/edit%d/eye.json" % k))
        return out
    ebase = "review/edit%d/eye.json" % k
    entries = eye
    if isinstance(eye, dict):
        entries = next((eye[x] for x in ("variants", "presets", "items", "rows", "entries")
                        if isinstance(eye.get(x), list)), None)
    if not isinstance(entries, list):
        out.append(row("eye", "-", "-", "-", "unreadable: %s (unrecognised shape)" % ebase))
        return out
    if not entries:
        out.append(row("eye", "-", "-", "-", "no entries in %s" % ebase))
        return out
    if not any(isinstance(e, dict) for e in entries):
        out.append(row("eye", "-", "-", "-", "unreadable: %s (unrecognised shape)" % ebase))
        return out
    for e in entries:
        if not isinstance(e, dict):
            continue
        name = next((str(e[x]) for x in ("variant", "preset", "item", "name") if e.get(x)), "-")
        out.append(row("eye %s" % name, "-", "-", "-", "%s: %s" % (
            "new defect" if e.get("new_defect") is True else "no new defect", one_line(e["sees"]) if e.get("sees") is not None else "")))
    return out


def edit_rows(ctx, k):
    ed = ctx.p("review", "edit%d" % k)
    return {"decision": edit_decision(ctx, k), "suite": edit_suite(ctx, k, ed), "guards": edit_guard_rows(ctx, k, ed)}


def do_addendum(args, ctx):
    exists = os.path.isfile(ctx.out)
    if not exists and args.kind != "user_edit":
        sys.stderr.write("morning_report.py: %s does not exist; write the report first\n" % ctx.out)
        return 2
    if not args.text or not args.text.strip():
        sys.stderr.write("morning_report.py: --addendum needs --text\n")
        return 2
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]{0,31}$", args.kind):
        sys.stderr.write("morning_report.py: --kind %r: use letters, digits and '_'\n" % args.kind)
        return 2
    rows_lines = []
    if args.edit is not None:
        if args.kind != "user_edit":
            sys.stderr.write("morning_report.py: --edit needs --addendum --kind user_edit\n")
            return 2
        if args.edit < 1:
            sys.stderr.write("morning_report.py: --edit must be an integer of 1 or more\n")
            return 2
        if not os.path.isdir(ctx.p("review", "edit%d" % args.edit)):
            sys.stderr.write("morning_report.py: %s is not a folder\n" % ctx.p("review", "edit%d" % args.edit))
            return 2
        rows_lines = render_rows(edit_rows(ctx, args.edit))
    if args.rows:
        try:
            extra = render_rows(json.loads(args.rows))
            rows_lines = rows_lines + ([""] if rows_lines else []) + extra
        except ValueError as e:
            sys.stderr.write("morning_report.py: --rows is not valid JSON: %s\n" % e)
            return 2
    chunk = ["", "## Addendum %s (%s)" % (utc_now(), args.kind), "", args.text.strip()]
    if rows_lines:
        chunk += [""] + rows_lines
    data = "\n".join(chunk) + "\n"
    if not exists:  # a user edit of a material that never had a morning report: the file starts here
        os.makedirs(os.path.dirname(os.path.abspath(ctx.out)), exist_ok=True)
        with open(ctx.out, "wb") as f:
            f.write(("# %s report\n\nNo morning report was written for this material; this file holds its edit "
                     "addenda.\n" % material_name(ctx)).encode("utf-8"))
        print("created %s" % ctx.out)
    with open(ctx.out, "ab") as f:
        f.write(("\n" if _lacks_final_newline(ctx.out) else "").encode("utf-8"))
        f.write(data.encode("utf-8"))
    print(ctx.out)
    print("addendum appended (%d lines); the rest of the report is unchanged" % len(chunk))
    return 0


def material_name(ctx):
    """RUN.json `material` when it is a non-empty string, else the tools folder's name without a trailing _tools."""
    run, _ = read_json(ctx.p("RUN.json"))
    name = run.get("material") if isinstance(run, dict) else None
    if isinstance(name, str) and name.strip():
        return name.strip()
    base = os.path.basename(ctx.tools.rstrip("/\\"))
    return base[:-len("_tools")] if base.endswith("_tools") and len(base) > len("_tools") else base


def _lacks_final_newline(path):
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        if f.tell() == 0:
            return False
        f.seek(-1, os.SEEK_END)
        return f.read(1) != b"\n"


# ---- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="Write the morning report of an unattended material run.")
    ap.add_argument("--tools", required=True, help="the material's tools folder (only read)")
    ap.add_argument("--out", help="the report path (default <tools>/REPORT.md)")
    ap.add_argument("--rounds", nargs="+", type=int, metavar="N", help="read only these review/round<N> folders")
    ap.add_argument("--stages", help="stamps file (default <tools>/stages.jsonl)")
    ap.add_argument("--cap", type=int, default=CAP, help="prose word cap (default %d)" % CAP)
    ap.add_argument("--addendum", action="store_true", help="append a dated Addendum section to the report (for "
                    "--kind user_edit, create the report first when there is none)")
    ap.add_argument("--kind", default="user_edit", help="addendum kind (default user_edit)")
    ap.add_argument("--text", help="addendum text: what changed, and the decisions row id")
    ap.add_argument("--edit", type=int, metavar="K", help="with --addendum --kind user_edit: build the rows from "
                    "<tools>/review/edit<K> (decisions row, targeted suite, fixcheck and eye rows)")
    ap.add_argument("--rows", help="addendum rows as JSON (a list of objects, an object, or a list)")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if not os.path.isdir(args.tools):
        sys.stderr.write("morning_report.py: --tools %s is not a folder\n" % args.tools)
        return 2
    if args.cap < 1:
        sys.stderr.write("morning_report.py: --cap must be 1 or more\n")
        return 2
    ctx = Ctx(args.tools, args.out, args.rounds, args.stages, args.cap)
    if args.edit is not None and not args.addendum:
        sys.stderr.write("morning_report.py: --edit needs --addendum --kind user_edit\n")
        return 2
    if args.addendum:
        return do_addendum(args, ctx)
    doc, A = build(ctx)
    moved = enforce_cap(doc, ctx.cap)
    text = doc.render()
    words = prose_words(text)
    os.makedirs(os.path.dirname(os.path.abspath(ctx.out)), exist_ok=True)
    tmp = ctx.out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, ctx.out)
    print(ctx.out)
    print("prose words: %d (cap %d%s)" % (words, ctx.cap, "; %s moved to references" % plural(moved, "detail run") if moved else ""))
    if words > ctx.cap:
        print("WARNING: the prose is over the cap and has no detail left to move")
    print("")
    print("Answer batch:")
    for line in batch_lines(A):
        print(line)
    return 0 if words <= ctx.cap else 1


if __name__ == "__main__":
    sys.exit(main())
