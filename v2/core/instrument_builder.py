"""
Instrument Builder for Options Breakout Tracker V2

Handles:
- Fetching current spot prices
- Calculating ATM strikes
- Building instrument key lists for WebSocket subscription
- Finding nearest weekly/monthly expiry
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import requests


class InstrumentBuilder:
    """
    Builds instrument keys for option subscriptions.

    Instrument key format:
    - Index: NSE_INDEX|Nifty 50, BSE_INDEX|SENSEX, NSE_INDEX|Nifty Bank
    - Options: NSE_FO|NIFTY25JAN26100CE (SYMBOL + YYMMM + STRIKE + CE/PE)
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        self._expiry_cache: Dict[str, str] = {}

    def get_spot_price(self, index_key: str) -> float:
        """
        Fetch current spot price from Upstox API.

        Args:
            index_key: Index instrument key (e.g., "NSE_INDEX|Nifty 50")

        Returns:
            Current spot price
        """
        url = 'https://api.upstox.com/v2/market-quote/quotes'
        params = {'instrument_key': index_key}

        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        # Response key format: NSE_INDEX:Nifty 50 (| replaced with :)
        response_key = index_key.replace('|', ':')
        return data['data'][response_key]['last_price']

    def get_atm_strike(self, spot_price: float, step: int) -> float:
        """
        Calculate ATM strike from spot price.

        Args:
            spot_price: Current spot price
            step: Strike step size (50 for NIFTY, 100 for BANKNIFTY/SENSEX)

        Returns:
            ATM strike price
        """
        return round(spot_price / step) * step

    def get_nearest_expiry(self, index_key: str) -> str:
        """
        Find nearest weekly expiry for symbol.

        Args:
            index_key: Index instrument key

        Returns:
            Expiry date string in YYYY-MM-DD format
        """
        # Check cache first
        if index_key in self._expiry_cache:
            cached_date = self._expiry_cache[index_key]
            # Validate cache is still valid (expiry not passed)
            if datetime.strptime(cached_date, '%Y-%m-%d').date() >= datetime.now().date():
                return cached_date

        today = datetime.now()

        # Check next 30 days for valid expiry
        for i in range(30):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            url = 'https://api.upstox.com/v2/option/chain'
            params = {
                'instrument_key': index_key,
                'expiry_date': date_str
            }

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        self._expiry_cache[index_key] = date_str
                        return date_str
            except Exception:
                continue

        # Fallback to next Thursday
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        fallback = (today + timedelta(days=days_until_thursday)).strftime('%Y-%m-%d')
        return fallback

    def format_option_key(
        self,
        option_prefix: str,
        expiry: str,
        strike: float,
        option_type: str
    ) -> str:
        """
        Format instrument key for option.

        Format: NSE_FO|NIFTY25JAN26100CE
        Where: PREFIX + YY + MMM + STRIKE + CE/PE

        Args:
            option_prefix: Option prefix (e.g., "NSE_FO|NIFTY")
            expiry: Expiry date in YYYY-MM-DD format
            strike: Strike price
            option_type: "CE" or "PE"

        Returns:
            Formatted instrument key
        """
        # Parse expiry date and format
        expiry_dt = datetime.strptime(expiry, '%Y-%m-%d')

        # Format: YYMMM (e.g., 25JAN for January 2025)
        expiry_str = expiry_dt.strftime('%y%b').upper()

        return f"{option_prefix}{expiry_str}{int(strike)}{option_type}"

    def build_subscription_list(
        self,
        symbol: str,
        index_key: str,
        option_prefix: str,
        strike_step: int,
        strikes_range: int = 10
    ) -> Tuple[List[str], Dict]:
        """
        Build complete list of instrument keys for a symbol.

        Fetches actual instrument keys from option chain API (numeric codes like NSE_FO|46051).

        Args:
            symbol: Symbol name (NIFTY, SENSEX, BANKNIFTY)
            index_key: Index instrument key
            option_prefix: Option prefix for instrument keys (unused, kept for compatibility)
            strike_step: Strike step size
            strikes_range: Number of strikes above and below ATM

        Returns:
            Tuple of (instrument_keys, metadata)
        """
        # Get current data
        spot_price = self.get_spot_price(index_key)
        atm_strike = self.get_atm_strike(spot_price, strike_step)
        expiry = self.get_nearest_expiry(index_key)

        # Fetch option chain to get actual instrument keys
        url = 'https://api.upstox.com/v2/option/chain'
        params = {
            'instrument_key': index_key,
            'expiry_date': expiry
        }

        response = requests.get(url, headers=self.headers, params=params, timeout=15)
        response.raise_for_status()
        chain_data = response.json().get('data', [])

        if not chain_data:
            raise ValueError(f"No option chain data for {symbol} expiry {expiry}")

        # Build strike range to filter
        min_strike = atm_strike - (strikes_range * strike_step)
        max_strike = atm_strike + (strikes_range * strike_step)

        # Extract instrument keys from option chain
        instrument_keys = []
        strike_map = {'CE': {}, 'PE': {}}
        strikes = []

        for entry in chain_data:
            strike = entry.get('strike_price')
            if strike is None:
                continue

            # Filter to our strike range
            if strike < min_strike or strike > max_strike:
                continue

            strikes.append(strike)

            # Get CE instrument key
            ce_data = entry.get('call_options', {})
            ce_key = ce_data.get('instrument_key')
            if ce_key:
                instrument_keys.append(ce_key)
                strike_map['CE'][strike] = ce_key

            # Get PE instrument key
            pe_data = entry.get('put_options', {})
            pe_key = pe_data.get('instrument_key')
            if pe_key:
                instrument_keys.append(pe_key)
                strike_map['PE'][strike] = pe_key

        strikes = sorted(set(strikes))

        metadata = {
            'symbol': symbol,
            'spot_price': spot_price,
            'atm_strike': atm_strike,
            'expiry': expiry,
            'strike_step': strike_step,
            'strikes': strikes,
            'strike_map': strike_map,
            'instrument_count': len(instrument_keys)
        }

        return instrument_keys, metadata

    def build_all_subscriptions(
        self,
        symbols_config: Dict
    ) -> Tuple[List[str], Dict[str, Dict]]:
        """
        Build subscription lists for all enabled symbols.

        Args:
            symbols_config: Dictionary of symbol configurations

        Returns:
            Tuple of (all_instrument_keys, metadata_by_symbol)
        """
        all_instruments = []
        all_metadata = {}

        for symbol, config in symbols_config.items():
            if not config.enabled:
                continue

            instruments, metadata = self.build_subscription_list(
                symbol=symbol,
                index_key=config.index_key,
                option_prefix=config.option_prefix,
                strike_step=config.strike_step,
                strikes_range=config.strikes_range
            )

            all_instruments.extend(instruments)
            all_metadata[symbol] = metadata

            print(f"  {symbol}: {len(instruments)} instruments "
                  f"(ATM: {metadata['atm_strike']}, Expiry: {metadata['expiry']})")

        return all_instruments, all_metadata

    def get_instrument_info(self, instrument_key: str) -> Optional[Dict]:
        """
        Parse instrument key to extract symbol, strike, and option type.

        Args:
            instrument_key: Instrument key (e.g., "NSE_FO|NIFTY25JAN26100CE")

        Returns:
            Dict with symbol, strike, option_type or None if parsing fails
        """
        try:
            # Split on | to get exchange and details
            parts = instrument_key.split('|')
            if len(parts) != 2:
                return None

            exchange = parts[0]
            details = parts[1]

            # Determine symbol based on prefix
            if details.startswith('NIFTY') and not details.startswith('NIFTYBANK'):
                symbol = 'NIFTY'
                remainder = details[5:]  # Remove 'NIFTY'
            elif details.startswith('BANKNIFTY'):
                symbol = 'BANKNIFTY'
                remainder = details[9:]  # Remove 'BANKNIFTY'
            elif details.startswith('SENSEX'):
                symbol = 'SENSEX'
                remainder = details[6:]  # Remove 'SENSEX'
            else:
                return None

            # Extract option type (last 2 chars)
            option_type = remainder[-2:]
            if option_type not in ['CE', 'PE']:
                return None

            # Extract strike (numeric part before CE/PE)
            # Format: 25JAN26100CE -> find where numbers start after month
            strike_and_type = remainder[5:]  # Skip expiry (25JAN)
            strike = int(strike_and_type[:-2])  # Remove CE/PE

            return {
                'exchange': exchange,
                'symbol': symbol,
                'strike': strike,
                'option_type': option_type,
                'instrument_key': instrument_key
            }

        except (ValueError, IndexError):
            return None
