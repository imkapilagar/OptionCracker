#!/usr/bin/env python3
"""
Track option lows using intraday candle data to get ACTUAL day's low
This fetches the true low from market open, not just since script started
"""
import requests
import pandas as pd
import json
import os
from datetime import datetime
import time

# Read credentials
with open('upstox_credentials.txt', 'r') as f:
    lines = f.readlines()
    access_token = lines[1].split('=')[1].strip()

def fetch_option_chain():
    """Fetch current option chain data with instrument keys"""
    url = 'https://api.upstox.com/v2/option/chain'
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    params = {'instrument_key': 'NSE_INDEX|Nifty 50', 'expiry_date': '2025-11-25'}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
    except Exception as e:
        print(f"❌ Error fetching option chain: {e}")
    return []

def fetch_intraday_low(instrument_key):
    """Fetch intraday candle data and calculate day's low"""
    url = f'https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute'
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            candles = data.get('data', {}).get('candles', [])

            if candles:
                # Candles format: [timestamp, open, high, low, close, volume, oi]
                lows = [candle[3] for candle in candles if len(candle) > 3]
                if lows:
                    return min(lows)
    except Exception as e:
        pass  # Silent fail for individual options

    return None

def find_options_near_50():
    """Find options whose day's LOW is nearest to Rs 50"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching option chain...")

    chain_data = fetch_option_chain()
    if not chain_data:
        print("❌ No option chain data")
        return None, None

    results = []
    processed = 0

    for strike_data in chain_data:
        strike = strike_data.get('strike_price')

        # Process CE
        ce_option = strike_data.get('call_options', {})
        ce_instrument_key = ce_option.get('instrument_key')
        ce_ltp = ce_option.get('market_data', {}).get('ltp', 0)

        # OPTIMIZATION: Only fetch intraday data for options in reasonable LTP range
        if ce_instrument_key and 10 <= ce_ltp <= 150:
            # Fetch intraday low
            day_low = fetch_intraday_low(ce_instrument_key)
            processed += 1

            if day_low and day_low > 0:
                distance = abs(day_low - 50)
                results.append({
                    'strike': strike,
                    'option_type': 'CE',
                    'instrument_key': ce_instrument_key,
                    'day_low': day_low,
                    'current_ltp': ce_ltp,
                    'distance_from_50': distance
                })

        # Process PE
        pe_option = strike_data.get('put_options', {})
        pe_instrument_key = pe_option.get('instrument_key')
        pe_ltp = pe_option.get('market_data', {}).get('ltp', 0)

        # OPTIMIZATION: Only fetch intraday data for options in reasonable LTP range
        if pe_instrument_key and 10 <= pe_ltp <= 150:
            # Fetch intraday low
            day_low = fetch_intraday_low(pe_instrument_key)
            processed += 1

            if day_low and day_low > 0:
                distance = abs(day_low - 50)
                results.append({
                    'strike': strike,
                    'option_type': 'PE',
                    'instrument_key': pe_instrument_key,
                    'day_low': day_low,
                    'current_ltp': pe_ltp,
                    'distance_from_50': distance
                })

    print(f"   Processed {processed} options in LTP range 10-150")

    if not results:
        return None, None

    # Convert to DataFrame and find nearest
    df = pd.DataFrame(results)

    ce_df = df[df['option_type'] == 'CE']
    pe_df = df[df['option_type'] == 'PE']

    ce_nearest = None
    pe_nearest = None

    if not ce_df.empty:
        nearest = ce_df.nsmallest(1, 'distance_from_50').iloc[0]
        ce_nearest = {
            'strike': int(nearest['strike']),
            'low': float(nearest['day_low']),
            'ltp': float(nearest['current_ltp']),
            'distance': float(nearest['distance_from_50']),
            'last_update': datetime.now().strftime('%H:%M:%S')
        }

    if not pe_df.empty:
        nearest = pe_df.nsmallest(1, 'distance_from_50').iloc[0]
        pe_nearest = {
            'strike': int(nearest['strike']),
            'low': float(nearest['day_low']),
            'ltp': float(nearest['current_ltp']),
            'distance': float(nearest['distance_from_50']),
            'last_update': datetime.now().strftime('%H:%M:%S')
        }

    return ce_nearest, pe_nearest

def save_tracking_data(ce_nearest, pe_nearest):
    """Save current tracking data to JSON"""
    thread_data = {
        'timeframe': '09:15-15:30',
        'start_time': '09:15',
        'end_time': '15:30',
        'status': 'active',
        'last_update': datetime.now().strftime('%H:%M:%S'),
        'ce_strike': ce_nearest,
        'pe_strike': pe_nearest
    }

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'debug_tracking_{datetime.now().strftime("%Y%m%d")}.json')

    live_data = {'thread_1': thread_data}

    with open(output_file, 'w') as f:
        json.dump(live_data, f, indent=2)

def continuous_tracking(interval_seconds=60):
    """Continuously track day's lows"""
    print("="*70)
    print("🎯 DAY'S LOW TRACKER - Using Intraday Candle Data")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Update interval: {interval_seconds} seconds")
    print(f"Target: Find options whose DAY'S LOW is closest to ₹50")
    print(f"Data source: Intraday 1-minute candles from market open")
    print("="*70)
    print()

    try:
        while True:
            # Find nearest to 50
            ce_nearest, pe_nearest = find_options_near_50()

            # Display current status
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} Status:")
            if ce_nearest:
                print(f"   📈 CE: Strike {ce_nearest['strike']} - DAY LOW: ₹{ce_nearest['low']:.2f} (Current: ₹{ce_nearest['ltp']:.2f}) - Distance: ₹{ce_nearest['distance']:.2f}")
            else:
                print(f"   📈 CE: No data")

            if pe_nearest:
                print(f"   📉 PE: Strike {pe_nearest['strike']} - DAY LOW: ₹{pe_nearest['low']:.2f} (Current: ₹{pe_nearest['ltp']:.2f}) - Distance: ₹{pe_nearest['distance']:.2f}")
            else:
                print(f"   📉 PE: No data")

            # Check if very close to target
            if ce_nearest and ce_nearest['distance'] <= 5:
                print(f"\n🔔 CE VERY CLOSE TO ₹50! Strike {ce_nearest['strike']} - Low: ₹{ce_nearest['low']:.2f}")

            if pe_nearest and pe_nearest['distance'] <= 5:
                print(f"\n🔔 PE VERY CLOSE TO ₹50! Strike {pe_nearest['strike']} - Low: ₹{pe_nearest['low']:.2f}")

            # Save to file for dashboard
            save_tracking_data(ce_nearest, pe_nearest)

            # Wait for next interval
            print(f"\n💤 Waiting {interval_seconds} seconds...")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n\n⏹️  Tracking stopped")

        # Final summary
        ce_nearest, pe_nearest = find_options_near_50()
        print("\n" + "="*70)
        print("FINAL SUMMARY - Options Nearest to ₹50 DAY'S LOW:")
        print("="*70)
        if ce_nearest:
            print(f"📈 CE: Strike {ce_nearest['strike']}")
            print(f"   DAY'S LOW: ₹{ce_nearest['low']:.2f}")
            print(f"   Current LTP: ₹{ce_nearest['ltp']:.2f}")
            print(f"   Distance from ₹50: ₹{ce_nearest['distance']:.2f}")
        if pe_nearest:
            print(f"📉 PE: Strike {pe_nearest['strike']}")
            print(f"   DAY'S LOW: ₹{pe_nearest['low']:.2f}")
            print(f"   Current LTP: ₹{pe_nearest['ltp']:.2f}")
            print(f"   Distance from ₹50: ₹{pe_nearest['distance']:.2f}")
        print("="*70)

if __name__ == '__main__':
    continuous_tracking(interval_seconds=60)
