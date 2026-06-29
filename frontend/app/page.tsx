"use client";

import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");
const MAX_FILE_BYTES = 25 * 1024 * 1024;
const MAX_FILES = 100;
const CONCURRENCY = 3;

type ConversionResult = {
  filename: string;
  markdown: string;
  page_count: number;
};

type BatchStatus = "queued" | "converting" | "done" | "error";

type BatchItem = {
  id: string;
  file: File;
  relativePath: string;
  status: BatchStatus;
  result?: ConversionResult;
  error?: string;
};

function fileSize(bytes: number) {
  return bytes < 1024 * 1024
    ? `${Math.ceil(bytes / 1024)} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function markdownPath(item: BatchItem) {
  const path = item.relativePath || item.file.name;
  return path.replace(/\.pdf$/i, ".md");
}

export default function Home() {
  const filesInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<BatchItem[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [zipping, setZipping] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [view, setView] = useState<"preview" | "source">("preview");

  useEffect(() => {
    folderInputRef.current?.setAttribute("webkitdirectory", "");
  }, []);

  const activeItem = useMemo(
    () => items.find((item) => item.id === activeId && item.result) ?? null,
    [activeId, items],
  );
  const completed = items.filter((item) => item.status === "done").length;
  const failed = items.filter((item) => item.status === "error").length;
  const processed = completed + failed;

  function addFiles(fileList?: FileList | File[]) {
    if (!fileList) return;
    setError("");
    setActiveId(null);
    setView("preview");

    const incoming = Array.from(fileList);
    const pdfs = incoming.filter(
      (file) =>
        file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"),
    );
    const valid = pdfs.filter(
      (file) => file.size > 0 && file.size <= MAX_FILE_BYTES,
    );
    const oversized = pdfs.length - valid.length;
    const skipped = incoming.length - pdfs.length;
    const limited = valid.slice(0, MAX_FILES);

    if (!limited.length) {
      setItems([]);
      setError(
        pdfs.length
          ? "No usable PDFs found. Each file must be non-empty and no larger than 25 MB."
          : "No PDF files were found in that selection.",
      );
      return;
    }

    const nextItems = limited.map((file, index) => {
      const relativePath =
        (file as File & { webkitRelativePath?: string }).webkitRelativePath ||
        file.name;
      return {
        id: `${relativePath}-${file.size}-${file.lastModified}-${index}`,
        file,
        relativePath,
        status: "queued" as const,
      };
    });
    setItems(nextItems);

    const notices = [
      skipped ? `${skipped} non-PDF file${skipped === 1 ? "" : "s"} skipped.` : "",
      oversized
        ? `${oversized} empty or oversized PDF${oversized === 1 ? "" : "s"} skipped.`
        : "",
      valid.length > MAX_FILES
        ? `Only the first ${MAX_FILES} PDFs were added.`
        : "",
    ].filter(Boolean);
    setError(notices.join(" "));
  }

  function onFileInput(event: ChangeEvent<HTMLInputElement>) {
    addFiles(event.target.files ?? undefined);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    addFiles(event.dataTransfer.files);
  }

  async function convertOne(item: BatchItem): Promise<ConversionResult> {
    const body = new FormData();
    body.append("file", item.file);
    const response = await fetch(`${API_URL}/convert`, { method: "POST", body });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(data?.detail ?? "The PDF could not be converted.");
    }
    return data as ConversionResult;
  }

  async function convertAll() {
    if (!items.length || loading) return;
    setLoading(true);
    setError("");
    setActiveId(null);

    const batch = items.map((item) => ({
      ...item,
      status: "queued" as const,
      result: undefined,
      error: undefined,
    }));
    setItems(batch);

    let cursor = 0;
    const successfulIds: string[] = [];

    async function worker() {
      while (cursor < batch.length) {
        const index = cursor++;
        const item = batch[index];
        setItems((current) =>
          current.map((entry) =>
            entry.id === item.id ? { ...entry, status: "converting" } : entry,
          ),
        );

        try {
          const result = await convertOne(item);
          successfulIds.push(item.id);
          setItems((current) =>
            current.map((entry) =>
              entry.id === item.id
                ? { ...entry, status: "done", result, error: undefined }
                : entry,
            ),
          );
          setActiveId((current) => current ?? item.id);
        } catch (caught) {
          const message =
            caught instanceof TypeError
              ? "Could not reach the local converter."
              : caught instanceof Error
                ? caught.message
                : "Conversion failed.";
          setItems((current) =>
            current.map((entry) =>
              entry.id === item.id
                ? { ...entry, status: "error", error: message }
                : entry,
            ),
          );
        }
      }
    }

    await Promise.all(
      Array.from({ length: Math.min(CONCURRENCY, batch.length) }, () => worker()),
    );
    if (!successfulIds.length) {
      setError("None of the selected PDFs could be converted.");
    }
    setLoading(false);
  }

  function downloadOne(item: BatchItem) {
    if (!item.result) return;
    downloadBlob(
      new Blob([item.result.markdown], { type: "text/markdown;charset=utf-8" }),
      markdownPath(item).split("/").pop() ?? item.result.filename,
    );
  }

  async function downloadAll() {
    const ready = items.filter((item) => item.result);
    if (!ready.length || zipping) return;
    setZipping(true);
    try {
      const JSZip = (await import("jszip")).default;
      const zip = new JSZip();
      ready.forEach((item) => zip.file(markdownPath(item), item.result!.markdown));
      const blob = await zip.generateAsync({
        type: "blob",
        compression: "DEFLATE",
        compressionOptions: { level: 6 },
      });
      downloadBlob(blob, "paperdown-markdown.zip");
    } finally {
      setZipping(false);
    }
  }

  function reset() {
    setItems([]);
    setActiveId(null);
    setError("");
    setView("preview");
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="/" aria-label="Paperdown home">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>Paperdown</span>
        </a>
        <span className="local-pill">
          <span className="status-dot" /> Runs locally
        </span>
      </header>

      <section className="hero">
        <p className="eyebrow">PDF → MARKDOWN</p>
        <h1>Turn documents into<br />clean Markdown.</h1>
        <p className="lede">
          Drop in one PDF or a whole folder. Convert up to 100 documents in one
          local batch—with headings, lists, and page markers preserved.
        </p>
      </section>

      <section className="workspace" aria-label="PDF converter">
        <div className="upload-column">
          <div
            className={`dropzone ${dragging ? "dragging" : ""} ${items.length ? "has-file" : ""}`}
            onDragEnter={() => setDragging(true)}
            onDragLeave={() => setDragging(false)}
            onDragOver={(event) => event.preventDefault()}
            onDrop={onDrop}
          >
            <input
              ref={filesInputRef}
              type="file"
              accept=".pdf,application/pdf"
              multiple
              onChange={onFileInput}
              hidden
            />
            <input
              ref={folderInputRef}
              type="file"
              multiple
              onChange={onFileInput}
              hidden
            />
            <div className="document-icon stack" aria-hidden="true">
              <span>PDF</span>
            </div>
            {items.length ? (
              <>
                <h2>{items.length} PDF{items.length === 1 ? "" : "s"} ready</h2>
                <p>{fileSize(items.reduce((total, item) => total + item.file.size, 0))} selected</p>
              </>
            ) : (
              <>
                <h2>Drop your PDFs here</h2>
                <p>Select files or choose an entire folder</p>
              </>
            )}
            <div className="picker-buttons">
              <button
                className="secondary-button"
                onClick={() => filesInputRef.current?.click()}
                disabled={loading}
              >
                Choose PDFs
              </button>
              <button
                className="secondary-button folder-button"
                onClick={() => folderInputRef.current?.click()}
                disabled={loading}
              >
                Choose folder
              </button>
            </div>
            <span className="limit">Up to 100 PDFs · 25 MB and 200 pages per file</span>
          </div>

          {items.length ? (
            <div className="file-queue" aria-label="Selected PDFs">
              <div className="queue-header">
                <span>FILES</span>
                {!loading ? <button className="text-button" onClick={reset}>Clear</button> : null}
              </div>
              <div className="queue-list">
                {items.map((item) => (
                  <button
                    key={item.id}
                    className={`queue-item ${activeId === item.id ? "active" : ""}`}
                    onClick={() => item.result && setActiveId(item.id)}
                    disabled={!item.result}
                    title={item.error ?? item.relativePath}
                  >
                    <span className={`file-status ${item.status}`}>
                      {item.status === "done" ? "✓" : item.status === "error" ? "!" : ""}
                    </span>
                    <span className="file-info">
                      <strong>{item.file.name}</strong>
                      <small>
                        {item.status === "queued" && fileSize(item.file.size)}
                        {item.status === "converting" && "Converting…"}
                        {item.status === "done" && `${item.result?.page_count} pages · Ready`}
                        {item.status === "error" && item.error}
                      </small>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <button
            className="primary-button"
            disabled={!items.length || loading}
            onClick={convertAll}
          >
            {loading ? <span className="spinner" aria-hidden="true" /> : null}
            {loading
              ? `Converting ${processed} of ${items.length}…`
              : `Convert ${items.length || ""} PDF${items.length === 1 ? "" : "s"}`}
            {!loading ? <span aria-hidden="true">→</span> : null}
          </button>

          {error ? <div className="error" role="alert">{error}</div> : null}

          <div className="privacy-note">
            <span aria-hidden="true">⌂</span>
            <div>
              <strong>Your files stay on your machine.</strong>
              <p>Three files convert at a time to keep large batches stable.</p>
            </div>
          </div>
        </div>

        <div className={`preview-panel ${activeItem ? "populated" : ""}`}>
          <div className="preview-toolbar">
            <div className="preview-title">
              <span className="preview-label">MARKDOWN</span>
              {activeItem ? (
                <span className="page-count">
                  {activeItem.file.name} · {activeItem.result?.page_count} pages
                </span>
              ) : null}
            </div>
            {activeItem ? (
              <div className="toolbar-actions">
                <div className="view-toggle">
                  <button className={view === "preview" ? "active" : ""} onClick={() => setView("preview")}>
                    Preview
                  </button>
                  <button className={view === "source" ? "active" : ""} onClick={() => setView("source")}>
                    Source
                  </button>
                </div>
                <button className="download-button" onClick={() => downloadOne(activeItem)}>
                  Download .md
                </button>
              </div>
            ) : null}
          </div>

          <div className="preview-body">
            {activeItem?.result ? (
              view === "preview" ? (
                <article className="markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {activeItem.result.markdown}
                  </ReactMarkdown>
                </article>
              ) : (
                <pre className="source">{activeItem.result.markdown}</pre>
              )
            ) : (
              <div className="empty-preview">
                <div className="empty-lines" aria-hidden="true">
                  <span /><span /><span /><span /><span />
                </div>
                <p>
                  {loading
                    ? "Your first converted file will appear here."
                    : "Select PDFs, convert them, then preview any result here."}
                </p>
              </div>
            )}
          </div>

          {completed ? (
            <div className="result-footer">
              <span>
                {completed} converted{failed ? ` · ${failed} failed` : ""}
              </span>
              <button className="download-all-button" onClick={downloadAll} disabled={zipping}>
                {zipping ? "Preparing ZIP…" : `Download all ${completed} as ZIP`}
              </button>
            </div>
          ) : null}
        </div>
      </section>

      <footer>Built for quiet, local workflows. No accounts. No tracking.</footer>
    </main>
  );
}
