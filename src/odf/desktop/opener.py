"""
File Opener Utility
Opens files using the default system application.
"""

import logging
import os
import subprocess
import platform

log = logging.getLogger(__name__)

def open_file(file_path):
    """
    Open a file using the default system application.
    
    Args:
        file_path (str): Path to the file to open
    """
    if not os.path.exists(file_path):
        log.warning("File not found: %s", file_path)
        return False
    
    try:
        system = platform.system()
        
        if system == "Windows":
            # Use os.startfile on Windows
            os.startfile(file_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", file_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", file_path])
        else:
            log.warning("Unsupported operating system: %s", system)
            return False
        
        log.info("Opened file: %s", file_path)
        return True
        
    except Exception:
        log.exception("Error opening file %s", file_path)
        return False
