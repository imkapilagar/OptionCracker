"""
Test Upstox live market option chain fetching
"""

import os
import requests
from datetime import datetime, timedelta

def main():
    print("=" * 60)
    print("UPSTOX LIVE MARKET OPTION CHAIN TEST")
    print(f"Time: {datetime.now()}")
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
        except FileNotFoundError:
            print("❌ No credentials found!")
            print("Run: python upstox_token_generator.py")
            return

    if not API_KEY or not ACCESS_TOKEN:
        print("❌ Missing credentials!")
        print("Run: python upstox_token_generator.py")
        return

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    # Test 1: Get NIFTY spot price
    print("\n1. Testing NIFTY spot price fetch...")
    try:
        url = "https://api.upstox.com/v2/market-quote/quotes"
        params = {'instrument_key': 'NSE_INDEX|Nifty 50'}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'success':
            nifty_price = data['data']['NSE_INDEX:Nifty 50']['last_price']
            print(f"✅ NIFTY 50 Spot Price: {nifty_price}")
        else:
            print(f"❌ Failed: {data}")
            return

    except Exception as e:
        print(f"❌ Failed to get spot price: {e}")
        if '401' in str(e):
            print("\n⚠️  Your access token might be expired!")
            print("Run: python upstox_token_generator.py")
        return

    # Test 2: Calculate ATM strike
    print("\n2. Finding ATM options for NIFTY...")
    step = 50
    atm_strike = round(nifty_price / step) * step
    print(f"   ATM Strike: {atm_strike}")

    # Get nearest Thursday (expiry)
    today = datetime.now().date()
    days_ahead = 3 - today.weekday()  # 3 = Thursday
    if days_ahead <= 0:
        days_ahead += 7
    nearest_thursday = today + timedelta(days=days_ahead)
    print(f"   Nearest Expiry: {nearest_thursday}")

    # Test 3: Format option symbols
    print("\n3. Creating option instrument keys...")
    expiry_str = nearest_thursday.strftime('%y%b%d').upper()

    atm_ce_key = f"NSE_FO|NIFTY{expiry_str}{int(atm_strike)}CE"
    atm_pe_key = f"NSE_FO|NIFTY{expiry_str}{int(atm_strike)}PE"

    print(f"   CE: {atm_ce_key}")
    print(f"   PE: {atm_pe_key}")

    # Test 4: Get live quotes for ATM options
    print("\n4. Fetching live quotes...")
    try:
        url = "https://api.upstox.com/v2/market-quote/quotes"
        params = {'instrument_key': f"{atm_ce_key},{atm_pe_key}"}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        quote_data = response.json()

        if quote_data['status'] == 'success':
            if atm_ce_key in quote_data['data']:
                ce_data = quote_data['data'][atm_ce_key]
                print(f"\n✅ ATM CE ({atm_ce_key}):")
                print(f"   LTP: {ce_data['last_price']}")
                print(f"   Volume: {ce_data.get('volume', 'N/A')}")
                print(f"   OI: {ce_data.get('oi', 'N/A')}")

            if atm_pe_key in quote_data['data']:
                pe_data = quote_data['data'][atm_pe_key]
                print(f"\n✅ ATM PE ({atm_pe_key}):")
                print(f"   LTP: {pe_data['last_price']}")
                print(f"   Volume: {pe_data.get('volume', 'N/A')}")
                print(f"   OI: {pe_data.get('oi', 'N/A')}")

            # Test 5: Get historical data (1-hour candles for today)
            print(f"\n5. Fetching 1-hour historical data...")
            today_str = datetime.now().strftime('%Y-%m-%d')
            yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

            hist_url = f"https://api.upstox.com/v2/historical-candle/{atm_ce_key}/60minute/{today_str}/{yesterday_str}"

            hist_response = requests.get(hist_url, headers=headers)
            hist_response.raise_for_status()
            hist_data = hist_response.json()

            if hist_data['status'] == 'success' and hist_data['data']['candles']:
                candles = hist_data['data']['candles']
                print(f"✅ Got {len(candles)} candles")

                if candles:
                    latest = candles[0]  # First candle is the latest
                    print(f"\n   Latest candle (CE):")
                    print(f"   Time: {datetime.fromtimestamp(latest[0]/1000)}")
                    print(f"   Open: {latest[1]}")
                    print(f"   High: {latest[2]}")
                    print(f"   Low: {latest[3]}")
                    print(f"   Close: {latest[4]}")
                    print(f"   Volume: {latest[5]}")
            else:
                print("⚠️  No historical data available yet")

            print("\n" + "=" * 60)
            print("🎉 SUCCESS! YOU CAN FETCH LIVE OPTION CHAIN DATA!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Run: python upstox_options_fetcher.py")
            print("2. Data will include ATM to OTM15 for both CE and PE")
            print("3. Results will be saved to output/ directory")

        else:
            print(f"⚠️  Quote API response: {quote_data}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nThis might mean:")
        print("1. Access token is expired - run: python upstox_token_generator.py")
        print("2. Market is closed (market hours: Mon-Fri 9:15 AM - 3:30 PM IST)")
        print("3. Option contracts don't exist for this expiry/strike")
        print("4. Network connectivity issue")


if __name__ == '__main__':
    main()
