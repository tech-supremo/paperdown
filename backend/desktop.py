"""Native desktop launcher for packaged Paperdown builds."""

from __future__ import annotations

import os
import socket
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import uvicorn
import webview

from app.main import app
from app.desktop_utils import safe_archive_path


class DesktopApi:
    def __init__(self) -> None:
        self.window: Any = None

    def _save_path(self, filename: str) -> Path | None:
        if self.window is None:
            return None
        safe_name = os.path.basename(filename) or "document.md"
        selection = self.window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=safe_name,
        )
        if not selection:
            return None
        if isinstance(selection, (str, os.PathLike)):
            return Path(selection)
        return Path(selection[0])

    def save_markdown(self, filename: str, content: str) -> bool:
        destination = self._save_path(filename)
        if destination is None:
            return False
        destination.write_text(content, encoding="utf-8")
        return True

    def save_zip(self, files: list[dict[str, str]]) -> bool:
        destination = self._save_path("paperdown-markdown.zip")
        if destination is None:
            return False
        with zipfile.ZipFile(
            destination,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            for item in files:
                archive.writestr(
                    safe_archive_path(str(item.get("path", "document.md"))),
                    str(item.get("content", "")),
                )
        return True


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

    desktop_api = DesktopApi()
    window = webview.create_window(
        "Paperdown — PDF to Markdown",
        url,
        width=1240,
        height=820,
        min_size=(900, 650),
        text_select=True,
        js_api=desktop_api,
    )
    desktop_api.window = window

    def stop_server() -> None:
        server.should_exit = True

    window.events.closed += stop_server
    webview.start()
    server.should_exit = True
    server_thread.join(timeout=3)


if __name__ == "__main__":
    main()
