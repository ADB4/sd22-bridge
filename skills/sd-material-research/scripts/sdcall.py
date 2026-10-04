#!/usr/bin/env python3
"""Run a Python file inside Designer through the sd_claude_bridge socket, without the MCP client's ~60 s limit.

Usage (from a shell, ideally as a background command):
    python3 sdcall.py job.py [--timeout 900] [--out job.result.json]

Sends the file's code as one run_python command (same namespace and undo group as the MCP tool) and writes the reply
({"stdout", "result"} or {"stdout", "error"}) to --out (default <job>.result.json). Prints a short summary.
Use it for cold exports of several variants, nowear + preset batches and node timing sweeps.
While it runs Designer is busy: MCP calls will time out, which is expected. Wait for this command instead.
Standard library only. Never prints the session token.
"""
import argparse
import json
import os
import socket
import sys
import time


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("job")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--out")
    ap.add_argument("--session", default=os.path.expanduser("~/.sd_claude_bridge/session.json"))
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # Designer's text may not fit a Windows console code page
        sys.stdout.reconfigure(errors="replace")
    with open(a.job, encoding="utf-8-sig") as fh:  # not the locale's code page (cp1252 on Windows)
        code = fh.read()
    with open(a.session, encoding="utf-8") as fh:
        s = json.load(fh)
    out = a.out or os.path.splitext(a.job)[0] + ".result.json"
    req = {"id": int(time.time()), "token": s["token"], "cmd": "run_python", "args": {"code": code}}
    t0 = time.time()
    try:
        k = socket.create_connection(("127.0.0.1", int(s["port"])), timeout=5)
    except OSError as e:
        print("cannot reach Designer's bridge on port %s: %s (is Designer running with the plugin?)" % (s.get("port"), e))
        return 2
    k.settimeout(a.timeout)
    k.sendall((json.dumps(req) + "\n").encode("utf-8"))
    buf = b""
    try:
        while b"\n" not in buf:
            chunk = k.recv(65536)
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        print("no reply within %.0f s; Designer may still be working (check with designer_status later)" % a.timeout)
        return 3
    except OSError as e:  # reset by the peer (Windows) when Designer goes away mid-job
        buf = b""
        print("connection error: %s" % e)
    finally:
        k.close()
    if b"\n" not in buf:
        print("Designer closed the connection without replying (it may have crashed, or the plugin reloaded). "
              "Check Designer before running the job again.")
        return 1
    reply = json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
    body = reply.get("result") if reply.get("ok") else {"error": reply.get("error"), "traceback": reply.get("traceback")}
    with open(out, "w") as fh:
        json.dump(body, fh, indent=1, default=str)
    secs = time.time() - t0
    err = (body or {}).get("error") if isinstance(body, dict) else None
    print("%s in %.1f s -> %s" % ("ERROR" if err or not reply.get("ok") else "ok", secs, out))
    if isinstance(body, dict) and body.get("stdout"):
        print(body["stdout"][-2000:])
    if err:
        print(str(err)[-2000:])
    return 1 if (err or not reply.get("ok")) else 0


if __name__ == "__main__":
    sys.exit(main())
