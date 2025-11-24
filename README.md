# NIFTY Option Chain Tracker

Real-time option chain tracking and analysis for NIFTY index options using Upstox API.

## 🔗 Live Report

View the latest option lows report: [Click Here](https://kapilagarwal.github.io/option_chain/)

## 📊 Features

- **Live Option Chain Fetching** - Get real-time option data during market hours
- **Low Tracking** - Track lowest prices for all strikes over a time period
- **Automated CSV Export** - Data saved every 2 minutes
- **HTML Reports** - Beautiful, responsive web reports
- **Strikes Analysis** - Automatically identifies strikes nearest to ₹50

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Upstox trading account
- Upstox API credentials

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/option_chain.git
cd option_chain

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Setup

1. **Get Upstox API Credentials**
   - Visit https://upstox.com/developer/
   - Create an app and get your API Key and Secret

2. **Generate Access Token**
   ```bash
   python upstox_token_generator.py
   ```

3. **Test Connection**
   ```bash
   python test_upstox_connection.py
   ```

## 📈 Usage

### Fetch Live Option Chain

```bash
python fetch_live_option_chain.py
```

Fetches current option chain data for NIFTY and BANKNIFTY (ATM to OTM15).

### Track Lows (11:30 AM - 12:30 PM)

```bash
python track_hourly_low_incremental.py
```

Automatically:
- Tracks lowest prices for all strikes
- Saves CSV every 2 minutes
- Identifies strikes nearest to ₹50
- Generates final report at 12:30 PM

### Generate HTML Report

```bash
python generate_html_report.py
```

Creates a beautiful HTML report showing:
- Start and end times
- CE and PE strikes nearest to ₹50
- Low prices and current LTP
- Price changes and percentages

## 📁 Project Structure

```
option_chain/
├── index.html                          # GitHub Pages report
├── fetch_live_option_chain.py          # Live data fetcher
├── track_hourly_low_incremental.py     # Low tracker
├── generate_html_report.py             # HTML generator
├── upstox_token_generator.py           # Token generator
├── output/                             # Output directory
│   ├── option_lows_*.csv              # CSV reports
│   └── option_lows_report.html        # HTML reports
└── requirements.txt                    # Dependencies
```

## 🔐 Security

**IMPORTANT:** Never commit your credentials!

- `upstox_credentials.txt` is in `.gitignore`
- Access tokens expire daily at 6 AM IST
- Regenerate tokens daily using `upstox_token_generator.py`

## 📊 Data Fields

The tracker provides:
- **symbol**: Index name (NIFTY)
- **strike**: Strike price
- **option_type**: CE or PE
- **low**: Lowest price during tracking period
- **current_ltp**: Current Last Traded Price
- **first_ltp**: Starting price
- **samples**: Number of data points collected

## ⚙️ Configuration

Edit the scripts to customize:
- Tracking time period (default: 11:30-12:30)
- Polling interval (default: 30 seconds)
- CSV save interval (default: 2 minutes)
- Symbols to track (NIFTY, BANKNIFTY)

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📝 License

MIT License - feel free to use for personal or commercial projects.

## ⚠️ Disclaimer

This tool is for educational and informational purposes only. Trading in derivatives involves risk. Always do your own research before making investment decisions.

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for options traders**
