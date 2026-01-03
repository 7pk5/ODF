# Resume / Portfolio Content for ODF

Here are professional descriptions of the project tailored for your resume and LinkedIn.

## 📌 Project Title Options
*   **Offline Document Finder (ODF)**: locally-hosted AI Search Engine.
*   **Semantic Desktop Search Utility**: RAG-based Information Retrieval System.
*   **AI-Powered File Explorer**: Hybrid Search Tool for Local Documents.

## 🛠️ Technical Stack
*   **Languages**: Python 3.10+
*   **UI/UX**: CustomTkinter (Glassmorphism Overlay), Threading handling.
*   **AI/ML**: Sentence-Transformers (`all-MiniLM-L6-v2` / `bge-small-en`), Vector Embeddings.
*   **Database**: ChromaDB (Vector Store), SQLite.
*   **Libraries**: PDFMiner, PyMuPDF, Keyboard (Global Hotkeys).

## 📄 Bullet Points (Choose 3-4)

### **Key Achievements:**
*   **Engineered a privacy-first, offline semantic search engine** that indexes and retrieves local documents (PDF, DOCX, TXT) using **Vector Embeddings** and **ChromaDB**, eliminating reliance on cloud APIs.
*   **Implemented a Hybrid Search Algorithm** (RAG-lite) that combines semantic understanding with **Exact Keyword Boosting**. This solved the common "loss of specificity" problem in vector search, prioritizing specific filenames/IDs while maintaining conceptual matching.
*   **Designed a "Spotlight-style" Desktop Overlay** using **CustomTkinter**, featuring a borderless, transparent UI with global hotkey support (`Ctrl+K`) and non-blocking background threading for instant responsiveness.
*   **Optimized Indexing Pipeline** to handle incremental updates, preventing redundant processing of unchanged files and ensuring swift startup times even with large document sets.

### **Problem Solving Focus:**
*   "Solved the inefficiency of traditional regex/keyword search by integrating an **embedding-based retrieval system**, allowing users to find files via **Natural Language Queries** (e.g., 'invoice from last month') rather than exact filenames."

---

## 🔗 Architecture Description (For Interviews)
"I built a desktop application that functions as a local RAG (Retrieval-Augmented Generation) system. It uses `pdfminer` to extract text, chunks it, and creates vector embeddings using `Sentence-Transformers`. These are stored in a local `ChromaDB` instance.
For the frontend, I moved away from web-based Electron wrappers to a native Python `CustomTkinter` overlay for better OS integration and memory efficiency. I also solved a key UX challenge by implementing a hybrid ranking system: expanding the vector search results (Top-30) and re-ranking them based on exact substring matches in filenames, ensuring the tool feels both 'smart' and 'precise'."
