"""FastAPI entry point for the local PDF to Markdown service."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .converter import EmptyPDFError, pdf_to_markdown


MAX_FILE_SIZE = 25 * 1024 * 1024
MAX_PAGES = 200
CHUNK_SIZE = 1024 * 1024

app = FastAPI(title="Local PDF to Markdown", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ConversionResponse(BaseModel):
    filename: str
    markdown: str
    page_count: int


def _markdown_filename(filename: str | None) -> str:
    original = filename or "document.pdf"
    base = re.sub(r"\.pdf$", "", original, flags=re.IGNORECASE).strip()
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base) or "document"
    return f"{base}.md"


async def _read_limited(upload: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(CHUNK_SIZE):
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="PDF is too large. The maximum file size is 25 MB.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/convert", response_model=ConversionResponse)
async def convert_pdf(file: UploadFile = File(...)) -> ConversionResponse:
    filename = file.filename or ""
    content_type = (file.content_type or "").lower()
    if not filename.lower().endswith(".pdf") and content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    try:
        content = await _read_limited(file)
    finally:
        await file.close()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

    try:
        document = fitz.open(stream=content, filetype="pdf")
    except (fitz.FileDataError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=400, detail="The PDF is damaged or cannot be opened."
        ) from exc

    try:
        if document.needs_pass:
            raise HTTPException(
                status_code=400, detail="Password-protected PDFs are not supported."
            )
        if document.page_count == 0:
            raise HTTPException(status_code=400, detail="The PDF contains no pages.")
        if document.page_count > MAX_PAGES:
            raise HTTPException(
                status_code=413,
                detail=f"PDF has too many pages. The maximum is {MAX_PAGES} pages.",
            )

        markdown = pdf_to_markdown(document)
        return ConversionResponse(
            filename=_markdown_filename(filename),
            markdown=markdown,
            page_count=document.page_count,
        )
    except EmptyPDFError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        document.close()


def _frontend_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "frontend-out"
    return Path(__file__).resolve().parents[2] / "frontend" / "out"


FRONTEND_DIRECTORY = _frontend_directory()
if FRONTEND_DIRECTORY.is_dir():
    next_assets = FRONTEND_DIRECTORY / "_next"
    if next_assets.is_dir():
        app.mount("/_next", StaticFiles(directory=next_assets), name="next-assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def desktop_frontend(path: str) -> FileResponse:
        requested = (FRONTEND_DIRECTORY / path).resolve()
        try:
            requested.relative_to(FRONTEND_DIRECTORY.resolve())
        except ValueError:
            requested = FRONTEND_DIRECTORY / "index.html"

        if requested.is_dir():
            requested = requested / "index.html"
        if not requested.is_file():
            requested = FRONTEND_DIRECTORY / "index.html"
        return FileResponse(requested)
