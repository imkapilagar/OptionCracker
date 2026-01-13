"""
Strategy Data Model for Options Breakout Tracker V2

Represents a user-defined trading strategy with:
- Index, Entry Time, Lookback Duration, Target Premium
- Phase tracking (PENDING → LOOKBACK → MONITORING → COMPLETED)
- Strike tracking during lookback
- Position tracking after entry
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Any
from enum import Enum


class StrategyPhase(Enum):
    """Strategy phase enumeration"""
    PENDING = "pending"         # Before lookback starts
    LOOKBACK = "lookback"       # Tracking lows during lookback period
    MONITORING = "monitoring"   # After entry - tracking P&L and SL
    COMPLETED = "completed"     # Strategy ended (market close or removed)


@dataclass
class StrategyStrikeData:
    """Data for a single option strike within a strategy"""
    instrument_key: str
    strike: float
    option_type: str  # CE or PE
    low: float = float('inf')
    ltp: float = 0.0
    tick_count: int = 0
    first_tick_time: Optional[str] = None
    last_tick_time: Optional[str] = None

    def update_tick(self, ltp: float, timestamp: datetime) -> bool:
        """Update with new tick. Returns True if new low."""
        self.ltp = ltp
        self.tick_count += 1
        self.last_tick_time = timestamp.strftime("%H:%M:%S")

        if self.first_tick_time is None:
            self.first_tick_time = timestamp.strftime("%H:%M:%S")

        if ltp < self.low:
            self.low = ltp
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'instrument_key': self.instrument_key,
            'strike': self.strike,
            'option_type': self.option_type,
            'low': self.low if self.low < float('inf') else None,
            'ltp': self.ltp,
            'tick_count': self.tick_count,
            'first_tick_time': self.first_tick_time,
            'last_tick_time': self.last_tick_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyStrikeData':
        return cls(
            instrument_key=data['instrument_key'],
            strike=data['strike'],
            option_type=data['option_type'],
            low=data['low'] if data.get('low') is not None else float('inf'),
            ltp=data.get('ltp', 0.0),
            tick_count=data.get('tick_count', 0),
            first_tick_time=data.get('first_tick_time'),
            last_tick_time=data.get('last_tick_time')
        )


@dataclass
class StrategyPosition:
    """Position created at entry time"""
    instrument_key: str
    strike: float
    option_type: str
    entry_price: float      # The low at entry time
    stop_loss: float        # entry_price * (1 + sl_percent/100)
    entry_time: str
    current_ltp: float = 0.0
    is_sl_hit: bool = False
    sl_hit_time: Optional[str] = None
    sl_hit_price: Optional[float] = None

    @property
    def unrealized_pnl(self) -> float:
        """Short position P&L: profit when price goes down"""
        if self.current_ltp == 0:
            return 0.0
        return self.entry_price - self.current_ltp

    @property
    def unrealized_pnl_percent(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.unrealized_pnl / self.entry_price) * 100

    def check_stop_loss(self, ltp: float, timestamp: datetime) -> bool:
        """Check if SL hit. Returns True if just hit."""
        self.current_ltp = ltp
        if not self.is_sl_hit and ltp >= self.stop_loss:
            self.is_sl_hit = True
            self.sl_hit_time = timestamp.strftime("%H:%M:%S")
            self.sl_hit_price = ltp
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'instrument_key': self.instrument_key,
            'strike': self.strike,
            'option_type': self.option_type,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'entry_time': self.entry_time,
            'current_ltp': self.current_ltp,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent,
            'is_sl_hit': self.is_sl_hit,
            'sl_hit_time': self.sl_hit_time,
            'sl_hit_price': self.sl_hit_price
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyPosition':
        pos = cls(
            instrument_key=data['instrument_key'],
            strike=data['strike'],
            option_type=data['option_type'],
            entry_price=data['entry_price'],
            stop_loss=data['stop_loss'],
            entry_time=data['entry_time'],
            current_ltp=data.get('current_ltp', 0.0),
            is_sl_hit=data.get('is_sl_hit', False),
            sl_hit_time=data.get('sl_hit_time'),
            sl_hit_price=data.get('sl_hit_price')
        )
        return pos


@dataclass
class Strategy:
    """
    User-defined trading strategy.

    Lifecycle:
    1. User creates strategy with index, entry_time, lookback_minutes, target_premium
    2. System calculates lookback_start from entry_time - lookback_minutes
    3. At lookback_start, phase changes to LOOKBACK, starts tracking lows
    4. At entry_time, phase changes to MONITORING, positions are created
    5. At market_close, phase changes to COMPLETED
    """
    id: str
    index: str                   # NIFTY, BANKNIFTY, SENSEX
    entry_time: str              # "11:00"
    lookback_minutes: int        # 60
    target_premium: float        # 60.0
    stop_loss_percent: float     # 50.0
    created_at: str

    # Computed fields
    lookback_start: str = ""     # Computed from entry_time - lookback_minutes

    # State
    phase: str = "pending"

    # Strike tracking during lookback
    ce_strikes: Dict[str, StrategyStrikeData] = field(default_factory=dict)
    pe_strikes: Dict[str, StrategyStrikeData] = field(default_factory=dict)

    # Instrument key to strike data mapping for O(1) lookup
    instrument_map: Dict[str, StrategyStrikeData] = field(default_factory=dict)

    # Positions after entry
    ce_position: Optional[StrategyPosition] = None
    pe_position: Optional[StrategyPosition] = None

    def __post_init__(self):
        """Calculate lookback_start if not set"""
        if not self.lookback_start:
            self.lookback_start = self._calculate_lookback_start()

    def _calculate_lookback_start(self) -> str:
        """Calculate lookback start time from entry_time - lookback_minutes"""
        parts = self.entry_time.split(':')
        entry_minutes = int(parts[0]) * 60 + int(parts[1])
        start_minutes = entry_minutes - self.lookback_minutes
        start_hour = start_minutes // 60
        start_min = start_minutes % 60
        return f"{start_hour:02d}:{start_min:02d}"

    def get_lookback_start_time(self) -> dt_time:
        """Get lookback_start as datetime.time object"""
        parts = self.lookback_start.split(':')
        return dt_time(int(parts[0]), int(parts[1]))

    def get_entry_time(self) -> dt_time:
        """Get entry_time as datetime.time object"""
        parts = self.entry_time.split(':')
        return dt_time(int(parts[0]), int(parts[1]))

    def add_strike(self, instrument_key: str, strike: float, option_type: str) -> None:
        """Add a strike to track"""
        strike_data = StrategyStrikeData(
            instrument_key=instrument_key,
            strike=strike,
            option_type=option_type
        )

        strike_key = str(int(strike))
        if option_type == 'CE':
            self.ce_strikes[strike_key] = strike_data
        else:
            self.pe_strikes[strike_key] = strike_data

        self.instrument_map[instrument_key] = strike_data

    def on_tick(self, instrument_key: str, ltp: float, timestamp: datetime) -> bool:
        """Process tick for this strategy. Returns True if relevant."""
        strike_data = self.instrument_map.get(instrument_key)
        if strike_data is None:
            return False

        if self.phase == StrategyPhase.LOOKBACK.value:
            strike_data.update_tick(ltp, timestamp)
            return True

        elif self.phase == StrategyPhase.MONITORING.value:
            strike_data.update_tick(ltp, timestamp)
            # Check positions
            if self.ce_position and self.ce_position.instrument_key == instrument_key:
                self.ce_position.check_stop_loss(ltp, timestamp)
            if self.pe_position and self.pe_position.instrument_key == instrument_key:
                self.pe_position.check_stop_loss(ltp, timestamp)
            return True

        return False

    def get_top_strikes(self, option_type: str, count: int = 3) -> List[StrategyStrikeData]:
        """Get top N strikes nearest to target premium"""
        strikes = self.ce_strikes if option_type == 'CE' else self.pe_strikes

        # Filter strikes with valid data
        valid = [s for s in strikes.values() if s.low < float('inf')]

        # Sort by distance to target
        valid.sort(key=lambda s: abs(s.low - self.target_premium))

        return valid[:count]

    def get_nearest_strike(self, option_type: str) -> Optional[StrategyStrikeData]:
        """Get strike nearest to target premium"""
        top = self.get_top_strikes(option_type, 1)
        return top[0] if top else None

    def generate_positions(self, timestamp: datetime) -> None:
        """Generate positions at entry time"""
        entry_time_str = timestamp.strftime("%H:%M:%S")
        sl_multiplier = 1 + (self.stop_loss_percent / 100)

        # CE position
        nearest_ce = self.get_nearest_strike('CE')
        if nearest_ce:
            self.ce_position = StrategyPosition(
                instrument_key=nearest_ce.instrument_key,
                strike=nearest_ce.strike,
                option_type='CE',
                entry_price=nearest_ce.low,
                stop_loss=nearest_ce.low * sl_multiplier,
                entry_time=entry_time_str,
                current_ltp=nearest_ce.ltp
            )

        # PE position
        nearest_pe = self.get_nearest_strike('PE')
        if nearest_pe:
            self.pe_position = StrategyPosition(
                instrument_key=nearest_pe.instrument_key,
                strike=nearest_pe.strike,
                option_type='PE',
                entry_price=nearest_pe.low,
                stop_loss=nearest_pe.low * sl_multiplier,
                entry_time=entry_time_str,
                current_ltp=nearest_pe.ltp
            )

    def get_state(self) -> Dict[str, Any]:
        """Get strategy state for dashboard"""
        state = {
            'id': self.id,
            'index': self.index,
            'entry_time': self.entry_time,
            'lookback_minutes': self.lookback_minutes,
            'lookback_start': self.lookback_start,
            'target_premium': self.target_premium,
            'stop_loss_percent': self.stop_loss_percent,
            'phase': self.phase,
            'created_at': self.created_at,

            # Top 3 strikes for preview
            'top_ce_strikes': [s.to_dict() for s in self.get_top_strikes('CE', 3)],
            'top_pe_strikes': [s.to_dict() for s in self.get_top_strikes('PE', 3)],

            # Positions (after entry)
            'ce_position': self.ce_position.to_dict() if self.ce_position else None,
            'pe_position': self.pe_position.to_dict() if self.pe_position else None,

            # Summary
            'total_pnl': self._calculate_total_pnl()
        }
        return state

    def _calculate_total_pnl(self) -> float:
        """Calculate total P&L from both positions"""
        total = 0.0
        if self.ce_position:
            total += self.ce_position.unrealized_pnl
        if self.pe_position:
            total += self.pe_position.unrealized_pnl
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Serialize strategy for persistence"""
        return {
            'id': self.id,
            'index': self.index,
            'entry_time': self.entry_time,
            'lookback_minutes': self.lookback_minutes,
            'lookback_start': self.lookback_start,
            'target_premium': self.target_premium,
            'stop_loss_percent': self.stop_loss_percent,
            'phase': self.phase,
            'created_at': self.created_at,
            'ce_strikes': {k: v.to_dict() for k, v in self.ce_strikes.items()},
            'pe_strikes': {k: v.to_dict() for k, v in self.pe_strikes.items()},
            'ce_position': self.ce_position.to_dict() if self.ce_position else None,
            'pe_position': self.pe_position.to_dict() if self.pe_position else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """Deserialize strategy from persistence"""
        strategy = cls(
            id=data['id'],
            index=data['index'],
            entry_time=data['entry_time'],
            lookback_minutes=data['lookback_minutes'],
            target_premium=data['target_premium'],
            stop_loss_percent=data['stop_loss_percent'],
            created_at=data['created_at'],
            lookback_start=data.get('lookback_start', ''),
            phase=data.get('phase', 'pending')
        )

        # Restore strikes
        for key, strike_data in data.get('ce_strikes', {}).items():
            sd = StrategyStrikeData.from_dict(strike_data)
            strategy.ce_strikes[key] = sd
            strategy.instrument_map[sd.instrument_key] = sd

        for key, strike_data in data.get('pe_strikes', {}).items():
            sd = StrategyStrikeData.from_dict(strike_data)
            strategy.pe_strikes[key] = sd
            strategy.instrument_map[sd.instrument_key] = sd

        # Restore positions
        if data.get('ce_position'):
            strategy.ce_position = StrategyPosition.from_dict(data['ce_position'])
        if data.get('pe_position'):
            strategy.pe_position = StrategyPosition.from_dict(data['pe_position'])

        return strategy

    @classmethod
    def create(
        cls,
        index: str,
        entry_time: str,
        lookback_minutes: int,
        target_premium: float,
        stop_loss_percent: float = 50.0
    ) -> 'Strategy':
        """Factory method to create a new strategy"""
        return cls(
            id=str(uuid.uuid4())[:8],
            index=index,
            entry_time=entry_time,
            lookback_minutes=lookback_minutes,
            target_premium=target_premium,
            stop_loss_percent=stop_loss_percent,
            created_at=datetime.now().strftime("%H:%M:%S")
        )

    def can_edit(self) -> bool:
        """Check if strategy can be edited (before entry)"""
        return self.phase in [StrategyPhase.PENDING.value, StrategyPhase.LOOKBACK.value]

    def update(
        self,
        entry_time: Optional[str] = None,
        lookback_minutes: Optional[int] = None,
        target_premium: Optional[float] = None,
        stop_loss_percent: Optional[float] = None
    ) -> bool:
        """Update strategy parameters. Returns True if updated."""
        if not self.can_edit():
            return False

        if entry_time is not None:
            self.entry_time = entry_time
        if lookback_minutes is not None:
            self.lookback_minutes = lookback_minutes
        if target_premium is not None:
            self.target_premium = target_premium
        if stop_loss_percent is not None:
            self.stop_loss_percent = stop_loss_percent

        # Recalculate lookback_start
        self.lookback_start = self._calculate_lookback_start()
        return True
