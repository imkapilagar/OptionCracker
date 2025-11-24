# Mac Setup Guide

Quick setup guide specifically for Mac users.

## Step 1: Install Python 3 (if not already installed)

```bash
# Check if Python 3 is installed
python3 --version

# If not installed, install it using Homebrew
brew install python3
```

## Step 2: Navigate to Project Folder

```bash
cd ~/Desktop/option_chain
```

## Step 3: Create Virtual Environment (RECOMMENDED)

**If you get "externally-managed-environment" errors, use a virtual environment:**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies (inside venv)
pip install -r requirements.txt
```

**See `SETUP_VENV.md` for detailed virtual environment instructions.**

### Alternative: Install Without Virtual Environment

**IMPORTANT: Use `pip3` on Mac, NOT `pip` or `brew`**

```bash
pip3 install --user -r requirements.txt
```

This will install:
- kiteconnect (Zerodha API library)
- pandas (Data manipulation)
- python-dateutil (Date utilities)

## Step 4: Create Zerodha Kite Connect App

1. Go to https://kite.zerodha.com/
2. Login with your Zerodha credentials
3. Click on "Create new app"
4. Fill in the form:

   **Type:** Select "Connect" (500 credits for 30 days)

   **App name:** Option Chain (or any name you like)

   **Zerodha Client ID:** Your Zerodha client ID (e.g., OP9095)

   **Redirect URL:** `http://127.0.0.1`

   **Postback URL:** `http://127.0.0.1` (or leave empty)

   **Description:** Fetch Option chain data

5. Click "Create"
6. You'll get:
   - **API Key** (like: xxxxxxxxxxxxxxxx)
   - **API Secret** (keep this secure!)

## Step 5: Generate Access Token

Run the helper script:

```bash
python3 generate_access_token.py
```

Follow the prompts:

1. **Enter API Key and Secret** from Step 4
2. **Browser will open** - Login with your Zerodha credentials
3. **Browser will redirect** to a URL like:
   ```
   http://127.0.0.1/?request_token=abc123xyz&action=login&status=success
   ```
4. **Browser will show "Unable to connect"** - THIS IS NORMAL!
5. **Copy the request_token** from the URL bar (the part after `request_token=`)
6. **Paste it** into the terminal when prompted
7. **Save credentials** when asked (y/n)

## Step 6: Set Environment Variables

### Option A: For current session only

```bash
export ZERODHA_API_KEY='your_api_key_here'
export ZERODHA_ACCESS_TOKEN='your_access_token_here'
```

### Option B: Permanent (recommended)

Add to your `~/.zshrc` file:

```bash
echo "export ZERODHA_API_KEY='your_api_key_here'" >> ~/.zshrc
echo "export ZERODHA_ACCESS_TOKEN='your_access_token_here'" >> ~/.zshrc
source ~/.zshrc
```

## Step 7: Run the Option Chain Fetcher

```bash
python3 zerodha_options_fetcher.py
```

This will:
- Fetch option data for NIFTY, BANKNIFTY, and SENSEX
- Get ATM to OTM15 strikes for CE and PE options
- Retrieve 1-hour high/low data
- Save CSV to `output/` folder

## Common Mac-Specific Issues

### "command not found: pip"
**Solution:** Use `pip3` instead of `pip` on Mac

### "command not found: python"
**Solution:** Use `python3` instead of `python` on Mac

### "No module named 'kiteconnect'"
**Solution:** Run `pip3 install -r requirements.txt` first

### Permission denied errors
**Solution:** Try with user flag:
```bash
pip3 install --user -r requirements.txt
```

### SSL Certificate errors
**Solution:** Update certificates:
```bash
pip3 install --upgrade certifi
```

## Daily Usage

Access tokens expire at 6 AM IST daily. Each morning:

```bash
cd ~/Desktop/option_chain

# Regenerate access token
python3 generate_access_token.py

# Update environment variable
export ZERODHA_ACCESS_TOKEN='new_token_here'

# Run the fetcher
python3 zerodha_options_fetcher.py
```

## Understanding the Redirect URL

The redirect URL `http://127.0.0.1` is a **local address** that points to your own computer. Here's why it works:

1. When you login to Zerodha, it redirects to this URL with the request_token
2. Since nothing is running on `127.0.0.1`, the browser shows "can't connect"
3. **This is intentional!** We just need the token from the URL, not a working webpage
4. You manually copy the token from the URL bar
5. The script uses it to generate your access token

Think of it as a way to "catch" the token that Zerodha sends back after login.

## What to Do Next

Once setup is complete:

1. Check `example_usage.py` for different use cases
2. Modify `zerodha_options_fetcher.py` for custom logic
3. Find CSV outputs in `~/Desktop/option_chain/output/`

## Need Help?

- Zerodha API Docs: https://kite.trade/docs/connect/v3/
- KiteConnect Python: https://github.com/zerodhatech/pykiteconnect
- Check `README_zerodha_options.md` for detailed documentation
