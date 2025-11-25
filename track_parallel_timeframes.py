#!/usr/bin/env python3
"""
Parallel Multi-Timeframe Option Chain Tracker
Tracks 4 overlapping 60-minute windows simultaneously:
- 09:30-10:30
- 10:00-11:00
- 10:30-11:30
- 11:00-12:00
"""

import requests
from datetime import datetime, time, timedelta
import time as time_module
import pandas as pd
import json
import os
import threading
import subprocess
from collections import defaultdict

# Read credentials
with open('upstox_credentials.txt', 'r') as f:
    lines = f.readlines()
    access_token = lines[1].split('=')[1].strip()

# Global lock for thread-safe operations
results_lock = threading.Lock()
completed_results = []

def get_nearest_weekly_expiry():
    """Get the nearest Thursday expiry date"""
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # 3 = Thursday
    if days_ahead <= 0:
        days_ahead += 7
    nearest_expiry = today + timedelta(days=days_ahead)
    return nearest_expiry.strftime('%Y-%m-%d')

def fetch_option_chain(access_token, symbol='NIFTY'):
    """Fetch live option chain data"""
    expiry_date = get_nearest_weekly_expiry()

    url = 'https://api.upstox.com/v2/option/chain'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    instrument_key = 'NSE_INDEX|Nifty 50' if symbol == 'NIFTY' else 'NSE_INDEX|Nifty Bank'

    params = {
        'instrument_key': instrument_key,
        'expiry_date': expiry_date
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            return data.get('data', [])
        return []
    except Exception as e:
        # Silently fail to avoid cluttering output with errors from parallel threads
        return []

def track_timeframe_parallel(thread_id, start_time_str, end_time_str, symbol='NIFTY', interval_seconds=30):
    """
    Track option lows for a specific 60-minute timeframe (thread-safe)
    """
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strptime(end_time_str, '%H:%M').time()

    print(f"[Thread {thread_id}] Timeframe {start_time_str}-{end_time_str} initialized", flush=True)

    # Wait until start time
    while datetime.now().time() < start_time:
        time_module.sleep(10)

    print(f"[Thread {thread_id}] 🚀 Starting tracking for {start_time_str}-{end_time_str} at {datetime.now().strftime('%H:%M:%S')}", flush=True)

    lows_tracker = {}
    sample_count = 0

    # Track until end time
    while datetime.now().time() < end_time:
        sample_count += 1

        # Fetch data
        option_data = fetch_option_chain(access_token, symbol)

        if not option_data:
            time_module.sleep(interval_seconds)
            continue

        # Process strikes
        for strike_data in option_data:
            strike = strike_data.get('strike_price')

            # Process CE and PE
            for option_type in ['call_options', 'put_options']:
                opt_type = 'CE' if option_type == 'call_options' else 'PE'
                market_data = strike_data.get(option_type, {}).get('market_data', {})

                if not market_data:
                    continue

                ltp = market_data.get('ltp', 0)
                instrument_key = strike_data.get(option_type, {}).get('instrument_key', '')

                if ltp == 0 or not instrument_key:
                    continue

                key = f"{symbol}_{strike}_{opt_type}"

                if key not in lows_tracker:
                    lows_tracker[key] = {
                        'symbol': symbol,
                        'strike': strike,
                        'option_type': opt_type,
                        'instrument_key': instrument_key,
                        'low': ltp,
                        'current_ltp': ltp,
                        'first_ltp': ltp,
                        'samples': 1
                    }
                else:
                    lows_tracker[key]['samples'] += 1
                    old_low = lows_tracker[key]['low']
                    lows_tracker[key]['current_ltp'] = ltp
                    if ltp < old_low:
                        # NEW LOW DETECTED!
                        lows_tracker[key]['low'] = ltp
                        drop_percent = ((old_low - ltp) / old_low) * 100

                        # Check if this strike is near Rs 50 (within Rs 15)
                        is_near_50 = abs(ltp - 50) <= 15
                        notification_icon = "🔔" if is_near_50 else "📉"

                        # Print notification (highlight if near 50)
                        if is_near_50:
                            print(f"\n{'='*60}", flush=True)
                        print(f"{notification_icon} [Thread {thread_id} | {start_time_str}-{end_time_str}] NEW LOW!", flush=True)
                        print(f"   Strike: {strike} {opt_type}", flush=True)
                        print(f"   Old Low: ₹{old_low:.2f} → New Low: ₹{ltp:.2f} (↓{drop_percent:.2f}%)", flush=True)
                        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}", flush=True)
                        if is_near_50:
                            print(f"   ⭐ NEAR ₹50 TARGET! Distance: ₹{abs(ltp - 50):.2f}", flush=True)
                            print(f"{'='*60}\n", flush=True)
                        else:
                            print("", flush=True)

        # Sleep until next sample
        time_module.sleep(interval_seconds)

    print(f"[Thread {thread_id}] ✅ Completed {start_time_str}-{end_time_str} at {datetime.now().strftime('%H:%M:%S')} ({sample_count} samples)", flush=True)

    # Find strikes nearest to Rs 50
    df = pd.DataFrame.from_dict(lows_tracker, orient='index')

    if df.empty:
        return

    # Filter by option type
    ce_df = df[df['option_type'] == 'CE'].copy()
    pe_df = df[df['option_type'] == 'PE'].copy()

    # Find nearest to 50
    ce_df['distance_from_50'] = abs(ce_df['low'] - 50)
    pe_df['distance_from_50'] = abs(pe_df['low'] - 50)

    result = {
        'timeframe': f"{start_time_str}-{end_time_str}",
        'start_time': start_time_str,
        'end_time': end_time_str,
        'ce_strike': None,
        'pe_strike': None,
        'completed_at': datetime.now().strftime('%H:%M:%S')
    }

    if not ce_df.empty:
        nearest_ce = ce_df.nsmallest(1, 'distance_from_50').iloc[0]
        result['ce_strike'] = {
            'strike': int(nearest_ce['strike']),
            'low': float(nearest_ce['low']),
            'ltp': float(nearest_ce['current_ltp']),
            'distance': float(nearest_ce['distance_from_50']),
            'samples': int(nearest_ce['samples'])
        }
        print(f"[Thread {thread_id}] 📈 CE: Strike {result['ce_strike']['strike']} | Low ₹{result['ce_strike']['low']}", flush=True)

    if not pe_df.empty:
        nearest_pe = pe_df.nsmallest(1, 'distance_from_50').iloc[0]
        result['pe_strike'] = {
            'strike': int(nearest_pe['strike']),
            'low': float(nearest_pe['low']),
            'ltp': float(nearest_pe['current_ltp']),
            'distance': float(nearest_pe['distance_from_50']),
            'samples': int(nearest_pe['samples'])
        }
        print(f"[Thread {thread_id}] 📉 PE: Strike {result['pe_strike']['strike']} | Low ₹{result['pe_strike']['low']}", flush=True)

    # Thread-safe: Add result and generate HTML
    with results_lock:
        completed_results.append(result)
        # Sort results by start time
        sorted_results = sorted(completed_results, key=lambda x: x['start_time'])

        # Save to JSON
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f'multi_timeframe_{datetime.now().strftime("%Y%m%d")}.json')
        with open(output_file, 'w') as f:
            json.dump(sorted_results, f, indent=2)

        # Generate HTML report
        print(f"[Thread {thread_id}] 🌐 Generating HTML report...", flush=True)
        subprocess.run(['python', 'generate_compact_report.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[Thread {thread_id}] ✅ Report updated: index.html", flush=True)

def main():
    """Main function to track all 4 timeframes in parallel"""

    # Define timeframes with 60-minute lookback
    timeframes = [
        ('09:30', '10:30'),  # Thread 1
        ('10:00', '11:00'),  # Thread 2
        ('10:30', '11:30'),  # Thread 3
        ('11:00', '12:00'),  # Thread 4
    ]

    print("="*70)
    print("NIFTY OPTION CHAIN - PARALLEL MULTI-TIMEFRAME TRACKER")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Tracking 4 overlapping timeframes simultaneously")
    print(f"Start script anytime - it will wait for market hours")
    print("="*70)
    print()

    # Create threads for each timeframe
    threads = []
    for i, (start_time, end_time) in enumerate(timeframes, 1):
        thread = threading.Thread(
            target=track_timeframe_parallel,
            args=(i, start_time, end_time, 'NIFTY', 30),
            daemon=False
        )
        threads.append(thread)
        thread.start()

    print(f"✅ All {len(threads)} tracking threads started")
    print(f"📊 Reports will be generated as each timeframe completes")
    print(f"🌐 View live updates at: index.html")
    print()

    # Wait for all threads to complete
    for i, thread in enumerate(threads, 1):
        thread.join()
        print(f"Thread {i} finished", flush=True)

    print()
    print("="*70)
    print("✅ ALL TIMEFRAMES COMPLETED!")
    print(f"📊 Final report: index.html")
    print(f"📁 Data saved: output/multi_timeframe_{datetime.now().strftime('%Y%m%d')}.json")
    print("="*70)

if __name__ == '__main__':
    main()
