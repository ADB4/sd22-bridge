#!/usr/bin/env python3
"""Run a material's measure suite in parallel and gate it: matcheck per config, wrong builds per config and per
cross-case group, previews per config and the material's own commands, then the wrong-builds merge and the previews
assemble. Never calls Designer. Stdlib only, Python 3.7 or newer; the jobs run under the child python (the analysis
venv). How to use it: references/checks.md, "Suite". This docstring is the reference.

Usage:
    python suite.py <tools>/SUITE.json --out <tools>/review/round<N> [--jobs N | --beside-designer] [--timeout S]
                    [--threads 2] [--configs a,b] [--kinds matcheck,wrong_builds,previews,commands] [--plan]

SUITE.json, paths relative to its folder (<tools>):
    configs     required: globs or files of checks configs. Skipped (listed under "skipped"): scorecard_*, SUITE.json
                and JSON with no "checks" key. A "checks" that is not a list is planned, and matcheck refuses it (red).
    cases       the wrong_builds.py cases module. Without it every config with a hard check is red (R6).
    checks_dir  where the cases' config names live (default: the cases module's folder).
    previews    {"configs": globs or files (default: configs), "args": only --sites N and --no-shadows}. Without it,
                no previews (a warning).
    commands    [{"name", "argv", "outputs": files it must write (default none), "timeout": seconds, "expect": seconds
                it takes, to order the jobs until a run has measured it (default 5), "after": true runs it after the
                other jobs (default false), "cwd" (default <tools>), "gate": {"json": one of its outputs, "empty",
                "true", "false": [fields, dotted for nested ones]}}]. argv, outputs, cwd and gate.json expand {python}
                (the child python), {out} (--out), {tools} (<tools>) and {scripts} (this folder).
    timeout     seconds per job (default 900). --timeout overrides it; a command's own timeout overrides both.
    python      the jobs' interpreter, a path or a command name (default: the one running suite.py).

Jobs. Phase 1, longest expected first: matcheck.py <config> --out <out> --quiet per config; wrong_builds.py --only
<name> per config the cases name and per cross-case group, into <out>/suite/wb/<name>/; previews.py <config> --part
per previews config; each command. Phase 2: wrong_builds.py --merge of the parts in --list order and previews.py
--assemble (full runs only), and the "after" commands. Order: the seconds each job took in <out>/suite/times.json;
when --out has none yet, in the newest <sibling of --out>/suite/times.json (last round's); else the estimate (a
command's expect). The run writes its times.json seeded with the times it read (times_from in suite.json).

Workers: --jobs; else $SUITE_JOBS; else max(1, min(CPUs - 2, 16, RAM jobs, jobs)). RAM jobs = (total physical RAM -
4 GB) / per-job GB, per-job GB = 1.5 x max(1, the largest height map's pixels / 2048^2) (6 GB at 4K), the size read
from the PNG header, else scale.resolution. Total, not free RAM: macOS counts its cache as used. Unreadable RAM leaves
the CPU rule. jobs = the most jobs one phase can run at once. --beside-designer caps the result at CPUs // 2, a
$SUITE_JOBS too; only --jobs overrides it. workers_rule names the cap that chose: cpu, ram, jobs, beside_designer,
SUITE_JOBS or --jobs. Each job gets --threads (default 2) OMP/OpenBLAS/MKL/vecLib/numexpr threads and
PYTHONDONTWRITEBYTECODE=1. Measured up to 6 workers (8-CPU Mac); on a hybrid CPU more than ~8 heavy jobs scale
sublinearly.

Delete before run, by exact name, never a prefix glob (detail_v1_* also matches detail_v1_nwp_*): every output a job
declares, its log, and a previews job's files of the last run (<out>/suite/previews_files.json and its old part). A
full run also deletes the merged wrong_builds.{json,md}, views_index.md and the compare sheets. First of all, every
run (argparse refusals included; --plan and -h excepted) deletes the report it writes, suite.{json,md} or
suite_partial.{json,md}, so the last run's report never stands in.

Gate, per job, on exit codes and JSON, never on text. Green needs rc 0, every declared output present and written
during the job (not older than its start, 2 s slack), and:
    matcheck      hard_failed and hard_unmeasured empty: an errored or vacuous hard check (exit 3) is red, no waiver.
                  Soft errors and scorecard warnings become warnings.
    wrong_builds  every row behaves and every missing list is empty. A config job whose config has a hard check must
                  report missing[<config>], a group job at least one row of its group, else "measured nothing".
    merge         the same over the merged report. It runs only when every part exists.
    previews      every file in the part's rows written during the job.
    assemble      views_index.md and, with two or more configs, both compare sheets. It runs only with every part.
    commands      the gate: each "empty" field an empty list, object or string, each "true" field true, each "false"
                  field false; a missing field is red.
A matcheck, wrong_builds or merge exit 1 or 3 is explained by its JSON. Any other nonzero exit is red with the log's
last line; for a command, its last line with "hard" and "FAIL", else with FAIL, hard, error or Traceback (any case;
a Traceback header quotes the last line), else its last 3 lines. A job over its timeout is killed with its process
group (POSIX: own session, killpg; Windows: CREATE_NEW_PROCESS_GROUP, taskkill /T) and is red. Ctrl-C, SIGTERM,
SIGHUP, SIGQUIT or SIGBREAK kill every job and write a red report; an ignored SIGHUP (nohup) stays ignored. A SIGKILL
of the suite leaves its jobs running: the next run into that --out refuses until they end (lock.json, below).
R6, in runs with the wrong builds: a config with a non-skipped hard check that the cases never name is red, its ids
under uncovered; with no "cases", every such config is; a config with hard checks that the cases name but "configs"
misses is red (never measured).

Refused, exit 2, no job run and no report: an unreadable SUITE.json; an unknown key, kind or placeholder; a value of
the wrong type; a file named literally that does not exist, or a glob that matches nothing; previews args other than
--sites N and --no-shadows; two configs (or previews configs) with one file stem or one variant, ignoring case (one
scorecard file); two previews configs with one file-safe variant name; a variant holding / or \\, or . or ..; a comma
in a config stem, variant, cases config, cross-case group or command name (--configs and wrong_builds --only split on
commas); two commands with one name; a cwd that is not a folder; a gate json that is not one of its command's
outputs; a cases module that does not load (wrong_builds.py --list exit 2) or that names one config with and without
.json; a config or group name that is also a hard check id, a case's check id or another group (one --only job would
run another's cases); a --configs name that matches no config stem or variant, group or command; --configs/--kinds
that select no job; an output that two jobs declare (ignoring case), that is a folder, or that is one of the suite's
inputs; --jobs or --threads below 1, a --timeout not above 0, a SUITE_JOBS that is not a positive number; an --out
that is a file; matcheck.py, wrong_builds.py or previews.py missing beside suite.py; the report or a full run's merged
file that cannot be deleted (a job output that cannot be deleted makes that job red); a suite.json a filtered run
cannot move aside; another suite running into this --out, or a job of a dead one.

One suite per --out: <out>/suite/lock.json holds the running suite's pid and start, created atomically (O_EXCL), and
each running job's pid (it leads its process group) and start, rewritten atomically as jobs start and end. A run that
finds it held by a live process exits 2 naming the pid. A dead holder's lock is taken over with a warning, unless a
job it recorded still runs, or (POSIX) its process group still has members after the job itself exited (a SIGKILLed
suite's): then the run exits 2 naming the pids; kill them (POSIX:
kill -TERM -<pid>; Windows: taskkill /T /F /PID <pid>) or let them finish. One run only takes a lock over: the one
that creates lock.json.break (also atomic; one older than 10 s is a dead breaker's). Liveness: os.kill(pid, 0) and
ps's elapsed time on POSIX, OpenProcess, GetExitCodeProcess and GetProcessTimes on Windows; a process that started
after the lock (a job: after its start) is a reused pid, so not the holder. When liveness cannot be told, a lock or
job older than the largest job timeout + 60 s is stale. Every exit removes the lock (normal, red, interrupt); --plan
takes none.

Filtered runs: --configs (config stems or variants, cross-case groups, command names) and --kinds select jobs. They
write suite_partial.{json,md} with full false and never touch the merged wrong builds, views_index.md or the compare
sheets; R6 covers the selected configs only. Before its first job, a filtered run moves a suite.json in --out (with its
suite.md) to <out>/suite/superseded_suite.{json,md}, replacing older ones, and warns: the folder no longer matches it,
and a missing suite.json is never green. A refused run moves nothing. --plan prints the planned jobs as JSON (with
expect_s) and runs nothing.

Outputs in --out: scorecard_<variant>.{json,md}, wrong_builds.{json,md}, the previews with views_index.md and the
compare sheets, suite.{json,md} (suite_partial.* for a filtered run). In <out>/suite/: logs/<kind>-<name>.log,
wb/<name>/, previews/<variant>.json (the parts), previews_files.json, times.json, superseded_suite.{json,md} (filtered
runs) and lock.json while it runs.
Progress: one line per finished job, "[k/n] ok|RED <kind> <name> <s> s: <first reason>", then every red entry with
its reasons and the report paths.
suite.json: green (true only with rc 0), rc, full (no --configs or --kinds), out, suite (SUITE.json), started and ended
(local time, as a manifest's exported_at), wall_s, workers, workers_rule, threads, cpus, ram_gb, per_job_gb, load
[1-min load before, after], times_from (the times.json that ordered the jobs, or null), filter (null, or {configs,
kinds}), jobs [{name, kind, config, phase, argv, rc, seconds, timeout_s, outputs, log, red [reasons], warnings}], red
[{job, reasons}] (job "suite" for an interrupt, "R6 coverage" for R6), uncovered {config: [hard check ids]},
warnings, skipped [{path, why}].
Exit code: 0 green; 1 red, an interrupt included; 2 refused (above).
"""
import argparse
import concurrent.futures as cf
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import threading
import time

if sys.version_info < (3, 7):  # before anything an older Python cannot run; the file parses on 3.5 or newer
    sys.stderr.write("suite.py needs Python 3.7 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ("matcheck", "wrong_builds", "previews", "commands")
TOP_KEYS = ("configs", "cases", "checks_dir", "previews", "commands", "timeout", "python")
PREVIEW_KEYS = ("configs", "args")
COMMAND_KEYS = ("name", "argv", "outputs", "timeout", "expect", "after", "gate", "cwd")
GATE_KEYS = ("json", "empty", "true", "false")
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
               "NUMEXPR_NUM_THREADS")
TIMEOUT = 900.0
EXPECT_COMMAND = 5.0  # seconds a command is expected to take when SUITE.json and times.json say nothing
MTIME_SLACK = 2.0  # coarse file-system timestamps (FAT keeps 2 s)
LOCK_SLACK = 60.0  # a lock whose holder cannot be checked is stale this long after its largest job timeout
PID_SLACK = 10.0  # a process that started this long after a lock did is a reused pid (ps is to 1 s; clock steps)
BREAK_STALE = 10.0  # a lock.json.break this old is a dead breaker's (a break takes microseconds)
PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
STOP = threading.Event()
RUNNING = {}
LOCK = threading.Lock()


class SuiteError(Exception):
    """Usage or SUITE.json error: exit 2, nothing run."""


class Job:
    def __init__(self, kind, name, argv, outputs, cwd, timeout, config=None, phase=1, expect=1.0, **extra):
        self.kind, self.name, self.argv, self.outputs, self.cwd = kind, name, argv, outputs, cwd
        self.timeout, self.config, self.phase, self.expect, self.extra = timeout, config, phase, expect, extra
        self.rc, self.seconds, self.started, self.log, self.proc = None, None, None, None, None
        self.red, self.warnings, self.ran, self.timed_out, self.interrupted = [], [], False, False, False

    @property
    def key(self):
        return "%s %s" % (self.kind, self.name)


# ----------------------------------------------------------------------------- SUITE.json


def safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def safe_key(name):
    """safe(name), plus a short hash of the name when safe() changed it, so "lane v3" and "lane_v3" get two files."""
    s = safe(name)
    return s if s == name else "%s-%s" % (s, hashlib.sha1(name.encode("utf-8")).hexdigest()[:6])


def safe_name(name):
    """previews.py's file-safe variant name."""
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name)


def dups(names):
    """Names that share one file on a case-insensitive disk (the macOS and Windows default), as spelled."""
    keys = [n.casefold() for n in names]
    return sorted({n for n, k in zip(names, keys) if keys.count(k) > 1})


def no_comma(names, what):
    """--configs and wrong_builds --only split on commas: a name holding one would select nothing."""
    bad = sorted({n for n in names if "," in n})
    if bad:
        raise SuiteError("%s with a comma: %s (--configs and wrong_builds.py --only split on commas; rename it)"
                         % (what, ", ".join(repr(n) for n in bad)))


def strip_json(name):
    return name[:-5] if name.endswith(".json") else name


def unknown(d, keys, where):
    bad = sorted(set(d) - set(keys))
    if bad:
        raise SuiteError("%s: unknown key%s %s (use %s)" % (where, "s" if len(bad) > 1 else "", ", ".join(bad),
                                                             ", ".join(keys)))


def expand(s, subs, where):
    def rep(m):
        if m.group(1) not in subs:
            raise SuiteError("%s: unknown placeholder {%s} (use %s)" % (where, m.group(1),
                                                                        ", ".join("{%s}" % k for k in sorted(subs))))
        return subs[m.group(1)]
    return PLACEHOLDER.sub(rep, s)


def path_in(base, p):
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(base, p))


def str_list(v, where, empty=True):
    if not (isinstance(v, list) and all(isinstance(x, str) and x for x in v) and (empty or v)):
        raise SuiteError("%s must be a %slist of strings" % (where, "" if empty else "non-empty "))
    return v


def positive(v, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0:
        raise SuiteError("%s must be a positive number of seconds, not %r" % (where, v))
    return float(v)


def read_config(path):
    """(cfg, error): cfg None when the file does not parse (its jobs then fail with the config error)."""
    try:
        with open(path) as fh:
            return json.load(fh), None
    except (OSError, ValueError) as e:
        return None, "%s: %s" % (type(e).__name__, e)


def png_area(path):
    """Width x height from a PNG's header, None when the file is not a readable PNG."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w * h


def height_png(path, cfg):
    """The config's main height map file, resolved as matcheck resolves it."""
    maps = cfg.get("maps") if isinstance(cfg.get("maps"), dict) else {}
    stem, d = maps.get("height", "height"), maps.get("dir", ".")
    if not (isinstance(stem, str) and isinstance(d, str)):
        return None
    d = d if os.path.isabs(d) else os.path.join(os.path.dirname(path), d)
    p = stem if os.path.isabs(stem) else os.path.join(d, str(maps.get("prefix") or "") + stem)
    return p if os.path.splitext(p)[1] else p + str(maps.get("ext") or ".png")


def config_info(path):
    """What planning needs from a config: stem, variant, hard check ids, check count, map size (px / 2048^2, from the
    height map's PNG header, else from scale.resolution)."""
    cfg, _ = read_config(path)
    stem = strip_json(os.path.basename(path))
    info = {"path": path, "stem": stem, "variant": stem, "hard": [], "n_checks": 0, "px": 1.0}
    if isinstance(cfg, dict):
        checks = cfg.get("checks")
        checks = [c for c in checks if isinstance(c, dict)] if isinstance(checks, list) else []
        info["variant"] = str(cfg.get("variant") or stem)  # matcheck's scorecard_<variant> name
        info["hard"] = [str(c.get("id")) for c in checks if c.get("severity") == "hard" and not c.get("skip")]
        info["n_checks"] = len([c for c in checks if not c.get("skip")])
        res = (cfg.get("scale") or {}).get("resolution") if isinstance(cfg.get("scale"), dict) else None
        try:
            r = [float(x) for x in (res if isinstance(res, list) else [res, res])][:2]
            info["px"] = max(r[0] * r[1] / 2048.0 ** 2, 0.1)
        except (TypeError, ValueError):
            pass
        hp = height_png(path, cfg)
        area = png_area(hp) if hp else None
        if area:
            info["px"] = max(area / 2048.0 ** 2, 0.1)
    return info


def expand_configs(patterns, tools, suite_path, where, skipped):
    """Config files for a list of globs or paths, in order, de-duplicated."""
    out, seen = [], set()
    for pat in patterns:
        if any(ch in pat for ch in "*?["):
            hits = sorted(glob.glob(os.path.join(glob.escape(tools), pat) if not os.path.isabs(pat) else pat))
            if not hits:  # a typo would otherwise measure nothing and still be green
                raise SuiteError("%s: %s matches no file" % (where, pat))
        else:
            hits = [path_in(tools, pat)]
            if not os.path.isfile(hits[0]):
                raise SuiteError("%s: no such file: %s" % (where, pat))
        for h in hits:
            h = os.path.normpath(os.path.abspath(h))
            if h in seen or not os.path.isfile(h):
                continue
            seen.add(h)
            base = os.path.basename(h)
            why = None
            if base.startswith("scorecard_"):
                why = "a matcheck scorecard"
            elif os.path.realpath(h) == os.path.realpath(suite_path) or base == "SUITE.json":
                why = "the suite file"
            elif not base.endswith(".json"):
                why = "not a .json file"
            else:
                cfg, err = read_config(h)
                if err is None and not (isinstance(cfg, dict) and "checks" in cfg):  # a non-list goes to matcheck
                    why = "no \"checks\" key"
            if why:
                if not any(s["path"] == h for s in skipped):
                    skipped.append({"path": h, "why": why})
                continue
            out.append(h)
    return out


def load_suite(path, out, scripts):
    """Validated SUITE.json with absolute paths."""
    try:
        with open(path) as fh:
            s = json.load(fh)
    except (OSError, ValueError) as e:
        raise SuiteError("cannot read %s: %s" % (path, e))
    if not isinstance(s, dict):
        raise SuiteError("%s: not a JSON object" % path)
    unknown(s, TOP_KEYS, "SUITE.json")
    tools = os.path.dirname(os.path.abspath(path))
    st = {"path": os.path.abspath(path), "tools": tools, "skipped": [], "warnings": []}
    py = s.get("python")
    if py is None:
        py = sys.executable
    elif not isinstance(py, str) or not py:
        raise SuiteError("SUITE.json python must be a path or a command name")
    elif os.sep in py or "/" in py:
        py = path_in(tools, py)
    else:
        py = shutil.which(py) or py
    if not (os.path.isfile(py) and os.access(py, os.X_OK)):
        raise SuiteError("SUITE.json python: %s is not an executable file" % py)
    st["python"] = py
    subs = {"python": py, "out": out, "tools": tools, "scripts": scripts}
    st["timeout"] = positive(s["timeout"], "SUITE.json timeout") if "timeout" in s else None
    if "configs" not in s:
        raise SuiteError("SUITE.json needs \"configs\" (globs or files of checks configs)")
    st["configs"] = expand_configs(str_list(s["configs"], "SUITE.json configs", empty=False), tools, path,
                                   "configs", st["skipped"])
    st["cases"] = None
    if s.get("cases") is not None:
        if not isinstance(s["cases"], str) or not s["cases"]:
            raise SuiteError("SUITE.json cases must be the path of a cases module")
        st["cases"] = path_in(tools, s["cases"])
        if not os.path.isfile(st["cases"]):
            raise SuiteError("SUITE.json cases: no such file: %s" % s["cases"])
    if s.get("checks_dir") is not None:
        if not isinstance(s["checks_dir"], str) or not s["checks_dir"]:
            raise SuiteError("SUITE.json checks_dir must be a folder")
        st["checks_dir"] = path_in(tools, s["checks_dir"])
    else:
        st["checks_dir"] = os.path.dirname(st["cases"]) if st["cases"] else os.path.join(tools, "checks")
    if st["cases"] and not os.path.isdir(st["checks_dir"]):
        raise SuiteError("SUITE.json checks_dir: no such folder: %s" % st["checks_dir"])
    st["previews"], st["previews_args"] = [], []
    pv = s.get("previews")
    if pv is not None:
        if not isinstance(pv, dict):
            raise SuiteError("SUITE.json previews must be an object {\"configs\": [...], \"args\": [...]}")
        unknown(pv, PREVIEW_KEYS, "SUITE.json previews")
        pats = str_list(pv["configs"], "SUITE.json previews.configs", empty=False) if "configs" in pv else s["configs"]
        st["previews"] = expand_configs(pats, tools, path, "previews.configs", st["skipped"])
        args = str_list(pv.get("args", []), "SUITE.json previews.args")
        i = 0
        while i < len(args):
            if args[i] == "--no-shadows":
                i += 1
            elif args[i] == "--sites" and i + 1 < len(args) and args[i + 1].isdigit():
                i += 2
            elif re.match(r"^--sites=\d+$", args[i]):
                i += 1
            else:
                raise SuiteError("SUITE.json previews.args: %r (use --sites N and --no-shadows)" % args[i])
        st["previews_args"] = args
    st["commands"] = []
    cmds = s.get("commands", [])
    if not isinstance(cmds, list):
        raise SuiteError("SUITE.json commands must be a list")
    for k, c in enumerate(cmds):
        where = "SUITE.json commands[%d]" % k
        if not isinstance(c, dict):
            raise SuiteError("%s is not an object" % where)
        unknown(c, COMMAND_KEYS, where)
        name = c.get("name")
        if not isinstance(name, str) or not name.strip():
            raise SuiteError("%s needs a \"name\"" % where)
        where = "command '%s'" % name
        if any(x["name"] == name for x in st["commands"]):
            raise SuiteError("two commands are named '%s'" % name)
        no_comma([name], "a command name")
        argv = [expand(a, subs, where) for a in str_list(c.get("argv"), "%s argv" % where, empty=False)]
        outs = [path_in(tools, expand(o, subs, where)) for o in str_list(c.get("outputs", []), "%s outputs" % where)]
        if "cwd" in c and not (isinstance(c["cwd"], str) and c["cwd"]):
            raise SuiteError("%s cwd must be a folder" % where)
        cwd = path_in(tools, expand(c["cwd"], subs, where)) if "cwd" in c else tools
        if not os.path.isdir(cwd):
            raise SuiteError("%s cwd: no such folder: %s" % (where, cwd))
        if not isinstance(c.get("after", False), bool):
            raise SuiteError("%s after must be true or false" % where)
        gate = c.get("gate")
        if gate is not None:
            if not isinstance(gate, dict) or not isinstance(gate.get("json"), str):
                raise SuiteError("%s gate must be {\"json\": path, \"empty\": [...], \"true\": [...], \"false\": [...]}"
                                 % where)
            unknown(gate, GATE_KEYS, "%s gate" % where)
            gate = dict(gate, json=path_in(tools, expand(gate["json"], subs, where)))
            for f in ("empty", "true", "false"):
                gate[f] = str_list(gate.get(f, []), "%s gate.%s" % (where, f))
            if gate["json"] not in outs:
                raise SuiteError("%s gate.json must be one of its outputs, so a stale file is deleted first" % where)
        st["commands"].append({"name": name, "argv": argv, "outputs": outs, "cwd": cwd, "after": c.get("after", False),
                               "gate": gate, "timeout": positive(c["timeout"], "%s timeout" % where)
                               if "timeout" in c else None,
                               "expect": positive(c["expect"], "%s expect" % where) if "expect" in c else None})
    if not st["configs"] and not st["commands"]:
        raise SuiteError("SUITE.json selects no config and no command")
    return st


# ----------------------------------------------------------------------------- planning


def list_cases(st, env):
    """wrong_builds.py --list: the cases' configs and groups, in the order a serial run takes them."""
    argv = [st["python"], os.path.join(HERE, "wrong_builds.py"), "--cases", st["cases"], "--list"]
    try:
        r = subprocess.run(argv, cwd=st["tools"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise SuiteError("wrong_builds.py --list: %s" % e)
    if r.returncode != 0:
        tail = [ln for ln in (r.stderr or "").splitlines() if ln.strip()]
        raise SuiteError("the cases module does not load (wrong_builds.py --list exit %d): %s"
                         % (r.returncode, tail[-1] if tail else "no message"))
    for line in reversed((r.stdout or "").splitlines()):
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict) and isinstance(data.get("configs"), list) and isinstance(data.get("groups"), list):
            if all(isinstance(x, str) and x for x in data["configs"] + data["groups"]):
                data["ids"] = [x for x in data.get("ids") or [] if isinstance(x, str)]
                return data
            raise SuiteError("wrong_builds.py --list: config and group names must be strings")
    raise SuiteError("wrong_builds.py --list printed no JSON")


def wb_config_path(checks_dir, name):
    return os.path.join(checks_dir, name if name.endswith(".json") else name + ".json")


def load_dict(path):
    """A JSON object from path, {} when missing or unreadable (history and file lists are hints, not gates)."""
    try:
        with open(path) as fh:
            t = json.load(fh)
        return t if isinstance(t, dict) else {}
    except (OSError, ValueError):
        return {}


def load_times(out):
    """(times, path): the job seconds of <out>/suite/times.json; when --out has none yet, of the newest
    <sibling>/suite/times.json beside it (last round's folder); else ({}, None). They order jobs, never gate them."""
    own = os.path.join(out, "suite", "times.json")
    if os.path.isfile(own):
        return load_dict(own), own
    parent, best = os.path.dirname(out), None
    try:
        names = sorted(os.listdir(parent))
    except OSError:
        names = []
    for n in names:
        p = os.path.join(parent, n, "suite", "times.json")
        if os.path.normcase(os.path.join(parent, n)) == os.path.normcase(out):
            continue
        try:
            m = os.stat(p).st_mtime
        except OSError:
            continue
        if best is None or m > best[0]:
            best = (m, p)
    return (load_dict(best[1]), best[1]) if best else ({}, None)


def plan(st, a, out, env):
    """(jobs, info): every job of this run, phase 1 then phase 2, plus the R6 coverage and the selection."""
    py, tools = st["python"], st["tools"]
    work = os.path.join(out, "suite")
    kinds = list(KINDS) if not a.kinds else [k.strip() for k in a.kinds.split(",") if k.strip()]
    bad = [k for k in kinds if k not in KINDS]
    if bad or not kinds:
        raise SuiteError("--kinds: unknown kind %s (use %s)" % (", ".join(bad) or "''", ",".join(KINDS)))
    names = [n.strip() for n in a.configs.split(",") if n.strip()] if a.configs else None
    if a.configs is not None and not names:
        raise SuiteError("--configs names no config")
    full = names is None and set(kinds) == set(KINDS)
    matched = set()

    def pick(*keys):
        if names is None:
            return True
        hit = [k for k in keys if k in names]
        matched.update(hit)
        return bool(hit)

    configs = [config_info(p) for p in st["configs"]]
    pconfigs = [config_info(p) for p in st["previews"]]
    if "previews" in kinds and not pconfigs:
        st["warnings"].append("no previews configs (SUITE.json \"previews\"), so this run renders no previews")
    no_comma([c["stem"] for c in configs + pconfigs], "a config file name")
    no_comma([c["variant"] for c in configs + pconfigs], "a config variant")
    for group, label in ((configs, "configs"), (pconfigs, "previews configs")):
        for key, what in (("stem", "file name"), ("variant", "variant (one scorecard)")):
            dup = dups([c[key] for c in group])
            if dup:
                raise SuiteError("two %s have one %s: %s" % (label, what, ", ".join(dup)))
        for c in group:
            if re.search(r"[\\/]", c["variant"]) or c["variant"] in (".", ".."):
                raise SuiteError("%s: variant %r is not a file name" % (c["path"], c["variant"]))
    dup = dups([safe_name(c["variant"]) for c in pconfigs])
    if dup:
        raise SuiteError("two previews configs have one file-safe variant name: %s (their PNGs would overwrite each "
                         "other)" % ", ".join(dup))
    by_real = {os.path.realpath(c["path"]): c for c in configs}
    times, times_from = load_times(out)
    timeout = a.timeout or st["timeout"] or TIMEOUT
    jobs = []

    def add(job):
        t = times.get(job.key)
        if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
            job.expect = float(t)  # the last run's seconds beat the estimate
        jobs.append(job)

    for c in configs:
        sel = pick(c["stem"], c["variant"])
        if sel and "matcheck" in kinds:
            add(Job("matcheck", c["stem"], [py, os.path.join(HERE, "matcheck.py"), c["path"], "--out", out, "--quiet"],
                    [os.path.join(out, "scorecard_%s.%s" % (c["variant"], e)) for e in ("json", "md")], tools,
                    timeout, config=c["stem"], expect=(1.0 + 0.1 * c["n_checks"]) * c["px"]))
    listed, unlisted = {"configs": [], "groups": [], "cases": 0, "ids": []}, []
    if st["cases"] and "wrong_builds" in kinds:
        listed = list_cases(st, env)
        no_comma(listed["configs"], "a config the cases name")
        no_comma(listed["groups"], "a cross-case group")
        stems = [strip_json(n) for n in listed["configs"]]
        dup = sorted({s for s in stems if stems.count(s) > 1})
        if dup:
            raise SuiteError("the cases name one config twice (with and without .json): %s" % ", ".join(dup))
        parts = listed["configs"] + listed["groups"]
        clash = sorted({g for g in listed["groups"] if strip_json(g) in stems})
        ids = set(listed["ids"])  # what --only selects besides configs and groups: hard ids and the cases' ids
        for n in listed["configs"]:
            cfg, _ = read_config(wb_config_path(st["checks_dir"], n))
            if isinstance(cfg, dict) and isinstance(cfg.get("checks"), list):
                ids.update(c.get("id") for c in cfg["checks"] if isinstance(c, dict) and c.get("severity") == "hard"
                           and not c.get("skip"))
        clash += sorted({p for p in parts if p in ids})
        if clash:
            raise SuiteError("wrong_builds.py --only cannot split these cases: %s is both a config or group name and "
                             "a hard check id, a case's check id or a group, so one job would run another's cases; "
                             "rename it" % ", ".join(clash))
        per_config = float(listed.get("cases") or 0) / max(1, len(listed["configs"]))  # about 0.5 s a case
        for n in listed["configs"]:
            real = os.path.realpath(wb_config_path(st["checks_dir"], n))
            c = by_real.get(real) or config_info(wb_config_path(st["checks_dir"], n))
            if not pick(n, strip_json(n), c["variant"]):
                continue
            if real not in by_real and c["hard"]:
                unlisted.append(strip_json(n))
            d = os.path.join(work, "wb", safe_key(strip_json(n)))
            add(Job("wrong_builds", strip_json(n), [py, os.path.join(HERE, "wrong_builds.py"), "--cases", st["cases"],
                                                    "--checks-dir", st["checks_dir"], "--only", n, "--out", d],
                    [os.path.join(d, "wrong_builds.json"), os.path.join(d, "wrong_builds.md")], tools, timeout,
                    config=strip_json(n), expect=(0.5 + 0.5 * max(len(c["hard"]), per_config)) * c["px"], dir=d,
                    only=n, hard=bool(c["hard"])))
        for g in listed["groups"]:
            if not pick(g):
                continue
            d = os.path.join(work, "wb", safe_key(g))
            add(Job("wrong_builds", g, [py, os.path.join(HERE, "wrong_builds.py"), "--cases", st["cases"],
                                        "--checks-dir", st["checks_dir"], "--only", g, "--out", d],
                    [os.path.join(d, "wrong_builds.json"), os.path.join(d, "wrong_builds.md")], tools, timeout,
                    expect=3.0, dir=d, group=g))
    for c in pconfigs:
        if not pick(c["stem"], c["variant"]) or "previews" not in kinds:
            continue
        part = os.path.join(work, "previews", safe_name(c["variant"]) + ".json")
        add(Job("previews", c["stem"], [py, os.path.join(HERE, "previews.py"), c["path"], "--out", out, "--part", part]
                + st["previews_args"], [part], tools, timeout, config=c["stem"], expect=4.0 * c["px"],
                variant=safe_name(c["variant"])))
    for c in st["commands"]:
        if pick(c["name"]) and "commands" in kinds:
            add(Job("commands", c["name"], c["argv"], c["outputs"], c["cwd"], c["timeout"] or timeout,
                    phase=2 if c["after"] else 1, expect=c["expect"] or EXPECT_COMMAND, gate=c["gate"]))
    if names is not None:
        miss = [n for n in names if n not in matched]
        if miss:
            raise SuiteError("--configs: %s matches no config, cross-case group or command" % ", ".join(miss))
    if full and st["cases"] and listed["configs"] + listed["groups"]:
        dirs = [j.extra["dir"] for j in jobs if j.kind == "wrong_builds"]
        add(Job("merge", "wrong_builds", [py, os.path.join(HERE, "wrong_builds.py"), "--merge"]
                + [os.path.relpath(d, work) for d in dirs] + ["--out", out],
                [os.path.join(out, "wrong_builds.json"), os.path.join(out, "wrong_builds.md")], work, timeout,
                phase=2, expect=1.0))
    if full and pconfigs:
        parts = [j.outputs[0] for j in jobs if j.kind == "previews"]
        outs = [os.path.join(out, "views_index.md")]
        if len(parts) > 1:
            outs += [os.path.join(out, "compare_front.png"), os.path.join(out, "compare_crop_raking.png")]
        add(Job("assemble", "previews", [py, os.path.join(HERE, "previews.py"), "--assemble"]
                + [os.path.relpath(p, work) for p in parts] + ["--out", out], outs, work, timeout, phase=2,
                expect=1.0))
    if not jobs:
        raise SuiteError("--configs/--kinds select no job")
    seen = {}
    inputs = {os.path.realpath(p) for p in [st["path"], st["cases"] or ""] + st["configs"] + st["previews"] if p}
    for j in jobs:
        j.log = os.path.join(work, "logs", "%s-%s.log" % (j.kind, safe_key(j.name)))
        for p in j.outputs + [j.log]:
            k = os.path.normcase(p).casefold()  # one file on a case-insensitive disk
            if k in seen and seen[k] != j.key:
                raise SuiteError("%s and %s both write %s" % (seen[k], j.key, p))
            if os.path.realpath(p) in inputs:
                raise SuiteError("%s declares an input of the suite as its output: %s" % (j.key, p))
            if os.path.isdir(p):
                raise SuiteError("%s declares a folder as an output: %s (outputs are files, deleted before the run)"
                                 % (j.key, p))
            seen[k] = j.key
    # R6: every config with a hard check needs a wrong-build case (static: the cases' --list)
    uncovered, r6 = {}, []
    if "wrong_builds" in kinds:
        covered = {os.path.realpath(wb_config_path(st["checks_dir"], n)) for n in listed["configs"]}
        for c in configs:
            if c["hard"] and (names is None or c["stem"] in names or c["variant"] in names) and \
                    os.path.realpath(c["path"]) not in covered:
                uncovered[c["stem"]] = sorted(set(c["hard"]))
        if uncovered:
            if not st["cases"]:
                r6.append("no \"cases\" in SUITE.json, but %d config(s) have hard checks: every hard check needs a "
                          "named wrong build (wrong_builds.py)" % len(uncovered))
            r6 += ["%s: %d hard check(s) without a wrong-build case, the cases never name this config (ids under "
                   "uncovered)" % (k, len(v)) for k, v in uncovered.items()]
        r6 += ["%s: the cases name this config but SUITE.json configs miss it, so its hard checks are never measured"
               % k for k in unlisted]
    px = max([c["px"] for c in configs + pconfigs] or [1.0])
    return jobs, {"full": full, "kinds": kinds, "names": names, "uncovered": uncovered, "r6": r6, "listed": listed,
                  "px": px, "times": times, "times_from": times_from}


# ----------------------------------------------------------------------------- running


def start(job, env, log):
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)
    else:
        kw["start_new_session"] = True
    return subprocess.Popen(job.argv, cwd=job.cwd, env=env, stdin=subprocess.DEVNULL, stdout=log,
                            stderr=subprocess.STDOUT, **kw)


def kill_tree(p):
    """Kill a job and everything it started (its process group); the leader is still unreaped here."""
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            p.kill()
        except OSError:
            pass
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def run_job(job, env, progress, lock=None):
    try:
        if STOP.is_set():
            job.interrupted = True
            job.red.append("not run: the suite was interrupted")
            return
        os.makedirs(os.path.dirname(job.log), exist_ok=True)
        with open(job.log, "w") as log:
            log.write("$ %s\n" % json.dumps(job.argv))
            log.flush()
            job.started = time.time()
            job.ran = True
            try:
                p = start(job, env, log)
            except OSError as e:
                job.red.append("cannot start: %s" % e)
                job.seconds = 0.0
                return
            job.proc = p
            with LOCK:
                RUNNING[job.key] = job
                why = record_jobs(lock)
            if why:
                job.warnings.append("not recorded in lock.json: %s" % why)
            deadline = job.started + job.timeout
            while True:
                try:
                    p.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    if STOP.is_set() or time.time() > deadline:
                        job.interrupted = STOP.is_set()
                        job.timed_out = not job.interrupted
                        kill_tree(p)
                        p.wait()
                        break
            with LOCK:
                RUNNING.pop(job.key, None)
                record_jobs(lock)
            if STOP.is_set() and p.returncode != 0 and not job.timed_out:
                job.interrupted = True  # killed by kill_all() before this thread saw STOP
            job.rc = p.returncode
            job.seconds = round(time.time() - job.started, 2)
        gate(job)
    except Exception as e:  # a suite bug must still leave the job red, never green
        job.red.append("suite error: %s: %s" % (type(e).__name__, e))
    finally:
        progress(job)


def kill_all():
    with LOCK:
        procs = [j.proc for j in RUNNING.values()]
    for p in procs:
        if p.poll() is None:
            kill_tree(p)


# ----------------------------------------------------------------------------- gates


def log_lines(path):
    """The non-empty lines of a job log's last 8 KB, without the argv header."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - 8192))
            lines = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("$ [")]


def tail(path, n=1):
    return " | ".join(log_lines(path)[-n:])[:300]


def command_why(path):
    """A command's rc reason: its last log line with "hard" and "FAIL" (a ladder's failed hard row, not the soft rows
    after it), else its last with FAIL, hard, error or Traceback (a Traceback header gives way to the last line, the
    exception), else its last 3 lines."""
    lines = log_lines(path)
    for test in (lambda ln: re.search(r"hard", ln, re.I) and re.search(r"fail", ln, re.I),
                 lambda ln: re.search(r"fail|hard|error|traceback", ln, re.I)):
        hit = [ln for ln in lines if test(ln)]
        if hit:
            return (lines[-1] if hit[-1].startswith("Traceback (most recent call last)") else hit[-1])[:300]
    return " | ".join(lines[-3:])[:300]


def short(v, n=80):
    s = json.dumps(v) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n - 3] + "..."


def fresh(job, p, label=None):
    """None when p exists and was written during the job, else the reason."""
    label = label or p
    try:
        m = os.stat(p).st_mtime
    except OSError:
        return "missing output %s" % label
    if m < job.started - MTIME_SLACK:
        return "stale output %s (older than the job's start)" % label
    return None


def read_json(job, p):
    try:
        with open(p) as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        job.red.append("unreadable output %s: %s" % (p, e))
        return None


def rel(job, p):
    out = job.extra.get("out_dir")
    return os.path.relpath(p, out) if out and p.startswith(out + os.sep) else p


def field(data, name):
    cur = data
    for part in name.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(name)
        cur = cur[part]
    return cur


def gate_matcheck(job):
    card = read_json(job, job.outputs[0])
    if not isinstance(card, dict):
        return []
    reasons = []
    if not all(isinstance(card.get(k), list) for k in ("hard_failed", "hard_unmeasured")):
        return ["scorecard has no hard_failed / hard_unmeasured lists (matcheck too old?)"]
    rows = {r.get("id"): r for r in card.get("results", []) if isinstance(r, dict)}
    for cid in card["hard_failed"]:
        r = rows.get(cid, {})
        reasons.append("hard check failed: %s (value %s, target %s)" % (cid, short(r.get("value")),
                                                                       short(r.get("target"))))
    for cid in card["hard_unmeasured"]:
        r = rows.get(cid, {})
        why = "error: %s" % r["error"] if r.get("error") else (r.get("note") or "no value")
        reasons.append("hard check measured nothing: %s (%s)" % (cid, short(why, 160)))
    for cid in card.get("errors", []):
        r = rows.get(cid, {})
        if r.get("severity") != "hard":
            job.warnings.append("soft check errored: %s: %s" % (cid, short(r.get("error"), 160)))
    job.warnings += ["scorecard warning: %s" % short(w, 200) for w in card.get("warnings", [])]
    return reasons


def wb_label(passed, fail, note):
    """A wrong-builds pass in words: an unmeasured one (null) is vacuous, or an error when the row's note says
    something other than "vacuous: ..." (a missing map, an edit that raised)."""
    if passed:
        return "pass"
    if passed is False:
        return fail
    return "error" if note and not note.startswith("vacuous") else "vacuous"


def wb_reasons(data, job, uncovered):
    reasons = []
    if not (isinstance(data, dict) and isinstance(data.get("rows"), list) and isinstance(data.get("missing"), dict)):
        return ["wrong_builds.json has no rows / missing"]
    for r in data["rows"]:
        if not r.get("behaves"):
            note = str(r.get("note") or "")
            reasons.append("case misbehaves: %s/%s: %s (real %s %s, wrong %s %s)%s" % (
                r.get("config"), r.get("check"), short(r.get("wrong_build"), 100), short(r.get("real"), 30),
                wb_label(r.get("real_pass"), "FAIL", note), short(r.get("wrong"), 30),
                wb_label(r.get("wrong_pass"), "fail", note), ": " + short(note, 160) if note else ""))
    for k, v in data["missing"].items():
        if v:
            reasons.append("hard check without a wrong-build case: %s: %s" % (k, ", ".join(map(str, v))))
            uncovered.setdefault(strip_json(k), [])
            uncovered[strip_json(k)] = sorted(set(uncovered[strip_json(k)]) | set(v))
    job.warnings += ["case on a check that is not hard in that config (skipped): %s" % "/".join(map(str, x))
                     for x in data.get("not_hard", [])]
    # proof that --only selected what the job is named after (a name --only cannot split selects nothing)
    if job.kind == "wrong_builds" and job.extra.get("group"):
        if not any(r.get("config") == job.extra["group"] for r in data["rows"]):
            reasons.append("measured nothing for cross-case group %s: wrong_builds.json has no row of it"
                           % job.extra["group"])
    elif job.kind == "wrong_builds" and job.extra.get("hard") and job.extra.get("only") not in data["missing"]:
        reasons.append("measured nothing for %s: its config has hard checks, but wrong_builds.json has no missing "
                       "entry for it" % job.extra.get("only"))
    return reasons


def gate(job):
    if job.timed_out:
        job.red.append("timed out after %g s: killed with its process group" % job.timeout)
    if job.interrupted:
        job.red.append("interrupted: killed with its process group")
    stopped = job.timed_out or job.interrupted
    specific, out_reasons = [], []
    for p in job.outputs:
        r = fresh(job, p, rel(job, p))
        if r:
            out_reasons.append(r)
    ok = lambda p: fresh(job, p) is None
    if not stopped:
        if job.kind == "matcheck" and ok(job.outputs[0]):
            specific = gate_matcheck(job)
        elif job.kind in ("wrong_builds", "merge") and ok(job.outputs[0]):
            data = read_json(job, job.outputs[0])
            if data is not None:
                specific = wb_reasons(data, job, job.extra.setdefault("uncovered", {}))
                if job.kind == "merge" and specific:
                    bad = sum(1 for s in specific if s.startswith("case misbehaves"))
                    specific = ["merged report: %d misbehaving case(s), uncovered %s" % (
                        bad, json.dumps(job.extra["uncovered"]) if job.extra["uncovered"] else "none")]
        elif job.kind == "previews" and ok(job.outputs[0]):
            part = read_json(job, job.outputs[0])
            try:
                rows, warn = part["info"]["rows"], part["info"].get("warn", [])
                for row in rows:
                    r = fresh(job, os.path.join(job.extra["out_dir"], os.path.basename(row[0])), row[0])
                    if r:
                        specific.append(r.replace("output", "preview file", 1))
                job.extra["files"] = [os.path.basename(row[0]) for row in rows]
                job.warnings += ["previews: %s" % short(w, 200) for w in warn]
            except (TypeError, KeyError, IndexError):
                if part is not None:
                    specific.append("previews part file has no info.rows")
        elif job.kind == "commands" and job.extra.get("gate") and ok(job.extra["gate"]["json"]):
            g = job.extra["gate"]
            data = read_json(job, g["json"])
            if data is not None:
                tests = (("empty", lambda v: isinstance(v, (list, dict, str)) and len(v) == 0),
                         ("true", lambda v: v is True), ("false", lambda v: v is False))
                for what, test in tests:
                    for f in g[what]:
                        try:
                            v = field(data, f)
                        except KeyError:
                            specific.append("gate: %s has no field %s" % (os.path.basename(g["json"]), f))
                            continue
                        if not test(v):
                            specific.append("gate: %s is not %s: %s" % (f, what, short(v)))
    # rc 1 (hard fail, misbehaving case) and 3 (unmeasured) are explained by the JSON reasons; anything else is not
    explained = specific and job.kind in ("matcheck", "wrong_builds", "merge") and job.rc in (1, 3)
    if not stopped and job.rc not in (0, None) and not explained:
        job.red.append("rc %s: %s" % (job.rc, (command_why(job.log) if job.kind == "commands" else tail(job.log))
                                      or "no output"))
    job.red += specific + out_reasons


# ----------------------------------------------------------------------------- report


def stamp(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))


def load1():
    try:
        return round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        return None


def write_atomic(path, text):
    tmp = os.path.join(os.path.dirname(path), ".%s.tmp" % os.path.basename(path))
    with open(tmp, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def job_dict(j):
    return {"name": j.name, "kind": j.kind, "config": j.config, "phase": j.phase, "argv": j.argv, "rc": j.rc,
            "seconds": j.seconds, "timeout_s": j.timeout, "outputs": j.outputs, "log": j.log, "red": j.red,
            "warnings": j.warnings}


def write_reports(out, doc):
    base = "suite" if doc["full"] else "suite_partial"
    write_atomic(os.path.join(out, base + ".json"), json.dumps(doc, indent=1))
    L = ["# Suite: %s" % ("GREEN" if doc["green"] else "RED"), "",
         "`%s` -> `%s`. %s. %d jobs, %d workers x %d threads, wall %.1f s, load %s -> %s, exit code %d." % (
             doc["suite"], doc["out"], "Full run" if doc["full"] else "Partial run (--configs %s, --kinds %s)" % (
                 ",".join(doc["filter"]["configs"] or ["all"]), ",".join(doc["filter"]["kinds"])),
             len(doc["jobs"]), doc["workers"], doc["threads"], doc["wall_s"], doc["load"][0], doc["load"][1],
             doc["rc"]), ""]
    if doc["red"]:
        L += ["## Red", ""] + ["- **%s**: %s" % (r["job"], "; ".join(r["reasons"])) for r in doc["red"]] + [""]
    if doc["uncovered"]:
        L += ["## Hard checks without a wrong-build case (R6)", ""]
        L += ["- %s: %s" % (k, ", ".join(v)) for k, v in doc["uncovered"].items()] + [""]
    warns = doc["warnings"] + ["%s %s: %s" % (j["kind"], j["name"], w) for j in doc["jobs"] for w in j["warnings"]]
    if warns:
        L += ["## Warnings", ""] + ["- " + w.replace("\n", " ") for w in warns] + [""]
    if doc["skipped"]:
        L += ["## Skipped files", ""] + ["- `%s`: %s" % (s["path"], s["why"]) for s in doc["skipped"]] + [""]
    L += ["## Jobs", "", "| job | phase | rc | seconds | result |", "|---|---|---|---|---|"]
    for j in doc["jobs"]:
        L.append("| %s %s | %d | %s | %s | %s |" % (j["kind"], j["name"], j["phase"], j["rc"], j["seconds"],
                                                     ("RED: " + "; ".join(j["red"])).replace("|", "/")
                                                     if j["red"] else "ok"))
    write_atomic(os.path.join(out, base + ".md"), "\n".join(L) + "\n")
    return os.path.join(out, base + ".json"), os.path.join(out, base + ".md")


# ----------------------------------------------------------------------------- main


def env_for(threads):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    env.update((k, str(threads)) for k in THREAD_VARS)
    return env


def total_ram():
    """Total physical RAM in bytes, None when it cannot be read. Total, not free: macOS counts its cache as used."""
    try:
        if os.name == "nt":
            import ctypes

            class Status(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + \
                    [(k, ctypes.c_ulonglong) for k in ("ullTotalPhys", "ullAvailPhys", "ullTotalPageFile",
                                                       "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
                                                       "ullAvailExtendedVirtual")]
            m = Status()
            m.dwLength = ctypes.sizeof(Status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                return None
            return int(m.ullTotalPhys) or None
        n = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        return n if n > 0 else None
    except (AttributeError, ValueError, OSError):
        return None


def per_job_gb(px):
    """A job's peak RAM: 1.5 GB at 2048 px or less, scaled by the pixels of the largest height map (px / 2048^2)."""
    return round(1.5 * max(1.0, px), 2)


def workers_for(cpus, ram_bytes, job_gb, n_jobs, beside=False, env_jobs=None, cli_jobs=None):
    """(workers, rule): --jobs, else SUITE_JOBS, else max(1, min(CPUs - 2, 16, RAM jobs, jobs)); beside a Designer
    build at most CPUs // 2, SUITE_JOBS too (only --jobs overrides it). RAM jobs = (total RAM - 4 GB) / job_gb, left
    out when the RAM is unknown. rule names the cap that chose the number: cpu, ram, jobs, beside_designer,
    SUITE_JOBS or --jobs."""
    if cli_jobs is not None:
        return cli_jobs, "--jobs"
    cpus = cpus or 3
    if env_jobs:
        if not env_jobs.strip().isdigit() or int(env_jobs) < 1:
            raise SuiteError("SUITE_JOBS=%r: use a positive number of workers" % env_jobs)
        rule, n = "SUITE_JOBS", int(env_jobs)
    else:
        caps = [("cpu", min(cpus - 2, 16))]
        if ram_bytes:
            caps.append(("ram", int((ram_bytes / 2.0 ** 30 - 4) // job_gb)))
        caps.append(("jobs", n_jobs))
        rule, n = min(caps, key=lambda c: c[1])  # the first of equal caps
    if beside and cpus // 2 < n:
        rule, n = "beside_designer", cpus // 2
    return max(1, n), rule


def stale_previews(job, work, out):
    """The previous run's files of this variant (its file list and its old part file), by exact name."""
    names = set(load_dict(os.path.join(work, "previews_files.json")).get(job.extra["variant"], []))
    old = load_dict(job.outputs[0])
    try:
        names.update(os.path.basename(r[0]) for r in old["info"]["rows"])
    except (KeyError, TypeError, IndexError):
        pass
    return [os.path.join(out, n) for n in sorted(x for x in names if isinstance(x, str))
            if n and os.path.basename(n) == n]


def pid_alive(pid, since=None):
    """True or False, or None when this process cannot tell. With since (a lock's start, epoch seconds), a live
    process that started after it is not the lock's holder but a reused pid: False."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    if pid == os.getpid():
        return False  # a recycled pid: this run holds no lock yet
    if not isinstance(since, (int, float)) or isinstance(since, bool):
        since = None
    if os.name == "nt":  # os.kill on Windows terminates the process, so ask the kernel instead
        try:
            import ctypes
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            k.OpenProcess.restype = ctypes.c_void_p
            k.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
            k.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
            k.GetProcessTimes.argtypes = (ctypes.c_void_p,) + (ctypes.POINTER(ctypes.c_ulonglong),) * 4
            k.CloseHandle.argtypes = (ctypes.c_void_p,)
            h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                err = ctypes.get_last_error()
                return False if err == 87 else True if err == 5 else None  # no such process; access denied
            try:
                code = ctypes.c_ulong()
                if not k.GetExitCodeProcess(h, ctypes.byref(code)):
                    return None
                if code.value != 259:  # STILL_ACTIVE
                    return False
                ft = [ctypes.c_ulonglong() for _ in range(4)]  # creation, exit, kernel, user: 100 ns since 1601
                if since is not None and k.GetProcessTimes(h, *[ctypes.byref(x) for x in ft]):
                    return ft[0].value / 1e7 - 11644473600.0 <= since + PID_SLACK
                return True
            finally:
                k.CloseHandle(h)
        except (AttributeError, OSError, ValueError):
            return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    except (OSError, OverflowError, ValueError):
        return None
    born = started_at(pid) if since is not None else None
    return born is None or born <= since + PID_SLACK


def started_at(pid):
    """When POSIX process pid started (epoch seconds, from ps's elapsed time), or None when ps cannot tell. Never
    later than the true start + 1 s: the clock is read before ps."""
    t = time.time()
    try:
        r = subprocess.run(["ps", "-o", "etime=", "-p", str(pid)], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, universal_newlines=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.match(r"\s*(?:(?:(\d+)-)?(\d+):)?(\d+):(\d+)\s*$", r.stdout)  # [[dd-]hh:]mm:ss
    if r.returncode or not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return t - (((d * 24 + h) * 60 + mi) * 60 + s)


def lock_state(held, alive, now, max_timeout):
    """Whether a lock is "held" or "stale": a live holder holds it, a dead one does not; when liveness is unknown
    (alive None), it is stale once older than its largest job timeout (else ours) + LOCK_SLACK."""
    if alive is not None:
        return "held" if alive else "stale"
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    lim = held["max_timeout_s"] if num(held.get("max_timeout_s")) else max_timeout
    t = held["started"] if num(held.get("started")) else held.get("mtime", now)  # unreadable: the file's age
    return "held" if now - t <= lim + LOCK_SLACK else "stale"


def read_lock(path):
    """The lock's contents plus its mtime, {} when it is gone; a lock being written reads after a short wait."""
    for _ in range(10):
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return {}
        held = load_dict(path)
        if "pid" in held:
            break
        time.sleep(0.05)
    held["mtime"] = mtime
    return held


def take_lock(work, max_timeout, warnings):
    """(lock, None) once this run holds <out>/suite/lock.json, else (None, why). Created with O_EXCL, so two runs
    never both hold it; a stale lock is broken by one run only (break_lock) and taken over with a warning."""
    path = os.path.join(work, "lock.json")
    now = time.time()
    me = {"pid": os.getpid(), "started": now, "stamp": stamp(now), "max_timeout_s": max_timeout, "jobs": []}
    for _ in range(5):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            held = read_lock(path)
            if not held:
                continue  # its holder just removed it
            alive = pid_alive(held.get("pid"), held.get("started"))
            if lock_state(held, alive, time.time(), max_timeout) == "held":
                return None, ("another suite runs into this --out (pid %s, started %s): wait for it, or delete %s if "
                              "no suite runs" % (held.get("pid"), held.get("stamp") or "?", path))
            orphans = live_jobs(held, time.time(), max_timeout)
            if orphans:  # a SIGKILLed suite's jobs could still write into this run's outputs
                return None, ("suite pid %s (started %s) no longer runs, but jobs it started do: %s. Kill them with "
                              "everything they started (%s) or let them finish, then run again" % (
                                  held.get("pid"), held.get("stamp") or "?",
                                  ", ".join("pid %d (%s)" % o for o in orphans), kill_hint([o[0] for o in orphans])))
            why = break_lock(path, held, warnings)
            if why:
                return None, why
            continue
        except OSError as e:
            return None, "cannot create the lock %s: %s" % (path, e)
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump(me, fh)
        except BaseException as e:  # never leave a lock with no holder in it (a full disk, Ctrl-C)
            try:
                os.remove(path)
            except OSError:
                pass
            if not isinstance(e, OSError):
                raise
            return None, "cannot write the lock %s: %s" % (path, e)
        return dict(me, path=path), None
    return None, "cannot take the lock %s: other runs keep taking or breaking it" % path


def break_lock(path, held, warnings):
    """Remove the stale lock held (as read from path) unless it changed since. Only the run that creates
    <path>.break (O_EXCL) compares and removes, so two runs that find one stale lock never both remove it and then both
    hold the lock. A .break older than BREAK_STALE s is a dead breaker's and is removed. None, or why the run stops."""
    brk = path + ".break"
    try:
        os.close(os.open(brk, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:  # another run is breaking it: look again
        try:
            if time.time() - os.stat(brk).st_mtime > BREAK_STALE:
                os.remove(brk)
        except OSError:
            pass
        time.sleep(0.05)
        return None
    except OSError as e:
        return "cannot create %s: %s" % (brk, e)
    try:
        if read_lock(path) != held:
            return None  # another run took it over meanwhile
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as e:
            return "cannot remove the stale lock %s: %s" % (path, e)
        warnings.append("took over the lock of suite pid %s (started %s), which no longer runs, nor does any job it "
                        "recorded" % (held.get("pid"), held.get("stamp") or "?"))
        return None
    finally:
        try:
            os.remove(brk)
        except OSError:
            pass


def group_alive(pgid):
    """POSIX: True when no process has this pid but its process group still has members (a job's leader exited and
    left children running). The kernel never reuses a pid while a group of that id lives. False otherwise."""
    if os.name == "nt" or not isinstance(pgid, int) or isinstance(pgid, bool) or pgid <= 1:
        return False
    try:
        os.kill(pgid, 0)
        return False  # the pid exists: pid_alive decides (alive, or a reused pid whose group is long gone)
    except ProcessLookupError:
        pass
    except (OSError, OverflowError, ValueError):
        return False
    try:
        os.killpg(pgid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, OverflowError, ValueError):
        return False


def live_jobs(held, now, max_timeout):
    """[(pid, job)] of the jobs a dead holder's lock recorded that still run, by the rules for the holder: a process
    that started after the job did is a reused pid; unknown liveness counts until the lock's largest timeout + slack.
    A job whose leader exited counts while its process group still has members (group_alive)."""
    jobs = held.get("jobs") if isinstance(held.get("jobs"), list) else []
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)

    def alive(j):
        a = pid_alive(j["pid"], j["started"])
        return True if a is False and group_alive(j["pid"]) else a
    return [(j["pid"], str(j.get("job") or "?")) for j in jobs
            if isinstance(j, dict) and isinstance(j.get("pid"), int) and num(j.get("started"))
            and lock_state(dict(j, max_timeout_s=held.get("max_timeout_s")), alive(j), now, max_timeout) == "held"]


def kill_hint(pids, nt=os.name == "nt"):
    """The command that kills these jobs and everything they started (each job leads its own process group)."""
    if nt:
        return "taskkill /T /F" + "".join(" /PID %d" % p for p in pids)
    return "kill -TERM" + "".join(" -%d" % p for p in pids)


def record_jobs(lock):
    """Rewrite this run's lock.json with its running jobs (each one's pid, which leads its process group, and start),
    so a run that finds the lock of a SIGKILLed suite sees its orphans (take_lock). Atomic, and only while lock.json
    is still this run's: the O_EXCL create stays the only way to take it. Call it holding LOCK. None, or why not."""
    if not lock:
        return None
    held = load_dict(lock["path"])
    if held.get("pid") != lock["pid"] or held.get("started") != lock["started"]:
        return "%s is no longer this run's lock" % lock["path"]
    doc = dict((k, v) for k, v in lock.items() if k != "path")
    doc["jobs"] = [{"pid": j.proc.pid, "started": j.started, "job": j.key} for j in RUNNING.values()]
    try:
        write_atomic(lock["path"], json.dumps(doc))
    except OSError as e:
        return "cannot update %s: %s" % (lock["path"], e)
    return None


def move_aside(out, work):
    """Move the full run's suite.{json,md} to <out>/suite/superseded_suite.{json,md}, replacing older ones: a filtered
    run rewrites files that report describes. None, or why it could not (then nothing has moved)."""
    moved = []
    for e in (".json", ".md"):
        src, dst = os.path.join(out, "suite" + e), os.path.join(work, "superseded_suite" + e)
        try:
            if os.path.exists(src):
                os.replace(src, dst)
                moved.append((dst, src))
            elif os.path.exists(dst):  # an older pair's suite.md must not pass for this suite.json's
                os.remove(dst)
        except OSError as err:
            for d, s in moved:  # a refused run moves nothing
                try:
                    os.replace(d, s)
                except OSError:
                    pass
            return "cannot move %s aside: %s" % (src, err)
    return None


def drop_lock(lock):
    """Remove this run's lock, never another run's."""
    if not lock:
        return
    held = load_dict(lock["path"])
    if held.get("pid") == lock["pid"] and held.get("started") == lock["started"]:
        try:
            os.remove(lock["path"])
        except OSError:
            pass


def drop_report(out, configs, kinds):
    """Delete the report this run writes (suite.*, or suite_partial.* for a filtered run) before anything can refuse
    the run, so the last run's report is never read as its own. None, or why it could not be deleted."""
    kinds = {k.strip() for k in (kinds or ",".join(KINDS)).split(",") if k.strip()}
    for e in (".json", ".md"):
        p = os.path.join(out, ("suite" if configs is None and kinds == set(KINDS) else "suite_partial") + e)
        try:
            os.remove(p)
        except FileNotFoundError:
            pass
        except OSError as err:
            return "cannot delete %s: %s" % (p, err)
    return None


class Quiet(argparse.ArgumentParser):
    """A parser whose errors raise instead of printing and exiting (exit_on_error=False needs Python 3.9)."""

    def error(self, message):
        raise ValueError(message)


class Parser(argparse.ArgumentParser):
    """An argument refused here exits before main's own delete: delete the report first, then exit 2."""

    def error(self, message):
        pre = Quiet(add_help=False)
        for k in ("--out", "--configs", "--kinds"):
            pre.add_argument(k)
        pre.add_argument("--plan", action="store_true")
        try:
            a = pre.parse_known_args(self.argv)[0]
        except (ValueError, SystemExit):
            a = None
        if a is not None and a.out and not a.plan and os.path.isdir(a.out):
            err = drop_report(os.path.abspath(a.out), a.configs, a.kinds)
            if err:
                sys.stderr.write("suite error: %s\n" % err)
        super().error(message)


def main(argv=None):
    ap = Parser(description=__doc__.split("\n")[0])
    ap.argv = sys.argv[1:] if argv is None else argv
    ap.add_argument("suite", help="SUITE.json")
    ap.add_argument("--out", required=True, help="round folder: scorecards, wrong_builds, previews, suite.json")
    ap.add_argument("--jobs", type=int, help="workers (default $SUITE_JOBS, else by CPUs, RAM and the job count)")
    ap.add_argument("--beside-designer", action="store_true", help="a run beside a Designer build (stage 7's "
                    "targeted sets): at most half the CPUs")
    ap.add_argument("--timeout", type=float, help="seconds per job (default SUITE.json timeout, else 900)")
    ap.add_argument("--threads", type=int, default=2, help="BLAS/OpenMP threads per job (default 2)")
    ap.add_argument("--configs", help="comma-separated config stems or variants, cross-case groups or commands")
    ap.add_argument("--kinds", help="comma-separated: %s" % ",".join(KINDS))
    ap.add_argument("--plan", action="store_true", help="print the planned jobs as JSON and run nothing")
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    if not a.plan and os.path.isdir(out):  # a refused run must not leave the last run's report to be read as its own
        err = drop_report(out, a.configs, a.kinds)
        if err:
            print("suite error: %s" % err, file=sys.stderr)
            return 2
    try:
        if a.jobs is not None and a.jobs < 1:
            raise SuiteError("--jobs must be at least 1")
        if a.threads < 1:
            raise SuiteError("--threads must be at least 1")
        if a.timeout is not None and not a.timeout > 0:
            raise SuiteError("--timeout must be a positive number of seconds")
        if os.path.exists(out) and not os.path.isdir(out):
            raise SuiteError("--out %s is a file, not a folder" % out)
        env = env_for(a.threads)
        st = load_suite(a.suite, out, HERE)
        for s in ("matcheck.py", "wrong_builds.py", "previews.py"):
            if not os.path.isfile(os.path.join(HERE, s)):
                raise SuiteError("%s is missing next to suite.py" % s)
        jobs, info = plan(st, a, out, env)
        ram, job_gb = total_ram(), per_job_gb(info["px"])
        n_jobs = max(len([j for j in jobs if j.phase == 1]), len([j for j in jobs if j.phase == 2]))
        workers, rule = workers_for(os.cpu_count(), ram, job_gb, n_jobs, a.beside_designer,
                                    os.environ.get("SUITE_JOBS"), a.jobs)
    except SuiteError as e:
        print("suite error: %s" % e, file=sys.stderr)
        return 2
    work = os.path.join(out, "suite")
    for j in jobs:
        j.extra["out_dir"] = out
    machine = {"workers": workers, "workers_rule": rule, "threads": a.threads, "cpus": os.cpu_count(),
               "ram_gb": round(ram / 2.0 ** 30, 1) if ram else None, "per_job_gb": job_gb,
               "times_from": info["times_from"]}
    phase1 = sorted([j for j in jobs if j.phase == 1], key=lambda j: -j.expect)
    phase2 = [j for j in jobs if j.phase == 2]
    if a.plan:
        doc = dict({"full": info["full"]}, **machine)
        doc.update(jobs=[dict(job_dict(j), expect_s=round(j.expect, 2)) for j in phase1 + phase2],
                   uncovered=info["uncovered"], r6=info["r6"], skipped=st["skipped"], warnings=st["warnings"])
        print(json.dumps(doc, indent=1))
        return 0
    os.makedirs(work, exist_ok=True)
    lock, why = take_lock(work, max(j.timeout for j in jobs), st["warnings"])
    if lock is None:
        print("suite error: %s" % why, file=sys.stderr)
        return 2
    old = {}  # signal handlers to restore
    try:
        return run_suite(a, st, info, jobs, phase1, phase2, machine, env, out, work, lock, old)
    finally:
        drop_lock(lock)  # every exit path: normal, red, interrupt, a suite bug
        for sig, h in old.items():
            signal.signal(getattr(signal, sig), h)


def run_suite(a, st, info, jobs, phase1, phase2, machine, env, out, work, lock, old):
    """Delete before run, run both phases, write the times and the report; the exit code. main holds the lock."""
    base = "suite" if info["full"] else "suite_partial"
    doomed = [os.path.join(out, base + e) for e in (".json", ".md")]
    if info["full"]:
        doomed += [os.path.join(out, n) for n in ("wrong_builds.json", "wrong_builds.md", "views_index.md",
                                                  "compare_front.png", "compare_crop_raking.png")]
    for p in doomed:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass
        except OSError as e:
            print("suite error: cannot delete %s: %s" % (p, e), file=sys.stderr)
            return 2
    if not info["full"] and os.path.exists(os.path.join(out, "suite.json")):
        why = move_aside(out, work)
        if why:
            print("suite error: %s" % why, file=sys.stderr)
            return 2
        st["warnings"].append("moved the full run's suite.json aside: this folder no longer matches it; run the full "
                              "suite again")
    for j in jobs:
        extra = stale_previews(j, work, out) if j.kind == "previews" else []
        for p in j.outputs + extra + [j.log]:
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
            except OSError as e:
                j.red.append("cannot delete stale output %s: %s" % (p, e))
    t0, load0 = time.time(), load1()
    total, done = len(jobs), [0]
    print("suite: %d jobs (%d after), %d workers (%s) x %d threads, %s run, out %s" % (
        total, len(phase2), machine["workers"], machine["workers_rule"], a.threads,
        "full" if info["full"] else "partial", out))
    for w in st["warnings"]:
        print("warning: %s" % w)
    for r in info["r6"]:
        print("RED R6 coverage: %s" % r)
    sys.stdout.flush()

    def progress(job):
        with LOCK:
            done[0] += 1
            k = done[0]
        line = "[%d/%d] %s %s %s %s s" % (k, total, "RED" if job.red else "ok", job.kind, job.name,
                                         "%.1f" % job.seconds if job.seconds is not None else "-")
        print(line + (": %s" % job.red[0] if job.red else ""))
        sys.stdout.flush()

    caught = []
    ttys = [fd for fd in (1, 2) if os.isatty(fd)]

    def on_term(signum, frame):
        caught.append("Ctrl-C" if signum == signal.SIGINT else signal.Signals(signum).name)
        if signum == getattr(signal, "SIGHUP", None) and ttys:  # the terminal is gone: a print to it raises EIO
            null = os.open(os.devnull, os.O_WRONLY)
            for fd in ttys:
                os.dup2(null, fd)
            os.close(null)
        raise KeyboardInterrupt()

    for sig in ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGBREAK"):  # SIGHUP: a closed terminal
        if hasattr(signal, sig) and signal.getsignal(getattr(signal, sig)) != signal.SIG_IGN:  # nohup keeps its ignore
            try:
                old[sig] = signal.signal(getattr(signal, sig), on_term)
            except ValueError:  # not the main thread
                pass
    STOP.clear()
    interrupted = False
    pool = cf.ThreadPoolExecutor(max_workers=machine["workers"])
    submitted = []
    try:
        for phase in (phase1, phase2):
            todo = []
            for j in phase:
                if j.red:  # could not delete a stale output: never run it on top
                    progress(j)
                    continue
                if j.kind == "merge":
                    gone = [p.key for p in jobs if p.kind == "wrong_builds" and not os.path.exists(p.outputs[0])]
                    if gone:
                        j.red.append("not run: no wrong_builds.json from %s" % ", ".join(gone))
                elif j.kind == "assemble":
                    gone = [p.key for p in jobs if p.kind == "previews" and not os.path.exists(p.outputs[0])]
                    if gone:
                        j.red.append("not run: no part file from %s" % ", ".join(gone))
                if j.red:
                    progress(j)
                    continue
                todo.append(pool.submit(run_job, j, env, progress, lock))
            submitted += todo
            pending = set(todo)
            while pending:
                _, pending = cf.wait(pending, timeout=0.5)
    except KeyboardInterrupt:
        interrupted = True
        for sig in old:  # finish the cleanup and the report even on a second Ctrl-C
            signal.signal(getattr(signal, sig), signal.SIG_IGN)
        STOP.set()
        kill_all()
        print("suite: interrupted, killing every job", file=sys.stderr)
    finally:
        for f in submitted:  # queued jobs never start (shutdown's cancel_futures needs Python 3.9)
            f.cancel()
        pool.shutdown(wait=True)
        kill_all()
    for j in jobs:
        if not j.ran and not j.red:
            j.red.append("not run: the suite was interrupted" if interrupted else "not run")
    t1 = time.time()
    uncovered = dict(info["uncovered"])
    for j in jobs:
        for k, v in j.extra.get("uncovered", {}).items():
            uncovered[k] = sorted(set(uncovered.get(k, [])) | set(v))
    red = ([{"job": "R6 coverage", "reasons": info["r6"]}] if info["r6"] else []) + \
        [{"job": j.key, "reasons": j.red} for j in phase1 + phase2 if j.red]
    if interrupted:
        red.insert(0, {"job": "suite", "reasons": ["interrupted (%s): every job was killed"
                                                   % (caught[0] if caught else "Ctrl-C")]})
    rc = 1 if red else 0
    try:
        times = dict(info["times"])  # seeded with the times that ordered this run (last round's for a fresh --out)
        times.update((j.key, j.seconds) for j in jobs if j.seconds and not j.timed_out and not j.interrupted)
        write_atomic(os.path.join(work, "times.json"), json.dumps(times, indent=1, sort_keys=True))
        files = load_dict(os.path.join(work, "previews_files.json"))
        files.update((j.extra["variant"], j.extra["files"]) for j in jobs if j.extra.get("files"))
        write_atomic(os.path.join(work, "previews_files.json"), json.dumps(files, indent=1, sort_keys=True))
    except OSError as e:
        print("suite: warning: cannot write %s: %s" % (work, e), file=sys.stderr)
    doc = {"green": rc == 0, "rc": rc, "full": info["full"], "out": out, "suite": st["path"], "started": stamp(t0),
           "ended": stamp(t1), "wall_s": round(t1 - t0, 2)}
    doc.update(machine)
    doc.update({"load": [load0, load1()],
                "filter": None if info["full"] else {"configs": info["names"], "kinds": info["kinds"]},
                "jobs": [job_dict(j) for j in phase1 + phase2], "red": red, "uncovered": uncovered,
                "warnings": st["warnings"], "skipped": st["skipped"]})
    paths = write_reports(out, doc)
    drop_lock(lock)
    for sig, h in old.items():
        signal.signal(getattr(signal, sig), h)
    old.clear()
    print("\nsuite %s: %d jobs, %d red, wall %.1f s" % ("GREEN" if rc == 0 else "RED", total, len(red), t1 - t0))
    for r in red:
        print("RED %s:" % r["job"])
        for reason in r["reasons"]:
            print("  - %s" % reason)
    if uncovered:
        print("hard checks without a wrong-build case: %s" % json.dumps(uncovered))
    print("wrote %s and %s" % paths)
    return rc


if __name__ == "__main__":
    sys.exit(main())
