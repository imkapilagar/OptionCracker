"""
Find actual weekly NIFTY options for current expiry
"""

import requests
import gzip
import io
from datetime import datetime

# Download instruments master
url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
response = requests.get(url)

if response.status_code == 200:
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        lines = f.readlines()

    print("Searching for NIFTY options expiring in Nov/Dec 2025...")
    print("=" * 80)

    # Filter for NIFTY options
    nifty_options = []
    for line in lines:
        if 'NIFTY' in line and ('25NOV' in line or '25DEC' in line or '24NOV' in line):
            parts = line.strip().split(',')
            if len(parts) > 5:
                instrument_key = parts[0].replace('"', '')
                symbol = parts[2].replace('"', '')
                expiry = parts[5].replace('"', '')
                strike = parts[6].replace('"', '')
                opt_type = parts[11].replace('"', '')

                if 'NIFTY' in instrument_key and 'BANK' not in instrument_key:
                    nifty_options.append({
                        'key': instrument_key,
                        'symbol': symbol,
                        'expiry': expiry,
                        'strike': float(strike) if strike else 0,
                        'type': opt_type
                    })

    # Sort by expiry and strike
    nifty_options.sort(key=lambda x: (x['expiry'], x['strike']))

    # Group by expiry
    expiries = {}
    for opt in nifty_options:
        exp = opt['expiry']
        if exp not in expiries:
            expiries[exp] = []
        expiries[exp].append(opt)

    print(f"\nFound {len(expiries)} expiries with NIFTY options\n")

    for expiry in sorted(expiries.keys())[:5]:  # Show first 5 expiries
        opts = expiries[expiry]
        print(f"\nExpiry: {expiry} ({len(opts)} options)")
        print("-" * 80)

        # Show ATM strikes (around 26100)
        atm_opts = [o for o in opts if 26000 <= o['strike'] <= 26300][:10]

        for opt in atm_opts:
            print(f"  {opt['key']:45} | Strike: {opt['strike']:7.0f} | {opt['type']}")

else:
    print(f"Failed to download: {response.status_code}")
