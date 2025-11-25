#!/usr/bin/env python3
"""
Continuously fetch data and update dashboard every 30 seconds
"""
import time
import subprocess
from datetime import datetime

def run_live_dashboard_with_refresh():
    """Fetch data and update dashboard in a loop"""
    print("="*70)
    print("🚀 Starting Live Dashboard with Data Refresh")
    print("="*70)
    print("Dashboard updates every 30 seconds with fresh API data")
    print("Open: live_dashboard.html in your browser")
    print("Press Ctrl+C to stop")
    print("="*70)
    print()

    try:
        while True:
            # Fetch fresh data
            print(f"🔄 {datetime.now().strftime('%H:%M:%S')} - Fetching fresh data...", flush=True)
            subprocess.run(['python3', 'refresh_current_data.py'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

            # Generate dashboard
            subprocess.run(['python3', 'generate_live_dashboard.py'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Dashboard updated", flush=True)
            print()

            # Wait 30 seconds
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n⏹️  Dashboard updater stopped")

if __name__ == '__main__':
    run_live_dashboard_with_refresh()
