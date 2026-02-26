# ODF — Setup & Usage Guide

## 📋 Prerequisites

### Windows
- Python 3.8+ ([Download](https://www.python.org/downloads/))
- No extra system packages needed

### Linux (Ubuntu/Debian)
```bash
sudo apt install python3-tk python3-venv
```

### macOS
- Python 3.8+ (via [Homebrew](https://brew.sh): `brew install python-tk`)

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ODF.git
cd ODF/ODF
```

### 2. Create and activate a virtual environment
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python main.py
```

> **First run** downloads the AI model (~67 MB). Subsequent launches are instant.

---

## 🔍 How to Use

| Action | How |
|---|---|
| **Toggle window** | Press **Ctrl + K** anywhere |
| **Index a folder** | Click the **＋ Index Folder** button and select a directory |
| **Search** | Type your query (minimum 2 characters) — results appear live |
| **Navigate results** | **↑ / ↓** arrow keys to move, **Enter** to open |
| **Open a file** | Click a result or press **Enter** on the selected one |
| **Close window** | Press **Esc** or click the `esc` pill |

---

## 📂 Supported File Types

| Format | Extension |
|---|---|
| PDF | `.pdf` |
| Word | `.docx` |

---

## 💡 Tips

- **Semantic search**: You don't need exact filenames. Search by *concept* — e.g., "marketing budget" finds `Q3_Strategy_v2.pdf`.
- **Hybrid search**: Exact keywords (like `INV-2024-001`) are automatically boosted to the top.
- **Re-index**: Just select the same folder again — already-indexed files are skipped automatically.
- **Clear index**: Delete the `data/chroma_db` folder to start fresh.

---

## 🛠️ Building a Standalone Executable (Windows)

```bash
python build_exe.py
```

This produces `dist/ODF.exe` — a single file anyone can double-click without installing Python.

---

## ⚠️ Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: tkinter` | **Linux**: `sudo apt install python3-tk` |
| Ctrl+K not working (Linux) | Make sure you're on X11, not Wayland. Or run with `sudo`. |
| Ctrl+K not working (macOS) | Grant Accessibility permissions in System Preferences → Privacy. |
| Model download fails | Check internet connection. The model is cached in `models/` after first download. |
| Slow indexing | Avoid indexing entire drives. Select specific folders like Documents or Desktop. |

---

## 🔒 Privacy

- **100% offline** — no data leaves your machine
- **Local AI** — embeddings are computed on your CPU
- **Your data** — stored in `data/chroma_db`, delete anytime
