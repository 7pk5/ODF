# Offline Document Finder (ODF)

A smart AI-powered desktop tool that helps users search for local files using natural language queries. It performs semantic search over PDF, DOCX, and TXT files, runs completely offline, and protects against scanning system directories.

## Features

- 🔍 **Natural Language Search**: Search using queries like "GitHub notes from January" or "invoice pdf 2023 client name"
- 🏠 **Offline Operation**: Completely offline - no internet or cloud services required
- 📁 **Smart File Support**: Supports PDF, DOCX, and TXT files
- 🛡️ **System Protection**: Automatically avoids scanning system directories like C:\Windows
- ⚡ **Global Shortcut**: Launch search window with Ctrl+Alt+F
- 🎯 **Semantic Search**: AI-powered similarity ranking using sentence transformers
- 📊 **Ranked Results**: Shows matching files with similarity percentage

## Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Minimum 4GB RAM recommended for AI model

## Installation

1. **Clone or download this project**
   ```bash
   git clone <repository-url>
   cd offline-doc-finder
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application** (choose one option):

   **Option A: Simple Mode (Recommended for macOS)**
   ```bash
   python main_simple.py
   ```
   - No admin privileges required
   - Full AI search functionality
   - No global shortcuts

   **Option B: Full Mode**
   ```bash
   python main.py
   ```
   - Includes global shortcuts (may require admin on macOS)
   - Full functionality

   **Option C: Admin Mode (for global shortcuts on macOS)**
   ```bash
   sudo python main.py
   ```
   - Enables global shortcuts on macOS
   - Requires administrator password

## Launch Modes

| Mode | Command | Global Shortcuts | Admin Required | Best For |
|------|---------|------------------|----------------|----------|
| **Simple** | `python main_simple.py` | ❌ | ❌ | macOS users, no shortcuts needed |
| **Standard** | `python main.py` | ⚠️ (errors on macOS) | ❌ | Testing, basic usage |
| **Admin** | `sudo python main.py` | ✅ | ✅ | Users who want global shortcuts |

💡 **Tip**: If you see keyboard/admin errors, use `main_simple.py` instead!

## Usage

### Basic Usage

1. **Launch the application**:
   ```bash
   python main.py
   ```

2. **Select a folder**: Click "Browse" to choose which folder to search
   - The system will automatically avoid system directories
   - Indexing will start automatically after folder selection

3. **Search**: Type your natural language query and press Enter or click "Search"
   - Example queries:
     - "meeting notes january"
     - "python tutorial pdf"
     - "invoice 2023"
     - "project report final"

4. **Open files**: Double-click any result to open the file

### Global Shortcut

- Press **Ctrl+Alt+F** to open the search window from anywhere
- Works when the application is running in the background

### Supported File Types

- **PDF files** (.pdf) - Extracts text content
- **Word documents** (.docx) - Extracts text from paragraphs and tables
- **Text files** (.txt) - Supports multiple encodings

## How It Works

### AI-Powered Search

1. **Document Indexing**: When you select a folder, ODF:
   - Scans for supported file types
   - Extracts text content from each file
   - Generates semantic embeddings using sentence transformers
   - Builds a FAISS vector index for fast similarity search

2. **Query Processing**: When you search:
   - Your query is converted to a semantic embedding
   - The system finds documents with similar meanings
   - Results are ranked by semantic similarity

3. **Privacy**: Everything runs locally on your machine
   - No data is sent to the internet
   - No cloud services are used
   - Your documents remain private

### System Protection

ODF automatically prevents scanning of system directories:
- C:\Windows
- C:\Program Files
- C:\Program Files (x86)
- C:\System32
- C:\ProgramData
- Other critical system folders

## Project Structure

```
offline-doc-finder/
├── main.py                     # Entry point
├── requirements.txt           # Dependencies
├── README.md                 # Documentation
├── ui/
│   └── search_window.py      # Search interface
├── search_engine/
│   ├── embedder.py          # Text embedding
│   ├── vector_search.py     # FAISS search
│   └── file_indexer.py      # File scanning
├── utils/
│   ├── open_file.py         # File operations
│   └── shortcuts.py         # Global shortcuts
└── models/                   # Generated index files
    ├── embeddings.index     # FAISS vector index
    └── metadata.pkl         # Document metadata
```

## Configuration

### Changing the Global Shortcut

Edit `main.py` and modify the shortcut registration:

```python
# Change 'ctrl+alt+f' to your preferred combination
register_global_shortcut(search_window.show_window, 'ctrl+shift+s')
```

### Adjusting Search Parameters

In `search_engine/vector_search.py`, you can modify:

```python
# Number of search results
results = self.vector_search.search(query, top_k=20)

# Text preprocessing length
text = self.embedder.preprocess_text(searchable_text, max_length=512)
```

## Troubleshooting

### Common Issues

1. **Global shortcut not working**:
   - Try running as administrator
   - Check if another application is using the same shortcut
   - Modify the shortcut in `main.py`

2. **Model download fails**:
   - Ensure internet connection for initial model download
   - The model (all-MiniLM-L6-v2) is downloaded once and cached locally

3. **PDF extraction issues**:
   - Some PDFs may be scanned images without extractable text
   - Password-protected PDFs are not supported

4. **Memory issues**:
   - Large document collections may require more RAM
   - Consider indexing smaller folders separately

### Performance Tips

- **Faster indexing**: Index smaller, specific folders rather than entire drives
- **Better results**: Use descriptive filenames that match your search terms
- **Memory optimization**: Close other applications when indexing large document sets

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug output
python main.py
```

### Adding New File Types

1. Add the extension to `FileIndexer.supported_extensions`
2. Implement extraction logic in `FileIndexer._extract_content()`
3. Test with sample files

### Customizing the AI Model

Edit `search_engine/embedder.py` to use a different sentence transformer model:

```python
# Use a different model
embedder = Embedder(model_name='paraphrase-MiniLM-L6-v2')
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or feature requests, please open an issue on the project repository.

---

**Note**: This application is designed for personal use and handles your documents locally to ensure privacy. Always backup important documents before running any indexing operations.
