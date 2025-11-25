#!/usr/bin/env python3
"""
Generate Live Dashboard for Rs 50 Target Tracking
Shows current nearest-to-50 options for each active thread
"""
import json
import os
from datetime import datetime

def generate_live_dashboard():
    """Generate HTML dashboard showing options nearest to Rs 50 for each thread"""

    today = datetime.now().strftime('%Y%m%d')
    # Try live tracking file first, then debug file, then fall back to completed file
    json_file = f'output/live_tracking_{today}.json'
    if not os.path.exists(json_file):
        json_file = f'output/debug_tracking_{today}.json'
    if not os.path.exists(json_file):
        json_file = f'output/multi_timeframe_{today}.json'

    # Check if data exists
    data_dict = {}
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)
            # Handle both dict and list formats
            if isinstance(loaded_data, dict):
                data_dict = loaded_data
            else:
                # Convert list to dict format
                for item in loaded_data:
                    tf = item['timeframe']
                    thread_num = ['09:30-10:30', '10:00-11:00', '10:30-11:30', '11:00-12:00'].index(tf) + 1
                    data_dict[f"thread_{thread_num}"] = item

    # Define all timeframes
    all_timeframes = [
        {'name': 'Thread 1', 'timeframe': '09:30-10:30'},
        {'name': 'Thread 2', 'timeframe': '10:00-11:00'},
        {'name': 'Thread 3', 'timeframe': '10:30-11:30'},
        {'name': 'Thread 4', 'timeframe': '11:00-12:00'},
    ]

    # Current time to determine which threads are active
    current_time = datetime.now().strftime('%H:%M')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">
    <title>Live ₹50 Target Tracker</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .header .time {{
            font-size: 1em;
            margin-top: 10px;
            opacity: 0.8;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .thread-card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .thread-card.inactive {{
            opacity: 0.6;
            background: #f5f5f5;
        }}

        .thread-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}

        .thread-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .thread-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .status-active {{
            background: #4ade80;
            color: white;
        }}

        .status-waiting {{
            background: #fbbf24;
            color: white;
        }}

        .status-completed {{
            background: #60a5fa;
            color: white;
        }}

        .timeframe {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 15px;
        }}

        .option-section {{
            margin-bottom: 20px;
        }}

        .option-type {{
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 8px;
        }}

        .option-type.ce {{
            background: #dcfce7;
            color: #166534;
        }}

        .option-type.pe {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .option-details {{
            padding: 10px;
            background: #f9fafb;
            border-radius: 8px;
            margin-top: 5px;
        }}

        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 0.95em;
        }}

        .detail-label {{
            color: #666;
        }}

        .detail-value {{
            font-weight: bold;
        }}

        .strike {{
            font-size: 1.3em;
            color: #333;
        }}

        .low-price {{
            font-size: 1.5em;
            color: #dc2626;
        }}

        .near-target {{
            background: #fef3c7;
            border: 2px solid #f59e0b;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}

        .no-data {{
            text-align: center;
            color: #999;
            font-style: italic;
            padding: 20px;
        }}

        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }}

        .auto-refresh {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Live ₹50 Target Tracker</h1>
            <div class="subtitle">NIFTY Options - Nearest to ₹50 Low</div>
            <div class="time">Last Updated: {datetime.now().strftime('%B %d, %Y %I:%M:%S %p')}</div>
        </div>

        <div class="grid">
"""

    # Generate cards for each thread
    for idx, tf_info in enumerate(all_timeframes):
        thread_name = tf_info['name']
        timeframe = tf_info['timeframe']
        thread_key = f"thread_{idx + 1}"

        # Find data for this timeframe
        tf_data = data_dict.get(thread_key, None)

        # Determine status
        start_time = timeframe.split('-')[0]
        end_time = timeframe.split('-')[1]

        if tf_data:
            # Check if it has status field
            data_status = tf_data.get('status', 'completed')
            if data_status == 'active':
                status = 'active'
                status_label = '🔴 LIVE'
                status_class = 'status-active'
                is_active = True
            else:
                status = 'completed'
                status_label = 'Completed'
                status_class = 'status-completed'
                is_active = False
        elif current_time >= start_time and current_time < end_time:
            status = 'active'
            status_label = '🔴 LIVE'
            status_class = 'status-active'
            is_active = True
        else:
            status = 'waiting'
            status_label = 'Waiting'
            status_class = 'status-waiting'
            is_active = False

        card_class = 'thread-card' if is_active or tf_data else 'thread-card inactive'

        html += f"""
            <div class="{card_class}">
                <div class="thread-header">
                    <div class="thread-name">{thread_name}</div>
                    <div class="thread-status {status_class}">{status_label}</div>
                </div>
                <div class="timeframe">⏰ {timeframe}</div>
"""

        if tf_data:
            # CE Option
            if tf_data.get('ce_strike'):
                ce = tf_data['ce_strike']
                distance = abs(ce['low'] - 50)
                near_target = 'near-target' if distance <= 15 else ''

                html += f"""
                <div class="option-section">
                    <div class="option-type ce">📈 CALL (CE)</div>
                    <div class="option-details {near_target}">
                        <div class="detail-row">
                            <span class="detail-label">Strike:</span>
                            <span class="detail-value strike">{int(ce['strike'])}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Low:</span>
                            <span class="detail-value low-price">₹{ce['low']:.2f}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Current LTP:</span>
                            <span class="detail-value">₹{ce['ltp']:.2f}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Distance from ₹50:</span>
                            <span class="detail-value">₹{distance:.2f}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Samples:</span>
                            <span class="detail-value">{ce['samples']}</span>
                        </div>
                    </div>
                </div>
"""
            else:
                html += """
                <div class="option-section">
                    <div class="option-type ce">📈 CALL (CE)</div>
                    <div class="no-data">No data yet</div>
                </div>
"""

            # PE Option
            if tf_data.get('pe_strike'):
                pe = tf_data['pe_strike']
                distance = abs(pe['low'] - 50)
                near_target = 'near-target' if distance <= 15 else ''

                html += f"""
                <div class="option-section">
                    <div class="option-type pe">📉 PUT (PE)</div>
                    <div class="option-details {near_target}">
                        <div class="detail-row">
                            <span class="detail-label">Strike:</span>
                            <span class="detail-value strike">{int(pe['strike'])}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Low:</span>
                            <span class="detail-value low-price">₹{pe['low']:.2f}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Current LTP:</span>
                            <span class="detail-value">₹{pe['ltp']:.2f}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Distance from ₹50:</span>
                            <span class="detail-value">₹{distance:.2f}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Samples:</span>
                            <span class="detail-value">{pe['samples']}</span>
                        </div>
                    </div>
                </div>
"""
            else:
                html += """
                <div class="option-section">
                    <div class="option-type pe">📉 PUT (PE)</div>
                    <div class="no-data">No data yet</div>
                </div>
"""
        else:
            html += """
                <div class="option-section">
                    <div class="option-type ce">📈 CALL (CE)</div>
                    <div class="no-data">Waiting for data...</div>
                </div>
                <div class="option-section">
                    <div class="option-type pe">📉 PUT (PE)</div>
                    <div class="no-data">Waiting for data...</div>
                </div>
"""

        html += """
            </div>
"""

    html += f"""
        </div>

        <div class="footer">
            <div class="auto-refresh">⚡ Auto-refreshes every 10 seconds</div>
            <div style="margin-top: 10px; font-size: 0.9em;">
                Tracking options nearest to ₹50 low across all timeframes
            </div>
        </div>
    </div>
</body>
</html>
"""

    # Save to file
    output_file = 'live_dashboard.html'
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Dashboard generated: {output_file}")
    print(f"🌐 Open in browser to view live tracking")
    return output_file

if __name__ == '__main__':
    generate_live_dashboard()
