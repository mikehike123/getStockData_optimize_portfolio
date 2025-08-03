import requests
import csv
from datetime import datetime, timedelta
import argparse
from collections import defaultdict

# Your StockData.org API key
API_KEY = 'dQKqFaZjEaNNHNii46QipNr2jCC1yb651OP2qO4v'

# API endpoint for end-of-day historical data
URL = 'https://api.stockdata.org/v1/data/eod'

def fetch_data(symbol, date_from, date_to):
    """Fetches daily stock data from the StockData.org API."""
    print("Requesting daily data from StockData.org...")
    params = {
        'api_token': API_KEY,
        'symbols': symbol,
        'date_from': date_from,
        'date_to': date_to,
        'format': 'json',
    }
    response = requests.get(URL, params=params)
    response.raise_for_status()  # Raise exception if error

    data = response.json()
    if 'data' not in data:
        raise ValueError("Unexpected response structure: 'data' key missing.")

    # Sort data by date ascending to ensure correct resampling
    data['data'].sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%dT%H:%M:%S.%fZ'))
    return data['data']

def resample_to_weekly(daily_data):
    """Resamples daily data into weekly data."""
    print("Resampling data to weekly interval...")
    if not daily_data:
        return []

    weekly_data = defaultdict(list)
    for record in daily_data:
        # The date format from the API is like '2023-01-31T22:00:00.000Z'
        dt = datetime.strptime(record['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        # Group by year and week number
        year, week, _ = dt.isocalendar()
        weekly_data[(year, week)].append(record)

    resampled_data = []
    for week_key in sorted(weekly_data.keys()):
        week_records = weekly_data[week_key]
        if not week_records:
            continue

        # Sort records within the week by date to find first and last
        week_records.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%dT%H:%M:%S.%fZ'))

        # Get the date of the last day of the trading week
        last_day_of_week_str = week_records[-1]['date'].split('T')[0]

        weekly_summary = {
            'date': last_day_of_week_str,
            'open': week_records[0]['open'],
            'high': max(d['high'] for d in week_records),
            'low': min(d['low'] for d in week_records),
            'close': week_records[-1]['close'],
            'volume': sum(d['volume'] for d in week_records),
        }
        resampled_data.append(weekly_summary)

    return resampled_data


def save_to_csv(data, filename):
    """Saves the given data to a CSV file."""
    print(f"Saving data to {filename} ...")

    if not data:
        print("No data to save. The CSV file will not be created.")
        return

    # Define CSV header from keys in the first record
    fieldnames = data[0].keys()

    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # If the date has a time component, remove it for the CSV
            if 'T' in str(row.get('date', '')):
                row['date'] = row['date'].split('T')[0]
            writer.writerow(row)

    print(f"File saved successfully: {filename}")

def main():

    symbols = 'SPY'
    date_from = '2019-01-01'
    date_to = '2025-07-24'
    interval = 'weekly'

    
    for symbol in symbols.split(','):
        symbol = symbol.strip()
        if not symbols:
            print("No symbols provided. Exiting.")
            return
    
        daily_data = fetch_data(symbols, date_from, date_to)

        if interval == 'weekly':
            output_data = resample_to_weekly(daily_data)
        else:
            output_data = daily_data

        filename = f"stock_data/{symbol.lower()}_{interval}_{date_from}_to_{date_to}.csv"
        save_to_csv(output_data, filename)

if __name__ == '__main__':
    main()