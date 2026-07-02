"""
Cross-platform path resolution for ODF data, models, logs, and ChromaDB.

All other modules import from here instead of hard-coding %APPDATA% or
platform checks. Three storage modes:

  Frozen/EXE  → user-writable OS data dir (never needs admin rights)
  Script mode → project root (developer convenience)

Platform mapping (frozen mode):
  Windows : %APPDATA%/ODF/
  macOS   : ~/Library/Application Support/ODF/
  Linux   : $XDG_DATA_HOME/ODF/  (defaults to ~/.local/share/ODF/)
"""

import os
import sys


def _user_data_root() -> str:
    """Return the platform-appropriate ODF data root (frozen/EXE mode only)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:  # Linux / BSD / other POSIX
        base = os.environ.get(
            "XDG_DATA_HOME",
            os.path.join(os.path.expanduser("~"), ".local", "share"),
        )
    return os.path.join(base, "ODF")


def _project_root() -> str:
    # utils/ is one level below the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_data_dir() -> str:
    """
    Root ODF data directory, writable without admin rights.
    Frozen → OS user-data dir.  Script → project root.
    """
    return _user_data_root() if getattr(sys, "frozen", False) else _project_root()


def log_path() -> str:
    """Full path to odf.log. Parent directory is created if absent."""
    d = app_data_dir()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "odf.log")


def model_cache_dir() -> str:
    """Directory where FastEmbed caches the AI model. Created if absent."""
    d = os.path.join(app_data_dir(), "models")
    os.makedirs(d, exist_ok=True)
    return d


def chroma_db_dir() -> str:
    """Directory for the ChromaDB persistent store. Created if absent."""
    d = os.path.join(app_data_dir(), "data", "chroma_db")
    os.makedirs(d, exist_ok=True)
    return d
