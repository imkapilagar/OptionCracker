"""
Upstox Option Chain Fetcher
Fetches 1-hour high/low data for ATM to OTM15 CE and PE options
Supports: NIFTY, BANKNIFTY, FINNIFTY
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class UpstoxOptionChainFetcher:
    def __init__(self, api_key, access_token):
        """Initialize Upstox API client"""
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = "https://api.upstox.com/v2"

        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        # Symbol mappings - Upstox uses different symbol formats
        self.symbols = {
            'NIFTY': {
                'instrument_key': 'NSE_INDEX|Nifty 50',
                'option_prefix': 'NSE_FO|NIFTY',
                'step': 50
            },
            'BANKNIFTY': {
                'instrument_key': 'NSE_INDEX|Nifty Bank',
                'option_prefix': 'NSE_FO|BANKNIFTY',
                'step': 100
            },
            'FINNIFTY': {
                'instrument_key': 'NSE_INDEX|Nifty Fin Service',
                'option_prefix': 'NSE_FO|FINNIFTY',
                'step': 50
            }
        }

    def get_spot_price(self, symbol):
        """Get current spot price of the index"""
        instrument_key = self.symbols[symbol]['instrument_key']

        url = f"{self.base_url}/market-quote/quotes"
        params = {'instrument_key': instrument_key}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Upstox API structure: data['instrument_key']['last_price']
            # Note: API returns key with colon, not pipe
            response_key = instrument_key.replace('|', ':')
            return data['data'][response_key]['last_price']
        except Exception as e:
            print(f"Error getting spot price: {e}")
            raise

    def get_atm_strike(self, spot_price, step):
        """Calculate ATM strike based on spot price"""
        return round(spot_price / step) * step

    def get_option_chain(self, symbol, expiry_date=None):
        """Get option chain data for a symbol"""
        url = f"{self.base_url}/option/chain"

        # For Upstox, we need the instrument key without option type
        instrument_key = self.symbols[symbol]['option_prefix']

        params = {'instrument_key': instrument_key}
        if expiry_date:
            params['expiry_date'] = expiry_date

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting option chain: {e}")
            return None

    def get_historical_data(self, instrument_key, from_date, to_date, interval='30minute'):
        """Fetch historical data for an instrument"""
        url = f"{self.base_url}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'success' and data['data']['candles']:
                # Convert to list of dicts for easier processing
                candles = []
                for candle in data['data']['candles']:
                    # Upstox format: [timestamp, open, high, low, close, volume, oi]
                    candles.append({
                        'date': datetime.fromtimestamp(candle[0] / 1000),  # Convert from ms
                        'open': candle[1],
                        'high': candle[2],
                        'low': candle[3],
                        'close': candle[4],
                        'volume': candle[5],
                        'oi': candle[6] if len(candle) > 6 else 0
                    })
                return candles
            return None
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def get_strikes_to_fetch(self, atm_strike, step, option_type):
        """Get list of strikes from ATM to OTM15"""
        strikes = [atm_strike]  # ATM

        if option_type == 'CE':
            # For CE, OTM is above ATM
            for i in range(1, 16):
                strikes.append(atm_strike + (i * step))
        else:  # PE
            # For PE, OTM is below ATM
            for i in range(1, 16):
                strikes.append(atm_strike - (i * step))

        return strikes

    def format_option_symbol(self, symbol, expiry, strike, option_type):
        """Format option symbol for Upstox
        Example: NSE_FO|NIFTY25DEC26100CE (monthly expiry)
        """
        # Format expiry: YYMMMM (e.g., 25DEC for Dec 2025)
        # Note: Upstox uses YY+MMM format for monthly expiries
        expiry_str = expiry.strftime('%y%b').upper()

        # Get the base symbol (without exchange)
        base_symbol = symbol

        # Construct the instrument key
        instrument_key = f"NSE_FO|{base_symbol}{expiry_str}{int(strike)}{option_type}"

        return instrument_key

    def get_nearest_expiry(self, symbol):
        """Get nearest monthly expiry date for the symbol"""
        # Upstox provides monthly expiries (last Thursday of the month)
        # For simplicity, using December 2025 monthly expiry
        # In production, you should fetch this from the instruments CSV or option chain API
        today = datetime.now()

        # Common monthly expiries for NIFTY/BANKNIFTY
        # Format: YYYY-MM-DD (last Thursday of month)
        monthly_expiries = [
            datetime(2025, 11, 27).date(),  # Nov 2025
            datetime(2025, 12, 30).date(),  # Dec 2025
            datetime(2026, 1, 27).date(),   # Jan 2026
        ]

        # Find nearest expiry
        for expiry in monthly_expiries:
            if expiry >= today.date():
                return expiry

        return monthly_expiries[-1]  # Fallback to last available

    def fetch_option_chain_data(self, symbol, from_date, to_date):
        """Fetch option chain data with 1-hour high/low"""
        print(f"\n{'='*60}")
        print(f"Processing {symbol}")
        print(f"{'='*60}")

        # Get spot price
        try:
            spot_price = self.get_spot_price(symbol)
            print(f"Spot Price: {spot_price}")
        except Exception as e:
            print(f"Error getting spot price: {e}")
            return []

        step = self.symbols[symbol]['step']
        atm_strike = self.get_atm_strike(spot_price, step)
        print(f"ATM Strike: {atm_strike}")

        # Get nearest expiry (you might want to get this from API)
        expiry_date = self.get_nearest_expiry(symbol)
        print(f"Expiry Date: {expiry_date}")

        results = []

        # Process CE options
        print("\nFetching CE options...")
        ce_strikes = self.get_strikes_to_fetch(atm_strike, step, 'CE')

        for strike in ce_strikes:
            instrument_key = self.format_option_symbol(symbol, expiry_date, strike, 'CE')
            print(f"  {instrument_key}...", end='')

            # Fetch historical data
            hist_data = self.get_historical_data(
                instrument_key,
                from_date.strftime('%Y-%m-%d'),
                to_date.strftime('%Y-%m-%d'),
                '60minute'
            )

            if hist_data and len(hist_data) > 0:
                # Calculate overall high/low from 1-hour candles
                highs = [candle['high'] for candle in hist_data]
                lows = [candle['low'] for candle in hist_data]

                results.append({
                    'symbol': symbol,
                    'option_type': 'CE',
                    'strike': strike,
                    'instrument_key': instrument_key,
                    'expiry': expiry_date,
                    'high_1h': max(highs) if highs else None,
                    'low_1h': min(lows) if lows else None,
                    'num_candles': len(hist_data)
                })
                print(f" ✓ High: {max(highs):.2f}, Low: {min(lows):.2f}")
            else:
                print(" ✗ No data")

            # Rate limiting - don't hit API too fast
            time.sleep(0.1)

        # Process PE options
        print("\nFetching PE options...")
        pe_strikes = self.get_strikes_to_fetch(atm_strike, step, 'PE')

        for strike in pe_strikes:
            instrument_key = self.format_option_symbol(symbol, expiry_date, strike, 'PE')
            print(f"  {instrument_key}...", end='')

            # Fetch historical data
            hist_data = self.get_historical_data(
                instrument_key,
                from_date.strftime('%Y-%m-%d'),
                to_date.strftime('%Y-%m-%d'),
                '60minute'
            )

            if hist_data and len(hist_data) > 0:
                # Calculate overall high/low from 1-hour candles
                highs = [candle['high'] for candle in hist_data]
                lows = [candle['low'] for candle in hist_data]

                results.append({
                    'symbol': symbol,
                    'option_type': 'PE',
                    'strike': strike,
                    'instrument_key': instrument_key,
                    'expiry': expiry_date,
                    'high_1h': max(highs) if highs else None,
                    'low_1h': min(lows) if lows else None,
                    'num_candles': len(hist_data)
                })
                print(f" ✓ High: {max(highs):.2f}, Low: {min(lows):.2f}")
            else:
                print(" ✗ No data")

            # Rate limiting
            time.sleep(0.1)

        return results

    def export_to_csv(self, data, filename, output_dir='output'):
        """Export data to CSV"""
        if not data:
            print("No data to export")
            return

        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, output_dir)

        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)

        # Full path for the CSV file
        full_path = os.path.join(output_path, filename)

        df = pd.DataFrame(data)
        df.to_csv(full_path, index=False)
        print(f"\n✓ Data exported to {full_path}")
        print(f"Total records: {len(data)}")


def main():
    # Load credentials from environment variables or file
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
            pass

    if not API_KEY or not ACCESS_TOKEN:
        print("⚠️  Please set your Upstox API credentials")
        print("Run: python upstox_token_generator.py")
        print("Or set environment variables: UPSTOX_API_KEY and UPSTOX_ACCESS_TOKEN")
        return

    # Initialize fetcher
    fetcher = UpstoxOptionChainFetcher(API_KEY, ACCESS_TOKEN)

    # Date range for historical data (today)
    to_date = datetime.now()
    from_date = to_date - timedelta(days=1)  # Last 1 day

    print(f"Fetching data from {from_date.date()} to {to_date.date()}")

    # Fetch data for all symbols
    all_results = []
    symbols_to_fetch = ['NIFTY', 'BANKNIFTY']  # Add 'FINNIFTY' if needed

    print(f"\nSymbols to fetch: {', '.join(symbols_to_fetch)}")

    for symbol in symbols_to_fetch:
        try:
            results = fetcher.fetch_option_chain_data(symbol, from_date, to_date)
            all_results.extend(results)
            print(f"✅ Successfully fetched {len(results)} records for {symbol}")
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            continue

    # Export to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'upstox_option_chain_{timestamp}.csv'
    fetcher.export_to_csv(all_results, filename)


if __name__ == '__main__':
    main()
