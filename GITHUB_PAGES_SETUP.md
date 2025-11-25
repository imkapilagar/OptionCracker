# GitHub Pages Setup for Live Dashboard

## Current Status
✅ Dashboard created with embedded data
✅ GitHub Actions workflow configured
✅ Auto-updates every 30 minutes during market hours

## GitHub Pages URL
https://imkapilagar.github.io/Option_Chain/

## How It Works

1. **Static Dashboard**: The `index.html` file contains the dashboard with embedded JSON data
2. **GitHub Actions**: Automatically fetches new data and updates the dashboard every 30 minutes during market hours (9:15 AM - 3:30 PM IST)
3. **Manual Updates**: You can manually trigger updates from your local machine

## Setup GitHub Actions (for auto-updates)

### Step 1: Add Upstox Access Token as GitHub Secret

1. Go to your repository: https://github.com/imkapilagar/Option_Chain
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `UPSTOX_ACCESS_TOKEN`
5. Value: Your Upstox access token (paste the token from `upstox_credentials.txt`)
6. Click **Add secret**

### Step 2: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If prompted, click **Enable GitHub Actions**
3. The workflow will run automatically on schedule or you can trigger it manually

### Step 3: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Source: Deploy from a branch
3. Branch: `main` / `root`
4. Click **Save**

## Manual Updates (from your local machine)

### Update and Push Data
```bash
# Fetch latest data
python3 refresh_current_data.py

# Generate updated dashboard
python3 create_github_pages_dashboard.py

# Commit and push
git add index.html output/debug_tracking_*.json
git commit -m "Update dashboard data"
git push origin main
```

### View Changes
- Wait 1-2 minutes for GitHub Pages to rebuild
- Visit: https://imkapilagar.github.io/Option_Chain/

## What the Dashboard Shows

- **Thread 1-4**: Four overlapping 60-minute tracking windows
- **CE Options**: Call options nearest to ₹50 low
- **PE Options**: Put options nearest to ₹50 low
- **Live Status**: Shows if each thread is active, waiting, or completed
- **Distance from ₹50**: How close the option is to your target price

## Limitations

⚠️ **Important Notes**:
1. GitHub Actions has a delay (not real-time)
2. Access tokens expire at 6 AM IST daily - you'll need to update the secret
3. For true real-time tracking, run the local dashboard: `live_dashboard.html`

## Notifications

The local tracker (running on your machine) will show notifications when:
- 📉 New lows are detected
- 🔔 Options get within ₹15 of ₹50

GitHub Pages dashboard is for viewing remotely but won't show notifications.
