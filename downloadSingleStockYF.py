import yfinance as yf
import pandas as pd

# Define a single, common ticker
ticker = 'MSFT' # Using Microsoft as a simple example

print(f"--- Attempting to download data for {ticker} ---")

try:
    # Use auto_adjust=True for clean, dividend-adjusted data
    data = yf.download(
        tickers=ticker,
        period="1y",       # Just get one year of data
        interval="1mo",    # On a monthly interval
        auto_adjust=True
    )
    
    print("\nSUCCESS: Data was downloaded.")
    print("--------------------------------------")
    print("Type of the downloaded object:", type(data))
    print("Is the header a MultiIndex?", isinstance(data.columns, pd.MultiIndex))
    print("--------------------------------------")
    print("\nFirst 5 rows of data:\n")
    print(data.head())
    print("--------------------------------------")

except Exception as e:
    print(f"\nAN ERROR OCCURRED: {e}")