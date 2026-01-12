"""
Dashboard WebSocket Server for Options Breakout Tracker V2

Provides:
- Real-time state updates via WebSocket
- Static file serving for dashboard HTML
- Multiple client support with broadcast
"""
import asyncio
import json
from pathlib import Path
from typing import Set, Dict, Any, Optional
from datetime import datetime

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp not installed. Run: pip install aiohttp")


class DashboardServer:
    """
    WebSocket server for real-time dashboard updates.

    Features:
    - Push updates on state changes
    - Broadcast to all connected clients
    - Serve static HTML dashboard
    - Throttled updates to prevent flooding
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        update_throttle_ms: int = 100
    ):
        """
        Initialize dashboard server.

        Args:
            host: Server host
            port: Server port
            update_throttle_ms: Minimum time between updates
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")

        self.host = host
        self.port = port
        self.update_throttle_ms = update_throttle_ms

        self._clients: Set[web.WebSocketResponse] = set()
        self._last_state: Dict[str, Any] = {}
        self._last_broadcast: Optional[datetime] = None
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._is_running = False

    async def start(self) -> None:
        """Start the dashboard server."""
        self._app = web.Application()

        # Add routes
        self._app.router.add_get('/ws', self._handle_websocket)
        self._app.router.add_get('/', self._handle_index)
        self._app.router.add_static('/static/',
                                    Path(__file__).parent / 'static',
                                    name='static')

        # Start server
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()

        self._is_running = True
        print(f"Dashboard server started at http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the dashboard server."""
        self._is_running = False

        # Close all WebSocket connections
        for ws in list(self._clients):
            await ws.close()

        self._clients.clear()

        # Cleanup server
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()

        print("Dashboard server stopped")

    async def broadcast(self, state: Dict[str, Any]) -> None:
        """
        Broadcast state to all connected clients.

        Implements throttling to prevent flooding.

        Args:
            state: State dictionary to broadcast
        """
        # Throttle updates
        now = datetime.now()
        if self._last_broadcast:
            elapsed_ms = (now - self._last_broadcast).total_seconds() * 1000
            if elapsed_ms < self.update_throttle_ms:
                return

        self._last_broadcast = now
        self._last_state = state

        if not self._clients:
            return

        # Prepare message
        message = json.dumps(state, default=str)

        # Send to all clients
        disconnected = []
        for ws in self._clients:
            try:
                await ws.send_str(message)
            except Exception:
                disconnected.append(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self._clients.discard(ws)

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._clients.add(ws)
        print(f"Dashboard client connected. Total clients: {len(self._clients)}")

        # Send current state immediately
        if self._last_state:
            await ws.send_str(json.dumps(self._last_state, default=str))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    # Handle client messages (e.g., ping)
                    if msg.data == 'ping':
                        await ws.send_str('pong')
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
        finally:
            self._clients.discard(ws)
            print(f"Dashboard client disconnected. Total clients: {len(self._clients)}")

        return ws

    async def _handle_index(self, request: web.Request) -> web.FileResponse:
        """Serve the dashboard HTML."""
        index_path = Path(__file__).parent / 'static' / 'index.html'
        return web.FileResponse(index_path)

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._is_running

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)

    @property
    def url(self) -> str:
        """Get server URL."""
        return f"http://{self.host}:{self.port}"


# Simplified synchronous wrapper for use with threading
class DashboardServerSync:
    """
    Synchronous wrapper for DashboardServer.

    Runs the async server in a separate thread.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        update_throttle_ms: int = 100
    ):
        self.host = host
        self.port = port
        self.update_throttle_ms = update_throttle_ms

        self._server: Optional[DashboardServer] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[Any] = None

    def start(self) -> None:
        """Start the server in a background thread."""
        import threading

        def run_server():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self._server = DashboardServer(
                self.host,
                self.port,
                self.update_throttle_ms
            )

            self._loop.run_until_complete(self._server.start())
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()

        # Wait for server to start
        import time
        time.sleep(0.5)

    def stop(self) -> None:
        """Stop the server."""
        if self._loop and self._server:
            asyncio.run_coroutine_threadsafe(
                self._server.stop(),
                self._loop
            ).result(timeout=5)

            self._loop.call_soon_threadsafe(self._loop.stop)

    def broadcast(self, state: Dict[str, Any]) -> None:
        """Broadcast state to clients."""
        if self._loop and self._server:
            asyncio.run_coroutine_threadsafe(
                self._server.broadcast(state),
                self._loop
            )

    @property
    def url(self) -> str:
        """Get server URL."""
        return f"http://{self.host}:{self.port}"
