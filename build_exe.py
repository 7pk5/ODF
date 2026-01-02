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

    # 1.5 Install FastEmbed if missing (Crucial!)
    try:
        import fastembed
        print("FastEmbed is found.")
    except ImportError:
        print("Installing FastEmbed (Required for build)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastembed"])

    # 1.6 Pre-download Models for Offline Use (CRITICAL)
    print("Pre-downloading AI Models to 'models' folder...")
    try:
        if not os.path.exists("models"):
            os.makedirs("models")
        
        # We use a temporary script to force download to our specific folder
        download_script = """
import os
from fastembed import TextEmbedding
print("Downloading BAAI/bge-small-en-v1.5 to local 'models' folder...")
os.environ["FASTEMBED_CACHE_PATH"] = os.path.abspath("models")
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir="models")
print("Download complete.")
"""
        with open("download_models.py", "w") as f:
            f.write(download_script)
            
        subprocess.check_call([sys.executable, "download_models.py"])
        os.remove("download_models.py")
        
    except Exception as e:
        print(f"Error downloading models: {e}")
        # Don't exit, maybe they exist? Using check_call above would have exited if failed.

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
        # Custom Data: Include the 'models' folder inside the EXE
        "--add-data", "models;models",
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
