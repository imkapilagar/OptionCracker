# Daily Workflow Guide

Quick reference for daily use of the Option Chain Fetcher.

## 🌅 Morning Routine (Before Market Hours)

Open Terminal and run these commands:

### Step 1: Navigate to Project Folder

```bash
cd ~/Desktop/option_chain
```

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

### Step 3: Generate New Access Token

```bash
python generate_access_token.py
```

**Follow the prompts:**
1. Enter your API Key: `mmfof9xckmsvdyyk`
2. Enter your API Secret: `[your secret]`
3. Browser will open - Login to Zerodha
4. Browser will show "Unable to connect" - **THIS IS NORMAL!**
5. Copy the `request_token` from the URL bar
6. Paste it into the terminal
7. Save credentials when asked (y)

### Step 4: Set Environment Variables

After the script completes, it will show you the export commands. Copy and run them:

```bash
export ZERODHA_API_KEY='mmfof9xckmsvdyyk'
export ZERODHA_ACCESS_TOKEN='[new_token_from_step_3]'
```

**Or use the saved credentials file:**

```bash
# View saved credentials
cat zerodha_credentials.txt

# Manually copy and export the values shown
```

### Step 5: Run the Option Chain Fetcher

```bash
python zerodha_options_fetcher.py
```

This will:
- Fetch option data for NIFTY, BANKNIFTY, and SENSEX
- Get ATM to OTM15 strikes for both CE and PE options
- Retrieve 1-hour high/low data
- Save CSV to `output/` folder

---

## 📋 One-Command Quick Start

Copy and paste this entire block (after activating venv):

```bash
cd ~/Desktop/option_chain && \
source venv/bin/activate && \
python generate_access_token.py
```

Then after getting your token, run:

```bash
export ZERODHA_API_KEY='mmfof9xckmsvdyyk' && \
export ZERODHA_ACCESS_TOKEN='paste_your_new_token_here' && \
python zerodha_options_fetcher.py
```

---

## 🔄 If You Already Have Today's Token

If you already generated the token earlier today and just want to fetch data:

```bash
cd ~/Desktop/option_chain
source venv/bin/activate

# Set your credentials (use today's token)
export ZERODHA_API_KEY='mmfof9xckmsvdyyk'
export ZERODHA_ACCESS_TOKEN='your_token_from_this_morning'

# Run fetcher
python zerodha_options_fetcher.py
```

---

## 📊 View Your Data

```bash
# List all CSV files
ls -lh output/

# View latest CSV file
ls -t output/*.csv | head -1

# Open output folder in Finder
open output/
```

---

## 🛠 Run Examples

Want to try different use cases?

```bash
# Make sure venv is activated first
source venv/bin/activate

# Set credentials
export ZERODHA_API_KEY='mmfof9xckmsvdyyk'
export ZERODHA_ACCESS_TOKEN='your_token'

# Run examples
python example_usage.py
```

---

## 🕐 When to Run

**Best Times (Monday - Friday):**
- **9:00 AM - 9:15 AM IST:** Before market opens (generate fresh token)
- **9:15 AM - 3:30 PM IST:** During market hours (fetch live intraday data)
- **3:30 PM onwards:** After market close (analyze full day's data)

**⚠️ Important:**
- **Weekends/Holidays:** Market is closed - you can only fetch historical data from past trading days
- **No live data on weekends** - The script will show "No data" or authentication errors for recent dates
- **Best results:** Run during market hours (Mon-Fri 9:15 AM - 3:30 PM IST)

**Remember:** Access tokens expire at 6 AM IST, so generate a new one each trading day!

---

## ⚠️ Troubleshooting

### "command not found: python"
**Solution:** Virtual environment not activated
```bash
cd ~/Desktop/option_chain
source venv/bin/activate
```

### "No module named 'kiteconnect'"
**Solution:** Install packages in venv
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Invalid access token"
**Solution:** Token expired or incorrect
```bash
# Generate new token
python generate_access_token.py

# Then export the new token
export ZERODHA_ACCESS_TOKEN='new_token_here'
```

### "No data returned"
**Possible causes:**
- Market is closed (try historical data with past dates)
- Options don't exist for the expiry being fetched
- Network connectivity issues

---

## 📝 Quick Reference Cheat Sheet

```bash
# Activate venv
cd ~/Desktop/option_chain && source venv/bin/activate

# Generate token (daily)
python generate_access_token.py

# Set credentials
export ZERODHA_API_KEY='mmfof9xckmsvdyyk'
export ZERODHA_ACCESS_TOKEN='token_here'

# Fetch option data
python zerodha_options_fetcher.py

# View output
open output/

# Deactivate venv when done
deactivate
```

---

## 💾 Save Credentials Permanently (Optional)

To avoid typing export commands daily, add to `~/.zshrc`:

```bash
# Add these lines to ~/.zshrc
echo "export ZERODHA_API_KEY='mmfof9xckmsvdyyk'" >> ~/.zshrc

# For access token, you'll still need to update daily since it expires
# You can create an alias for the common commands
echo "alias option_chain='cd ~/Desktop/option_chain && source venv/bin/activate'" >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

Then you can just type:
```bash
option_chain
# Now you're in the folder with venv activated!
```

---

## 🎯 Pro Tips

1. **Set up a morning script:** Create a shell script to automate the process
2. **Schedule with cron:** Auto-fetch data at specific times
3. **Use screen/tmux:** Keep the session running in background
4. **Monitor logs:** Check for errors in real-time
5. **Backup CSVs:** Regularly backup your output folder

---

## 📞 Need Help?

- Check `README_zerodha_options.md` for detailed documentation
- See `SETUP_VENV.md` for virtual environment help
- See `MAC_SETUP.md` for Mac-specific setup
- Zerodha API Docs: https://kite.trade/docs/connect/v3/

---

**Last Updated:** 22 Nov 2024
**Your API Key:** mmfof9xckmsvdyyk
**Remember:** Generate new access token daily at 6 AM IST!
