import pandas as pd
import os

input_dir = 'stock_data_yfinance'

print(f"--- Checking for Missing Data Points ('Holes') in '{input_dir}' ---")

# Load all data into a single DataFrame
all_prices = {}
for filename in os.listdir(input_dir):
    if filename.endswith('.csv'):
        ticker = filename.split('.')[0]
        file_path = os.path.join(input_dir, filename)
        df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        all_prices[ticker] = df['Close']

price_df = pd.DataFrame(all_prices)

# Count the number of missing (NaN) values in each column
missing_counts = price_df.isna().sum()

print("\nNumber of missing data points per file:")
print(missing_counts)

# Check if there are any missing values at all
if missing_counts.sum() > 0:
    print("\nWARNING: Missing data detected. This is likely the cause of the failure.")
    print("The rows below show the specific dates where data is missing for at least one asset:")
    # Show the specific rows that contain at least one NaN
    print(price_df[price_df.isna().any(axis=1)])
else:
    print("\nSUCCESS: No missing data points were found.")