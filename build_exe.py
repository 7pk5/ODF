"""
ODF Build Script
Produces a single ODF.exe that anyone can double-click and run.
No Python installation required on the target machine.

Usage:
    python build_exe.py
"""

import os
import subprocess
import sys
import shutil


def build_exe():
    print("=" * 60)
    print("  ODF - Build Script")
    print("  Output: dist/ODF.exe  (single file, share and run)")
    print("=" * 60)

    # ── 0. Clean previous builds ─────────────────────────────────
    for path in ["dist", "build", "ODF.spec"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Cleaned: {path}")

    # ── 1. Ensure PyInstaller is installed ───────────────────────
    try:
        import PyInstaller
        print(f"PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # ── 2. Ensure FastEmbed is installed ─────────────────────────
    try:
        import fastembed
        print("FastEmbed found.")
    except ImportError:
        print("Installing FastEmbed...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastembed"])

    # ── 3. (Model is downloaded on first launch by the end user) ──
    #       The AI model is NOT bundled in the EXE — this keeps the
    #       distribution small (~70 MB vs ~200 MB). On first launch,
    #       FastEmbed downloads the model (~130 MB) once to
    #       %APPDATA%\ODF\models\ and reuses it on every subsequent run.

    # ── 4. Resolve icon path (optional) ──────────────────────────
    icon_args = []
    icon_candidates = [
        os.path.join(os.path.dirname(__file__), "ODF_Logo.ico"),
        os.path.join(os.path.dirname(__file__), "icon.ico"),
    ]
    for ico in icon_candidates:
        if os.path.exists(ico):
            icon_args = ["--icon", ico]
            print(f"Using icon: {ico}")
            break
    if not icon_args:
        print("No icon file found — building without icon. (Add ODF_Logo.ico to project root to include one.)")

    # ── 5. PyInstaller command ────────────────────────────────────
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",            # Folder distribution — no extraction on every launch
        "--windowed",          # No console window
        "--name", "ODF",
        "--clean",

        # Collect all files for packages that use dynamic loading
        "--collect-all", "chromadb",
        "--collect-all", "fastembed",
        "--collect-all", "onnxruntime",
        "--collect-all", "tokenizers",
        "--collect-all", "huggingface_hub",
        "--collect-all", "customtkinter",
        "--collect-all", "pdfminer",

        # Hidden imports that PyInstaller may miss
        "--hidden-import", "fastembed",
        "--hidden-import", "fastembed.common",
        "--hidden-import", "fastembed.text",
        "--hidden-import", "fastembed.text.text_embedding",
        "--hidden-import", "pdfminer.high_level",
        "--hidden-import", "pdfminer.layout",
        "--hidden-import", "docx",
        "--hidden-import", "keyboard",
        "--hidden-import", "chromadb.migrations",
        "--hidden-import", "sqlite3",

        # Exclude heavy packages that are not used
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "wx",
        "--exclude-module", "IPython",
        "--exclude-module", "notebook",
        "--exclude-module", "pytest",
        "--exclude-module", "unittest",

        # Entry point
        "main.py",
    ] + icon_args

    print("\nRunning PyInstaller...\n")
    print(" ".join(cmd))
    print()
    subprocess.check_call(cmd)

    # ── 6. Done ───────────────────────────────────────────────────
    exe_path = os.path.join("dist", "ODF", "ODF.exe")
    folder_path = os.path.join("dist", "ODF")
    if os.path.exists(exe_path):
        folder_mb = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, filenames in os.walk(folder_path)
            for f in filenames
        ) / (1024 * 1024)
        print(f"\n{'=' * 60}")
        print(f"  BUILD SUCCESSFUL")
        print(f"  Folder : dist/ODF/")
        print(f"  EXE    : dist/ODF/ODF.exe")
        print(f"  Size   : {folder_mb:.1f} MB (total folder)")
        print(f"{'=' * 60}")
        print("\nHow to share:")
        print("  1. Zip the entire 'dist/ODF/' folder")
        print("  2. Send the zip — recipients unzip and double-click ODF.exe")
        print("  3. First launch downloads the AI model once (~130 MB).")
        print("     Every launch after that is instant, no internet needed.")
    else:
        print("\nBuild may have failed — check output above.")


if __name__ == "__main__":
    build_exe()
