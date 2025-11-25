#!/usr/bin/env python3
"""
Quick script to view current tracking status
"""
import json
import os
from datetime import datetime

def view_current_status():
    """Display current tracking status"""

    # Check for today's data file
    today = datetime.now().strftime('%Y%m%d')
    json_file = f'output/multi_timeframe_{today}.json'

    if not os.path.exists(json_file):
        print(f"❌ No data file found for today: {json_file}")
        print("\n📊 Available files:")
        if os.path.exists('output'):
            for f in os.listdir('output'):
                if f.startswith('multi_timeframe_') and f.endswith('.json'):
                    print(f"   - {f}")
        return

    # Load data
    with open(json_file, 'r') as f:
        data = json.load(f)

    if not data:
        print("⏳ No timeframes completed yet. Tracker is still running...")
        return

    print("="*70)
    print(f"NIFTY OPTION LOWS - {datetime.now().strftime('%B %d, %Y %H:%M:%S')}")
    print("="*70)
    print()

    for tf in data:
        timeframe = tf['timeframe']
        completed = tf.get('completed_at', 'In Progress')

        print(f"⏰ {timeframe} (Completed: {completed})")
        print("-" * 70)

        # CE Strike
        if tf.get('ce_strike'):
            ce = tf['ce_strike']
            distance = abs(ce['low'] - 50)
            icon = "🔔" if distance <= 15 else "📈"
            print(f"  {icon} CE Strike {ce['strike']}")
            print(f"     Low: ₹{ce['low']:.2f} | Current: ₹{ce['ltp']:.2f}")
            print(f"     Distance from ₹50: ₹{distance:.2f}")
            print(f"     Samples: {ce['samples']}")
        else:
            print("  📈 CE: No data yet")

        print()

        # PE Strike
        if tf.get('pe_strike'):
            pe = tf['pe_strike']
            distance = abs(pe['low'] - 50)
            icon = "🔔" if distance <= 15 else "📉"
            print(f"  {icon} PE Strike {pe['strike']}")
            print(f"     Low: ₹{pe['low']:.2f} | Current: ₹{pe['ltp']:.2f}")
            print(f"     Distance from ₹50: ₹{distance:.2f}")
            print(f"     Samples: {pe['samples']}")
        else:
            print("  📉 PE: No data yet")

        print()

    print("="*70)
    print(f"📊 View full report: open output/option_lows_compact.html")
    print(f"📁 Data file: {json_file}")
    print("="*70)

if __name__ == '__main__':
    view_current_status()
