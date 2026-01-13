#!/usr/bin/env python3
"""
Options Breakout Tracker V2 - Multi-Strategy Edition
Real-time WebSocket-based tracking for options breakout strategies

Usage:
    python main.py [--config CONFIG_PATH]
"""
import sys
import time
import signal
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from v2.config.settings import Settings
from v2.core.instrument_builder import InstrumentBuilder
from v2.core.websocket_manager import WebSocketManager, TickData, ConnectionStatus
from v2.core.strategy_manager import StrategyManager
from v2.core.strategy import Strategy
from v2.alerts.notifier import create_notifier_from_config
from v2.persistence.state_manager import StateManager
from v2.persistence.tick_data_store import TickDataStore
from v2.persistence.strategy_store import StrategyStore
from v2.dashboard.server import DashboardServerSync


class BreakoutApp:
    """Main application orchestrator for multi-strategy tracking"""

    def __init__(self, config_path: str = None):
        """
        Initialize the breakout tracker application.

        Args:
            config_path: Optional path to config file
        """
        print("\n" + "=" * 70)
        print("OPTIONS BREAKOUT TRACKER V2")
        print("Multi-Strategy Edition")
        print("=" * 70 + "\n")

        # Load configuration
        print("Loading configuration...")
        self.settings = Settings.load(config_path) if config_path else Settings.load_default()
        print(f"  Market Close: {self.settings.timing.market_close}")

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

        # Tick data store for saving raw tick data
        self.tick_store = TickDataStore(
            output_dir=self.settings.persistence.output_directory,
            file_prefix="tick_data",
            buffer_size=50
        )

        # Strategy store for persistence
        self.strategy_store = StrategyStore(
            output_dir=self.settings.persistence.output_directory
        )

        # Core components (initialized later)
        self.ws_manager = None
        self.strategy_manager = None
        self.dashboard_server = None
        self.all_instruments = []
        self.symbol_metadata = {}
        self.index_instruments = {}  # index -> {instrument_key: {strike, option_type}}

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

        # Build index_instruments mapping for strategy manager
        for symbol, metadata in self.symbol_metadata.items():
            strike_map = metadata.get('strike_map', {})
            instruments = {}

            for opt_type in ['CE', 'PE']:
                for strike, inst_key in strike_map.get(opt_type, {}).items():
                    instruments[inst_key] = {
                        'strike': strike,
                        'option_type': opt_type
                    }

            self.index_instruments[symbol] = instruments
            print(f"  {symbol}: {len(instruments)} instruments")

        # Initialize strategy manager with tick data filepath
        print("\nInitializing strategy manager...")
        tick_filepath = str(self.tick_store.output_dir / f"tick_data_{datetime.now().strftime('%Y%m%d')}.json")
        self.strategy_manager = StrategyManager(
            market_close=self.settings.timing.market_close.strftime('%H:%M'),
            on_entry_signal=self._on_entry_signal,
            on_sl_hit=self._on_sl_hit,
            on_phase_change=self._on_phase_change,
            tick_data_filepath=tick_filepath
        )

        # Set index instruments for strategy manager
        for index, instruments in self.index_instruments.items():
            self.strategy_manager.set_index_instruments(index, instruments)

        # Load saved strategies
        saved_strategies = self.strategy_store.load()
        if saved_strategies:
            loaded = self.strategy_manager.load_strategies(saved_strategies)
            print(f"  Loaded {loaded} saved strategies")

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

            # Set strategy callbacks
            self.dashboard_server.set_strategy_callbacks(
                create_callback=self._on_create_strategy,
                update_callback=self._on_update_strategy,
                remove_callback=self._on_remove_strategy,
                preview_callback=self._on_get_preview
            )

            self.dashboard_server.start()
            print(f"  Dashboard: {self.dashboard_server.url}")

    def start(self) -> None:
        """Start the tracker"""
        print("\n" + "=" * 70)
        print("STARTING TRACKER")
        print("=" * 70)

        # Start tick data recording
        print("\nStarting tick data recording...")
        tick_file = self.tick_store.start()
        print(f"  Tick data file: {tick_file}")

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
        print("TRACKER RUNNING - MULTI-STRATEGY MODE")
        print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
        print("Create strategies via the dashboard")
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
                # Check phase transitions for all strategies
                self.strategy_manager.check_phase_transitions()

                # Broadcast to dashboard
                if self.dashboard_server:
                    state = self.strategy_manager.get_state()
                    # Add data range info
                    data_range = self.tick_store.get_data_range()
                    state['data_range'] = {
                        'start': data_range.get('start_time'),
                        'end': data_range.get('end_time')
                    }
                    self.dashboard_server.broadcast(state)

                # Periodic state save
                if time.time() - last_save >= save_interval:
                    # Save strategies
                    strategies_data = self.strategy_manager.save_strategies()
                    self.strategy_store.save(strategies_data)

                    # Save general state
                    self.state_manager.save_state(self.strategy_manager.get_state())
                    last_save = time.time()

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
        if self.strategy_manager:
            print("\nSaving strategies...")
            strategies_data = self.strategy_manager.save_strategies()
            self.strategy_store.save(strategies_data)
            print(f"  Saved {len(strategies_data)} strategies")

            state = self.strategy_manager.get_state()
            state['shutdown_time'] = datetime.now().isoformat()
            self.state_manager.save_state(state)

        # Stop tick data recording
        if self.tick_store:
            print("\nStopping tick data recording...")
            tick_summary = self.tick_store.stop()
            print(f"  Tick data saved: {tick_summary.get('filepath')}")
            print(f"  Total ticks recorded: {tick_summary.get('total_ticks')}")

        # Disconnect WebSocket
        if self.ws_manager:
            print("\nDisconnecting WebSocket...")
            self.ws_manager.disconnect()

        # Stop dashboard server
        if self.dashboard_server:
            print("\nStopping dashboard server...")
            self.dashboard_server.stop()

        # Print summary
        if self.strategy_manager:
            stats = self.strategy_manager.get_stats()
            print(f"\nSession Summary:")
            print(f"  Total ticks: {stats['tick_count']}")
            print(f"  Strategies: {stats['strategies_count']}")

        print("\nShutdown complete.")

    def _on_tick(self, tick: TickData) -> None:
        """Handle incoming tick data"""
        # Record tick to persistent storage
        self.tick_store.record_tick(
            instrument_key=tick.instrument_key,
            ltp=tick.ltp,
            timestamp=tick.timestamp,
            volume=tick.volume
        )

        # Pass to strategy manager for processing
        self.strategy_manager.on_tick(
            instrument_key=tick.instrument_key,
            ltp=tick.ltp,
            timestamp=tick.timestamp
        )

    def _on_entry_signal(self, strategy: Strategy, option_type: str) -> None:
        """Handle entry signal from strategy"""
        position = strategy.ce_position if option_type == 'CE' else strategy.pe_position
        if position:
            self.notifier.send_entry_signal(
                symbol=strategy.index,
                option_type=option_type,
                strike=position.strike,
                entry_price=position.entry_price,
                stop_loss=position.stop_loss
            )

    def _on_sl_hit(self, strategy: Strategy, option_type: str) -> None:
        """Handle stop loss hit"""
        position = strategy.ce_position if option_type == 'CE' else strategy.pe_position
        if position:
            self.notifier.send_stop_loss_hit(
                symbol=strategy.index,
                option_type=option_type,
                strike=position.strike,
                sl_price=position.current_ltp,
                entry_price=position.entry_price
            )

    def _on_phase_change(self, strategy: Strategy, old_phase: str, new_phase: str) -> None:
        """Handle phase change"""
        self.notifier.send_phase_change(old_phase, new_phase)

    def _on_ws_status(self, status: ConnectionStatus, message: str) -> None:
        """Handle WebSocket status changes"""
        if status == ConnectionStatus.CONNECTED:
            self.notifier.send_connection_status(True, message)
        elif status == ConnectionStatus.DISCONNECTED:
            self.notifier.send_connection_status(False, message)
        elif status == ConnectionStatus.ERROR:
            self.notifier.send_warning("WebSocket Error", message)

    # Strategy CRUD callbacks from dashboard
    def _on_create_strategy(self, data: dict) -> Strategy:
        """Handle create strategy request from dashboard"""
        print(f"\n[CREATE STRATEGY] {data}")

        strategy = self.strategy_manager.add_strategy(
            index=data.get('index', 'NIFTY'),
            entry_time=data.get('entry_time', '11:00'),
            lookback_minutes=data.get('lookback_minutes', 60),
            target_premium=data.get('target_premium', 60.0),
            stop_loss_percent=data.get('stop_loss_percent', 50.0)
        )

        # Save immediately
        strategies_data = self.strategy_manager.save_strategies()
        self.strategy_store.save(strategies_data)

        return strategy

    def _on_update_strategy(self, data: dict) -> bool:
        """Handle update strategy request from dashboard"""
        print(f"\n[UPDATE STRATEGY] {data}")

        strategy_id = data.get('strategy_id')
        if not strategy_id:
            return False

        success = self.strategy_manager.update_strategy(
            strategy_id=strategy_id,
            entry_time=data.get('entry_time'),
            lookback_minutes=data.get('lookback_minutes'),
            target_premium=data.get('target_premium'),
            stop_loss_percent=data.get('stop_loss_percent')
        )

        if success:
            # Save immediately
            strategies_data = self.strategy_manager.save_strategies()
            self.strategy_store.save(strategies_data)

        return success

    def _on_remove_strategy(self, strategy_id: str) -> bool:
        """Handle remove strategy request from dashboard"""
        print(f"\n[REMOVE STRATEGY] {strategy_id}")

        success = self.strategy_manager.remove_strategy(strategy_id)

        if success:
            # Save immediately
            strategies_data = self.strategy_manager.save_strategies()
            self.strategy_store.save(strategies_data)

        return success

    def _on_get_preview(self, data: dict) -> dict:
        """Handle get preview request from dashboard - returns historical data for lookback period"""
        index = data.get('index', 'NIFTY')
        entry_time = data.get('entry_time', '11:00')
        lookback_minutes = data.get('lookback_minutes', 60)
        target_premium = data.get('target_premium', 60.0)

        # Calculate lookback_start from entry_time - lookback_minutes
        parts = entry_time.split(':')
        entry_minutes = int(parts[0]) * 60 + int(parts[1])
        start_minutes = entry_minutes - lookback_minutes
        start_hour = start_minutes // 60
        start_min = start_minutes % 60
        lookback_start = f"{start_hour:02d}:{start_min:02d}"

        print(f"\n[GET PREVIEW] {index} | {lookback_start}-{entry_time} | Target: Rs.{target_premium}")

        return self.strategy_manager.get_preview_data(
            index=index,
            target_premium=target_premium,
            lookback_start=lookback_start,
            entry_time=entry_time
        )


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description='Options Breakout Tracker V2 - Multi-Strategy Edition'
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
        print(f"  Market Close: {settings.timing.market_close}")
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
