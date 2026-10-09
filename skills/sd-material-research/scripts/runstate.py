#!/usr/bin/env python3
"""Share one unattended material run's state between its sessions ("legs") and the watchdog routine.
A run is carried by several sessions in turn plus a watchdog; they share <tools>/RUN.json (mode, deadline_local,
standing_decisions, continuation, owner, next_leg, estimate, caffeinate_pid, incidents, ...) and stamp
<tools>/stages.jsonl. Writers take a lock file so concurrent writers never lose an update, and a leg can tell whether
it still owns the run. This docstring is the reference.

Usage:
    python runstate.py get       --tools T [KEY]
    python runstate.py set       --tools T KEY=VALUE [KEY=VALUE ...]
    python runstate.py incident  --tools T --text TEXT [--by WHO]
    python runstate.py stamp     --tools T --stage S --event E [--note N] [--extra JSON]
    python runstate.py heartbeat --tools T [--loop SECONDS]
    python runstate.py heartbeat-age --tools T
    python runstate.py owner-check   --tools T
All subcommands take --session ID (default $CLAUDE_CODE_SESSION_ID); only its first 8 characters are used to match.

Subcommands:
    get            print RUN.json, or one key, as JSON. A dotted key reaches nested objects (estimate.ready_to).
                   A missing RUN.json prints {} and a missing key prints null; exit 0.
    set            each VALUE is parsed as JSON when it parses, else kept as a string; a dotted key creates the nested
                   objects. One locked update; prints the keys it set.
    incident       append {utc, by, text} to incidents (created if missing); by defaults to the session's first 8
                   characters.
    stamp          append one line to stages.jsonl: stage (omitted when S is "-"), event, utc, note (when given), then
                   the keys of the --extra object (a touch row's kind, asked_utc, answered_utc, recommended_taken);
                   --extra cannot replace stage, event or utc. The session's first line in that file also carries
                   session (8 characters) and effort ($CLAUDE_EFFORT, omitted when unset). Prints the line, then
                   touches the heartbeat.
    heartbeat      write "<utc> <session8>" to review/heartbeat. With --loop, repeat every SECONDS while RUN.json mode
                   is unattended or probe and its owner is this session; otherwise print why and exit 0. For a
                   background shell.
    heartbeat-age  minutes since the heartbeat file's mtime, one decimal; "none" and exit 1 when there is no file.
    owner-check    exit 0 when RUN.json owner is this session (owner may be a full id or its first 8 characters);
                   3 when it is not (prints the owner) or is "pending"; 2 when RUN.json is missing.
Files under T: RUN.json, RUN.json.lock and RUN.json.tmp (update), stages.jsonl and stages.jsonl.lock, review/heartbeat.
A lock is a file created with O_CREAT|O_EXCL; one older than 60 s is stale and taken over; a writer waits 15 s for it.
Module API for other scripts (sys.path.insert(0, scripts dir)): load(tools) -> dict, update(tools, mutate) -> dict,
touch_heartbeat(tools, session), utc().
Standard library only, Python 3.9 or newer; os.path and UTF-8 throughout, so it runs on Windows.
Exit code: 0 ok; 1 no heartbeat file; 2 usage error, bad JSON or lock timeout; 3 not the owner.
"""
import argparse
import contextlib
import json
import os
import sys
import time

if sys.version_info < (3, 9):
    sys.stderr.write("runstate.py needs Python 3.9 or newer (this is %s)\n" % sys.version.split()[0])
    sys.exit(2)

STALE_S = 60
WAIT_S = 15


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _path(tools, *parts):
    return os.path.join(tools, *parts)


@contextlib.contextmanager
def _lock(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    end = time.time() + WAIT_S
    while True:
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(path) > STALE_S:
                    os.unlink(path)
                    continue
            except OSError:
                continue
            if time.time() > end:
                raise RuntimeError("could not take the lock %s in %d s" % (path, WAIT_S))
            time.sleep(0.02)
    try:
        yield
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def load(tools):
    try:
        with open(_path(tools, "RUN.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def update(tools, mutate):
    run = _path(tools, "RUN.json")
    with _lock(run + ".lock"):
        d = load(tools)
        mutate(d)
        with open(run + ".tmp", "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(run + ".tmp", run)
    return d


def touch_heartbeat(tools, session):
    os.makedirs(_path(tools, "review"), exist_ok=True)
    path = _path(tools, "review", "heartbeat")
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("%s %s\n" % (utc(), (session or "")[:8]))
    os.replace(tmp, path)


def _owns(d, session):
    owner = str(d.get("owner") or "")
    return bool(session) and owner != "pending" and owner[:8] == session[:8] and owner != ""


def _dig(d, key):
    for part in key.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d


def _put(d, key, value):
    parts = key.split(".")
    for part in parts[:-1]:
        if not isinstance(d.get(part), dict):
            d[part] = {}
        d = d[part]
    d[parts[-1]] = value


def _parse(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def _show(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_get(a, session):
    d = load(a.tools)
    _show(d if a.key is None else _dig(d, a.key))
    return 0


def cmd_set(a, session):
    pairs = []
    for item in a.pairs:
        if "=" not in item or not item.split("=", 1)[0]:
            sys.stderr.write("set wants KEY=VALUE, got %r\n" % item)
            return 2
        k, v = item.split("=", 1)
        pairs.append((k, _parse(v)))

    def mutate(d):
        for k, v in pairs:
            _put(d, k, v)
    update(a.tools, mutate)
    _show(dict(pairs))
    return 0


def cmd_incident(a, session):
    row = {"utc": utc(), "by": a.by or session[:8], "text": a.text}

    def mutate(d):
        if not isinstance(d.get("incidents"), list):
            d["incidents"] = []
        d["incidents"].append(row)
    update(a.tools, mutate)
    _show(row)
    return 0


def _has_session(path, sid):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    if json.loads(line).get("session") == sid:
                        return True
                except (ValueError, AttributeError):
                    pass
    except FileNotFoundError:
        pass
    return False


def cmd_stamp(a, session):
    extra = _parse(a.extra) if a.extra else {}
    if not isinstance(extra, dict):
        sys.stderr.write("--extra must be a JSON object\n")
        return 2
    sid = session[:8]
    path = _path(a.tools, "stages.jsonl")
    line = {}
    if a.stage != "-":
        line["stage"] = a.stage
    line["event"] = a.event
    line["utc"] = utc()
    if a.note is not None:
        line["note"] = a.note
    with _lock(path + ".lock"):
        if sid and not _has_session(path, sid):
            line["session"] = sid
            if os.environ.get("CLAUDE_EFFORT"):
                line["effort"] = os.environ["CLAUDE_EFFORT"]
        for k, v in extra.items():
            if k not in ("stage", "event", "utc"):
                line[k] = v
        data = (json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8")
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0))
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    print(data.decode("utf-8").rstrip("\n"))
    touch_heartbeat(a.tools, session)
    return 0


def _stop_reason(tools, session):
    if not os.path.exists(_path(tools, "RUN.json")):
        return "RUN.json is gone"
    d = load(tools)
    if d.get("mode") not in ("unattended", "probe"):
        return "mode is %s" % d.get("mode")
    if not _owns(d, session):
        return "owner is %s, not this session" % d.get("owner")
    return None


def cmd_heartbeat(a, session):
    if a.loop is not None and a.loop <= 0:
        sys.stderr.write("--loop wants a positive number of seconds\n")
        return 2
    if a.loop is None:
        touch_heartbeat(a.tools, session)
        return 0
    while True:
        why = _stop_reason(a.tools, session)
        if why:
            print("heartbeat stopped: " + why, flush=True)
            return 0
        touch_heartbeat(a.tools, session)
        time.sleep(a.loop)


def cmd_heartbeat_age(a, session):
    try:
        age = (time.time() - os.path.getmtime(_path(a.tools, "review", "heartbeat"))) / 60.0
    except OSError:
        print("none")
        return 1
    print("%.1f" % max(age, 0.0))
    return 0


def cmd_owner_check(a, session):
    if not os.path.exists(_path(a.tools, "RUN.json")):
        print("no RUN.json")
        return 2
    d = load(a.tools)
    if _owns(d, session):
        return 0
    print(d.get("owner") if d.get("owner") else "none")
    return 3


def main(argv=None):
    ap = argparse.ArgumentParser(description="Shared state of an unattended material run (see the module docstring).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn):
        p = sub.add_parser(name)
        p.add_argument("--tools", required=True)
        p.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID", ""))
        p.set_defaults(fn=fn)
        return p

    add("get", cmd_get).add_argument("key", nargs="?")
    add("set", cmd_set).add_argument("pairs", nargs="+", metavar="KEY=VALUE")
    p = add("incident", cmd_incident)
    p.add_argument("--text", required=True)
    p.add_argument("--by")
    p = add("stamp", cmd_stamp)
    p.add_argument("--stage", required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--note")
    p.add_argument("--extra")
    add("heartbeat", cmd_heartbeat).add_argument("--loop", type=float)
    add("heartbeat-age", cmd_heartbeat_age)
    add("owner-check", cmd_owner_check)
    a = ap.parse_args(argv)
    try:
        return a.fn(a, a.session)
    except (RuntimeError, ValueError) as e:
        sys.stderr.write("runstate: %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
