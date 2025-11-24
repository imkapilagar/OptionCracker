"""
Track LOW of option strikes from 11:30 to 12:30
Fetches data every 30 seconds and tracks the lowest price for each strike
"""

import requests
import pandas as pd
from datetime import datetime, time
import os
import time as time_module

def fetch_option_chain_snapshot(access_token, symbol='NIFTY', expiry_date='2025-11-25'):
    """Fetch current option chain snapshot"""

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    symbol_map = {
        'NIFTY': 'NSE_INDEX|Nifty 50',
        'BANKNIFTY': 'NSE_INDEX|Nifty Bank',
    }

    instrument_key = symbol_map.get(symbol, 'NSE_INDEX|Nifty 50')

    url = 'https://api.upstox.com/v2/option/chain'
    params = {
        'instrument_key': instrument_key,
        'expiry_date': expiry_date
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return None

    data = response.json()
    if data['status'] != 'success':
        return None

    chain_data = data['data']
    if not chain_data:
        return None

    # Get spot price and ATM
    spot_price = chain_data[0].get('underlying_spot_price', 0)
    step = 50 if symbol in ['NIFTY', 'FINNIFTY'] else 100
    atm_strike = round(spot_price / step) * step

    # Collect all strikes data
    strikes_data = {}

    for strike_data in chain_data:
        strike = strike_data['strike_price']

        # CE: ATM to OTM15
        if atm_strike <= strike <= atm_strike + (15 * step):
            ce_option = strike_data.get('call_options', {})
            if ce_option and ce_option.get('market_data'):
                key = f"{symbol}_{strike}_CE"
                strikes_data[key] = {
                    'symbol': symbol,
                    'strike': strike,
                    'option_type': 'CE',
                    'ltp': ce_option['market_data'].get('ltp', 0),
                    'instrument_key': ce_option.get('instrument_key', '')
                }

        # PE: ATM to OTM15
        if atm_strike - (15 * step) <= strike <= atm_strike:
            pe_option = strike_data.get('put_options', {})
            if pe_option and pe_option.get('market_data'):
                key = f"{symbol}_{strike}_PE"
                strikes_data[key] = {
                    'symbol': symbol,
                    'strike': strike,
                    'option_type': 'PE',
                    'ltp': pe_option['market_data'].get('ltp', 0),
                    'instrument_key': pe_option.get('instrument_key', '')
                }

    return strikes_data, spot_price


def track_lows(access_token, start_time_str='11:30', end_time_str='12:30', symbols=['NIFTY'], interval_seconds=30):
    """
    Track lows for option strikes between start and end time

    Args:
        access_token: Upstox access token
        start_time_str: Start time (HH:MM format)
        end_time_str: End time (HH:MM format)
        symbols: List of symbols to track
        interval_seconds: Polling interval in seconds
    """

    # Parse times
    start_hour, start_min = map(int, start_time_str.split(':'))
    end_hour, end_min = map(int, end_time_str.split(':'))

    start_time = time(start_hour, start_min)
    end_time = time(end_hour, end_min)

    print("="*100)
    print(f"OPTION LOW TRACKER")
    print("="*100)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Tracking Period: {start_time_str} to {end_time_str}")
    print(f"Polling Interval: {interval_seconds} seconds")
    print(f"Current Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*100)

    # Wait until start time
    while datetime.now().time() < start_time:
        current = datetime.now().strftime('%H:%M:%S')
        print(f"\rWaiting for {start_time_str}... Current time: {current}", end='', flush=True)
        time_module.sleep(1)

    print(f"\n\n{'='*100}")
    print(f"✅ TRACKING STARTED at {datetime.now().strftime('%H:%M:%S')}")
    print("="*100)

    # Dictionary to track lows for each strike
    lows_tracker = {}
    fetch_count = 0

    # Start tracking
    while datetime.now().time() < end_time:
        fetch_count += 1
        current_time = datetime.now().strftime('%H:%M:%S')

        print(f"\n[{current_time}] Fetch #{fetch_count}...", flush=True)

        for symbol in symbols:
            try:
                strikes_data, spot_price = fetch_option_chain_snapshot(access_token, symbol)

                if not strikes_data:
                    print(f"  ❌ {symbol}: No data")
                    continue

                print(f"  ✅ {symbol}: Spot={spot_price:.2f}, Strikes={len(strikes_data)}")

                # Update lows
                for key, data in strikes_data.items():
                    ltp = data['ltp']

                    if key not in lows_tracker:
                        # First time seeing this strike
                        lows_tracker[key] = {
                            'symbol': data['symbol'],
                            'strike': data['strike'],
                            'option_type': data['option_type'],
                            'instrument_key': data['instrument_key'],
                            'low': ltp,
                            'first_ltp': ltp,
                            'last_ltp': ltp,
                            'samples': 1
                        }
                    else:
                        # Update low if current is lower
                        if ltp < lows_tracker[key]['low']:
                            lows_tracker[key]['low'] = ltp
                        lows_tracker[key]['last_ltp'] = ltp
                        lows_tracker[key]['samples'] += 1

            except Exception as e:
                print(f"  ❌ {symbol}: Error - {e}")

        # Check if we're past end time
        if datetime.now().time() >= end_time:
            break

        # Sleep until next fetch
        time_module.sleep(interval_seconds)

    print(f"\n\n{'='*100}")
    print(f"✅ TRACKING COMPLETED at {datetime.now().strftime('%H:%M:%S')}")
    print("="*100)
    print(f"Total fetches: {fetch_count}")
    print(f"Total strikes tracked: {len(lows_tracker)}")

    return lows_tracker


def save_lows_to_csv(lows_data, start_time, end_time, output_dir='output'):
    """Save tracked lows to CSV"""

    if not lows_data:
        print("\n❌ No data to save")
        return

    # Convert to list
    results = []
    for key, data in lows_data.items():
        results.append({
            'symbol': data['symbol'],
            'strike': data['strike'],
            'option_type': data['option_type'],
            'instrument_key': data['instrument_key'],
            'low': data['low'],
            'first_ltp': data['first_ltp'],
            'last_ltp': data['last_ltp'],
            'samples': data['samples']
        })

    # Create DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values(['symbol', 'option_type', 'strike'])

    # Create output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_dir)
    os.makedirs(output_path, exist_ok=True)

    # Create filename
    date_str = datetime.now().strftime('%Y%m%d')
    time_range = f"{start_time.replace(':', '')}_to_{end_time.replace(':', '')}"
    filename = f'option_lows_{date_str}_{time_range}.csv'
    full_path = os.path.join(output_path, filename)

    # Save to CSV
    df.to_csv(full_path, index=False)

    print(f"\n✅ Data saved to: {full_path}")
    print(f"   Total records: {len(results)}")

    # Print summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print("="*100)

    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        print(f"\n{symbol}:")
        print(f"  CE options: {len(symbol_df[symbol_df['option_type'] == 'CE'])}")
        print(f"  PE options: {len(symbol_df[symbol_df['option_type'] == 'PE'])}")
        print(f"  Total: {len(symbol_df)}")

    # Show sample
    print(f"\n{'='*100}")
    print("SAMPLE DATA (First 10 strikes)")
    print("="*100)
    print(df[['symbol', 'strike', 'option_type', 'low', 'first_ltp', 'last_ltp']].head(10).to_string(index=False))

    return full_path


def main():
    # Load credentials
    try:
        with open('upstox_credentials.txt', 'r') as f:
            for line in f:
                if line.startswith('ACCESS_TOKEN='):
                    ACCESS_TOKEN = line.split('=')[1].strip()
    except FileNotFoundError:
        print("❌ upstox_credentials.txt not found!")
        return

    # Configuration
    START_TIME = '11:30'
    END_TIME = '12:30'
    SYMBOLS = ['NIFTY']  # Add 'BANKNIFTY' if needed
    INTERVAL = 30  # Fetch every 30 seconds

    # Track lows
    lows_data = track_lows(
        ACCESS_TOKEN,
        start_time_str=START_TIME,
        end_time_str=END_TIME,
        symbols=SYMBOLS,
        interval_seconds=INTERVAL
    )

    # Save to CSV
    if lows_data:
        save_lows_to_csv(lows_data, START_TIME, END_TIME)
    else:
        print("\n❌ No data tracked")


if __name__ == '__main__':
    main()
