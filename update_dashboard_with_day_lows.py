#!/usr/bin/env python3
"""
One-time update: Fetch day's lows and update dashboard
"""
import requests
import json
from datetime import datetime

# Read credentials
with open('upstox_credentials.txt', 'r') as f:
    lines = f.readlines()
    access_token = lines[1].split('=')[1].strip()

def fetch_day_low_for_strike(instrument_key):
    """Fetch day's low from intraday candles"""
    url = f'https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute'
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            candles = data.get('data', {}).get('candles', [])
            if candles:
                lows = [candle[3] for candle in candles if len(candle) > 3]
                if lows:
                    return min(lows)
    except:
        pass
    return None

# Fetch option chain
url = 'https://api.upstox.com/v2/option/chain'
headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
params = {'instrument_key': 'NSE_INDEX|Nifty 50', 'expiry_date': '2025-11-25'}

print("Fetching option chain...")
chain_data = requests.get(url, headers=headers, params=params, timeout=10).json()

# Focus on key strikes
key_strikes = [25900, 25950, 26000, 26050, 26100]

results = {'ce': [], 'pe': []}

print("\nProcessing key strikes...")
for strike_data in chain_data.get('data', []):
    strike = strike_data.get('strike_price')

    if strike not in key_strikes:
        continue

    print(f"  Strike {int(strike)}...")

    # CE
    ce_option = strike_data.get('call_options', {})
    ce_inst_key = ce_option.get('instrument_key')
    ce_ltp = ce_option.get('market_data', {}).get('ltp', 0)

    if ce_inst_key and ce_ltp > 0:
        day_low = fetch_day_low_for_strike(ce_inst_key)
        if day_low:
            distance = abs(day_low - 50)
            results['ce'].append({
                'strike': int(strike),
                'day_low': day_low,
                'ltp': ce_ltp,
                'distance': distance
            })

    # PE
    pe_option = strike_data.get('put_options', {})
    pe_inst_key = pe_option.get('instrument_key')
    pe_ltp = pe_option.get('market_data', {}).get('ltp', 0)

    if pe_inst_key and pe_ltp > 0:
        day_low = fetch_day_low_for_strike(pe_inst_key)
        if day_low:
            distance = abs(day_low - 50)
            results['pe'].append({
                'strike': int(strike),
                'day_low': day_low,
                'ltp': pe_ltp,
                'distance': distance
            })

# Find nearest to 50
ce_nearest = min(results['ce'], key=lambda x: x['distance']) if results['ce'] else None
pe_nearest = min(results['pe'], key=lambda x: x['distance']) if results['pe'] else None

print("\n" + "="*70)
print("RESULTS - Options Nearest to ₹50 (Day's Low):")
print("="*70)

if ce_nearest:
    print(f"📈 CE: Strike {ce_nearest['strike']}")
    print(f"   Day's Low: ₹{ce_nearest['day_low']:.2f}")
    print(f"   Current LTP: ₹{ce_nearest['ltp']:.2f}")
    print(f"   Distance: ₹{ce_nearest['distance']:.2f}")

if pe_nearest:
    print(f"📉 PE: Strike {pe_nearest['strike']}")
    print(f"   Day's Low: ₹{pe_nearest['day_low']:.2f}")
    print(f"   Current LTP: ₹{pe_nearest['ltp']:.2f}")
    print(f"   Distance: ₹{pe_nearest['distance']:.2f}")

print("="*70)

# Save to JSON
thread_data = {
    'timeframe': '09:15-15:30',
    'start_time': '09:15',
    'end_time': '15:30',
    'status': 'active',
    'last_update': datetime.now().strftime('%H:%M:%S'),
    'ce_strike': {
        'strike': ce_nearest['strike'],
        'low': ce_nearest['day_low'],
        'ltp': ce_nearest['ltp'],
        'distance': ce_nearest['distance'],
        'samples': 1,
        'last_update': datetime.now().strftime('%H:%M:%S')
    } if ce_nearest else None,
    'pe_strike': {
        'strike': pe_nearest['strike'],
        'low': pe_nearest['day_low'],
        'ltp': pe_nearest['ltp'],
        'distance': pe_nearest['distance'],
        'samples': 1,
        'last_update': datetime.now().strftime('%H:%M:%S')
    } if pe_nearest else None
}

output_data = {'thread_1': thread_data}

with open('output/debug_tracking_20251125.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✅ Saved to output/debug_tracking_20251125.json")
print("\nNow run: python3 generate_live_dashboard.py")
