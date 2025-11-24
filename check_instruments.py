"""
Check available NIFTY option instruments
"""

import requests

# Load credentials
with open('upstox_credentials.txt', 'r') as f:
    for line in f:
        if line.startswith('ACCESS_TOKEN='):
            ACCESS_TOKEN = line.split('=')[1].strip()

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

# Try to get option chain
print("Fetching NIFTY option chain...")
print("=" * 60)

url = "https://api.upstox.com/v2/option/chain"
params = {
    'instrument_key': 'NSE_FO|NIFTY',
    'expiry_date': '2025-11-27'
}

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data['status'] == 'success':
        # Show sample strikes
        strikes = data['data'][:5]  # First 5 strikes
        print("\nSample NIFTY options available:")
        print("=" * 60)
        for strike_data in strikes:
            print(f"\nStrike: {strike_data.get('strike_price', 'N/A')}")
            if 'call_options' in strike_data:
                ce = strike_data['call_options']
                print(f"  CE: {ce.get('instrument_key', 'N/A')}")
            if 'put_options' in strike_data:
                pe = strike_data['put_options']
                print(f"  PE: {pe.get('instrument_key', 'N/A')}")
    else:
        print(f"Error: {data}")
else:
    print(f"Response: {response.text}")
