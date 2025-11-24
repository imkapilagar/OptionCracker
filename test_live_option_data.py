"""
Test ALL possible live option data endpoints for Upstox
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

print("=" * 100)
print(f"TESTING LIVE OPTION DATA - Market is OPEN")
print(f"Time: {datetime.now()}")
print("=" * 100)

# First, get NIFTY spot to calculate ATM
print("\n1. Getting NIFTY Spot Price...")
print("-" * 100)

url = "https://api.upstox.com/v2/market-quote/quotes"
params = {'instrument_key': 'NSE_INDEX|Nifty 50'}

response = requests.get(url, headers=headers, params=params)
data = response.json()

if data['status'] == 'success':
    nifty_price = data['data']['NSE_INDEX:Nifty 50']['last_price']
    print(f"✅ NIFTY 50: {nifty_price}")

    # Calculate ATM
    atm_strike = round(nifty_price / 50) * 50
    print(f"   ATM Strike: {atm_strike}")
else:
    print("❌ Failed to get NIFTY price")
    atm_strike = 26100  # Fallback

# Try different option symbols for nearest expiry (Nov 25)
print(f"\n2. Testing LIVE quotes for Nov 25 expiry options (ATM = {atm_strike})...")
print("-" * 100)

test_options = [
    f"NSE_FO|NIFTY25NOV{atm_strike}CE",
    f"NSE_FO|NIFTY25NOV{atm_strike}PE",
    f"NSE_FO|NIFTY25NOV{atm_strike+50}CE",
    f"NSE_FO|NIFTY25NOV{atm_strike+50}PE",
]

for opt in test_options:
    params = {'instrument_key': opt}
    response = requests.get("https://api.upstox.com/v2/market-quote/quotes", headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        print(f"\n{opt}")
        print(f"  Status: {result['status']}")
        print(f"  Data: {result.get('data', {})}")
    else:
        print(f"\n{opt}")
        print(f"  Error: {response.status_code}")

# Try LTP endpoint (might be different)
print(f"\n\n3. Testing LTP (Last Traded Price) endpoint...")
print("-" * 100)

url = "https://api.upstox.com/v2/market-quote/ltp"
params = {'instrument_key': f"NSE_FO|NIFTY25NOV{atm_strike}CE"}

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Try full market quote
print(f"\n\n4. Testing Full Market Quote endpoint...")
print("-" * 100)

url = "https://api.upstox.com/v2/market-quote/quotes"
params = {'instrument_key': f"NSE_FO|NIFTY25NOV{atm_strike}CE"}

response = requests.get(url, headers=headers, params=params)
result = response.json()
print(f"Status: {response.status_code}")
print(f"Response: {result}")

# Try OHLC endpoint
print(f"\n\n5. Testing OHLC endpoint...")
print("-" * 100)

url = "https://api.upstox.com/v2/market-quote/ohlc"
params = {'instrument_key': f"NSE_FO|NIFTY25NOV{atm_strike}CE"}

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Try with December monthly expiry (might work better)
print(f"\n\n6. Testing with December MONTHLY expiry...")
print("-" * 100)

dec_options = [
    f"NSE_FO|NIFTY25DEC{atm_strike}CE",
    f"NSE_FO|NIFTY25DEC{atm_strike}PE",
]

for opt in dec_options:
    url = "https://api.upstox.com/v2/market-quote/ltp"
    params = {'instrument_key': opt}
    response = requests.get(url, headers=headers, params=params)

    result = response.json()
    print(f"\n{opt}")
    print(f"  Status: {result['status']}")
    if result['status'] == 'success' and result.get('data'):
        for key, value in result['data'].items():
            print(f"  {key}: {value}")

print("\n\n" + "=" * 100)
print("TEST COMPLETE")
print("=" * 100)
