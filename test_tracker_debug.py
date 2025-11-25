#!/usr/bin/env python3
"""
Debug version of tracker to see what's happening
"""
import requests
import pandas as pd
import json
import os
from datetime import datetime

# Read credentials
with open('upstox_credentials.txt', 'r') as f:
    lines = f.readlines()
    access_token = lines[1].split('=')[1].strip()

print("="*70)
print("DEBUG TRACKER TEST")
print("="*70)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print(f"Access token loaded: {access_token[:20]}...")
print()

# Fetch option chain
url = 'https://api.upstox.com/v2/option/chain'
headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
params = {'instrument_key': 'NSE_INDEX|Nifty 50', 'expiry_date': '2025-11-25'}

print("Fetching option chain...")
response = requests.get(url, headers=headers, params=params, timeout=10)
print(f"Response status: {response.status_code}")

if response.status_code != 200:
    print(f"ERROR: {response.text}")
    exit(1)

data = response.json()
chain_data = data.get('data', [])
print(f"Strikes available: {len(chain_data)}")

if not chain_data:
    print("ERROR: No strikes returned!")
    exit(1)

# Process strikes
print("\nProcessing strikes...")
lows_tracker = {}
processed = 0

for strike_data in chain_data:
    strike = strike_data.get('strike_price')

    # Process CE
    ce_option = strike_data.get('call_options', {})
    ce_market = ce_option.get('market_data', {})

    if ce_market:
        ltp = ce_market.get('ltp', 0)
        instrument_key = ce_option.get('instrument_key', '')

        if ltp > 0 and instrument_key:
            key = f"NIFTY_{strike}_CE"
            lows_tracker[key] = {
                'symbol': 'NIFTY',
                'strike': strike,
                'option_type': 'CE',
                'instrument_key': instrument_key,
                'low': ltp,
                'current_ltp': ltp,
                'samples': 1
            }
            processed += 1

print(f"Processed {processed} options")

# Create DataFrame
print("\nCreating DataFrame...")
df = pd.DataFrame.from_dict(lows_tracker, orient='index')
print(f"DataFrame shape: {df.shape}")

if df.empty:
    print("ERROR: DataFrame is empty!")
    exit(1)

# Find nearest to 50
df['distance_from_50'] = abs(df['low'] - 50)
ce_df = df[df['option_type'] == 'CE'].copy()

print(f"\nCE options: {len(ce_df)}")

if not ce_df.empty:
    nearest_ce = ce_df.nsmallest(1, 'distance_from_50').iloc[0]

    thread_data = {
        'timeframe': '09:30-10:30',
        'start_time': '09:30',
        'end_time': '10:30',
        'status': 'active',
        'samples': 1,
        'last_update': datetime.now().strftime('%H:%M:%S'),
        'ce_strike': {
            'strike': int(nearest_ce['strike']),
            'low': float(nearest_ce['low']),
            'ltp': float(nearest_ce['current_ltp']),
            'distance': float(nearest_ce['distance_from_50']),
            'samples': int(nearest_ce['samples'])
        }
    }

    print("\nNearest to ₹50:")
    print(f"  Strike: {thread_data['ce_strike']['strike']}")
    print(f"  Low: ₹{thread_data['ce_strike']['low']:.2f}")
    print(f"  Distance: ₹{thread_data['ce_strike']['distance']:.2f}")

    # Save to JSON
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'debug_tracking_{datetime.now().strftime("%Y%m%d")}.json')

    live_data = {'thread_1': thread_data}

    print(f"\nSaving to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(live_data, f, indent=2)

    print(f"✅ File saved successfully!")
    print(f"File exists: {os.path.exists(output_file)}")

    # Read it back
    with open(output_file, 'r') as f:
        verify = json.load(f)
    print(f"Verification: {len(verify)} threads in file")

print("\n" + "="*70)
print("DEBUG TEST COMPLETE")
print("="*70)
