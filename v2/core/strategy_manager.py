"""
Strategy Manager for Options Breakout Tracker V2

Orchestrates multiple strategies:
- Routes ticks to relevant strategies based on index
- Handles phase transitions per-strategy
- Manages strategy CRUD operations
- Provides combined state for dashboard
"""
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Callable, Any
import threading

from v2.core.strategy import Strategy, StrategyPhase
from v2.persistence.tick_data_store import TickDataStore


class StrategyManager:
    """
    Manages multiple trading strategies.

    Each strategy has its own:
    - Index (NIFTY, BANKNIFTY, SENSEX)
    - Timing (entry_time, lookback_minutes)
    - Target premium
    - Phase tracking
    - Positions
    """

    def __init__(
        self,
        market_close: str = "15:30",
        on_entry_signal: Optional[Callable[[Strategy, str], None]] = None,
        on_sl_hit: Optional[Callable[[Strategy, str], None]] = None,
        on_phase_change: Optional[Callable[[Strategy, str, str], None]] = None,
        tick_data_filepath: Optional[str] = None
    ):
        """
        Initialize strategy manager.

        Args:
            market_close: Market close time (HH:MM)
            on_entry_signal: Callback when position is created (strategy, option_type)
            on_sl_hit: Callback when SL is hit (strategy, option_type)
            on_phase_change: Callback when phase changes (strategy, old_phase, new_phase)
            tick_data_filepath: Path to tick data file for loading historical data
        """
        self.market_close = market_close
        self.on_entry_signal = on_entry_signal
        self.on_sl_hit = on_sl_hit
        self.on_phase_change = on_phase_change
        self.tick_data_filepath = tick_data_filepath

        self._strategies: Dict[str, Strategy] = {}  # id -> Strategy
        self._lock = threading.Lock()

        # Index to instrument mapping (populated by main app)
        self._index_instruments: Dict[str, Dict[str, Any]] = {}  # index -> {instrument_key: strike_info}

        # Stats
        self._tick_count = 0
        self._start_time: Optional[datetime] = None

    def set_index_instruments(self, index: str, instruments: Dict[str, Any]) -> None:
        """
        Set instruments for an index.

        Args:
            index: Index name (NIFTY, BANKNIFTY, SENSEX)
            instruments: Dict mapping instrument_key to {strike, option_type}
        """
        self._index_instruments[index] = instruments

    def add_strategy(
        self,
        index: str,
        entry_time: str,
        lookback_minutes: int,
        target_premium: float,
        stop_loss_percent: float = 50.0
    ) -> Strategy:
        """
        Create and add a new strategy.

        Args:
            index: Index to track (NIFTY, BANKNIFTY, SENSEX)
            entry_time: Entry time (HH:MM)
            lookback_minutes: Lookback duration
            target_premium: Target premium for strike selection
            stop_loss_percent: Stop loss percentage

        Returns:
            Created Strategy
        """
        strategy = Strategy.create(
            index=index,
            entry_time=entry_time,
            lookback_minutes=lookback_minutes,
            target_premium=target_premium,
            stop_loss_percent=stop_loss_percent
        )

        # Add strikes for this index
        if index in self._index_instruments:
            for inst_key, info in self._index_instruments[index].items():
                strategy.add_strike(
                    instrument_key=inst_key,
                    strike=info['strike'],
                    option_type=info['option_type']
                )

        # Load historical tick data for the lookback period
        self._load_historical_data(strategy)

        with self._lock:
            self._strategies[strategy.id] = strategy

        print(f"[StrategyManager] Added strategy {strategy.id}: {index} @ {entry_time}")
        return strategy

    def _load_historical_data(self, strategy: Strategy) -> None:
        """
        Load historical tick data for a strategy's lookback period.

        This allows creating strategies mid-day that use already-captured data.
        """
        if not self.tick_data_filepath:
            return

        # Get lookback time range
        lookback_start = strategy.lookback_start
        entry_time = strategy.entry_time

        # Get list of instrument keys for this strategy
        instrument_keys = list(strategy.instrument_map.keys())

        if not instrument_keys:
            return

        try:
            # Load historical lows for the time range
            historical_data = TickDataStore.get_strike_lows_for_range(
                filepath=self.tick_data_filepath,
                start_time=lookback_start,
                end_time=entry_time,
                instrument_keys=instrument_keys
            )

            if not historical_data:
                print(f"[StrategyManager] No historical data found for {strategy.index} ({lookback_start}-{entry_time})")
                return

            # Update strike data with historical lows
            loaded_count = 0
            for inst_key, hist in historical_data.items():
                strike_data = strategy.instrument_map.get(inst_key)
                if strike_data:
                    strike_data.low = hist['low']
                    strike_data.ltp = hist['ltp']
                    strike_data.tick_count = hist['tick_count']
                    strike_data.first_tick_time = hist['first_tick']
                    strike_data.last_tick_time = hist['last_tick']
                    loaded_count += 1

            print(f"[StrategyManager] Loaded historical data for {loaded_count} strikes ({lookback_start}-{entry_time})")

        except Exception as e:
            print(f"[StrategyManager] Error loading historical data: {e}")

    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy by ID."""
        with self._lock:
            if strategy_id in self._strategies:
                strategy = self._strategies.pop(strategy_id)
                print(f"[StrategyManager] Removed strategy {strategy_id}: {strategy.index}")
                return True
        return False

    def update_strategy(
        self,
        strategy_id: str,
        entry_time: Optional[str] = None,
        lookback_minutes: Optional[int] = None,
        target_premium: Optional[float] = None,
        stop_loss_percent: Optional[float] = None
    ) -> bool:
        """Update a strategy's parameters (only before entry)."""
        with self._lock:
            strategy = self._strategies.get(strategy_id)
            if strategy:
                return strategy.update(
                    entry_time=entry_time,
                    lookback_minutes=lookback_minutes,
                    target_premium=target_premium,
                    stop_loss_percent=stop_loss_percent
                )
        return False

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by ID."""
        return self._strategies.get(strategy_id)

    def get_all_strategies(self) -> List[Strategy]:
        """Get all strategies."""
        return list(self._strategies.values())

    def on_tick(self, instrument_key: str, ltp: float, timestamp: datetime) -> None:
        """
        Process incoming tick.

        Routes to all relevant strategies.
        """
        self._tick_count += 1
        if self._start_time is None:
            self._start_time = timestamp

        with self._lock:
            for strategy in self._strategies.values():
                # Check if this instrument belongs to strategy's index
                if instrument_key in strategy.instrument_map:
                    strategy.on_tick(instrument_key, ltp, timestamp)

                    # Check for SL hits in monitoring phase
                    if strategy.phase == StrategyPhase.MONITORING.value:
                        if strategy.ce_position and strategy.ce_position.instrument_key == instrument_key:
                            if strategy.ce_position.is_sl_hit and self.on_sl_hit:
                                self.on_sl_hit(strategy, 'CE')
                        if strategy.pe_position and strategy.pe_position.instrument_key == instrument_key:
                            if strategy.pe_position.is_sl_hit and self.on_sl_hit:
                                self.on_sl_hit(strategy, 'PE')

    def check_phase_transitions(self) -> None:
        """
        Check and handle phase transitions for all strategies.

        Should be called periodically (e.g., every second).
        """
        now = datetime.now().time()
        market_close_time = self._parse_time(self.market_close)

        with self._lock:
            for strategy in self._strategies.values():
                old_phase = strategy.phase
                new_phase = self._get_target_phase(strategy, now, market_close_time)

                if old_phase != new_phase:
                    self._transition_phase(strategy, old_phase, new_phase)

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse HH:MM string to time object."""
        parts = time_str.split(':')
        return dt_time(int(parts[0]), int(parts[1]))

    def _get_target_phase(self, strategy: Strategy, now: dt_time, market_close: dt_time) -> str:
        """Determine what phase strategy should be in."""
        lookback_start = strategy.get_lookback_start_time()
        entry_time = strategy.get_entry_time()

        if now >= market_close:
            return StrategyPhase.COMPLETED.value
        elif now >= entry_time:
            return StrategyPhase.MONITORING.value
        elif now >= lookback_start:
            return StrategyPhase.LOOKBACK.value
        else:
            return StrategyPhase.PENDING.value

    def _transition_phase(self, strategy: Strategy, old_phase: str, new_phase: str) -> None:
        """Handle phase transition for a strategy."""
        strategy.phase = new_phase

        print(f"[Strategy {strategy.id}] Phase: {old_phase} → {new_phase}")

        # Handle entry signal generation
        if new_phase == StrategyPhase.MONITORING.value:
            strategy.generate_positions(datetime.now())

            if strategy.ce_position:
                print(f"  CE: Strike {int(strategy.ce_position.strike)} | "
                      f"Entry ₹{strategy.ce_position.entry_price:.2f} | "
                      f"SL ₹{strategy.ce_position.stop_loss:.2f}")
                if self.on_entry_signal:
                    self.on_entry_signal(strategy, 'CE')

            if strategy.pe_position:
                print(f"  PE: Strike {int(strategy.pe_position.strike)} | "
                      f"Entry ₹{strategy.pe_position.entry_price:.2f} | "
                      f"SL ₹{strategy.pe_position.stop_loss:.2f}")
                if self.on_entry_signal:
                    self.on_entry_signal(strategy, 'PE')

        # Notify phase change
        if self.on_phase_change:
            self.on_phase_change(strategy, old_phase, new_phase)

    def get_state(self) -> Dict[str, Any]:
        """
        Get combined state for dashboard.

        Returns:
            Dict with all strategies and summary
        """
        with self._lock:
            strategies_state = []
            for strategy in self._strategies.values():
                strategies_state.append(strategy.get_state())

            # Calculate totals
            total_pnl = sum(s.get('total_pnl', 0) for s in strategies_state)
            active_count = sum(1 for s in strategies_state
                             if s['phase'] in ['lookback', 'monitoring'])

            return {
                'tick_count': self._tick_count,
                'start_time': self._start_time.isoformat() if self._start_time else None,
                'current_time': datetime.now().isoformat(),
                'market_close': self.market_close,
                'strategies': strategies_state,
                'summary': {
                    'total_strategies': len(self._strategies),
                    'active_strategies': active_count,
                    'total_pnl': total_pnl
                }
            }

    def get_preview_data(self, index: str, target_premium: float, lookback_start: str, entry_time: str) -> Dict[str, Any]:
        """
        Get preview data for strategy builder using historical tick data.

        Shows top 3 strikes nearest to target for the selected index,
        calculated from historical lows in the specified time range.

        Args:
            index: Index to preview
            target_premium: Target premium for distance calculation
            lookback_start: Start of lookback period (HH:MM)
            entry_time: End of lookback period (HH:MM)

        Returns:
            Dict with top strikes for CE and PE
        """
        ce_strikes = []
        pe_strikes = []

        # Get instrument keys for this index
        instruments = self._index_instruments.get(index, {})
        if not instruments:
            return {
                'index': index,
                'target_premium': target_premium,
                'lookback_start': lookback_start,
                'entry_time': entry_time,
                'top_ce_strikes': [],
                'top_pe_strikes': [],
                'message': f'No instruments found for {index}'
            }

        # Load historical data from tick file
        if self.tick_data_filepath:
            try:
                instrument_keys = list(instruments.keys())
                historical_data = TickDataStore.get_strike_lows_for_range(
                    filepath=self.tick_data_filepath,
                    start_time=lookback_start,
                    end_time=entry_time,
                    instrument_keys=instrument_keys
                )

                # Build strike data from historical lows
                for inst_key, hist in historical_data.items():
                    info = instruments.get(inst_key)
                    if not info:
                        continue

                    strike_data = {
                        'strike': info['strike'],
                        'low': hist['low'],
                        'ltp': hist['ltp'],
                        'tick_count': hist['tick_count'],
                        'distance': abs(hist['low'] - target_premium)
                    }

                    if info['option_type'] == 'CE':
                        ce_strikes.append(strike_data)
                    else:
                        pe_strikes.append(strike_data)

            except Exception as e:
                print(f"[StrategyManager] Error loading preview data: {e}")

        # Sort by distance to target
        ce_strikes.sort(key=lambda x: x['distance'])
        pe_strikes.sort(key=lambda x: x['distance'])

        return {
            'index': index,
            'target_premium': target_premium,
            'lookback_start': lookback_start,
            'entry_time': entry_time,
            'top_ce_strikes': ce_strikes[:3],
            'top_pe_strikes': pe_strikes[:3],
            'total_ce_strikes': len(ce_strikes),
            'total_pe_strikes': len(pe_strikes)
        }

    def load_strategies(self, strategies_data: List[Dict[str, Any]]) -> int:
        """
        Load strategies from persistence.

        Args:
            strategies_data: List of serialized strategies

        Returns:
            Number of strategies loaded
        """
        count = 0
        for data in strategies_data:
            try:
                strategy = Strategy.from_dict(data)

                # Re-add instruments for this index
                if strategy.index in self._index_instruments:
                    for inst_key, info in self._index_instruments[strategy.index].items():
                        if inst_key not in strategy.instrument_map:
                            strategy.add_strike(
                                instrument_key=inst_key,
                                strike=info['strike'],
                                option_type=info['option_type']
                            )

                self._strategies[strategy.id] = strategy
                count += 1
                print(f"[StrategyManager] Loaded strategy {strategy.id}: {strategy.index} @ {strategy.entry_time}")
            except Exception as e:
                print(f"[StrategyManager] Failed to load strategy: {e}")

        return count

    def save_strategies(self) -> List[Dict[str, Any]]:
        """
        Serialize all strategies for persistence.

        Returns:
            List of serialized strategies
        """
        with self._lock:
            return [s.to_dict() for s in self._strategies.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            'tick_count': self._tick_count,
            'strategies_count': len(self._strategies),
            'start_time': self._start_time.isoformat() if self._start_time else None
        }
