import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# --- Configuration ---
pseudo_ticker = 'BOEING_BALANCED_70_30' # New name to avoid confusion

# <<< NEW, MORE AGGRESSIVE BLEND >>>
blend_components = {
    'SPY': 0.45,
    'QQQ': 0.25,
    'AGG': 0.30
}

output_dir = 'stock_data_yfinance'
end_date = datetime.today()
start_date = end_date - timedelta(days=20 * 365)
initial_value = 1.0

print(f"Creating a custom 70/30 balanced proxy file for '{pseudo_ticker}'...")

# --- (The rest of the script is identical) ---
try:
    component_data = yf.download(
        list(blend_components.keys()),
        start=start_date,
        end=end_date,
        interval='1mo',
        auto_adjust=True
    )['Close']
    component_data = component_data.dropna()
    monthly_returns = component_data.pct_change().dropna()
    blended_returns = (monthly_returns * list(blend_components.values())).sum(axis=1)
    blended_price_index = (1 + blended_returns).cumprod() * initial_value
    blended_price_index.iloc[0] = initial_value
    final_data = blended_price_index.to_frame(name='Close')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{pseudo_ticker}.csv")
    final_data.to_csv(file_path)
    print("\nSUCCESS!")
    print(f"A new data file has been saved to: {file_path}")

    # --- Performance Verification ---
    print("\n--- Performance Verification ---")
    print("Comparing our new 70/30 proxy against the fund's reported returns.")
    if len(final_data) > 60:
        end_price = final_data['Close'].iloc[-1]
        price_1y_ago = final_data['Close'].iloc[-13]
        price_3y_ago = final_data['Close'].iloc[-37]
        price_5y_ago = final_data['Close'].iloc[-61]
        return_1y = (end_price / price_1y_ago) - 1
        return_3y_annualized = ((end_price / price_3y_ago) ** (1/3)) - 1
        return_5y_annualized = ((end_price / price_5y_ago) ** (1/5)) - 1
        print(f"\n1-Year Annualized Return:")
        print(f"  - Our Proxy:   {return_1y:.2%}")
        print(f"  - Fund Target: +12.18%")
        print(f"\n3-Year Annualized Return:")
        print(f"  - Our Proxy:   {return_3y_annualized:.2%}")
        print(f"  - Fund Target: +11.21%")
        print(f"\n5-Year Annualized Return:")
        print(f"  - Our Proxy:   {return_5y_annualized:.2%}")
        print(f"  - Fund Target: +7.70%")
    else:
        print("\nNot enough historical data to calculate 5-year returns for comparison.")
except Exception as e:
    print(f"\nAN ERROR OCCURRED: {e}")