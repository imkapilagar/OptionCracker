"""
Alert/Notification System for Options Breakout Tracker V2

Supports:
- macOS Desktop Notifications (osascript)
- Console logging with formatting
- Sound alerts
"""
import subprocess
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AlertType(Enum):
    """Types of alerts"""
    ENTRY_SIGNAL = "entry_signal"
    STOP_LOSS_HIT = "stop_loss_hit"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    PHASE_CHANGE = "phase_change"
    NEW_LOW = "new_low"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Alert:
    """Alert data structure"""
    alert_type: AlertType
    title: str
    message: str
    symbol: Optional[str] = None
    strike: Optional[float] = None
    option_type: Optional[str] = None
    price: Optional[float] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class Notifier:
    """
    Multi-channel alert system.

    Channels:
    1. macOS Desktop Notifications (osascript)
    2. Console logging (structured)
    3. Sound alerts
    """

    # Sound mappings for different alert types
    SOUNDS = {
        AlertType.ENTRY_SIGNAL: "Glass",
        AlertType.STOP_LOSS_HIT: "Sosumi",
        AlertType.CONNECTION_LOST: "Basso",
        AlertType.CONNECTION_RESTORED: "Ping",
        AlertType.PHASE_CHANGE: "Pop",
        AlertType.WARNING: "Funk",
    }

    def __init__(
        self,
        desktop_notifications: bool = True,
        sound_enabled: bool = True,
        console_logging: bool = True
    ):
        """
        Initialize notifier.

        Args:
            desktop_notifications: Enable macOS desktop notifications
            sound_enabled: Enable sound alerts
            console_logging: Enable console logging
        """
        self.desktop_enabled = desktop_notifications
        self.sound_enabled = sound_enabled
        self.console_enabled = console_logging

    def send(self, alert: Alert) -> None:
        """
        Send alert through all enabled channels.

        Args:
            alert: Alert to send
        """
        if self.console_enabled:
            self._log_to_console(alert)

        if self.desktop_enabled:
            self._send_desktop_notification(alert)

        if self.sound_enabled and alert.alert_type in self.SOUNDS:
            self._play_sound(alert.alert_type)

    def send_entry_signal(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        entry_price: float,
        stop_loss: float
    ) -> None:
        """Send entry signal alert"""
        alert = Alert(
            alert_type=AlertType.ENTRY_SIGNAL,
            title=f"SHORT SIGNAL: {symbol} {option_type}",
            message=f"Strike {int(strike)} @ Rs.{entry_price:.2f} | SL Rs.{stop_loss:.2f}",
            symbol=symbol,
            strike=strike,
            option_type=option_type,
            price=entry_price
        )
        self.send(alert)

    def send_stop_loss_hit(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        sl_price: float,
        entry_price: float
    ) -> None:
        """Send stop loss hit alert"""
        loss = sl_price - entry_price
        loss_pct = (loss / entry_price) * 100

        alert = Alert(
            alert_type=AlertType.STOP_LOSS_HIT,
            title=f"STOP LOSS HIT: {symbol} {option_type}",
            message=f"Strike {int(strike)} | SL @ Rs.{sl_price:.2f} | Loss Rs.{loss:.2f} ({loss_pct:.1f}%)",
            symbol=symbol,
            strike=strike,
            option_type=option_type,
            price=sl_price
        )
        self.send(alert)

    def send_phase_change(self, old_phase: str, new_phase: str) -> None:
        """Send phase change alert"""
        alert = Alert(
            alert_type=AlertType.PHASE_CHANGE,
            title=f"Phase: {new_phase.upper()}",
            message=f"Transitioned from {old_phase} to {new_phase}"
        )
        self.send(alert)

    def send_connection_status(self, connected: bool, message: str = "") -> None:
        """Send connection status alert"""
        if connected:
            alert = Alert(
                alert_type=AlertType.CONNECTION_RESTORED,
                title="Connection Restored",
                message=message or "WebSocket connection established"
            )
        else:
            alert = Alert(
                alert_type=AlertType.CONNECTION_LOST,
                title="Connection Lost",
                message=message or "WebSocket disconnected"
            )
        self.send(alert)

    def send_info(self, title: str, message: str) -> None:
        """Send informational alert"""
        alert = Alert(
            alert_type=AlertType.INFO,
            title=title,
            message=message
        )
        self.send(alert)

    def send_warning(self, title: str, message: str) -> None:
        """Send warning alert"""
        alert = Alert(
            alert_type=AlertType.WARNING,
            title=title,
            message=message
        )
        self.send(alert)

    def _send_desktop_notification(self, alert: Alert) -> None:
        """Send macOS desktop notification using osascript"""
        try:
            # Escape special characters for AppleScript
            title = alert.title.replace('"', '\\"').replace('\\', '\\\\')
            message = alert.message.replace('"', '\\"').replace('\\', '\\\\')

            # Build AppleScript command
            if self.sound_enabled and alert.alert_type in self.SOUNDS:
                sound = self.SOUNDS[alert.alert_type]
                script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
            else:
                script = f'display notification "{message}" with title "{title}"'

            result = subprocess.run(
                ['osascript', '-e', script],
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode != 0 and result.stderr:
                print(f"Notification error: {result.stderr}")

        except Exception as e:
            print(f"Failed to send desktop notification: {e}")

    def _log_to_console(self, alert: Alert) -> None:
        """Log alert to console with formatting"""
        timestamp = alert.timestamp.strftime('%H:%M:%S')

        if alert.alert_type == AlertType.ENTRY_SIGNAL:
            print(f"\n{'='*70}")
            print(f"[{timestamp}] SHORT SIGNAL: {alert.symbol} {alert.option_type}")
            print(f"   Strike: {int(alert.strike)} | Entry: Rs.{alert.price:.2f}")
            if alert.symbol and alert.price:
                # Calculate SL (assuming 50% SL)
                sl = alert.price * 1.5
                print(f"   Stop Loss: Rs.{sl:.2f}")
            print(f"{'='*70}\n")

        elif alert.alert_type == AlertType.STOP_LOSS_HIT:
            print(f"\n{'='*70}")
            print(f"[{timestamp}] STOP LOSS HIT: {alert.symbol} {alert.option_type}")
            print(f"   Strike: {int(alert.strike)} | Hit @ Rs.{alert.price:.2f}")
            print(f"{'='*70}\n")

        elif alert.alert_type == AlertType.PHASE_CHANGE:
            print(f"\n{'='*70}")
            print(f"[{timestamp}] PHASE CHANGE: {alert.title}")
            print(f"   {alert.message}")
            print(f"{'='*70}\n")

        elif alert.alert_type == AlertType.CONNECTION_LOST:
            print(f"\n[{timestamp}] CONNECTION LOST: {alert.message}")

        elif alert.alert_type == AlertType.CONNECTION_RESTORED:
            print(f"\n[{timestamp}] CONNECTION RESTORED: {alert.message}")

        elif alert.alert_type == AlertType.WARNING:
            print(f"\n[{timestamp}] WARNING: {alert.title} - {alert.message}")

        else:
            print(f"[{timestamp}] {alert.title}: {alert.message}")

    def _play_sound(self, alert_type: AlertType) -> None:
        """Play alert sound based on type"""
        if alert_type not in self.SOUNDS:
            return

        sound_name = self.SOUNDS[alert_type]

        try:
            subprocess.run(
                ['afplay', f'/System/Library/Sounds/{sound_name}.aiff'],
                check=False,
                capture_output=True
            )
        except Exception:
            pass  # Silently fail if sound doesn't play


# Convenience function to create notifier from config
def create_notifier_from_config(alerts_config) -> Notifier:
    """
    Create Notifier instance from AlertsConfig.

    Args:
        alerts_config: AlertsConfig dataclass

    Returns:
        Configured Notifier instance
    """
    return Notifier(
        desktop_notifications=alerts_config.desktop_notifications,
        sound_enabled=alerts_config.sound_enabled,
        console_logging=alerts_config.console_logging
    )
