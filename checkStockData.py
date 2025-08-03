import pandas as pd
import os

# The directory where all your data files are stored
input_dir = 'stock_data_yfinance'

print(f"--- Checking Date Ranges in '{input_dir}' ---")

# A list to hold our results
date_info = []

# Loop through each file
for filename in os.listdir(input_dir):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_dir, filename)
        try:
            # Load the file, ensuring the 'Date' column is parsed correctly
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            
            if not df.empty:
                # Get the first and last date from the index
                start_date = df.index.min().strftime('%Y-%m-%d')
                end_date = df.index.max().strftime('%Y-%m-%d')
                date_info.append({
                    'File': filename, 
                    'StartDate': start_date, 
                    'EndDate': end_date
                })
            else:
                date_info.append({'File': filename, 'StartDate': 'EMPTY', 'EndDate': 'EMPTY'})
        except Exception as e:
            print(f"Could not process {filename}: {e}")

# Display the results in a clean table
if date_info:
    results_df = pd.DataFrame(date_info)
    print(results_df.to_string(index=False))
else:
    print("No CSV files found in the directory.")