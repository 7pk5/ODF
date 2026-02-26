"""
ODF Search Window
Spotlight-inspired UI: clean, minimal, two-panel layout.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import platform
import datetime

from search_engine.vector_search import VectorSearch
from search_engine.file_indexer import FileIndexer
from utils.open_file import open_file

# ── Colour palette ───────────────────────────────────────────────
BG         = "#1c1c1e"   # Window background  (macOS-dark)
BG_PANEL   = "#242426"   # Right detail panel
HOVER      = "#3a3a3c"   # Row hover
SELECTED   = "#0A84FF"   # Apple-blue selection
SEPARATOR  = "#38383a"   # Divider lines
TEXT_1     = "#ffffff"   # Primary text
TEXT_2     = "#98989e"   # Secondary / muted text
ACCENT     = "#0A84FF"   # Button accent
DANGER     = "#ff453a"   # Danger / close
FONT       = "Segoe UI" if platform.system() == "Windows" else "Helvetica"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class SearchWindow:
    # Layout constants
    WIDTH         = 740
    LIST_W        = 400   # left panel width
    DETAIL_W      = 300   # right panel width  (LIST_W + DETAIL_W = 700 + padding)
    BAR_H         = 64    # search-bar-only height
    FOOTER_H      = 38    # always-visible footer
    IDLE_H        = BAR_H + FOOTER_H   # collapsed window height
    ROW_H         = 58    # each result row
    MAX_ROWS      = 6     # rows visible before scrolling
    MAX_H         = BAR_H + FOOTER_H + MAX_ROWS * ROW_H + 2  # max window height

    def __init__(self):
        self.root         = None
        self.vector_search = VectorSearch()
        self.file_indexer  = FileIndexer()
        self.results       = []
        self.selected_idx  = -1
        self.search_timer  = None
        self._win_h       = self.IDLE_H   # track window height manually

    # ── Window lifecycle ─────────────────────────────────────────

    def toggle_window(self):
        if not self.root:
            self._build()
        elif self.root.state() == "withdrawn":
            self._reveal()
        else:
            self.root.withdraw()

    def show_window(self):
        if not self.root:
            self._build()
        else:
            self._reveal()

    def _reveal(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.search_entry.focus_set()
        self.root.after(350, self._check_empty_db)

    def _build(self):
        self.root = ctk.CTk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.configure(fg_color=BG)
        self._center()

        # Single outer frame — gives us the rounded border
        self.shell = ctk.CTkFrame(
            self.root,
            fg_color=BG,
            corner_radius=14,
            border_width=1,
            border_color=SEPARATOR,
        )
        self.shell.pack(fill="both", expand=True)
        self.shell.pack_propagate(False)   # window size controlled by geometry only

        self._make_search_bar()
        self._make_footer()          # packed to bottom; always visible
        self._make_body()            # packed in middle; hidden until results

        self._bind_keys()
        self._bind_drag()
        self.root.after(350, self._check_empty_db)

    def _center(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - self.WIDTH) // 2
        y  = int(sh * 0.20)
        self._win_h = self.IDLE_H
        self.root.geometry(f"{self.WIDTH}x{self._win_h}+{x}+{y}")

    # ── Search bar ───────────────────────────────────────────────

    def _make_search_bar(self):
        bar = ctk.CTkFrame(self.shell, fg_color="transparent", height=self.BAR_H)
        bar.pack(fill="x", padx=14, pady=0)
        bar.pack_propagate(False)

        # Search glyph
        ctk.CTkLabel(
            bar, text="⌕",
            font=(FONT, 26),
            text_color=TEXT_2,
            width=34,
        ).pack(side="left", padx=(4, 8))

        # Text input
        self.query = tk.StringVar()
        self.query.trace_add("write", self._on_type)
        self.search_entry = ctk.CTkEntry(
            bar,
            textvariable=self.query,
            font=(FONT, 20),
            fg_color="transparent",
            border_width=0,
            text_color=TEXT_1,
            placeholder_text="Search documents…",
            placeholder_text_color=TEXT_2,
        )
        self.search_entry.pack(side="left", fill="both", expand=True, ipady=4)
        self.search_entry.focus()

        # ESC pill
        esc = ctk.CTkLabel(
            bar, text="esc",
            font=(FONT, 10),
            text_color=TEXT_2,
            fg_color=HOVER,
            corner_radius=4,
            width=30, height=18,
        )
        esc.pack(side="right", padx=(0, 4))
        esc.bind("<Button-1>", lambda e: self.root.withdraw())

    # ── Footer (always visible) ───────────────────────────────────

    def _make_footer(self):
        foot = ctk.CTkFrame(self.shell, fg_color="transparent", height=self.FOOTER_H)
        foot.pack(side="bottom", fill="x", padx=14, pady=(0, 6))
        foot.pack_propagate(False)

        self.status_lbl = ctk.CTkLabel(
            foot, text="",
            font=(FONT, 11),
            text_color=TEXT_2,
        )
        self.status_lbl.pack(side="left", padx=2)

        self.progress = ctk.CTkProgressBar(
            foot, width=120, height=3,
            progress_color=ACCENT,
        )
        self.progress.set(0)

        ctk.CTkButton(
            foot,
            text="＋  Index Folder",
            font=(FONT, 11),
            fg_color=HOVER,
            hover_color="#4a4a4c",
            text_color=TEXT_1,
            corner_radius=6,
            height=26, width=130,
            command=self._browse_folder,
        ).pack(side="right")

    # ── Body: divider + list + detail ────────────────────────────

    def _make_body(self):
        self.divider = ctk.CTkFrame(self.shell, fg_color=SEPARATOR, height=1)

        self.body = ctk.CTkFrame(self.shell, fg_color="transparent")

        # ── Left: scrollable result rows ──
        self.list_frame = ctk.CTkScrollableFrame(
            self.body,
            fg_color="transparent",
            scrollbar_button_color=SEPARATOR,
            scrollbar_button_hover_color=HOVER,
            width=self.LIST_W,
            height=self.ROW_H,   # will be resized dynamically in _render
        )
        self.list_frame.pack(side="left", fill="y", padx=(4, 0), pady=4)

        # ── Vertical separator ──
        self.vsep = ctk.CTkFrame(self.body, fg_color=SEPARATOR, width=1)
        self.vsep.pack(side="left", fill="y", pady=8)

        # ── Right: detail panel ──
        self.detail = ctk.CTkFrame(
            self.body,
            fg_color=BG_PANEL,
            corner_radius=0,
            width=self.DETAIL_W,
            height=self.ROW_H,   # will be resized dynamically in _render
        )
        self.detail.pack(side="right", fill="y", padx=0, pady=0)
        self.detail.pack_propagate(False)
        self._detail_placeholder()

    def _show_body(self):
        self.divider.pack(fill="x")
        self.body.pack(fill="x")

    def _hide_body(self):
        self.body.pack_forget()
        self.divider.pack_forget()
        self.list_frame.configure(height=self.ROW_H)
        self.detail.configure(height=self.ROW_H)
        self._animate(self.IDLE_H)
        self._detail_placeholder()

    # ── Detail panel ─────────────────────────────────────────────

    def _detail_placeholder(self):
        for w in self.detail.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.detail,
            text="←  select a result",
            font=(FONT, 12),
            text_color=TEXT_2,
            justify="center",
        ).place(relx=0.5, rely=0.44, anchor="center")

    def _detail_fill(self, res):
        for w in self.detail.winfo_children():
            w.destroy()

        ext   = os.path.splitext(res.get("filename", ""))[1].lower()
        icons = {".pdf": "📕", ".docx": "📘", ".txt": "📄"}
        icon  = icons.get(ext, "📄")

        pad = ctk.CTkFrame(self.detail, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=16, pady=16)

        # Big file icon
        ctk.CTkLabel(pad, text=icon, font=(FONT, 40)).pack(anchor="w")

        # Filename
        ctk.CTkLabel(
            pad,
            text=res.get("filename", "Unknown"),
            font=(FONT, 13, "bold"),
            text_color=TEXT_1,
            wraplength=self.DETAIL_W - 36,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(6, 10))

        # Metadata rows
        meta      = res.get("metadata", {})
        size_b    = meta.get("size", 0)
        size_str  = (f"{size_b/1024:.1f} KB" if size_b < 1_048_576
                     else f"{size_b/1_048_576:.1f} MB")
        mtime     = meta.get("modified", 0)
        date_str  = (datetime.datetime.fromtimestamp(mtime).strftime("%d %b %Y")
                     if mtime else "—")
        score_str = f"{int(res.get('similarity', 0) * 100)}%"

        for label, value in [
            ("Type",     ext.upper().lstrip(".") or "—"),
            ("Size",     size_str),
            ("Modified", date_str),
            ("Match",    score_str),
        ]:
            r = ctk.CTkFrame(pad, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=label,  font=(FONT, 11),
                         text_color=TEXT_2, width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=value,  font=(FONT, 11),
                         text_color=TEXT_1, anchor="w").pack(side="left")

        # Thin rule
        ctk.CTkFrame(pad, fg_color=SEPARATOR, height=1).pack(fill="x", pady=(10, 8))

        # Content preview
        ctk.CTkLabel(pad, text="Preview",
                     font=(FONT, 11), text_color=TEXT_2, anchor="w").pack(fill="x")

        raw     = res.get("content", "").strip()
        preview = (raw[:200] + "…") if len(raw) > 200 else raw or "No preview available."
        ctk.CTkLabel(
            pad,
            text=preview,
            font=(FONT, 10),
            text_color=TEXT_2,
            wraplength=self.DETAIL_W - 36,
            justify="left",
            anchor="nw",
        ).pack(fill="x", pady=(4, 0))

        # Open button pinned to bottom
        ctk.CTkButton(
            pad,
            text="Open File  →",
            font=(FONT, 12, "bold"),
            fg_color=ACCENT,
            hover_color="#0066cc",
            corner_radius=8,
            height=32,
            command=lambda: open_file(res.get("file_path", "")),
        ).pack(fill="x", side="bottom", pady=(8, 0))

    # ── Typing / debounce ────────────────────────────────────────

    def _on_type(self, *_):
        q = self.query.get().strip()
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
            self.search_timer = None
        if len(q) >= 2:
            self.search_timer = self.root.after(280, lambda: self._do_search(q))
        else:
            self._hide_body()
            self.status_lbl.configure(text="")

    def _do_search(self, q):
        def run():
            res = self.vector_search.search(q, top_k=8)
            self.root.after(0, lambda: self._render(res))
        threading.Thread(target=run, daemon=True).start()

    # ── Render results ───────────────────────────────────────────

    def _render(self, results):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.results     = results
        self.selected_idx = -1

        if not results:
            self._hide_body()
            self.status_lbl.configure(text="No results")
            return

        self._show_body()
        self.status_lbl.configure(
            text=f"{len(results)} result{'s' if len(results) > 1 else ''}"
        )

        for i, r in enumerate(results):
            self._make_row(i, r)

        self._select(0)

        rows      = min(len(results), self.MAX_ROWS)
        content_h = rows * self.ROW_H + 8   # 8 = pady top+bottom on list_frame
        self.list_frame.configure(height=content_h)
        self.detail.configure(height=content_h)

        target = self.BAR_H + 1 + content_h + self.FOOTER_H
        self._animate(min(target, self.MAX_H))

    def _make_row(self, idx, res):
        ext   = os.path.splitext(res.get("filename", ""))[1].lower()
        icons = {".pdf": "📕", ".docx": "📘", ".txt": "📄"}
        icon  = icons.get(ext, "📄")
        score = int(res.get("similarity", 0) * 100)

        row = ctk.CTkFrame(
            self.list_frame,
            fg_color="transparent",
            corner_radius=8,
            height=self.ROW_H,
        )
        row.pack(fill="x", padx=4, pady=2)
        row.pack_propagate(False)

        # Icon
        ctk.CTkLabel(row, text=icon, font=(FONT, 22), width=38).pack(
            side="left", padx=(6, 2)
        )

        # Text
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", fill="both", expand=True, pady=8)

        name = ctk.CTkLabel(
            txt,
            text=res.get("filename", "Unknown"),
            font=(FONT, 13, "bold"),
            text_color=TEXT_1,
            anchor="w",
        )
        name.pack(fill="x")

        path     = res.get("file_path", "")
        short_p  = ("…" + path[-40:]) if len(path) > 43 else path
        path_lbl = ctk.CTkLabel(
            txt,
            text=short_p,
            font=(FONT, 10),
            text_color=TEXT_2,
            anchor="w",
        )
        path_lbl.pack(fill="x")

        # Score
        score_lbl = ctk.CTkLabel(
            row,
            text=f"{score}%",
            font=(FONT, 11, "bold"),
            text_color=TEXT_2,
            width=38,
            anchor="e",
        )
        score_lbl.pack(side="right", padx=(0, 10))

        # Events — bind to all children so the whole row is clickable
        for w in (row, txt, name, path_lbl, score_lbl):
            w.bind("<Enter>",    lambda e, i=idx: self._hover(i))
            w.bind("<Button-1>", lambda e, i=idx: self._click(i))

        # Stash child refs so we can recolour on selection
        row._name_lbl  = name
        row._path_lbl  = path_lbl
        row._score_lbl = score_lbl

    # ── Selection logic ──────────────────────────────────────────

    def _hover(self, idx):
        if idx != self.selected_idx:
            self._select(idx)

    def _click(self, idx):
        self._select(idx)
        self._open_selected()

    def _select(self, idx):
        rows = self.list_frame.winfo_children()

        # De-highlight old row
        if 0 <= self.selected_idx < len(rows):
            old = rows[self.selected_idx]
            old.configure(fg_color="transparent")
            old._name_lbl.configure(text_color=TEXT_1)
            old._path_lbl.configure(text_color=TEXT_2)
            old._score_lbl.configure(text_color=TEXT_2)

        self.selected_idx = idx

        # Highlight new row
        if 0 <= idx < len(rows):
            new = rows[idx]
            new.configure(fg_color=SELECTED)
            new._name_lbl.configure(text_color=TEXT_1)
            new._path_lbl.configure(text_color="#d0e8ff")
            new._score_lbl.configure(text_color=TEXT_1)
            if idx < len(self.results):
                self._detail_fill(self.results[idx])

    # ── Keyboard navigation ──────────────────────────────────────

    def _bind_keys(self):
        self.root.bind("<Escape>", lambda e: self.root.withdraw())
        self.root.bind("<Down>",   lambda e: self._move(+1))
        self.root.bind("<Up>",     lambda e: self._move(-1))
        self.root.bind("<Return>", lambda e: self._open_selected())

    def _move(self, delta):
        new = max(0, min(self.selected_idx + delta, len(self.results) - 1))
        self._select(new)

    def _open_selected(self):
        if 0 <= self.selected_idx < len(self.results):
            open_file(self.results[self.selected_idx]["file_path"])

    # ── Drag to move window ──────────────────────────────────────

    def _bind_drag(self):
        self.shell.bind("<Button-1>",  self._drag_start)
        self.shell.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    # ── Smooth height animation ───────────────────────────────────

    def _animate(self, target):
        if self._win_h == target:
            return

        def tick():
            diff = target - self._win_h
            if abs(diff) <= 3:
                self._win_h = target
                self.root.geometry(f"{self.WIDTH}x{target}")
                return
            step = max(4, abs(diff) // 4)
            self._win_h += step if diff > 0 else -step
            self.root.geometry(f"{self.WIDTH}x{self._win_h}")
            self.root.after(8, tick)

        tick()

    # ── Indexing ─────────────────────────────────────────────────

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        # Warn if user selected a root drive (D:\, C:\, etc.)
        norm = os.path.normpath(folder)
        drive, tail = os.path.splitdrive(norm)
        if (drive and tail in ("\\", "/", "")) or norm == "/":
            proceed = messagebox.askyesno(
                "Large Folder Warning",
                f"You selected an entire drive ({drive}\\).\n\n"
                "Indexing a whole drive can take a very long time and may slow your PC.\n\n"
                "Recommended: select a specific folder (e.g. Documents, Desktop).\n\n"
                "Continue anyway?",
            )
            if not proceed:
                return

        self.progress.pack(side="left", padx=(8, 0))
        threading.Thread(target=self._index_thread, args=(folder,), daemon=True).start()

    def _index_thread(self, folder):
        try:
            files = self.file_indexer.scan_directory(folder)
            if not files:
                self.root.after(
                    0, lambda: messagebox.showinfo(
                        "No Files", "No PDF or DOCX files found in that folder."
                    )
                )
                self.root.after(0, lambda: self.progress.pack_forget())
                return

            total    = len(files)
            existing = self.vector_search.get_all_ids()

            # Throttle UI updates — only refresh every 5 files to avoid flooding
            # the event queue and freezing the window
            def on_progress(i, name):
                if total > 0 and (i % 5 == 0 or i == total):
                    pct = i / total
                    self.root.after(0, lambda p=pct: self.progress.set(p))
                    self.root.after(
                        0, lambda n=i: self.status_lbl.configure(
                            text=f"Indexing  {n} / {total}"
                        )
                    )

            gen = self.file_indexer.process_files(files, existing_ids=existing)
            self.vector_search.add_documents(gen, progress_callback=on_progress)

            self.root.after(
                0, lambda: messagebox.showinfo(
                    "Done ✓", f"Indexed {total} file{'s' if total > 1 else ''} successfully."
                )
            )
            self.root.after(
                0, lambda: self.status_lbl.configure(text=f"{total} files indexed")
            )

        except Exception as ex:
            self.root.after(0, lambda: messagebox.showerror("Error", str(ex)))
        finally:
            self.root.after(0, lambda: self.progress.pack_forget())

    def _check_empty_db(self):
        try:
            if self.vector_search.get_stats()["count"] == 0:
                if messagebox.askyesno(
                    "Welcome to ODF",
                    "No documents indexed yet.\nWould you like to index a folder now?",
                ):
                    self._browse_folder()
        except Exception:
            pass
