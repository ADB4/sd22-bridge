"""Claude bridge plugin for Adobe Substance 3D Designer.

Target: Designer 2022 (12.x). Written to run on the Python bundled with
Designer 12.0 and later (3.7+), with no third-party packages.

When Designer loads this plugin it opens a TCP server on 127.0.0.1 that the
companion MCP server (sd_designer_mcp.py) connects to. Every request is
executed on Designer's main thread, so the sd API is safe to call.
"""

import traceback

VERSION = "1.0.0"

_server = None


def initializeSDPlugin():
    """Designer entry point: start the bridge."""
    global _server
    if _server is not None:
        # Loaded twice: stop the old server so its port and timer don't linger.
        uninitializeSDPlugin()
    try:
        from .bridge import BridgeServer
        from .commands import dispatch

        _server = BridgeServer(dispatch, VERSION)
        _server.start()
    except Exception:
        print("[Claude bridge] failed to start:\n" + traceback.format_exc())
        _server = None


def uninitializeSDPlugin():
    """Designer exit point: close sockets and remove the session file."""
    global _server
    if _server is not None:
        try:
            _server.stop()
        except Exception:
            traceback.print_exc()
        _server = None
