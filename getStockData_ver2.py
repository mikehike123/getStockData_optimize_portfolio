import http.client
import urllib.parse
import json

# Your API token from StockData.org
api_token = 'dQKqFaZjEaNNHNii46QipNr2jCC1yb651OP2qO4v'

# The symbols for the stocks you want to retrieve data for
symbols = 'AAPL,TSLA'

# The date range for the historical data
date_from = '2023-01-01'
date_to = '2023-01-31'

# Establish a connection to the API
conn = http.client.HTTPSConnection('api.stockdata.org')

# Define the parameters for the API request
params = urllib.parse.urlencode({
    'api_token': api_token,
    'symbols': symbols,
    'date_from': date_from,
    'date_to': date_to,
})

# Send the GET request
conn.request('GET', f'/v1/data/eod?{params}')

# Get the response
resp = conn.getresponse()

# Read and decode the response data
data = resp.read().decode('utf-8')

# Close the connection
conn.close()

# Parse the JSON response
try:
    response_data = json.loads(data)
    print(json.dumps(response_data, indent=4))
except json.JSONDecodeError:
    print(f"Failed to decode JSON: {data}")
