# Paperdown — Local PDF to Markdown

Paperdown is a fully local PDF-to-Markdown web app. The browser sends one PDF
to a FastAPI server running on your machine. PyMuPDF extracts the text and basic
font metadata, then the backend turns it into readable Markdown.

No paid API, cloud account, or external processing is required.

## Desktop installers

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
- Text extraction using PyMuPDF
- Heading detection based on relative font size and bold weight
- Preservation of common bullet and numbered-list markers
- `<!-- Page N -->` comments between every source page
- Rendered Markdown preview and raw-source view
- One-click `.md` download
- Friendly errors for invalid, empty, image-only, password-protected, oversized,
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
python -m pip install pytest
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
Scanned/image-only PDFs need OCR, which this app intentionally does not perform.
Tables, multi-column documents, and unusual typography may need light cleanup in
the downloaded Markdown.

## Local-only notes

- Files are processed in memory and are not stored by the backend.
- The frontend only connects to the local FastAPI URL.
- CORS is restricted to the standard local frontend addresses.
- To change the file or page limits, edit `MAX_FILE_SIZE` and `MAX_PAGES` in
  `backend/app/main.py`, then update the matching UI text in
  `frontend/app/page.tsx`.
