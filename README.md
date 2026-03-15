# Offline Document Finder (ODF)

> **"Search Like You Think"** — A local-first, AI-powered semantic document search engine for Windows.

ODF replaces traditional keyword-based file search with a hybrid semantic retrieval system. It understands the *concepts* inside your documents, not just their filenames — so you can find a file called `Q3_Strategy_v2.pdf` by searching *"marketing campaign planning"*.

All processing happens on-device. No cloud. No telemetry. No internet required.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Architecture](#architecture)
- [Search Pipeline](#search-pipeline)
- [Indexing Pipeline](#indexing-pipeline)
- [Tech Stack](#tech-stack)
- [Privacy & Data Storage](#privacy--data-storage)
- [Getting Started](#getting-started)
- [Building the Executable](#building-the-executable)
- [Supported File Types](#supported-file-types)

---

## Problem Statement

Standard OS file search (`Windows Search`, `Spotlight`) operates on **exact keyword matching**. If a document is named `2023_Financial_Review.pdf` and you search for `"budget report"`, it returns nothing.

This is a fundamental limitation — users rarely remember exact filenames. They remember *what the document was about*.

ODF addresses this by indexing the semantic content of every document. A query is matched against the meaning of the text, not just its surface characters.

---

## Architecture

ODF is structured as a three-layer desktop application:

```
┌──────────────────────────────────────────────────────────────┐
│                        UI Layer                              │
│          CustomTkinter overlay — borderless, always-on-top   │
│          Global hotkey (Ctrl+K), debounced search, animated  │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     Engine Layer                             │
│   VectorSearch  ←→  Embedder (FastEmbed / ONNX)             │
│   FileIndexer   ←→  ThreadPoolExecutor (8 workers)          │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     Storage Layer                            │
│   ChromaDB (SQLite-backed) — persistent, local, no server   │
│   data/chroma_db/   (script mode)                           │
│   %APPDATA%/ODF/    (executable mode)                       │
└──────────────────────────────────────────────────────────────┘
```

### UI Layer

- **Framework**: CustomTkinter (modern Tkinter wrapper)
- **Window style**: Borderless overlay (`overrideredirect=True`), always-on-top, draggable
- **Theme**: Ultra-dark (`#1c1c1e` background, `#0A84FF` accent)
- **Global hotkey**: `Ctrl+K` registered at OS level via `keyboard` library
- **Search behavior**: 280ms debounce on input, results rendered on daemon thread, UI updated via `root.after()`
- **Navigation**: Arrow keys to move between results, `Enter` to open, `Escape` to dismiss
- **Animation**: Smooth height transition between idle (102px) and expanded state (~380px)

### Engine Layer

- **Embedder**: FastEmbed + `BAAI/bge-small-en-v1.5` — ONNX runtime, no PyTorch dependency, 384-dimensional output
- **VectorSearch**: ChromaDB collection with cosine similarity, hybrid re-ranking on top of vector retrieval
- **FileIndexer**: Parallel document scanner — 8 worker threads, MD5-based deduplication, multi-encoding text fallback

### Storage Layer

- **Backend**: ChromaDB 0.4.22+ (embedded SQLite, no external server)
- **Document IDs**: `{md5(filepath + mtime)}_chunk_{index}` — deterministic, supports incremental re-indexing
- **Metadata per chunk**: `source`, `filename`, `modified`, `size`, `type`, `chunk_index`

---

## Search Pipeline

```
User query (≥ 2 chars)
        │
        ▼
  280ms debounce
        │
        ▼
  Embedder.embed_text()  →  384-dim vector
        │
        ▼
  ChromaDB.query(n_results=30)  →  top-30 candidates (3× overfetch)
        │
        ▼
  Hybrid re-ranking:
    base_score  = 1 - cosine_distance
    title_boost = +0.25  if query ⊆ filename
    body_boost  = +0.15  if query ⊆ chunk_text
    final_score = min(base_score + boosts, 1.0)
        │
        ▼
  Sort by final_score, return top 8–10 results
        │
        ▼
  UI renders results  →  first result auto-selected
```

The overfetch (30 candidates for top-10 results) ensures keyword-exact matches that might rank lower under pure cosine distance still surface after boosting. This handles both semantic queries ("invoices from last year") and exact lookups ("INV-2024-001") robustly.

---

## Indexing Pipeline

```
User selects folder
        │
        ▼
  FileIndexer.scan_directory()
    - Recursively walks directory tree
    - Skips hidden folders, venv, __pycache__, system paths
    - Collects .pdf, .docx, .txt paths
        │
        ▼
  Deduplication check
    - Computes MD5(filepath + mtime) per file
    - Skips files already present in ChromaDB
        │
        ▼
  ThreadPoolExecutor (8 workers) — parallel extraction
    PDF   →  pdfminer.six
    DOCX  →  python-docx (paragraphs + tables)
    TXT   →  UTF-8 / UTF-16 / Latin-1 / CP1252 fallback chain
        │
        ▼
  Text cleaning
    - Compress whitespace
    - Strip null bytes and control characters
    - Cap at 100,000 characters per document
        │
        ▼
  VectorSearch.add_documents()
    - Split into chunks (1000 chars, 100 char overlap)
    - Batch embed via FastEmbed (batch size = 32)
    - Upsert to ChromaDB in batches of 100
        │
        ▼
  Progress reported to UI (throttled every 5 documents)
```

---

## Tech Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| UI framework | CustomTkinter | Modern Tkinter, dark theme, native feel |
| Vector database | ChromaDB 0.4.22+ | SQLite-backed, embedded, no server |
| Embedding model | BAAI/bge-small-en-v1.5 | 384-dim, ONNX, ~130MB |
| Inference runtime | FastEmbed | ONNX Runtime, no PyTorch required |
| PDF extraction | pdfminer.six | Layout-aware text extraction |
| DOCX extraction | python-docx | Paragraphs + table cells |
| Global hotkey | keyboard | OS-level key capture |
| Packaging | PyInstaller | Single `.exe`, model bundled |
| Concurrency | ThreadPoolExecutor | 8 workers for parallel indexing |

---

## Privacy & Data Storage

- **Fully offline**: No network calls at runtime. The embedding model is bundled inside the executable.
- **Local storage only**: All vectors and metadata are stored in `data/chroma_db/` (script mode) or `%APPDATA%\ODF\data\chroma_db\` (exe mode).
- **No telemetry**: Nothing leaves the machine.
- **Data portability**: Delete the `chroma_db/` directory to wipe the index entirely.

---

## Download

A pre-built Windows executable is available — no Python installation required.

**[Download ODF.exe](https://drive.google.com/file/d/1-HyNhxTyl6uBrq5v6ctnsE8-KGoGbbu7/view)**

> First launch takes 20–30 seconds while the executable extracts its bundled dependencies. Subsequent launches are faster.

---

## Getting Started

**Prerequisites**: Python 3.9+, Windows 10/11

```bash
# 1. Clone the repository
git clone <repo-url>
cd ODF

# 2. Create and activate virtual environment
python -m venv odf_env
odf_env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

**First launch**: A setup dialog will prompt you to index a folder. Click **Index Folder**, select a directory, and wait for indexing to complete. After that, press `Ctrl+K` anywhere to open the search overlay.

---

## Building the Executable

Produces a single `dist/ODF.exe` with all dependencies and the AI model bundled.

```bash
python build_exe.py
```

The build script will:
1. Download and cache the embedding model locally under `models/`
2. Clean previous `dist/` and `build/` artifacts
3. Run PyInstaller with `--onefile --windowed` and the appropriate `--add-data` and `--collect-all` flags

The resulting executable requires no Python installation on the target machine. First launch takes 20–30 seconds for extraction; subsequent launches are faster.

---

## Supported File Types

| Extension | Parser |
|-----------|--------|
| `.pdf` | pdfminer.six |
| `.docx` | python-docx |
| `.txt` | Built-in (multi-encoding) |

---

*Built by Parimal Kalpande and Krunal Wankhade.*
