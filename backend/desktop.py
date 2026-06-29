"""Native desktop launcher for packaged Paperdown builds."""

from __future__ import annotations

import socket
import threading
import time
import urllib.request

import uvicorn
import webview

from app.main import app


def _available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, attempts: int = 100) -> None:
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=0.25):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("Paperdown's local service did not start.")


def main() -> None:
    port = _available_port()
    url = f"http://127.0.0.1:{port}"
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    _wait_until_ready(url)

    window = webview.create_window(
        "Paperdown — PDF to Markdown",
        url,
        width=1240,
        height=820,
        min_size=(900, 650),
        text_select=True,
    )

    def stop_server() -> None:
        server.should_exit = True

    window.events.closed += stop_server
    webview.start()
    server.should_exit = True
    server_thread.join(timeout=3)


if __name__ == "__main__":
    main()
