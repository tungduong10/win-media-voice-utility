import ctypes
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002

def send_media_key(vk_code: int) -> None:
    """Press and release a Windows media virtual key using user32.dll."""
    #key down
    ctypes.windll.user32.keybd_event(
        vk_code,
        0,
        0,
        0
    )
    #key up
    ctypes.windll.user32.keybd_event(
            vk_code,
            0,
            KEYEVENTF_KEYUP,
            0
        )

def is_system_audio_playing(threshold: float = 0.001) -> bool:
    """Return True if any Windows audio session has a peak meter value above threshold."""
    for session in AudioUtilities.GetAllSessions():
        try:
            meter = session._ctl.QueryInterface(IAudioMeterInformation)
            peak = meter.GetPeakValue()
            
            if peak > threshold:
                return True
            
        except Exception:
            #some audio sessions may not expose a usable meter
            continue
        
    return False


if __name__ == "__main__":
    print("Audio currently playing?", is_system_audio_playing())