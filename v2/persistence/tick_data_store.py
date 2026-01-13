"""
Tick Data Store for Options Breakout Tracker V2

Saves all incoming tick data to a file for historical analysis.
This allows replaying the day's data for backtesting and analysis.
"""
import json
import gzip
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading


class TickDataStore:
    """
    Stores raw tick data for later analysis.

    Features:
    - Saves ticks to JSON file (optionally gzipped)
    - Buffered writes for performance
    - Thread-safe operations
    - Can replay stored ticks
    """

    def __init__(
        self,
        output_dir: str = "output",
        file_prefix: str = "tick_data",
        buffer_size: int = 100,
        compress: bool = False
    ):
        """
        Initialize tick data store.

        Args:
            output_dir: Directory for output files
            file_prefix: Prefix for tick data files
            buffer_size: Number of ticks to buffer before flushing
            compress: Whether to gzip compress the output
        """
        self.output_dir = Path(output_dir)
        self.file_prefix = file_prefix
        self.buffer_size = buffer_size
        self.compress = compress

        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._tick_count = 0
        self._file_handle = None
        self._filepath: Optional[Path] = None

        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)

    def start(self, date: Optional[datetime] = None) -> Path:
        """
        Start recording ticks for the day.

        Args:
            date: Date for the file (defaults to today)

        Returns:
            Path to the tick data file
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime('%Y%m%d')
        ext = ".json.gz" if self.compress else ".json"
        self._filepath = self.output_dir / f"{self.file_prefix}_{date_str}{ext}"

        # Open file for writing
        if self.compress:
            self._file_handle = gzip.open(self._filepath, 'wt', encoding='utf-8')
        else:
            self._file_handle = open(self._filepath, 'w', encoding='utf-8')

        # Write header
        header = {
            "type": "header",
            "date": date_str,
            "start_time": datetime.now().isoformat(),
            "version": "2.0"
        }
        self._file_handle.write(json.dumps(header) + "\n")

        print(f"Tick data recording started: {self._filepath}")
        return self._filepath

    def record_tick(
        self,
        instrument_key: str,
        ltp: float,
        timestamp: datetime,
        volume: Optional[int] = None,
        oi: Optional[int] = None
    ) -> None:
        """
        Record a single tick.

        Args:
            instrument_key: Instrument key
            ltp: Last traded price
            timestamp: Tick timestamp
            volume: Optional volume
            oi: Optional open interest
        """
        tick = {
            "t": timestamp.strftime("%H:%M:%S.%f")[:12],  # HH:MM:SS.mmm
            "i": instrument_key,
            "p": ltp
        }

        # Only add optional fields if present
        if volume is not None:
            tick["v"] = volume
        if oi is not None:
            tick["oi"] = oi

        with self._lock:
            self._buffer.append(tick)
            self._tick_count += 1

            # Flush buffer if full
            if len(self._buffer) >= self.buffer_size:
                self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffer to file (must be called with lock held)."""
        if not self._file_handle or not self._buffer:
            return

        for tick in self._buffer:
            self._file_handle.write(json.dumps(tick) + "\n")

        self._file_handle.flush()
        self._buffer.clear()

    def stop(self) -> Dict[str, Any]:
        """
        Stop recording and close file.

        Returns:
            Summary of recorded data
        """
        with self._lock:
            # Flush remaining buffer
            self._flush_buffer()

            # Write footer
            if self._file_handle:
                footer = {
                    "type": "footer",
                    "end_time": datetime.now().isoformat(),
                    "total_ticks": self._tick_count
                }
                self._file_handle.write(json.dumps(footer) + "\n")
                self._file_handle.close()
                self._file_handle = None

        summary = {
            "filepath": str(self._filepath) if self._filepath else None,
            "total_ticks": self._tick_count
        }

        print(f"Tick data recording stopped. Total ticks: {self._tick_count}")
        return summary

    def get_tick_count(self) -> int:
        """Get total number of recorded ticks."""
        return self._tick_count

    def get_data_range(self) -> Dict[str, Any]:
        """Get the time range of data in the current file."""
        if not self._filepath or not self._filepath.exists():
            return {'start_time': None, 'end_time': None, 'tick_count': 0}

        try:
            start_time = None
            end_time = None

            with open(self._filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get("type") == "header":
                            continue
                        if data.get("type") == "footer":
                            continue

                        tick_time = data.get('t', '')
                        if tick_time:
                            # Format: HH:MM:SS.mmm - extract HH:MM
                            time_short = tick_time[:5]
                            if start_time is None:
                                start_time = time_short
                            end_time = time_short
                    except json.JSONDecodeError:
                        continue

            return {
                'start_time': start_time,
                'end_time': end_time,
                'tick_count': self._tick_count
            }
        except Exception as e:
            print(f"[TickDataStore] Error getting data range: {e}")
            return {'start_time': None, 'end_time': None, 'tick_count': self._tick_count}

    @staticmethod
    def load_ticks(filepath: str) -> List[Dict[str, Any]]:
        """
        Load recorded ticks from file.

        Args:
            filepath: Path to tick data file

        Returns:
            List of tick dictionaries
        """
        ticks = []
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Tick file not found: {filepath}")

        # Determine if compressed
        opener = gzip.open if path.suffix == '.gz' else open

        with opener(path, 'rt', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # Skip header and footer
                    if data.get("type") in ["header", "footer"]:
                        continue
                    ticks.append(data)
                except json.JSONDecodeError:
                    continue

        return ticks

    @staticmethod
    def get_file_info(filepath: str) -> Dict[str, Any]:
        """
        Get information about a tick data file.

        Args:
            filepath: Path to tick data file

        Returns:
            Dictionary with file info
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Tick file not found: {filepath}")

        info = {
            "filepath": str(path),
            "size_bytes": path.stat().st_size,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2)
        }

        # Read header and footer
        opener = gzip.open if path.suffix == '.gz' else open

        with opener(path, 'rt', encoding='utf-8') as f:
            # Read header (first line)
            first_line = f.readline()
            try:
                header = json.loads(first_line)
                if header.get("type") == "header":
                    info["date"] = header.get("date")
                    info["start_time"] = header.get("start_time")
            except json.JSONDecodeError:
                pass

            # Read footer (last line) - need to read all
            last_line = None
            for line in f:
                last_line = line

            if last_line:
                try:
                    footer = json.loads(last_line)
                    if footer.get("type") == "footer":
                        info["end_time"] = footer.get("end_time")
                        info["total_ticks"] = footer.get("total_ticks")
                except json.JSONDecodeError:
                    pass

        return info

    @staticmethod
    def get_strike_lows_for_range(
        filepath: str,
        start_time: str,
        end_time: str,
        instrument_keys: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get the lowest prices for each instrument within a time range.

        Args:
            filepath: Path to tick data file
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            instrument_keys: Optional list of instruments to filter (None = all)

        Returns:
            Dict mapping instrument_key to {low, ltp, tick_count, first_tick, last_tick}
        """
        path = Path(filepath)

        if not path.exists():
            print(f"[TickDataStore] File not found: {filepath}")
            return {}

        # Parse times
        start_parts = start_time.split(':')
        end_parts = end_time.split(':')
        start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
        end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

        # Results dict
        results: Dict[str, Dict[str, Any]] = {}

        # Determine if compressed
        opener = gzip.open if path.suffix == '.gz' else open

        with opener(path, 'rt', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())

                    # Skip header and footer
                    if data.get("type") in ["header", "footer"]:
                        continue

                    # Get tick time
                    tick_time = data.get('t', '')  # Format: HH:MM:SS.mmm
                    if not tick_time:
                        continue

                    # Parse tick time to minutes
                    time_parts = tick_time.split(':')
                    tick_minutes = int(time_parts[0]) * 60 + int(time_parts[1])

                    # Check if in range
                    if tick_minutes < start_minutes or tick_minutes >= end_minutes:
                        continue

                    # Get instrument and price
                    inst_key = data.get('i', '')
                    price = data.get('p', 0)

                    if not inst_key or price <= 0:
                        continue

                    # Filter by instrument if specified
                    if instrument_keys and inst_key not in instrument_keys:
                        continue

                    # Update results
                    if inst_key not in results:
                        results[inst_key] = {
                            'low': price,
                            'ltp': price,
                            'tick_count': 1,
                            'first_tick': tick_time,
                            'last_tick': tick_time
                        }
                    else:
                        r = results[inst_key]
                        if price < r['low']:
                            r['low'] = price
                        r['ltp'] = price
                        r['tick_count'] += 1
                        r['last_tick'] = tick_time

                except json.JSONDecodeError:
                    continue

        print(f"[TickDataStore] Loaded historical data for {len(results)} instruments ({start_time}-{end_time})")
        return results
