"""
Search Window UI for Offline Document Finder
Provides the main interface for users to search documents.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from search_engine.vector_search import VectorSearch
from search_engine.file_indexer import FileIndexer
from utils.open_file import open_file

class SearchWindow:
    def __init__(self, fast_mode=True):
        self.root = None
        # Elon Musk style: default to fast mode, but allow override
        self.vector_search = VectorSearch(use_accurate_model=not fast_mode, use_fast_model=fast_mode)
        self.file_indexer = FileIndexer()
        self.current_folder = None
        self.is_indexing = False
        
    def show_window(self):
        """Show the search window."""
        if self.root is None:
            self._create_window()
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
    
    def _create_window(self):
        """Create the main search window."""
        self.root = tk.Tk()
        self.root.title("Offline Document Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Offline Document Finder", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Folder selection
        ttk.Label(main_frame, text="Folder to search:").grid(row=1, column=0, sticky=tk.W)
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(main_frame, textvariable=self.folder_var, state="readonly")
        self.folder_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        self.browse_button = ttk.Button(main_frame, text="Browse", command=self._browse_folder)
        self.browse_button.grid(row=1, column=2, padx=(5, 0))
        
        # Search box
        ttk.Label(main_frame, text="Search query:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var, font=("Arial", 12))
        self.search_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(10, 0))
        self.search_entry.bind('<Return>', lambda e: self._search())
        
        self.search_button = ttk.Button(main_frame, text="Search", command=self._search)
        self.search_button.grid(row=2, column=2, padx=(5, 0), pady=(10, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="5")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results treeview
        columns = ("filename", "path", "similarity", "type")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="tree headings")
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns
        self.results_tree.heading("#0", text="File")
        self.results_tree.heading("filename", text="Filename")
        self.results_tree.heading("path", text="Path")
        self.results_tree.heading("similarity", text="Similarity %")
        self.results_tree.heading("type", text="Type")
        
        self.results_tree.column("#0", width=200, minwidth=100)
        self.results_tree.column("filename", width=200, minwidth=100)
        self.results_tree.column("path", width=250, minwidth=150)
        self.results_tree.column("similarity", width=100, minwidth=80)
        self.results_tree.column("type", width=80, minwidth=60)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Double-click to open file
        self.results_tree.bind("<Double-1>", self._open_selected_file)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a folder and enter a search query")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Focus on search entry
        self.search_entry.focus()
    
    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select folder to search")
        if folder:
            # Check if it's a system folder (basic protection)
            if self._is_system_folder(folder):
                messagebox.showwarning("System Folder Warning", 
                                     "Cannot select system folders like C:\\Windows or C:\\Program Files for security reasons.")
                return
            
            self.folder_var.set(folder)
            self.current_folder = folder
            self._index_folder_async()
    
    def _is_system_folder(self, folder_path):
        """Check if the folder is a system folder that should be avoided."""
        system_folders = [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\System32",
            "C:\\ProgramData",
            "C:\\Users\\Default",
            "C:\\Boot",
            "C:\\Recovery"
        ]
        
        folder_path = os.path.normpath(folder_path.upper())
        for sys_folder in system_folders:
            if folder_path.startswith(sys_folder.upper()):
                return True
        return False
    
    def _index_folder_async(self):
        """Index the selected folder in a background thread."""
        if self.is_indexing:
            return
        
        self.is_indexing = True
        self.status_var.set("Indexing folder... Please wait.")
        self.search_button.config(state="disabled")
        
        def index_thread():
            try:
                files_data = self.file_indexer.index_folder(self.current_folder)
                self.vector_search.build_index(files_data)
                self.status_var.set(f"Indexed {len(files_data)} files. Ready to search!")
            except Exception as e:
                self.status_var.set(f"Error indexing folder: {str(e)}")
                messagebox.showerror("Indexing Error", f"Error indexing folder: {str(e)}")
            finally:
                self.is_indexing = False
                self.search_button.config(state="normal")
        
        threading.Thread(target=index_thread, daemon=True).start()
    
    def _search(self):
        """Perform search with the current query."""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query.")
            return
        
        if not self.current_folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder to search.")
            return
        
        if self.is_indexing:
            messagebox.showinfo("Indexing in Progress", "Please wait for folder indexing to complete.")
            return
        
        self.status_var.set("Searching...")
        self._clear_results()
        
        def search_thread():
            try:
                results = self.vector_search.search(query, top_k=20)
                self._display_results(results)
                self.status_var.set(f"Found {len(results)} matching files")
            except Exception as e:
                self.status_var.set(f"Search error: {str(e)}")
                messagebox.showerror("Search Error", f"Error during search: {str(e)}")
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def _clear_results(self):
        """Clear the results tree."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def _display_results(self, results):
        """Display search results in the tree view."""
        self._clear_results()
        for result in results:
            # Support both 3-tuple and 4-tuple results for backward compatibility
            if len(result) == 4:
                file_path, similarity, content, match_type = result
            else:
                file_path, similarity, content = result
                match_type = "semantic"
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].upper()
            similarity_percent = f"{similarity * 100:.1f}%"
            
            # Insert into tree
            item = self.results_tree.insert("", "end", 
                                          text=filename,
                                          values=(filename, file_path, similarity_percent, file_ext))
    
    def _open_selected_file(self, event):
        """Open the selected file when double-clicked."""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            file_path = item['values'][1]  # Path is the second value
            open_file(file_path)
    
    def _on_closing(self):
        """Handle window closing event."""
        self.root.withdraw()  # Hide instead of destroy to allow reopening
    
    def destroy(self):
        """Completely destroy the window."""
        if self.root:
            self.root.destroy()
            self.root = None
