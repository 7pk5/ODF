import os
import subprocess
import sys
import shutil

def build_exe():
    print("--- ODF Build Script ---")
    
    # 0. Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("Deleted 'dist' folder.")
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("Deleted 'build' folder.")
    if os.path.exists("ODF.spec"):
        os.remove("ODF.spec")
        print("Deleted 'ODF.spec'.")

    # 1. Install PyInstaller if missing
    try:
        import PyInstaller
        print("PyInstaller is found.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Add CustomTkinter and ChromaDB data
    # We need to find where packages are to tell PyInstaller where to look
    # But PyInstaller's --collect-all usually handles this.
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ODF",
        "--icon", r"D:\FInalYear-Krunal\ODF\Gemini_Generated_Image_eiywc8eiywc8eiyw.ico",
        "--clean",
        # ChromaDB needs these
        "--collect-all", "chromadb",
        "--collect-all", "langchain", # If used (not used here but good practice)
        "--collect-all", "sentence_transformers", # If used by fastembed internally?
        "--collect-all", "fastembed",
        "--collect-all", "onnxruntime",
        # Explicit hidden imports for FastEmbed
        "--hidden-import", "fastembed",
        "--hidden-import", "fastembed.common",
        "--hidden-import", "fastembed.text",
        "--hidden-import", "fastembed.text.text_embedding",
        # CustomTkinter needs json/images
        "--collect-all", "customtkinter",
        # PDFMiner
        "--hidden-import", "pdfminer.six",
        # Main Entry Point
        "main.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("\n✅ Build Complete!")
    print("Look in the 'dist' folder for ODF_Search.exe")

if __name__ == "__main__":
    build_exe()
