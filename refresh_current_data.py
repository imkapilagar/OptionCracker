#!/usr/bin/env python3
"""
Fetch current option data and show options nearest to Rs 50
Updates the debug tracking file
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

# Fetch option chain
url = 'https://api.upstox.com/v2/option/chain'
headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
params = {'instrument_key': 'NSE_INDEX|Nifty 50', 'expiry_date': '2025-11-25'}

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Fetching current option data...", flush=True)

response = requests.get(url, headers=headers, params=params, timeout=10)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    exit(1)

data = response.json()
chain_data = data.get('data', [])

if not chain_data:
    print("❌ No option data available")
    exit(1)

# Process all options
lows_tracker_ce = {}
lows_tracker_pe = {}

for strike_data in chain_data:
    strike = strike_data.get('strike_price')

    # Process CE
    ce_option = strike_data.get('call_options', {})
    ce_market = ce_option.get('market_data', {})
    if ce_market:
        ltp = ce_market.get('ltp', 0)
        if ltp > 0:
            lows_tracker_ce[f"NIFTY_{strike}_CE"] = {
                'strike': strike,
                'option_type': 'CE',
                'low': ltp,
                'current_ltp': ltp,
                'samples': 1
            }

    # Process PE
    pe_option = strike_data.get('put_options', {})
    pe_market = pe_option.get('market_data', {})
    if pe_market:
        ltp = pe_market.get('ltp', 0)
        if ltp > 0:
            lows_tracker_pe[f"NIFTY_{strike}_PE"] = {
                'strike': strike,
                'option_type': 'PE',
                'low': ltp,
                'current_ltp': ltp,
                'samples': 1
            }

# Find nearest to Rs 50
thread_data = {
    'timeframe': '09:30-10:30',
    'start_time': '09:30',
    'end_time': '10:30',
    'status': 'active',
    'samples': 1,
    'last_update': datetime.now().strftime('%H:%M:%S'),
    'ce_strike': None,
    'pe_strike': None
}

# CE
if lows_tracker_ce:
    df_ce = pd.DataFrame.from_dict(lows_tracker_ce, orient='index')
    df_ce['distance_from_50'] = abs(df_ce['low'] - 50)
    nearest_ce = df_ce.nsmallest(1, 'distance_from_50').iloc[0]

    thread_data['ce_strike'] = {
        'strike': int(nearest_ce['strike']),
        'low': float(nearest_ce['low']),
        'ltp': float(nearest_ce['current_ltp']),
        'distance': float(nearest_ce['distance_from_50']),
        'samples': 1
    }

    print(f"📈 CE: Strike {thread_data['ce_strike']['strike']} @ ₹{thread_data['ce_strike']['low']:.2f} (Distance: ₹{thread_data['ce_strike']['distance']:.2f})")

# PE
if lows_tracker_pe:
    df_pe = pd.DataFrame.from_dict(lows_tracker_pe, orient='index')
    df_pe['distance_from_50'] = abs(df_pe['low'] - 50)
    nearest_pe = df_pe.nsmallest(1, 'distance_from_50').iloc[0]

    thread_data['pe_strike'] = {
        'strike': int(nearest_pe['strike']),
        'low': float(nearest_pe['low']),
        'ltp': float(nearest_pe['current_ltp']),
        'distance': float(nearest_pe['distance_from_50']),
        'samples': 1
    }

    print(f"📉 PE: Strike {thread_data['pe_strike']['strike']} @ ₹{thread_data['pe_strike']['low']:.2f} (Distance: ₹{thread_data['pe_strike']['distance']:.2f})")

# Save
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f'debug_tracking_{datetime.now().strftime("%Y%m%d")}.json')

live_data = {'thread_1': thread_data}

with open(output_file, 'w') as f:
    json.dump(live_data, f, indent=2)

print(f"✅ Updated: {output_file}")
