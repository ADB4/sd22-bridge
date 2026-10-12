#!/usr/bin/env python3
"""docsplice.py: splice the docs workflow's verified changes into REFERENCE.md, spec.md and the other files they name.

    docsplice.py --tools T --dir D (--dry | --apply) [KEY ...]

T is the material's tools folder. D holds one `<KEY>.verified.json` per key (the docs workflow, assets/workflows/docs.js,
writes them to <T>/review/docs); a relative D is read against T. With no KEY, every `*.verified.json` in D is used,
sorted by name; keys apply in the order given (or sorted), and a later key sees the text an earlier one produced.

A verified file is a JSON object (extra fields such as key, started, ended, claims, corrections, open_questions, and
`why` on an edit are ignored):
  replace_sections  [{file, heading, text}]  `heading` is an existing heading line, copied exactly (`### Slab (459
                    nodes; ...)`). It must occur exactly once as a whole line of `file`, not inside a fenced code
                    block (CommonMark fences: a closing line may have trailing spaces, and a line that starts
                    with an inline code span is not an opener). A file, or a replacement text, that leaves a
                    fence unclosed is a problem, since the fence would hide every later heading. The section it
                    names runs to the next heading of the same or a higher level (fewer or as many `#`; fenced
                    lines are not headings) or the end of the file, and `text` replaces it whole.
                    `text` must start with a heading of the same level (its wording may change, node counts do) and
                    must hold no other heading of that level or higher, since that would end the section early.
                    A blank line is kept between the new text and the next heading.
  edits             [{file, old, new}]       `old` must occur exactly once in the file's current text (overlapping
                    occurrences count) and is replaced by `new`.
Within a key, replace_sections apply first, in order, then edits in order, each against the text the earlier ones
left. `file` is a path relative to T; it must exist, be a regular UTF-8 text file, and stay inside T after symlinks
are resolved (an absolute path or a `..` that leaves T is a problem).

--dry reads and applies everything in memory, prints every problem (not just the first) and writes nothing; exit 1 if
there is any problem, else 0. --apply does the same checks over all keys first and, on any problem, applies nothing
(exit 1). Otherwise it copies each file it changes to D/backup/<utc>/<relpath> (utc as YYYYmmddTHHMMSSZ; a second run
in the same second gets -2, -3, ...) and then writes each changed file atomically (temp file in the same folder, then
rename; the mode is kept; a file whose text did not change is not touched). If a write fails it puts back the files
already written from the backup and exits 1. Exit 2: usage error (bad arguments, D or T missing).

Warnings (stdout, `warning:` prefix, never change the exit code): a changed line longer than 120 characters that is not
a table row (new text only; lines already in the file are not reported), a `key` field that differs from the file name.
CRLF files keep their line ends on untouched lines; new text is written with LF.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import sys
import tempfile

MAXLINE = 120


class Usage(Exception):
    pass


# ----------------------------------------------------------------------------- text helpers

def level(line):
    """Heading level of a markdown heading line, else 0."""
    m = re.match(r"^(#+) ", line.rstrip("\r"))
    return len(m.group(1)) if m else 0


def fence_scan(lines):
    """(mask, open_line): mask[i] is True for a line inside a fenced code block (the fence lines included);
    open_line is the 1-based line of a fence still open at the end of the text, else None.
    CommonMark rules: an opening run of 3+ backticks or tildes (a backtick fence's info string holds no backtick, so
    a line starting with an inline code span is text); a closing line is a run of the same character at least as
    long, then only spaces or tabs."""
    out, fence, opened = [], None, None
    for n, ln in enumerate(lines, 1):
        s = ln.lstrip().rstrip("\r")
        if fence is None:
            m = re.match(r"^(`{3,}|~{3,})(.*)$", s)
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence, opened = (m.group(1)[0], len(m.group(1))), n
            out.append(fence is not None)
        else:
            out.append(True)
            m = re.match(r"^(`{3,}|~{3,})[ \t]*$", s)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence, opened = None, None
    return out, opened


def fenced_mask(lines):
    return fence_scan(lines)[0]


def count_overlapping(text, sub):
    n, i = 0, text.find(sub)
    while i >= 0:
        n += 1
        i = text.find(sub, i + 1)
    return n


def replace_section(text, head, new_text):
    """(new file text, None) or (None, problem). Pure; the caller labels the problem."""
    lines = text.split("\n")
    fm, unclosed = fence_scan(lines)
    if unclosed:
        return None, "the file has an unclosed code fence opened at line %d: every heading after it would be " \
                     "masked, so nothing is spliced until it is closed" % unclosed
    hl = level(head)
    if not hl:
        return None, "heading %r is not a markdown heading line (#, a space, a title)" % head[:80]
    idx = [i for i, ln in enumerate(lines) if not fm[i] and ln.rstrip("\r") == head]
    if len(idx) != 1:
        return None, "heading %r found %d times (needs exactly 1)" % (head[:90], len(idx))
    i = idx[0]
    j = i + 1
    while j < len(lines) and not (not fm[j] and 0 < level(lines[j]) <= hl):
        j += 1
    new = new_text.rstrip("\n").split("\n")
    if level(new[0]) != hl:
        return None, "replacement for %r does not start with a level-%d heading (starts %r)" % (
            head[:60], hl, new[0][:60])
    nfm, nopen = fence_scan(new)
    if nopen:
        return None, "replacement for %r leaves a code fence open (opened at its line %d)" % (head[:60], nopen)
    for k, ln in enumerate(new[1:], 1):
        if not nfm[k] and 0 < level(ln) <= hl:
            return None, "replacement for %r holds a level-%d heading at its line %d (%r), which would end the " \
                         "section early" % (head[:60], level(ln), k + 1, ln[:60])
    if j < len(lines):
        tail = [""] if new[-1] != "" else []
    else:
        # the section ran to the end of the file; the old last element "" is the file's final newline
        tail = [""] if lines[-1] == "" else []
    return "\n".join(lines[:i] + new + tail + lines[j:]), None


# ----------------------------------------------------------------------------- loading and planning

def safe_file(tools_real, f):
    """(real path, None) or (None, problem) for a JSON path relative to the tools folder."""
    if not isinstance(f, str) or not f.strip():
        return None, "file must be a non-empty string"
    if "\0" in f:
        return None, "file %r holds a NUL" % f[:60]
    if os.path.isabs(f) or re.match(r"^[A-Za-z]:[\\/]", f):
        return None, "file %r is absolute: paths are relative to the tools folder" % f
    real = os.path.realpath(os.path.join(tools_real, f))
    if os.path.commonpath([tools_real, real]) != tools_real or real == tools_real:
        return None, "file %r leaves the tools folder" % f
    if not os.path.isfile(real):
        return None, "file %r does not exist in the tools folder" % f
    return real, None


def load_key(dirp, key):
    """(data, None) or (None, problem)."""
    p = os.path.join(dirp, "%s.verified.json" % key)
    if not os.path.isfile(p):
        return None, "%s: %s does not exist" % (key, p)
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        return None, "%s: %s is not readable JSON (%s)" % (key, p, e)
    if not isinstance(d, dict):
        return None, "%s: %s is not a JSON object" % (key, p)
    for fld in ("replace_sections", "edits"):
        v = d.get(fld, [])
        if not isinstance(v, list) or not all(isinstance(x, dict) for x in v):
            return None, "%s: %r must be a list of objects" % (key, fld)
    return d, None


def plan(tools, dirp, keys):
    """Run every key in memory. Returns (texts {real path: new text}, originals {real path: text}, rels {real path:
    relpath}, problems [str], warnings [str], summary [(key, n_sections, n_edits)])."""
    tools_real = os.path.realpath(tools)
    texts, origs, rels, problems, warns, summary = {}, {}, {}, [], [], []

    def get(f, key, label):
        real, err = safe_file(tools_real, f)
        if err:
            problems.append("%s: %s: %s" % (key, label, err))
            return None
        if real not in texts:
            try:
                with open(real, encoding="utf-8", newline="") as fh:
                    texts[real] = origs[real] = fh.read()
            except (OSError, UnicodeDecodeError) as e:
                problems.append("%s: %s: %r cannot be read as UTF-8 text (%s)" % (key, label, f, e))
                return None
            rels[real] = os.path.relpath(real, tools_real)
        return real

    for key in keys:
        d, err = load_key(dirp, key)
        if err:
            problems.append(err)
            continue
        if d.get("key") not in (None, key):
            warns.append("%s: the file's key field is %r" % (key, d.get("key")))
        secs, eds = d.get("replace_sections", []), d.get("edits", [])
        for n, s in enumerate(secs):
            label = "replace_sections[%d]" % n
            if not all(isinstance(s.get(k), str) and s.get(k).strip() for k in ("file", "heading", "text")):
                problems.append("%s: %s needs non-empty string fields file, heading, text" % (key, label))
                continue
            real = get(s["file"], key, label)
            if real is None:
                continue
            new, perr = replace_section(texts[real], s["heading"].rstrip("\n"), s["text"])
            if perr:
                problems.append("%s: %s (%s): %s" % (key, label, s["file"], perr))
            else:
                texts[real] = new
        for n, e in enumerate(eds):
            label = "edits[%d]" % n
            if not (isinstance(e.get("file"), str) and e.get("file").strip()
                    and isinstance(e.get("old"), str) and e.get("old") != ""
                    and isinstance(e.get("new"), str)):
                problems.append("%s: %s needs string fields file, new and a non-empty string old" % (key, label))
                continue
            real = get(e["file"], key, label)
            if real is None:
                continue
            c = count_overlapping(texts[real], e["old"])
            if c != 1:
                problems.append("%s: %s (%s): old found %d times (needs exactly 1): %r"
                                % (key, label, e["file"], c, e["old"][:90]))
                continue
            i = texts[real].index(e["old"])
            texts[real] = texts[real][:i] + e["new"] + texts[real][i + len(e["old"]):]
        summary.append((key, len(secs), len(eds)))
    for real, t in texts.items():
        if t == origs[real]:
            continue
        old_lines = set(origs[real].split("\n"))
        for n, ln in enumerate(t.split("\n"), 1):
            if len(ln) > MAXLINE and not ln.startswith("|") and ln not in old_lines:
                warns.append("long line %s:%d (%d chars)" % (rels[real], n, len(ln)))
    return texts, origs, rels, problems, warns, summary


# ----------------------------------------------------------------------------- applying

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_atomic(path, text):
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".docsplice.", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def apply(dirp, texts, origs, rels):
    """Back up and write the changed files. Returns (backup dir or None, [changed rel paths])."""
    changed = sorted(r for r in texts if texts[r] != origs[r])
    if not changed:
        return None, []
    base = os.path.join(dirp, "backup", stamp())
    bdir, n = base, 1
    while os.path.exists(bdir):
        n += 1
        bdir = "%s-%d" % (base, n)
    for real in changed:
        dst = os.path.join(bdir, rels[real])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(real, dst)
    done = []
    try:
        for real in changed:
            write_atomic(real, texts[real])
            done.append(real)
    except BaseException as e:
        for real in done:
            shutil.copy2(os.path.join(bdir, rels[real]), real)
        raise OSError("write failed (%s); restored %d file(s) from %s" % (e, len(done), bdir))
    return bdir, [rels[r] for r in changed]


# ----------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="docsplice.py", add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("--tools", required=True)
    ap.add_argument("--dir", required=True, dest="dirp")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("keys", nargs="*")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    tools = os.path.abspath(os.path.expanduser(a.tools))
    if not os.path.isdir(tools):
        print("usage error: --tools %s is not a folder" % a.tools)
        return 2
    dirp = os.path.expanduser(a.dirp)
    dirp = dirp if os.path.isabs(dirp) else os.path.join(tools, dirp)
    dirp = os.path.normpath(dirp)
    if not os.path.isdir(dirp):
        print("usage error: --dir %s is not a folder" % dirp)
        return 2
    keys = a.keys
    if len(set(keys)) != len(keys):
        print("usage error: a key is given twice")
        return 2
    for k in keys:
        if not re.match(r"^[A-Za-z0-9_-]+$", k):
            print("usage error: key %r: letters, digits, _ and - only" % k)
            return 2
    if not keys:
        keys = sorted(f[:-len(".verified.json")] for f in os.listdir(dirp) if f.endswith(".verified.json"))
        if not keys:
            print("problem: no *.verified.json in %s" % dirp)
            return 1
    texts, origs, rels, problems, warns, summary = plan(tools, dirp, keys)
    for w in warns:
        print("warning: " + w)
    for p in problems:
        print("problem: " + p)
    files = sorted(rels[r] for r in texts if texts[r] != origs[r])
    if problems:
        print("%d problem%s in %s: nothing %s" % (len(problems), "" if len(problems) == 1 else "s", keys,
                                                   "applied" if a.apply else "to apply (dry run)"))
        return 1
    for key, ns, ne in summary:
        print("%s: %d section%s, %d edit%s" % (key, ns, "" if ns == 1 else "s", ne, "" if ne == 1 else "s"))
    if a.dry:
        print("dry run ok", keys, "->", files)
        return 0
    try:
        bdir, changed = apply(dirp, texts, origs, rels)
    except OSError as e:
        print("problem: " + str(e))
        return 1
    print("applied", keys, "->", changed, "(backup %s)" % bdir if bdir else "(no file changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
