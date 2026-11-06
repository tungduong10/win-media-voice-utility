import asyncio
import queue
import threading
from typing import Optional
from src.controller.media_controller import MediaController


class CommandRouter:
    # Natural language / spoken aliases mapped to canonical commands
    COMMAND_ALIASES = {
        # PAUSE
        "pause": "PAUSE",
        "stop": "PAUSE",
        "hold": "PAUSE",
        "freeze": "PAUSE",
        # RESUME
        "resume": "RESUME",
        "play": "RESUME",
        "continue": "RESUME",
        "unpause": "RESUME",
        # NEXT
        "next": "NEXT",
        "skip": "NEXT",
        "forward": "NEXT",
        # BACK
        "back": "BACK",
        "previous": "BACK",
        "prev": "BACK",
        "rewind": "BACK",
    }

    def __init__(self, media_controller: Optional[MediaController] = None):
        self.controller = media_controller or MediaController()
        self.queue: queue.Queue[str] = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def post(self, raw_command: str) -> None:
        """Push a raw command string from any thread into the queue."""
        self.queue.put(raw_command.strip().lower())

    def _worker(self) -> None:
        """Background thread target: initializes its own asyncio loop and processes queue items."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._process_queue_async())
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            self._loop = None
            asyncio.set_event_loop(None)

    async def _process_queue_async(self) -> None:
        """Async consumer loop pulling commands from the thread-safe queue."""
        while self._running:
            try:
                item = self.queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue
            
            try:
                if item == "__EXIT__":
                    break
                
                normalized = item.strip().casefold()
                action = self.COMMAND_ALIASES.get(normalized)
                
                if action is not None:
                    await self._dispatch(action)
                else:
                    print(f"[Command Router] Unknown command: {item!r}")
            except Exception as e:
                print(f"[Command Router] Error processing: {item!r}")
            finally:
                self.queue.task_done()

    async def _dispatch(self, canonical_action: str) -> None:
        """Execute the matching MediaController coroutine."""
        match canonical_action:
            case "PAUSE":
                await self.controller.pause()
            case "RESUME":
                await self.controller.resume()
            case "NEXT":
                await self.controller.next_track()               
            case "BACK":
                await self.controller.previous_track()
            case _:
                print(f"[Command Router] Unsupported action: {canonical_action!r}")

    def start(self) -> None:
        """Start the background consumer thread."""
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the consumer thread to exit."""
        self._running = False
        self.post("__EXIT__")
        if self._thread:
            self._thread.join(timeout=2.0)
    
if __name__ == "__main__":
    import time
    router = CommandRouter()
    router.start()
    print("Command Router running!")
    print("Type a command (pause, play, skip, back, unpause) or 'quit' to exit:")

    try:
        while True:
            cmd = input("> ")
            if cmd.strip().lower() in ("quit", "exit", "q"):
                break
            router.post(cmd)
            time.sleep(0.2)
    finally:
        router.stop()
        print("Router stopped.")