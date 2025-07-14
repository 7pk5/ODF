# Offline Document Finder (ODF)

A smart AI-powered desktop tool for semantic search of local documents using natural language queries. Search your PDF, DOCX, and TXT files with AI - completely offline and private.

## ✨ Features

- 🔍 **Natural Language Search**: Find documents using queries like "meeting notes january" or "python tutorial pdf"
- 🏠 **100% Offline**: No internet required after installation - your documents stay private
- 📁 **Multiple File Types**: Supports PDF, DOCX, and TXT files
- 🤖 **AI-Powered**: Uses advanced sentence transformers for semantic understanding
- 📊 **Ranked Results**: Shows similarity scores to help you find the best matches
- � **Cross-Platform**: Works on Windows, macOS, and Linux

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
3. **Search**: Type natural language queries like:
   - "budget report 2023"
   - "python programming notes"
   - "client meeting minutes"
4. **Open Results**: Click on any result to open the document

## 📁 Project Structure

```
ODF/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── search_engine/            # Core AI search functionality
│   ├── embedder.py          # Text embedding with AI models
│   ├── vector_search.py     # FAISS-based similarity search
│   └── file_indexer.py      # Document processing and indexing
├── ui/                      # User interface
│   └── search_window.py     # Main search window (Tkinter)
├── utils/                   # Helper utilities
│   ├── open_file.py         # Cross-platform file opening
│   └── shortcuts.py         # Keyboard shortcut handling
└── models/                  # Generated files (created after first use)
    ├── embeddings.index     # AI vector index
    └── metadata.pkl         # Document metadata
```

## 🔧 Technical Details

### AI Models Used
- **Sentence Transformers**: For converting text to semantic vectors
- **FAISS**: For fast similarity search across document embeddings
- **Multiple Models**: Automatically switches between fast and accurate models

### Supported File Types
- **PDF** (.pdf) - Extracts text content using pdfminer.six
- **Word Documents** (.docx) - Extracts text using python-docx
- **Text Files** (.txt) - Direct text processing

### Privacy & Security
- ✅ **Completely Offline**: No data sent to internet after initial setup
- ✅ **Local Processing**: All AI inference runs on your machine
- ✅ **Private**: Your documents never leave your computer

## 🛠️ Dependencies

The project uses these main libraries:
- `sentence-transformers` - AI text embeddings
- `faiss-cpu` - Fast similarity search
- `torch` - PyTorch for AI models
- `transformers` - Hugging Face transformers
- `pdfminer.six` - PDF text extraction
- `python-docx` - Word document processing
- `tkinter` - GUI interface (included with Python)

## 🔍 Search Examples

Try these natural language queries:
- `"project proposal final version"`
- `"meeting notes with john"`
- `"invoice march 2024"`
- `"python programming tutorial"`
- `"budget financial report"`

## ❓ Troubleshooting

### First-time setup taking long?
- The AI models need to download (one-time, ~500MB)
- Document indexing takes time proportional to your document count

### Not finding documents?
- Make sure documents contain searchable text (not just images)
- Try different search terms or keywords from the document

### Performance issues?
- Index smaller folders instead of entire drives
- Ensure you have enough RAM (4GB+ recommended)
- Close other memory-intensive applications

## 🔄 How It Works

1. **Document Processing**: Extracts text from your PDF, DOCX, and TXT files
2. **AI Embedding**: Converts document text into semantic vectors using transformer models
3. **Vector Indexing**: Builds a FAISS search index for fast similarity matching
4. **Query Processing**: Converts your search query into the same vector space
5. **Similarity Search**: Finds documents with similar meaning, not just exact keywords

## 💡 Tips for Better Results

- Use descriptive search terms
- Try different phrasings if you don't find what you're looking for
- Organize documents in focused folders rather than massive directories
- Include relevant keywords in your document filenames

## 📄 License

MIT License - feel free to use and modify for your needs.

---

**Note**: This application processes your documents locally to ensure complete privacy. No data is transmitted over the internet during normal operation.
