"""PDF text extraction and lightweight Markdown conversion."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

import fitz


LIST_MARKER = re.compile(
    r"^\s*(?P<marker>(?:[\u00B7\u2022\u2023\u25E6\u2043\u2219\u25AA\u25CF\u25CB\u2013\u2014\-*])|(?:\d{1,3}[.)]))\s+(?P<text>.+)$"
)
NUMBERED_MARKER = re.compile(r"^\d{1,3}[.)]$")
WHITESPACE = re.compile(r"[ \t]+")


class EmptyPDFError(ValueError):
    """Raised when a PDF has no usable text."""


@dataclass(frozen=True)
class Line:
    text: str
    size: float
    is_bold: bool
    y: float


def _clean_inline_text(text: str) -> str:
    """Normalize whitespace and escape Markdown syntax that changes meaning."""
    normalized = WHITESPACE.sub(" ", text).strip()
    return normalized.replace("\\", "\\\\")


def _extract_lines(page: fitz.Page) -> list[Line]:
    """Return positioned text lines, preserving basic font information."""
    page_data = page.get_text("dict", sort=True)
    lines: list[Line] = []

    for block in page_data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for raw_line in block.get("lines", []):
            spans = raw_line.get("spans", [])
            if not spans:
                continue
            text = "".join(span.get("text", "") for span in spans)
            text = _clean_inline_text(text)
            if not text:
                continue
            sizes = [
                float(span.get("size", 0))
                for span in spans
                if span.get("text", "").strip()
            ]
            size = max(sizes, default=0.0)
            is_bold = any(
                "bold" in str(span.get("font", "")).lower()
                for span in spans
                if span.get("text", "").strip()
            )
            bbox = raw_line.get("bbox", (0, 0, 0, 0))
            lines.append(Line(text=text, size=size, is_bold=is_bold, y=float(bbox[1])))

    return lines


def _body_font_size(pages: list[list[Line]]) -> float:
    """Estimate body size from the most common rounded span size."""
    sizes = [
        round(line.size, 1)
        for page in pages
        for line in page
        if line.size > 0 and len(line.text) > 1
    ]
    if not sizes:
        return 11.0

    frequency: dict[float, int] = {}
    for size in sizes:
        frequency[size] = frequency.get(size, 0) + 1
    most_common_count = max(frequency.values())
    candidates = [size for size, count in frequency.items() if count == most_common_count]
    return statistics.median(candidates)


def _heading_level(line: Line, body_size: float) -> int | None:
    """Infer a Markdown heading level from font size and weight."""
    text = line.text
    if len(text) > 140 or LIST_MARKER.match(text):
        return None

    ratio = line.size / body_size if body_size else 1
    if ratio >= 1.65:
        return 1
    if ratio >= 1.35:
        return 2
    if ratio >= 1.15 and (line.is_bold or len(text) <= 80):
        return 3
    if line.is_bold and ratio >= 1.02 and len(text) <= 70:
        return 4
    return None


def _as_list_item(text: str) -> str | None:
    match = LIST_MARKER.match(text)
    if not match:
        return None
    marker = match.group("marker")
    content = match.group("text").strip()
    if NUMBERED_MARKER.match(marker):
        number = re.match(r"\d+", marker)
        return f"{number.group(0) if number else '1'}. {content}"
    return f"- {content}"


def _looks_like_sentence_continuation(previous: str, current: str) -> bool:
    if not previous or previous.startswith(("#", "-", ">")):
        return False
    if re.match(r"^\d+\.\s", previous):
        return False
    if previous.endswith((".", "!", "?", ":", ";")):
        return False
    return bool(current) and (current[0].islower() or previous.endswith("-"))


def _page_to_markdown(lines: list[Line], body_size: float) -> list[str]:
    output: list[str] = []

    for line in lines:
        heading = _heading_level(line, body_size)
        list_item = _as_list_item(line.text)

        if heading:
            output.extend([f"{'#' * heading} {line.text}", ""])
            continue
        if list_item:
            output.append(list_item)
            continue

        if output and _looks_like_sentence_continuation(output[-1], line.text):
            if output[-1].endswith("-"):
                output[-1] = output[-1][:-1] + line.text
            else:
                output[-1] += f" {line.text}"
        else:
            if output and output[-1] and (
                output[-1].startswith("- ") or re.match(r"^\d+\.\s", output[-1])
            ):
                output.append("")
            output.append(line.text)

    while output and not output[-1]:
        output.pop()
    return output


def pdf_to_markdown(document: fitz.Document) -> str:
    """Convert an open PDF document to Markdown with page comments."""
    pages = [_extract_lines(page) for page in document]
    if not any(pages):
        raise EmptyPDFError(
            "This PDF contains no extractable text. It may be empty or image-only."
        )

    body_size = _body_font_size(pages)
    sections: list[str] = []
    for page_number, lines in enumerate(pages, start=1):
        page_lines = _page_to_markdown(lines, body_size)
        page_content = "\n".join(page_lines).strip()
        marker = f"<!-- Page {page_number} -->"
        sections.append(f"{marker}\n\n{page_content}" if page_content else marker)

    return "\n\n".join(sections).strip() + "\n"
