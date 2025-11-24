#!/usr/bin/env python3
"""
Test/Demo of notification system for low breaks
"""

import time
from datetime import datetime

def simulate_low_breaks():
    """Simulate new lows being detected"""

    print("="*70)
    print("NOTIFICATION SYSTEM DEMO")
    print("="*70)
    print("Simulating low breaks during tracking...")
    print()
    time.sleep(1)

    # Simulate various scenarios
    scenarios = [
        {
            'thread_id': 1,
            'timeframe': '09:30-10:30',
            'strike': 26150,
            'type': 'CE',
            'old_low': 58.30,
            'new_low': 55.20,
            'near_50': False
        },
        {
            'thread_id': 2,
            'timeframe': '10:00-11:00',
            'strike': 26200,
            'type': 'CE',
            'old_low': 52.40,
            'new_low': 48.75,
            'near_50': True
        },
        {
            'thread_id': 1,
            'timeframe': '09:30-10:30',
            'strike': 26100,
            'type': 'PE',
            'old_low': 55.60,
            'new_low': 51.20,
            'near_50': True
        },
        {
            'thread_id': 3,
            'timeframe': '10:30-11:30',
            'strike': 26150,
            'type': 'CE',
            'old_low': 48.75,
            'new_low': 45.50,
            'near_50': True
        },
        {
            'thread_id': 2,
            'timeframe': '10:00-11:00',
            'strike': 26300,
            'type': 'CE',
            'old_low': 25.60,
            'new_low': 23.80,
            'near_50': False
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"Sample #{i} - Checking strikes...")
        time.sleep(1)

        thread_id = scenario['thread_id']
        timeframe = scenario['timeframe']
        strike = scenario['strike']
        opt_type = scenario['type']
        old_low = scenario['old_low']
        new_low = scenario['new_low']
        is_near_50 = scenario['near_50']

        drop_percent = ((old_low - new_low) / old_low) * 100
        notification_icon = "🔔" if is_near_50 else "📉"

        if is_near_50:
            print(f"\n{'='*60}")
        print(f"{notification_icon} [Thread {thread_id} | {timeframe}] NEW LOW!")
        print(f"   Strike: {strike} {opt_type}")
        print(f"   Old Low: ₹{old_low:.2f} → New Low: ₹{new_low:.2f} (↓{drop_percent:.2f}%)")
        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
        if is_near_50:
            print(f"   ⭐ NEAR ₹50 TARGET! Distance: ₹{abs(new_low - 50):.2f}")
            print(f"{'='*60}\n")
        else:
            print("")

        time.sleep(2)

    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nNotification Types:")
    print("  📉 Regular low break (any strike)")
    print("  🔔 Special alert (strikes near ₹50)")
    print("  ⭐ Highlighted when distance from ₹50 is shown")
    print()

if __name__ == '__main__':
    simulate_low_breaks()
