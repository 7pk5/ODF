"""
Offline Document Finder (ODF)
A smart AI-powered desktop tool for semantic search of local documents.

Main entry point for the application.
"""

import os
import sys
import threading
from ui.search_window import SearchWindow



from pynput import keyboard as pynput_keyboard

def main():
    """Main entry point for the ODF application."""
    print("Starting Offline Document Finder (ODF)...")
    
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
    
    # Initialize the search window
    search_window = SearchWindow()
    
    # Bind Global Hotkey
    try:
        def on_activate():
            if search_window.root:
                search_window.root.after(0, search_window.toggle_window)
            else:
                search_window.toggle_window()

        listener = pynput_keyboard.GlobalHotKeys({'<ctrl>+k': on_activate})
        listener.start()
        print("✅ Global Hotkey Active: Press 'Ctrl + K' to toggle search")
    except Exception as e:
        print(f"⚠️ Could not bind hotkey: {e}")

    print("\n" + "="*60)
    print("🔍 Offline Document Finder (ODF) is ready!")
    print("="*60)
    print("📂 How to use:")
    print("   1. Press 'Ctrl + K' to toggle the search window")
    print("   2. Add documents using the 'Index Folder' button")
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
        try:
            listener.stop()
        except: pass
        sys.exit(0)

if __name__ == "__main__":
    main()

