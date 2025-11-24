# Zerodha Option Chain Fetcher

Fetches 1-hour high/low data for ATM to OTM15 CE and PE options for NIFTY, BANKNIFTY, and SENSEX using Zerodha Kite Connect API.

## Features

- Fetches option chain data for NIFTY, BANKNIFTY, and SENSEX
- Automatically identifies ATM strike based on spot price
- Retrieves data for ATM + 15 OTM strikes for both CE and PE options (32 strikes total per index)
- Fetches 1-hour candlestick data (high/low)
- Exports data to CSV format
- Supports both historical and live data (configurable)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Zerodha API Credentials

1. Sign up for Kite Connect at https://kite.zerodha.com/
2. Create a new app to get your API Key and API Secret
3. Generate an access token (see Authentication section below)

### 3. Configure Credentials

**Option A: Environment Variables (Recommended)**

```bash
export ZERODHA_API_KEY="your_api_key"
export ZERODHA_ACCESS_TOKEN="your_access_token"
```

**Option B: Edit Script Directly**

Edit `zerodha_options_fetcher.py` and replace:
```python
API_KEY = 'your_api_key_here'
ACCESS_TOKEN = 'your_access_token_here'
```

## Authentication

Zerodha uses a multi-step authentication process:

### First Time Setup

1. **Get API Key and Secret** from Kite Connect dashboard

2. **Generate Request Token** - Visit this URL in browser (replace YOUR_API_KEY):
   ```
   https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY&v=3
   ```
   After login, you'll be redirected to a URL with a `request_token` parameter

3. **Generate Access Token** - Use this Python snippet:

```python
from kiteconnect import KiteConnect

api_key = "your_api_key"
api_secret = "your_api_secret"
request_token = "request_token_from_step_2"

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]

print(f"Access Token: {access_token}")
```

4. **Save Access Token** - Access tokens are valid until you logout or till 6 AM next day

## Usage

### Basic Usage

```bash
python zerodha_options_fetcher.py
```

This will:
- Fetch option chain data for NIFTY, BANKNIFTY, and SENSEX
- Get 1-hour high/low data for the last 5 trading days
- Export to CSV file with timestamp

### Output

The script generates a CSV file named `option_chain_data_YYYYMMDD_HHMMSS.csv` with columns:

- `symbol`: Underlying index (NIFTY/BANKNIFTY/SENSEX)
- `option_type`: CE or PE
- `strike`: Strike price
- `tradingsymbol`: Full trading symbol
- `expiry`: Option expiry date
- `instrument_token`: Zerodha instrument token
- `high_1h`: Highest price from 1-hour candles
- `low_1h`: Lowest price from 1-hour candles
- `num_candles`: Number of 1-hour candles in the period

### Example Output

```
symbol,option_type,strike,tradingsymbol,expiry,instrument_token,high_1h,low_1h,num_candles
NIFTY,CE,24000,NIFTY24DEC24000CE,2024-12-26,12345678,125.50,98.30,25
NIFTY,CE,24050,NIFTY24DEC24050CE,2024-12-26,12345679,110.20,85.10,25
...
```

## Customization

### Modify Date Range

In `zerodha_options_fetcher.py`, change:

```python
# Fetch last 10 days instead of 5
from_date = to_date - timedelta(days=10)
```

### Change Symbols

Modify the symbols list in `main()`:

```python
for symbol in ['NIFTY', 'BANKNIFTY']:  # Only NIFTY and BANKNIFTY
    results = fetcher.fetch_option_chain_data(symbol, from_date, to_date)
```

### Live Data Mode

For live data, modify the date range to current day:

```python
from_date = datetime.now().replace(hour=9, minute=15, second=0)  # Market open
to_date = datetime.now()
```

### Different Time Intervals

Change the interval parameter:

```python
# 5-minute candles
hist_data = self.get_historical_data(inst['instrument_token'], from_date, to_date, interval='5minute')

# 15-minute candles
hist_data = self.get_historical_data(inst['instrument_token'], from_date, to_date, interval='15minute')

# Daily candles
hist_data = self.get_historical_data(inst['instrument_token'], from_date, to_date, interval='day')
```

## Understanding Strike Selection

The script fetches:
- **ATM (At The Money)**: Strike closest to current spot price
- **OTM 1-15**: 15 strikes away from ATM

### For CE (Call Options):
- ATM: 24000 (if spot is 24012)
- OTM1: 24050
- OTM2: 24100
- ...
- OTM15: 24750

### For PE (Put Options):
- ATM: 24000 (if spot is 24012)
- OTM1: 23950
- OTM2: 23900
- ...
- OTM15: 23250

## Rate Limits

Zerodha API has rate limits:
- Historical data: 3 requests/second
- Quote API: 1 request/second

The script includes basic error handling but may need delays for large datasets.

## Troubleshooting

### "Invalid token" error
- Access tokens expire at 6 AM daily
- Generate a new access token

### "Too many requests" error
- API rate limit exceeded
- Add delays between requests

### No data returned
- Check if market is open (historical data requires past trading days)
- Verify expiry dates are correct
- Some far OTM options may not have traded

## Notes

- Historical data is available for the last 60 days for minute candles
- Options with no trading volume may not return data
- The script uses the nearest expiry by default
- SENSEX options trade on BFO exchange (BSE)
- NIFTY and BANKNIFTY trade on NFO exchange (NSE)

## Files

- `zerodha_options_fetcher.py` - Main script
- `requirements.txt` - Python dependencies
- `config_template.py` - Configuration template
- `README_zerodha_options.md` - This file

## License

For educational and personal use.
