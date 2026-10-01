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
    from PySide2 import QtCore
except ImportError:  # newer Designer builds
    from PySide6 import QtCore

LOG = "[Claude bridge]"
DEFAULT_PORT = 9881
PORT_ATTEMPTS = 10
MAX_REQUEST_BYTES = 16 * 1024 * 1024
POLL_MS = 25


def session_dir():
    return os.path.join(os.path.expanduser("~"), ".sd_claude_bridge")


def session_path():
    return os.environ.get("SD_CLAUDE_BRIDGE_SESSION") or os.path.join(
        session_dir(), "session.json"
    )


class _Client(object):
    __slots__ = ("sock", "buf", "closed")

    def __init__(self, sock):
        self.sock = sock
        self.buf = b""
        self.closed = False


class BridgeServer(object):
    def __init__(self, dispatch, version):
        self._dispatch = dispatch
        self._version = version
        self._sock = None
        self._clients = []
        self._timer = None
        self._busy = False
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
        if not os.path.isdir(folder):
            os.makedirs(folder)
        data = {
            "port": self.port,
            "token": self.token,
            "pid": os.getpid(),
            "bridge_version": self._version,
            "python": sys.version.split()[0],
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)

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
        if self._busy or self._sock is None:
            return
        self._busy = True
        try:
            self._accept()
            for c in list(self._clients):
                self._service(c)
        except Exception:
            print("%s poll error:\n%s" % (LOG, traceback.format_exc()))
        finally:
            self._busy = False

    def _accept(self):
        while True:
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
        while True:
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
            if len(c.buf) > MAX_REQUEST_BYTES and b"\n" not in c.buf:
                self._send(c, {"id": None, "ok": False, "error": "request too large"})
                self._drop(c)
                return

        while b"\n" in c.buf and not c.closed:
            line, c.buf = c.buf.split(b"\n", 1)
            if line.strip():
                self._send(c, self._handle(line))

        if eof:
            self._drop(c)

    def _handle(self, line):
        req_id = None
        try:
            req = json.loads(line.decode("utf-8"))
            req_id = req.get("id")
            token = str(req.get("token", ""))
            if not hmac.compare_digest(token.encode("utf-8"), self.token.encode("utf-8")):
                return {
                    "id": req_id,
                    "ok": False,
                    "error": "bad token (session file is stale; restart the MCP server or Designer)",
                }
            result = self._dispatch(req.get("cmd"), req.get("args") or {})
            return {"id": req_id, "ok": True, "result": result}
        except BaseException as e:
            # Always answer. The sd API raises APIException, which derives from
            # BaseException; letting it escape left the client waiting until timeout.
            return {
                "id": req_id,
                "ok": False,
                "error": "%s: %s" % (type(e).__name__, e),
                "traceback": traceback.format_exc(),
            }

    def _send(self, c, payload):
        if c.closed:
            return
        try:
            data = (json.dumps(payload, default=str) + "\n").encode("utf-8")
            c.sock.settimeout(30)
            c.sock.sendall(data)
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
