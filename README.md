# Offline Document Finder (ODF)
**"Search Like You Think"** – A Local-First, AI-Powered Document Search Engine.

![UI Screenshot](https://via.placeholder.com/800x400?text=ODF+Ultra+Dark+UI+Overview)
*(Note: Replace with actual screenshot of your new UI)*

## 🚀 Problem Solved
Traditional file search is broken. It relies on **exact keyword matching**, meaning if you name a file "2023_Financial_Review.pdf" and search for "Budget Report", you'll find nothing.

ODF solves this by using **Semantic Search (AI)**. It reads your documents, understands the *concepts* inside them (not just the text), and lets you search using natural language.
*   **Problem**: "I don't remember the filename, just what it's about."
*   **Solution**: "Show me the project files regarding the new marketing strategy." -> *Finds 'Q3_Strategy_v2.pdf'*

---

## 🏗️ Architecture

ODF is built as a **Native Desktop Overlay** using a modern Python stack. It is designed to be lightweight, fast, and completely offline.

### 1. The Frontend (UI Layer)
*   **Framework**: `CustomTkinter` (Modernized wrapper around Tkinter).
*   **Design System**: "Glassmorphism" Overlay.
    *   **Transparency**: `alpha=0.97` for a native, integrated feel.
    *   **Windowing**: Borderless window (`overrideredirect=True`) that floats on top (`-topmost`).
    *   **Theme**: Ultra-Dark (`#0d0d0d`) with Electric Blue (`#3B8ED0`) accents.
*   **Global Hotkey**: Uses `keyboard` library to listen for `Ctrl+K` at the OS level to toggle the window instantly.

### 2. The Backend (Engine Layer)
*   **Orchestration**: Python `threading` ensures the UI never hangs while indexing or searching.
*   **Text Extraction**:
    *   `pdfminer.six` for PDFs.
    *   `python-docx` for Word documents.
    *   Native reading for Text files.

### 3. The "Brain" (Storage & Retrieval)
*   **Vector Database**: `ChromaDB` (Persistent local storage).
    *   Stores the "embeddings" (mathematical representations) of your documents.
    *   No external server required; runs embedded within the app.
*   **AI Model**: `sentence-transformers` (specifically `BAAI/bge-small-en-v1.5`).
    *   Converts text into 384-dimensional vectors.
    *   Highly optimized for semantic similarity.

---

## 🧠 The "RAG" Concept (Retrieve-and-Rank)
While ODF is a search engine, it utilizes the core **Retrieval** component of **RAG (Retrieval-Augmented Generation)** systems.

### How it works:
1.  **Ingestion (Indexing)**:
    *   Documents are split into **Chunks** (e.g., 500 characters).
    *   Each chunk is passed through the AI Model to generate an **Embedding Vector**.
    *   These vectors are stored in **ChromaDB**.

2.  **Retrieval (The Search)**:
    *   When you type a query, it is also converted into a vector.
    *   We compare the *angle* (Cosine Similarity) between your query vector and all document vectors.
    *   **Result**: We find the chunks that are *conceptually* closest to your query.

### 🧪 Hybrid Search Implementation
ODF uses a **Hybrid Search** strategy to ensure robustness. Pure AI search sometimes misses exact keywords (e.g., specific ID numbers), so we combine functionality:

1.  **Broad Cast**: We fetch **30 candidates** (3x the needed amount) using the AI Vector Search.
2.  **Keyword Check**: We scan these candidates for **Exact Substring Matches** of your query.
3.  **Boosting Logic**:
    *   **Title Match**: +25% Score Bonus (If filename contains the query).
    *   **Content Match**: +15% Score Bonus (If text contains the query).
4.  **Re-Ranking**: The final list is sorted by this new weighted score.

**Why?** This gives you the best of both worlds:
*   Searching "Invoices" (Concept) finds files named "Billing_2024".
*   Searching "INV-2024-001" (Exact Key) forces that specific file to the top.

---

## 🔒 Privacy & Security
*   **Local-First**: No data is ever sent to the cloud. All embeddings are calculated on your CPU.
*   **Offline**: Works entirely without an internet connection.
*   **Data Control**: The database lives in `data/chroma_db` and can be deleted at any time.

---

## 🛠️ Usage
1.  **Launch**: Run `python main.py`.
2.  **Toggle**: Press **Ctrl+K** anywhere.
3.  **Index**: Click "Index Folder" and select a directory containing your documents.
4.  **Search**: Type freely!

---

*Built with ❤️ using Python, ChromaDB, and CustomTkinter.*
