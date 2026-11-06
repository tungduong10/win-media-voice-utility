# Windows Media Voice Utility

A lightweight, state-aware background utility for Windows that lets you control OS media playback (YouTube, YouTube Music, Spotify, Edge, etc.) using offline voice commands or global hotkeys.

Built specifically for hands-free media control while gaming.

## Features

- **State-Aware Playback:** Uses Windows Runtime (WinRT) GSMTC APIs to inspect playback status. Calling **Pause** when already paused will *never* accidentally unpause music.
- **Offline Voice Recognition:** Powered by [Vosk](https://alphacephei.com/vosk/) with a grammar-constrained acoustic model (<100ms latency, zero cloud dependencies).
- **Wake Word Standby:** Uses [openWakeWord](https://github.com/dscripka/openWakeWord) for a two-stage listening pipeline (*"Hey Jarvis"* -> command).
- **System Tray Integration:** Runs silently in the background with mute toggle and exit options via [pystray](https://pypi.org/project/pystray/).
- **Global Hotkeys:** Works system-wide even when full-screen games are focused.

## Voice Commands

Wake Word: **"Hey Jarvis"** *(audio chime indicates activation)*

- **Pause / Stop:** `pause`, `stop`
- **Resume / Play:** `play`, `resume`, `continue`, `unpause`
- **Next Track:** `next`, `skip`
- **Previous Track:** `back`, `previous`

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/win-media-voice-utility.git
cd win-media-voice-utility
```

### 2. Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Download speech & wake word models
1. Download [vosk-model-small-en-us-0.15.zip](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip).
2. Extract it into the project root and rename the folder to `model`.
3. Download openWakeWord base models:
   ```powershell
   python -c "import openwakeword.utils; openwakeword.utils.download_models()"
   ```

### 5. Run the application
```powershell
python src/main.py
```
*(Or use `pythonw src/main.py` to run without a command prompt window).*
*(Or use the .bat file)*
## Hotkeys

- `Ctrl + Alt + Space`: Pause
- `Ctrl + Alt + Shift + Space`: Resume
- `Ctrl + Alt + Right`: Next Track
- `Ctrl + Alt + Left`: Previous Track

## Project Architecture

```text
win_media_voice_utility/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── model/                      # Extracted Vosk acoustic model
└── src/
    ├── main.py                 # Single-instance entry point & tray lifecycle
    ├── controller/
    │   ├── media_controller.py # State-aware WinRT GSMTC playback manager
    │   └── fallback_win32.py   # pycaw audio-meter check + ctypes virtual keys
    ├── router/
    │   └── command_router.py   # Thread-safe queue on an isolated asyncio loop
    ├── listeners/
    │   ├── hotkey_listener.py  # Global keyboard shortcuts
    │   └── voice_listener.py   # Two-stage openWakeWord + Vosk listener
    └── ui/
        └── tray_app.py         # pystray system tray icon and mute controls
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
