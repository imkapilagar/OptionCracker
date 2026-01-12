"""
State Manager for Options Breakout Tracker V2

Handles:
- State persistence to JSON files
- Session resume capability
- Historical data archival
- Atomic file writes
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading


class StateManager:
    """
    Manages state persistence and recovery.

    Features:
    - Auto-save with configurable interval
    - Crash recovery
    - Session resume capability
    - Historical data archival
    - Thread-safe operations
    """

    def __init__(
        self,
        output_dir: str = "output",
        file_prefix: str = "breakout_v2"
    ):
        """
        Initialize state manager.

        Args:
            output_dir: Directory for output files
            file_prefix: Prefix for state files
        """
        self.output_dir = Path(output_dir)
        self.file_prefix = file_prefix
        self._lock = threading.Lock()

        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)

    def get_state_file_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get path for state file for given date.

        Args:
            date: Date for the state file (defaults to today)

        Returns:
            Path to the state file
        """
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y%m%d')
        return self.output_dir / f"{self.file_prefix}_{date_str}.json"

    def save_state(self, state: Dict[str, Any]) -> bool:
        """
        Save current state to file (thread-safe).

        Uses atomic write (write to temp, then rename) for safety.

        Args:
            state: State dictionary to save

        Returns:
            True if save was successful
        """
        with self._lock:
            try:
                # Add metadata
                state_with_meta = state.copy()
                state_with_meta['_metadata'] = {
                    'last_save': datetime.now().isoformat(),
                    'version': '2.0',
                    'file_prefix': self.file_prefix
                }

                filepath = self.get_state_file_path()

                # Write to temp file first, then rename (atomic)
                temp_path = filepath.with_suffix('.tmp')

                with open(temp_path, 'w') as f:
                    json.dump(state_with_meta, f, indent=2, default=str)

                # Atomic rename
                temp_path.replace(filepath)

                return True

            except Exception as e:
                print(f"Error saving state: {e}")
                return False

    def load_state(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Load state from file.

        Args:
            date: Date to load state for (defaults to today)

        Returns:
            State dictionary or None if not found/error
        """
        filepath = self.get_state_file_path(date)

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading state: {e}")
            return None

    def can_resume(self) -> bool:
        """
        Check if today's session can be resumed.

        A session can be resumed if:
        - State file exists for today
        - Phase is not 'completed'

        Returns:
            True if session can be resumed
        """
        state = self.load_state()
        if state is None:
            return False

        # Check if session is from today
        metadata = state.get('_metadata', {})
        last_save = metadata.get('last_save')

        if not last_save:
            return False

        try:
            last_save_dt = datetime.fromisoformat(last_save)
            if last_save_dt.date() != datetime.now().date():
                return False
        except ValueError:
            return False

        # Check if not completed
        phase = state.get('phase', '')
        return phase not in ['completed']

    def get_resume_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about resumable session.

        Returns:
            Dict with resume info or None
        """
        if not self.can_resume():
            return None

        state = self.load_state()
        if state is None:
            return None

        metadata = state.get('_metadata', {})

        return {
            'last_save': metadata.get('last_save'),
            'phase': state.get('phase'),
            'tick_count': state.get('tick_count', 0),
            'positions_count': len(state.get('positions', [])),
            'symbols': list(state.get('symbols', {}).keys())
        }

    def archive_old_sessions(self) -> int:
        """
        Archive sessions from previous days.

        Renames files from prefix_YYYYMMDD.json to prefix_YYYYMMDD_archived.json

        Returns:
            Number of files archived
        """
        today = datetime.now().strftime('%Y%m%d')
        archived_count = 0

        for file in self.output_dir.glob(f"{self.file_prefix}_*.json"):
            # Skip already archived files
            if '_archived' in file.stem:
                continue

            # Extract date from filename
            # Format: prefix_YYYYMMDD.json
            try:
                file_date = file.stem.replace(f"{self.file_prefix}_", "")
                if file_date != today:
                    new_name = file.with_stem(f"{file.stem}_archived")
                    file.rename(new_name)
                    print(f"Archived: {file.name} -> {new_name.name}")
                    archived_count += 1
            except Exception as e:
                print(f"Error archiving {file.name}: {e}")

        return archived_count

    def list_sessions(self, include_archived: bool = False) -> list:
        """
        List all available sessions.

        Args:
            include_archived: Include archived sessions

        Returns:
            List of session info dictionaries
        """
        sessions = []

        pattern = f"{self.file_prefix}_*.json"
        for file in sorted(self.output_dir.glob(pattern), reverse=True):
            is_archived = '_archived' in file.stem

            if not include_archived and is_archived:
                continue

            try:
                with open(file, 'r') as f:
                    data = json.load(f)

                metadata = data.get('_metadata', {})

                sessions.append({
                    'filename': file.name,
                    'path': str(file),
                    'date': metadata.get('last_save', ''),
                    'phase': data.get('phase', ''),
                    'is_archived': is_archived,
                    'tick_count': data.get('tick_count', 0),
                    'positions_count': len(data.get('positions', []))
                })
            except Exception:
                continue

        return sessions

    def delete_old_archives(self, keep_days: int = 30) -> int:
        """
        Delete archived sessions older than specified days.

        Args:
            keep_days: Number of days to keep

        Returns:
            Number of files deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        for file in self.output_dir.glob(f"{self.file_prefix}_*_archived.json"):
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < cutoff_date:
                    file.unlink()
                    print(f"Deleted old archive: {file.name}")
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting {file.name}: {e}")

        return deleted_count

    def export_session(self, date: Optional[datetime] = None, format: str = "json") -> Optional[str]:
        """
        Export session data.

        Args:
            date: Session date (defaults to today)
            format: Export format (currently only 'json')

        Returns:
            Path to exported file or None
        """
        state = self.load_state(date)
        if state is None:
            return None

        if format == "json":
            date_str = (date or datetime.now()).strftime('%Y%m%d')
            export_path = self.output_dir / f"{self.file_prefix}_{date_str}_export.json"

            with open(export_path, 'w') as f:
                json.dump(state, f, indent=2, default=str)

            return str(export_path)

        return None
