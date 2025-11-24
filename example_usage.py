"""
Example usage of Zerodha Option Chain Fetcher
Demonstrates different use cases and configurations
"""

import os
from datetime import datetime, timedelta
from zerodha_options_fetcher import OptionChainFetcher

def example_1_basic_usage():
    """Example 1: Basic usage - fetch data for all indices"""
    print("\n" + "="*60)
    print("Example 1: Basic Usage")
    print("="*60)

    # Setup credentials
    api_key = os.getenv('ZERODHA_API_KEY')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    # Initialize fetcher
    fetcher = OptionChainFetcher(api_key, access_token)

    # Fetch last 5 days of data
    to_date = datetime.now()
    from_date = to_date - timedelta(days=5)

    # Fetch for all symbols
    all_results = []
    for symbol in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
        results = fetcher.fetch_option_chain_data(symbol, from_date, to_date)
        all_results.extend(results)

    # Export to CSV
    fetcher.export_to_csv(all_results, 'example1_all_indices.csv')


def example_2_single_index():
    """Example 2: Fetch data for single index only"""
    print("\n" + "="*60)
    print("Example 2: Single Index (NIFTY only)")
    print("="*60)

    api_key = os.getenv('ZERODHA_API_KEY')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    fetcher = OptionChainFetcher(api_key, access_token)

    # Fetch last 3 days for NIFTY only
    to_date = datetime.now()
    from_date = to_date - timedelta(days=3)

    results = fetcher.fetch_option_chain_data('NIFTY', from_date, to_date)
    fetcher.export_to_csv(results, 'example2_nifty_only.csv')


def example_3_today_data():
    """Example 3: Fetch today's data only (live trading session)"""
    print("\n" + "="*60)
    print("Example 3: Today's Data (Live Session)")
    print("="*60)

    api_key = os.getenv('ZERODHA_API_KEY')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    fetcher = OptionChainFetcher(api_key, access_token)

    # Set date range to today's trading session
    to_date = datetime.now()
    from_date = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)

    print(f"Fetching data from {from_date} to {to_date}")

    results = fetcher.fetch_option_chain_data('NIFTY', from_date, to_date)
    fetcher.export_to_csv(results, 'example3_today_live.csv')


def example_4_custom_analysis():
    """Example 4: Custom analysis on fetched data"""
    print("\n" + "="*60)
    print("Example 4: Custom Analysis")
    print("="*60)

    api_key = os.getenv('ZERODHA_API_KEY')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    fetcher = OptionChainFetcher(api_key, access_token)

    to_date = datetime.now()
    from_date = to_date - timedelta(days=5)

    results = fetcher.fetch_option_chain_data('BANKNIFTY', from_date, to_date)

    # Analyze the data
    print("\n" + "="*60)
    print("Analysis Results")
    print("="*60)

    # Find options with highest volatility (high-low range)
    for result in results:
        if result['high_1h'] and result['low_1h']:
            result['range'] = result['high_1h'] - result['low_1h']
            result['range_pct'] = (result['range'] / result['low_1h']) * 100

    # Sort by range percentage
    sorted_results = sorted(results, key=lambda x: x.get('range_pct', 0), reverse=True)

    print("\nTop 10 Most Volatile Options (by range %):")
    print(f"{'Symbol':<15} {'Strike':<8} {'Type':<4} {'Range':<10} {'Range %':<10}")
    print("-" * 60)

    for i, result in enumerate(sorted_results[:10], 1):
        print(f"{result['tradingsymbol']:<15} {result['strike']:<8} "
              f"{result['option_type']:<4} {result.get('range', 0):<10.2f} "
              f"{result.get('range_pct', 0):<10.2f}%")

    # Export with analysis
    fetcher.export_to_csv(sorted_results, 'example4_with_analysis.csv')


def example_5_ce_pe_comparison():
    """Example 5: Compare CE and PE options at same strikes"""
    print("\n" + "="*60)
    print("Example 5: CE vs PE Comparison")
    print("="*60)

    api_key = os.getenv('ZERODHA_API_KEY')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    fetcher = OptionChainFetcher(api_key, access_token)

    to_date = datetime.now()
    from_date = to_date - timedelta(days=5)

    results = fetcher.fetch_option_chain_data('NIFTY', from_date, to_date)

    # Group by strike
    strikes_data = {}
    for result in results:
        strike = result['strike']
        if strike not in strikes_data:
            strikes_data[strike] = {'CE': None, 'PE': None}
        strikes_data[strike][result['option_type']] = result

    # Display comparison
    print("\nCE vs PE Comparison at Each Strike:")
    print(f"{'Strike':<8} {'CE High':<10} {'CE Low':<10} {'PE High':<10} {'PE Low':<10}")
    print("-" * 60)

    for strike in sorted(strikes_data.keys()):
        ce = strikes_data[strike].get('CE', {})
        pe = strikes_data[strike].get('PE', {})

        ce_high = ce.get('high_1h', 0) if ce else 0
        ce_low = ce.get('low_1h', 0) if ce else 0
        pe_high = pe.get('high_1h', 0) if pe else 0
        pe_low = pe.get('low_1h', 0) if pe else 0

        print(f"{strike:<8} {ce_high:<10.2f} {ce_low:<10.2f} "
              f"{pe_high:<10.2f} {pe_low:<10.2f}")


def main():
    """Run all examples"""

    # Check credentials
    if not os.getenv('ZERODHA_API_KEY') or not os.getenv('ZERODHA_ACCESS_TOKEN'):
        print("⚠️  Please set ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN environment variables")
        print("\nRun:")
        print("  export ZERODHA_API_KEY='your_key'")
        print("  export ZERODHA_ACCESS_TOKEN='your_token'")
        return

    # Menu
    print("\n" + "="*60)
    print("Zerodha Option Chain Fetcher - Examples")
    print("="*60)
    print("\n1. Basic Usage - All Indices")
    print("2. Single Index (NIFTY only)")
    print("3. Today's Live Data")
    print("4. Custom Analysis")
    print("5. CE vs PE Comparison")
    print("6. Run All Examples")
    print("0. Exit")

    choice = input("\nSelect example (0-6): ").strip()

    examples = {
        '1': example_1_basic_usage,
        '2': example_2_single_index,
        '3': example_3_today_data,
        '4': example_4_custom_analysis,
        '5': example_5_ce_pe_comparison,
    }

    if choice == '0':
        print("Goodbye!")
        return
    elif choice == '6':
        for func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Invalid choice!")


if __name__ == '__main__':
    main()
