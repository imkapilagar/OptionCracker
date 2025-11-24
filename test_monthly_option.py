"""
Test fetching monthly NIFTY option data
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

print("Testing December 2025 monthly expiry NIFTY options...")
print("=" * 80)

# Test ATM strikes for December expiry (nearest monthly)
# NIFTY is at ~26129, so test 26000, 26100, 26150, 26200
test_strikes = [26000, 26100, 26150, 26200]

for strike in test_strikes:
    ce_symbol = f"NSE_FO|NIFTY25DEC{strike}CE"
    pe_symbol = f"NSE_FO|NIFTY25DEC{strike}PE"

    print(f"\nStrike {strike}:")
    print("-" * 80)

    # Get quotes
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {'instrument_key': f"{ce_symbol},{pe_symbol}"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            # Check CE
            ce_key = ce_symbol.replace('|', ':')
            if ce_key in data['data']:
                ce_data = data['data'][ce_key]
                print(f"  ✅ CE: LTP={ce_data.get('last_price', 'N/A'):8.2f} | Vol={ce_data.get('volume', 'N/A')}")
            else:
                print(f"  ❌ CE: No data")

            # Check PE
            pe_key = pe_symbol.replace('|', ':')
            if pe_key in data['data']:
                pe_data = data['data'][pe_key]
                print(f"  ✅ PE: LTP={pe_data.get('last_price', 'N/A'):8.2f} | Vol={pe_data.get('volume', 'N/A')}")
            else:
                print(f"  ❌ PE: No data")
    else:
        print(f"  ❌ API Error: {response.status_code}")

# Now test historical data
print("\n\n" + "=" * 80)
print("Testing 1-hour historical data for NIFTY25DEC26100CE...")
print("=" * 80)

from_date = "2025-11-23"
to_date = "2025-11-24"
symbol = "NSE_FO|NIFTY25DEC26100CE"

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

        print(f"1-hour High: {max(highs):.2f}")
        print(f"1-hour Low:  {min(lows):.2f}")

        print(f"\nLatest candle:")
        latest = candles[0]
        print(f"  Time:  {datetime.fromtimestamp(latest[0]/1000)}")
        print(f"  Open:  {latest[1]:.2f}")
        print(f"  High:  {latest[2]:.2f}")
        print(f"  Low:   {latest[3]:.2f}")
        print(f"  Close: {latest[4]:.2f}")

        print("\n" + "=" * 80)
        print("🎉 SUCCESS! We can fetch option chain data!")
        print("=" * 80)
    else:
        print(f"❌ No candle data: {data}")
else:
    print(f"❌ HTTP Error: {response.status_code} - {response.text}")
