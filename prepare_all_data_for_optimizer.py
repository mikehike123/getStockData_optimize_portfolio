import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# --- MASTER CONFIGURATION ---
output_dir = 'stock_data_yfinance'
end_date = datetime.now() # Use now() to be explicit
start_date = end_date - timedelta(days=20 * 365)
os.makedirs(output_dir, exist_ok=True)
print(f"Data will be generated for the period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"All output will be saved in '{output_dir}'")

# --- 1. DOWNLOAD ALL PUBLIC TICKERS (WITH TIMEZONE FIX) ---
print("\n--- Part 1: Downloading Public Tickers ---")
public_tickers = ['SPY', 'AGG', 'GLD', 'QQQ', 'EFA', 'BA', 'XLV', 'XLU']
# We need a reference index for our custom funds, so we'll grab it from AGG.
reference_index = None

for ticker in public_tickers:
    print(f"Processing {ticker}...")
    try:
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(start=start_date, end=end_date, interval='1mo', auto_adjust=True)
        
        # <<< FIX #1: REMOVE TIMEZONE INFORMATION >>>
        # This makes the index 'timezone-naive' so it can match our generated files.
        data.index = data.index.tz_localize(None)

        if not data.empty:
            if reference_index is None:
                reference_index = data.index # Save the clean index from the first successful download
            
            columns_to_drop = ['Dividends', 'Stock Splits', 'Capital Gains']
            data = data.drop(columns=[col for col in columns_to_drop if col in data.columns], errors='ignore')
            data.to_csv(os.path.join(output_dir, f"{ticker}.csv"))
    except Exception as e:
        print(f"ERROR downloading {ticker}: {e}")

# Check if we got a reference index
if reference_index is None:
    print("FATAL ERROR: Could not download any public data to use as a reference. Cannot proceed.")
    exit()

# --- 2. CREATE CUSTOM BALANCED FUND (HARDENED) ---
print("\n--- Part 2: Creating Custom Balanced Fund ---")
try:
    pseudo_ticker_balanced = 'BOEING_BALANCED_70_30'
    blend_components = {'SPY': 0.45, 'QQQ': 0.25, 'AGG': 0.30}
    component_data = yf.download(list(blend_components.keys()), start=start_date, end=end_date, interval='1mo', auto_adjust=True)['Close']
    component_data.index = component_data.index.tz_localize(None) # Remove timezone here too
    
    monthly_returns = component_data.pct_change()
    blended_returns = (monthly_returns * list(blend_components.values())).sum(axis=1)
    blended_price_index = (1 + blended_returns).cumprod()
    blended_price_index = blended_price_index.ffill() * 1.0
    final_data_balanced = blended_price_index.to_frame(name='Close')
    # Reindex to match the reference index perfectly, filling any gaps
    final_data_balanced = final_data_balanced.reindex(reference_index, method='ffill') 
    final_data_balanced.to_csv(os.path.join(output_dir, f"{pseudo_ticker_balanced}.csv"))
    print(f"Successfully created {pseudo_ticker_balanced}.csv")
except Exception as e:
    print(f"ERROR creating balanced fund: {e}")

# --- 3. CREATE CUSTOM FIXED INCOME FUND (HARDENED) ---
print("\n--- Part 3: Creating Custom Fixed Income Fund ---")
try:
    pseudo_ticker_fixed = 'BOEING_Stable_2_84'
    annual_return_fixed = 0.0284
    # <<< FIX #2: USE THE REFERENCE INDEX FOR PERFECT ALIGNMENT >>>
    # Instead of creating our own date range, we use the one from the downloaded data.
    monthly_return_fixed = (1 + annual_return_fixed)**(1/12) - 1
    prices = [100.0 * ((1 + monthly_return_fixed) ** i) for i in range(len(reference_index))]
    final_data_fixed = pd.DataFrame(data=prices, index=reference_index, columns=['Close'])
    final_data_fixed.index.name = 'Date'
    final_data_fixed.to_csv(os.path.join(output_dir, f"{pseudo_ticker_fixed}.csv"))
    print(f"Successfully created {pseudo_ticker_fixed}.csv")
except Exception as e:
    print(f"ERROR creating fixed income fund: {e}")

print("\n------------------------------------")
print("All data preparation is complete.")
print("You can now run the portfolio optimizer without errors.")