#!/usr/bin/env python3
"""
Track 4 parallel timeframes and update dashboard with alerts
- Thread 1: 09:30-10:30
- Thread 2: 10:00-11:00
- Thread 3: 10:30-11:30
- Thread 4: 11:00-12:00
"""
import requests
import json
from datetime import datetime
import time
import subprocess
import os

# Read credentials
with open('upstox_credentials.txt', 'r') as f:
    lines = f.readlines()
    access_token = lines[1].split('=')[1].strip()

# Define all 4 timeframes
TIMEFRAMES = [
    {'id': 'thread_1', 'start': (9, 30), 'end': (10, 30), 'label': '09:30-10:30'},
    {'id': 'thread_2', 'start': (10, 0), 'end': (11, 0), 'label': '10:00-11:00'},
    {'id': 'thread_3', 'start': (10, 30), 'end': (11, 30), 'label': '10:30-11:30'},
    {'id': 'thread_4', 'start': (11, 0), 'end': (12, 0), 'label': '11:00-12:00'},
]

def fetch_timeframe_low(instrument_key, start_time, end_time):
    """Fetch low from specific timeframe using intraday candles"""
    url = f'https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute'
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            candles = data.get('data', {}).get('candles', [])

            timeframe_lows = []
            for candle in candles:
                if len(candle) > 3:
                    timestamp_str = candle[0]
                    time_part = timestamp_str.split('T')[1].split('+')[0]
                    hour = int(time_part.split(':')[0])
                    minute = int(time_part.split(':')[1])

                    # Check if within timeframe
                    start_h, start_m = start_time
                    end_h, end_m = end_time

                    current_minutes = hour * 60 + minute
                    start_minutes = start_h * 60 + start_m
                    end_minutes = end_h * 60 + end_m

                    if start_minutes <= current_minutes < end_minutes:
                        timeframe_lows.append(candle[3])

            if timeframe_lows:
                return min(timeframe_lows)
    except:
        pass
    return None

def check_current_timeframe():
    """Check which timeframe is currently active"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_minutes = current_hour * 60 + current_minute

    active_threads = []
    for tf in TIMEFRAMES:
        start_minutes = tf['start'][0] * 60 + tf['start'][1]
        end_minutes = tf['end'][0] * 60 + tf['end'][1]

        if start_minutes <= current_minutes < end_minutes:
            active_threads.append(tf['id'])

    return active_threads

def update_all_timeframes():
    """Fetch and update data for all timeframes"""
    # Fetch option chain
    url = 'https://api.upstox.com/v2/option/chain'
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    params = {'instrument_key': 'NSE_INDEX|Nifty 50', 'expiry_date': '2025-11-25'}

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching option chain for all timeframes...")

    chain_data = requests.get(url, headers=headers, params=params, timeout=10).json()
    key_strikes = [25900, 25950, 26000, 26050, 26100]

    active_threads = check_current_timeframe()
    all_data = {}

    for tf in TIMEFRAMES:
        print(f"  Processing {tf['label']}...")

        results = {'ce': [], 'pe': []}

        for strike_data in chain_data.get('data', []):
            strike = strike_data.get('strike_price')
            if strike not in key_strikes:
                continue

            # CE
            ce_option = strike_data.get('call_options', {})
            ce_inst_key = ce_option.get('instrument_key')
            ce_ltp = ce_option.get('market_data', {}).get('ltp', 0)

            if ce_inst_key and ce_ltp > 0:
                timeframe_low = fetch_timeframe_low(ce_inst_key, tf['start'], tf['end'])
                if timeframe_low:
                    distance = abs(timeframe_low - 50)
                    results['ce'].append({
                        'strike': int(strike),
                        'timeframe_low': timeframe_low,
                        'ltp': ce_ltp,
                        'distance': distance
                    })

            # PE
            pe_option = strike_data.get('put_options', {})
            pe_inst_key = pe_option.get('instrument_key')
            pe_ltp = pe_option.get('market_data', {}).get('ltp', 0)

            if pe_inst_key and pe_ltp > 0:
                timeframe_low = fetch_timeframe_low(pe_inst_key, tf['start'], tf['end'])
                if timeframe_low:
                    distance = abs(timeframe_low - 50)
                    results['pe'].append({
                        'strike': int(strike),
                        'timeframe_low': timeframe_low,
                        'ltp': pe_ltp,
                        'distance': distance
                    })

        # Find nearest to 50
        ce_nearest = min(results['ce'], key=lambda x: x['distance']) if results['ce'] else None
        pe_nearest = min(results['pe'], key=lambda x: x['distance']) if results['pe'] else None

        # Determine status
        status = 'active' if tf['id'] in active_threads else 'waiting'

        # Build thread data
        all_data[tf['id']] = {
            'timeframe': tf['label'],
            'start_time': f"{tf['start'][0]:02d}:{tf['start'][1]:02d}",
            'end_time': f"{tf['end'][0]:02d}:{tf['end'][1]:02d}",
            'status': status,
            'last_update': datetime.now().strftime('%H:%M:%S'),
            'ce_strike': {
                'strike': ce_nearest['strike'],
                'low': ce_nearest['timeframe_low'],
                'ltp': ce_nearest['ltp'],
                'distance': ce_nearest['distance'],
                'samples': 1,
                'last_update': datetime.now().strftime('%H:%M:%S')
            } if ce_nearest else None,
            'pe_strike': {
                'strike': pe_nearest['strike'],
                'low': pe_nearest['timeframe_low'],
                'ltp': pe_nearest['ltp'],
                'distance': pe_nearest['distance'],
                'samples': 1,
                'last_update': datetime.now().strftime('%H:%M:%S')
            } if pe_nearest else None
        }

        # Check for alerts (LTP approaching low from above, within ₹2)
        if ce_nearest:
            diff = ce_nearest['ltp'] - ce_nearest['timeframe_low']
            if 0 <= diff <= 2:  # Only alert if LTP is 0-2 rupees ABOVE the low
                alert_msg = f"🔔 ALERT! {tf['label']} CE {ce_nearest['strike']}: LTP ₹{ce_nearest['ltp']:.2f} approaching LOW ₹{ce_nearest['timeframe_low']:.2f}"
                print(f"\n{'='*70}")
                print(alert_msg)
                print(f"{'='*70}\n")
                os.system(f'osascript -e \'display notification "{alert_msg}" with title "Low Alert"\'')

        if pe_nearest:
            diff = pe_nearest['ltp'] - pe_nearest['timeframe_low']
            if 0 <= diff <= 2:  # Only alert if LTP is 0-2 rupees ABOVE the low
                alert_msg = f"🔔 ALERT! {tf['label']} PE {pe_nearest['strike']}: LTP ₹{pe_nearest['ltp']:.2f} approaching LOW ₹{pe_nearest['timeframe_low']:.2f}"
                print(f"\n{'='*70}")
                print(alert_msg)
                print(f"{'='*70}\n")
                os.system(f'osascript -e \'display notification "{alert_msg}" with title "Low Alert"\'')

    # Save all data
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'debug_tracking_{datetime.now().strftime("%Y%m%d")}.json')

    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ All timeframes updated: {output_file}")

    # Show summary
    print("\n" + "="*70)
    print("SUMMARY:")
    print("="*70)
    for tf in TIMEFRAMES:
        data = all_data[tf['id']]
        status = "🔴 LIVE" if data['status'] == 'active' else "⏸️  Waiting"
        print(f"{tf['label']} {status}")
        if data['ce_strike']:
            print(f"  📈 CE {data['ce_strike']['strike']}: Low ₹{data['ce_strike']['low']:.2f} (LTP: ₹{data['ce_strike']['ltp']:.2f})")
        if data['pe_strike']:
            print(f"  📉 PE {data['pe_strike']['strike']}: Low ₹{data['pe_strike']['low']:.2f} (LTP: ₹{data['pe_strike']['ltp']:.2f})")
    print("="*70)

if __name__ == '__main__':
    print("="*70)
    print("🎯 MULTI-TIMEFRAME TRACKER - All 4 Threads")
    print("="*70)
    print("Tracking:")
    for tf in TIMEFRAMES:
        print(f"  - {tf['label']}")
    print("="*70)
    print()

    while True:
        try:
            update_all_timeframes()

            # Generate dashboard
            subprocess.run(['python3', 'generate_live_dashboard.py'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"\n💤 Waiting 60 seconds...\n")
            time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n⏹️  Tracker stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)
