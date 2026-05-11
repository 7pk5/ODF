import hashlib
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

from search_engine.vector_search import VectorSearch
from search_engine.file_indexer import FileIndexer
from utils.open_file import open_file

# -------------------- THEME -------------------- 
THEME = {
    "bg": "#0d0d0d",           # Ultra Dark 
    "card": "#1a1a1a",         # Slightly lighter for contrast 
    "card_hover": "#252525",   # Hover Grey 
    "border": "#444444",       # Light Border for visibility 
    "accent": "#3B8ED0",       # Electric Blue 
    "text_primary": "#FFFFFF",
    "text_secondary": "#808080",
    "danger": "#C42B1C"
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# -------------------- CUSTOM WIDGETS -------------------- 
class CircularProgress(tk.Canvas):
    def __init__(self, master, size=45, bg_color=THEME["bg"],
                 fg_color=THEME["accent"], track_color="#333333"):
        super().__init__(
            master,
            width=size,
            height=size,
            bg=bg_color,
            highlightthickness=0
        )
        self.size = size
        self.fg_color = fg_color
        self.track_color = track_color
        self.percentage = 0
        self.center = size / 2
        self.radius = (size - 8) / 2
        self.stroke_width = 5
        self.draw()

    def set(self, value):
        self.percentage = max(0.0, min(value, 1.0))
        self.draw()

    def draw(self):
        self.delete("all")

        # Background Track 
        self.create_oval(
            self.center - self.radius, self.center - self.radius,
            self.center + self.radius, self.center + self.radius,
            outline="#2b2b2b", width=self.stroke_width
        )

        # Progress Arc 
        if self.percentage >= 1.0:
            self.create_oval(
                self.center - self.radius, self.center - self.radius,
                self.center + self.radius, self.center + self.radius,
                outline="#3B8ED0", width=self.stroke_width
            )
        elif self.percentage > 0:
            angle = -360 * self.percentage
            self.create_arc(
                self.center - self.radius, self.center - self.radius,
                self.center + self.radius, self.center + self.radius,
                start=90, extent=angle, style="arc",
                outline="#3B8ED0", width=self.stroke_width
            )

        # Percentage Text 
        text_content = f"{int(self.percentage * 100)}%"
        self.create_text(
            self.center, self.center,
            text=text_content, fill="white",
            font=("Segoe UI", 10, "bold")
        )


# -------------------- MAIN WINDOW -------------------- 
class SearchWindow:
    WIDTH = 800
    INITIAL_HEIGHT = 160
    MAX_HEIGHT = 700

    def __init__(self):
        self.root = None
        self.vector_search = VectorSearch()
        self.file_indexer = FileIndexer()
        self.results = []
        self.selected_index = -1

    # -------------------- WINDOW LOGIC -------------------- 
    def toggle_window(self):
        if not self.root:
            self.show_window()
        elif self.root.state() in ('withdrawn', 'iconic'):
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
        self.root.overrideredirect(False)
        self.root.title("Offline Document Finder")
        self.root.attributes("-topmost", False)
        self.root.configure(fg_color=THEME["bg"])
        self.root.resizable(True, True)
        self._center()

        self.main = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            fg_color=THEME["bg"],
            border_width=0
        )
        self.main.pack(fill="both", expand=True)

        self._build_search_bar()
        self._build_results()
        self._build_footer()
        self._bind_keys()

        # --- IMPORTANT CHANGE: Fully close the app on exit --- 
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """ 
        Handles the window close event. 
        Destroys the window and forces the python process to exit. 
        """
        try:
            if self.root:
                self.root.quit()    # Stops the main loop 
                self.root.destroy()  # Destroys the UI 
        except Exception as e:
            print(f"Error closing: {e}")

        # Force kill the process to stop any background threads immediately 
        os._exit(0)

    def _center(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = (sw - self.WIDTH) // 2
        y = sh // 4
        self.root.geometry(f"{self.WIDTH}x{self.INITIAL_HEIGHT}+{x}+{y}")

    # -------------------- SEARCH BAR -------------------- 
    def _build_search_bar(self):
        bar = ctk.CTkFrame(self.main, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(bar, text="🔍", font=("Segoe UI", 22)).pack(side="left", padx=(4, 12))

        self.query = tk.StringVar()

        self.search_entry = ctk.CTkEntry(
            bar,
            textvariable=self.query,
            font=("Segoe UI", 18),
            height=48,
            fg_color=THEME["card"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=8,
            placeholder_text="Search documents..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.focus()

        # --- NEW: Submit Button --- 
        self.btn_search = ctk.CTkButton(
            bar,
            text="Search",
            fg_color=THEME["accent"],
            text_color="#000",
            corner_radius=8,
            width=100,
            command=self._on_search_click
        )
        self.btn_search.pack(side="left")

    # -------------------- SEARCH TRIGGER -------------------- 
    def _on_search_click(self):
        q = self.query.get().strip()
        if not q:
            self.status.configure(text="Please enter a search term.")
            return
        self._search(q)

    # -------------------- SEARCH EXECUTION -------------------- 
    def _search(self, query):
        self.status.configure(text="Searching...")

        def task():
            # 1. Fetch more results than needed (e.g., 50) to allow for filtering 
            raw_results = self.vector_search.search(query, top_k=50)

            # 2. De-duplicate: Keep only the best scoring chunk for each file 
            unique_results = []
            seen_files = set()

            for res in raw_results:
                fname = res.get("filename", "unknown")
                if fname not in seen_files:
                    unique_results.append(res)
                    seen_files.add(fname)

            # 3. Slice to get the top 10 UNIQUE files 
            final_results = unique_results[:10]

            self.root.after(0, lambda: self._render_results(final_results))

        threading.Thread(target=task, daemon=True).start()

    # -------------------- RENDER RESULTS -------------------- 
    def _build_results(self):
        self.separator = ctk.CTkFrame(self.main, height=1, fg_color=THEME["border"])
        self.results_view = ctk.CTkScrollableFrame(
            self.main,
            fg_color="transparent",
            corner_radius=0
        )

    def _show_results(self):
        self.separator.pack(fill="x", padx=20, pady=10)
        self.results_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _hide_results(self):
        self.separator.pack_forget()
        self.results_view.pack_forget()
        if self.root.state() != 'zoomed':
            self._animate_height(self.INITIAL_HEIGHT)

    def _render_results(self, results):
        for w in self.results_view.winfo_children():
            w.destroy()
        self.results = results
        self.selected_index = -1

        if not results:
            self.status.configure(text="No results found.")
            self._hide_results()
            return

        self._show_results()
        for i, r in enumerate(results[:10]):  # show only first 10 
            self._create_card(i, r)

        if self.root.state() != 'zoomed':
            height = min(self.MAX_HEIGHT, self.INITIAL_HEIGHT + len(results[:10]) * 85)
            self._animate_height(height)

        self.status.configure(text=f"Showing {len(results[:10])} results")

    # -------------------- RESULT CARD -------------------- 
    def _create_card(self, index, res):
        frame = ctk.CTkFrame(
            self.results_view,
            fg_color=THEME["card"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["border"]
        )
        frame.pack(fill="x", pady=6)

        icon = "📄"
        ext = os.path.splitext(res.get("filename", "file"))[1].lower()
        if ext == ".pdf":
            icon = "📕"
        elif ext == ".docx":
            icon = "📘"
        elif ext == ".txt":
            icon = "📄"

        ctk.CTkLabel(frame, text=icon, font=("Segoe UI", 22)).pack(side="left", padx=12)

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True, pady=8)

        ctk.CTkLabel(
            body,
            text=res.get("filename", "Unknown"),
            font=("Segoe UI", 14, "bold"),
            text_color=THEME["accent"],
            anchor="w"
        ).pack(fill="x")

        content = res.get("content", "")
        preview_text = content[:200].replace("\n", " ") + "..."
        if not content.strip():
            preview_text = "No text content found."

        ctk.CTkLabel(
            body,
            text=preview_text,
            font=("Segoe UI", 11),
            text_color=THEME["text_secondary"],
            anchor="w",
            wraplength=600
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

        # Bindings 
        frame.bind("<Enter>", lambda e: frame.configure(fg_color=THEME["card_hover"], border_color=THEME["accent"]))
        frame.bind("<Leave>", lambda e: frame.configure(fg_color=THEME["card"], border_color=THEME["border"]))
        
        click_handler = lambda e: open_file(res.get("file_path", ""))
        frame.bind("<Button-1>", click_handler)
        
        for child in frame.winfo_children():
            if not isinstance(child, ctk.CTkButton):
                child.bind("<Button-1>", click_handler)
        for child in body.winfo_children():
            child.bind("<Button-1>", click_handler)

    # -------------------- FOOTER -------------------- 
    def _build_footer(self):
        self.footer = ctk.CTkFrame(self.main, fg_color="transparent")
        self.footer.pack(fill="x", padx=20, pady=(0, 20), side="bottom")

        self.status = ctk.CTkLabel(
            self.footer,
            text="Ready",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"]
        )
        self.status.pack(side="left", pady=5)

        self.progress_donut = CircularProgress(
            self.footer,
            size=40,
            bg_color=THEME["bg"]
        )

        # --- UPDATED: Button Container for Right Alignment --- 
        btn_container = ctk.CTkFrame(self.footer, fg_color="transparent")
        btn_container.pack(side="right", padx=0, pady=5)

        # --- NEW: Reset Index Button (Red) --- 
        self.btn_reset = ctk.CTkButton(
            btn_container,
            text=" Reset Index",
            command=self._on_reset_click,
            fg_color=THEME["danger"],
            hover_color="#8B0000",
            width=100,
            height=30
        )
        self.btn_reset.pack(side="left", padx=(0, 10))

        # Existing Index Folder Button 
        self.btn_index = ctk.CTkButton(
            btn_container,
            text=" Index Folder",
            command=self._browse_folder,
            fg_color="#2a2a2a",
            width=120,
            height=30
        )
        self.btn_index.pack(side="left")

    # -------------------- KEYBOARD NAV -------------------- 
    def _bind_keys(self):
        self.root.bind("<Escape>", lambda e: self._on_close())
        self.root.bind("<Return>", lambda e: self._on_search_click())  # NEW: Enter triggers Search 
        self.root.bind("<Down>", self._select_next)
        self.root.bind("<Up>", self._select_prev)

    def _select_next(self, _=None):
        self._select(min(self.selected_index + 1, len(self.results) - 1))

    def _select_prev(self, _=None):
        self._select(max(self.selected_index - 1, 0))

    def _select(self, index):
        children = self.results_view.winfo_children()
        if 0 <= self.selected_index < len(children):
            children[self.selected_index].configure(fg_color=THEME["card"], border_color=THEME["border"])
        self.selected_index = index
        if 0 <= index < len(children):
            children[index].configure(fg_color=THEME["card_hover"], border_color=THEME["accent"])
            self.results_view._parent_canvas.yview_moveto(index / len(children))

    def _open_selected(self, _=None):
        if 0 <= self.selected_index < len(self.results):
            open_file(self.results[self.selected_index]["file_path"])

    # -------------------- ANIMATION -------------------- 
    def _animate_height(self, target):
        if self.root.state() == 'zoomed':
            return
        cur = self.root.winfo_height()
        step = 20 if target > cur else -20

        def run():
            nonlocal cur
            if (step > 0 and cur < target) or (step < 0 and cur > target):
                cur += step
                self.root.geometry(f"{self.WIDTH}x{cur}")
                self.root.after(5, run)
        run()

    # -------------------- INDEXING -------------------- 
    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.status.pack_forget()
        self.progress_donut.pack(side="left", padx=10)
        self.progress_donut.set(0)
        threading.Thread(target=self._index_thread, args=(folder,), daemon=True).start()

    def _index_thread(self, folder):
        try:
            files = self.file_indexer.scan_directory(folder)
            total = len(files)
            if total == 0:
                self.root.after(0, lambda: self.status.configure(text="No supported files found."))
                self.root.after(1500, self._reset_footer)
                return

            existing_ids = self.vector_search.get_all_ids()
            new_files = []
            skipped_count = 0
            self.root.after(0, lambda: self.status.configure(text="Checking file status..."))
            last_update_pct = 0.0

            for i, f in enumerate(files):
                try:
                    stats = os.stat(f)
                    doc_id = hashlib.md5(f"{f}_{stats.st_mtime}".encode()).hexdigest()
                    if doc_id in existing_ids:
                        skipped_count += 1
                    else:
                        new_files.append(f)

                    current_progress = (i + 1) / total
                    if current_progress - last_update_pct >= 0.01:
                        self.root.after(0, lambda p=current_progress: self.progress_donut.set(p))
                        last_update_pct = current_progress
                except Exception:
                    new_files.append(f)

            final_skipped_pct = skipped_count / total
            self.root.after(0, lambda: self.progress_donut.set(final_skipped_pct))

            if not new_files:
                self.root.after(0, lambda: self.progress_donut.set(1.0))
                self.root.after(0, lambda: self.status.configure(text="All files up to date."))
                self.root.after(1500, self._reset_footer)
                return

            self.root.after(0, lambda: self.status.configure(text=f"Indexing {len(new_files)} new files..."))

            def progress_callback(i, name):
                current_total = skipped_count + i
                pct = current_total / total
                self.root.after(0, lambda: self.progress_donut.set(pct))

            gen = self.file_indexer.process_files(new_files, existing_ids=existing_ids)
            self.vector_search.add_documents(gen, progress_callback=progress_callback)

            self.root.after(0, lambda: self.progress_donut.set(1.0))
            self.root.after(0, lambda: self.status.configure(text=f"Indexed {len(new_files)} new files."))

        except Exception as e:
            print(f"Indexing error: {e}")
            self.root.after(0, lambda: self.status.configure(text="Error during indexing."))
        finally:
            self.root.after(2000, self._reset_footer)

    def _reset_footer(self):
        self.progress_donut.pack_forget()
        self.status.pack(side="left", pady=5)

    def _check_empty_db(self):
        try:
            if self.vector_search.get_stats()["count"] == 0:
                if messagebox.askyesno("Welcome", "No documents indexed. Index now?"):
                    self._browse_folder()
        except:
            pass

    # --- NEW: Handler for Resetting Index --- 
    def _on_reset_click(self):
        """ 
        Deletes all indexed data after confirmation. 
        """
        msg = "Are you sure you want to delete all indexed documents?\nThis action cannot be undone."
        if messagebox.askyesno("Reset Index", msg):
            try:
                # 1. Clear UI Results 
                for w in self.results_view.winfo_children():
                    w.destroy()
                self.results = []
                self.status.configure(text="Clearing database...")

                # 2. Call Backend 
                if hasattr(self.vector_search, 'clear_database'):
                    success = self.vector_search.clear_database()
                    if success:
                        self.status.configure(text="Database cleared.")
                        messagebox.showinfo("Success", "All indexed documents have been removed.")
                    else:
                        self.status.configure(text="Error clearing DB.")
                        messagebox.showerror("Error", "Failed to clear database.")
                else:
                    msg_err = "Your backend is outdated.\nPlease add 'clear_database()' to vector_search.py."
                    messagebox.showerror("Error", msg_err)
            except Exception as e:
                print(f"Error resetting: {e}")
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
