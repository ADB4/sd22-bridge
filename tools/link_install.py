"""Point this machine's installed bridge at this git checkout.

The installers copy files: the plugin into Designer's sduserplugins folder and the MCP
server into a per-user folder. After a git pull those copies are stale, and an edit made
in one of them never reaches the repo. This replaces each copy with a link into the repo:

    <sduserplugins>/sd_claude_bridge       -> designer_plugin/sd_claude_bridge
    <install dir>/sd_designer_mcp.py, ...  -> mcp_server/...
    ~/.claude/skills/sd-material-research  -> skills/sd-material-research

Run the installer once first (it makes the Python environment and the Claude config), then:

    macOS:    python3 tools/link_install.py
    Windows:  py tools\\link_install.py

--status shows what each location is and changes nothing. --unlink turns each link back
into a plain copy of the repo. A copy that differs from the repo is moved to
.link-backups/<time>/ in the repo, never deleted: diff it against the repo before removing it.

Windows: folders become junctions, which need no special rights. The three server files
need file symlinks, which Windows allows only with Developer Mode on (Settings > System >
For developers) or from an administrator prompt.
"""

import argparse
import base64
import os
import shutil
import stat
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDOWS = sys.platform == "win32"
SERVER_FILES = ("sd_designer_mcp.py", "configure_claude.py", "requirements.txt")
SKILL = "sd-material-research"
IGNORED = {"__pycache__", ".DS_Store", "Thumbs.db", "desktop.ini"}


def documents():
    if WINDOWS:
        # Follows OneDrive redirection, the same lookup install.ps1 uses. The path comes back as
        # base64 of its UTF-8 bytes: PowerShell writes plain text in the console's OEM code page.
        cmd = ("[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("
               "[Environment]::GetFolderPath('MyDocuments')))")
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=60,
            ).stdout.strip()
            if out:
                return base64.b64decode(out).decode("utf-8")
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def install_dir():
    if WINDOWS:
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "sd-claude-bridge")
    return os.path.expanduser("~/Library/Application Support/sd-claude-bridge")


def targets():
    """(location, repo path, label) for every place this machine should link."""
    out = []
    docs = documents()
    # Adobe installs and the Steam edition keep user plugins in different folders.
    for sub in (("Adobe", "Adobe Substance 3D Designer"), ("Allegorithmic", "Substance Designer")):
        plugins = os.path.join(docs, *sub, "python", "sduserplugins")
        if os.path.isdir(plugins):
            out.append((os.path.join(plugins, "sd_claude_bridge"),
                        os.path.join(REPO, "designer_plugin", "sd_claude_bridge"),
                        "plugin-" + sub[0].lower()))
    labels = [label for _, _, label in out]
    if not labels:
        print("! No Designer sduserplugins folder under %s. Start Designer once, then run this again." % docs)
    elif labels == ["plugin-adobe"]:
        # The installer makes the Adobe folder when it finds none, before a Steam Designer ever ran.
        print("! Only the Adobe Designer folder has sduserplugins. Using the Steam edition? Start Designer once,"
              " then run this again.")
    inst = install_dir()
    if os.path.isdir(inst):
        for name in SERVER_FILES:
            out.append((os.path.join(inst, name), os.path.join(REPO, "mcp_server", name), "server-" + name))
    else:
        print("! %s doesn't exist: run the installer first, then this script." % inst)
    out.append((os.path.join(os.path.expanduser("~"), ".claude", "skills", SKILL),
                os.path.join(REPO, "skills", SKILL), "skill"))
    return out


# Reparse tags of a symlink and a junction. Other reparse points, such as OneDrive placeholders, are plain files and
# folders here.
LINK_TAGS = (0xA000000C, 0xA0000003)


def is_link(path):
    """A symlink, or on Windows also a junction (os.path.islink misses those before 3.12)."""
    if os.path.islink(path):
        return True
    try:
        st = os.lstat(path)
    except OSError:
        return False
    tag = getattr(st, "st_reparse_tag", None)  # Windows, Python 3.8+
    if tag is not None:
        return tag in LINK_TAGS
    return bool(getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def links_to(path, target):
    try:
        return os.path.samefile(path, target)
    except OSError:
        return False


def in_repo(path):
    """True when path, with its parent folders' links resolved, is the repo or inside it. Then the
    location reaches the repo through a linked parent folder (or is the checkout itself), and
    deleting it would delete repo files."""
    real = os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))
    real, repo = os.path.normcase(real), os.path.normcase(os.path.realpath(REPO))
    return real == repo or real.startswith(repo + os.sep)


def tree(root):
    """Relative path -> full path of every file under root, skipping caches and OS clutter."""
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED]
        for name in filenames:
            if name in IGNORED or name.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, name)
            files[os.path.relpath(full, root)] = full
    return files


def same_file(a, b):
    """Equal apart from line endings (a Windows copy may have CRLF where the repo has LF)."""
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read().replace(b"\r\n", b"\n") == fb.read().replace(b"\r\n", b"\n")


def same_content(copy, target):
    if os.path.isdir(target):
        if not os.path.isdir(copy):
            return False
        a, b = tree(copy), tree(target)
        return a.keys() == b.keys() and all(same_file(a[k], b[k]) for k in a)
    return os.path.isfile(copy) and same_file(copy, target)


def remove_link(path):
    # Removes the link only, never what it points to.
    if WINDOWS and os.path.isdir(path):
        os.rmdir(path)
    else:
        os.unlink(path)


def make_link(path, target):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    if WINDOWS and os.path.isdir(target):
        # A junction needs no special rights, unlike a directory symlink.
        r = subprocess.run(["cmd", "/c", "mklink", "/J", path, target], capture_output=True, text=True)
        if r.returncode != 0:
            raise OSError((r.stdout + r.stderr).strip())
    else:
        os.symlink(target, path)


def copy_from_repo(path, target):
    if os.path.isdir(target):
        shutil.copytree(target, path, ignore=shutil.ignore_patterns(*IGNORED, "*.pyc"))
    else:
        shutil.copy2(target, path)


def describe(path, target):
    if in_repo(path):
        if links_to(path, target):
            return "linked to this repo (by a parent folder)"
        return "inside this repo (by a parent folder link)"
    if is_link(path):
        if links_to(path, target):
            return "linked to this repo"
        try:
            return "linked elsewhere: %s" % os.readlink(path)
        except OSError:
            return "linked elsewhere"
    if not os.path.lexists(path):
        return "missing"
    return "copy, %s" % ("same as repo" if same_content(path, target) else "DIFFERS from repo")


def link(path, target, label, backups):
    if in_repo(path):
        if links_to(path, target):
            print("  ok       %s (a parent folder links into the repo)" % path)
            return True
        print("  FAILED   %s is inside this repo (a parent folder links into it, or the repo was cloned"
              " here). Left as is; fix that by hand." % path)
        return False
    if is_link(path):
        if links_to(path, target):
            print("  ok       %s" % path)
            return True
        remove_link(path)
        print("  relink   %s (it pointed elsewhere)" % path)
    elif os.path.lexists(path):
        if same_content(path, target):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        else:
            if not os.path.isdir(backups):
                os.makedirs(backups)
            kept = os.path.join(backups, label)
            shutil.move(path, kept)
            print("  set aside %s\n            -> %s (differs from the repo)" % (path, kept))
    try:
        make_link(path, target)
    except OSError as e:
        print("  FAILED   %s: %s" % (path, e))
        if WINDOWS and not os.path.isdir(target):
            print("           File symlinks need Developer Mode (Settings > System > For developers)")
            print("           or an administrator prompt. Turn one on and run this again.")
        if not os.path.lexists(path):
            copy_from_repo(path, target)
            print("           Put a plain copy of the repo file back so the bridge keeps working.")
        return False
    print("  linked   %s" % path)
    return True


def unlink(path, target):
    if not (is_link(path) and links_to(path, target)):
        print("  skip     %s (%s)" % (path, describe(path, target)))
        return
    remove_link(path)
    copy_from_repo(path, target)
    print("  copied   %s" % path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true", help="show each location; change nothing")
    mode.add_argument("--unlink", action="store_true", help="replace each link with a copy of the repo")
    ns = ap.parse_args()

    print("Repo: %s" % REPO)
    places = targets()
    if ns.status:
        for path, target, _ in places:
            print("  %-34s %s" % (describe(path, target), path))
        return 0
    if ns.unlink:
        for path, target, _ in places:
            unlink(path, target)
        return 0

    backups = os.path.join(REPO, ".link-backups", time.strftime("%Y%m%d-%H%M%S"))
    ok = all([link(path, target, label, backups) for path, target, label in places])
    print()
    print("Restart Designer to load the plugin from the repo. Server changes reach Claude in a new")
    print("session, and the skill in any new Claude Code session.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
