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

    # ── 3. Pre-download the AI model to the local 'models' folder ─
    #       This gets bundled inside the EXE so users need no internet.
    models_dir = os.path.abspath("models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    print("\nChecking / downloading AI model (BAAI/bge-small-en-v1.5)...")
    download_script = f"""
import os
from fastembed import TextEmbedding
models_dir = r"{models_dir}"
print(f"Saving model to: {{models_dir}}")
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=models_dir)
# Run one embed to confirm the model loaded
list(model.embed(["test"]))
print("Model ready.")
"""
    tmp_script = "_download_model_tmp.py"
    with open(tmp_script, "w") as f:
        f.write(download_script)
    try:
        subprocess.check_call([sys.executable, tmp_script])
    finally:
        if os.path.exists(tmp_script):
            os.remove(tmp_script)

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
        "--onefile",           # Single .exe — double-click and run
        "--windowed",          # No console window
        "--name", "ODF",
        "--clean",

        # Bundle the AI model inside the EXE (users need no internet)
        "--add-data", f"{models_dir}{os.pathsep}models",

        # Collect all files for packages that use dynamic loading
        "--collect-all", "chromadb",
        "--collect-all", "fastembed",
        "--collect-all", "onnxruntime",
        "--collect-all", "tokenizers",       # fastembed internal dependency
        "--collect-all", "huggingface_hub",  # fastembed internal dependency
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

        # Entry point
        "main.py",
    ] + icon_args

    print("\nRunning PyInstaller...\n")
    print(" ".join(cmd))
    print()
    subprocess.check_call(cmd)

    # ── 6. Done ───────────────────────────────────────────────────
    exe_path = os.path.join("dist", "ODF.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n{'=' * 60}")
        print(f"  BUILD SUCCESSFUL")
        print(f"  File : dist/ODF.exe")
        print(f"  Size : {size_mb:.1f} MB")
        print(f"{'=' * 60}")
        print("\nHow to share:")
        print("  1. Send 'dist/ODF.exe' to anyone")
        print("  2. They double-click it — no Python or setup needed")
        print("  NOTE: First launch takes ~20-30 sec (one-time extraction).")
        print("        Subsequent launches are faster.")
    else:
        print("\nBuild may have failed — check output above.")


if __name__ == "__main__":
    build_exe()
