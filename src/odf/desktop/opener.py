"""
File Opener Utility
Opens files using the default system application.
"""

import os
import subprocess
import platform

def open_file(file_path):
    """
    Open a file using the default system application.
    
    Args:
        file_path (str): Path to the file to open
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
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
            print(f"Unsupported operating system: {system}")
            return False
        
        print(f"Opened file: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error opening file {file_path}: {e}")
        return False
