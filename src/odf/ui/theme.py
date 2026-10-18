"""Colours and file-type icons for the search window."""

import os

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

FILE_ICONS = {".pdf": "📕", ".docx": "📘", ".txt": "📄"}
DEFAULT_ICON = "📄"


def file_icon(filename):
    """Icon for a filename based on its extension."""
    return FILE_ICONS.get(os.path.splitext(filename)[1].lower(), DEFAULT_ICON)
