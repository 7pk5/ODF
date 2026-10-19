"""Walk folders and collect supported document files."""

import logging
import os

from odf.extract import SUPPORTED_EXTENSIONS, extension_of

log = logging.getLogger(__name__)

# Windows system locations never worth indexing (matched by path prefix)
SYSTEM_FOLDERS = {
    "C:\\WINDOWS",
    "C:\\PROGRAM FILES",
    "C:\\PROGRAM FILES (X86)",
    "C:\\SYSTEM32",
    "C:\\PROGRAMDATA",
    "C:\\USERS\\DEFAULT",
    "C:\\BOOT",
    "C:\\RECOVERY",
}

# Dev-environment / build folders (matched by folder name, case-insensitive)
IGNORED_FOLDER_NAMES = {
    "node_modules",
    "site-packages",
    "dist-info",
    "__pycache__",
    "venv",
    "env",
    "odf_env",
    "libs",
    "include",
    "scripts",
    "bin",
    "obj",
}


def should_skip_folder(folder_path):
    """Check if a folder should be skipped (system, hidden, dev envs)."""
    if not folder_path:
        return False

    name = os.path.basename(folder_path)

    # 1. Skip hidden directories
    if name.startswith("."):
        return True

    # 2. Skip specific ignore patterns
    if name.lower() in IGNORED_FOLDER_NAMES:
        return True

    # 3. Skip system folders (check start of path)
    norm_path = os.path.normpath(folder_path.upper())
    return any(norm_path.startswith(system_folder) for system_folder in SYSTEM_FOLDERS)


def scan_directory(folder_path, extensions=SUPPORTED_EXTENSIONS):
    """
    Scans the folder and returns a list of supported files.
    Useful for getting a total count before processing.
    """
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder does not exist: {folder_path}")

    all_files = []
    for root, dirs, files in os.walk(folder_path, followlinks=True):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if not should_skip_folder(os.path.join(root, d))]

        for file in files:
            if extension_of(file) in extensions:
                all_files.append(os.path.join(root, file))

    log.info("Found %d supported files to scan.", len(all_files))
    return all_files
