#!/usr/bin/env python3
"""Get Designer back when it stops answering during an unattended run: say whether a relaunch would work at night
(check), and do the one relaunch the run is allowed (relaunch). Designer here is a Steam install: a launch is handed to
Steam, and Steam can stop at a dialog that needs a click, so a relaunch is only worth doing when no such dialog is in
the way. This docstring is the reference.

Usage:
    python designer_relaunch.py check    [--tools T] [--steam-log FILE] [--session FILE]
    python designer_relaunch.py relaunch --tools T [--wait-min 30] [--package P] [--job J [--golden DIR --out DIR]]
                                         [--app PATH] [--steam-log FILE] [--session FILE] [--force]

T is the material's tools folder. --session is the bridge's session file (default: $SD_CLAUDE_BRIDGE_SESSION, else
~/.sd_claude_bridge/session.json; {port, token, pid, started}; the token is never printed). --steam-log defaults to
~/Library/Application Support/Steam/logs/console_log.txt (macOS) or %ProgramFiles(x86)%\\Steam\\logs\\console_log.txt
(Windows); its last 4 MB are read. Log timestamps are local time without a zone ("[YYYY-MM-DD HH:MM:SS] ...").

check   Read-only, no side effects (a ping, a process listing and, on macOS, one `sample`). Prints one JSON object:
    utc, platform;
    process     {pid, pri, napping (macOS pri 4), app} for the Designer process (as preflight_night.py finds it: macOS
                `ps`, the main process only; Windows tasklist, pri "unknown", napping null), or null;
    bridge      {answers, ms, session_pid, matches}: a ping of the session file's port; matches is session_pid equal to
                the process pid;
    modal_hints only when a process exists and the bridge does not answer, on macOS: `sample <pid> 2 -file <tmp>` and the
                count of lines matching runModal|QDialog::exec|NSAlert|QMessageBox|modalSession (a modal dialog inside
                Designer stops the bridge); else null (also null when sample failed);
    steam       {running (steam_osx or steam.exe is a process), log (path), log_found, app_id, last_launch};
                app_id comes from the last 'Game process added : AppID <n> "...Substance 3D Designer..."' line, else from
                a 'GameAction [AppID <n>' line within 5 s after a steam://run/<n> line, else null; last_launch is the last
                launch of that app, {action_id, started_local, dialogs, pending}, or null. A launch is the run of
                'GameAction [AppID n, ActionID k] : LaunchApp ...' lines of one ActionID. Its dialogs are the lines
                'waiting for user response to <Task> "<reason>"' with a non-empty reason, each
                {local, task, reason, answered, response, wait_s}: answered by the next 'continues with user response'
                line (wait_s the seconds between the two, null while pending). A wait with an empty reason
                (ShowInterstitials "", CreatingProcess "") is Steam's own step, not a dialog, and is not listed.
                pending: a dialog with no continue line;
    relaunch_safe  false when the last launch had a dialog (it waits for a click: answered by a person, or still
                pending; the same "syncfailed" dialog was answered in 1 s by the person launching at 2026-10-06 19:07 and
                stayed pending, unanswered, at 2026-10-09 00:25); true when it had none; null when there is no Steam log
                or no launch of the app in it; true whatever the log says when the app path is known and not under a
                Steam folder (a "steamapps" or "Steam" folder in its path);
    advice      one line, e.g. 'the last Designer launch waited 3 s for a click on Steam's
                "SynchronizingControllerConfig syncfailed" dialog: a relaunch at night would stop there' or 'the last
                Steam launch needed no click'.
    The app is the process's, else <T>/review/preflight.json part1.app when --tools is given.
    Exit 0 when the bridge answers, 1 when it does not, 2 usage.

relaunch   The skill allows ONE relaunch per run. Steps:
    0. Refuse (exit 4, prints {"action": "refused", "reason": ...}) when <T>/review/relaunch.json (a JSON list of
       attempts) already holds an attempt whose action is not "none" and whose utc_start is at or after RUN.json go_utc
       (any such attempt when go_utc is missing or unparseable), unless --force. A refusal writes nothing.
    1. Run check. The bridge answers and no --force: record action "none", exit 0. --force goes on.
    2. Find the app: the process's app, else --app, else <T>/review/preflight.json part1.app; none: action
       "failed_no_app", exit 3 (this is decided before the kill, so a Designer that cannot be started again is not killed).
       Kill the process if one exists: SIGTERM, wait up to 20 s, then SIGKILL, wait up to 10 s (Windows: taskkill /PID,
       then /F). killed is "term", "kill" or "none"; a process that survives SIGKILL: action "failed_kill", exit 3.
    3. T = now. Launch: macOS `open -a <app>`; Windows os.startfile(<exe>). A launch that fails: action "failed_launch".
    4. Poll every 10 s for up to --wait-min minutes (default 30), in this order:
       a. Steam: take the last launch of the app (any app when its id is unknown). A dialog with a non-empty reason and
          no continue line for 30 s after it, in a launch that started at or after T - 2 s: stop with action
          "blocked_steam_dialog", dialog {task, reason, local}. A dialog that was already pending in the last launch
          before T - 2 s counts the same 30 s after T while Steam is running (the Steam launch from the earlier try is
          still stopped there).
       b. A Designer process whose pid differs from the killed one, session.json pid equal to it, and a ping that
          answers: action "relaunched", seconds_to_bridge (seconds since T).
       c. That new process alive for more than 5 min without the bridge answering: on macOS `sample` it once; modal hints
          above 0: stop with action "blocked_designer_modal".
       d. At the end of the wait: "failed_no_process" (no new process was seen) or "failed_no_bridge".
    5. On "relaunched": --package P is reopened through the bridge with run_python (a loaded user package with that file
       path, compared by normcase and abspath, is left alone, else app.getPackageMgr().loadUserPackage(P); up to 3 tries
       10 s apart) -> package_reopened true or false. --job J runs `python sdcall.py J --timeout 900` (sdcall.py from this
       folder; --session is passed on when given) -> job_rc; with --golden G and --out O every *.png in G is compared byte
       for byte with the same name in O -> diff {same: n, changed: [names], missing: [names]}.
    6. Append the attempt {utc_start, utc_end, action, reason, old_pid, new_pid, killed, seconds_to_bridge,
       steam_running, dialog, modal_hints, package_reopened, job_rc, diff, app, forced} to <T>/review/relaunch.json
       (the list is created; atomic write) and, when <T>/RUN.json exists, an incident {utc, by: "relaunch", text:
       "relaunch: <action>; <details>"} through runstate.update(). Prints the attempt as JSON.
    Exit 0 relaunched (and, when asked, the package reopened, job_rc 0, nothing changed or missing) or action "none"; 1
    relaunched but the package did not reopen, the job failed or the export differs; 3 blocked or failed; 4 refused;
    2 usage.

Side effects (processes, kill, launch, ping, run_python, sample, clock, sleep, the job) all go through the Env class, so a
test drives the loop with a fake Env and a fake clock: main(argv, env=FakeEnv()). Module API: parse_steam_log(text),
launch_blocks(launch), main(argv, env=None). Standard library only, Python 3.9 or newer; os.path and UTF-8 throughout, so
it runs on Windows.
"""
import argparse
import calendar
import csv
import filecmp
import io
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time

if sys.version_info < (3, 9):
    sys.stderr.write("designer_relaunch.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import preflight_night as pf  # noqa: E402  process finding, utc(), the preflight.json layout
import runstate  # noqa: E402  RUN.json load/update

MAC = sys.platform == "darwin"
WIN = sys.platform.startswith("win")
POLL_S = 10
TERM_WAIT_S = 20
KILL_WAIT_S = 10
DIALOG_WAIT_S = 30
MODAL_AFTER_S = 300
LOG_TAIL_BYTES = 4000000
MODAL_RE = re.compile(r"runModal|QDialog::exec|NSAlert|QMessageBox|modalSession")
LINE_RE = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] (.*)$")
GA_RE = re.compile(r"^GameAction \[AppID (\d+), ActionID (\d+)\] : LaunchApp (.*)$")
ADDED_RE = re.compile(r'^Game process added : AppID (\d+) "(.*)"')
URL_RE = re.compile(r'^ExecuteSteamURL: "steam://run/(\d+)"')
TASK_RE = re.compile(r'^changed task to (\w+) with "(.*)"$')
WAIT_RE = re.compile(r'^waiting for user response to (\w+) "(.*)"$')
CONT_RE = re.compile(r'^continues with user response "(.*)"$')
UTC_FMT = "%Y-%m-%dT%H:%M:%SZ"


def die(msg):
    sys.stderr.write("designer_relaunch.py: %s\n" % msg)
    sys.exit(2)


def note(msg):
    sys.stderr.write("designer_relaunch.py: %s\n" % msg)
    sys.stderr.flush()


def show(obj):
    print(json.dumps(obj, indent=2, sort_keys=False))


def local_iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))


# ---- the side effects (replaced by a fake in the tests) ----

class Env(object):
    platform = sys.platform
    can_sample = MAC

    def now(self):
        return time.time()

    def sleep(self, seconds):
        time.sleep(seconds)

    def designer(self):
        """{pid, pri, napping, app} of the Designer main process, or None."""
        d = pf.read_designer()
        if not d.get("running"):
            return None
        app = d.get("app")
        if app is None and WIN:
            out = pf.sh("powershell", "-NoProfile", "-Command",
                        "(Get-CimInstance Win32_Process -Filter 'ProcessId=%d').ExecutablePath" % d["pid"]).strip()
            app = out or None
        return {"pid": d["pid"], "pri": d.get("pri"), "napping": d.get("napping"), "app": app}

    def steam_running(self):
        if MAC:
            return any(os.path.basename(ln.strip()) == "steam_osx" for ln in pf.sh("ps", "-axo", "comm=").splitlines())
        if WIN:
            for row in csv.reader(io.StringIO(pf.sh("tasklist", "/FO", "CSV", "/NH"))):
                if row and row[0].lower() == "steam.exe":
                    return True
        return False

    def alive(self, pid):
        d = self.designer()
        return bool(d and d["pid"] == pid)

    def kill(self, pid, force):
        if WIN:
            cmd = ["taskkill", "/PID", str(pid)] + (["/F"] if force else [])
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            return
        try:
            os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
        except OSError:
            pass

    def launch(self, app):
        if WIN:
            os.startfile(app)  # noqa: pylint (Windows only)
            return
        p = subprocess.run(["open", "-a", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        if p.returncode != 0:
            raise OSError("open -a exited with %d" % p.returncode)

    def session(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return None
        return d if isinstance(d, dict) else None

    def _talk(self, path, cmd, args, timeout):
        s = self.session(path)
        if not s:
            return None
        req = {"id": int(time.time()), "token": s.get("token"), "cmd": cmd, "args": args}
        try:
            k = socket.create_connection(("127.0.0.1", int(s["port"])), timeout=5)
            try:
                k.settimeout(timeout)
                k.sendall((json.dumps(req) + "\n").encode("utf-8"))
                buf = b""
                while b"\n" not in buf:
                    chunk = k.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
            finally:
                k.close()
            if b"\n" not in buf:
                return None
            reply = json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return reply if isinstance(reply, dict) else None

    def ping(self, path):
        """(answers, ms)."""
        t0 = time.time()
        reply = self._talk(path, "ping", {}, 5)
        ok = bool(reply and reply.get("ok") and isinstance(reply.get("result"), dict) and reply["result"].get("pong"))
        return ok, (int(round((time.time() - t0) * 1000)) if ok else None)

    def run_python(self, path, code):
        return self._talk(path, "run_python", {"code": code}, 120)

    def sample(self, pid):
        """Number of modal-dialog frames in a 2 s `sample` of the process, or None when sample did not work."""
        fd, tmp = tempfile.mkstemp(prefix="designer_sample_", suffix=".txt")
        os.close(fd)
        try:
            p = subprocess.run(["sample", str(pid), "2", "-file", tmp], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=90)
            if p.returncode != 0:
                return None
            with open(tmp, encoding="utf-8", errors="replace") as f:
                text = f.read()
            return sum(1 for ln in text.splitlines() if MODAL_RE.search(ln)) if text.strip() else None
        except (OSError, subprocess.SubprocessError):
            return None
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def default_steam_log(self):
        if WIN:
            base = os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)"
            return os.path.join(base, "Steam", "logs", "console_log.txt")
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Steam", "logs", "console_log.txt")

    def read_tail(self, path):
        """The last LOG_TAIL_BYTES of a text file (whole lines), or None when it cannot be read."""
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(max(0, size - LOG_TAIL_BYTES))
                data = f.read()
        except OSError:
            return None
        text = data.decode("utf-8", "replace")
        if size > LOG_TAIL_BYTES and "\n" in text:
            text = text.split("\n", 1)[1]
        return text

    def run_job(self, cmd, timeout):
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            return -1
        sys.stderr.write(p.stdout.decode("utf-8", "replace")[-4000:])
        return p.returncode


# ---- Steam console log ----

def _epoch(ts):
    return time.mktime(time.strptime(ts, "%Y-%m-%d %H:%M:%S"))


def parse_steam_log(text):
    """{"app_id": int or None, "launches": [launch, ...]} from console_log.txt text. A launch is {app_id, action_id,
    started_local, dialogs, pending, _epoch, _task}; a dialog {local, task, reason, answered, response, wait_s, _epoch}
    (keys with an underscore are for the callers in this file). Only waits with a non-empty reason are dialogs."""
    launches, live = [], {}  # live: (app, action) -> its launch, so another app's lines in between do not split one
    added_id, urls = None, []
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        ts, rest = m.group(1), m.group(2)
        try:
            ep = _epoch(ts)
        except (ValueError, OverflowError):
            continue
        a = ADDED_RE.match(rest)
        if a and "Substance 3D Designer" in a.group(2):
            added_id = int(a.group(1))
            continue
        u = URL_RE.match(rest)
        if u:
            urls.append((ep, int(u.group(1))))
            continue
        g = GA_RE.match(rest)
        if not g:
            continue
        key = (int(g.group(1)), int(g.group(2)))
        body = g.group(3)
        t = TASK_RE.match(body)
        cur = live.get(key)
        restart = bool(t and t.group(1) == "RunningInstallScript" and cur is not None and cur["_seen_start"])
        if cur is None or restart:
            cur = {"app_id": key[0], "action_id": key[1], "started_local": local_iso(ep), "dialogs": [],
                   "pending": False, "_epoch": ep, "_key": key, "_seen_start": False, "_open": None}
            launches.append(cur)
            live[key] = cur
        if t and t.group(1) == "RunningInstallScript":
            cur["_seen_start"] = True
        w = WAIT_RE.match(body)
        if w:
            if w.group(2):
                dlg = {"local": local_iso(ep), "task": w.group(1), "reason": w.group(2), "answered": False,
                       "response": None, "wait_s": None, "_epoch": ep}
                cur["dialogs"].append(dlg)
                cur["_open"] = dlg
                cur["pending"] = True
            else:
                cur["_open"] = None
            continue
        c = CONT_RE.match(body)
        if c and cur["_open"] is not None:
            dlg = cur["_open"]
            dlg["answered"], dlg["response"] = True, c.group(1)
            dlg["wait_s"] = int(round(ep - dlg["_epoch"]))
            cur["pending"] = any(not d["answered"] for d in cur["dialogs"])
            cur["_open"] = None
    app_id = added_id
    if app_id is None:
        for ep, n in reversed(urls):
            if any(l["app_id"] == n and 0 <= l["_epoch"] - ep <= 5 for l in launches):
                app_id = n
                break
    return {"app_id": app_id, "launches": launches}


def dialog_blocks(dlg):
    """A dialog with a reason waits for a click, however fast the click came, so it blocks a night run."""
    return bool(dlg["reason"])


def launch_blocks(launch):
    return any(dialog_blocks(d) for d in launch["dialogs"])


def public_dialog(d):
    return {k: d[k] for k in ("local", "task", "reason", "answered", "response", "wait_s")}


def public_launch(l):
    return {"action_id": l["action_id"], "started_local": l["started_local"],
            "dialogs": [public_dialog(d) for d in l["dialogs"]], "pending": l["pending"]}


def last_launch_of(parsed, app_id):
    mine = [l for l in parsed["launches"] if app_id is None or l["app_id"] == app_id]
    return mine[-1] if mine else None


def under_steam(path):
    parts = [p.lower() for p in re.split(r"[\\/]+", path or "")]
    return "steamapps" in parts or "steam" in parts


def advice_line(app, parsed_ok, launch, safe):
    if safe is True and app and not under_steam(app):
        return "Designer is not under a Steam folder: no Steam dialog to expect"
    if not parsed_ok:
        return "no Steam log to read: whether a relaunch would stop at a Steam dialog is unknown"
    if launch is None:
        return "the Steam log has no launch of Designer: whether a relaunch would stop at a Steam dialog is unknown"
    bad = [d for d in launch["dialogs"] if dialog_blocks(d)]
    if not bad:
        return "the last Steam launch needed no click"
    d = next((x for x in bad if not x["answered"]), bad[0])
    what = 'Steam\'s "%s %s" dialog' % (d["task"], d["reason"])
    if not d["answered"]:
        return ("the last Designer launch (%s) is stopped at %s with no answer yet: a relaunch at night would stop there"
                % (launch["started_local"], what))
    return ("the last Designer launch waited %d s for a click on %s: a relaunch at night would stop there"
            % (d["wait_s"], what))


# ---- check ----

def read_preflight_app(tools):
    if not tools:
        return None
    try:
        with open(os.path.join(tools, "review", "preflight.json"), encoding="utf-8") as f:
            return (json.load(f).get("part1") or {}).get("app") or None
    except (OSError, ValueError, AttributeError):
        return None


def run_check(env, tools, steam_log, session):
    proc = env.designer()
    answers, ms = env.ping(session)
    sess = env.session(session) or {}
    spid = sess.get("pid") if isinstance(sess.get("pid"), int) else None
    hints = None
    if proc and not answers and env.can_sample:
        hints = env.sample(proc["pid"])
    log_path = steam_log or env.default_steam_log()
    text = env.read_tail(log_path)
    parsed = parse_steam_log(text) if text is not None else {"app_id": None, "launches": []}
    app = (proc or {}).get("app") or read_preflight_app(tools)
    launch = last_launch_of(parsed, parsed["app_id"]) if parsed["app_id"] is not None else None
    if app and not under_steam(app):
        safe = True
    elif launch is None:
        safe = None
    else:
        safe = not launch_blocks(launch)
    return {
        "utc": pf.utc(env.now()), "platform": env.platform,
        "process": ({"pid": proc["pid"], "pri": proc["pri"], "napping": proc["napping"], "app": proc["app"]}
                    if proc else None),
        "bridge": {"answers": answers, "ms": ms, "session_pid": spid,
                   "matches": bool(proc and spid is not None and spid == proc["pid"])},
        "modal_hints": hints,
        "steam": {"running": env.steam_running(), "log": log_path, "log_found": text is not None,
                  "app_id": parsed["app_id"], "last_launch": public_launch(launch) if launch else None},
        "relaunch_safe": safe,
        "advice": advice_line(app, text is not None, launch, safe),
    }, parsed


def cmd_check(a, env):
    tools = os.path.abspath(a.tools) if a.tools else None
    if tools and not os.path.isdir(tools):
        die("--tools %s is not a folder" % a.tools)
    out, _ = run_check(env, tools, a.steam_log, a.session)
    show(out)
    return 0 if out["bridge"]["answers"] else 1


# ---- relaunch ----

def parse_utc(s):
    try:
        return calendar.timegm(time.strptime(s, UTC_FMT))
    except (ValueError, TypeError):
        return None


def read_attempts(tools):
    path = os.path.join(tools, "review", "relaunch.json")
    if not os.path.exists(path):
        return path, []
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
    except (OSError, ValueError):
        rows = None
    if not isinstance(rows, list):
        die("%s is not a JSON list" % path)
    return path, rows


def prior_attempt(rows, go_utc):
    """The first earlier attempt that used up the run's relaunch, or None."""
    go = parse_utc(go_utc) if go_utc else None
    for r in rows:
        if not isinstance(r, dict) or r.get("action") == "none":
            continue
        t = parse_utc(r.get("utc_start") or r.get("utc"))
        if go is None or t is None or t >= go:
            return r
    return None


def write_attempts(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def wait_gone(env, pid, limit):
    end = env.now() + limit
    while True:
        if not env.alive(pid):
            return True
        if env.now() >= end:
            return False
        env.sleep(1)


def steam_blocker(parsed, app_id, t0, now, steam_up):
    """The dialog that has held the launch for 30 s (see the docstring, step 4a), or None."""
    launch = last_launch_of(parsed, app_id)
    if launch is None:
        return None
    fresh = launch["_epoch"] >= t0 - 2
    for d in launch["dialogs"]:
        if d["answered"]:
            continue
        if fresh:
            since = d["_epoch"]
        elif steam_up:
            since = t0
        else:
            continue
        if now - since >= DIALOG_WAIT_S:
            return {"task": d["task"], "reason": d["reason"], "local": d["local"]}
    return None


def reopen_code(path):
    return (
        "import os\n"
        "want = os.path.normcase(os.path.abspath(%r))\n"
        "def _items(x):\n"
        "    try:\n"
        "        return list(x)\n"
        "    except TypeError:\n"
        "        return [x.getItem(i) for i in range(x.getSize())]\n"
        "def _have():\n"
        "    for p in _items(pkg_mgr.getUserPackages()):\n"
        "        fp = p.getFilePath()\n"
        "        if fp and os.path.normcase(os.path.abspath(fp)) == want:\n"
        "            return True\n"
        "    return False\n"
        "already = _have()\n"
        "if not already:\n"
        "    pkg_mgr.loadUserPackage(%r)\n"
        "result = {'loaded': _have(), 'already': already}\n" % (path, path))


def reopen_package(env, session, path):
    for i in range(3):
        reply = env.run_python(session, reopen_code(path))
        res = (reply or {}).get("result") if reply and reply.get("ok") else None
        if isinstance(res, dict) and not res.get("error") and isinstance(res.get("result"), dict) \
                and res["result"].get("loaded"):
            return True
        if i < 2:
            env.sleep(POLL_S)
    return False


def png_diff(golden, out):
    same, changed, missing = 0, [], []
    for n in sorted(os.listdir(golden)):
        if not n.lower().endswith(".png") or not os.path.isfile(os.path.join(golden, n)):
            continue
        o = os.path.join(out, n)
        if not os.path.isfile(o):
            missing.append(n)
        elif filecmp.cmp(os.path.join(golden, n), o, shallow=False):
            same += 1
        else:
            changed.append(n)
    return {"same": same, "changed": changed, "missing": missing}


def details(att):
    bits = []
    if att["old_pid"] is not None or att["new_pid"] is not None:
        bits.append("pid %s -> %s" % (att["old_pid"], att["new_pid"]))
    if att["seconds_to_bridge"] is not None:
        bits.append("bridge after %s s" % att["seconds_to_bridge"])
    if att["dialog"]:
        bits.append('Steam dialog %s "%s"' % (att["dialog"]["task"], att["dialog"]["reason"]))
    if att["modal_hints"]:
        bits.append("%d modal hints" % att["modal_hints"])
    if att["package_reopened"] is not None:
        bits.append("package reopened %s" % str(att["package_reopened"]).lower())
    if att["job_rc"] is not None:
        bits.append("job_rc %s" % att["job_rc"])
    if att["diff"]:
        bits.append("export: %d same, %d changed, %d missing"
                    % (att["diff"]["same"], len(att["diff"]["changed"]), len(att["diff"]["missing"])))
    return ", ".join(bits) or att["reason"]


def finish(env, tools, att, code, rows, path):
    att["utc_end"] = pf.utc(env.now())
    rows.append(att)
    write_attempts(path, rows)
    if os.path.exists(os.path.join(tools, "RUN.json")):
        def mutate(d):
            if not isinstance(d.get("incidents"), list):
                d["incidents"] = []
            d["incidents"].append({"utc": att["utc_end"], "by": "relaunch",
                                   "text": "relaunch: %s; %s" % (att["action"], details(att))})
        runstate.update(tools, mutate)
    show(att)
    return code


def cmd_relaunch(a, env):
    tools = os.path.abspath(a.tools)
    if not os.path.isdir(tools):
        die("--tools %s is not a folder" % a.tools)
    if a.golden or a.out:
        if not (a.job and a.golden and a.out):
            die("--golden and --out go together and need --job")
        if not os.path.isdir(a.golden):
            die("--golden %s is not a folder" % a.golden)
    if a.job and not os.path.isfile(a.job):
        die("--job %s is not a file" % a.job)
    if a.package and not os.path.isfile(a.package):
        die("--package %s is not a file" % a.package)
    if a.wait_min <= 0:
        die("--wait-min must be positive")
    path, rows = read_attempts(tools)
    if not a.force:
        prev = prior_attempt(rows, runstate.load(tools).get("go_utc"))
        if prev is not None:
            show({"action": "refused", "reason": "this run already used its relaunch (%s at %s); --force overrides"
                  % (prev.get("action"), prev.get("utc_start") or prev.get("utc")), "previous": prev})
            return 4
    t_start = env.now()
    att = {"utc_start": pf.utc(t_start), "utc_end": None, "action": None, "reason": None, "old_pid": None,
           "new_pid": None, "killed": "none", "seconds_to_bridge": None, "steam_running": None, "dialog": None,
           "modal_hints": None, "package_reopened": None, "job_rc": None, "diff": None, "app": None,
           "forced": bool(a.force)}
    chk, _ = run_check(env, tools, a.steam_log, a.session)
    proc = chk["process"]
    att["old_pid"] = proc["pid"] if proc else None
    att["modal_hints"] = chk["modal_hints"]
    if chk["bridge"]["answers"] and not a.force:
        att.update(action="none", reason="the bridge answers; nothing to do", steam_running=chk["steam"]["running"])
        return finish(env, tools, att, 0, rows, path)
    app = (proc or {}).get("app") or a.app or read_preflight_app(tools)
    att["app"] = app
    if not app:
        att.update(action="failed_no_app", reason="no app path: no Designer process, no --app, no preflight.json part1.app",
                   steam_running=chk["steam"]["running"])
        return finish(env, tools, att, 3, rows, path)
    if proc:
        env.kill(proc["pid"], False)
        if wait_gone(env, proc["pid"], TERM_WAIT_S):
            att["killed"] = "term"
        else:
            env.kill(proc["pid"], True)
            if wait_gone(env, proc["pid"], KILL_WAIT_S):
                att["killed"] = "kill"
            else:
                att.update(killed="failed", action="failed_kill", steam_running=env.steam_running(),
                           reason="Designer pid %d survived SIGTERM and SIGKILL" % proc["pid"])
                return finish(env, tools, att, 3, rows, path)
    t0 = env.now()
    try:
        env.launch(app)
    except OSError as e:
        att.update(action="failed_launch", reason="could not launch %s: %s" % (app, e), steam_running=env.steam_running())
        return finish(env, tools, att, 3, rows, path)
    log_path = a.steam_log or env.default_steam_log()
    deadline = t0 + a.wait_min * 60
    app_id = chk["steam"]["app_id"]
    seen_pid, seen_at, sampled, hints = None, None, False, att["modal_hints"]
    action = reason = None
    while action is None:
        env.sleep(POLL_S)
        now = env.now()
        text = env.read_tail(log_path)
        if text is not None:
            parsed = parse_steam_log(text)
            app_id = parsed["app_id"] if parsed["app_id"] is not None else app_id
            blk = steam_blocker(parsed, app_id, t0, now, env.steam_running())
            if blk:
                att["dialog"] = blk
                action = "blocked_steam_dialog"
                reason = 'Steam has waited %d s or more for a click on %s "%s" (%s)' % (
                    DIALOG_WAIT_S, blk["task"], blk["reason"], blk["local"])
                break
        cur = env.designer()
        if cur and cur["pid"] != att["old_pid"]:
            if cur["pid"] != seen_pid:
                seen_pid, seen_at, sampled = cur["pid"], now, False
            att["new_pid"] = cur["pid"]
            sess = env.session(a.session)
            if sess and sess.get("pid") == cur["pid"] and env.ping(a.session)[0]:
                action = "relaunched"
                att["seconds_to_bridge"] = round(now - t0, 1)
                reason = "Designer pid %d answers on the bridge %s s after the launch" % (cur["pid"], att["seconds_to_bridge"])
                break
            if now - seen_at > MODAL_AFTER_S and not sampled and env.can_sample:
                sampled = True
                hints = env.sample(cur["pid"])
                att["modal_hints"] = hints
                if hints and hints > 0:
                    action = "blocked_designer_modal"
                    reason = ("the new Designer pid %d has been up for over %d min without the bridge answering and "
                              "sample shows %d modal-dialog frames" % (cur["pid"], MODAL_AFTER_S // 60, hints))
                    break
        if now >= deadline:
            if att["new_pid"] is None:
                action, reason = "failed_no_process", "no new Designer process within %s min" % a.wait_min
            else:
                action = "failed_no_bridge"
                reason = "Designer pid %d is up but the bridge did not answer within %s min" % (att["new_pid"], a.wait_min)
    att["action"], att["reason"] = action, reason
    att["steam_running"] = env.steam_running()
    if action != "relaunched":
        return finish(env, tools, att, 3, rows, path)
    code = 0
    if a.package:
        att["package_reopened"] = reopen_package(env, a.session, a.package)
        if not att["package_reopened"]:
            code = 1
    if a.job:
        cmd = [sys.executable, os.path.join(HERE, "sdcall.py"), a.job, "--timeout", "900"]
        if a.session_given:
            cmd += ["--session", a.session]
        att["job_rc"] = env.run_job(cmd, 960)
        if att["job_rc"] != 0:
            code = 1
        if a.golden:
            att["diff"] = png_diff(a.golden, a.out)
            if att["diff"]["changed"] or att["diff"]["missing"]:
                code = 1
    return finish(env, tools, att, code, rows, path)


def main(argv=None, env=None):
    ap = argparse.ArgumentParser(prog="designer_relaunch.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    default_session = os.environ.get("SD_CLAUDE_BRIDGE_SESSION") or os.path.expanduser("~/.sd_claude_bridge/session.json")
    for name in ("check", "relaunch"):
        p = sub.add_parser(name)
        p.add_argument("--tools", required=(name == "relaunch"))
        p.add_argument("--steam-log")
        p.add_argument("--session", default=default_session,
                       help="the bridge's session file (default: %(default)s; set by SD_CLAUDE_BRIDGE_SESSION)")
    r = sub.choices["relaunch"]
    r.add_argument("--wait-min", type=float, default=30)
    r.add_argument("--package")
    r.add_argument("--job")
    r.add_argument("--golden")
    r.add_argument("--out")
    r.add_argument("--app")
    r.add_argument("--force", action="store_true")
    raw = list(sys.argv[1:] if argv is None else argv)
    a = ap.parse_args(raw)
    a.session_given = any(x == "--session" or x.startswith("--session=") for x in raw)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    env = env or Env()
    return cmd_check(a, env) if a.cmd == "check" else cmd_relaunch(a, env)


if __name__ == "__main__":
    sys.exit(main())
