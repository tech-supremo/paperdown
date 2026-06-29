import fitz
import pytest

from app.converter import EmptyPDFError, pdf_to_markdown


def test_converts_pages_headings_and_lists() -> None:
    document = fitz.open()
    first = document.new_page()
    first.insert_text((72, 72), "Project Guide", fontsize=22)
    first.insert_text((72, 110), "Introduction", fontsize=16)
    first.insert_text((72, 140), "A short paragraph.", fontsize=11)
    first.insert_text((72, 165), "• First item", fontsize=11)
    first.insert_text((72, 185), "2. Second item", fontsize=11)
    second = document.new_page()
    second.insert_text((72, 72), "Second page text.", fontsize=11)

    markdown = pdf_to_markdown(document)

    assert "<!-- Page 1 -->" in markdown
    assert "<!-- Page 2 -->" in markdown
    assert "# Project Guide" in markdown
    assert "## Introduction" in markdown
    assert "- First item" in markdown
    assert "2. Second item" in markdown


def test_rejects_pdf_without_extractable_text() -> None:
    document = fitz.open()
    document.new_page()

    with pytest.raises(EmptyPDFError):
        pdf_to_markdown(document)
