"""
File Opener Utility
Opens files using the default system application.
"""

import os
import sys
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

def open_folder(folder_path):
    """
    Open a folder in the default file manager.
    
    Args:
        folder_path (str): Path to the folder to open
    """
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return False
    
    try:
        system = platform.system()
        
        if system == "Windows":
            subprocess.run(["explorer", folder_path])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", folder_path])
        else:
            print(f"Unsupported operating system: {system}")
            return False
        
        print(f"Opened folder: {folder_path}")
        return True
        
    except Exception as e:
        print(f"Error opening folder {folder_path}: {e}")
        return False

def get_file_info(file_path):
    """
    Get basic information about a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        dict: File information including size, modified time, etc.
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_file': os.path.isfile(file_path),
            'is_directory': os.path.isdir(file_path),
            'extension': os.path.splitext(file_path)[1],
            'basename': os.path.basename(file_path)
        }
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return None
