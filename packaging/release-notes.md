## Pictures and charts now stay with your Markdown

- Embedded pictures appear near the extracted text.
- Pages containing drawn charts, diagrams or tables include a full-page visual reference.
- The preview displays graphics locally.
- Downloads include the Markdown and images in a ZIP. Text-only PDFs still download as `.md` files.
- Scanned pages are preserved as images. OCR and AI image descriptions are not included.

## Updating an existing installation

There is no separate patch installer. Quit Paperdown and install this version over your existing copy.

**Mac:** Open `Paperdown-macOS.dmg`, drag Paperdown into Applications and choose **Replace**.

**Windows:** Run `Paperdown-Windows-Setup.exe` and use the same install location.

Your saved PDFs, Markdown files and ZIPs remain in place. See the attached `UPGRADE.md` for full steps.

## Limits

Vector graphics use a full-page snapshot, which can repeat text or include decorative lines. PNG images are limited to 1,600 pixels on the longest side. Graphics bundles are limited to 32 MB or 1,000 images per PDF.

Both installers are unsigned, as in previous versions. macOS or Windows may show a security warning. `SHA256SUMS.txt` contains installer hashes.
