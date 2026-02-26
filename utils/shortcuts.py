"""
Global Shortcut Registration
Handles global keyboard shortcuts for the application.
Uses pynput for cross-platform support (works on Linux without root).
"""

from pynput import keyboard as pynput_kb
import threading
import time


class ShortcutManager:
    def __init__(self):
        """Initialize the shortcut manager."""
        self.shortcuts = {}
        self.listeners = {}
        self.is_running = False

    def register_shortcut(self, hotkey, callback):
        """
        Register a global shortcut.

        Args:
            hotkey (str): Hotkey combination in pynput format (e.g., '<ctrl>+<alt>+f')
            callback (function): Function to call when shortcut is pressed
        """
        try:
            # Remove existing shortcut if it exists
            if hotkey in self.listeners:
                self.listeners[hotkey].stop()

            # Register new shortcut using pynput GlobalHotKeys
            listener = pynput_kb.GlobalHotKeys({hotkey: callback})
            listener.start()
            self.listeners[hotkey] = listener
            self.shortcuts[hotkey] = callback
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
            if hotkey in self.listeners:
                self.listeners[hotkey].stop()
                del self.listeners[hotkey]
                del self.shortcuts[hotkey]
                print(f"Unregistered shortcut: {hotkey}")
                return True
            return False
        except Exception as e:
            print(f"Error unregistering shortcut {hotkey}: {e}")
            return False

    def stop_listener(self):
        """Stop all keyboard listeners."""
        self.is_running = False
        for hotkey in list(self.listeners.keys()):
            self.unregister_shortcut(hotkey)

    def list_shortcuts(self):
        """Get list of registered shortcuts."""
        return list(self.shortcuts.keys())


# Global shortcut manager instance
_shortcut_manager = ShortcutManager()


def register_global_shortcut(callback, hotkey='<ctrl>+<alt>+f'):
    """
    Register the default global shortcut for the application.

    Args:
        callback (function): Function to call when shortcut is pressed
        hotkey (str): Hotkey combination in pynput format (default: '<ctrl>+<alt>+f')
    """
    def safe_callback():
        """Wrapper to handle exceptions in callback."""
        try:
            callback()
        except Exception as e:
            print(f"Error in shortcut callback: {e}")

    success = _shortcut_manager.register_shortcut(hotkey, safe_callback)
    if success:
        print(f"Global shortcut {hotkey} registered successfully")
        print("Press the shortcut to open the search window")
    else:
        print(f"Failed to register global shortcut {hotkey}")
        print("You may need to check your display server permissions")

    return success


def unregister_global_shortcut(hotkey='<ctrl>+<alt>+f'):
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


# Alternative function with error handling for systems where pynput might not work
def register_global_shortcut_safe(callback, hotkey='<ctrl>+<alt>+f'):
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
