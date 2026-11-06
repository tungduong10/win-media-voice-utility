import asyncio
from typing import Optional
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSession as MediaSession,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from src.controller.fallback_win32 import (
    send_media_key,
    is_system_audio_playing,
    VK_MEDIA_PLAY_PAUSE,
    VK_MEDIA_NEXT_TRACK,
    VK_MEDIA_PREV_TRACK,
)


class MediaController:
    def __init__(self):
        self._manager: Optional[MediaManager] = None

    async def _get_manager(self) -> Optional[MediaManager]:
        """Cache and return the WinRT SessionManager instance."""
        if self._manager is None:
            try:
                self._manager = await MediaManager.request_async()
            except Exception as e:
                print(f"[WinRT] Error requesting SessionManager: {e}")
        return self._manager

    async def _get_current_session(self) -> Optional[MediaSession]:
        """Get the current active media session."""
        manager = await self._get_manager()
        if manager is None:
            return None        
        try:
            return manager.get_current_session()
        except Exception as e:
            print(f"[WinRT] Error getting current session: {e}")
            return None

    async def pause(self) -> bool:
        """Pause active media. Never unpauses if already paused."""
        session = await self._get_current_session()
        
        if session:
            try:
                status = session.get_playback_info().playback_status                
                if status == PlaybackStatus.PAUSED:
                    return True                
                if status == PlaybackStatus.PLAYING:
                    return await session.try_pause_async()                
            except Exception as e:
                print(f"[WinRT] Pause failed: {e}")
        
        # Fallback: only toggle is the audio is currently playing
        if is_system_audio_playing():
            send_media_key(VK_MEDIA_PLAY_PAUSE)
            return True
        
        return False

    async def resume(self) -> bool:
        """Resume paused media. Never pauses if already playing."""
        session = await self._get_current_session()
        
        if session:
            try:
                status = session.get_playback_info().playback_status                
                if status == PlaybackStatus.PLAYING:
                    return True
                if status == PlaybackStatus.PAUSED:
                    return await session.try_play_async()            
            except Exception as e:
                print(f"[WinRT] Resume failed: {e}")
                
        # Fallback: audio meter cannot distinguish paused from stopped.
        # This is therefore a best-effort fallback.
        if not is_system_audio_playing():
            send_media_key(VK_MEDIA_PLAY_PAUSE)
            return True
        
        return False

    async def next_track(self) -> bool:
        """Skip to next track."""
        session = await self._get_current_session()
                
        if session:
            try:
                if await session.try_skip_next_async():
                    return True                    
            except Exception as e:
                        print(f"[WinRT] Next failed: {e}")

        send_media_key(VK_MEDIA_NEXT_TRACK)
        return True
        
    async def previous_track(self) -> bool:
        """Skip to previous track."""
        session = await self._get_current_session()
                        
        if session:
            try:
                if await session.try_skip_previous_async():
                    return True                    
            except Exception as e:
                        print(f"[WinRT] Previous failed: {e}")

        send_media_key(VK_MEDIA_PREV_TRACK)
        return True


if __name__ == "__main__":
    async def test():
        ctrl = MediaController()
        print("--- Testing State Guard ---")
        
        # Start with music PLAYING
        print("First pause (should pause):", await ctrl.pause())
        await asyncio.sleep(2)

        # Call pause AGAIN while already paused
        print("Second pause (should stay paused):", await ctrl.pause())
        await asyncio.sleep(2)

        print("Resume (should play):", await ctrl.resume())

    asyncio.run(test())