"""
Generate HTML report from option lows CSV
"""

import pandas as pd
from datetime import datetime
import os

def generate_html_report(csv_file):
    """Generate HTML report from CSV"""

    # Read CSV
    df = pd.read_csv(csv_file)

    # Remove the special strikes rows (we'll handle them separately)
    df_main = df[df['symbol'] == 'NIFTY'].copy()

    # Convert numeric columns to proper types
    df_main['strike'] = pd.to_numeric(df_main['strike'], errors='coerce')
    df_main['low'] = pd.to_numeric(df_main['low'], errors='coerce')
    df_main['current_ltp'] = pd.to_numeric(df_main['current_ltp'], errors='coerce')
    df_main['first_ltp'] = pd.to_numeric(df_main['first_ltp'], errors='coerce')
    df_main['samples'] = pd.to_numeric(df_main['samples'], errors='coerce')

    # Drop any rows with NaN values
    df_main = df_main.dropna(subset=['strike', 'low', 'current_ltp'])

    # Find strikes nearest to 50
    ce_df = df_main[df_main['option_type'] == 'CE'].copy()
    pe_df = df_main[df_main['option_type'] == 'PE'].copy()

    ce_df['distance_from_50'] = abs(ce_df['low'] - 50)
    pe_df['distance_from_50'] = abs(pe_df['low'] - 50)

    nearest_ce = ce_df.nsmallest(1, 'distance_from_50').iloc[0]
    nearest_pe = pe_df.nsmallest(1, 'distance_from_50').iloc[0]

    # Get tracking times from the data
    start_time = "11:30 AM"
    end_time = "12:30 PM"
    date_str = datetime.now().strftime('%B %d, %Y')

    # Create HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIFTY Option Lows Report - {date_str}</title>
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
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .tracking-info {{
            background: #f8f9fa;
            padding: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            border-bottom: 3px solid #e9ecef;
        }}

        .info-box {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .info-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .info-value {{
            font-size: 1.5em;
            font-weight: 700;
            color: #333;
        }}

        .strikes-container {{
            padding: 40px;
        }}

        .strike-card {{
            margin-bottom: 30px;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .strike-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}

        .strike-header {{
            padding: 20px;
            font-weight: 700;
            font-size: 1.3em;
            color: white;
        }}

        .ce-header {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}

        .pe-header {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}

        .strike-body {{
            padding: 30px;
            background: #f8f9fa;
        }}

        .strike-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .metric {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}

        .metric-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            color: #333;
        }}

        .metric-value.low {{
            color: #28a745;
        }}

        .metric-value.ltp {{
            color: #007bff;
        }}

        .change-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-top: 10px;
        }}

        .change-positive {{
            background: #d4edda;
            color: #155724;
        }}

        .change-negative {{
            background: #f8d7da;
            color: #721c24;
        }}

        .footer {{
            background: #343a40;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 12px;
            background: #667eea;
            color: white;
            border-radius: 15px;
            font-size: 0.85em;
            margin-top: 10px;
        }}

        @media (max-width: 768px) {{
            .tracking-info {{
                grid-template-columns: 1fr;
            }}

            .strike-info {{
                grid-template-columns: 1fr;
            }}

            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 NIFTY Option Lows Report</h1>
            <p>{date_str}</p>
        </div>

        <!-- Tracking Info -->
        <div class="tracking-info">
            <div class="info-box">
                <div class="info-label">Start Time</div>
                <div class="info-value">{start_time}</div>
            </div>
            <div class="info-box">
                <div class="info-label">End Time</div>
                <div class="info-value">{end_time}</div>
            </div>
            <div class="info-box">
                <div class="info-label">Duration</div>
                <div class="info-value">1 Hour</div>
            </div>
        </div>

        <!-- Strikes Container -->
        <div class="strikes-container">
            <h2 style="margin-bottom: 30px; color: #333; text-align: center;">Strikes Nearest to ₹50</h2>

            <!-- CE Strike Card -->
            <div class="strike-card">
                <div class="strike-header ce-header">
                    ✅ CALL Option (CE) - Strike {nearest_ce['strike']:.0f}
                </div>
                <div class="strike-body">
                    <div class="strike-info">
                        <div class="metric">
                            <div class="metric-label">Lowest Price</div>
                            <div class="metric-value low">₹{nearest_ce['low']:.2f}</div>
                            <div class="badge">Distance from ₹50: ₹{abs(nearest_ce['low'] - 50):.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Current LTP</div>
                            <div class="metric-value ltp">₹{nearest_ce['current_ltp']:.2f}</div>
                            {get_change_badge(nearest_ce['first_ltp'], nearest_ce['current_ltp'])}
                        </div>
                    </div>
                    <div class="strike-info">
                        <div class="metric">
                            <div class="metric-label">Starting Price</div>
                            <div class="metric-value">₹{nearest_ce['first_ltp']:.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Samples</div>
                            <div class="metric-value">{nearest_ce['samples']:.0f}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PE Strike Card -->
            <div class="strike-card">
                <div class="strike-header pe-header">
                    ✅ PUT Option (PE) - Strike {nearest_pe['strike']:.0f}
                </div>
                <div class="strike-body">
                    <div class="strike-info">
                        <div class="metric">
                            <div class="metric-label">Lowest Price</div>
                            <div class="metric-value low">₹{nearest_pe['low']:.2f}</div>
                            <div class="badge">Distance from ₹50: ₹{abs(nearest_pe['low'] - 50):.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Current LTP</div>
                            <div class="metric-value ltp">₹{nearest_pe['current_ltp']:.2f}</div>
                            {get_change_badge(nearest_pe['first_ltp'], nearest_pe['current_ltp'])}
                        </div>
                    </div>
                    <div class="strike-info">
                        <div class="metric">
                            <div class="metric-label">Starting Price</div>
                            <div class="metric-value">₹{nearest_pe['first_ltp']:.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Samples</div>
                            <div class="metric-value">{nearest_pe['samples']:.0f}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            <br>
            Data tracked every 30 seconds from {start_time} to {end_time}
        </div>
    </div>
</body>
</html>
"""

    return html_content


def get_change_badge(first_price, current_price):
    """Generate change badge HTML"""
    if first_price == 0:
        return ''

    change_pct = ((current_price - first_price) / first_price) * 100
    badge_class = 'change-positive' if change_pct >= 0 else 'change-negative'
    sign = '+' if change_pct >= 0 else ''

    return f'<div class="change-badge {badge_class}">{sign}{change_pct:.2f}%</div>'


def main():
    # CSV file path
    csv_file = 'output/option_lows_20251124_1130_to_1230.csv'

    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return

    print("="*80)
    print("Generating HTML Report...")
    print("="*80)

    # Generate HTML
    html_content = generate_html_report(csv_file)

    # Save HTML file
    output_file = 'output/option_lows_report.html'
    with open(output_file, 'w') as f:
        f.write(html_content)

    # Get absolute path
    abs_path = os.path.abspath(output_file)

    print(f"\n✅ HTML report generated successfully!")
    print(f"\n📄 File: {abs_path}")
    print(f"\n🌐 Open in browser:")
    print(f"   file://{abs_path}")
    print("\n" + "="*80)

    # Try to open in browser
    import webbrowser
    try:
        webbrowser.open(f'file://{abs_path}')
        print("\n✅ Opening in browser...")
    except:
        print("\n💡 Copy the file path above and paste in your browser")


if __name__ == '__main__':
    main()
