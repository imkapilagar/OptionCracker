#!/usr/bin/env python3
"""
Quick demo of parallel tracking - simulates timeframes completing at different times
"""

import json
import os
import time
import subprocess
from datetime import datetime

def simulate_timeframe_completion():
    """Simulate timeframes completing one by one"""

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    all_results = [
        {
            "timeframe": "09:30-10:30",
            "start_time": "09:30",
            "end_time": "10:30",
            "ce_strike": {"strike": 26200, "low": 48.75, "ltp": 52.30, "distance": 1.25, "samples": 120},
            "pe_strike": {"strike": 26050, "low": 51.20, "ltp": 58.40, "distance": 1.20, "samples": 120}
        },
        {
            "timeframe": "10:00-11:00",
            "start_time": "10:00",
            "end_time": "11:00",
            "ce_strike": {"strike": 26150, "low": 47.90, "ltp": 49.60, "distance": 2.10, "samples": 120},
            "pe_strike": {"strike": 26100, "low": 52.40, "ltp": 61.75, "distance": 2.40, "samples": 120}
        },
        {
            "timeframe": "10:30-11:30",
            "start_time": "10:30",
            "end_time": "11:30",
            "ce_strike": {"strike": 26150, "low": 45.50, "ltp": 47.45, "distance": 4.50, "samples": 120},
            "pe_strike": {"strike": 26100, "low": 53.90, "ltp": 74.25, "distance": 3.90, "samples": 120}
        },
        {
            "timeframe": "11:00-12:00",
            "start_time": "11:00",
            "end_time": "12:00",
            "ce_strike": {"strike": 26100, "low": 46.20, "ltp": 50.85, "distance": 3.80, "samples": 120},
            "pe_strike": {"strike": 26050, "low": 48.60, "ltp": 67.30, "distance": 1.40, "samples": 120}
        }
    ]

    print("="*70)
    print("SIMULATING PARALLEL TRACKING")
    print("="*70)
    print("Watch the report update as each timeframe completes...")
    print()

    # Simulate completion at different times
    completed = []

    for i, result in enumerate(all_results, 1):
        print(f"⏱️  Simulating completion of timeframe {i}: {result['start_time']}-{result['end_time']}")
        completed.append(result)

        # Save JSON
        output_file = os.path.join(output_dir, f'multi_timeframe_{datetime.now().strftime("%Y%m%d")}.json')
        with open(output_file, 'w') as f:
            json.dump(completed, f, indent=2)

        # Generate HTML
        subprocess.run(['python', 'generate_compact_report.py'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

        print(f"✅ Report updated with {len(completed)}/4 timeframes")
        print(f"   View at: index.html")
        print()

        if i < len(all_results):
            print("Waiting 3 seconds before next completion...")
            time.sleep(3)

    print("="*70)
    print("✅ DEMO COMPLETE - All 4 timeframes now showing in report")
    print("="*70)

if __name__ == '__main__':
    simulate_timeframe_completion()
