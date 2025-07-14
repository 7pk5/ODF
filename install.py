#!/usr/bin/env python3
"""
Robust installation script for ODF (Offline Document Finder)
This script tries multiple installation strategies to ensure compatibility.
"""

import subprocess
import sys
import platform
import importlib.util

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_package(package_name):
    """Check if a package is already installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def main():
    """Main installation function with fallback strategies."""
    print("ODF Installation Script")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        print("Warning: Could not upgrade pip, continuing anyway...")
    
    # Strategy 1: Try main requirements
    print("\nStrategy 1: Installing main requirements...")
    if run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing main requirements"):
        print("✓ Main installation successful!")
        return
    
    # Strategy 2: Try minimal requirements
    print("\nStrategy 2: Trying minimal requirements...")
    if run_command(f"{sys.executable} -m pip install -r requirements-minimal.txt", "Installing minimal requirements"):
        print("✓ Minimal installation successful!")
        return
    
    # Strategy 3: Install packages one by one with fallbacks
    print("\nStrategy 3: Installing packages individually...")
    
    packages = [
        ("numpy>=1.19.0,<2.0.0", "numpy", "Core numerical computing"),
        ("torch>=1.10.0 --index-url https://download.pytorch.org/whl/cpu", "torch", "PyTorch CPU version"),
        ("sentence-transformers>=2.0.0", "sentence_transformers", "Sentence transformers"),
        ("faiss-cpu>=1.6.0", "faiss", "Vector search engine"),
        ("transformers>=4.15.0,<5.0.0", "transformers", "HuggingFace transformers"),
        ("scikit-learn>=1.0.0", "sklearn", "Machine learning library"),
        ("scipy>=1.7.0", "scipy", "Scientific computing"),
        ("pdfminer.six>=20200104", "pdfminer", "PDF processing"),
        ("python-docx>=0.8.10", "docx", "Word document processing"),
        ("rank-bm25>=0.2.1", "rank_bm25", "BM25 ranking"),
        ("nltk>=3.6.0", "nltk", "Natural language toolkit"),
        ("tqdm>=4.50.0", "tqdm", "Progress bars"),
        ("requests>=2.20.0", "requests", "HTTP library"),
    ]
    
    failed_packages = []
    
    for package_spec, import_name, description in packages:
        if check_package(import_name):
            print(f"✓ {description} already installed")
            continue
            
        if not run_command(f"{sys.executable} -m pip install {package_spec}", f"Installing {description}"):
            failed_packages.append((package_spec, description))
    
    # Strategy 4: Try alternative versions for failed packages
    if failed_packages:
        print("\nStrategy 4: Trying alternative versions for failed packages...")
        
        alternatives = {
            "torch": "torch>=1.8.0 --index-url https://download.pytorch.org/whl/cpu",
            "sentence-transformers": "sentence-transformers>=1.2.0",
            "transformers": "transformers>=4.10.0",
            "scipy": "scipy>=1.5.0",
            "scikit-learn": "scikit-learn>=0.24.0",
        }
        
        for package_spec, description in failed_packages:
            package_name = package_spec.split(">=")[0].split("==")[0]
            if package_name in alternatives:
                alt_spec = alternatives[package_name]
                run_command(f"{sys.executable} -m pip install {alt_spec}", f"Installing {description} (alternative)")
    
    # Final verification
    print("\nVerifying installation...")
    verification_imports = [
        ("numpy", "import numpy"),
        ("torch", "import torch"),
        ("sentence_transformers", "import sentence_transformers"),
        ("transformers", "import transformers"),
        ("requests", "import requests"),
    ]
    
    success_count = 0
    for name, import_cmd in verification_imports:
        try:
            exec(import_cmd)
            print(f"✓ {name} import successful")
            success_count += 1
        except ImportError:
            print(f"✗ {name} import failed")
    
    if success_count >= 4:
        print(f"\n🎉 Installation completed! {success_count}/{len(verification_imports)} core packages working.")
        print("You can now run the ODF application.")
    else:
        print(f"\n⚠️  Partial installation: {success_count}/{len(verification_imports)} packages working.")
        print("Some features may not work. Consider manual installation of missing packages.")

if __name__ == "__main__":
    main()
