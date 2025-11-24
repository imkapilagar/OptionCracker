"""
Test Upstox API connection
Run this to verify your credentials are working
"""

import os
import requests

def test_connection():
    print("=" * 60)
    print("Upstox Connection Test")
    print("=" * 60)

    # Load credentials
    API_KEY = os.getenv('UPSTOX_API_KEY')
    ACCESS_TOKEN = os.getenv('UPSTOX_ACCESS_TOKEN')

    # Try to load from file if env vars not set
    if not API_KEY or not ACCESS_TOKEN:
        try:
            with open('upstox_credentials.txt', 'r') as f:
                for line in f:
                    if line.startswith('API_KEY='):
                        API_KEY = line.split('=')[1].strip()
                    elif line.startswith('ACCESS_TOKEN='):
                        ACCESS_TOKEN = line.split('=')[1].strip()
            print("✓ Loaded credentials from upstox_credentials.txt")
        except FileNotFoundError:
            print("❌ No credentials found!")
            print("Run: python upstox_token_generator.py")
            return

    if not API_KEY or not ACCESS_TOKEN:
        print("❌ Missing credentials!")
        print("Run: python upstox_token_generator.py")
        return

    print(f"\nAPI Key: {API_KEY[:10]}...")
    print(f"Access Token: {ACCESS_TOKEN[:20]}...")

    # Test 1: Get user profile
    print("\n" + "=" * 60)
    print("Test 1: Getting User Profile")
    print("=" * 60)

    url = "https://api.upstox.com/v2/user/profile"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        profile = response.json()

        if profile['status'] == 'success':
            print("✅ Connection successful!")
            data = profile['data']
            print(f"\nUser Details:")
            print(f"  Name: {data.get('user_name', 'N/A')}")
            print(f"  Email: {data.get('email', 'N/A')}")
            print(f"  User ID: {data.get('user_id', 'N/A')}")
            print(f"  Broker: {data.get('broker', 'N/A')}")

            # Test 2: Get NIFTY spot price
            print("\n" + "=" * 60)
            print("Test 2: Getting NIFTY Spot Price")
            print("=" * 60)

            quote_url = "https://api.upstox.com/v2/market-quote/quotes"
            params = {'instrument_key': 'NSE_INDEX|Nifty 50'}

            try:
                quote_response = requests.get(quote_url, headers=headers, params=params)
                quote_response.raise_for_status()
                quote_data = quote_response.json()

                if quote_data['status'] == 'success':
                    nifty_data = quote_data['data']['NSE_INDEX:Nifty 50']
                    ltp = nifty_data['last_price']

                    print(f"✅ NIFTY 50 Spot Price: {ltp}")
                    print(f"   Open: {nifty_data.get('ohlc', {}).get('open', 'N/A')}")
                    print(f"   High: {nifty_data.get('ohlc', {}).get('high', 'N/A')}")
                    print(f"   Low: {nifty_data.get('ohlc', {}).get('low', 'N/A')}")
                    print(f"   Close: {nifty_data.get('ohlc', {}).get('close', 'N/A')}")

                    print("\n" + "=" * 60)
                    print("🎉 ALL TESTS PASSED!")
                    print("=" * 60)
                    print("\nYour Upstox API is working perfectly!")
                    print("You can now run: python upstox_options_fetcher.py")

                else:
                    print(f"⚠️  Quote API returned: {quote_data.get('message', 'Unknown error')}")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    print("❌ Access token expired!")
                    print("Run: python upstox_token_generator.py")
                else:
                    print(f"❌ Quote API error: {e}")
                    print(f"Response: {e.response.text}")

        else:
            print(f"⚠️  Unexpected response: {profile}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Authentication failed!")
            print("Your access token might be expired or invalid.")
            print("\nRun: python upstox_token_generator.py")
        else:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {e.response.text}")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nPossible issues:")
        print("1. Network connectivity")
        print("2. Invalid credentials")
        print("3. API server issues")


if __name__ == '__main__':
    test_connection()
