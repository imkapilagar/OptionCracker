"""
Find the correct NIFTY option format for Nov 2025
"""

import requests
import gzip
import io

url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
response = requests.get(url)

if response.status_code == 200:
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        lines = f.readlines()

    print("Searching for NIFTY Nov 2025 options around strike 26000...")
    print("=" * 100)

    found = []
    for line in lines:
        # Look for NIFTY (not BANKNIFTY) Nov 2025 options
        if '"NIFTY' in line and 'BANK' not in line and 'FINN' not in line and '2025-11-27' in line:
            parts = line.strip().split(',')
            if len(parts) > 6:
                instrument_key = parts[0].replace('"', '')
                symbol = parts[2].replace('"', '')
                strike = float(parts[6].replace('"', '')) if parts[6].replace('"', '') else 0

                # Filter for strikes around 26000
                if 25800 <= strike <= 26400:
                    found.append({
                        'key': instrument_key,
                        'symbol': symbol,
                        'strike': strike,
                        'line': line.strip()
                    })

    # Sort by strike
    found.sort(key=lambda x: x['strike'])

    print(f"\nFound {len(found)} NIFTY options for Nov 27, 2025 (strikes 25800-26400):\n")

    for opt in found[:20]:  # Show first 20
        print(f"{opt['key']:50} | Strike: {opt['strike']:7.0f} | {opt['symbol']}")

    if found:
        print("\n" + "=" * 100)
        print("Sample instrument key format:")
        print(found[0]['key'])
else:
    print(f"Failed: {response.status_code}")
