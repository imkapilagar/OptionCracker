"""
Get full symbol details for NIFTY options
"""

import requests
import gzip
import io

url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
response = requests.get(url)

if response.status_code == 200:
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        lines = f.readlines()

    print("Getting full details for NIFTY 26100 options (Nov 25 expiry)...")
    print("=" * 120)

    header = lines[0].strip()
    print(f"CSV Header:\n{header}\n")
    print("=" * 120)

    for line in lines:
        # Look for Nov 25, strike 26100
        if '2025-11-25' in line and '26100' in line and '"NIFTY' in line and 'BANK' not in line:
            print(line.strip())
            print()

else:
    print(f"Failed: {response.status_code}")
