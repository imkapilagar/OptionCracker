"""
Test to show what the CSV will look like at 12:30 with strikes nearest to Rs 50
"""

import pandas as pd

# Read current CSV
csv_file = 'output/option_lows_20251124_1130_to_1230.csv'

try:
    df = pd.read_csv(csv_file)

    print("="*100)
    print("PREVIEW: What will be added to CSV at 12:30")
    print("="*100)

    # Show current data structure
    print("\nCurrent data (first 5 rows):")
    print(df.head().to_string(index=False))

    # Find strikes nearest to 50
    ce_df = df[df['option_type'] == 'CE'].copy()
    pe_df = df[df['option_type'] == 'PE'].copy()

    ce_df['distance_from_50'] = abs(ce_df['low'] - 50)
    pe_df['distance_from_50'] = abs(pe_df['low'] - 50)

    nearest_ce = ce_df.nsmallest(1, 'distance_from_50')
    nearest_pe = pe_df.nsmallest(1, 'distance_from_50')

    print("\n" + "="*100)
    print("STRIKES NEAREST TO ₹50 (will be appended at end of CSV)")
    print("="*100)

    print("\n🔹 CE Strike Nearest to ₹50:")
    print(nearest_ce[['strike', 'low', 'current_ltp', 'first_ltp', 'distance_from_50']].to_string(index=False))

    print("\n🔹 PE Strike Nearest to ₹50:")
    print(nearest_pe[['strike', 'low', 'current_ltp', 'first_ltp', 'distance_from_50']].to_string(index=False))

    print("\n" + "="*100)
    print("CSV STRUCTURE AT 12:30 will be:")
    print("="*100)
    print("""
1. All 32 strikes with their lows (rows 1-32)
2. Blank row (row 33)
3. Header row: "SPECIAL STRIKES NEAREST TO Rs 50" (row 34)
4. CE strike nearest to ₹50 (row 35)
5. PE strike nearest to ₹50 (row 36)
    """)

    print("\nExample of what will be added:")
    print("-"*100)

    # Show what will be appended
    blank_row = pd.DataFrame([{'symbol': '', 'strike': '', 'option_type': '', 'low': '', 'current_ltp': '', 'first_ltp': ''}])
    header_row = pd.DataFrame([{'symbol': 'SPECIAL', 'strike': 'STRIKES', 'option_type': 'NEAREST', 'low': 'Rs 50', 'current_ltp': '', 'first_ltp': ''}])

    preview_df = pd.concat([blank_row, header_row, nearest_ce[['symbol', 'strike', 'option_type', 'low', 'current_ltp', 'first_ltp']],
                           nearest_pe[['symbol', 'strike', 'option_type', 'low', 'current_ltp', 'first_ltp']]], ignore_index=True)

    print(preview_df.to_string(index=False))

    print("\n" + "="*100)

except FileNotFoundError:
    print(f"CSV file not found yet. It will be created when the tracker saves at 11:46.")
except Exception as e:
    print(f"Error: {e}")
