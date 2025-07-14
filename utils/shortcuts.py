"""
Global Shortcut Registration
Handles global keyboard shortcuts for the application.
"""

import keyboard
import threading
import time

class ShortcutManager:
    def __init__(self):
        """Initialize the shortcut manager."""
        self.shortcuts = {}
        self.is_running = False
        self.listener_thread = None
    
    def register_shortcut(self, hotkey, callback):
        """
        Register a global shortcut.
        
        Args:
            hotkey (str): Hotkey combination (e.g., 'ctrl+alt+f')
            callback (function): Function to call when shortcut is pressed
        """
        try:
            # Remove existing shortcut if it exists
            if hotkey in self.shortcuts:
                keyboard.remove_hotkey(self.shortcuts[hotkey])
            
            # Register new shortcut
            self.shortcuts[hotkey] = keyboard.add_hotkey(hotkey, callback)
            print(f"Registered global shortcut: {hotkey}")
            return True
        except Exception as e:
            print(f"Error registering shortcut {hotkey}: {e}")
            return False
    
    def unregister_shortcut(self, hotkey):
        """
        Unregister a global shortcut.
        
        Args:
            hotkey (str): Hotkey combination to unregister
        """
        try:
            if hotkey in self.shortcuts:
                keyboard.remove_hotkey(self.shortcuts[hotkey])
                del self.shortcuts[hotkey]
                print(f"Unregistered shortcut: {hotkey}")
                return True
            return False
        except Exception as e:
            print(f"Error unregistering shortcut {hotkey}: {e}")
            return False
    
    def start_listener(self):
        """Start the keyboard listener in a separate thread."""
        if self.is_running:
            return
        
        self.is_running = True
        
        def listener():
            try:
                # Keep the listener alive
                while self.is_running:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error in shortcut listener: {e}")
        
        self.listener_thread = threading.Thread(target=listener, daemon=True)
        self.listener_thread.start()
    
    def stop_listener(self):
        """Stop the keyboard listener."""
        self.is_running = False
        
        # Remove all shortcuts
        for hotkey in list(self.shortcuts.keys()):
            self.unregister_shortcut(hotkey)
    
    def list_shortcuts(self):
        """Get list of registered shortcuts."""
        return list(self.shortcuts.keys())

# Global shortcut manager instance
_shortcut_manager = ShortcutManager()

def register_global_shortcut(callback, hotkey='ctrl+alt+f'):
    """
    Register the default global shortcut for the application.
    
    Args:
        callback (function): Function to call when shortcut is pressed
        hotkey (str): Hotkey combination (default: 'ctrl+alt+f')
    """
    def safe_callback():
        """Wrapper to handle exceptions in callback."""
        try:
            callback()
        except Exception as e:
            print(f"Error in shortcut callback: {e}")
    
    success = _shortcut_manager.register_shortcut(hotkey, safe_callback)
    if success:
        _shortcut_manager.start_listener()
        print(f"Global shortcut {hotkey} registered successfully")
        print("Press the shortcut to open the search window")
    else:
        print(f"Failed to register global shortcut {hotkey}")
        print("You may need to run the application as administrator")
    
    return success

def unregister_global_shortcut(hotkey='ctrl+alt+f'):
    """
    Unregister the global shortcut.
    
    Args:
        hotkey (str): Hotkey combination to unregister
    """
    return _shortcut_manager.unregister_shortcut(hotkey)

def stop_all_shortcuts():
    """Stop all keyboard shortcuts and listener."""
    _shortcut_manager.stop_listener()

def list_active_shortcuts():
    """Get list of active shortcuts."""
    return _shortcut_manager.list_shortcuts()

# Alternative function with error handling for systems where keyboard might not work
def register_global_shortcut_safe(callback, hotkey='ctrl+alt+f'):
    """
    Safely register global shortcut with fallback.
    
    Args:
        callback (function): Function to call when shortcut is pressed
        hotkey (str): Hotkey combination
    """
    try:
        return register_global_shortcut(callback, hotkey)
    except Exception as e:
        print(f"Could not register global shortcut: {e}")
        print("Global shortcuts may not be available on this system")
        print("You can still use the application by running main.py directly")
        return False
