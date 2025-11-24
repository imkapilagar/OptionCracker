"""
Quick view of current option prices (what's being tracked)
"""

import requests
from datetime import datetime

# Load credentials
with open('upstox_credentials.txt', 'r') as f:
    for line in f:
        if line.startswith('ACCESS_TOKEN='):
            ACCESS_TOKEN = line.split('=')[1].strip()

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

print("="*100)
print(f"CURRENT OPTION PRICES - NIFTY (Being Tracked)")
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("="*100)

# Fetch option chain
url = 'https://api.upstox.com/v2/option/chain'
params = {
    'instrument_key': 'NSE_INDEX|Nifty 50',
    'expiry_date': '2025-11-25'
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

if data['status'] == 'success':
    chain_data = data['data']
    spot_price = chain_data[0].get('underlying_spot_price', 0)
    atm_strike = round(spot_price / 50) * 50

    print(f"\nNIFTY Spot: {spot_price:.2f}")
    print(f"ATM Strike: {atm_strike}")

    print(f"\n{'='*100}")
    print(f"{'Strike':<10} {'Type':<6} {'LTP':<10} {'Volume':<15} {'OI':<15}")
    print("="*100)

    tracked_count = 0

    for strike_data in chain_data:
        strike = strike_data['strike_price']

        # CE: ATM to OTM15
        if atm_strike <= strike <= atm_strike + (15 * 50):
            ce_option = strike_data.get('call_options', {})
            if ce_option and ce_option.get('market_data'):
                ltp = ce_option['market_data'].get('ltp', 0)
                volume = ce_option['market_data'].get('volume', 0)
                oi = ce_option['market_data'].get('oi', 0)
                print(f"{strike:<10.0f} {'CE':<6} {ltp:<10.2f} {volume:<15,.0f} {oi:<15,.0f}")
                tracked_count += 1

        # PE: ATM to OTM15
        if atm_strike - (15 * 50) <= strike <= atm_strike:
            pe_option = strike_data.get('put_options', {})
            if pe_option and pe_option.get('market_data'):
                ltp = pe_option['market_data'].get('ltp', 0)
                volume = pe_option['market_data'].get('volume', 0)
                oi = pe_option['market_data'].get('oi', 0)
                print(f"{strike:<10.0f} {'PE':<6} {ltp:<10.2f} {volume:<15,.0f} {oi:<15,.0f}")
                tracked_count += 1

    print("="*100)
    print(f"\n✅ Total strikes being tracked: {tracked_count}")
    print(f"📊 The tracker is recording the LOWEST price for each strike from 11:30 to 12:30")
    print(f"💾 Results will be saved to: output/option_lows_20251124_1130_to_1230.csv")
else:
    print("❌ Failed to fetch data")
