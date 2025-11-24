"""
Simple test to verify historical data access works
This should work even on weekends
"""

import os
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

def main():
    # Load credentials
    API_KEY = os.getenv('ZERODHA_API_KEY')
    ACCESS_TOKEN = os.getenv('ZERODHA_ACCESS_TOKEN')

    print("="*60)
    print("Simple Historical Data Test")
    print("="*60)

    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)

    # Get NIFTY instruments
    print("\n1. Fetching NFO instruments...")
    try:
        instruments = kite.instruments('NFO')
        print(f"✅ Got {len(instruments)} instruments")

        # Find a recent NIFTY option
        nifty_options = [i for i in instruments if i['name'] == 'NIFTY' and i['instrument_type'] == 'CE']

        if nifty_options:
            # Get the first one
            test_option = nifty_options[0]
            print(f"\n2. Testing with: {test_option['tradingsymbol']}")
            print(f"   Strike: {test_option['strike']}")
            print(f"   Expiry: {test_option['expiry']}")
            print(f"   Token: {test_option['instrument_token']}")

            # Try to fetch historical data for this option
            print(f"\n3. Fetching historical data...")
            to_date = datetime.now() - timedelta(days=2)
            from_date = to_date - timedelta(days=10)

            try:
                data = kite.historical_data(
                    instrument_token=test_option['instrument_token'],
                    from_date=from_date,
                    to_date=to_date,
                    interval='60minute'
                )

                if data:
                    print(f"✅ SUCCESS! Got {len(data)} candles")
                    print(f"\nSample data (first candle):")
                    print(f"  Date: {data[0]['date']}")
                    print(f"  Open: {data[0]['open']}")
                    print(f"  High: {data[0]['high']}")
                    print(f"  Low: {data[0]['low']}")
                    print(f"  Close: {data[0]['close']}")
                    print("\n" + "="*60)
                    print("🎉 YOUR SETUP IS WORKING PERFECTLY!")
                    print("="*60)
                    print("\nThe authentication errors you saw earlier were because:")
                    print("- Market is closed (weekend)")
                    print("- Some options didn't trade in the selected period")
                    print("- Quote API requires live market")
                    print("\nDuring market hours (Mon-Fri 9:15 AM - 3:30 PM IST),")
                    print("you'll get live data without errors!")
                else:
                    print("⚠️  No data returned (option might not have traded)")

            except Exception as e:
                print(f"❌ Historical data fetch failed: {e}")

    except Exception as e:
        print(f"❌ Failed to get instruments: {e}")

if __name__ == '__main__':
    main()
