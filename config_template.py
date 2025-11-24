"""
Configuration Template for Zerodha API
Copy this file to config.py and fill in your credentials
"""

# Zerodha API Credentials
# Get these from https://kite.zerodha.com/
ZERODHA_API_KEY = "your_api_key_here"
ZERODHA_API_SECRET = "your_api_secret_here"
ZERODHA_ACCESS_TOKEN = "your_access_token_here"

# Optional: Request token (needed to generate access token)
ZERODHA_REQUEST_TOKEN = ""

# Data fetch settings
HISTORICAL_DAYS = 5  # Number of days to fetch historical data
INTERVAL = "60minute"  # Data interval (60minute for 1-hour candles)

# Symbols to track
SYMBOLS = ['NIFTY', 'BANKNIFTY', 'SENSEX']

# Output settings
OUTPUT_DIR = "output"
CSV_FILENAME_PREFIX = "option_chain_data"
