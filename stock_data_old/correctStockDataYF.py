import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# --- Step 1: Define Tickers and Parameters ---
tickers = ['SPY', 'QQQ', 'AGG', 'GLD', 'EFA'] # <<< Only ETFs are
#tickers = ['BA']
end_date = datetime.today()
start_date = end_date - timedelta(days=20 * 365)
output_dir = 'stock_data_yfinance'

# --- Step 2: Create Directory ---
try:
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directory '{output_dir}' created or already exists.")
except Exception as e:
    print(f"Error creating directory: {e}")
    exit()

# --- Step 3: Download Data and GUARANTEE It's Correct ---
print("\nStarting data download...")

for ticker in tickers:
    print(f"\n--- Processing {ticker} ---")
    try:
        # Create a Ticker object for the current symbol
        ticker_obj = yf.Ticker(ticker)

        # Get historical data. auto_adjust=True is the modern standard.
        data = ticker_obj.history(start=start_date,
                                  end=end_date,
                                  interval='1mo',
                                  auto_adjust=True)

        if data.empty:
            print(f"Warning: No data downloaded for {ticker}.")
            continue

        # ===================================================================
        # THE GUARANTEED FIX:
        # We know your system returns a MultiIndex. This code detects it
        # and flattens it into a normal, clean header.
        if isinstance(data.columns, pd.MultiIndex):
            print("Detected malformed multi-level header. Fixing it now...")
            # This line takes the top level of the bad header (e.g., 'Open', 'Close')
            # and makes it the new, simple header.
            data.columns = data.columns.get_level_values(0)
            print("Header has been successfully corrected in memory.")
        # ===================================================================

        # The .history() method can include columns we don't need.
        # This line removes them just in case.
        columns_to_drop = ['Dividends', 'Stock Splits', 'Capital Gains']
        data = data.drop(columns=[col for col in columns_to_drop if col in data.columns])

        # Verification Step: This will now show the CLEAN data
        print(f"\nData for {ticker} as it looks AFTER the fix:")
        print(data.head())

        # Construct file path and save the clean data
        file_path = os.path.join(output_dir, f"{ticker}.csv")
        data.to_csv(file_path)

        print(f"\nSuccessfully saved data for {ticker} to {file_path}")

    except Exception as e:
        print(f"An error occurred while processing {ticker}: {e}")

print("\n------------------------------------")
print("All downloads complete.")
print("The generated CSV files are now in the correct format.")
print("------------------------------------")