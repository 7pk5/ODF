"""
Spotlight Search UI for Offline Document Finder
A sleek, borderless, dark-themed search interface using CustomTkinter.
"""

import customtkinter as ctk
import tkinter as tk # For some constants or mixins if needed
from tkinter import filedialog, messagebox
import os
import threading
from search_engine.vector_search import VectorSearch
from search_engine.file_indexer import FileIndexer
from utils.open_file import open_file
from PIL import Image

# Set Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SearchWindow:
    def __init__(self):
        self.root = None
        self.vector_search = VectorSearch()
        self.file_indexer = FileIndexer()
        self.current_folder = None
        self.is_indexing = False
        
        # Dimensions
        self.WIDTH = 800
        self.INITIAL_HEIGHT = 90
        self.MAX_HEIGHT = 600
        
    def show_window(self):
        """Show the search window."""
        if self.root is None:
            self._create_window()
        else:
            self.root.deiconify()
            self._center_window()
            self.root.lift()
            self.root.focus_force()
            self.search_entry.focus_set()
            
        # Check if DB is empty and prompt user
        self.root.after(500, self._check_empty_db)
            
    def _check_empty_db(self):
        """Check if the database is empty and prompt user to index."""
        try:
            stats = self.vector_search.get_stats()
            if stats['count'] == 0:
                # Use standard tkinter messagebox since CTk doesn't have one builtin yet (or it's complex)
                # But to keep it safe from threading issues, we usually run this on main thread.
                # However, messagebox blocks. 
                # Let's use a non-blocking way or just standard message box which is fine.
                response = messagebox.askyesno("Welcome", "No documents found in index.\n\nWould you like to select a folder to index now?")
                if response:
                    self._browse_folder()
        except Exception as e:
            print(f"Error checking DB stats: {e}")
    
    def _create_window(self):
        """Create the main search window."""
        # Use CTk instead of Tk for modern theming
        self.root = ctk.CTk()
        self.root.title("ODF Spotlight")
        
        # Make borderless
        self.root.overrideredirect(True)
        
        # Center initially
        self._center_window()
        
        # Main container with border effect (using frame color)
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15, border_width=2, border_color="#3B8ED0")
        self.main_frame.pack(fill="both", expand=True)
        
        # --- Search Bar Area ---
        self.search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        # Search Icon
        self.search_icon_label = ctk.CTkLabel(self.search_frame, text="🔍", font=("Segoe UI", 24))
        self.search_icon_label.pack(side="left", padx=(5, 10))
        
        # Search Input
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame, 
            textvariable=self.search_var,
            width=600,
            height=50,
            font=("Segoe UI", 20),
            placeholder_text="Type to search documents...",
            border_width=0,
            fg_color="transparent" 
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.focus()
        
        # Close Button (X)
        self.close_btn = ctk.CTkButton(
            self.search_frame, 
            text="✕", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            hover_color="#C42B1C", 
            text_color="#888888",
            font=("Arial", 16),
            command=self.root.destroy
        )
        self.close_btn.pack(side="right", padx=5)

        # --- Separator ---
        self.separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="#333333")
        # Don't pack initially
        
        # --- Results Area ---
        self.results_scroll = ctk.CTkScrollableFrame(
            self.main_frame, 
            corner_radius=10, 
            fg_color="transparent",
            height=0 # Start hidden
        )
        # Don't pack initially
        
        # --- Footer ---
        self.footer_frame = ctk.CTkFrame(self.main_frame, height=30, corner_radius=0, fg_color="transparent")
        self.footer_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.footer_frame, text="Ready", text_color="gray", font=("Segoe UI", 12))
        self.status_label.pack(side="left")
        
        # Progress Bar (initially hidden)
        self.progress_bar = ctk.CTkProgressBar(self.footer_frame, width=200, height=10, progress_color="#3B8ED0")
        self.progress_bar.set(0)
        
        self.index_btn = ctk.CTkButton(
            self.footer_frame, 
            text="📁 Index Folder", 
            command=self._browse_folder,
            width=100,
            height=25,
            font=("Segoe UI", 12),
            fg_color="#2B2B2B",
            hover_color="#3A3A3A"
        )
        self.index_btn.pack(side="right")
        
        # Bindings
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<FocusOut>", self._on_focus_out)
        # Mouse drag to move window
        self.main_frame.bind("<Button-1>", self._start_move)
        self.main_frame.bind("<B1-Motion>", self._do_move)

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _center_window(self):
        """Center the window on the screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - self.WIDTH) // 2
        y = (screen_height - self.MAX_HEIGHT) // 3
        
        self.root.geometry(f"{self.WIDTH}x{self.INITIAL_HEIGHT}+{x}+{y}")
        
    def _on_search_change(self, *args):
        """Handle text changes in search bar (Auto-search)."""
        query = self.search_var.get().strip()
        if len(query) > 1:
            self._search(query)
        else:
            self._hide_results()
            
    def _hide_results(self):
        self.results_scroll.pack_forget()
        self.separator.pack_forget()
        self.root.geometry(f"{self.WIDTH}x{self.INITIAL_HEIGHT}")
            
    def _search(self, query):
        """Perform search."""
        def search_thread():
            try:
                results = self.vector_search.search(query, top_k=10)
                self.root.after(0, lambda: self._display_results(results))
            except Exception as e:
                print(f"Search error: {e}")
        
        threading.Thread(target=search_thread, daemon=True).start()
        
    def _display_results(self, results):
        """Display results and expand window."""
        # Clear existing
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
            
        if not results:
            self.status_label.configure(text="No results found")
            return
            
        self.separator.pack(fill="x", padx=10, pady=5)
        self.results_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        for res in results:
            self._create_result_card(res)
            
        # Expand window
        # Estimate height: 60px per item + header/footer
        content_height = min(self.MAX_HEIGHT, self.INITIAL_HEIGHT + 20 + (len(results) * 75))
        self.root.geometry(f"{self.WIDTH}x{content_height}")
        self.status_label.configure(text=f"Found {len(results)} matches")

    def _create_result_card(self, res):
        """Create a card for a single result."""
        fname = res.get('filename', 'Unknown')
        path = res.get('file_path', '')
        score = int(res.get('similarity', 0) * 100)
        preview = res.get('content', '')[:100].replace('\n', ' ') + "..."
        
        ext = os.path.splitext(fname)[1].lower()
        icon = "📄"
        if ext == '.pdf': icon = "📕"
        elif ext == '.docx': icon = "📘"
        elif ext == '.txt': icon = "📝"
        elif ext in ['.py', '.js', '.html', '.css']: icon = "💻"
        
        card = ctk.CTkFrame(self.results_scroll, fg_color="#2B2B2B", corner_radius=8)
        card.pack(fill="x", pady=5, padx=5)
        
        # Icon
        icon_lbl = ctk.CTkLabel(card, text=icon, font=("Segoe UI", 24))
        icon_lbl.pack(side="left", padx=10, pady=10)
        
        # Text Content (Filename + Preview)
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        name_lbl = ctk.CTkLabel(text_frame, text=fname, font=("Segoe UI", 14, "bold"), anchor="w")
        name_lbl.pack(fill="x")
        
        preview_lbl = ctk.CTkLabel(text_frame, text=preview, font=("Segoe UI", 11), text_color="gray", anchor="w")
        preview_lbl.pack(fill="x")
        
        # Score Badge
        score_lbl = ctk.CTkLabel(card, text=f"{score}%", font=("Segoe UI", 10, "bold"), 
                                fg_color="#3B8ED0", text_color="white", corner_radius=10, width=40)
        score_lbl.pack(side="right", padx=10)
        
        # Hover Effect
        def on_enter(e): card.configure(fg_color="#3A3A3A")
        def on_leave(e): card.configure(fg_color="#2B2B2B")
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        
        # Click to open
        def on_click(e):
            open_file(path)
            # self.root.destroy() # Keep window open
            
        # Bind click to all elements in card
        for w in [card, icon_lbl, text_frame, name_lbl, preview_lbl, score_lbl]:
            w.bind("<Button-1>", on_click)

    def _on_escape(self, event):
        """Handle Esc key."""
        if self.search_var.get():
            self.search_var.set("")
            self._hide_results()
        else:
            self.root.destroy()
            
    def _on_focus_out(self, event):
        """Close window when clicking outside."""
        # Simple implementation - if focus moves to another app, close
        pass
        
    def _browse_folder(self):
        """Open folder browser."""
        folder = filedialog.askdirectory()
        if folder:
            self.status_label.configure(text="Scanning files...")
            self.progress_bar.pack(side="left", padx=10)
            self.progress_bar.set(0)
            self.index_btn.configure(state="disabled")
            
            threading.Thread(target=self._index_thread, args=(folder,), daemon=True).start()
            
    def _index_thread(self, folder):
        try:
            # 1. Scan first
            files = self.file_indexer.scan_directory(folder)
            total_files = len(files)
            
            if total_files == 0:
                 self.root.after(0, lambda: self._indexing_finished("No supported files found."))
                 return

            self.root.after(0, lambda: self.status_label.configure(text=f"Indexing {total_files} files..."))
            
            # 2. Get existing IDs for incremental update
            existing_ids = self.vector_search.get_all_ids()
            
            # 3. Callback for progress
            def on_progress(current_count, filename):
                progress = current_count / total_files
                self.root.after(0, lambda: self._update_progress(progress, current_count, total_files, filename))

            # 4. Process (pass existing_ids to skip duplicates)
            gen = self.file_indexer.process_files(files, existing_ids=existing_ids)
            self.vector_search.add_documents(gen, progress_callback=on_progress)
            
            self.root.after(0, lambda: self._indexing_finished("Indexing Complete!"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._indexing_error(error_msg))

    def _update_progress(self, progress, current, total, filename):
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"Scanning {current}/{total}: {filename[:20]}...")

    def _indexing_finished(self, msg):
        self.progress_bar.set(1)
        self.status_label.configure(text=msg)
        self.progress_bar.pack_forget()
        self.index_btn.configure(state="normal")
        messagebox.showinfo("Done", msg)

    def _indexing_error(self, error_msg):
        self.status_label.configure(text=f"Error: {error_msg}")
        self.progress_bar.pack_forget()
        self.index_btn.configure(state="normal")

    def destroy(self):
        if self.root: self.root.destroy()
