"""
Real-time viewer for current option lows being tracked
"""

import pandas as pd
import os
from datetime import datetime
import time

def view_current_lows():
    """Display current lows from the CSV file"""

    # CSV filename
    date_str = datetime.now().strftime('%Y%m%d')
    csv_filename = f'option_lows_{date_str}_1130_to_1230.csv'
    csv_path = os.path.join('output', csv_filename)

    # Clear screen
    os.system('clear')

    print("="*120)
    print(f"REAL-TIME OPTION LOWS VIEWER")
    print(f"Refreshing every 10 seconds... Press Ctrl+C to exit")
    print("="*120)

    while True:
        try:
            # Check if file exists
            if not os.path.exists(csv_path):
                print(f"\n⏳ Waiting for CSV to be created: {csv_path}")
                print(f"   Current time: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(10)
                continue

            # Read CSV
            df = pd.read_csv(csv_path)

            # Clear screen
            os.system('clear')

            # Header
            print("="*120)
            print(f"REAL-TIME OPTION LOWS TRACKER - NIFTY")
            print(f"Last Updated: {df['last_updated'].iloc[0] if 'last_updated' in df.columns else 'N/A'}")
            print(f"Current Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Total Strikes: {len(df)}")
            print("="*120)

            # Separate CE and PE
            ce_df = df[df['option_type'] == 'CE'].sort_values('strike')
            pe_df = df[df['option_type'] == 'PE'].sort_values('strike')

            # Display CE options
            print(f"\n{'CALL OPTIONS (CE)':.^120}")
            print("-"*120)
            print(f"{'Strike':<10} {'Low':<12} {'Current LTP':<12} {'First LTP':<12} {'Change %':<12} {'Samples':<10}")
            print("-"*120)

            for _, row in ce_df.iterrows():
                strike = row['strike']
                low = row['low']
                current = row['current_ltp']
                first = row['first_ltp']
                samples = row['samples']

                # Calculate change
                if first > 0:
                    change_pct = ((current - first) / first) * 100
                    change_str = f"{change_pct:+.2f}%"
                else:
                    change_str = "N/A"

                # Highlight if current = low (new low)
                marker = "🔻" if abs(current - low) < 0.01 else "  "

                print(f"{strike:<10.0f} ₹{low:<11.2f} ₹{current:<11.2f} ₹{first:<11.2f} {change_str:<12} {samples:<10} {marker}")

            # Display PE options
            print(f"\n{'PUT OPTIONS (PE)':.^120}")
            print("-"*120)
            print(f"{'Strike':<10} {'Low':<12} {'Current LTP':<12} {'First LTP':<12} {'Change %':<12} {'Samples':<10}")
            print("-"*120)

            for _, row in pe_df.iterrows():
                strike = row['strike']
                low = row['low']
                current = row['current_ltp']
                first = row['first_ltp']
                samples = row['samples']

                # Calculate change
                if first > 0:
                    change_pct = ((current - first) / first) * 100
                    change_str = f"{change_pct:+.2f}%"
                else:
                    change_str = "N/A"

                # Highlight if current = low
                marker = "🔻" if abs(current - low) < 0.01 else "  "

                print(f"{strike:<10.0f} ₹{low:<11.2f} ₹{current:<11.2f} ₹{first:<11.2f} {change_str:<12} {samples:<10} {marker}")

            # Summary stats
            print("\n" + "="*120)
            print("SUMMARY")
            print("="*120)

            # Find strikes with biggest drops
            df['price_drop'] = df['first_ltp'] - df['low']
            df['drop_pct'] = (df['price_drop'] / df['first_ltp'] * 100).fillna(0)

            top_drops = df.nlargest(5, 'price_drop')

            print("\nTop 5 Biggest Price Drops:")
            print(f"{'Strike':<12} {'Type':<6} {'First':<10} {'Low':<10} {'Drop':<10} {'Drop %':<10}")
            print("-"*60)
            for _, row in top_drops.iterrows():
                print(f"{row['strike']:<12.0f} {row['option_type']:<6} ₹{row['first_ltp']:<9.2f} ₹{row['low']:<9.2f} ₹{row['price_drop']:<9.2f} {row['drop_pct']:<9.2f}%")

            print("\n" + "="*120)
            print(f"🔻 = Currently at LOW | File: {csv_filename}")
            print(f"Next refresh in 10 seconds...")
            print("="*120)

            # Wait before refresh
            time.sleep(10)

        except KeyboardInterrupt:
            print("\n\n✅ Viewer stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == '__main__':
    view_current_lows()
