import keyboard
from src.router.command_router import CommandRouter


class HotkeyListener:
    def __init__(self, router: CommandRouter):
        self.router = router
        self._registered = False

    def start(self) -> None:
        """Register global hotkeys that push intents into the router."""
        if self._registered:
            return

        # Pick shortcuts that don't collide with default Windows hotkeys
        keyboard.add_hotkey("ctrl+alt+space", lambda: self.router.post("pause"))
        keyboard.add_hotkey("ctrl+alt+shift+space", lambda: self.router.post("resume"))
        keyboard.add_hotkey("ctrl+alt+right", lambda: self.router.post("next"))
        keyboard.add_hotkey("ctrl+alt+left", lambda: self.router.post("back"))

        self._registered = True
        print("[HotkeyListener] Hotkeys registered (Ctrl+Alt+Space, Ctrl+Alt+Shift+Space, etc.)")

    def stop(self) -> None:
        """Unhook all hotkeys."""
        if self._registered:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
            self._registered = False