"""
Detailed diagnostic test to understand the API issue
"""

import os
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

def main():
    API_KEY = os.getenv('ZERODHA_API_KEY')
    ACCESS_TOKEN = os.getenv('ZERODHA_ACCESS_TOKEN')

    print("="*60)
    print("Detailed API Diagnostic Test")
    print("="*60)
    print(f"\nAPI Key: {API_KEY}")
    print(f"Token (first 20): {ACCESS_TOKEN[:20]}...")

    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)

    # Test 1: Try fetching historical data for NIFTY index (not options)
    print("\n" + "="*60)
    print("Test 1: NIFTY 50 Index Historical Data")
    print("="*60)

    try:
        # Get NIFTY 50 instrument token
        instruments = kite.instruments('NSE')
        nifty = [i for i in instruments if i['tradingsymbol'] == 'NIFTY 50'][0]
        print(f"NIFTY 50 Token: {nifty['instrument_token']}")

        to_date = datetime(2025, 11, 21)  # Thursday
        from_date = datetime(2025, 11, 14)  # Previous Thursday

        print(f"Date range: {from_date.date()} to {to_date.date()}")

        data = kite.historical_data(
            instrument_token=nifty['instrument_token'],
            from_date=from_date,
            to_date=to_date,
            interval='day'
        )

        if data:
            print(f"✅ SUCCESS! Got {len(data)} candles for NIFTY index")
            print(f"Latest: {data[-1]}")
        else:
            print("⚠️  No data returned")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Check account permissions
    print("\n" + "="*60)
    print("Test 2: Check Account Info")
    print("="*60)

    try:
        profile = kite.profile()
        print(f"User: {profile.get('user_name', 'N/A')}")
        print(f"Email: {profile.get('email', 'N/A')}")
        print(f"User Type: {profile.get('user_type', 'N/A')}")
        print(f"Broker: {profile.get('broker', 'N/A')}")

        # Check exchanges
        exchanges = profile.get('exchanges', [])
        print(f"Exchanges: {exchanges}")

        # Check products
        products = profile.get('products', [])
        print(f"Products: {products}")

        # Check order types
        order_types = profile.get('order_types', [])
        print(f"Order Types: {order_types}")

    except Exception as e:
        print(f"❌ FAILED: {e}")

    # Test 3: Try with a very recent option that definitely traded
    print("\n" + "="*60)
    print("Test 3: Recent ATM Option Historical Data")
    print("="*60)

    try:
        instruments = kite.instruments('NFO')

        # Find current week's ATM-ish NIFTY option
        # Use strike around 24000-24500 range which should have traded
        nifty_ce = [i for i in instruments
                    if i['name'] == 'NIFTY'
                    and i['instrument_type'] == 'CE'
                    and i['strike'] == 24000.0
                    and i['expiry'].year == 2025
                    and i['expiry'].month == 11]

        if nifty_ce:
            option = nifty_ce[0]
            print(f"Testing: {option['tradingsymbol']}")
            print(f"Token: {option['instrument_token']}")
            print(f"Strike: {option['strike']}")
            print(f"Expiry: {option['expiry']}")

            # Try last week's data
            to_date = datetime(2025, 11, 21)
            from_date = datetime(2025, 11, 18)

            print(f"Date range: {from_date.date()} to {to_date.date()}")

            data = kite.historical_data(
                instrument_token=option['instrument_token'],
                from_date=from_date,
                to_date=to_date,
                interval='60minute'
            )

            if data:
                print(f"✅ SUCCESS! Got {len(data)} candles")
                print(f"First candle: {data[0]}")
            else:
                print("⚠️  No data (option might not have traded)")

        else:
            print("Could not find suitable option")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Diagnosis Complete")
    print("="*60)

if __name__ == '__main__':
    main()
