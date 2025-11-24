# Upstox API Setup Guide

## Step 1: Get API Credentials

1. Visit https://upstox.com/developer/
2. Login with your Upstox account
3. Create a new app:
   - App Name: "Option Chain Fetcher"
   - Redirect URL: `http://127.0.0.1:5000/callback`
4. Note down your:
   - **API Key**
   - **API Secret**

## Step 2: Install Upstox Python SDK

```bash
pip install upstox-python-sdk
```

## Step 3: Generate Access Token

Run the token generator script (I'll create this for you)

## Step 4: Fetch Option Chain Data

Use the Upstox version of the option chain fetcher

## Key Differences from Zerodha

- **Authentication**: OAuth 2.0 (similar to Zerodha)
- **Token validity**: Tokens expire daily (similar to Zerodha)
- **Data format**: Slightly different JSON structure
- **Symbol names**: Different format (e.g., "NIFTY" vs "NIFTY 50")

## API Rate Limits

- Market data: Generous limits for retail users
- Historical data: Available for subscribed users
- WebSocket: Real-time streaming available

## Next Steps

1. Get your Upstox API credentials
2. I'll create the token generator
3. I'll adapt the option chain fetcher for Upstox
4. Test live market data fetching

Would you like me to proceed with Upstox setup?
