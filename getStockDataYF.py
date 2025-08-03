import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# --- Step 1: Define Tickers and Parameters ---
#tickers = ['SPY', 'AGG', 'GLD', 'QQQ', 'EFA', 'AAPL', 'MSFT']
tickers = ['MSFT']
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

# --- Step 3: Download Data with the Explicit Fix ---
print("\nStarting data download...")

for ticker in tickers:
    print(f"\n--- Downloading data for {ticker} ---")
    try:
        # THE GUARANTEED FIX IS HERE:
        # We explicitly set auto_adjust=True to get the correct,
        # clean DataFrame with dividend-adjusted prices.
        data = yf.download(ticker,
                           start=start_date,
                           end=end_date,
                           interval='1mo',
                           auto_adjust=True) # <<< THIS IS THE FIX

        if data.empty:
            print(f"Warning: No data downloaded for {ticker}.")
            continue

        # Verification Step
        print(f"Data for {ticker} as it looks in memory (first 5 rows):")
        print(data.head())

        file_path = os.path.join(output_dir, f"{ticker}.csv")
        # Because 'data' is now clean, this will save correctly.
        data.to_csv(file_path)

        print(f"\nSuccessfully saved data for {ticker} to {file_path}")

    except Exception as e:
        print(f"An error occurred while processing {ticker}: {e}")

print("\n------------------------------------")
print("All downloads complete.")
print("------------------------------------")