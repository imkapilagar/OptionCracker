"""
Zerodha Option Chain Fetcher
Fetches 1-hour high/low data for ATM to OTM15 CE and PE options
Supports: NIFTY, BANKNIFTY, SENSEX
"""

import os
import csv
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import pandas as pd

class OptionChainFetcher:
    def __init__(self, api_key, access_token):
        """Initialize Kite Connect"""
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

        # Symbol mappings
        self.symbols = {
            'NIFTY': {'instrument_token': None, 'exchange': 'NSE', 'tradingsymbol': 'NIFTY 50', 'step': 50},
            'BANKNIFTY': {'instrument_token': None, 'exchange': 'NSE', 'tradingsymbol': 'NIFTY BANK', 'step': 100},
            'SENSEX': {'instrument_token': None, 'exchange': 'BSE', 'tradingsymbol': 'SENSEX', 'step': 100}
        }

    def get_instrument_token(self, symbol):
        """Get instrument token for the underlying index"""
        instruments = self.kite.instruments(self.symbols[symbol]['exchange'])

        for instrument in instruments:
            if instrument['tradingsymbol'] == self.symbols[symbol]['tradingsymbol']:
                return instrument['instrument_token']

        return None

    def get_spot_price(self, symbol):
        """Get current spot price of the index"""
        instrument_token = self.get_instrument_token(symbol)
        if not instrument_token:
            raise ValueError(f"Could not find instrument token for {symbol}")

        quote = self.kite.quote([f"{self.symbols[symbol]['exchange']}:{self.symbols[symbol]['tradingsymbol']}"])
        key = f"{self.symbols[symbol]['exchange']}:{self.symbols[symbol]['tradingsymbol']}"

        return quote[key]['last_price']

    def get_atm_strike(self, spot_price, step):
        """Calculate ATM strike based on spot price"""
        return round(spot_price / step) * step

    def get_option_instruments(self, symbol, expiry_date=None):
        """Get all option instruments for a symbol"""
        exchange = 'NFO' if symbol in ['NIFTY', 'BANKNIFTY'] else 'BFO'
        instruments = self.kite.instruments(exchange)

        # Filter options for the symbol
        options = [
            inst for inst in instruments
            if inst['name'] == symbol and inst['instrument_type'] in ['CE', 'PE']
        ]

        # If expiry date not specified, use nearest expiry
        if not expiry_date:
            expiries = sorted(set(inst['expiry'] for inst in options))
            if expiries:
                expiry_date = expiries[0]

        # Filter by expiry
        options = [inst for inst in options if inst['expiry'] == expiry_date]

        return options, expiry_date

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

    def get_historical_data(self, instrument_token, from_date, to_date, interval='60minute'):
        """Fetch historical data for an instrument"""
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            return data
        except Exception as e:
            print(f"Error fetching data for token {instrument_token}: {e}")
            return None

    def fetch_option_chain_data(self, symbol, from_date, to_date):
        """Fetch option chain data with 1-hour high/low"""
        print(f"\n{'='*60}")
        print(f"Processing {symbol}")
        print(f"{'='*60}")

        # Get spot price (for historical, we'll use a sample date quote)
        try:
            spot_price = self.get_spot_price(symbol)
        except:
            # Fallback for historical testing
            spot_prices = {'NIFTY': 24000, 'BANKNIFTY': 52000, 'SENSEX': 79000}
            spot_price = spot_prices.get(symbol, 24000)
            print(f"Using fallback spot price: {spot_price}")

        step = self.symbols[symbol]['step']
        atm_strike = self.get_atm_strike(spot_price, step)

        print(f"Spot Price: {spot_price}")
        print(f"ATM Strike: {atm_strike}")

        # Get option instruments
        options, expiry_date = self.get_option_instruments(symbol)
        print(f"Expiry Date: {expiry_date}")

        results = []

        # Process CE options
        print("\nFetching CE options...")
        ce_strikes = self.get_strikes_to_fetch(atm_strike, step, 'CE')
        for strike in ce_strikes:
            # Find matching instrument
            matching_inst = [
                opt for opt in options
                if opt['strike'] == strike and opt['instrument_type'] == 'CE'
            ]

            if matching_inst:
                inst = matching_inst[0]
                print(f"  {inst['tradingsymbol']}...", end='')

                # Fetch historical data
                hist_data = self.get_historical_data(
                    inst['instrument_token'],
                    from_date,
                    to_date
                )

                if hist_data:
                    # Calculate overall high/low from 1-hour candles
                    highs = [candle['high'] for candle in hist_data]
                    lows = [candle['low'] for candle in hist_data]

                    results.append({
                        'symbol': symbol,
                        'option_type': 'CE',
                        'strike': strike,
                        'tradingsymbol': inst['tradingsymbol'],
                        'expiry': expiry_date,
                        'instrument_token': inst['instrument_token'],
                        'high_1h': max(highs) if highs else None,
                        'low_1h': min(lows) if lows else None,
                        'num_candles': len(hist_data)
                    })
                    print(f" ✓ High: {max(highs):.2f}, Low: {min(lows):.2f}")
                else:
                    print(" ✗ No data")

        # Process PE options
        print("\nFetching PE options...")
        pe_strikes = self.get_strikes_to_fetch(atm_strike, step, 'PE')
        for strike in pe_strikes:
            # Find matching instrument
            matching_inst = [
                opt for opt in options
                if opt['strike'] == strike and opt['instrument_type'] == 'PE'
            ]

            if matching_inst:
                inst = matching_inst[0]
                print(f"  {inst['tradingsymbol']}...", end='')

                # Fetch historical data
                hist_data = self.get_historical_data(
                    inst['instrument_token'],
                    from_date,
                    to_date
                )

                if hist_data:
                    # Calculate overall high/low from 1-hour candles
                    highs = [candle['high'] for candle in hist_data]
                    lows = [candle['low'] for candle in hist_data]

                    results.append({
                        'symbol': symbol,
                        'option_type': 'PE',
                        'strike': strike,
                        'tradingsymbol': inst['tradingsymbol'],
                        'expiry': expiry_date,
                        'instrument_token': inst['instrument_token'],
                        'high_1h': max(highs) if highs else None,
                        'low_1h': min(lows) if lows else None,
                        'num_candles': len(hist_data)
                    })
                    print(f" ✓ High: {max(highs):.2f}, Low: {min(lows):.2f}")
                else:
                    print(" ✗ No data")

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
    # Load credentials from environment variables or config
    API_KEY = os.getenv('ZERODHA_API_KEY', 'your_api_key_here')
    ACCESS_TOKEN = os.getenv('ZERODHA_ACCESS_TOKEN', 'your_access_token_here')

    if API_KEY == 'your_api_key_here' or ACCESS_TOKEN == 'your_access_token_here':
        print("⚠️  Please set your Zerodha API credentials")
        print("Set environment variables: ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN")
        print("Or edit this script to add credentials directly")
        return

    # Initialize fetcher
    fetcher = OptionChainFetcher(API_KEY, ACCESS_TOKEN)

    # Date range for historical data (last 5 trading days)
    to_date = datetime.now()
    from_date = to_date - timedelta(days=5)

    print(f"Fetching data from {from_date.date()} to {to_date.date()}")

    # Fetch data for all symbols
    # Note: SENSEX requires BSE access and may not work with all API subscriptions
    # Remove 'SENSEX' from the list if you get authentication errors
    all_results = []
    symbols_to_fetch = ['NIFTY', 'BANKNIFTY']  # SENSEX removed - requires BSE access

    print(f"\nSymbols to fetch: {', '.join(symbols_to_fetch)}")
    print("Note: SENSEX is skipped by default (requires BSE access)")
    print("To enable SENSEX, edit this script and add 'SENSEX' to symbols_to_fetch list\n")

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
    filename = f'option_chain_data_{timestamp}.csv'
    fetcher.export_to_csv(all_results, filename)


if __name__ == '__main__':
    main()
