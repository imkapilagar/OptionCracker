"""
Breakout Tracker Core Engine for Options Breakout Tracker V2

Handles:
- Phase management (WAITING -> LOOKBACK -> ENTRY_SIGNAL -> MONITORING)
- Low price tracking during lookback period
- Entry signal generation at entry time
- Stop loss monitoring during monitoring phase
- P&L calculation
"""
from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import threading


class TrackerPhase(Enum):
    """Tracker phase enumeration"""
    WAITING = "waiting"           # Before lookback starts
    LOOKBACK = "lookback"         # Tracking lows
    ENTRY_SIGNAL = "entry_signal" # At entry time - generating signals
    MONITORING = "monitoring"     # After entry - tracking P&L and SL
    COMPLETED = "completed"       # Trading day ended


@dataclass
class StrikeData:
    """Data for a single option strike"""
    instrument_key: str
    symbol: str
    strike: float
    option_type: str  # CE or PE
    low: float = float('inf')
    ltp: float = 0.0
    first_tick_time: Optional[datetime] = None
    last_tick_time: Optional[datetime] = None
    tick_count: int = 0

    def update_tick(self, ltp: float, timestamp: datetime) -> bool:
        """
        Update with new tick data.

        Returns:
            True if new low was recorded
        """
        self.ltp = ltp
        self.last_tick_time = timestamp
        self.tick_count += 1

        if self.first_tick_time is None:
            self.first_tick_time = timestamp

        if ltp < self.low:
            self.low = ltp
            return True

        return False


@dataclass
class Position:
    """Represents a short position"""
    instrument_key: str
    symbol: str
    strike: float
    option_type: str
    entry_price: float      # The low at entry time
    stop_loss: float        # entry_price * (1 + sl_percent/100)
    entry_time: datetime
    current_ltp: float = 0.0
    is_sl_hit: bool = False
    sl_hit_time: Optional[datetime] = None
    sl_hit_price: Optional[float] = None

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L (for short position)"""
        if self.current_ltp == 0:
            return 0.0
        # Short position: profit when price goes down
        return self.entry_price - self.current_ltp

    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.entry_price == 0:
            return 0.0
        return (self.unrealized_pnl / self.entry_price) * 100

    def check_stop_loss(self, current_price: float, timestamp: datetime) -> bool:
        """
        Check if stop loss is hit.

        Returns:
            True if SL was just hit (first time)
        """
        self.current_ltp = current_price

        if not self.is_sl_hit and current_price >= self.stop_loss:
            self.is_sl_hit = True
            self.sl_hit_time = timestamp
            self.sl_hit_price = current_price
            return True

        return False


@dataclass
class SymbolTracker:
    """Tracker for a single symbol (NIFTY, SENSEX, BANKNIFTY)"""
    symbol: str
    target_premium: float
    stop_loss_percent: float
    spot_price: float = 0.0
    atm_strike: float = 0.0
    strike_step: int = 50
    expiry: str = ""

    # All strikes being tracked (key: strike price)
    ce_strikes: Dict[float, StrikeData] = field(default_factory=dict)
    pe_strikes: Dict[float, StrikeData] = field(default_factory=dict)

    # Instrument key to strike mapping
    instrument_map: Dict[str, StrikeData] = field(default_factory=dict)

    # Selected positions at entry time
    selected_ce: Optional[Position] = None
    selected_pe: Optional[Position] = None

    def add_strike(self, strike_data: StrikeData) -> None:
        """Add a strike to track"""
        if strike_data.option_type == 'CE':
            self.ce_strikes[strike_data.strike] = strike_data
        else:
            self.pe_strikes[strike_data.strike] = strike_data

        self.instrument_map[strike_data.instrument_key] = strike_data

    def get_nearest_to_target(self, option_type: str) -> Optional[StrikeData]:
        """Find strike with low nearest to target premium"""
        strikes = self.ce_strikes if option_type == 'CE' else self.pe_strikes

        if not strikes:
            return None

        # Filter strikes that have valid data
        valid_strikes = [s for s in strikes.values() if s.low < float('inf')]

        if not valid_strikes:
            return None

        # Find nearest to target
        return min(valid_strikes, key=lambda s: abs(s.low - self.target_premium))

    def create_position(self, strike_data: StrikeData, entry_time: datetime) -> Position:
        """Create a position from strike data"""
        sl_multiplier = 1 + (self.stop_loss_percent / 100)

        return Position(
            instrument_key=strike_data.instrument_key,
            symbol=self.symbol,
            strike=strike_data.strike,
            option_type=strike_data.option_type,
            entry_price=strike_data.low,
            stop_loss=strike_data.low * sl_multiplier,
            entry_time=entry_time,
            current_ltp=strike_data.ltp
        )


class BreakoutTracker:
    """
    Main breakout tracking engine.

    Phases:
    1. WAITING: Before 10:00 AM - setup and subscribe
    2. LOOKBACK: 10:00-11:00 AM - track lows for all strikes
    3. ENTRY_SIGNAL: At 11:00 AM - find nearest to target and signal
    4. MONITORING: After 11:00 AM - track P&L and SL
    5. COMPLETED: After market close
    """

    def __init__(
        self,
        lookback_start: dt_time,
        lookback_end: dt_time,
        entry_time: dt_time,
        market_close: dt_time,
        on_signal: Callable[[Position], None],
        on_sl_hit: Callable[[Position], None],
        on_phase_change: Optional[Callable[[TrackerPhase, TrackerPhase], None]] = None,
        on_new_low: Optional[Callable[[StrikeData], None]] = None
    ):
        """
        Initialize breakout tracker.

        Args:
            lookback_start: Start time for lookback period
            lookback_end: End time for lookback period (same as entry_time)
            entry_time: Time to generate entry signals
            market_close: Market close time
            on_signal: Callback when entry signal is generated
            on_sl_hit: Callback when stop loss is hit
            on_phase_change: Optional callback for phase changes
            on_new_low: Optional callback when new low is detected
        """
        self.lookback_start = lookback_start
        self.lookback_end = lookback_end
        self.entry_time = entry_time
        self.market_close = market_close

        self.on_signal = on_signal
        self.on_sl_hit = on_sl_hit
        self.on_phase_change = on_phase_change
        self.on_new_low = on_new_low

        # State
        self._phase = TrackerPhase.WAITING
        self._symbols: Dict[str, SymbolTracker] = {}
        self._positions: List[Position] = []
        self._entry_signals_generated = False
        self._lock = threading.Lock()

        # Stats
        self._tick_count = 0
        self._start_time: Optional[datetime] = None

    @property
    def phase(self) -> TrackerPhase:
        """Current tracker phase"""
        return self._phase

    @property
    def positions(self) -> List[Position]:
        """All generated positions"""
        return self._positions.copy()

    def add_symbol(
        self,
        symbol: str,
        target_premium: float,
        stop_loss_percent: float,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Add a symbol to track.

        Args:
            symbol: Symbol name (NIFTY, SENSEX, BANKNIFTY)
            target_premium: Target premium for this symbol
            stop_loss_percent: Stop loss percentage
            metadata: Metadata from instrument builder (includes strike_map)
        """
        tracker = SymbolTracker(
            symbol=symbol,
            target_premium=target_premium,
            stop_loss_percent=stop_loss_percent,
            spot_price=metadata.get('spot_price', 0),
            atm_strike=metadata.get('atm_strike', 0),
            strike_step=metadata.get('strike_step', 50),
            expiry=metadata.get('expiry', '')
        )

        # Add strikes from metadata
        strike_map = metadata.get('strike_map', {})

        for opt_type in ['CE', 'PE']:
            for strike, instrument_key in strike_map.get(opt_type, {}).items():
                strike_data = StrikeData(
                    instrument_key=instrument_key,
                    symbol=symbol,
                    strike=strike,
                    option_type=opt_type
                )
                tracker.add_strike(strike_data)

        self._symbols[symbol] = tracker
        print(f"Added {symbol}: {len(tracker.ce_strikes)} CE + {len(tracker.pe_strikes)} PE strikes")

    def on_tick(self, instrument_key: str, ltp: float, timestamp: datetime) -> None:
        """
        Process incoming tick data.

        Args:
            instrument_key: Instrument key
            ltp: Last traded price
            timestamp: Tick timestamp
        """
        with self._lock:
            self._tick_count += 1

            if self._start_time is None:
                self._start_time = timestamp

            # Find the strike data for this instrument
            strike_data = self._find_strike_data(instrument_key)
            if strike_data is None:
                return

            # Process based on current phase
            if self._phase == TrackerPhase.LOOKBACK:
                # Track lows during lookback
                is_new_low = strike_data.update_tick(ltp, timestamp)
                if is_new_low and self.on_new_low:
                    self.on_new_low(strike_data)

            elif self._phase == TrackerPhase.MONITORING:
                # Update LTP and check stop loss for positions
                strike_data.update_tick(ltp, timestamp)
                self._check_positions_sl(instrument_key, ltp, timestamp)

            elif self._phase == TrackerPhase.WAITING:
                # Just update data
                strike_data.update_tick(ltp, timestamp)

    def _find_strike_data(self, instrument_key: str) -> Optional[StrikeData]:
        """Find strike data by instrument key"""
        for symbol_tracker in self._symbols.values():
            if instrument_key in symbol_tracker.instrument_map:
                return symbol_tracker.instrument_map[instrument_key]
        return None

    def _check_positions_sl(
        self,
        instrument_key: str,
        ltp: float,
        timestamp: datetime
    ) -> None:
        """Check if any position's stop loss is hit"""
        for position in self._positions:
            if position.instrument_key == instrument_key:
                if position.check_stop_loss(ltp, timestamp):
                    # SL hit!
                    self.on_sl_hit(position)

    def check_phase_transition(self) -> None:
        """
        Check if phase should transition based on current time.
        Should be called periodically.

        Handles late starts: if started after entry_time, stays in LOOKBACK
        to collect some data before generating signals.
        """
        now = datetime.now().time()

        with self._lock:
            old_phase = self._phase

            if self._phase == TrackerPhase.WAITING:
                # Always start with lookback if market is open
                if now >= self.lookback_start and now < self.market_close:
                    self._phase = TrackerPhase.LOOKBACK

                    if now >= self.entry_time:
                        print(f"\n{'='*60}")
                        print(f"PHASE: LOOKBACK (LATE START) at {now}")
                        print(f"Started after entry time - tracking lows for 2 minutes")
                        print(f"{'='*60}\n")
                        # Mark that we need delayed entry signal generation
                        self._late_start = True
                        self._late_start_time = datetime.now()
                    else:
                        print(f"\n{'='*60}")
                        print(f"PHASE: LOOKBACK STARTED at {now}")
                        print(f"Tracking lows until {self.entry_time}")
                        print(f"{'='*60}\n")
                        self._late_start = False

            elif self._phase == TrackerPhase.LOOKBACK:
                should_generate_signals = False

                if hasattr(self, '_late_start') and self._late_start:
                    # For late starts, wait 30 seconds to collect data
                    elapsed = (datetime.now() - self._late_start_time).total_seconds()
                    if elapsed >= 30:  # 30 seconds
                        should_generate_signals = True
                        print(f"\n{'='*60}")
                        print(f"PHASE: ENTRY TIME (LATE START) - {elapsed:.0f}s of data collected")
                        print(f"{'='*60}\n")
                elif now >= self.entry_time:
                    should_generate_signals = True
                    print(f"\n{'='*60}")
                    print(f"PHASE: ENTRY TIME at {now}")
                    print(f"{'='*60}\n")

                if should_generate_signals:
                    self._phase = TrackerPhase.ENTRY_SIGNAL

                    # Generate entry signals
                    if not self._entry_signals_generated:
                        self._generate_entry_signals()
                        self._entry_signals_generated = True

                    # Move to monitoring
                    self._phase = TrackerPhase.MONITORING
                    print(f"\n{'='*60}")
                    print(f"PHASE: MONITORING STARTED")
                    print(f"Tracking positions until {self.market_close}")
                    print(f"{'='*60}\n")

            elif self._phase == TrackerPhase.MONITORING:
                if now >= self.market_close:
                    self._phase = TrackerPhase.COMPLETED
                    print(f"\n{'='*60}")
                    print(f"PHASE: COMPLETED - Market closed at {now}")
                    print(f"{'='*60}\n")

            # Notify phase change
            if old_phase != self._phase and self.on_phase_change:
                self.on_phase_change(old_phase, self._phase)

    def _generate_entry_signals(self) -> None:
        """Generate entry signals for all symbols"""
        entry_time = datetime.now()

        print("\n" + "="*70)
        print("GENERATING ENTRY SIGNALS")
        print("="*70)

        for symbol, tracker in self._symbols.items():
            print(f"\n{symbol} (Target: Rs.{tracker.target_premium}):")

            # Find nearest CE to target
            nearest_ce = tracker.get_nearest_to_target('CE')
            if nearest_ce:
                position = tracker.create_position(nearest_ce, entry_time)
                tracker.selected_ce = position
                self._positions.append(position)

                print(f"  CE: Strike {int(position.strike)} | "
                      f"Entry Rs.{position.entry_price:.2f} | "
                      f"SL Rs.{position.stop_loss:.2f}")

                self.on_signal(position)
            else:
                print(f"  CE: No valid data")

            # Find nearest PE to target
            nearest_pe = tracker.get_nearest_to_target('PE')
            if nearest_pe:
                position = tracker.create_position(nearest_pe, entry_time)
                tracker.selected_pe = position
                self._positions.append(position)

                print(f"  PE: Strike {int(position.strike)} | "
                      f"Entry Rs.{position.entry_price:.2f} | "
                      f"SL Rs.{position.stop_loss:.2f}")

                self.on_signal(position)
            else:
                print(f"  PE: No valid data")

        print("\n" + "="*70)
        print(f"Total positions: {len(self._positions)}")
        print("="*70 + "\n")

    def get_state(self) -> Dict[str, Any]:
        """
        Get current state for dashboard/persistence.

        Returns:
            Dictionary with complete current state
        """
        with self._lock:
            state = {
                'phase': self._phase.value,
                'tick_count': self._tick_count,
                'start_time': self._start_time.isoformat() if self._start_time else None,
                'current_time': datetime.now().isoformat(),
                'entry_time': self.entry_time.strftime('%H:%M'),
                'symbols': {},
                'positions': [],
                'summary': {}
            }

            # Add symbol data
            for symbol, tracker in self._symbols.items():
                symbol_data = {
                    'symbol': symbol,
                    'target_premium': tracker.target_premium,
                    'stop_loss_percent': tracker.stop_loss_percent,
                    'spot_price': tracker.spot_price,
                    'atm_strike': tracker.atm_strike,
                    'expiry': tracker.expiry,
                    'ce_strikes': {},
                    'pe_strikes': {},
                    'selected_ce': None,
                    'selected_pe': None
                }

                # CE strikes
                for strike, data in tracker.ce_strikes.items():
                    symbol_data['ce_strikes'][str(int(strike))] = {
                        'strike': strike,
                        'low': data.low if data.low < float('inf') else None,
                        'ltp': data.ltp,
                        'tick_count': data.tick_count,
                        'distance_to_target': abs(data.low - tracker.target_premium) if data.low < float('inf') else None
                    }

                # PE strikes
                for strike, data in tracker.pe_strikes.items():
                    symbol_data['pe_strikes'][str(int(strike))] = {
                        'strike': strike,
                        'low': data.low if data.low < float('inf') else None,
                        'ltp': data.ltp,
                        'tick_count': data.tick_count,
                        'distance_to_target': abs(data.low - tracker.target_premium) if data.low < float('inf') else None
                    }

                # Selected positions
                if tracker.selected_ce:
                    symbol_data['selected_ce'] = self._position_to_dict(tracker.selected_ce)
                if tracker.selected_pe:
                    symbol_data['selected_pe'] = self._position_to_dict(tracker.selected_pe)

                state['symbols'][symbol] = symbol_data

            # Add positions
            for position in self._positions:
                state['positions'].append(self._position_to_dict(position))

            # Summary
            total_pnl = sum(p.unrealized_pnl for p in self._positions)
            sl_hit_count = sum(1 for p in self._positions if p.is_sl_hit)

            state['summary'] = {
                'total_positions': len(self._positions),
                'sl_hit_count': sl_hit_count,
                'total_unrealized_pnl': total_pnl,
                'phase': self._phase.value
            }

            return state

    def _position_to_dict(self, position: Position) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            'symbol': position.symbol,
            'strike': position.strike,
            'option_type': position.option_type,
            'entry_price': position.entry_price,
            'stop_loss': position.stop_loss,
            'current_ltp': position.current_ltp,
            'unrealized_pnl': position.unrealized_pnl,
            'unrealized_pnl_percent': position.unrealized_pnl_percent,
            'is_sl_hit': position.is_sl_hit,
            'sl_hit_time': position.sl_hit_time.isoformat() if position.sl_hit_time else None,
            'sl_hit_price': position.sl_hit_price,
            'entry_time': position.entry_time.isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        with self._lock:
            return {
                'phase': self._phase.value,
                'tick_count': self._tick_count,
                'symbols_count': len(self._symbols),
                'positions_count': len(self._positions),
                'start_time': self._start_time.isoformat() if self._start_time else None
            }
