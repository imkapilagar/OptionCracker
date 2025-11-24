"""
Track LOW of option strikes from 11:30 to 12:30
Updates CSV every 2 minutes with current lows
"""

import requests
import pandas as pd
from datetime import datetime, time
import os
import time as time_module
import sys

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
        return None, None

    data = response.json()
    if data['status'] != 'success':
        return None, None

    chain_data = data['data']
    if not chain_data:
        return None, None

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


def save_current_lows(lows_data, filename, output_dir='output', is_final=False):
    """Save current lows to CSV"""

    if not lows_data:
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
            'current_ltp': data['last_ltp'],
            'first_ltp': data['first_ltp'],
            'samples': data['samples'],
            'last_updated': datetime.now().strftime('%H:%M:%S')
        })

    # Create DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values(['symbol', 'option_type', 'strike'])

    # Create output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_dir)
    os.makedirs(output_path, exist_ok=True)

    # Full path
    full_path = os.path.join(output_path, filename)

    # If final save, add special strikes nearest to 50
    if is_final:
        # Find CE and PE strikes with LOW nearest to 50
        ce_df = df[df['option_type'] == 'CE'].copy()
        pe_df = df[df['option_type'] == 'PE'].copy()

        # Calculate distance from 50
        ce_df['distance_from_50'] = abs(ce_df['low'] - 50)
        pe_df['distance_from_50'] = abs(pe_df['low'] - 50)

        # Find nearest
        nearest_ce = ce_df.nsmallest(1, 'distance_from_50')
        nearest_pe = pe_df.nsmallest(1, 'distance_from_50')

        # Add a blank row and header
        blank_row = pd.DataFrame([{
            'symbol': '',
            'strike': '',
            'option_type': '',
            'instrument_key': '',
            'low': '',
            'current_ltp': '',
            'first_ltp': '',
            'samples': '',
            'last_updated': ''
        }])

        header_row = pd.DataFrame([{
            'symbol': 'SPECIAL',
            'strike': 'STRIKES',
            'option_type': 'NEAREST',
            'instrument_key': 'TO',
            'low': 'Rs 50',
            'current_ltp': '',
            'first_ltp': '',
            'samples': '',
            'last_updated': ''
        }])

        # Combine
        final_df = pd.concat([df, blank_row, header_row, nearest_ce, nearest_pe], ignore_index=True)
    else:
        final_df = df

    # Save to CSV
    final_df.to_csv(full_path, index=False)

    return full_path


def track_lows(access_token, start_time_str='11:30', end_time_str='12:30', symbols=['NIFTY'],
               interval_seconds=30, save_interval_minutes=2):
    """
    Track lows for option strikes between start and end time
    Saves CSV every save_interval_minutes
    """

    # Parse times
    start_hour, start_min = map(int, start_time_str.split(':'))
    end_hour, end_min = map(int, end_time_str.split(':'))

    start_time = time(start_hour, start_min)
    end_time = time(end_hour, end_min)

    print("="*100)
    print(f"OPTION LOW TRACKER (Incremental CSV Updates)")
    print("="*100)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Tracking Period: {start_time_str} to {end_time_str}")
    print(f"Polling Interval: {interval_seconds} seconds")
    print(f"CSV Update Interval: {save_interval_minutes} minutes")
    print(f"Current Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*100)
    sys.stdout.flush()

    # Wait until start time
    while datetime.now().time() < start_time:
        current = datetime.now().strftime('%H:%M:%S')
        print(f"\rWaiting for {start_time_str}... Current time: {current}", end='', flush=True)
        time_module.sleep(1)

    print(f"\n\n{'='*100}")
    print(f"✅ TRACKING STARTED at {datetime.now().strftime('%H:%M:%S')}")
    print("="*100)
    sys.stdout.flush()

    # Dictionary to track lows
    lows_tracker = {}
    fetch_count = 0
    last_save_time = datetime.now()

    # CSV filename
    date_str = datetime.now().strftime('%Y%m%d')
    time_range = f"{start_time_str.replace(':', '')}_to_{end_time_str.replace(':', '')}"
    csv_filename = f'option_lows_{date_str}_{time_range}.csv'

    # Start tracking
    while datetime.now().time() < end_time:
        fetch_count += 1
        current_time = datetime.now().strftime('%H:%M:%S')

        print(f"\n[{current_time}] Fetch #{fetch_count}")
        sys.stdout.flush()

        for symbol in symbols:
            try:
                strikes_data, spot_price = fetch_option_chain_snapshot(access_token, symbol)

                if not strikes_data:
                    print(f"  ❌ {symbol}: No data")
                    sys.stdout.flush()
                    continue

                print(f"  ✅ {symbol}: Spot={spot_price:.2f}, Strikes={len(strikes_data)}")
                sys.stdout.flush()

                # Update lows
                for key, data in strikes_data.items():
                    ltp = data['ltp']

                    if key not in lows_tracker:
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
                        if ltp < lows_tracker[key]['low']:
                            lows_tracker[key]['low'] = ltp
                        lows_tracker[key]['last_ltp'] = ltp
                        lows_tracker[key]['samples'] += 1

            except Exception as e:
                print(f"  ❌ {symbol}: Error - {e}")
                sys.stdout.flush()

        # Check if it's time to save CSV
        time_since_save = (datetime.now() - last_save_time).total_seconds() / 60
        if time_since_save >= save_interval_minutes:
            print(f"\n  💾 Saving CSV update...")
            sys.stdout.flush()
            saved_path = save_current_lows(lows_tracker, csv_filename)
            print(f"  ✅ CSV updated: {saved_path}")
            print(f"     Records: {len(lows_tracker)}")
            sys.stdout.flush()
            last_save_time = datetime.now()

        # Show current lowest strikes
        if lows_tracker:
            # Show ATM options
            atm_ce = [v for k, v in lows_tracker.items() if v['option_type'] == 'CE' and 'ATM' in k or v['strike'] == round(spot_price / 50) * 50]
            atm_pe = [v for k, v in lows_tracker.items() if v['option_type'] == 'PE' and 'ATM' in k or v['strike'] == round(spot_price / 50) * 50]

            if atm_ce:
                ce = atm_ce[0]
                print(f"     ATM CE Low: ₹{ce['low']:.2f} (Current: ₹{ce['last_ltp']:.2f})")
            if atm_pe:
                pe = atm_pe[0]
                print(f"     ATM PE Low: ₹{pe['low']:.2f} (Current: ₹{pe['last_ltp']:.2f})")
            sys.stdout.flush()

        # Check if past end time
        if datetime.now().time() >= end_time:
            break

        # Sleep until next fetch
        time_module.sleep(interval_seconds)

    # Final save with special strikes
    print(f"\n\n{'='*100}")
    print(f"✅ TRACKING COMPLETED at {datetime.now().strftime('%H:%M:%S')}")
    print("="*100)
    print(f"Total fetches: {fetch_count}")
    print(f"Total strikes tracked: {len(lows_tracker)}")
    sys.stdout.flush()

    print(f"\n💾 Saving final CSV with special strikes nearest to ₹50...")
    sys.stdout.flush()
    final_path = save_current_lows(lows_tracker, csv_filename, is_final=True)
    print(f"✅ Final CSV saved: {final_path}")

    # Find and display the special strikes
    results = []
    for key, data in lows_tracker.items():
        results.append(data)

    df = pd.DataFrame(results)
    ce_df = df[df['option_type'] == 'CE'].copy()
    pe_df = df[df['option_type'] == 'PE'].copy()

    ce_df['distance_from_50'] = abs(ce_df['low'] - 50)
    pe_df['distance_from_50'] = abs(pe_df['low'] - 50)

    nearest_ce = ce_df.nsmallest(1, 'distance_from_50').iloc[0]
    nearest_pe = pe_df.nsmallest(1, 'distance_from_50').iloc[0]

    print(f"\n{'='*100}")
    print("SPECIAL STRIKES NEAREST TO ₹50")
    print("="*100)
    print(f"\n📌 CE Strike: {nearest_ce['strike']:.0f} | LOW: ₹{nearest_ce['low']:.2f} | Distance from ₹50: ₹{nearest_ce['distance_from_50']:.2f}")
    print(f"📌 PE Strike: {nearest_pe['strike']:.0f} | LOW: ₹{nearest_pe['low']:.2f} | Distance from ₹50: ₹{nearest_pe['distance_from_50']:.2f}")
    print("="*100)
    sys.stdout.flush()

    return lows_tracker, csv_filename


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
    SYMBOLS = ['NIFTY']
    INTERVAL = 30  # Fetch every 30 seconds
    SAVE_INTERVAL = 2  # Save CSV every 2 minutes

    # Track lows
    lows_data, csv_filename = track_lows(
        ACCESS_TOKEN,
        start_time_str=START_TIME,
        end_time_str=END_TIME,
        symbols=SYMBOLS,
        interval_seconds=INTERVAL,
        save_interval_minutes=SAVE_INTERVAL
    )

    # Print summary
    if lows_data:
        results = []
        for key, data in lows_data.items():
            results.append(data)

        df = pd.DataFrame(results)
        df = df.sort_values(['option_type', 'strike'])

        print(f"\n\n{'='*100}")
        print("FINAL SUMMARY - TOP 5 LOWEST CE OPTIONS")
        print("="*100)
        ce_df = df[df['option_type'] == 'CE'].nsmallest(5, 'low')
        print(ce_df[['strike', 'low', 'first_ltp', 'last_ltp', 'samples']].to_string(index=False))

        print(f"\n{'='*100}")
        print("FINAL SUMMARY - TOP 5 LOWEST PE OPTIONS")
        print("="*100)
        pe_df = df[df['option_type'] == 'PE'].nsmallest(5, 'low')
        print(pe_df[['strike', 'low', 'first_ltp', 'last_ltp', 'samples']].to_string(index=False))

        print(f"\n{'='*100}")
        print(f"✅ All data saved to: output/{csv_filename}")
        print("="*100)


if __name__ == '__main__':
    main()
