"""
Configuration settings for Options Breakout Tracker V2
"""
from dataclasses import dataclass, field
from datetime import time as dt_time
from typing import Dict, Optional
from pathlib import Path
import yaml


@dataclass
class SymbolConfig:
    """Configuration for a single trading symbol"""
    enabled: bool
    index_key: str
    option_prefix: str
    exchange: str
    target_premium: float
    stop_loss_percent: float
    strike_step: int
    strikes_range: int


@dataclass
class TimingConfig:
    """Market timing configuration"""
    lookback_start: dt_time
    lookback_end: dt_time
    entry_time: dt_time
    market_close: dt_time
    lookback_duration_minutes: int


@dataclass
class WebSocketConfig:
    """WebSocket connection configuration"""
    subscription_mode: str
    auto_reconnect: bool
    reconnect_interval_seconds: int
    max_reconnect_attempts: int


@dataclass
class DashboardConfig:
    """Dashboard server configuration"""
    enabled: bool
    host: str
    port: int
    update_throttle_ms: int


@dataclass
class AlertsConfig:
    """Alerts configuration"""
    desktop_notifications: bool
    sound_enabled: bool
    console_logging: bool


@dataclass
class PersistenceConfig:
    """State persistence configuration"""
    save_interval_seconds: int
    output_directory: str
    file_prefix: str


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str
    file: str
    console: bool


@dataclass
class Settings:
    """Main settings container"""
    timing: TimingConfig
    symbols: Dict[str, SymbolConfig]
    websocket: WebSocketConfig
    dashboard: DashboardConfig
    alerts: AlertsConfig
    persistence: PersistenceConfig
    logging: LoggingConfig

    @classmethod
    def _parse_time(cls, time_str: str) -> dt_time:
        """Parse time string (HH:MM) to datetime.time"""
        parts = time_str.split(':')
        return dt_time(int(parts[0]), int(parts[1]))

    @classmethod
    def from_dict(cls, config: dict) -> "Settings":
        """Create Settings from dictionary"""
        # Parse timing
        timing_raw = config['timing']
        timing = TimingConfig(
            lookback_start=cls._parse_time(timing_raw['lookback_start']),
            lookback_end=cls._parse_time(timing_raw['lookback_end']),
            entry_time=cls._parse_time(timing_raw['entry_time']),
            market_close=cls._parse_time(timing_raw['market_close']),
            lookback_duration_minutes=timing_raw['lookback_duration_minutes']
        )

        # Parse symbols
        symbols = {}
        for name, sym_config in config['symbols'].items():
            symbols[name] = SymbolConfig(
                enabled=sym_config['enabled'],
                index_key=sym_config['index_key'],
                option_prefix=sym_config['option_prefix'],
                exchange=sym_config['exchange'],
                target_premium=sym_config['target_premium'],
                stop_loss_percent=sym_config['stop_loss_percent'],
                strike_step=sym_config['strike_step'],
                strikes_range=sym_config['strikes_range']
            )

        # Parse websocket
        ws_raw = config['websocket']
        websocket = WebSocketConfig(
            subscription_mode=ws_raw['subscription_mode'],
            auto_reconnect=ws_raw['auto_reconnect'],
            reconnect_interval_seconds=ws_raw['reconnect_interval_seconds'],
            max_reconnect_attempts=ws_raw['max_reconnect_attempts']
        )

        # Parse dashboard
        dash_raw = config['dashboard']
        dashboard = DashboardConfig(
            enabled=dash_raw['enabled'],
            host=dash_raw['host'],
            port=dash_raw['port'],
            update_throttle_ms=dash_raw['update_throttle_ms']
        )

        # Parse alerts
        alerts_raw = config['alerts']
        alerts = AlertsConfig(
            desktop_notifications=alerts_raw['desktop_notifications'],
            sound_enabled=alerts_raw['sound_enabled'],
            console_logging=alerts_raw['console_logging']
        )

        # Parse persistence
        persist_raw = config['persistence']
        persistence = PersistenceConfig(
            save_interval_seconds=persist_raw['save_interval_seconds'],
            output_directory=persist_raw['output_directory'],
            file_prefix=persist_raw['file_prefix']
        )

        # Parse logging
        log_raw = config['logging']
        logging_config = LoggingConfig(
            level=log_raw['level'],
            file=log_raw['file'],
            console=log_raw['console']
        )

        return cls(
            timing=timing,
            symbols=symbols,
            websocket=websocket,
            dashboard=dashboard,
            alerts=alerts,
            persistence=persistence,
            logging=logging_config
        )

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent / 'default_config.yaml'

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return cls.from_dict(config)

    @classmethod
    def load_default(cls) -> "Settings":
        """Load default settings"""
        return cls.load()

    def get_enabled_symbols(self) -> Dict[str, SymbolConfig]:
        """Get only enabled symbols"""
        return {name: cfg for name, cfg in self.symbols.items() if cfg.enabled}
