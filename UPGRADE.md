# Upgrade to Paperdown 1.1.0

This update keeps pictures and charts when converting PDFs to Markdown.
Download the installer for your computer from:
https://github.com/tech-supremo/paperdown/releases/tag/v1.1.0

## Already using Paperdown?

There is no separate patch or automatic updater. Install the new version over
the previous one. You do not need Python, Node.js, Terminal or a new account.
Paperdown does not keep a document library or conversion history. PDFs and
Markdown or ZIP files you already saved stay where you put them.

### Mac

1. Quit Paperdown completely.
2. Download and open `Paperdown-macOS.dmg`.
3. Drag Paperdown into Applications. Choose **Replace** when asked.
4. Open the app from Applications. If macOS shows an unsigned-app warning,
   right-click the app and choose **Open**. Your Mac may require approval in
   System Settings > Privacy & Security.
5. Convert a PDF containing a picture. The result should show images and offer
   **Download ZIP with images**.

### Windows

1. Close Paperdown.
2. Download and run `Paperdown-Windows-Setup.exe`.
3. Install to the same location as your existing copy. The installer keeps the
   same application identity and replaces the executable.
4. Open Paperdown and convert a PDF containing a picture. The result should
   show images and offer **Download ZIP with images**.

Both installers remain unsigned. Windows may show a SmartScreen warning.

## Working with the converted files

Extract the downloaded ZIP before opening its Markdown file. Keep the `images`
folder beside that file so the images display in your Markdown reader.
Batch downloads put each PDF's result in its own folder.

Drawn charts and diagrams are preserved in full-page visual references. These
can repeat text from the page. Scanned pages stay as images, without searchable
text. This release does not include OCR or AI descriptions of graphics.

## Check your download

`SHA256SUMS.txt` lists the SHA-256 hashes for both installers. These let you check
file integrity. They do not replace code signing.
