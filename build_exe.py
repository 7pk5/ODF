"""
ODF Build Script
Produces dist/ODF/ (folder with ODF.exe) that anyone can unzip and run.
No Python installation required on the target machine.

Usage:
    python build_exe.py
"""

import os
import shutil
import subprocess
import sys


def build_exe():
    print("=" * 60)
    print("  ODF - Build Script")
    print("  Output: dist/ODF/ODF.exe  (zip the folder to share)")
    print("=" * 60)

    # ── 0. Clean previous builds ─────────────────────────────────
    for path in ["dist", "build", "ODF.spec"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Cleaned: {path}")

    # ── 1. Install locked build + runtime dependencies ───────────
    #       Same lock file that CI uses, so local and release builds
    #       get identical package versions (verified by hash).
    root = os.path.dirname(os.path.abspath(__file__))
    lock = {"win32": "requirements-windows.lock", "linux": "requirements-linux.lock"}.get(sys.platform)
    if lock:
        install = ["--require-hashes", "-r", os.path.join(root, lock)]
    else:
        install = ["-r", os.path.join(root, "requirements-build.txt")]  # no lock for this OS
    print("Installing pinned dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *install])

    # ── 2. (Model is downloaded on first launch by the end user) ──
    #       The AI model is NOT bundled in the EXE — this keeps the
    #       distribution small (~70 MB vs ~200 MB). On first launch,
    #       FastEmbed downloads the model (~130 MB) once to
    #       %APPDATA%\ODF\models\ and reuses it on every subsequent run.

    # ── 3. PyInstaller command ────────────────────────────────────
    #       All build settings (collected packages, hidden imports,
    #       excludes, icon) live in packaging/odf.spec, shared with CI.
    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packaging", "odf.spec")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        spec_path,
    ]

    print("\nRunning PyInstaller...\n")
    print(" ".join(cmd))
    print()
    subprocess.check_call(cmd)

    # ── 4. Done ───────────────────────────────────────────────────
    exe_path = os.path.join("dist", "ODF", "ODF.exe")
    folder_path = os.path.join("dist", "ODF")
    if os.path.exists(exe_path):
        folder_mb = sum(
            os.path.getsize(os.path.join(dp, f)) for dp, _, filenames in os.walk(folder_path) for f in filenames
        ) / (1024 * 1024)
        print(f"\n{'=' * 60}")
        print("  BUILD SUCCESSFUL")
        print("  Folder : dist/ODF/")
        print("  EXE    : dist/ODF/ODF.exe")
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
