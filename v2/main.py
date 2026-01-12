#!/usr/bin/env python3
"""
Options Breakout Tracker V2
Real-time WebSocket-based tracking for options breakout strategy

Usage:
    python main.py [--config CONFIG_PATH]
"""
import sys
import time
import signal
import argparse
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from v2.config.settings import Settings
from v2.core.instrument_builder import InstrumentBuilder
from v2.core.websocket_manager import WebSocketManager, TickData, ConnectionStatus
from v2.core.breakout_tracker import BreakoutTracker, TrackerPhase, Position
from v2.alerts.notifier import Notifier, create_notifier_from_config
from v2.persistence.state_manager import StateManager
from v2.dashboard.server import DashboardServerSync


class BreakoutApp:
    """Main application orchestrator"""

    def __init__(self, config_path: str = None):
        """
        Initialize the breakout tracker application.

        Args:
            config_path: Optional path to config file
        """
        print("\n" + "=" * 70)
        print("OPTIONS BREAKOUT TRACKER V2")
        print("Real-time WebSocket Edition")
        print("=" * 70 + "\n")

        # Load configuration
        print("Loading configuration...")
        self.settings = Settings.load(config_path) if config_path else Settings.load_default()
        print(f"  Entry Time: {self.settings.timing.entry_time}")
        print(f"  Lookback: {self.settings.timing.lookback_start} - {self.settings.timing.lookback_end}")

        # Load credentials
        print("\nLoading credentials...")
        self.access_token = self._load_credentials()
        print("  Access token loaded")

        # Initialize components
        print("\nInitializing components...")
        self.notifier = create_notifier_from_config(self.settings.alerts)
        self.state_manager = StateManager(
            self.settings.persistence.output_directory,
            self.settings.persistence.file_prefix
        )

        # Core components (initialized later)
        self.ws_manager = None
        self.tracker = None
        self.dashboard_server = None
        self.all_instruments = []
        self.symbol_metadata = {}

        # Control flags
        self._shutdown = False
        self._phase_check_interval = 1  # seconds

    def _load_credentials(self) -> str:
        """Load access token from credentials file"""
        creds_path = Path(__file__).parent.parent / 'upstox_credentials.txt'

        if not creds_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {creds_path}\n"
                "Please run upstox_token_generator.py first."
            )

        with open(creds_path, 'r') as f:
            for line in f:
                if line.startswith('ACCESS_TOKEN='):
                    return line.split('=', 1)[1].strip()

        raise ValueError("ACCESS_TOKEN not found in credentials file")

    def initialize(self) -> None:
        """Initialize all components"""
        # Check for session resume
        if self.state_manager.can_resume():
            resume_info = self.state_manager.get_resume_info()
            print(f"\nResumable session found:")
            print(f"  Phase: {resume_info['phase']}")
            print(f"  Ticks: {resume_info['tick_count']}")
            print(f"  Last save: {resume_info['last_save']}")

            response = input("\nResume previous session? (y/n): ").strip().lower()
            if response == 'y':
                print("\nSession resume not yet implemented. Starting fresh.")
                # TODO: Implement session resume

        # Archive old sessions
        archived = self.state_manager.archive_old_sessions()
        if archived > 0:
            print(f"\nArchived {archived} old session(s)")

        # Build instrument subscriptions
        print("\nBuilding instrument subscriptions...")
        instrument_builder = InstrumentBuilder(self.access_token)

        enabled_symbols = self.settings.get_enabled_symbols()
        self.all_instruments, self.symbol_metadata = instrument_builder.build_all_subscriptions(
            enabled_symbols
        )

        print(f"\nTotal instruments: {len(self.all_instruments)}")

        # Initialize tracker
        print("\nInitializing breakout tracker...")
        self.tracker = BreakoutTracker(
            lookback_start=self.settings.timing.lookback_start,
            lookback_end=self.settings.timing.lookback_end,
            entry_time=self.settings.timing.entry_time,
            market_close=self.settings.timing.market_close,
            on_signal=self._on_signal,
            on_sl_hit=self._on_sl_hit,
            on_phase_change=self._on_phase_change,
            on_new_low=self._on_new_low
        )

        # Add symbols to tracker
        for symbol, config in enabled_symbols.items():
            if symbol in self.symbol_metadata:
                self.tracker.add_symbol(
                    symbol=symbol,
                    target_premium=config.target_premium,
                    stop_loss_percent=config.stop_loss_percent,
                    metadata=self.symbol_metadata[symbol]
                )

        # Initialize WebSocket manager
        print("\nInitializing WebSocket manager...")
        self.ws_manager = WebSocketManager(
            access_token=self.access_token,
            on_tick=self._on_tick,
            on_status=self._on_ws_status,
            subscription_mode=self.settings.websocket.subscription_mode,
            auto_reconnect=self.settings.websocket.auto_reconnect,
            reconnect_interval=self.settings.websocket.reconnect_interval_seconds,
            max_reconnect_attempts=self.settings.websocket.max_reconnect_attempts
        )

        # Start dashboard server
        if self.settings.dashboard.enabled:
            print("\nStarting dashboard server...")
            self.dashboard_server = DashboardServerSync(
                host=self.settings.dashboard.host,
                port=self.settings.dashboard.port,
                update_throttle_ms=self.settings.dashboard.update_throttle_ms
            )
            self.dashboard_server.start()
            print(f"  Dashboard: {self.dashboard_server.url}")

    def start(self) -> None:
        """Start the tracker"""
        print("\n" + "=" * 70)
        print("STARTING TRACKER")
        print("=" * 70)

        # Connect WebSocket and subscribe
        print("\nConnecting to Upstox WebSocket...")
        self.ws_manager.connect(self.all_instruments)

        # Wait for connection
        time.sleep(2)

        if not self.ws_manager.is_connected:
            print("Warning: WebSocket not yet connected. Will retry automatically.")

        # Open dashboard in browser
        if self.settings.dashboard.enabled and self.dashboard_server:
            print(f"\nOpening dashboard: {self.dashboard_server.url}")
            webbrowser.open(self.dashboard_server.url)

        print("\n" + "=" * 70)
        print("TRACKER RUNNING")
        print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Entry time: {self.settings.timing.entry_time}")
        print("Press Ctrl+C to stop")
        print("=" * 70 + "\n")

    def run(self) -> None:
        """Main run loop"""
        self.initialize()
        self.start()

        save_interval = self.settings.persistence.save_interval_seconds
        last_save = time.time()

        try:
            while not self._shutdown:
                # Check phase transitions
                self.tracker.check_phase_transition()

                # Broadcast to dashboard
                if self.dashboard_server:
                    state = self.tracker.get_state()
                    self.dashboard_server.broadcast(state)

                # Periodic state save
                if time.time() - last_save >= save_interval:
                    self.state_manager.save_state(self.tracker.get_state())
                    last_save = time.time()

                # Check if completed
                if self.tracker.phase == TrackerPhase.COMPLETED:
                    print("\nTrading day completed.")
                    break

                time.sleep(self._phase_check_interval)

        except KeyboardInterrupt:
            print("\n\nInterrupt received...")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Graceful shutdown"""
        print("\n" + "=" * 70)
        print("SHUTTING DOWN")
        print("=" * 70)

        self._shutdown = True

        # Save final state
        if self.tracker:
            print("\nSaving final state...")
            state = self.tracker.get_state()
            state['shutdown_time'] = datetime.now().isoformat()
            state['shutdown_reason'] = 'user_requested'
            self.state_manager.save_state(state)
            print(f"  Saved to: {self.state_manager.get_state_file_path()}")

        # Disconnect WebSocket
        if self.ws_manager:
            print("\nDisconnecting WebSocket...")
            self.ws_manager.disconnect()

        # Stop dashboard server
        if self.dashboard_server:
            print("\nStopping dashboard server...")
            self.dashboard_server.stop()

        # Print summary
        if self.tracker:
            stats = self.tracker.get_stats()
            print(f"\nSession Summary:")
            print(f"  Total ticks: {stats['tick_count']}")
            print(f"  Positions: {stats['positions_count']}")
            print(f"  Final phase: {stats['phase']}")

        print("\nShutdown complete.")

    def _on_tick(self, tick: TickData) -> None:
        """Handle incoming tick data"""
        self.tracker.on_tick(
            instrument_key=tick.instrument_key,
            ltp=tick.ltp,
            timestamp=tick.timestamp
        )

    def _on_signal(self, position: Position) -> None:
        """Handle entry signal"""
        self.notifier.send_entry_signal(
            symbol=position.symbol,
            option_type=position.option_type,
            strike=position.strike,
            entry_price=position.entry_price,
            stop_loss=position.stop_loss
        )

    def _on_sl_hit(self, position: Position) -> None:
        """Handle stop loss hit"""
        self.notifier.send_stop_loss_hit(
            symbol=position.symbol,
            option_type=position.option_type,
            strike=position.strike,
            sl_price=position.current_ltp,
            entry_price=position.entry_price
        )

    def _on_phase_change(self, old_phase: TrackerPhase, new_phase: TrackerPhase) -> None:
        """Handle phase change"""
        self.notifier.send_phase_change(old_phase.value, new_phase.value)

    def _on_new_low(self, strike_data) -> None:
        """Handle new low detection (optional logging)"""
        # Can be used for verbose logging during lookback
        pass

    def _on_ws_status(self, status: ConnectionStatus, message: str) -> None:
        """Handle WebSocket status changes"""
        if status == ConnectionStatus.CONNECTED:
            self.notifier.send_connection_status(True, message)
        elif status == ConnectionStatus.DISCONNECTED:
            self.notifier.send_connection_status(False, message)
        elif status == ConnectionStatus.ERROR:
            self.notifier.send_warning("WebSocket Error", message)


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description='Options Breakout Tracker V2 - Real-time WebSocket Edition'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration YAML file'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (prints config and exits)'
    )

    args = parser.parse_args()

    if args.test:
        print("Test mode - Loading configuration...")
        settings = Settings.load(args.config) if args.config else Settings.load_default()
        print(f"\nConfiguration loaded successfully:")
        print(f"  Entry Time: {settings.timing.entry_time}")
        print(f"  Symbols: {list(settings.get_enabled_symbols().keys())}")
        print(f"  Dashboard Port: {settings.dashboard.port}")
        return

    # Setup signal handlers
    app = BreakoutApp(args.config)

    def signal_handler(signum, frame):
        print("\n\nSignal received, shutting down...")
        app._shutdown = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run
    app.run()


if __name__ == '__main__':
    main()
