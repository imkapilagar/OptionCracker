#!/usr/bin/env python3
"""
Interactive demo showing EXACTLY when notifications trigger
"""

import time

def demo_trigger_logic():
    """Step-by-step demonstration of trigger logic"""

    print("="*70)
    print("NOTIFICATION TRIGGER - STEP BY STEP DEMO")
    print("="*70)
    print("\nTracking Strike: 26200 CE")
    print("Thread: 2 | Timeframe: 10:00-11:00")
    print("-"*70)

    # Simulated LTP values over time
    samples = [
        {'time': '10:00:00', 'ltp': 55.30, 'stored_low': None},
        {'time': '10:00:30', 'ltp': 54.80, 'stored_low': 55.30},
        {'time': '10:01:00', 'ltp': 55.10, 'stored_low': 54.80},
        {'time': '10:01:30', 'ltp': 53.20, 'stored_low': 54.80},
        {'time': '10:02:00', 'ltp': 53.50, 'stored_low': 53.20},
        {'time': '10:02:30', 'ltp': 52.80, 'stored_low': 53.20},
        {'time': '10:03:00', 'ltp': 48.75, 'stored_low': 52.80},
        {'time': '10:03:30', 'ltp': 49.20, 'stored_low': 48.75},
        {'time': '10:04:00', 'ltp': 47.50, 'stored_low': 48.75},
    ]

    for i, sample in enumerate(samples, 1):
        print(f"\n{'#'*70}")
        print(f"Sample #{i} at {sample['time']}")
        print(f"{'#'*70}")

        current_ltp = sample['ltp']
        stored_low = sample['stored_low']

        print(f"\n1️⃣ API returns: LTP = ₹{current_ltp:.2f}")

        if stored_low is None:
            print(f"2️⃣ First time seeing this strike")
            print(f"3️⃣ Store low = ₹{current_ltp:.2f}")
            print(f"4️⃣ Result: ❌ NO NOTIFICATION (initial sample)")
        else:
            print(f"2️⃣ Stored low = ₹{stored_low:.2f}")
            print(f"3️⃣ Compare: LTP < Stored Low?")
            print(f"   {current_ltp:.2f} < {stored_low:.2f} ?")

            if current_ltp < stored_low:
                drop = stored_low - current_ltp
                drop_percent = (drop / stored_low) * 100

                print(f"   ✅ YES! {current_ltp:.2f} is less than {stored_low:.2f}")
                print(f"\n4️⃣ Calculate drop:")
                print(f"   Drop: ₹{drop:.2f}")
                print(f"   Drop %: {drop_percent:.2f}%")

                is_near_50 = abs(current_ltp - 50) <= 15
                distance = abs(current_ltp - 50)

                print(f"\n5️⃣ Check if near ₹50:")
                print(f"   Distance from ₹50: ₹{distance:.2f}")
                print(f"   Within ₹15? {is_near_50}")

                print(f"\n6️⃣ Update stored low:")
                print(f"   Old: ₹{stored_low:.2f} → New: ₹{current_ltp:.2f}")

                print(f"\n7️⃣ 🔔 TRIGGER NOTIFICATION:")
                print("-"*70)

                if is_near_50:
                    print("============================================================")
                    print("🔔 [Thread 2 | 10:00-11:00] NEW LOW!")
                    print(f"   Strike: 26200 CE")
                    print(f"   Old Low: ₹{stored_low:.2f} → New Low: ₹{current_ltp:.2f} (↓{drop_percent:.2f}%)")
                    print(f"   Time: {sample['time']}")
                    print(f"   ⭐ NEAR ₹50 TARGET! Distance: ₹{distance:.2f}")
                    print("============================================================")
                else:
                    print("📉 [Thread 2 | 10:00-11:00] NEW LOW!")
                    print(f"   Strike: 26200 CE")
                    print(f"   Old Low: ₹{stored_low:.2f} → New Low: ₹{current_ltp:.2f} (↓{drop_percent:.2f}%)")
                    print(f"   Time: {sample['time']}")

                print("-"*70)
            else:
                print(f"   ❌ NO! {current_ltp:.2f} is NOT less than {stored_low:.2f}")
                print(f"\n4️⃣ Result: ❌ NO NOTIFICATION")
                print(f"   (LTP is higher or equal to stored low)")

        time.sleep(2)

    print(f"\n{'='*70}")
    print("DEMO COMPLETE")
    print("="*70)
    print("\n📊 Summary:")
    print(f"   Total samples: {len(samples)}")
    print(f"   Notifications: 5 (at samples #2, #4, #6, #7, #9)")
    print(f"   Special alerts (near ₹50): 2 (at samples #7, #9)")
    print()

if __name__ == '__main__':
    demo_trigger_logic()
