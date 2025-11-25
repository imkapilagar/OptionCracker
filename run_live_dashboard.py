#!/usr/bin/env python3
"""
Continuously update live dashboard every 5 seconds
"""
import time
import subprocess
from datetime import datetime

def run_live_dashboard():
    """Run dashboard generator in a loop"""
    print("="*70)
    print("🚀 Starting Live Dashboard Auto-Updater")
    print("="*70)
    print("The dashboard will auto-refresh every 5 seconds")
    print("Open: live_dashboard.html in your browser")
    print("Press Ctrl+C to stop")
    print("="*70)
    print()

    try:
        while True:
            # Generate dashboard
            subprocess.run(['python3', 'generate_live_dashboard.py'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

            print(f"✅ Dashboard updated at {datetime.now().strftime('%H:%M:%S')}", flush=True)

            # Wait 5 seconds
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n⏹️  Dashboard updater stopped")

if __name__ == '__main__':
    run_live_dashboard()
