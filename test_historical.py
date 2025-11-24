"""
Test script to fetch historical option chain data
Uses a specific date range to avoid market closed issues
"""

import os
from datetime import datetime, timedelta
from zerodha_options_fetcher import OptionChainFetcher

def main():
    # Load credentials
    API_KEY = os.getenv('ZERODHA_API_KEY', 'your_api_key_here')
    ACCESS_TOKEN = os.getenv('ZERODHA_ACCESS_TOKEN', 'your_access_token_here')

    if API_KEY == 'your_api_key_here' or ACCESS_TOKEN == 'your_access_token_here':
        print("⚠️  Please set your Zerodha API credentials")
        print("Run:")
        print("  export ZERODHA_API_KEY='your_key'")
        print("  export ZERODHA_ACCESS_TOKEN='your_token'")
        return

    # Initialize fetcher
    fetcher = OptionChainFetcher(API_KEY, ACCESS_TOKEN)

    # Use a specific date range - last Thursday (market was definitely open)
    # Go back 10 days to ensure we catch a trading day
    to_date = datetime.now() - timedelta(days=3)  # 3 days ago
    from_date = to_date - timedelta(days=7)        # 7 days before that

    print("="*60)
    print("Historical Option Chain Test")
    print("="*60)
    print(f"\nFetching data from {from_date.date()} to {to_date.date()}")
    print("Note: Using historical dates to avoid market closed issues\n")

    # Test with just NIFTY first
    all_results = []

    for symbol in ['NIFTY', 'BANKNIFTY']:
        print(f"\nTesting {symbol}...")
        try:
            results = fetcher.fetch_option_chain_data(symbol, from_date, to_date)
            all_results.extend(results)
            print(f"✅ Successfully fetched {len(results)} records for {symbol}")
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Export to CSV
    if all_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'test_historical_{timestamp}.csv'
        fetcher.export_to_csv(all_results, filename)
        print("\n" + "="*60)
        print("✅ TEST SUCCESSFUL!")
        print("="*60)
        print(f"Total records fetched: {len(all_results)}")
        print("\nYour setup is working correctly!")
        print("During market hours, you'll get live data.")
    else:
        print("\n" + "="*60)
        print("⚠️  No data fetched")
        print("="*60)
        print("This might be due to:")
        print("- Weekend/holiday period with no trading")
        print("- Options not traded in the selected date range")
        print("- API rate limits")
        print("\nTry running during market hours (Mon-Fri 9:15 AM - 3:30 PM IST)")


if __name__ == '__main__':
    main()
