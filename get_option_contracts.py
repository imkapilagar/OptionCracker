"""
Get all available option contracts for NIFTY
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

# Method 1: Try getting contract information
print("Getting NIFTY 26100 CE for Nov 27...")
print("=" * 60)

# Try different symbol formats
test_symbols = [
    "NSE_FO|NIFTY24NOV26100CE",  # Format 1
    "NSE_FO|NIFTY2427NOV26100CE",  # Format 2
    "NSE_FO|NIFTY24N2726100CE",  # Format 3
    "NSE_FO|44194",  # Try with instrument token if we know it
]

for symbol in test_symbols:
    print(f"\nTrying: {symbol}")
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {'instrument_key': symbol}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print(f"✅ SUCCESS! Found it: {symbol}")
            print(data)
            break
        else:
            print(f"❌ Not found")
    else:
        print(f"❌ Error: {response.status_code}")

# Method 2: Download instruments master file
print("\n\n" + "=" * 60)
print("Downloading instruments master file...")
print("=" * 60)

url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
import gzip
import io

response = requests.get(url)
if response.status_code == 200:
    # Decompress and read
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        lines = f.readlines()[:100]  # First 100 lines

    print("\nSearching for NIFTY options in master file...")
    nifty_options = [line for line in lines if 'NIFTY' in line and ('CE' in line or 'PE' in line)][:10]

    print(f"\nFound {len(nifty_options)} NIFTY options (showing first 10):")
    print("=" * 60)
    for line in nifty_options:
        print(line.strip())
else:
    print(f"Failed to download: {response.status_code}")
