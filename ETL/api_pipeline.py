import os
from datetime import datetime, date, timedelta
import time
import requests
from dotenv import load_dotenv
import sys
from tenacity import retry, wait_fixed, stop_after_attempt

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.fetch_last_cdc import fetch_cdc

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("alphavantage_API_KEY")

# Passing only year and month to adhere strictly to API/library documentation for reliability.
year_month = date.today().strftime("%Y-%m")

# --- Constants ---
# Defining date time format (used for both parsing CDC and API response)
FORMAT_CODE = "%Y-%m-%d %H:%M:%S"
TIME_SERIES_KEY = "Time Series (30min)"


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def fetch_data(symbol):
    """
    Fetches intraday stock data from AlphaVantage since the last CDC timestamp.
    Returns: (list of tuples) final_data, (datetime object) new_cdc_watermark
    """
    SYMBOL = symbol

    # 1. Fetch and Parse CDC Timestamp
    last_cdc_str = fetch_cdc()

    # FIX: Convert string CDC to datetime object for arithmetic
    try:
        last_cdc = datetime.strptime(last_cdc_str, FORMAT_CODE)
    except Exception as e:
        print(f"Error parsing last_cdc timestamp: {e}. Using default old date.")
        # Default to a very old date if CDC is missing or invalid
        last_cdc = datetime(2025 - 11 - 1)

    # 2. Add safe buffer to CDC
    # Use >= safe_cdc in filter to ensure all records *after* the last processed
    safe_cdc = last_cdc + timedelta(seconds=1)

    # 3. API Call Setup
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={SYMBOL}&interval=30min&apikey={API_KEY}&month={year_month}&outputsize=full"
    for i in range(3):  # Try 3 times
        try:
            r = requests.get(url)
            r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            data = r.json()
            break  # If successful, break the loop
        except requests.exceptions.RequestException as e:
            print(f"API call failed (attempt {i + 1}/3): {e}")
            time.sleep(5)  # Wait 5 seconds before trying again
    else:  # If the loop finishes without a break
        print("API call failed after 3 attempts. Exiting.")
        # You might want to send an email notification here
        return [], last_cdc

    # 4. Error and Rate Limit Check
    if TIME_SERIES_KEY not in data:
        print(
            f"Error fetching data for {SYMBOL}: {data.get('Note', 'Check API key or symbol, or check API rate limits. Exiting!!')}"
        )
        # Return empty list and current CDC without halting the program
        return [], last_cdc

    all_dates = list(data[TIME_SERIES_KEY].keys())

    # 5. Filter Data
    new_timestamps = [
        dt for dt in all_dates if datetime.strptime(dt, FORMAT_CODE) >= safe_cdc
    ]

    if not new_timestamps:
        # Use datetime.now() for the log, not the unused 'date_time' variable
        print(
            f"FROM: api_pipeline.py - No new data found since last CDC {last_cdc_str} Exiting!!"
        )
        return [[]], last_cdc

    # Get raw keys for one entry
    raw_keys = list(data[TIME_SERIES_KEY][new_timestamps[0]].keys())

    # 6. Build Final Dataset (Converting values to float)
    final_data = [
        tuple(
            [ts]  # Timestamp (str)
            + [SYMBOL]  # Symbol (str)
            + [
                float(data[TIME_SERIES_KEY][ts][key]) for key in raw_keys
            ]  # Values (float)
        )
        for ts in new_timestamps
    ]

    return final_data, all_dates[0]
