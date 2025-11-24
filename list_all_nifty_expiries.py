"""
List all available NIFTY expiries
"""

import requests
import gzip
import io
from collections import defaultdict

url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
response = requests.get(url)

if response.status_code == 200:
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        lines = f.readlines()

    print("Finding all NIFTY option expiries...")
    print("=" * 100)

    expiries = defaultdict(list)

    for line in lines:
        # Look for pure NIFTY (not BANKNIFTY/FINNIFTY) options
        if '"NSE_FO' in line and '"NIFTY' in line and 'BANK' not in line and 'FINN' not in line and 'NXT' not in line:
            parts = line.strip().split(',')
            if len(parts) > 6:
                instrument_key = parts[0].replace('"', '')
                symbol = parts[2].replace('"', '')
                expiry = parts[5].replace('"', '')
                strike = parts[6].replace('"', '')

                if 'NIFTY' in symbol and ('CE' in symbol or 'PE' in symbol):
                    expiries[expiry].append({
                        'key': instrument_key,
                        'symbol': symbol,
                        'strike': float(strike) if strike else 0
                    })

    print(f"\nAvailable NIFTY option expiries:\n")

    for expiry in sorted(expiries.keys())[:10]:  # Show first 10 expiries
        opts = expiries[expiry]
        # Show ATM range
        atm_opts = [o for o in opts if 26000 <= o['strike'] <= 26200]

        print(f"\nExpiry: {expiry} ({len(opts)} total options)")
        print("-" * 100)

        if atm_opts:
            print("  Sample ATM options:")
            for opt in atm_opts[:5]:
                print(f"    {opt['key']:50} | Strike: {opt['strike']:7.0f}")
        else:
            # Show any 3 options as sample
            print("  Sample options (any strikes):")
            for opt in opts[:3]:
                print(f"    {opt['key']:50} | Strike: {opt['strike']:7.0f}")

else:
    print(f"Failed: {response.status_code}")
