# Option Cracker

Real-time options breakout tracking system for Indian markets (NSE/BSE). Track multiple strategies simultaneously with customizable entry times, lookback periods, and target premiums.

## Features

- **Multi-Strategy Support**: Run multiple strategies with different parameters simultaneously
- **Real-time WebSocket Data**: Live tick data from Upstox API
- **Historical Data Analysis**: Backfill strategies with saved tick data
- **Web Dashboard**: Real-time visualization with strategy builder
- **Configurable Parameters**: Index, Entry Time, Lookback, Target Premium, Stop Loss
- **Data Persistence**: Tick data and strategies saved for analysis

## Supported Indices

- NIFTY 50
- BANK NIFTY
- SENSEX

## Quick Start

### Prerequisites

- Python 3.10+
- Upstox Trading Account with API access

### Installation

```bash
# Clone the repository
git clone https://github.com/kapilagarwal/OptionCracker.git
cd OptionCracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Generate Upstox Access Token**:
   ```bash
   python upstox_token_generator.py
   ```
   Follow the OAuth flow to get your access token.

2. **Configure Settings** (optional):
   Edit `v2/config/default_config.yaml` to customize:
   - Market timing
   - Symbol configurations
   - Dashboard port
   - Alert settings

### Running the Tracker

```bash
python v2/main.py
```

The dashboard will open automatically at `http://localhost:8765`

## Dashboard Usage

### Create a Strategy

1. Select **Index** (NIFTY, BANKNIFTY, SENSEX)
2. Choose **Entry Time** (when to enter the position)
3. Set **Lookback Period** (time to track lows before entry)
4. Select **Target Premium** (desired option premium)
5. Set **Stop Loss %**
6. Click **"+ Add as Strategy"**

### Strategy Phases

- **PENDING**: Before lookback period starts
- **LOOKBACK**: Tracking lows during lookback period
- **MONITORING**: Position taken, tracking P&L and stop loss
- **COMPLETED**: Market closed or strategy ended

## Project Structure

```
OptionCracker/
├── v2/
│   ├── main.py              # Main application entry point
│   ├── config/
│   │   ├── settings.py      # Configuration loader
│   │   └── default_config.yaml
│   ├── core/
│   │   ├── strategy.py      # Strategy data model
│   │   ├── strategy_manager.py
│   │   ├── websocket_manager.py
│   │   └── instrument_builder.py
│   ├── dashboard/
│   │   ├── server.py        # WebSocket dashboard server
│   │   └── static/
│   │       └── index.html   # Dashboard UI
│   ├── persistence/
│   │   ├── tick_data_store.py
│   │   ├── strategy_store.py
│   │   └── state_manager.py
│   └── alerts/
│       └── notifier.py
├── output/                   # Data output directory
├── requirements.txt
└── README.md
```

## Deployment Options

### Option 1: Local Machine
- **Pros**: Simple, no cost
- **Cons**: Requires machine to be running during market hours

### Option 2: Cloud VM (Recommended for Production)

**AWS EC2 / Google Cloud / Azure VM**:
- Instance: t3.small (2 vCPU, 2GB RAM) - ~$15-20/month
- Storage: 20GB SSD
- Run as systemd service for auto-restart

```bash
# Create systemd service
sudo nano /etc/systemd/system/optioncracker.service
```

```ini
[Unit]
Description=Option Cracker Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/OptionCracker
ExecStart=/home/ubuntu/OptionCracker/venv/bin/python v2/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable optioncracker
sudo systemctl start optioncracker
```

### Option 3: Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8765

CMD ["python", "v2/main.py"]
```

```bash
docker build -t optioncracker .
docker run -d -p 8765:8765 -v $(pwd)/output:/app/output optioncracker
```

### Option 4: Railway / Render / Fly.io

These platforms offer easy deployment:

**Railway**:
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Infrastructure Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Storage | 10 GB | 20 GB SSD |
| Network | Stable internet | Low latency connection |

### Important Considerations

1. **Token Refresh**: Upstox tokens expire daily. Implement auto-refresh or manual refresh each morning.

2. **Data Backup**: Tick data files can grow large. Consider:
   - Compressing old data
   - Archiving to cloud storage (S3, GCS)
   - Rotating files daily

3. **Monitoring**: Set up alerts for:
   - WebSocket disconnections
   - High memory usage
   - Application crashes

4. **Security**:
   - Never commit credentials to git
   - Use environment variables for secrets
   - Restrict dashboard access if exposed publicly

## API Reference

### WebSocket Actions

```javascript
// Create Strategy
{
    "action": "create_strategy",
    "index": "NIFTY",
    "entry_time": "11:00",
    "lookback_minutes": 60,
    "target_premium": 60,
    "stop_loss_percent": 50
}

// Get Historical Preview
{
    "action": "get_preview",
    "index": "NIFTY",
    "entry_time": "11:00",
    "lookback_minutes": 60,
    "target_premium": 60
}

// Remove Strategy
{
    "action": "remove_strategy",
    "strategy_id": "abc123"
}
```

## License

MIT License - see LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Trading in options involves substantial risk of loss. Past performance is not indicative of future results. Always do your own research and consult with a financial advisor before trading.
