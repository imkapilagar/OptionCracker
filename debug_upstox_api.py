"""
Debug script to see actual Upstox API response
"""

import requests
import json

# Load credentials
with open('upstox_credentials.txt', 'r') as f:
    for line in f:
        if line.startswith('API_KEY='):
            API_KEY = line.split('=')[1].strip()
        elif line.startswith('ACCESS_TOKEN='):
            ACCESS_TOKEN = line.split('=')[1].strip()

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

print("Testing NIFTY quote API...")
print("=" * 60)

url = "https://api.upstox.com/v2/market-quote/quotes"
params = {'instrument_key': 'NSE_INDEX|Nifty 50'}

response = requests.get(url, headers=headers, params=params)

print(f"Status Code: {response.status_code}")
print(f"\nFull Response:")
print("=" * 60)
print(json.dumps(response.json(), indent=2))
