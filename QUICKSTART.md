# Quick Start Guide

Get up and running with the Zerodha Option Chain Fetcher in 5 minutes.

**Mac Users:** See `MAC_SETUP.md` for detailed Mac-specific instructions including Zerodha app setup.

## Step 0: Navigate to the Project Folder

```bash
cd ~/Desktop/option_chain
```

All scripts and data will be managed from this folder. CSV output files will be saved to the `output/` subdirectory.

## Step 1: Install Dependencies

```bash
# For Mac users, use pip3
pip3 install -r requirements.txt

# For other systems
pip install -r requirements.txt
```

## Step 2: Get Zerodha Credentials

### Option A: Use the helper script (Recommended)

```bash
# For Mac users, use python3
python3 generate_access_token.py

# For other systems
python generate_access_token.py
```

Follow the prompts to:
1. Enter your API Key and Secret
2. Login through the browser
3. Copy the request token
4. Get your access token

### Option B: Manual process

1. Get API credentials from https://kite.zerodha.com/
2. Visit: `https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY&v=3`
3. Login and copy the `request_token` from redirect URL
4. Run this code:

```python
from kiteconnect import KiteConnect

kite = KiteConnect(api_key="your_key")
data = kite.generate_session("request_token", api_secret="your_secret")
print(data["access_token"])
```

## Step 3: Set Environment Variables

```bash
export ZERODHA_API_KEY='your_api_key'
export ZERODHA_ACCESS_TOKEN='your_access_token'
```

## Step 4: Run the Fetcher

```bash
# For Mac users, use python3
python3 zerodha_options_fetcher.py

# For other systems
python zerodha_options_fetcher.py
```

This will:
- Fetch option data for NIFTY, BANKNIFTY, and SENSEX
- Get ATM to OTM15 strikes for CE and PE
- Retrieve 1-hour high/low data
- Export to CSV file

## Output

You'll get a CSV file saved in the `output/` folder, named `option_chain_data_YYYYMMDD_HHMMSS.csv` with:

| Column | Description |
|--------|-------------|
| symbol | Index name (NIFTY/BANKNIFTY/SENSEX) |
| option_type | CE or PE |
| strike | Strike price |
| tradingsymbol | Full option symbol |
| expiry | Expiry date |
| instrument_token | Zerodha token |
| high_1h | Highest price from 1-hour candles |
| low_1h | Lowest price from 1-hour candles |
| num_candles | Number of candles fetched |

## Examples

See `example_usage.py` for:
- Fetching specific indices
- Live data fetching
- Custom analysis
- CE vs PE comparisons

```bash
python example_usage.py
```

## Common Issues

**"Invalid token" error**
- Access tokens expire at 6 AM daily
- Run `generate_access_token.py` again

**No data returned**
- Ensure you're fetching data for past trading days
- Check if options for selected expiry exist

**Rate limit errors**
- Zerodha limits: 3 historical requests/second
- Script includes basic error handling

## Daily Usage

Access tokens expire daily. For daily use:

1. Create a script to auto-generate tokens:
```bash
# Morning routine (before 9:15 AM)
python generate_access_token.py
source zerodha_credentials.txt  # or export manually
python zerodha_options_fetcher.py
```

2. Or set up a cron job for automated fetching

## Next Steps

- Read `README_zerodha_options.md` for detailed documentation
- Explore `example_usage.py` for advanced use cases
- Modify `zerodha_options_fetcher.py` for custom logic

## Files Overview

```
~/Desktop/option_chain/
├── zerodha_options_fetcher.py    # Main script
├── generate_access_token.py      # Helper for authentication
├── example_usage.py               # Usage examples
├── requirements.txt               # Dependencies
├── config_template.py             # Config template
├── .gitignore                     # Git ignore file
├── QUICKSTART.md                  # This file
├── README_zerodha_options.md      # Full documentation
└── output/                        # CSV files will be saved here
```

## Support

- Zerodha API Docs: https://kite.trade/docs/connect/v3/
- KiteConnect Python: https://github.com/zerodhatech/pykiteconnect

Happy Trading! 📈
