"""
Fetch LIVE Option Chain Data from Upstox
Works during market hours!
"""

import requests
import pandas as pd
from datetime import datetime
import os

def fetch_live_option_chain(access_token, symbol='NIFTY', expiry_date='2025-11-25'):
    """
    Fetch live option chain data

    Args:
        access_token: Upstox access token
        symbol: NIFTY, BANKNIFTY, or FINNIFTY
        expiry_date: Expiry date in YYYY-MM-DD format
    """

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    # Symbol mapping
    symbol_map = {
        'NIFTY': 'NSE_INDEX|Nifty 50',
        'BANKNIFTY': 'NSE_INDEX|Nifty Bank',
        'FINNIFTY': 'NSE_INDEX|Nifty Fin Service'
    }

    instrument_key = symbol_map.get(symbol, 'NSE_INDEX|Nifty 50')

    print(f"\n{'='*100}")
    print(f"Fetching LIVE Option Chain for {symbol}")
    print(f"Expiry: {expiry_date}")
    print(f"Time: {datetime.now()}")
    print(f"{'='*100}")

    # Fetch option chain
    url = 'https://api.upstox.com/v2/option/chain'
    params = {
        'instrument_key': instrument_key,
        'expiry_date': expiry_date
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

    data = response.json()

    if data['status'] != 'success':
        print(f"❌ API Error: {data}")
        return None

    chain_data = data['data']

    if not chain_data:
        print("❌ No option chain data available")
        return None

    # Get spot price
    spot_price = chain_data[0].get('underlying_spot_price', 0)
    print(f"\n✅ {symbol} Spot Price: {spot_price}")

    # Calculate ATM
    step = 50 if symbol in ['NIFTY', 'FINNIFTY'] else 100
    atm_strike = round(spot_price / step) * step
    print(f"   ATM Strike: {atm_strike}")
    print(f"   Total Strikes Available: {len(chain_data)}")

    # Filter for ITM5 to OTM15 (21 strikes each side: 5 ITM + ATM + 15 OTM)
    ce_options = []
    pe_options = []

    for strike_data in chain_data:
        strike = strike_data['strike_price']

        # CE: ITM5 to OTM15 (ATM - 5 strikes below to ATM + 15 strikes above)
        # For CE, ITM is below ATM (lower strikes are in-the-money)
        if atm_strike - (5 * step) <= strike <= atm_strike + (15 * step):
            ce_option = strike_data.get('call_options', {})
            if ce_option and ce_option.get('market_data'):
                ce_options.append({
                    'symbol': symbol,
                    'expiry': expiry_date,
                    'strike': strike,
                    'option_type': 'CE',
                    'instrument_key': ce_option.get('instrument_key', ''),
                    'ltp': ce_option['market_data'].get('ltp', 0),
                    'volume': ce_option['market_data'].get('volume', 0),
                    'oi': ce_option['market_data'].get('oi', 0),
                    'bid_price': ce_option['market_data'].get('bid_price', 0),
                    'ask_price': ce_option['market_data'].get('ask_price', 0),
                    'iv': ce_option.get('option_greeks', {}).get('iv', 0),
                    'delta': ce_option.get('option_greeks', {}).get('delta', 0),
                    'gamma': ce_option.get('option_greeks', {}).get('gamma', 0),
                    'theta': ce_option.get('option_greeks', {}).get('theta', 0),
                    'vega': ce_option.get('option_greeks', {}).get('vega', 0),
                })

        # PE: ITM5 to OTM15 (ATM - 15 strikes below to ATM + 5 strikes above)
        # For PE, ITM is above ATM (higher strikes are in-the-money)
        if atm_strike - (15 * step) <= strike <= atm_strike + (5 * step):
            pe_option = strike_data.get('put_options', {})
            if pe_option and pe_option.get('market_data'):
                pe_options.append({
                    'symbol': symbol,
                    'expiry': expiry_date,
                    'strike': strike,
                    'option_type': 'PE',
                    'instrument_key': pe_option.get('instrument_key', ''),
                    'ltp': pe_option['market_data'].get('ltp', 0),
                    'volume': pe_option['market_data'].get('volume', 0),
                    'oi': pe_option['market_data'].get('oi', 0),
                    'bid_price': pe_option['market_data'].get('bid_price', 0),
                    'ask_price': pe_option['market_data'].get('ask_price', 0),
                    'iv': pe_option.get('option_greeks', {}).get('iv', 0),
                    'delta': pe_option.get('option_greeks', {}).get('delta', 0),
                    'gamma': pe_option.get('option_greeks', {}).get('gamma', 0),
                    'theta': pe_option.get('option_greeks', {}).get('theta', 0),
                    'vega': pe_option.get('option_greeks', {}).get('vega', 0),
                })

    # Combine CE and PE
    all_options = ce_options + pe_options

    print(f"\n✅ Fetched {len(ce_options)} CE options (ITM5 to OTM15)")
    print(f"✅ Fetched {len(pe_options)} PE options (ITM5 to OTM15)")
    print(f"✅ Total: {len(all_options)} options")

    return all_options, spot_price


def save_to_csv(data, symbol, output_dir='output'):
    """Save option chain data to CSV"""
    if not data:
        print("❌ No data to save")
        return

    # Create output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_dir)
    os.makedirs(output_path, exist_ok=True)

    # Create filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'live_option_chain_{symbol}_{timestamp}.csv'
    full_path = os.path.join(output_path, filename)

    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df = df.sort_values(['option_type', 'strike'])
    df.to_csv(full_path, index=False)

    print(f"\n✅ Data saved to: {full_path}")
    print(f"   Total records: {len(data)}")

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
        print("Run: python upstox_token_generator.py")
        return

    # Fetch option chains
    all_results = []

    # Symbols to fetch
    symbols_to_fetch = [
        {'symbol': 'NIFTY', 'expiry': '2025-11-25'},
        {'symbol': 'BANKNIFTY', 'expiry': '2025-11-25'},
    ]

    for config in symbols_to_fetch:
        symbol = config['symbol']
        expiry = config['expiry']

        try:
            options, spot_price = fetch_live_option_chain(ACCESS_TOKEN, symbol, expiry)

            if options:
                all_results.extend(options)

                # Also save individual symbol
                save_to_csv(options, symbol)

                print(f"\n{'='*100}")
                print(f"✅ {symbol} - Successfully fetched {len(options)} options")
                print(f"{'='*100}")
            else:
                print(f"\n❌ {symbol} - No data available")

        except Exception as e:
            print(f"\n❌ Error fetching {symbol}: {e}")
            import traceback
            traceback.print_exc()

    # Save combined data
    if all_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        combined_file = save_to_csv(all_results, f'ALL_{timestamp}')

        print(f"\n\n{'='*100}")
        print(f"🎉 SUCCESS! Live option chain data fetched and saved!")
        print(f"{'='*100}")
        print(f"\nTotal options fetched: {len(all_results)}")
        print(f"Combined file: {combined_file}")
    else:
        print("\n❌ No data fetched from any symbol")


if __name__ == '__main__':
    main()
