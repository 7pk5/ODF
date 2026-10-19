# ODF — How It Actually Works (Plain English)

This document explains everything about ODF in simple language: what it does, how to run it, what happens step by step, how fast it is, and what its limits are. No jargon where possible.

---

## What Is ODF?

ODF (Offline Document Finder) is a desktop app that lets you search your PDF and Word files using plain English — like Google, but for your own computer, completely offline.

Normal file search (Windows Explorer, Finder) only works if you remember the exact filename. ODF reads the actual content of your documents and understands meaning, so you can search things like:

- `"invoice from last quarter"` → finds billing files even if they're named `Q3_Billing_Final_v2.pdf`
- `"machine learning notes"` → finds your study materials even if the file is called `CS_Lecture_7.docx`
- `"contract renewal date"` → finds any document that talks about contract dates

Everything runs on your machine. No internet. No cloud. No data leaves your PC.

---

## Is There an EXE?

**Yes.** There are two ways to run ODF:

### Option 1 — Run from Python (for developers)
You need Python installed. This is the "raw" way.

### Option 2 — Build a standalone EXE (for anyone)
Run `build_exe.py` once and it produces `dist/ODF/` — a folder containing `ODF.exe` that you can double-click. No Python needed on the target machine. Zip the folder and share it with anyone.

> **Note:** The EXE takes 20–30 seconds to open on the very first launch. This is a one-time thing — it's extracting bundled files to a temp folder. After that, it opens much faster.

---

## How to Run It

### Method A — Python Script

**Step 1: Set up (first time only)**
```
pip install -e .
```
This installs ODF and downloads all the libraries the app needs (~500 MB total, mostly the AI model and database).

**Step 2: Run**
```
python -m odf
```

---

### Method B — Build the EXE

```
python build_exe.py
```

This takes several minutes. When done, `dist/ODF/` is your finished app. Zip that folder and share it with anyone.

---

## Step-by-Step: What Happens When You Launch

1. **App starts** — a floating dark window appears in the center of your screen (looks like macOS Spotlight).
2. **AI model loads** — in the background, it loads the BAAI/bge-small-en-v1.5 embedding model into memory. This takes 5–15 seconds on first run, faster afterwards.
3. **ChromaDB connects** — the app connects to its local database stored at `data/chroma_db/`. If it's empty, it will ask you to index a folder.
4. **Global hotkey activates** — `Ctrl+K` is now registered at the OS level. Press it anytime, even when ODF is not in focus, to show/hide the window.

---

## Step-by-Step: What Happens During Indexing

Indexing is the process of reading your files and preparing them for search. You do this once per folder, not every time you search.

**How to start:** Click the **"＋ Index Folder"** button in the bottom-right of the window. A folder picker appears.

Here is exactly what happens after you pick a folder:

### Phase 1 — Scanning
The app walks through every subfolder and finds all `.pdf` and `.docx` files.

It automatically **skips**:
- Hidden folders (starting with `.`)
- Dev folders: `node_modules`, `venv`, `__pycache__`, etc.
- System folders: `C:\Windows`, `C:\Program Files`, etc.
- Folders named: `env`, `odf_env`, `libs`, `bin`, `obj`, `scripts`

It shows you a count: `"Found 47 supported files to scan."`

### Phase 2 — Smart Skip (Incremental Indexing)
For each file, the app computes a fingerprint: `MD5(filepath + last-modified-time)`.

It checks this fingerprint against what's already in the database. **If the file hasn't changed, it skips it.** This means:
- First time: indexes everything
- Second time on the same folder: only indexes new or modified files
- Re-indexing is fast if most files are unchanged

### Phase 3 — Text Extraction (Parallel)
The app processes files using up to 8 worker threads running at the same time (so 8 files at once).

For each file:
- **PDF** → uses `pdfminer` to extract all the text from the PDF's text layer
- **DOCX** → uses `python-docx` to extract all paragraphs and table cells
- Text is cleaned: extra spaces removed, control characters stripped
- Text is capped at 100,000 characters per file (very large files don't break anything)

**Important:** Scanned PDFs (photos of paper, no real text layer) return empty and are skipped with a warning. ODF cannot read images inside PDFs.

### Phase 4 — Chunking
Each document is too long to compare as a whole. So it's cut into overlapping pieces:
- Each chunk is ~1,000 characters long
- Chunks overlap by 100 characters so context doesn't get cut off at boundaries
- A 10-page document becomes roughly 20–50 chunks

### Phase 5 — Embedding (The AI Step)
Each chunk of text is fed into the BAAI/bge-small-en-v1.5 AI model, which converts it into a list of 384 numbers (called a vector or embedding). This vector mathematically represents the meaning of that chunk.

- This runs in batches of 32 chunks at a time
- Uses ONNX Runtime (a fast CPU inference engine) — **no GPU needed**
- The numbers are stored in ChromaDB alongside the original text and file metadata

### Phase 6 — Stored
The vectors are saved to disk in `data/chroma_db/`. This database survives restarts — you don't re-index every time you open the app.

When done: `"Indexed 47 files successfully."` appears.

---

## Step-by-Step: What Happens During Search

You type in the search box. Here's what runs:

1. **Debounce** — the app waits 280ms after you stop typing before it searches. This prevents firing a search on every single keystroke.

2. **Minimum 2 characters** — nothing happens until you've typed at least 2 characters.

3. **Query embedding** — your query text is converted to a 384-dim vector using the same AI model.

4. **Vector search** — ChromaDB compares your query vector against all stored chunk vectors using cosine similarity. It fetches the top 24 candidates (3× the final result count).

5. **Hybrid boosting** — on top of the AI score, keyword bonuses are applied:
   - `+25%` if your query appears in the filename
   - `+15%` if your query appears literally in the chunk text
   - Final score is capped at 100%

6. **Re-ranking** — the 24 candidates are sorted by final score. Top 8 are returned.

7. **Results appear** — the window expands and shows up to 8 rows. Selecting a row shows the detail panel on the right: filename, type, size, modified date, match %, and a preview of the matching text.

8. **Open file** — press `Enter` or click "Open File →" and the OS opens the file in its default app (e.g., Adobe Acrobat for PDF).

Total search time from when you stop typing to results appearing: **typically 0.3–2 seconds** depending on database size.

---

## After Indexing — What Can You Do?

Once your documents are indexed, the index lives forever on disk. You can:

- **Close and reopen ODF** — your index is still there, no re-indexing needed
- **Press Ctrl+K anytime** — toggle the window while working in any app
- **Search instantly** — results in under 2 seconds for most collections
- **Re-index to update** — if you added new files to a folder, click "Index Folder" again on that same folder. Only new/changed files get processed (smart skip)
- **Clear the index** — delete the `data/chroma_db/` folder entirely. Next launch starts fresh.

---

## Performance: How Fast Is It?

### Indexing Speed
Speed depends on your CPU and number of files. Rough estimates:

| Files | File Size (avg) | Approx Time |
|-------|----------------|-------------|
| 50 PDFs | 2 MB each | 1–3 minutes |
| 200 PDFs | 2 MB each | 5–12 minutes |
| 500 mixed PDFs + DOCX | 1–5 MB each | 15–40 minutes |

The main bottleneck is the AI embedding step, not text extraction. The model runs on CPU with 8 parallel threads.

### Search Speed
| Database Size | Search Time |
|---------------|-------------|
| < 500 files | 0.3–0.8 seconds |
| 500–2,000 files | 0.5–1.5 seconds |
| 2,000–5,000 files | 1–3 seconds |
| 5,000+ files | 2–5 seconds |

Search speed grows slowly with database size because ChromaDB uses HNSW (a fast approximate nearest-neighbor algorithm), not a brute-force scan.

---

## System Requirements

### Minimum (to run at all)
| Component | Minimum |
|-----------|---------|
| OS | Windows 10/11, macOS 10.15+, or Linux |
| CPU | Any modern 64-bit CPU (2015 or newer) |
| RAM | **4 GB** (2 GB for the OS, ~1.5 GB for the AI model + app) |
| Disk | 1 GB free (for the app + AI model files) |
| Python | 3.11 or 3.12 (not needed for EXE) |
| GPU | **Not required — runs entirely on CPU** |
| Internet | **Not required at runtime** (only needed on first setup to download the AI model) |

### Recommended (for comfortable use)
| Component | Recommended |
|-----------|-------------|
| RAM | **8 GB or more** — gives headroom for large document collections |
| CPU | 4+ cores — indexing uses up to 8 threads, more cores = faster |
| Disk | SSD preferred — ChromaDB reads/writes faster on SSD |
| Storage for index | ~50 MB per 1,000 documents indexed |

### RAM Detail
Here's where the memory goes:
- **AI model (BAAI/bge-small-en-v1.5)**: ~90 MB loaded into RAM
- **ONNX Runtime**: ~100 MB overhead
- **ChromaDB**: ~50–200 MB depending on collection size
- **The UI + Python**: ~80 MB
- **Total at idle (after loading)**: ~400–600 MB
- **During indexing (peak)**: ~800 MB – 1.5 GB (8 threads × text buffers)

If you have less than 4 GB of free RAM, the app may slow down significantly during indexing due to memory pressure.

### GPU
**ODF does not use a GPU.** The ONNX Runtime runs the AI model entirely on CPU. This was a deliberate design choice — it means the app works on any machine, even budget laptops with no dedicated GPU, without installing CUDA or any GPU drivers.

The trade-off: embedding is slower than GPU-based tools. For a typical personal document collection (a few hundred files), this is not a problem in practice.

---

## Limits and Constraints

### File Type Limits
| Format | Supported? | Notes |
|--------|-----------|-------|
| PDF (text) | ✅ Yes | Works if PDF has a real text layer |
| PDF (scanned) | ❌ No | Image-only PDFs return no content |
| DOCX (Word) | ✅ Yes | Full support including tables |
| TXT | ❌ Not enabled | Code exists but extension not in active list |
| XLSX (Excel) | ❌ No | Not supported |
| PPTX (PowerPoint) | ❌ No | Not supported |
| Images (PNG, JPG) | ❌ No | Not supported |

### Content Limits
- **Max text per file**: 100,000 characters (~50–70 pages). Content beyond this is silently cut off during extraction.
- **Min text per file**: Files with no extractable text are skipped with a warning.
- **Language**: The AI model (`bge-small-en-v1.5`) is optimised for English. Other languages will still work but accuracy drops.
- **Handwritten content in PDFs**: Not readable. Only digital text inside PDF files works.

### Search Limits
- **Minimum query length**: 2 characters
- **Results shown**: Top 8 results per search
- **Results are ranked by semantic meaning + keyword bonus** — there is no way to filter by date or file type in the current version
- **No multi-folder search filtering**: All indexed folders are searched together

### Indexing Limits
- **Large drives**: Indexing an entire drive (C:\, D:\) is technically possible but warned against — it can take hours and slow your PC
- **Network drives**: Should work but performance depends on network speed; not officially tested
- **Password-protected PDFs**: Cannot be read — they return no content
- **Encrypted DOCX files**: Same — not readable

### Hotkey Limits
- **Windows**: `Ctrl+K` requires the app to be running as Administrator on some systems (keyboard library restriction)
- **macOS / Linux**: May need accessibility permissions for global hotkey to work

### EXE-specific Limits
- **Windows only**: The EXE build script targets Windows. macOS/Linux users must use the Python script method.
- **First launch is slow**: 20–30 second extraction delay, one-time only
- **Antivirus**: Some antivirus software may flag or slow the EXE because it's a PyInstaller bundle (common false positive). You may need to add it to your AV whitelist.

---

## What Happens to Your Data

- Your document text is extracted, chunked, and stored as mathematical vectors in `data/chroma_db/`
- The original files are **never copied or moved** — ODF just stores a path to them
- If you delete, move, or rename a file after indexing, ODF's search results will still show it but clicking "Open File →" will fail (file not found)
- Re-indexing the folder after changes fixes stale entries
- To wipe everything: delete the `data/chroma_db/` folder

---

## Quick Reference Card

```
FIRST TIME SETUP
─────────────────
pip install -e .                         # install ODF + dependencies
python -m odf                            # launch the app

DAILY USE
──────────
python -m odf                            # launch
Ctrl+K                                   # toggle window on/off
Click "＋ Index Folder" → pick folder    # index documents (do once per folder)
Type your query                          # search
↑ / ↓                                   # navigate results
Enter or click "Open File →"             # open the selected file
Esc                                      # hide the window

BUILD EXE (share with anyone)
───────────────────────────────
python build_exe.py                      # builds dist/ODF/ODF.exe
                                         # zip dist/ODF/ and share — no Python needed

SYSTEM NEEDS
─────────────
RAM:   4 GB minimum, 8 GB recommended
GPU:   Not needed
Net:   Not needed after first setup
OS:    Windows / macOS / Linux
```

---

## Common Questions

**Q: Do I need to re-index every time I open the app?**
No. The index is saved to disk and loaded automatically. You only re-index when you add new files.

**Q: Can I search while indexing is running?**
Yes. Search and indexing run on separate threads. Search results may be incomplete until indexing finishes.

**Q: My search returns irrelevant results. Why?**
The AI model works on meaning, not just words. Very short or vague queries (e.g., `"the"`, `"file"`) may return poor results. Try more descriptive phrases. Also, if the document is a scanned PDF, its text was never extracted and it won't appear in results.

**Q: Can I index multiple folders?**
Yes. Click "Index Folder" multiple times for different folders. All indexed content goes into the same database and is searched together.

**Q: What if I delete a file after indexing it?**
The index will still have that file's data. The search result will appear but clicking "Open File" will fail. To clean up, delete `data/chroma_db/` and re-index your folders.

**Q: Does it work on macOS / Linux?**
The Python script version works on macOS and Linux. The EXE build only targets Windows. The global hotkey (`Ctrl+K`) may need extra permissions on macOS (Accessibility settings).

**Q: How much disk space does the index use?**
Roughly 30–80 MB per 1,000 documents, depending on document length. A personal collection of 500 files typically takes 20–40 MB.
