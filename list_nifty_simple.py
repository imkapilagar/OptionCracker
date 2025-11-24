"""
Simple listing of NIFTY options
"""

import requests
import gzip
import io

url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
response = requests.get(url)

if response.status_code == 200:
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        lines = f.readlines()

    print(f"Total lines: {len(lines)}")
    print("\nSearching for pure NIFTY options (not BANKNIFTY, FINNIFTY)...")
    print("=" * 100)

    count = 0
    for line in lines:
        # Look for NIFTY but not BANKNIFTY or FINNIFTY
        if '"NIFTY' in line and 'BANK' not in line and 'FINN' not in line and ('CE"' in line or 'PE"' in line):
            print(line.strip())
            count += 1
            if count >= 20:  # Show first 20
                break

    print(f"\n(Showing first 20 of many)")
else:
    print(f"Failed: {response.status_code}")
