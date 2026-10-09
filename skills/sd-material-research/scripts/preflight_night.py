#!/usr/bin/env python3
"""Before an unattended night: check that Designer runs fresh plugin code and is not napping, that the Mac will stay
awake, and keep it awake with a detached caffeinate whose pid lives in RUN.json. Read-only except the caffeinate
commands and --wake. This docstring is the reference.

Usage:
    python preflight_night.py part1 --tools T [--designer-status ok|timeout|error|not_checked] [--plugin DIR] [--wake]
    python preflight_night.py part2 --tools T [--keep-awake-setting true|false|unknown]
    python preflight_night.py caffeinate start --tools T --until LOCAL_ISO [--extra-hours 3]
    python preflight_night.py caffeinate check --tools T [--extra-hours 3]
    python preflight_night.py caffeinate stop  --tools T

T is the material's tools folder. Files: T/review/preflight.json {"part1": {...}, "part2": {...}}, each subcommand
replaces only its own part (atomic write); T/RUN.json (through runstate.py, same folder as this script):
caffeinate_pid, caffeinate_until (local ISO, the end of the caffeinate, extra hours included), incidents [{utc, by, text}].
Subcommands:
    part1  Designer process and plugin freshness. macOS: `ps -axo pid=,pri=,lstart=,comm=`; the main process is the
           one whose comm ends with "/Adobe Substance 3D Designer" (helpers such as crashpad_handler are ignored);
           recorded: pid, pri, napping (pri 4), started (local and UTC), app. Windows: tasklist, running and pid
           only (pri and start time "unknown", so stale_plugin is null). Plugin: --plugin, else
           <repo>/designer_plugin/sd_claude_bridge if it exists (the repo is three folders above this script's
           folder), else ~/Documents/Allegorithmic/Substance Designer/python/sduserplugins/sd_claude_bridge; its
           newest *.py mtime (not __pycache__) with the file name. stale_plugin: Designer started before that
           mtime, so it runs old plugin code. --wake (macOS, only when napping): `open -a <app>` once, re-read pri,
           record woke. --designer-status is what the session saw from designer_status.
           Verdict: not_answering (Designer not running, or status timeout or error), restart_needed (stale_plugin),
           else green.
    part2  macOS only (elsewhere "unsupported", exit 0): pmset -g batt (AC or battery), pmset -g custom (sleep and
           displaysleep minutes per power source), ioreg AppleClamshellState (lid closed), free disk GB on the tools
           folder's volume, and the app's keep-awake setting as passed (never set here). Problems: not on AC, lid
           closed, free disk under 10 GB, keep-awake setting false. AC sleep above 0 is fine (caffeinate -s holds it).
    caffeinate start   macOS only. `caffeinate -i -s -t N` detached (new session, no stdio), N = until + extra hours
           - now, at least 60 s; sets caffeinate_pid and caffeinate_until. A live caffeinate already in RUN.json: nothing.
    caffeinate check   alive: the pid exists and its comm ends with "caffeinate". Dead, RUN.json mode "unattended"
           and the run's own end (caffeinate_until minus the extra hours) not yet passed: start a new one for the
           time left and append an incident. Prints alive, restarted or not needed. --extra-hours must match start.
    caffeinate stop    SIGTERM to a live caffeinate, then caffeinate_pid and caffeinate_until null (so check does
           not bring it back).
Exit code: part1 0 green, 1 restart_needed, 2 not_answering; part2 0 no problem, 1 a problem; caffeinate 0 ok, 1 a
needed caffeinate could not be started; 2 a usage or input error. Standard library only, Python 3.9 or newer; runs on
Windows (caffeinate and the macOS checks say so and exit 0).
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

if sys.version_info < (3, 9):
    sys.stderr.write("preflight_night.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.realpath(__file__))
MAC = sys.platform == "darwin"
WIN = sys.platform.startswith("win")
DESIGNER_COMM = "/Adobe Substance 3D Designer"
DESIGNER_EXE = "Adobe Substance 3D Designer.exe"
NAPPING_PRI = 4
MIN_FREE_GB = 10
PS_RE = re.compile(r"^\s*(\d+)\s+(-?\d+)\s+(\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4})\s+(.*\S)\s*$")


def utc(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def local_iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))


def sh(*cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return ""
    return p.stdout.decode("utf-8", "replace")


def die(msg):
    sys.stderr.write("preflight_night.py: %s\n" % msg)
    sys.exit(2)


def tools_dir(args):
    if not os.path.isdir(args.tools):
        die("--tools %s is not a folder" % args.tools)
    return os.path.abspath(args.tools)


def runstate_module():
    sys.path.insert(0, HERE)
    import runstate
    return runstate


# ---- parsers (canned text in the tests) ----

def parse_ps(text):
    """Rows {pid, pri, started (epoch, local lstart), comm} for every line of ps -axo pid=,pri=,lstart=,comm=."""
    rows = []
    for line in text.splitlines():
        m = PS_RE.match(line)
        if not m:
            continue
        started = time.mktime(time.strptime(re.sub(r"\s+", " ", m.group(3)), "%a %b %d %H:%M:%S %Y"))
        rows.append({"pid": int(m.group(1)), "pri": int(m.group(2)), "started": started, "comm": m.group(4)})
    return rows


def find_designer(rows):
    for r in rows:
        if r["comm"].endswith(DESIGNER_COMM):
            return r
    return None


def app_path(comm):
    i = comm.find(".app")
    return comm[:i + 4] if i >= 0 else comm


def parse_tasklist(text):
    for row in csv.reader(io.StringIO(text)):
        if len(row) >= 2 and row[0].lower() == DESIGNER_EXE.lower():
            return int(row[1])
    return None


def parse_batt(text):
    m = re.search(r"Now drawing from '([^']*)'", text)
    return {"on_ac": (m.group(1) == "AC Power") if m else None, "source": m.group(1) if m else None}


def parse_custom(text):
    """{"AC Power": {"sleep": n, "displaysleep": n}, "Battery Power": {...}} from pmset -g custom."""
    out, cur = {}, None
    for line in text.splitlines():
        h = re.match(r"^(\S.*):\s*$", line)
        if h:
            cur = out.setdefault(h.group(1), {})
            continue
        m = re.match(r"^\s+(sleep|displaysleep)\s+(\d+)", line)
        if m and cur is not None:
            cur[m.group(1)] = int(m.group(2))
    return out


def parse_clamshell(text):
    m = re.search(r'"AppleClamshellState"\s*=\s*(Yes|No)', text)
    return (m.group(1) == "Yes") if m else None


# ---- shared helpers ----

def write_part(tools, part, data):
    d = os.path.join(tools, "review")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "preflight.json")
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        doc = {}
    doc[part] = data
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    return path


def default_plugin():
    repo = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
    p = os.path.join(repo, "designer_plugin", "sd_claude_bridge")
    if os.path.isdir(p):
        return os.path.realpath(p)
    return os.path.realpath(os.path.join(os.path.expanduser("~"), "Documents", "Allegorithmic", "Substance Designer",
                                         "python", "sduserplugins", "sd_claude_bridge"))


def newest_mtime(folder):
    best = (None, None)
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in files:
            if n.endswith(".py"):
                full = os.path.join(root, n)
                try:
                    t = os.path.getmtime(full)
                except OSError:
                    continue
                if best[0] is None or t > best[0]:
                    best = (t, os.path.relpath(full, folder))
    return best


def read_designer():
    if MAC:
        r = find_designer(parse_ps(sh("ps", "-axo", "pid=,pri=,lstart=,comm=")))
        if not r:
            return {"running": False}
        return {"running": True, "pid": r["pid"], "pri": r["pri"], "napping": r["pri"] == NAPPING_PRI,
                "started_epoch": r["started"], "app": app_path(r["comm"])}
    if WIN:
        pid = parse_tasklist(sh("tasklist", "/FO", "CSV", "/NH"))
        if pid is None:
            return {"running": False}
        return {"running": True, "pid": pid, "pri": "unknown", "napping": None, "started_epoch": None, "app": None}
    return {"running": False}


# ---- part1 ----

def cmd_part1(args):
    tools = tools_dir(args)
    d = read_designer()
    woke = None
    if args.wake and d.get("napping") and d.get("app"):
        sh("open", "-a", d["app"])
        time.sleep(2)
        d2 = read_designer()
        if d2.get("running"):
            d["pri"], d["napping"] = d2["pri"], d2["napping"]
            woke = not d2["napping"]
        else:
            woke = False
    elif args.wake and not MAC:
        print("--wake is macOS only; nothing done")
    started = d.get("started_epoch")
    plugin_dir = os.path.realpath(args.plugin) if args.plugin else default_plugin()
    t, name = newest_mtime(plugin_dir) if os.path.isdir(plugin_dir) else (None, None)
    stale = (started < t) if (started is not None and t is not None) else None
    if not d["running"] or args.designer_status in ("timeout", "error"):
        verdict, code = "not_answering", 2
    elif stale:
        verdict, code = "restart_needed", 1
    else:
        verdict, code = "green", 0
    rec = {
        "checked_utc": utc(), "platform": sys.platform, "designer_status": args.designer_status,
        "running": d["running"], "pid": d.get("pid"), "pri": d.get("pri", "unknown"), "napping": d.get("napping"),
        "started_local": local_iso(started) if started else "unknown",
        "started_utc": utc(started) if started else "unknown", "app": d.get("app"), "woke": woke,
        "plugin": {"dir": plugin_dir, "newest_file": name, "newest_mtime_local": local_iso(t) if t else None,
                   "newest_mtime_utc": utc(t) if t else None},
        "stale_plugin": stale, "verdict": verdict,
    }
    path = write_part(tools, "part1", rec)
    if d["running"]:
        print("Designer: pid %s, pri %s%s, started %s" % (rec["pid"], rec["pri"], " (napping)" if rec["napping"] else "",
                                                          rec["started_local"]))
    else:
        print("Designer: not running")
    if woke is not None:
        print("wake: open -a done, now %s" % ("awake" if woke else "still napping"))
    print("designer_status: %s" % args.designer_status)
    print("plugin: %s" % plugin_dir)
    print("  newest %s at %s; stale_plugin: %s" % (name, rec["plugin"]["newest_mtime_local"], stale))
    print("verdict: %s (written to %s)" % (verdict, path))
    return code


# ---- part2 ----

def cmd_part2(args):
    tools = tools_dir(args)
    if not MAC:
        write_part(tools, "part2", {"checked_utc": utc(), "platform": sys.platform, "status": "unsupported"})
        print("part2 is macOS only (pmset, ioreg); recorded unsupported")
        return 0
    batt = parse_batt(sh("pmset", "-g", "batt"))
    custom = parse_custom(sh("pmset", "-g", "custom"))
    lid = parse_clamshell(sh("ioreg", "-r", "-k", "AppleClamshellState", "-d", "4"))
    free_gb = round(shutil.disk_usage(tools).free / 1e9, 1)
    problems, notes = [], []
    if batt["on_ac"] is False:
        problems.append("not on AC power (%s)" % batt["source"])
    if lid:
        problems.append("lid is closed")
    if free_gb < MIN_FREE_GB:
        problems.append("free disk %.1f GB is under %d GB" % (free_gb, MIN_FREE_GB))
    if args.keep_awake_setting == "false":
        problems.append("the app's keep-awake setting is false")
    ac_sleep = custom.get("AC Power", {}).get("sleep")
    if ac_sleep:
        notes.append("AC sleep is %d min; caffeinate -s holds it" % ac_sleep)
    rec = {"checked_utc": utc(), "platform": sys.platform, "status": "checked", "on_ac": batt["on_ac"],
           "power_source": batt["source"], "pmset_custom": custom, "lid_closed": lid, "free_disk_gb": free_gb,
           "keep_awake_setting": args.keep_awake_setting, "problems": problems, "notes": notes}
    path = write_part(tools, "part2", rec)
    print("power: %s; lid closed: %s; free disk: %.1f GB; keep-awake setting: %s"
          % (batt["source"], lid, free_gb, args.keep_awake_setting))
    for k, v in custom.items():
        print("  %s: %s" % (k, ", ".join("%s %s" % kv for kv in sorted(v.items()))))
    for n in notes:
        print("note: " + n)
    for p in problems:
        print("PROBLEM: " + p)
    print("%s (written to %s)" % ("problems found" if problems else "no problem", path))
    return 1 if problems else 0


# ---- caffeinate ----

def caff_alive(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        return False
    out = sh("ps", "-p", str(int(pid)), "-o", "stat=,comm=").split(None, 1)
    return len(out) == 2 and not out[0].startswith("Z") and out[1].strip().endswith("caffeinate")


def parse_local(s):
    try:
        return datetime.datetime.fromisoformat(s).timestamp()
    except ValueError:
        die("--until %r is not a local ISO time like 2026-10-09T07:30:00" % s)


def spawn_caffeinate(seconds):
    p = subprocess.Popen(["caffeinate", "-i", "-s", "-t", str(seconds)], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.pid


def start_for(tools, rs, seconds):
    pid = spawn_caffeinate(seconds)
    end = time.time() + seconds

    def mutate(d):
        d["caffeinate_pid"] = pid
        d["caffeinate_until"] = local_iso(end)
    rs.update(tools, mutate)
    return pid, end


def cmd_caffeinate(args):
    tools = tools_dir(args)
    if not MAC:
        print("caffeinate is macOS only; nothing done")
        return 0
    rs = runstate_module()
    run = rs.load(tools)
    pid = run.get("caffeinate_pid")
    alive = caff_alive(pid)
    if args.action == "start":
        if alive:
            print("caffeinate already running, pid %s until %s; nothing done" % (pid, run.get("caffeinate_until")))
            return 0
        seconds = max(60, int(parse_local(args.until) + args.extra_hours * 3600 - time.time()))
        pid, end = start_for(tools, rs, seconds)
        print("caffeinate started: pid %d for %d s, until %s" % (pid, seconds, local_iso(end)))
        return 0
    if args.action == "stop":
        if alive:
            os.kill(int(pid), signal.SIGTERM)
            for _ in range(20):
                if not caff_alive(pid):
                    break
                time.sleep(0.1)
            print("caffeinate pid %s stopped" % pid)
        else:
            print("no live caffeinate (pid %s); cleared" % pid)

        def mutate(d):
            d["caffeinate_pid"] = None
            d["caffeinate_until"] = None
        rs.update(tools, mutate)
        return 0
    if alive:
        print("alive: pid %s until %s" % (pid, run.get("caffeinate_until")))
        return 0
    until = run.get("caffeinate_until")
    if run.get("mode") != "unattended" or not until:
        print("not needed (caffeinate dead or never started; mode %s)" % run.get("mode"))
        return 0
    end = parse_local(until)
    if end - args.extra_hours * 3600 <= time.time():
        print("not needed (the run's end has passed)")
        return 0
    seconds = max(60, int(end - time.time()))
    try:
        new, _ = start_for(tools, rs, seconds)
    except OSError as e:
        print("restart failed: %s" % e)
        return 1

    def mutate(d):
        d.setdefault("incidents", []).append({"utc": utc(), "by": "preflight",
                                              "text": "caffeinate pid %s was dead; restarted as pid %d for %d s" % (pid, new, seconds)})
    rs.update(tools, mutate)
    print("restarted: pid %s was dead, new pid %d for %d s" % (pid, new, seconds))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="preflight_night.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("part1")
    p1.add_argument("--tools", required=True)
    p1.add_argument("--designer-status", choices=("ok", "timeout", "error", "not_checked"), default="not_checked")
    p1.add_argument("--plugin")
    p1.add_argument("--wake", action="store_true")
    p1.set_defaults(fn=cmd_part1)
    p2 = sub.add_parser("part2")
    p2.add_argument("--tools", required=True)
    p2.add_argument("--keep-awake-setting", choices=("true", "false", "unknown"), default="unknown")
    p2.set_defaults(fn=cmd_part2)
    pc = sub.add_parser("caffeinate")
    pc.add_argument("action", choices=("start", "check", "stop"))
    pc.add_argument("--tools", required=True)
    pc.add_argument("--until")
    pc.add_argument("--extra-hours", type=float, default=3)
    pc.set_defaults(fn=cmd_caffeinate)
    args = ap.parse_args(argv)
    if args.cmd == "caffeinate" and args.action == "start" and not args.until:
        ap.error("caffeinate start needs --until")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
