#!/usr/bin/env python3
"""
Multi-Timeframe Option Chain Tracker
Tracks option lows for 4 time periods with 60-minute lookback:
- 10:30 AM (lookback: 09:30-10:30)
- 11:00 AM (lookback: 10:00-11:00)
- 11:30 AM (lookback: 10:30-11:30)
- 12:00 PM (lookback: 11:00-12:00)
"""

import requests
from datetime import datetime, time, timedelta
import time as time_module
import pandas as pd
import json
import os

# Read credentials
with open('upstox_credentials.txt', 'r') as f:
    lines = f.readlines()
    access_token = lines[2].split('=')[1].strip()

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
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            return data.get('data', [])
        return []
    except Exception as e:
        print(f"Error fetching option chain: {e}", flush=True)
        return []

def track_timeframe(access_token, start_time_str, end_time_str, symbol='NIFTY', interval_seconds=30):
    """
    Track option lows for a specific 60-minute timeframe
    Returns: dict with CE and PE strikes nearest to Rs 50
    """
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strptime(end_time_str, '%H:%M').time()

    print(f"\n{'='*60}", flush=True)
    print(f"Tracking Period: {start_time_str} to {end_time_str}", flush=True)
    print(f"{'='*60}", flush=True)

    # Wait until start time
    while datetime.now().time() < start_time:
        remaining = (datetime.combine(datetime.today(), start_time) - datetime.now()).total_seconds()
        print(f"\rWaiting for {start_time_str}... ({int(remaining)}s remaining)", end='', flush=True)
        time_module.sleep(5)

    print(f"\n\n🚀 Starting tracking at {datetime.now().strftime('%H:%M:%S')}", flush=True)

    lows_tracker = {}
    sample_count = 0

    # Track until end time
    while datetime.now().time() < end_time:
        sample_count += 1
        print(f"\n📊 Sample #{sample_count} at {datetime.now().strftime('%H:%M:%S')}", flush=True)

        # Fetch data
        option_data = fetch_option_chain(access_token, symbol)

        if not option_data:
            print("❌ No data received", flush=True)
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
                    lows_tracker[key]['current_ltp'] = ltp
                    if ltp < lows_tracker[key]['low']:
                        lows_tracker[key]['low'] = ltp

        print(f"✅ Tracked {len(lows_tracker)} strikes", flush=True)

        # Sleep until next sample
        time_module.sleep(interval_seconds)

    print(f"\n✅ Tracking completed at {datetime.now().strftime('%H:%M:%S')}", flush=True)
    print(f"Total samples: {sample_count}", flush=True)

    # Find strikes nearest to Rs 50
    df = pd.DataFrame.from_dict(lows_tracker, orient='index')

    if df.empty:
        return None

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
        'pe_strike': None
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
        print(f"\n📈 CE Strike nearest to ₹50: {result['ce_strike']['strike']} (Low: ₹{result['ce_strike']['low']})", flush=True)

    if not pe_df.empty:
        nearest_pe = pe_df.nsmallest(1, 'distance_from_50').iloc[0]
        result['pe_strike'] = {
            'strike': int(nearest_pe['strike']),
            'low': float(nearest_pe['low']),
            'ltp': float(nearest_pe['current_ltp']),
            'distance': float(nearest_pe['distance_from_50']),
            'samples': int(nearest_pe['samples'])
        }
        print(f"📉 PE Strike nearest to ₹50: {result['pe_strike']['strike']} (Low: ₹{result['pe_strike']['low']})", flush=True)

    return result

def generate_html_now(results):
    """Generate HTML report immediately with current results"""
    import subprocess
    output_dir = 'output'
    output_file = os.path.join(output_dir, f'multi_timeframe_{datetime.now().strftime("%Y%m%d")}.json')

    # Save current results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Generate HTML report
    print(f"\n🌐 Generating HTML report...", flush=True)
    subprocess.run(['python', 'generate_compact_report.py'], check=True)
    print(f"✅ Report updated at: index.html", flush=True)

def main():
    """Main function to track all 4 timeframes"""

    # Define timeframes with 60-minute lookback
    timeframes = [
        ('09:30', '10:30'),  # 10:30 lookback
        ('10:00', '11:00'),  # 11:00 lookback
        ('10:30', '11:30'),  # 11:30 lookback
        ('11:00', '12:00'),  # 12:00 lookback
    ]

    results = []

    print("="*60)
    print("NIFTY OPTION CHAIN - MULTI-TIMEFRAME TRACKER")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Tracking 4 timeframes with 60-minute lookback periods")
    print("="*60)

    for start_time, end_time in timeframes:
        result = track_timeframe(access_token, start_time, end_time, symbol='NIFTY', interval_seconds=30)
        if result:
            results.append(result)

            # Generate HTML report immediately after each timeframe
            generate_html_now(results)

    print(f"\n{'='*60}")
    print(f"✅ All timeframes completed!")
    print(f"📊 Final report available at: index.html")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
