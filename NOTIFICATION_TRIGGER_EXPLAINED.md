# Notification Trigger - Detailed Explanation

## Overview
The notification system triggers **automatically** whenever a strike's current LTP (Last Traded Price) drops below its previously recorded low during a tracking timeframe.

## Code Flow (Line by Line)

### 1. Data Collection (Every 30 seconds)
```python
# Line 91: Fetch live option chain data
option_data = fetch_option_chain(access_token, symbol)

# Lines 98-110: Loop through all strikes and extract LTP
for strike_data in option_data:
    strike = strike_data.get('strike_price')  # e.g., 26200
    ltp = market_data.get('ltp', 0)           # e.g., 48.50
```

### 2. Tracking Logic
```python
# Line 115: Create unique key for each strike
key = f"{symbol}_{strike}_{opt_type}"  # e.g., "NIFTY_26200_CE"

# Lines 117-127: First time seeing this strike
if key not in lows_tracker:
    lows_tracker[key] = {
        'low': ltp,              # Store first LTP as initial low
        'current_ltp': ltp,
        'samples': 1
    }
```

### 3. **NOTIFICATION TRIGGER** (Lines 128-152)
```python
# Line 128-131: Strike already exists, update it
else:
    lows_tracker[key]['samples'] += 1
    old_low = lows_tracker[key]['low']      # Get previous low (e.g., 52.40)
    lows_tracker[key]['current_ltp'] = ltp  # Update current LTP (e.g., 48.75)

    # Line 132: THE TRIGGER CONDITION
    if ltp < old_low:  # 48.75 < 52.40 → TRUE! Notification fires!

        # Line 134: Update the low to new value
        lows_tracker[key]['low'] = ltp  # 48.75 becomes new low

        # Line 135: Calculate drop percentage
        drop_percent = ((old_low - ltp) / old_low) * 100  # 6.97%

        # Line 138: Check if near ₹50 target
        is_near_50 = abs(ltp - 50) <= 15  # |48.75 - 50| = 1.25 ≤ 15 → TRUE

        # Lines 142-152: PRINT NOTIFICATION
        if is_near_50:
            print("============================================================")
            print("🔔 [Thread 2 | 10:00-11:00] NEW LOW!")
            print("   Strike: 26200 CE")
            print("   Old Low: ₹52.40 → New Low: ₹48.75 (↓6.97%)")
            print("   Time: 10:25:45")
            print("   ⭐ NEAR ₹50 TARGET! Distance: ₹1.25")
            print("============================================================")
```

## Trigger Conditions Summary

### When Notification Fires:
✅ **Condition Met:** `Current LTP < Previous Low`

### Example Timeline:

| Time     | Strike   | LTP   | Stored Low | Trigger? | Notification |
|----------|----------|-------|------------|----------|--------------|
| 09:30:00 | 26200 CE | 52.40 | 52.40      | ❌ No    | (First sample) |
| 09:30:30 | 26200 CE | 53.10 | 52.40      | ❌ No    | LTP > Low (53.10 > 52.40) |
| 09:31:00 | 26200 CE | 52.40 | 52.40      | ❌ No    | LTP = Low (52.40 = 52.40) |
| 09:31:30 | 26200 CE | 51.80 | 52.40      | ✅ **YES** | **🔔 NEW LOW! 52.40 → 51.80** |
| 09:32:00 | 26200 CE | 52.00 | 51.80      | ❌ No    | LTP > Low (52.00 > 51.80) |
| 09:32:30 | 26200 CE | 51.20 | 51.80      | ✅ **YES** | **🔔 NEW LOW! 51.80 → 51.20** |
| 09:33:00 | 26200 CE | 48.75 | 51.20      | ✅ **YES** | **🔔 NEW LOW! 51.20 → 48.75** |

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Every 30 seconds: Fetch Live Data                         │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  For each strike (26100, 26150, 26200, etc.)               │
│  Extract: strike price, option type (CE/PE), LTP           │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Strike exists in     │
        │  tracker?             │
        └───────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
       NO               YES
        │                │
        ▼                ▼
┌──────────────┐  ┌────────────────────┐
│ Add new      │  │ Compare LTP vs     │
│ strike       │  │ stored low         │
│ low = LTP    │  └────────┬───────────┘
└──────────────┘           │
                           ▼
                   ┌───────────────┐
                   │ LTP < Low?    │
                   └───────┬───────┘
                           │
                   ┌───────┴────────┐
                   │                │
                  NO               YES
                   │                │
                   ▼                ▼
         ┌─────────────────┐  ┌──────────────────────┐
         │ No notification │  │ 🔔 TRIGGER           │
         │ Continue        │  │ NOTIFICATION!        │
         └─────────────────┘  │                      │
                              │ - Update low         │
                              │ - Calculate drop %   │
                              │ - Check if near ₹50  │
                              │ - Print alert        │
                              └──────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Near ₹50?       │
                              └────────┬────────┘
                                       │
                               ┌───────┴────────┐
                               │                │
                              YES              NO
                               │                │
                               ▼                ▼
                    ┌──────────────────┐  ┌────────────┐
                    │ Highlighted      │  │ Regular    │
                    │ 🔔 with border   │  │ 📉 alert   │
                    │ ⭐ target marker │  │            │
                    └──────────────────┘  └────────────┘
```

## Key Variables

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `ltp` | Current Last Traded Price from API | 48.75 |
| `old_low` | Previously stored lowest price | 52.40 |
| `lows_tracker[key]['low']` | Stored low for this strike | 52.40 → updated to 48.75 |
| `drop_percent` | Percentage drop from old to new low | 6.97% |
| `is_near_50` | Boolean: Is LTP within ₹15 of ₹50? | True (if 35 ≤ LTP ≤ 65) |

## Trigger Frequency

- **Polling**: Every 30 seconds
- **Notifications**: Only when `LTP < stored_low`
- **No limit**: Can trigger multiple times for same strike if it keeps making new lows
- **Per timeframe**: Each thread tracks its own lows independently

## Real-World Example

**Scenario:** 26200 CE during 10:00-11:00 timeframe

```
10:00:00 → LTP: 55.30 → Low: 55.30 [First sample, no notification]
10:00:30 → LTP: 54.80 → Low: 55.30 → 🔔 NEW LOW! 55.30 → 54.80
10:01:00 → LTP: 55.10 → Low: 54.80 [No notification - LTP higher]
10:01:30 → LTP: 53.20 → Low: 54.80 → 🔔 NEW LOW! 54.80 → 53.20
10:02:00 → LTP: 53.50 → Low: 53.20 [No notification - LTP higher]
10:02:30 → LTP: 48.75 → Low: 53.20 → 🔔 NEW LOW! 53.20 → 48.75 ⭐ NEAR ₹50!
```

## Code Location

**File:** `track_parallel_timeframes.py`
**Lines:** 128-152
**Trigger Line:** 132 (`if ltp < old_low:`)

## Customization Options

You can modify the notification behavior:

### Change "near ₹50" threshold (Line 138):
```python
# Current: within ₹15 of ₹50 (35-65 range)
is_near_50 = abs(ltp - 50) <= 15

# More strict: within ₹10 of ₹50 (40-60 range)
is_near_50 = abs(ltp - 50) <= 10

# More lenient: within ₹20 of ₹50 (30-70 range)
is_near_50 = abs(ltp - 50) <= 20
```

### Only notify for strikes near ₹50 (add condition):
```python
if ltp < old_low and abs(ltp - 50) <= 15:
    # Notification code here
```

### Add minimum drop threshold (only notify if drop > 2%):
```python
if ltp < old_low:
    drop_percent = ((old_low - ltp) / old_low) * 100
    if drop_percent >= 2.0:  # Only notify if drop is 2% or more
        # Notification code here
```
