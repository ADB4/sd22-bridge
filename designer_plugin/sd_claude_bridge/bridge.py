"""Loopback TCP server that runs inside Designer.

Protocol: one JSON object per line in each direction.
  request : {"id": 1, "token": "...", "cmd": "get_graph", "args": {...}}
  response: {"id": 1, "ok": true, "result": ...}
            {"id": 1, "ok": false, "error": "...", "traceback": "..."}

The listening socket is non-blocking and polled by a QTimer, so every
command runs on Designer's main (GUI) thread. This avoids QtNetwork and
threading entirely and works with PySide2 (Designer 2022) or PySide6.
"""

import hmac
import json
import os
import secrets
import socket
import sys
import time
import traceback

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:  # newer Designer builds
    from PySide6 import QtCore, QtWidgets

from . import activity

LOG = "[Claude bridge]"
DEFAULT_PORT = 9881
PORT_ATTEMPTS = 10
MAX_REQUEST_BYTES = 16 * 1024 * 1024
POLL_MS = 25
# Bounds on what one poll does, so a misbehaving local client can't hold the GUI thread or exhaust
# Designer's file handles. The clients send one request per connection.
MAX_CLIENTS = 16
MAX_READ_PER_POLL = 4 * 1024 * 1024
MAX_LINES_PER_POLL = 8
IDLE_SECONDS = 60
SESSION_CHECK_SECONDS = 5
BAD_TOKEN = "bad token (the session file doesn't match this Designer; restart Designer)"
# A reply to a client that already closed must raise EPIPE, not kill Designer with SIGPIPE (macOS).
SEND_FLAGS = getattr(socket, "MSG_NOSIGNAL", 0)


def _modal_open():
    # Qt fires this timer inside modal dialogs too (a "save changes?" prompt). Wait until the
    # dialog closes instead of editing behind it.
    try:
        return (QtCore.QCoreApplication.instance() is not None
                and QtWidgets.QApplication.activeModalWidget() is not None)
    except Exception:
        return False


def session_dir():
    return os.path.join(os.path.expanduser("~"), ".sd_claude_bridge")


def session_path():
    return os.environ.get("SD_CLAUDE_BRIDGE_SESSION") or os.path.join(
        session_dir(), "session.json"
    )


class _Client(object):
    __slots__ = ("sock", "buf", "closed", "active")

    def __init__(self, sock):
        self.sock = sock
        self.buf = bytearray()
        self.closed = False
        self.active = time.time()


class BridgeServer(object):
    def __init__(self, dispatch, version):
        self._dispatch = dispatch
        self._version = version
        self._sock = None
        self._clients = []
        self._timer = None
        self._busy = False
        self._authed = False
        self._session_check = time.monotonic()  # its zero point is undefined
        self._session_error = None
        self.port = None
        self.token = secrets.token_hex(16)

    # ------------------------------------------------------------------ setup
    def start(self):
        first = int(os.environ.get("SD_CLAUDE_BRIDGE_PORT", DEFAULT_PORT))
        last_error = None
        for port in range(first, first + PORT_ATTEMPTS):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # On Windows, refuse to share the port with another process.
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                except OSError:
                    pass
            try:
                s.bind(("127.0.0.1", port))
            except OSError as e:
                last_error = e
                s.close()
                continue
            s.listen(8)
            s.setblocking(False)
            self._sock = s
            self.port = port
            break
        if self._sock is None:
            raise RuntimeError(
                "could not bind 127.0.0.1:%d-%d (%s)"
                % (first, first + PORT_ATTEMPTS - 1, last_error)
            )

        self._write_session()
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._poll)
        self._timer.start(POLL_MS)
        print("%s v%s listening on 127.0.0.1:%d" % (LOG, self._version, self.port))

    def stop(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        for c in list(self._clients):
            self._drop(c)
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self._remove_session()
        print("%s stopped" % LOG)

    def _write_session(self):
        path = session_path()
        folder = os.path.dirname(path)
        # The token lets a client run code in Designer, so only this user may read it.
        if not os.path.isdir(folder):
            os.makedirs(folder, 0o700)
        elif os.path.basename(folder) == ".sd_claude_bridge":
            try:
                os.chmod(folder, 0o700)
            except OSError:
                pass
        data = {
            "port": self.port,
            "token": self.token,
            "pid": os.getpid(),
            "bridge_version": self._version,
            "python": sys.version.split()[0],
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        tmp = path + ".tmp"
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)

    def _restore_session(self):
        # A second Designer takes the session file over, and removes it when it quits. Write it
        # again once it's gone, so this Designer is reachable again without a restart.
        now = time.monotonic()
        if now - self._session_check < SESSION_CHECK_SECONDS:
            return
        self._session_check = now
        if os.path.exists(session_path()):
            return
        try:
            self._write_session()
        except Exception as e:
            if str(e) != self._session_error:  # once, not every few seconds
                print("%s could not write the session file again: %s" % (LOG, e))
            self._session_error = str(e)
            return
        self._session_error = None
        print("%s the session file was gone; wrote it again (port %d)" % (LOG, self.port))

    def _remove_session(self):
        path = session_path()
        try:
            with open(path) as f:
                data = json.load(f)
            if data.get("pid") == os.getpid() and data.get("port") == self.port:
                os.remove(path)
        except Exception:
            pass

    # ---------------------------------------------------------------- polling
    def _poll(self):
        # A command can pump the Qt event loop (e.g. while computing a graph),
        # which would fire this timer again. Never re-enter.
        if self._busy or self._sock is None or _modal_open():
            return
        self._busy = True
        try:
            self._restore_session()
            self._accept()
            for c in list(self._clients):
                self._service(c)
        except Exception:
            print("%s poll error:\n%s" % (LOG, traceback.format_exc()))
        finally:
            self._busy = False

    def _accept(self):
        # Past the cap, connections wait in the listen backlog until a slot frees up.
        while len(self._clients) < MAX_CLIENTS:
            try:
                conn, addr = self._sock.accept()
            except (BlockingIOError, InterruptedError):
                return
            except OSError:
                return
            if addr[0] != "127.0.0.1":
                conn.close()
                continue
            conn.setblocking(False)
            self._clients.append(_Client(conn))

    def _service(self, c):
        eof = False
        budget = MAX_READ_PER_POLL
        while budget > 0:
            try:
                chunk = c.sock.recv(65536)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                eof = True
                break
            if not chunk:
                eof = True
                break
            c.buf += chunk
            c.active = time.time()
            budget -= len(chunk)

        start = handled = 0
        while not c.closed and handled < MAX_LINES_PER_POLL:
            end = c.buf.find(b"\n", start)
            if end < 0:
                break
            line = bytes(c.buf[start:end])
            start = end + 1
            if line.strip():
                handled += 1
                self._send(c, self._handle(line))
                if not self._authed:
                    self._drop(c)  # no second try without the token
        del c.buf[:start]

        if c.closed:
            return
        if len(c.buf) > MAX_REQUEST_BYTES:
            self._send(c, {"id": None, "ok": False, "error": "request too large"})
            self._drop(c)
        elif eof or time.time() - c.active > IDLE_SECONDS:
            self._drop(c)

    def _handle(self, line):
        req_id = None
        self._authed = False
        try:
            req = json.loads(line.decode("utf-8"))
            req_id = req.get("id")
            token = str(req.get("token", ""))
            if not hmac.compare_digest(token.encode("utf-8"), self.token.encode("utf-8")):
                return {"id": req_id, "ok": False, "error": BAD_TOKEN}
            self._authed = True
            # macOS: no App Nap while the command runs (7.5-14x slower when Designer is hidden).
            tok = activity.begin(req.get("cmd"))
            try:
                result = self._dispatch(req.get("cmd"), req.get("args") or {})
            finally:
                activity.end(tok)
            return {"id": req_id, "ok": True, "result": result}
        except BaseException as e:
            # Always answer. The sd API raises APIException, which derives from
            # BaseException; letting it escape left the client waiting until timeout.
            reply = {"id": req_id, "ok": False, "error": "%s: %s" % (type(e).__name__, e)}
            if self._authed:  # tracebacks show local paths: only for clients with the token
                reply["traceback"] = traceback.format_exc()
            return reply

    def _send(self, c, payload):
        if c.closed:
            return
        try:
            data = (json.dumps(payload, default=str) + "\n").encode("utf-8")
            c.sock.settimeout(30)
            c.sock.sendall(data, SEND_FLAGS)
            c.sock.setblocking(False)
        except Exception:
            self._drop(c)

    def _drop(self, c):
        c.closed = True
        try:
            c.sock.close()
        except OSError:
            pass
        if c in self._clients:
            self._clients.remove(c)
