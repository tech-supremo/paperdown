from app.desktop_utils import safe_archive_path


def test_safe_archive_path_preserves_folders() -> None:
    assert safe_archive_path("reports/june/file.md") == "reports/june/file.md"


def test_safe_archive_path_removes_traversal() -> None:
    assert safe_archive_path("../../private/file.md") == "private/file.md"
    assert safe_archive_path("") == "document.md"
