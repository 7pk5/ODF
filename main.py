"""
Offline Document Finder (ODF)
A smart AI-powered desktop tool for semantic search of local documents.
"""

import os
import sys
import logging

import keyboard
from ui.search_window import SearchWindow


def _setup_logging():
    """Write logs to %APPDATA%/ODF/odf.log (or project root in script mode)."""
    if getattr(sys, 'frozen', False):
        log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'ODF')
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'odf.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_path


def _check_vcredist():
    """On Windows, ONNX Runtime needs VCREDIST 2019+. Warn early if DLLs are missing."""
    if sys.platform != "win32":
        return
    import ctypes
    missing = [dll for dll in ("msvcp140.dll", "vcruntime140.dll")
               if not ctypes.util.find_library(dll)]
    if missing:
        try:
            import tkinter as tk
            from tkinter import messagebox
            _r = tk.Tk()
            _r.withdraw()
            messagebox.showerror(
                "Missing System Requirement",
                "ODF requires the Microsoft Visual C++ Redistributable (2019 or later),\n"
                "which is not installed on this PC.\n\n"
                "Please download and install it from:\n"
                "https://aka.ms/vs/17/release/vc_redist.x64.exe\n\n"
                "After installing, restart ODF.",
            )
        except Exception:
            pass
        sys.exit(1)


def main():
    log_path = _setup_logging()
    logging.info("ODF starting")
    _check_vcredist()
    try:
        _run()
    except Exception as exc:
        logging.exception("Fatal error")
        try:
            import tkinter as tk
            from tkinter import messagebox
            _r = tk.Tk()
            _r.withdraw()
            messagebox.showerror(
                "ODF — Fatal Error",
                f"ODF crashed unexpectedly.\n\nError: {exc}\n\nLog: {log_path}",
            )
        except Exception:
            pass
        sys.exit(1)


def _run():
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    os.makedirs(models_dir, exist_ok=True)

    search_window = SearchWindow()

    try:
        keyboard.add_hotkey('ctrl+k', search_window.toggle_window)
        logging.info("Global hotkey Ctrl+K registered")
    except Exception as e:
        logging.warning("Could not bind hotkey: %s", e)

    try:
        search_window.show_window()
        search_window.root.mainloop()
    except KeyboardInterrupt:
        logging.info("Shutting down")
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()


