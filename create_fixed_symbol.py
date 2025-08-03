import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# --- Configuration ---
# The custom name for the fixed-income fund
pseudo_ticker = 'BOEING_Stable_2_84'

# The fixed annual return for the fund
annual_return = 0.0284 

# The directory to save the file
output_dir = 'stock_data_yfinance'

# Define the time period to match your other files
end_date = datetime.today()
start_date = end_date - timedelta(days=20 * 365)
initial_price = 100.0 # An arbitrary starting price

print(f"Creating a synthetic data file for '{pseudo_ticker}' with a fixed {annual_return:.2%} annual return.")

# --- Generate the Price History ---
try:
    # 1. Create a monthly date range for our history
    # 'MS' stands for 'Month Start' frequency
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')

    # 2. Convert the annual return to an equivalent monthly return
    # This is the key formula for the calculation
    monthly_return = (1 + annual_return)**(1/12) - 1

    # 3. Generate the price history by compounding the monthly return
    prices = []
    current_price = initial_price
    for _ in date_range:
        prices.append(current_price)
        current_price *= (1 + monthly_return)

    # 4. Create a pandas DataFrame in the correct format
    final_data = pd.DataFrame(data=prices, index=date_range, columns=['Close'])
    final_data.index.name = 'Date'

    # --- Save the Final Data ---
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{pseudo_ticker}.csv")
    final_data.to_csv(file_path)

    print("\nSUCCESS!")
    print(f"A new data file for your fixed-income fund has been saved to: {file_path}")
    print("This file can now be used by the portfolio optimizer.")

except Exception as e:
    print(f"\nAN ERROR OCCURRED: {e}")