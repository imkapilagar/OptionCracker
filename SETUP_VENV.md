# Virtual Environment Setup (Recommended for Mac)

If you're getting "externally-managed-environment" errors, use a virtual environment.

## One-Time Setup

```bash
# Navigate to the project folder
cd ~/Desktop/option_chain

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import kiteconnect; print('✅ kiteconnect installed successfully')"
```

## Daily Usage

**Every time** you open a new terminal and want to use the scripts:

```bash
# Navigate to the project folder
cd ~/Desktop/option_chain

# Activate the virtual environment
source venv/bin/activate

# Now you can run the scripts
python generate_access_token.py
python zerodha_options_fetcher.py
```

You'll know the virtual environment is active when you see `(venv)` at the start of your terminal prompt:

```
(venv) kapilagarwal@Kapils-MacBook-Pro Option_Chain %
```

## Deactivating the Virtual Environment

When you're done:

```bash
deactivate
```

## Why Use a Virtual Environment?

- **Isolates packages:** Doesn't conflict with system Python
- **No permission issues:** Install packages without sudo
- **Clean management:** Easy to delete and recreate if needed
- **Best practice:** Recommended by Python developers

## Quick Reference Card

```bash
# Activate venv (do this first, every time)
cd ~/Desktop/option_chain && source venv/bin/activate

# Generate access token
python generate_access_token.py

# Set environment variables
export ZERODHA_API_KEY='your_key'
export ZERODHA_ACCESS_TOKEN='your_token'

# Run the fetcher
python zerodha_options_fetcher.py

# Deactivate when done
deactivate
```

## Troubleshooting

**"venv not found" error**
```bash
# Create it first
cd ~/Desktop/option_chain
python3 -m venv venv
```

**"command not found: python"**
```bash
# Make sure venv is activated
source venv/bin/activate
```

**Want to start fresh?**
```bash
# Delete the old venv
rm -rf ~/Desktop/option_chain/venv

# Create new one
cd ~/Desktop/option_chain
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
