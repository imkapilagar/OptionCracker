# Upstox Option Chain Fetcher

Complete setup guide for fetching live option chain data using Upstox API.

## 🚀 Quick Start Guide

### Step 1: Get Upstox API Credentials

1. Visit https://upstox.com/developer/
2. Login with your Upstox trading account
3. Click "Create App"
4. Fill in the details:
   - **App Name**: Option Chain Fetcher
   - **Redirect URL**: `http://127.0.0.1:5000/callback` (exactly this!)
   - **Description**: Fetching option chain data
5. Save and note down:
   - **API Key**
   - **API Secret**

### Step 2: Generate Access Token

Run the token generator script:

```bash
source venv/bin/activate
python upstox_token_generator.py
```

Follow the prompts:
1. Enter your API Key
2. Enter your API Secret
3. Browser will open - login to Upstox
4. After login, you'll be redirected to a URL (browser will show "Unable to connect" - THIS IS NORMAL!)
5. Copy the `code` parameter from the URL
6. Paste it in the terminal
7. Your access token will be generated and saved to `upstox_credentials.txt`

### Step 3: Test Connection

```bash
source venv/bin/activate
python test_upstox_connection.py
```

This will verify:
- ✅ Your credentials are valid
- ✅ You can fetch user profile
- ✅ You can get live NIFTY price

### Step 4: Test Live Market Data

```bash
source venv/bin/activate
python test_upstox_live_market.py
```

This will:
- Fetch NIFTY spot price
- Calculate ATM strike
- Get live quotes for ATM CE and PE
- Fetch 1-hour historical data

### Step 5: Fetch Full Option Chain

```bash
source venv/bin/activate
python upstox_options_fetcher.py
```

This will:
- Fetch option chain for NIFTY and BANKNIFTY
- Get ATM to OTM15 strikes for both CE and PE
- Fetch 1-hour high/low data
- Save results to `output/upstox_option_chain_YYYYMMDD_HHMMSS.csv`

## 📁 Files Created

### Token Generation
- `upstox_token_generator.py` - Interactive token generator
- `upstox_credentials.txt` - Saved credentials (auto-generated)

### Main Scripts
- `upstox_options_fetcher.py` - Main option chain fetcher
- `test_upstox_connection.py` - Basic connection test
- `test_upstox_live_market.py` - Live market data test

### Documentation
- `README_UPSTOX.md` - This file
- `upstox_setup_guide.md` - Additional setup notes

## 🎯 What Data You Get

The option chain fetcher provides:

- **Symbol**: NIFTY, BANKNIFTY, FINNIFTY
- **Option Type**: CE (Call) and PE (Put)
- **Strikes**: ATM to OTM15 (16 strikes per side)
- **Data Points**:
  - Strike price
  - Instrument key
  - Expiry date
  - 1-hour high
  - 1-hour low
  - Number of candles

## ⚙️ Configuration

### Supported Symbols
```python
symbols_to_fetch = ['NIFTY', 'BANKNIFTY']  # Add 'FINNIFTY' if needed
```

### Strike Range
Default: ATM to OTM15 (16 strikes each for CE and PE)
- NIFTY: 50-point steps
- BANKNIFTY: 100-point steps
- FINNIFTY: 50-point steps

### Time Interval
Default: 60-minute candles
Available: 1minute, 30minute, 60minute, 1day

## 🔧 Troubleshooting

### Access Token Expired
**Error**: `401 Unauthorized`

**Solution**:
```bash
python upstox_token_generator.py
```
Tokens expire at 6 AM IST daily.

### Market Closed
**Error**: No data available

**Solution**: Run during market hours (Mon-Fri 9:15 AM - 3:30 PM IST)

### Redirect URI Mismatch
**Error**: Invalid redirect_uri

**Solution**: Ensure your Upstox app settings have exactly: `http://127.0.0.1:5000/callback`

### Rate Limiting
**Error**: Too many requests

**Solution**: The fetcher includes 0.1s delay between API calls. If you still hit limits, increase the `time.sleep()` value in `upstox_options_fetcher.py`

## 📊 Output Format

CSV file with columns:
```
symbol,option_type,strike,instrument_key,expiry,high_1h,low_1h,num_candles
```

Example:
```
NIFTY,CE,24500,NSE_FO|NIFTY24NOV2450CE,2024-11-28,125.50,110.25,6
```

## 🔐 Security Notes

- Never commit `upstox_credentials.txt` to git
- Access tokens expire daily at 6 AM IST
- Keep your API Secret secure
- Don't share your access tokens

## 🆚 Upstox vs Zerodha

### Advantages of Upstox
- Easier authentication process
- Better API documentation
- More generous rate limits
- Supports FINNIFTY out of the box

### API Differences
- **Symbol format**: Different instrument key format
- **Historical data**: Different response structure
- **Expiry format**: YYMmmDD (e.g., 24NOV28)

## 📝 Daily Workflow

1. **Morning** (before 9:15 AM):
   ```bash
   python upstox_token_generator.py
   ```

2. **During Market Hours**:
   ```bash
   python upstox_options_fetcher.py
   ```

3. **Check Output**:
   ```bash
   ls -la output/
   ```

## 🚨 Common Issues

### Issue: Browser shows "Unable to connect"
**Status**: ✅ This is normal!
**Action**: Just copy the authorization code from the URL bar

### Issue: "Invalid authorization code"
**Cause**: Code already used or expired
**Solution**: Start over with `python upstox_token_generator.py`

### Issue: No historical data
**Cause**: Option contract didn't trade or market closed
**Solution**: Check if market is open, try different strikes

## 📞 Support

- Upstox API Docs: https://upstox.com/developer/api-documentation
- Upstox Support: https://support.upstox.com/

## 🎓 Next Steps

1. Run the option chain fetcher during market hours
2. Analyze the CSV output
3. Integrate with your trading strategy
4. Set up automated data collection (cron jobs)

---

**Happy Trading! 📈**
