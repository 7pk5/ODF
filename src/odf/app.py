"""
Offline Document Finder (ODF)
A smart AI-powered desktop tool for semantic search of local documents.
"""

import sys
import logging

import keyboard
from odf.logging_setup import setup_logging
from odf.ui.search_window import SearchWindow

log = logging.getLogger(__name__)


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
    log_path = setup_logging()
    log.info("ODF starting")
    _check_vcredist()
    try:
        _run()
    except Exception as exc:
        log.exception("Fatal error")
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
    search_window = SearchWindow()

    try:
        keyboard.add_hotkey('ctrl+k', search_window.toggle_window)
        log.info("Global hotkey Ctrl+K registered")
    except Exception as e:
        log.warning("Could not bind hotkey: %s", e)

    try:
        search_window.show_window()
        search_window.root.mainloop()
    except KeyboardInterrupt:
        log.info("Shutting down")
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()


