"""Keep macOS App Nap off while the bridge runs a command.

When Designer isn't visible, App Nap drops it to scheduler priority 4 and the same graph job runs
7.5-14x slower. An NSProcessInfo activity held for the length of each command keeps it at full
speed; between commands Designer naps as usual. Nothing persists: the activity ends with the
command, or at the latest when Designer quits.

A no-op off macOS, and with SD_CLAUDE_BRIDGE_NO_ACTIVITY=1. It fails open: if the Objective-C
calls don't work, it says so once in Designer's console and commands run as they would without it.
"""

import ctypes
import ctypes.util
import os
import sys

LOG = "[Claude bridge]"
# NSActivityUserInitiatedAllowingIdleSystemSleep | NSActivityLatencyCritical: no App Nap while the
# command runs, while an idle Mac may still sleep.
OPTIONS = (0x00FFFFFF & ~(1 << 20)) | 0xFF00000000
FOUNDATION = "/System/Library/Frameworks/Foundation.framework/Foundation"

DISABLED = os.environ.get("SD_CLAUDE_BRIDGE_NO_ACTIVITY", "").strip().lower() not in ("", "0", "false", "no", "off")

_objc = None  # the loaded calls, see _load()
_failed = False  # after the first failure every call is a no-op


def _load():
    lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc") or "/usr/lib/libobjc.A.dylib")
    # NSProcessInfo lives in Foundation. Designer has it loaded already; a plain Python doesn't.
    ctypes.cdll.LoadLibrary(FOUNDATION)
    P = ctypes.c_void_p
    for name, res, args in (
        ("objc_getClass", P, [ctypes.c_char_p]),
        ("sel_registerName", P, [ctypes.c_char_p]),
        ("objc_autoreleasePoolPush", P, []),
        ("objc_autoreleasePoolPop", None, [P]),
    ):
        f = getattr(lib, name)
        f.restype, f.argtypes = res, args
    # objc_msgSend has to be called through the exact prototype of each method (arm64 and x86_64).
    send = ctypes.cast(lib.objc_msgSend, P).value

    def msg(res, *args):
        return ctypes.CFUNCTYPE(res, P, P, *args)(send)

    sel = lib.sel_registerName
    calls = {
        "lib": lib,
        "info": lib.objc_getClass(b"NSProcessInfo"),
        "string": lib.objc_getClass(b"NSString"),
        "id": msg(P),  # processInfo, alloc, retain
        "void": msg(None),  # release
        "init_utf8": msg(P, ctypes.c_char_p),
        "begin": msg(P, ctypes.c_uint64, P),
        "end": msg(None, P),
        "sel": {
            s: sel(s)
            for s in (b"processInfo", b"alloc", b"initWithUTF8String:", b"retain", b"release",
                      b"beginActivityWithOptions:reason:", b"endActivity:")
        },
    }
    if not (calls["info"] and calls["string"]) or not all(calls["sel"].values()):
        raise RuntimeError("NSProcessInfo or NSString not found")
    return calls


def _fail(what, e):
    global _failed
    if not _failed:
        _failed = True
        print("%s could not %s an App Nap activity, commands run without it: %s: %s"
              % (LOG, what, type(e).__name__, e))


def enabled():
    return sys.platform == "darwin" and not DISABLED and not _failed


def begin(reason):
    """Start an activity for one command. Returns a token for end(), or None when there's none."""
    global _objc
    if not enabled():
        return None
    try:
        if _objc is None:
            _objc = _load()
        c, s = _objc, _objc["sel"]
        # Own pool: the reason string and the autoreleased token go away here, not whenever
        # Designer's run loop drains its pool. The token is retained until end().
        pool = c["lib"].objc_autoreleasePoolPush()
        try:
            text = ("sd-claude-bridge: %s" % (reason,))[:200].encode("utf-8", "replace")
            info = c["id"](c["info"], s[b"processInfo"])
            name = c["init_utf8"](c["id"](c["string"], s[b"alloc"]), s[b"initWithUTF8String:"], text)
            try:
                tok = c["begin"](info, s[b"beginActivityWithOptions:reason:"], OPTIONS, name)
            finally:
                if name:
                    c["void"](name, s[b"release"])
            if not tok:
                raise RuntimeError("beginActivityWithOptions:reason: returned nil")
            c["id"](tok, s[b"retain"])
            return tok
        finally:
            c["lib"].objc_autoreleasePoolPop(pool)
    except Exception as e:
        _fail("start", e)
        return None


def end(tok):
    """End an activity begin() started. A None token does nothing."""
    global _objc
    if tok is None:
        return
    try:
        if _objc is None:  # this module was reloaded while the command ran
            _objc = _load()
        c, s = _objc, _objc["sel"]
        c["end"](c["id"](c["info"], s[b"processInfo"]), s[b"endActivity:"], tok)
        c["void"](tok, s[b"release"])
    except Exception as e:
        _fail("end", e)
