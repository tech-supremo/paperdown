# Paperdown — Local PDF to Markdown

Paperdown is a fully local PDF-to-Markdown web app. The browser sends one PDF
to a FastAPI server running on your machine. PyMuPDF extracts the text and basic
font metadata, then the backend turns it into readable Markdown with local image files.

No paid API, cloud account, or external processing is required.

## Desktop installers

Download the latest Mac and Windows installers from [Releases](https://github.com/tech-supremo/paperdown/releases/latest).
Already installed an older version? Follow [UPGRADE.md](UPGRADE.md) to replace it.
No separate patch installer is needed.

Paperdown can also be packaged as a self-contained desktop application. People
using an installer do not need Python, Node.js, or Terminal. Closing the native
Paperdown window also stops its private localhost service.

- **macOS:** Open `Paperdown-macOS.dmg`, then drag Paperdown into Applications.
- **Windows:** Run `Paperdown-Windows-Setup.exe` and follow the installer.

The automated GitHub Actions workflow builds both installers. Open the
repository's **Actions** tab, run **Build desktop installers**, then download the
two artifacts from the completed run.

The generated installers are unsigned by default. macOS users may need to
right-click Paperdown and choose **Open** the first time. Windows may show a
SmartScreen warning. Public distribution without those warnings requires Apple
Developer ID and Windows code-signing certificates.

## Features

- Single or multi-PDF upload with drag and drop
- Whole-folder selection for batches of up to 100 PDFs
- Three-at-a-time conversion queue with per-file progress and errors
- Individual Markdown downloads or one ZIP preserving folder structure
- Embedded pictures preserved as PNG crops near the matching text
- Full-page visual references for pages with vector charts, diagrams or tables
- Markdown and images bundled in ZIP downloads, with image previews
- Text extraction using PyMuPDF
- Heading detection based on relative font size and bold weight
- Preservation of common bullet and numbered-list markers
- `<!-- Page N -->` comments between every source page
- Rendered Markdown preview and raw-source view
- One-click `.md` download
- Friendly errors for invalid, empty, password-protected, oversized,
  or very long PDFs

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer
- npm

The default limits are 25 MB and 200 pages per PDF.

## 1. Start the FastAPI backend

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is now available at `http://localhost:8000`. You can confirm it with:

```bash
curl http://localhost:8000/health
```

## 2. Start the Next.js frontend

Open a second terminal at the project root:

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and upload a PDF.

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`, so copying the
environment file is optional for the standard setup.

## Run the backend tests

With the backend virtual environment active:

```bash
cd backend
python -m pip install -r requirements-dev.txt
pytest
```

## Build an installer locally

On macOS:

```bash
bash packaging/build_macos.sh
```

The DMG is written to `outputs/Paperdown-macOS.dmg`.

On Windows, install Python 3.10+, Node.js 20+, and Inno Setup 6, then run:

```powershell
.\packaging\build_windows.ps1
```

The installer is written to `outputs\Paperdown-Windows-Setup.exe`.

## How conversion works

PyMuPDF returns each page as positioned text spans. Paperdown estimates the
document's body font size, treats larger or bold short lines as headings, and
normalizes common list markers to Markdown. It also joins obvious wrapped lines.
Every page begins with a page comment.

PDF is a visual format, so no converter can perfectly recover complex layouts.
Scanned/image-only PDFs are preserved as images. Text inside those images is not
extracted because this app does not perform OCR.
Tables, multi-column documents, and unusual typography may need light cleanup in
the downloaded Markdown.

## Local-only notes

- Files are processed in memory and are not stored by the backend.
- The frontend only connects to the local FastAPI URL.
- CORS is restricted to the standard local frontend addresses.
- To change the file or page limits, edit `MAX_FILE_SIZE` and `MAX_PAGES` in
  `backend/app/main.py`, then update the matching UI text in
  `frontend/app/page.tsx`.

## Graphics and downloads

Embedded pictures are rendered as PNG crops of their visible page regions, placed
near the extracted text in page order. PDFs with vector drawings get a full-page
visual reference after that page's text. This deliberately preserves chart labels
and context, but may repeat text and also capture decorative lines or table borders.
Complex columns and overlapping graphics may still need manual cleanup. Images
are not interpreted or described by AI.

For a document with graphics, **Download ZIP with images** includes its Markdown
and an `images/` folder. Extract the ZIP and keep that folder beside the Markdown.
Text-only files still offer a standalone `.md` download. Batch ZIPs preserve the
source folder hierarchy and give every PDF its own folder to avoid image-name
collisions. The desktop app uses its native save dialog for both formats.

PNG output is capped at 1,600 pixels on the longest side, so this is a readable
visual reference rather than a lossless export of original image files. Conversion
stops with an error if graphics exceed 32 MB or 1,000 images per PDF. Everything
runs locally and stays in memory. Existing desktop installations need a rebuilt
installer to get this feature.
