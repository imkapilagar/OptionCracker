#!/usr/bin/env python3
"""
Generate compact tabular HTML report for multi-timeframe option data
All 4 timeframes visible on one page without scrolling
"""

import json
import os
from datetime import datetime

def generate_compact_html(json_file):
    """Generate a compact, single-page HTML report"""

    # Read JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Define all 4 timeframes
    all_timeframes = [
        ('09:30', '10:30'),
        ('10:00', '11:00'),
        ('10:30', '11:30'),
        ('11:00', '12:00')
    ]

    # Create a lookup dict for completed timeframes
    completed_data = {(tf['start_time'], tf['end_time']): tf for tf in data}

    # Get current date
    report_date = datetime.now().strftime('%B %d, %Y')

    html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIFTY Option Lows - {report_date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .container {{
            width: 100%;
            max-width: 1000px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 1.8em;
            margin-bottom: 5px;
        }}

        .header p {{
            font-size: 1em;
            opacity: 0.9;
        }}

        .table-container {{
            padding: 30px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px 8px;
            text-align: center;
            font-weight: 600;
            border: 1px solid #5568d3;
        }}

        td {{
            padding: 10px 8px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}

        tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        tr:hover {{
            background: #e3e6ff;
            transition: background 0.2s;
        }}

        .time-col {{
            font-weight: 600;
            color: #333;
        }}

        .ce-data {{
            background: #d4f4dd;
        }}

        .pe-data {{
            background: #ffe5e5;
        }}

        .strike {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.05em;
        }}

        .low {{
            color: #28a745;
            font-weight: 600;
        }}

        .ltp {{
            color: #007bff;
            font-weight: 600;
        }}

        .distance {{
            font-size: 0.85em;
            color: #6c757d;
        }}

        .footer {{
            background: #343a40;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 0.85em;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header h1 {{
                font-size: 1.4em;
            }}

            table {{
                font-size: 0.8em;
            }}

            th, td {{
                padding: 8px 4px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 NIFTY Option Lows Report</h1>
            <p>{report_date} | Strikes Nearest to ₹50</p>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th rowspan="2">Time Period<br><span style="font-size:0.85em">(60 min lookback)</span></th>
                        <th colspan="3" style="background: #11998e;">CALL (CE)</th>
                        <th colspan="3" style="background: #ee0979;">PUT (PE)</th>
                    </tr>
                    <tr>
                        <th style="background: #0e8070;">Strike | Low | LTP</th>
                        <th style="background: #0e8070;">Distance</th>
                        <th style="background: #0e8070;">Samples</th>
                        <th style="background: #d6086b;">Strike | Low | LTP</th>
                        <th style="background: #d6086b;">Distance</th>
                        <th style="background: #d6086b;">Samples</th>
                    </tr>
                </thead>
                <tbody>
'''

    # Add data rows for all 4 timeframes
    for start, end in all_timeframes:
        timeframe_key = (start, end)

        if timeframe_key in completed_data:
            # Timeframe completed - show data
            timeframe = completed_data[timeframe_key]
            ce = timeframe.get('ce_strike')
            pe = timeframe.get('pe_strike')

            # CE data
            ce_strike = f"{ce['strike']}" if ce else "N/A"
            ce_low = f"₹{ce['low']:.2f}" if ce else "N/A"
            ce_ltp = f"₹{ce['ltp']:.2f}" if ce else "N/A"
            ce_dist = f"₹{ce['distance']:.2f}" if ce else "N/A"
            ce_samples = ce['samples'] if ce else "N/A"

            # PE data
            pe_strike = f"{pe['strike']}" if pe else "N/A"
            pe_low = f"₹{pe['low']:.2f}" if pe else "N/A"
            pe_ltp = f"₹{pe['ltp']:.2f}" if pe else "N/A"
            pe_dist = f"₹{pe['distance']:.2f}" if pe else "N/A"
            pe_samples = pe['samples'] if pe else "N/A"

            html += f'''
                    <tr>
                        <td class="time-col">{start} - {end}</td>
                        <td class="ce-data">
                            <span class="strike">{ce_strike}</span><br>
                            <span class="low">{ce_low}</span> | <span class="ltp">{ce_ltp}</span>
                        </td>
                        <td class="ce-data distance">{ce_dist}</td>
                        <td class="ce-data">{ce_samples}</td>
                        <td class="pe-data">
                            <span class="strike">{pe_strike}</span><br>
                            <span class="low">{pe_low}</span> | <span class="ltp">{pe_ltp}</span>
                        </td>
                        <td class="pe-data distance">{pe_dist}</td>
                        <td class="pe-data">{pe_samples}</td>
                    </tr>
'''
        else:
            # Timeframe not yet completed - show "Pending..."
            html += f'''
                    <tr>
                        <td class="time-col">{start} - {end}</td>
                        <td colspan="3" style="background: #f0f0f0; color: #999; font-style: italic;">Pending...</td>
                        <td colspan="3" style="background: #f0f0f0; color: #999; font-style: italic;">Pending...</td>
                    </tr>
'''

    html += '''
                </tbody>
            </table>
        </div>

        <div class="footer">
            Generated on ''' + datetime.now().strftime('%B %d, %Y at %I:%M %p') + '''<br>
            Data tracked every 30 seconds with 60-minute lookback periods
        </div>
    </div>
</body>
</html>
'''

    return html

def main():
    """Main function"""
    # Find the latest JSON file
    output_dir = 'output'
    json_files = [f for f in os.listdir(output_dir) if f.startswith('multi_timeframe_') and f.endswith('.json')]

    if not json_files:
        print("❌ No JSON data files found in output/ directory")
        return

    # Use the latest file
    json_files.sort(reverse=True)
    latest_json = os.path.join(output_dir, json_files[0])

    print(f"📊 Generating HTML report from: {latest_json}")

    # Generate HTML
    html_content = generate_compact_html(latest_json)

    # Save both to output/ and root (for GitHub Pages)
    output_html = os.path.join(output_dir, 'option_lows_compact.html')
    root_html = 'index.html'

    with open(output_html, 'w') as f:
        f.write(html_content)

    with open(root_html, 'w') as f:
        f.write(html_content)

    print(f"✅ HTML report generated:")
    print(f"   - {output_html}")
    print(f"   - {root_html} (for GitHub Pages)")
    print(f"\nOpen in browser:")
    print(f"   file://{os.path.abspath(root_html)}")

if __name__ == '__main__':
    main()
