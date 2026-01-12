"""
WebSocket Manager for Options Breakout Tracker V2

Manages Upstox WebSocket V3 connection with:
- Auto-reconnection with exponential backoff
- Subscription management for multiple instruments
- Message parsing and routing
- Connection health monitoring
"""
import asyncio
import threading
from datetime import datetime
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    import upstox_client
    UPSTOX_SDK_AVAILABLE = True
except ImportError:
    UPSTOX_SDK_AVAILABLE = False
    print("Warning: upstox-python-sdk not installed. Run: pip install upstox-python-sdk")


class ConnectionStatus(Enum):
    """WebSocket connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class TickData:
    """Parsed tick data from WebSocket"""
    instrument_key: str
    ltp: float
    timestamp: datetime
    volume: Optional[int] = None
    oi: Optional[int] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    close: Optional[float] = None


class WebSocketManager:
    """
    Manages Upstox WebSocket V3 connection.

    Usage:
        manager = WebSocketManager(access_token, on_tick, on_status)
        manager.connect()
        manager.subscribe(["NSE_FO|NIFTY25JAN26100CE"], "full")
        ...
        manager.disconnect()
    """

    def __init__(
        self,
        access_token: str,
        on_tick: Callable[[TickData], None],
        on_status: Callable[[ConnectionStatus, str], None],
        subscription_mode: str = "full",
        auto_reconnect: bool = True,
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 10
    ):
        """
        Initialize WebSocket manager.

        Args:
            access_token: Upstox API access token
            on_tick: Callback for market data ticks
            on_status: Callback for connection status changes
            subscription_mode: "ltpc", "full", or "option_greeks"
            auto_reconnect: Enable auto-reconnection
            reconnect_interval: Seconds between reconnect attempts
            max_reconnect_attempts: Maximum reconnect attempts
        """
        if not UPSTOX_SDK_AVAILABLE:
            raise ImportError("upstox-python-sdk is required. Install with: pip install upstox-python-sdk")

        self.access_token = access_token
        self.on_tick = on_tick
        self.on_status = on_status
        self.subscription_mode = subscription_mode
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts

        # Internal state
        self._streamer: Optional[Any] = None
        self._subscribed_instruments: List[str] = []
        self._status = ConnectionStatus.DISCONNECTED
        self._reconnect_count = 0
        self._is_running = False
        self._lock = threading.Lock()

    @property
    def status(self) -> ConnectionStatus:
        """Current connection status"""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._status == ConnectionStatus.CONNECTED

    def connect(self, instruments: Optional[List[str]] = None) -> None:
        """
        Establish WebSocket connection.

        Args:
            instruments: Optional list of instruments to subscribe immediately
        """
        if self._status == ConnectionStatus.CONNECTED:
            print("Already connected")
            return

        self._update_status(ConnectionStatus.CONNECTING, "Initiating connection...")

        try:
            # Configure Upstox client
            configuration = upstox_client.Configuration()
            configuration.access_token = self.access_token

            # Initial instruments (can be empty, will subscribe later)
            initial_instruments = instruments or []

            # Create MarketDataStreamerV3
            self._streamer = upstox_client.MarketDataStreamerV3(
                upstox_client.ApiClient(configuration),
                initial_instruments,
                self.subscription_mode
            )

            # Set up event handlers
            self._streamer.on("message", self._on_message)
            self._streamer.on("open", self._on_open)
            self._streamer.on("close", self._on_close)
            self._streamer.on("error", self._on_error)
            self._streamer.on("reconnecting", self._on_reconnecting)
            self._streamer.on("autoReconnectStopped", self._on_auto_reconnect_stopped)

            # Configure auto-reconnect
            if self.auto_reconnect:
                self._streamer.auto_reconnect(
                    True,
                    self.reconnect_interval,
                    self.max_reconnect_attempts
                )

            # Connect (this starts the WebSocket in a separate thread)
            self._is_running = True
            self._streamer.connect()

            if instruments:
                self._subscribed_instruments = instruments.copy()

        except Exception as e:
            self._update_status(ConnectionStatus.ERROR, f"Connection failed: {e}")
            raise

    def subscribe(self, instruments: List[str], mode: Optional[str] = None) -> None:
        """
        Subscribe to instruments.

        Args:
            instruments: List of instrument keys
            mode: Optional mode override (ltpc, full, option_greeks)
        """
        if not self._streamer:
            print("Warning: Not connected. Call connect() first.")
            return

        if not instruments:
            return

        with self._lock:
            # Add to tracked instruments
            for inst in instruments:
                if inst not in self._subscribed_instruments:
                    self._subscribed_instruments.append(inst)

        # Subscribe via streamer
        try:
            use_mode = mode or self.subscription_mode
            self._streamer.subscribe(instruments, use_mode)
            print(f"Subscribed to {len(instruments)} instruments (mode: {use_mode})")
        except Exception as e:
            print(f"Subscription error: {e}")

    def unsubscribe(self, instruments: List[str]) -> None:
        """
        Unsubscribe from instruments.

        Args:
            instruments: List of instrument keys to unsubscribe
        """
        if not self._streamer:
            return

        with self._lock:
            for inst in instruments:
                if inst in self._subscribed_instruments:
                    self._subscribed_instruments.remove(inst)

        try:
            self._streamer.unsubscribe(instruments)
            print(f"Unsubscribed from {len(instruments)} instruments")
        except Exception as e:
            print(f"Unsubscribe error: {e}")

    def change_mode(self, instruments: List[str], mode: str) -> None:
        """
        Change subscription mode for instruments.

        Args:
            instruments: List of instrument keys
            mode: New mode (ltpc, full, option_greeks)
        """
        if not self._streamer:
            return

        try:
            self._streamer.change_mode(instruments, mode)
            print(f"Changed mode to {mode} for {len(instruments)} instruments")
        except Exception as e:
            print(f"Change mode error: {e}")

    def disconnect(self) -> None:
        """Gracefully close connection."""
        self._is_running = False

        if self._streamer:
            try:
                self._streamer.disconnect()
            except Exception as e:
                print(f"Disconnect error: {e}")
            finally:
                self._streamer = None

        self._update_status(ConnectionStatus.CLOSED, "Disconnected")

    def _update_status(self, status: ConnectionStatus, message: str) -> None:
        """Update status and notify callback."""
        self._status = status
        try:
            self.on_status(status, message)
        except Exception as e:
            print(f"Status callback error: {e}")

    def _on_message(self, message: Any) -> None:
        """
        Handle incoming WebSocket message.

        Parses the message and calls the tick callback.
        """
        try:
            # The message format from MarketDataStreamerV3
            # Can be dict or protobuf depending on SDK version
            if isinstance(message, dict):
                self._parse_dict_message(message)
            else:
                # Try to access as object
                self._parse_object_message(message)
        except Exception as e:
            print(f"Message parse error: {e}")

    def _parse_dict_message(self, message: dict) -> None:
        """Parse dictionary format message."""
        feeds = message.get('feeds', {})

        for instrument_key, data in feeds.items():
            try:
                # Extract LTP from various possible locations
                ltp = None
                ff = data.get('ff', {})
                ltpc = ff.get('ltpc', {}) or data.get('ltpc', {})

                if ltpc:
                    ltp = ltpc.get('ltp')

                if ltp is None:
                    # Try market_ff
                    market_ff = ff.get('marketFF', {})
                    ltpc = market_ff.get('ltpc', {})
                    if ltpc:
                        ltp = ltpc.get('ltp')

                if ltp is not None:
                    tick = TickData(
                        instrument_key=instrument_key,
                        ltp=float(ltp),
                        timestamp=datetime.now(),
                        volume=self._safe_int(ltpc.get('v')),
                        close=self._safe_float(ltpc.get('cp'))
                    )
                    self.on_tick(tick)

            except Exception as e:
                print(f"Error parsing tick for {instrument_key}: {e}")

    def _parse_object_message(self, message: Any) -> None:
        """Parse object format message (protobuf decoded)."""
        try:
            # Access feeds attribute
            feeds = getattr(message, 'feeds', None)
            if feeds is None:
                return

            for instrument_key, data in feeds.items():
                try:
                    ltp = None

                    # Try different data paths
                    if hasattr(data, 'ff'):
                        ff = data.ff
                        if hasattr(ff, 'ltpc'):
                            ltp = ff.ltpc.ltp if hasattr(ff.ltpc, 'ltp') else None
                        elif hasattr(ff, 'marketFF') and hasattr(ff.marketFF, 'ltpc'):
                            ltp = ff.marketFF.ltpc.ltp

                    if ltp is not None:
                        tick = TickData(
                            instrument_key=instrument_key,
                            ltp=float(ltp),
                            timestamp=datetime.now()
                        )
                        self.on_tick(tick)

                except Exception as e:
                    print(f"Error parsing object tick for {instrument_key}: {e}")

        except Exception as e:
            print(f"Error parsing object message: {e}")

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _on_open(self) -> None:
        """Handle WebSocket connection opened."""
        self._reconnect_count = 0
        self._update_status(ConnectionStatus.CONNECTED, "Connected to Upstox WebSocket")
        print(f"WebSocket connected. Subscribed to {len(self._subscribed_instruments)} instruments.")

    def _on_close(self) -> None:
        """Handle WebSocket connection closed."""
        if self._is_running:
            self._update_status(ConnectionStatus.DISCONNECTED, "Connection closed unexpectedly")
        else:
            self._update_status(ConnectionStatus.CLOSED, "Connection closed")

    def _on_error(self, error: Any) -> None:
        """Handle WebSocket error."""
        error_msg = str(error) if error else "Unknown error"
        print(f"WebSocket error: {error_msg}")

        if "token" in error_msg.lower() or "auth" in error_msg.lower():
            self._update_status(ConnectionStatus.ERROR, f"Authentication error: {error_msg}")
        else:
            self._update_status(ConnectionStatus.ERROR, f"Error: {error_msg}")

    def _on_reconnecting(self) -> None:
        """Handle reconnection attempt."""
        self._reconnect_count += 1
        self._update_status(
            ConnectionStatus.RECONNECTING,
            f"Reconnecting... attempt {self._reconnect_count}/{self.max_reconnect_attempts}"
        )
        print(f"Reconnecting... attempt {self._reconnect_count}")

    def _on_auto_reconnect_stopped(self) -> None:
        """Handle exhausted reconnection attempts."""
        self._update_status(
            ConnectionStatus.ERROR,
            "Auto-reconnect stopped - max attempts exceeded"
        )
        print("CRITICAL: Auto-reconnect stopped - max attempts exceeded")

    def get_subscribed_instruments(self) -> List[str]:
        """Get list of currently subscribed instruments."""
        with self._lock:
            return self._subscribed_instruments.copy()
