"""
Strategy Store for Options Breakout Tracker V2

Persists strategies to JSON file for:
- Recovery after restart
- Historical reference
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading


class StrategyStore:
    """
    Persists strategies to a JSON file.

    Features:
    - Atomic writes (write to temp, then rename)
    - Auto-save support
    - Thread-safe operations
    """

    def __init__(
        self,
        output_dir: str = "output",
        filename: str = "strategies.json"
    ):
        """
        Initialize strategy store.

        Args:
            output_dir: Directory for output files
            filename: Name of the strategies file
        """
        self.output_dir = Path(output_dir)
        self.filename = filename
        self._filepath = self.output_dir / filename
        self._lock = threading.Lock()

        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)

    def save(self, strategies: List[Dict[str, Any]]) -> bool:
        """
        Save strategies to file.

        Args:
            strategies: List of serialized strategies

        Returns:
            True if successful
        """
        with self._lock:
            try:
                data = {
                    'saved_at': datetime.now().isoformat(),
                    'count': len(strategies),
                    'strategies': strategies
                }

                # Write to temp file first
                temp_path = self._filepath.with_suffix('.tmp')

                with open(temp_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

                # Atomic rename
                temp_path.replace(self._filepath)

                return True

            except Exception as e:
                print(f"[StrategyStore] Save error: {e}")
                return False

    def load(self) -> List[Dict[str, Any]]:
        """
        Load strategies from file.

        Returns:
            List of serialized strategies (empty if file not found)
        """
        if not self._filepath.exists():
            return []

        try:
            with open(self._filepath, 'r') as f:
                data = json.load(f)

            strategies = data.get('strategies', [])
            print(f"[StrategyStore] Loaded {len(strategies)} strategies from {self._filepath}")
            return strategies

        except (json.JSONDecodeError, IOError) as e:
            print(f"[StrategyStore] Load error: {e}")
            return []

    def get_filepath(self) -> Path:
        """Get the path to the strategies file."""
        return self._filepath

    def exists(self) -> bool:
        """Check if strategies file exists."""
        return self._filepath.exists()

    def get_last_save_time(self) -> Optional[str]:
        """Get the last save timestamp."""
        if not self._filepath.exists():
            return None

        try:
            with open(self._filepath, 'r') as f:
                data = json.load(f)
            return data.get('saved_at')
        except:
            return None
