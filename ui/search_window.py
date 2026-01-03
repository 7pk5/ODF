import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
from PIL import Image

from search_engine.vector_search import VectorSearch
from search_engine.file_indexer import FileIndexer
from utils.open_file import open_file

# -------------------- THEME --------------------
THEME = {
    "bg": "#0d0d0d",          # Ultra Dark
    "card": "transparent",    # Ghost Cards (Default)
    "card_hover": "#252525",  # Hover Grey
    "border": "#444444",      # Lightened Border for visibility
    "accent": "#3B8ED0",      # Electric Blue
    "text_primary": "#FFFFFF",
    "text_secondary": "#808080",
    "danger": "#C42B1C"
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SearchWindow:
    WIDTH = 800
    INITIAL_HEIGHT = 140
    MAX_HEIGHT = 600

    def __init__(self):
        self.root = None
        self.vector_search = VectorSearch()
        self.file_indexer = FileIndexer()

        self.results = []
        self.selected_index = -1
        self.search_counter = 0

    # -------------------- WINDOW --------------------
    def toggle_window(self):
        """Toggle window visibility."""
        if not self.root:
            self.show_window()
        elif self.root.state() == 'withdrawn':
            self.show_window()
        else:
            self.root.withdraw()

    def show_window(self):
        if not self.root:
            self._create_window()
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.search_entry.focus_set()

        self.root.after(400, self._check_empty_db)

    def _create_window(self):
        self.root = ctk.CTk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97) # Glassmorphism
        self.root.configure(fg_color=THEME["bg"])
        self._center()

        self.main = ctk.CTkFrame(
            self.root,
            corner_radius=16,
            fg_color=THEME["card"],
            border_width=1,
            border_color=THEME["border"]
        )
        self.main.pack(fill="both", expand=True)

        self._build_search_bar()
        self._build_results()
        self._build_footer()
        self._bind_keys()
        self._bind_drag()

    def _center(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = (sw - self.WIDTH) // 2
        y = sh // 4
        self.root.geometry(f"{self.WIDTH}x{self.INITIAL_HEIGHT}+{x}+{y}")

    # -------------------- SEARCH BAR --------------------
    def _build_search_bar(self):
        bar = ctk.CTkFrame(self.main, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(bar, text="🔍", font=("Segoe UI", 22)).pack(side="left", padx=(4, 12))

        self.query = tk.StringVar()
        self.query.trace_add("write", self._on_query_change)

        self.search_entry = ctk.CTkEntry(
            bar,
            textvariable=self.query,
            font=("Segoe UI", 18),
            height=48,
            fg_color="transparent",
            border_width=1,
            border_color=THEME["border"],
            corner_radius=8,
            placeholder_text="Search documents..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.focus()

        ctk.CTkButton(
            bar,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=THEME["danger"],
            command=self.root.destroy
        ).pack(side="right")

        ctk.CTkButton(
            bar,
            text="−", # Minimize/Hide
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=THEME["card_hover"],
            command=self.toggle_window
        ).pack(side="right", padx=(0, 4))

    # -------------------- RESULTS --------------------
    def _build_results(self):
        self.separator = ctk.CTkFrame(self.main, height=1, fg_color=THEME["border"])
        self.results_view = ctk.CTkScrollableFrame(
            self.main,
            fg_color="transparent",
            corner_radius=0
        )

    def _show_results(self):
        self.separator.pack(fill="x", padx=12, pady=6)
        self.results_view.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _hide_results(self):
        self.separator.pack_forget()
        self.results_view.pack_forget()
        self._animate_height(self.INITIAL_HEIGHT)

    # -------------------- FOOTER --------------------
    def _build_footer(self):
        footer = ctk.CTkFrame(self.main, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 10))

        self.status = ctk.CTkLabel(
            footer,
            text="Ready",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"]
        )
        self.status.pack(side="left")

        self.progress = ctk.CTkProgressBar(
            footer,
            width=200,
            height=6,
            progress_color=THEME["accent"]
        )
        self.progress.set(0)

        ctk.CTkButton(
            footer,
            text="📁 Index Folder",
            command=self._browse_folder,
            fg_color="#2a2a2a",
            width=120,
            height=30
        ).pack(side="right", padx=10, pady=5)

    # -------------------- SEARCH --------------------
    def _on_query_change(self, *_):
        q = self.query.get().strip()
        if len(q) > 1:
            self._search(q)
        else:
            self._hide_results()

    def _search(self, query):
        def task():
            res = self.vector_search.search(query, top_k=10)
            self.root.after(0, lambda: self._render_results(res))

        threading.Thread(target=task, daemon=True).start()

    def _render_results(self, results):
        for w in self.results_view.winfo_children():
            w.destroy()

        self.results = results
        self.selected_index = -1

        if not results:
            self.status.configure(text="No results")
            return

        self._show_results()

        for i, r in enumerate(results):
            self._create_card(i, r)

        height = min(self.MAX_HEIGHT, self.INITIAL_HEIGHT + len(results) * 78)
        self._animate_height(height)
        self.status.configure(text=f"{len(results)} results")

    # -------------------- RESULT CARD --------------------
    def _create_card(self, index, res):
        frame = ctk.CTkFrame(
            self.results_view,
            fg_color=THEME["card"],
            corner_radius=10,
            border_width=0,
            border_color=THEME["border"]
        )
        frame.pack(fill="x", pady=6)

        icon = "📄"
        ext = os.path.splitext(res.get("filename", "file"))[1].lower()
        if ext == ".pdf": icon = "📕"
        elif ext == ".docx": icon = "�"
        elif ext == ".txt": icon = "�"

        ctk.CTkLabel(frame, text=icon, font=("Segoe UI", 22)).pack(side="left", padx=12)

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            body,
            text=res.get("filename", "Unknown"),
            font=("Segoe UI", 14, "bold"),
            text_color=THEME["accent"],
            anchor="w"
        ).pack(fill="x")

        # DEBUG PRINT
        # if "content" in res:
        #      print(f"DEBUG: Result content for {res.get('filename')}: {repr(res['content'][:50])}")
        
        content = res.get("content", "")
        preview_text = content[:100].replace("\n", " ") + "..."
        if not content.strip():
            preview_text = "No text content found (scanned PDF or empty)."

        ctk.CTkLabel(
            body,
            text=preview_text,
            font=("Segoe UI", 11),
            text_color=THEME["text_secondary"],
            anchor="w",
            wraplength=520
        ).pack(fill="x")

        score = int(res.get("similarity", 0) * 100)
        ctk.CTkLabel(
            frame,
            text=f"{score}%",
            fg_color=THEME["accent"],
            text_color="#000",
            corner_radius=12,
            width=48
        ).pack(side="right", padx=12)

        frame.bind("<Enter>", lambda e: frame.configure(fg_color=THEME["card_hover"]))
        frame.bind("<Leave>", lambda e: frame.configure(fg_color=THEME["card"]))
        frame.bind("<Button-1>", lambda e: open_file(res.get("file_path", "")))
        
        # Helper to bind child widgets too
        for child in frame.winfo_children():
            # Don't bind buttons if any
            if not isinstance(child, ctk.CTkButton):
                child.bind("<Button-1>", lambda e: open_file(res.get("file_path", "")))
        for child in body.winfo_children():
            child.bind("<Button-1>", lambda e: open_file(res.get("file_path", "")))

        frame._ref = frame

    # -------------------- KEYBOARD NAV --------------------
    def _bind_keys(self):
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Down>", self._select_next)
        self.root.bind("<Up>", self._select_prev)
        self.root.bind("<Return>", self._open_selected)

    def _select_next(self, _=None):
        self._select(min(self.selected_index + 1, len(self.results) - 1))

    def _select_prev(self, _=None):
        self._select(max(self.selected_index - 1, 0))

    def _select(self, index):
        children = self.results_view.winfo_children()
        if 0 <= self.selected_index < len(children):
            children[self.selected_index].configure(fg_color=THEME["card"])

        self.selected_index = index
        if 0 <= index < len(children):
            children[index].configure(fg_color=THEME["card_hover"])

    def _open_selected(self, _=None):
        if 0 <= self.selected_index < len(self.results):
            open_file(self.results[self.selected_index]["file_path"])

    # -------------------- DRAGGING --------------------
    def _bind_drag(self):
        # Bind dragging to all major container frames to ensure capture
        frames = [self.main, self.status, self.search_entry, self.separator]
        
        # Also bind to the specific frames that might block clicks
        if hasattr(self, 'footer_frame'): frames.append(self.footer_frame) # If you named it
        
        # Recursive bind helper
        def bind_recursive(widget):
            try:
                widget.bind("<Button-1>", self._start_move)
                widget.bind("<B1-Motion>", self._do_move)
            except: pass
            
        # Bind main background
        self.main.bind("<Button-1>", self._start_move)
        self.main.bind("<B1-Motion>", self._do_move)
        
        # Bind Status Label
        if self.status:
            self.status.bind("<Button-1>", self._start_move)
            self.status.bind("<B1-Motion>", self._do_move)
            
    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    # -------------------- ANIMATION --------------------
    def _animate_height(self, target):
        cur = self.root.winfo_height()
        step = 12 if target > cur else -12

        def run():
            nonlocal cur
            if (step > 0 and cur < target) or (step < 0 and cur > target):
                cur += step
                self.root.geometry(f"{self.WIDTH}x{cur}")
                self.root.after(8, run)

        run()

    # -------------------- INDEXING --------------------
    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.progress.pack(side="left", padx=12)
        threading.Thread(target=self._index_thread, args=(folder,), daemon=True).start()

    def _index_thread(self, folder):
        files = self.file_indexer.scan_directory(folder)
        total = len(files)
        
        existing_ids = self.vector_search.get_all_ids()

        def progress(i, name):
            self.root.after(0, lambda: self.progress.set(i / total))

        gen = self.file_indexer.process_files(files, existing_ids=existing_ids)
        self.vector_search.add_documents(gen, progress_callback=progress)

        self.root.after(0, lambda: self.progress.pack_forget())

    def _check_empty_db(self):
        try:
            if self.vector_search.get_stats()["count"] == 0:
                if messagebox.askyesno("Welcome", "No documents indexed. Index now?"):
                    self._browse_folder()
        except:
            pass
