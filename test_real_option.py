"""
Test fetching real NIFTY option data (Nov 25 expiry)
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

print("Testing NIFTY Nov 25, 2025 expiry options...")
print("=" * 80)

# Test a few ATM strikes
test_options = [
    "NSE_FO|NIFTY25NOV26050CE",
    "NSE_FO|NIFTY25NOV26050PE",
    "NSE_FO|NIFTY25NOV26100CE",
    "NSE_FO|NIFTY25NOV26100PE",
    "NSE_FO|NIFTY25NOV26150CE",
    "NSE_FO|NIFTY25NOV26150PE",
]

print("\n1. Fetching live quotes...")
print("-" * 80)

url = "https://api.upstox.com/v2/market-quote/quotes"
params = {'instrument_key': ','.join(test_options)}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    if data['status'] == 'success':
        for opt in test_options:
            opt_key = opt.replace('|', ':')
            if opt_key in data['data']:
                opt_data = data['data'][opt_key]
                ltp = opt_data.get('last_price', 0)
                volume = opt_data.get('volume', 0)
                oi = opt_data.get('oi', 0)
                print(f"✅ {opt:35} | LTP: {ltp:8.2f} | Vol: {volume:10} | OI: {oi:10}")
            else:
                print(f"❌ {opt:35} | No data")
    else:
        print(f"Error: {data}")
else:
    print(f"HTTP Error: {response.status_code}")

# Test historical data
print("\n\n2. Fetching 30-minute historical data for NIFTY25NOV26100CE...")
print("-" * 80)

symbol = "NSE_FO|NIFTY25NOV26100CE"
from_date = "2025-11-23"
to_date = "2025-11-24"

url = f"https://api.upstox.com/v2/historical-candle/{symbol}/30minute/{to_date}/{from_date}"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    if data['status'] == 'success' and data['data'].get('candles'):
        candles = data['data']['candles']
        print(f"✅ Got {len(candles)} candles\n")

        # Calculate high/low
        highs = [c[2] for c in candles]
        lows = [c[3] for c in candles]

        print(f"30-minute High: {max(highs):.2f}")
        print(f"30-minute Low:  {min(lows):.2f}")

        print(f"\nLatest 3 candles:")
        for i, candle in enumerate(candles[:3]):
            print(f"  {i+1}. Time: {datetime.fromtimestamp(candle[0]/1000)} | O:{candle[1]:7.2f} H:{candle[2]:7.2f} L:{candle[3]:7.2f} C:{candle[4]:7.2f}")

        print("\n" + "=" * 80)
        print("🎉 SUCCESS! WE CAN FETCH LIVE OPTION CHAIN DATA!")
        print("=" * 80)
        print("\nNext step: Run the full option chain fetcher")
        print("Command: python upstox_options_fetcher.py")

    else:
        print(f"No candle data: {data}")
else:
    print(f"HTTP Error: {response.status_code} - {response.text}")
