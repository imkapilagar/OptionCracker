"""
Test live market option chain fetching
"""

import os
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

def main():
    # Load credentials
    API_KEY = 'mmfof9xckmsvdyyk'
    ACCESS_TOKEN = 'NdCCam6BMNMYUlMuZ6pTzGmdpYqvcfiq'

    print("="*60)
    print("LIVE MARKET OPTION CHAIN TEST")
    print(f"Time: {datetime.now()}")
    print("="*60)

    try:
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(ACCESS_TOKEN)

        # Test 1: Get NIFTY spot price
        print("\n1. Testing NIFTY spot price fetch...")
        try:
            quote = kite.quote(['NSE:NIFTY 50'])
            nifty_price = quote['NSE:NIFTY 50']['last_price']
            print(f"✅ NIFTY 50 Spot Price: {nifty_price}")
        except Exception as e:
            print(f"❌ Failed to get spot price: {e}")
            print("\n⚠️  Your access token might be expired!")
            print("Run: python generate_access_token.py")
            return

        # Test 2: Get option instruments
        print("\n2. Fetching NFO instruments...")
        instruments = kite.instruments('NFO')
        print(f"✅ Got {len(instruments)} NFO instruments")

        # Test 3: Find current ATM options
        print("\n3. Finding ATM options for NIFTY...")
        step = 50
        atm_strike = round(nifty_price / step) * step
        print(f"   ATM Strike: {atm_strike}")

        # Get options for nearest expiry
        nifty_options = [i for i in instruments if i['name'] == 'NIFTY' and i['instrument_type'] in ['CE', 'PE']]
        expiries = sorted(set(opt['expiry'] for opt in nifty_options))
        nearest_expiry = expiries[0] if expiries else None
        print(f"   Nearest Expiry: {nearest_expiry}")

        # Find ATM CE and PE
        atm_ce = [opt for opt in nifty_options if opt['strike'] == atm_strike and opt['instrument_type'] == 'CE' and opt['expiry'] == nearest_expiry]
        atm_pe = [opt for opt in nifty_options if opt['strike'] == atm_strike and opt['instrument_type'] == 'PE' and opt['expiry'] == nearest_expiry]

        if atm_ce and atm_pe:
            print(f"\n4. Found ATM options:")
            print(f"   CE: {atm_ce[0]['tradingsymbol']}")
            print(f"   PE: {atm_pe[0]['tradingsymbol']}")

            # Test 4: Get live quotes for ATM options
            print(f"\n5. Fetching live quotes...")
            ce_key = f"NFO:{atm_ce[0]['tradingsymbol']}"
            pe_key = f"NFO:{atm_pe[0]['tradingsymbol']}"

            quotes = kite.quote([ce_key, pe_key])

            print(f"\n✅ ATM CE ({atm_ce[0]['tradingsymbol']}):")
            print(f"   LTP: {quotes[ce_key]['last_price']}")
            print(f"   Volume: {quotes[ce_key]['volume']}")

            print(f"\n✅ ATM PE ({atm_pe[0]['tradingsymbol']}):")
            print(f"   LTP: {quotes[pe_key]['last_price']}")
            print(f"   Volume: {quotes[pe_key]['volume']}")

            # Test 5: Get historical data (1-hour candles for today)
            print(f"\n6. Fetching 1-hour historical data for today...")
            today = datetime.now().date()
            from_date = datetime.combine(today, datetime.min.time())
            to_date = datetime.now()

            hist_data = kite.historical_data(
                instrument_token=atm_ce[0]['instrument_token'],
                from_date=from_date,
                to_date=to_date,
                interval='60minute'
            )

            if hist_data:
                print(f"✅ Got {len(hist_data)} candles for today")
                print(f"\n   Latest candle:")
                latest = hist_data[-1]
                print(f"   Time: {latest['date']}")
                print(f"   Open: {latest['open']}")
                print(f"   High: {latest['high']}")
                print(f"   Low: {latest['low']}")
                print(f"   Close: {latest['close']}")
            else:
                print("⚠️  No historical data available yet")

            print("\n" + "="*60)
            print("🎉 SUCCESS! YOU CAN FETCH LIVE OPTION CHAIN DATA!")
            print("="*60)
            print("\nNext steps:")
            print("1. Use zerodha_options_fetcher.py to fetch full option chain")
            print("2. Data will include ATM to OTM15 for both CE and PE")
            print("3. Results will be saved to output/ directory")

        else:
            print("⚠️  Could not find ATM options for current expiry")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nThis might mean:")
        print("1. Access token is expired - run: python generate_access_token.py")
        print("2. Market is closed (market hours: Mon-Fri 9:15 AM - 3:30 PM IST)")
        print("3. Network connectivity issue")

if __name__ == '__main__':
    main()
