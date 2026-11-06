import os
import sys
import ctypes
import traceback
from src.router.command_router import CommandRouter
from src.listeners.hotkey_listener import HotkeyListener
from src.listeners.voice_listener import VoiceListener
from src.ui.tray_app import TrayApp

def insure_single_instances(app_id="WinMediaVoiceUtility_Single_Instance_Mutex"):
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, app_id)
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        print("[App] Another instance is already running. Exiting.")
        sys.exit(0)
    return mutex

def setup_logging():
    log_file = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "app.log")
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "a", encoding="utf-8")
        def write(self, message):
            if self.terminal:
                self.terminal.write(message)
            self.log.write(message)
            self.log.flush()
        def flush(self):
            if self.terminal:
                self.terminal.flush()
            self.log.flush()
    sys.stdout = Logger(log_file)
    sys.stderr = sys.stdout

setup_logging()

def main():
    print("=" * 50)
    print(" Starting State-Aware Media Controller Utility")
    print(" Look for the blue icon in your Windows Taskbar Tray!")
    print("=" * 50)

    # 1. Start the Command Router (background thread with asyncio loop)
    router = CommandRouter()
    router.start()

    # 2. Register global hotkeys
    hotkeys = HotkeyListener(router)
    hotkeys.start()

    # 3. Register voice
    voice = VoiceListener(router, vosk_model_path="model")
    voice.start()
    
    # 4. Create the System Tray UI
    tray = TrayApp(router, voice_listener=voice)

    try:
        # icon.run() blocks the main thread with the Windows event pump
        tray.run()
    finally:
        # Clean shutdown when user clicks "Exit" in tray
        print("Cleaning up resources...")
        voice.stop()
        hotkeys.stop()
        router.stop()
        print("Shutdown complete.")
        sys.exit(0)


if __name__ == "__main__":
    main()