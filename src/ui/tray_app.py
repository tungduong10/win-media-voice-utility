import pystray
from PIL import Image, ImageDraw
from src.router.command_router import CommandRouter
from typing import Optional
from src.listeners.voice_listener import VoiceListener

def create_tray_icon_image(color="dodgerblue") -> Image.Image:
    """Generate a clean 64x64 icon in memory."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Draw a smooth circle with a media play symbol inside
    draw.ellipse((4, 4, 60, 60), fill=color)
    draw.polygon([(24, 18), (24, 46), (46, 32)], fill="white")
    return image


class TrayApp:
    def __init__(self, router: CommandRouter, voice_listener: Optional[VoiceListener] = None):
        self.router = router
        self.voice_listener = voice_listener
        self.is_listening = True  # Ready for Phase 4 voice toggle!
        self.icon = None

    def _toggle_listening(self, icon, item):
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.voice_listener.enabled = self.is_listening
        status = "Enabled" if self.is_listening else "Muted"
        print(f"[Tray] Voice/Input: {status}")
        # When muted, change icon color to gray; when active, restore blue
        icon.icon = create_tray_icon_image("dodgerblue" if self.is_listening else "gray")

    def _on_exit(self, icon, item):
        print("[Tray] Stopping application...")
        icon.stop()

    def run(self) -> None:
        """Build the tray menu and start the icon loop."""
        menu = pystray.Menu(
            pystray.MenuItem("State-Aware Media Controller", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pause", lambda icon, item: self.router.post("pause")),
            pystray.MenuItem("Resume", lambda icon, item: self.router.post("resume")),
            pystray.MenuItem("Next Track", lambda icon, item: self.router.post("next")),
            pystray.MenuItem("Previous Track", lambda icon, item: self.router.post("back")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Voice Listening Active",
                self._toggle_listening,
                checked=lambda item: self.is_listening,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit),
        )

        self.icon = pystray.Icon(
            name="WinMediaVoiceUtility",
            icon=create_tray_icon_image("dodgerblue"),
            title="Media Controller (State-Aware)",
            menu=menu,
        )
        self.icon.run()