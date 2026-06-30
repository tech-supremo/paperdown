"""Helpers shared by the native desktop runtime."""

from pathlib import PurePosixPath


def safe_archive_path(value: str) -> str:
    parts = [
        part
        for part in PurePosixPath(value.replace("\\", "/")).parts
        if part not in ("", ".", "..", "/")
    ]
    return "/".join(parts) or "document.md"
