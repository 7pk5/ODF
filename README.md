# Offline Document Finder (ODF) - The Solution (MVP)

See PROBLEM.md for a detailed breakdown of Windows search limitations and why traditional file search fails.

**Finally, AI-powered file search that actually works!** 🎯

Tired of Windows search failing you? ODF brings Google-like semantic search to your local documents - completely offline and private.

## 🎯 The Solution to Windows Search Problems

### **Before ODF (Windows Search)**
❌ Search: `"Q3 budget meeting"` → **Nothing found**  
❌ Your file: `"notes_march_15.pdf"` (contains budget discussion)

### **After ODF (AI Search)**
✅ Search: `"Q3 budget meeting"` → **Found instantly!**  
✅ AI understands: *This file contains budget discussions from Q3*

## ✨ How ODF Solves Your Problems

| **Problem** | **Windows Search** | **ODF Solution** |
|-------------|-------------------|------------------|
| **Semantic Search** | Only exact keywords | AI understands meaning & context |
| **Content Search** | Poor PDF/DOCX support | Deep content analysis |
| **Natural Language** | Must use exact terms | Talk naturally: "budget meeting last month" |
| **File Discovery** | Remember exact filenames | Find by content and context |
| **Speed** | Slow, often fails | Instant AI-powered results |
| **Privacy** | May sync to cloud | 100% offline and private |

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- 4GB+ RAM recommended for AI models

### Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/7pk5/ODF.git
   cd ODF
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

That's it! The search window will open automatically.

## 📖 How to Use

1. **Add Documents**: Click "Add Documents" to select a folder containing your files
2. **Wait for Indexing**: The AI will process your documents (one-time setup per folder)
3. **Search Naturally**: Type queries like a human:
   - `"meeting notes about budget"`
   - `"chocolate cake recipe"`
   - `"client proposal with pricing"`
4. **Get Instant Results**: Click on any result to open the document

## 🔍 Real Search Examples That Work

### **Natural Language Queries:**
- `"project proposal final version"` → Finds any proposals, even if filename is "client_doc_v3.pdf"
- `"meeting notes with john"` → Finds meetings mentioning John, regardless of filename
- `"python programming tutorial"` → Finds coding documents by content
- `"invoice march 2024"` → Finds financial documents from that period
- `"chocolate dessert recipe"` → Finds recipes even if titled "Grandma's Special Cake"

## 🤖 AI-Powered Features

- 🧠 **Semantic Understanding**: Finds documents by meaning, not just keywords
- 📄 **Deep Content Analysis**: Searches inside PDF, DOCX, and TXT files
- 🎯 **Context Awareness**: Understands relationships between concepts
- 📊 **Relevance Scoring**: Shows how well each result matches your query
- 🏠 **100% Offline**: No internet required, completely private

## 📁 Supported File Types

- **PDF** (.pdf) - Full text extraction and search
- **Word Documents** (.docx) - Complete content analysis
- **Text Files** (.txt) - Direct text processing

## 🔧 Technical Details

### **AI Models Used**
- **Sentence Transformers**: Converts text to semantic vectors
- **FAISS**: Lightning-fast similarity search
- **PyTorch**: Powers the AI inference

### **How It Works**
1. **AI Processing**: Converts your documents into semantic "fingerprints"
2. **Smart Indexing**: Builds a searchable AI index of your content
3. **Natural Queries**: Understands what you mean, not just what you type
4. **Instant Results**: Finds relevant documents in milliseconds

## 🛠️ Dependencies

```txt
sentence-transformers>=2.3.0    # AI text understanding
faiss-cpu>=1.7.4               # Fast similarity search
torch>=2.1.0                   # AI processing engine
transformers>=4.35.0           # Language models
pdfminer.six>=20231228         # PDF text extraction
python-docx>=1.1.0            # Word document processing
numpy>=1.26.0,<2.0.0          # Numerical computations
scikit-learn>=1.3.0           # Machine learning utilities
scipy>=1.11.0                 # Scientific computing
rank-bm25>=0.2.2              # Text ranking algorithm
nltk>=3.8.1                   # Natural language processing
tqdm>=4.65.0                  # Progress bars
requests>=2.31.0              # HTTP requests
```

## 🔒 Privacy & Security

- ✅ **Completely Offline**: No data sent to internet after setup
- ✅ **Local Processing**: All AI runs on your machine
- ✅ **Private**: Your documents never leave your computer
- ✅ **No Tracking**: No analytics, no data collection

## ❓ Troubleshooting

### **First-time setup taking long?**
- AI models need to download (one-time, ~500MB)
- Document indexing scales with document count

### **Not finding documents?**
- Ensure documents contain searchable text (not just images)
- Try different search phrases
- Make sure the folder was properly indexed

### **Performance issues?**
- Index smaller folders instead of entire drives
- Ensure sufficient RAM (4GB+ recommended)
- Close memory-intensive applications

## 🆚 Comparison

| Feature | Windows Search | Google Drive | ODF |
|---------|---------------|--------------|-----|
| **Semantic Search** | ❌ | ✅ | ✅ |
| **Offline** | ✅ | ❌ | ✅ |
| **Privacy** | ⚠️ | ❌ | ✅ |
| **Content Search** | ⚠️ | ✅ | ✅ |
| **Natural Language** | ❌ | ✅ | ✅ |
| **Speed** | ⚠️ | ✅ | ✅ |

## 📄 License

MIT License - Use freely for personal and commercial projects.

---

## 🎯 Why ODF Exists

**The Problem**: Windows file search is stuck in the past. You think in concepts, but Windows only understands exact keywords.

**The Solution**: ODF brings modern AI search to your local files. Search naturally, find instantly, stay private.

**Ready to upgrade your file search experience?** Get started above! 🚀

---

*See [PROBLEM.md](PROBLEM.md) for a detailed breakdown of Windows search limitations and why traditional file search fails.*
