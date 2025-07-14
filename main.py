"""
Offline Document Finder (ODF)
A smart AI-powered desktop tool for semantic search of local documents.

Main entry point for the application.
"""

import os
import sys
import threading
from ui.search_window import SearchWindow

def main():
    """Main entry point for the ODF application."""
    print("Starting Offline Document Finder (ODF)...")
    
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
    
    # Initialize the search window
    search_window = SearchWindow()
    
    print("\n" + "="*60)
    print("🔍 Offline Document Finder (ODF) is ready!")
    print("="*60)
    print("📂 How to use:")
    print("   1. The search window will open automatically")
    print("   2. Add documents using the 'Add Documents' button")
    print("   3. Search your documents with AI-powered semantic search")
    print("\n💡 Tip: You can always restart by running: python main.py")
    print("="*60)
    
    # Keep the main thread alive and show search window
    try:
        # Show the search window initially
        search_window.show_window()
        search_window.root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Shutting down ODF...")
        sys.exit(0)

if __name__ == "__main__":
    main()
