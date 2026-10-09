#!/usr/bin/env python3
"""Say how big this Claude Code session's context is, so an unattended material run can hand off to a new leg.
A run continues in legs (sessions); a leg hands off at a context budget. This docstring is the reference.

Usage:
    python context_size.py [--session ID] [--soft 400000] [--hard 500000] [--json]

Options:
    --session   the session id; default $CLAUDE_CODE_SESSION_ID. Neither set: exit 2.
    --soft      tokens at or above which the state is handoff_at_clean_point (default 400000)
    --hard      tokens at or above which the state is handoff_now (default 500000)
    --json      print {session, jsonl, tokens, soft, hard, state, record_utc} instead of the line
Files: the transcript ~/.claude/projects/*/<id>.jsonl (the projects root is $CLAUDE_PROJECTS_DIR when set); if
several match, the newest mtime. None: exit 2.
Context size: of the last record with "type": "assistant", not "isSidechain": true, and message.usage,
input_tokens + cache_read_input_tokens + cache_creation_input_tokens (a missing field counts 0). The last 4 MB of
the file are scanned backwards first (transcripts reach 50+ MB), the whole file only if that finds no such record.
Lines that are not valid JSON (a partial last line while the session writes) are ignored.
State: ok below soft; handoff_at_clean_point at or above soft; handoff_now at or above hard.
Output: '<tokens> tokens (<state>; soft <soft>, hard <hard>) at <record utc>'. Works on any OS.
Standard library only, Python 3.9 or newer.
Exit code: 0 measured; 2 usage error, no session id, no transcript, or no usage record in it.
"""
import argparse
import glob
import json
import os
import sys

TAIL = 4 * 1024 * 1024


def find_transcript(session, root=None):
    root = root or os.environ.get("CLAUDE_PROJECTS_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "projects")
    hits = glob.glob(os.path.join(glob.escape(root), "*", glob.escape(session) + ".jsonl"))
    return max(hits, key=os.path.getmtime) if hits else None


def usage_of(line):
    try:
        rec = json.loads(line)
    except ValueError:
        return None
    if not isinstance(rec, dict) or rec.get("type") != "assistant" or rec.get("isSidechain") is True:
        return None
    msg = rec.get("message")
    use = msg.get("usage") if isinstance(msg, dict) else None
    if not isinstance(use, dict):
        return None
    total = sum(int(use.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return total, rec.get("timestamp") or ""


def last_usage(path):
    size = os.path.getsize(path)
    for start in (max(0, size - TAIL), 0):
        with open(path, "rb") as f:
            f.seek(start)
            data = f.read()
        lines = data.split(b"\n")
        if start > 0:
            lines = lines[1:]  # the first line is cut mid-record
        for raw in reversed(lines):
            if raw.strip():
                got = usage_of(raw.decode("utf-8", "replace"))
                if got:
                    return got
        if start == 0:
            break
    return None


def state_of(tokens, soft, hard):
    return "handoff_now" if tokens >= hard else "handoff_at_clean_point" if tokens >= soft else "ok"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Report the context size of a Claude Code session.")
    ap.add_argument("--session")
    ap.add_argument("--soft", type=int, default=400000)
    ap.add_argument("--hard", type=int, default=500000)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    session = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session:
        print("context_size: no session id (use --session or set CLAUDE_CODE_SESSION_ID)", file=sys.stderr)
        return 2
    path = find_transcript(session)
    if not path:
        print("context_size: no transcript for session %s under the projects root" % session, file=sys.stderr)
        return 2
    got = last_usage(path)
    if not got:
        print("context_size: no assistant record with usage in %s" % path, file=sys.stderr)
        return 2
    tokens, utc = got
    state = state_of(tokens, args.soft, args.hard)
    if args.json:
        print(json.dumps({"session": session, "jsonl": path, "tokens": tokens, "soft": args.soft,
                          "hard": args.hard, "state": state, "record_utc": utc}))
    else:
        print("%d tokens (%s; soft %d, hard %d) at %s" % (tokens, state, args.soft, args.hard, utc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
