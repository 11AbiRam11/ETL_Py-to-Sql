import os
from datetime import datetime
import time
import requests
from dotenv import load_dotenv
import sys
import logging
from tenacity import retry, wait_fixed, stop_after_attempt

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# --- Logger Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Configure basic logging if not already done
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("alphavantage_API_KEY")
if not API_KEY:
    logger.error(
        "API key for AlphaVantage not found. Set alphavantage_API_KEY in .env file."
    )
    sys.exit(1)

# --- Constants ---
FORMAT_CODE = "%Y-%m-%d %H:%M:%S"
TIME_SERIES_KEY = "Time Series (30min)"
# Alphavantage free tier limit is 5 calls per minute (12 seconds minimum delay)
API_CALL_DELAY_SECONDS = 13


# --- Data Range for Backfilling ---
# Generates a list of year-month strings, e.g., ['2000-01', '2000-02', ..., '2024-12']
year_months = [
    f"{year}-{month:02d}"
    for year in range(2000, datetime.now().year + 1)
    for month in range(1, 13)
]


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def fetch_data(symbol: str, target_year_month: str):
    """
    Fetches intraday stock data from AlphaVantage for a specific year and month.

    Args:
        symbol (str): The stock ticker (e.g., 'V').
        target_year_month (str): The month to fetch (e.g., '2024-05').

    Returns:
        A list of tuples, where each tuple represents a row of stock data.
        Returns an empty list if there's an error or no data.
    """
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=30min&apikey={API_KEY}&month={target_year_month}"
    logger.info(f"Attempting to fetch {symbol} for month {target_year_month}...")

    # --- API Request Block ---
    try:
        r = requests.get(url)
        r.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        data = r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed for {target_year_month} after retries: {e}")
        raise  # Re-raise to let tenacity handle the retry

    # --- Error and Rate Limit Check ---
    if TIME_SERIES_KEY not in data:
        error_message = data.get("Note", data.get("Information", "Unknown API error."))
        logger.error(
            f"Error fetching data for {symbol} ({target_year_month}): {error_message}"
        )
        return []  # Return empty list to signify failure

    all_timestamps = list(data[TIME_SERIES_KEY].keys())

    if not all_timestamps:
        logger.info(
            f"No data returned for {symbol} for month {target_year_month}. Skipping."
        )
        return []

    # Get raw keys from the first data point
    raw_keys = list(data[TIME_SERIES_KEY][all_timestamps[0]].keys())

    # --- Build Final Dataset ---
    final_data = [
        tuple(
            [ts]
            + [symbol]
            + [float(data[TIME_SERIES_KEY][ts][key]) for key in raw_keys]
        )
        for ts in all_timestamps
    ]

    logger.info(
        f"Successfully fetched {len(final_data)} records for {symbol} in {target_year_month}."
    )
    return final_data


def backfill_data(symbol: str):
    """
    Primary generator function to iterate through all months and yield data chunks.
    This approach is memory-efficient as it doesn't load the entire dataset into memory.

    Args:
        symbol (str): The stock symbol to backfill (e.g., 'V').

    Yields:
        A list of tuples (a chunk of data for one month).
    """
    logger.info(f"Starting backfill for symbol: {symbol}...")

    # --- Loop through all required months ---
    for target_month in year_months:
        data_chunk = []
        try:
            data_chunk = fetch_data(symbol=symbol, target_year_month=target_month)
        except Exception as e:
            # This catches the final exception after tenacity retries have failed
            logger.error(
                f"Failed to fetch data for {symbol} in month {target_month}. Moving to next month. Error: {e}"
            )

        if data_chunk:
            yield data_chunk

        # --- Rate Limit Protection ---
        # Wait after every attempt, successful or not, to respect the API limit.
        logger.debug(
            f"Waiting for {API_CALL_DELAY_SECONDS} seconds to respect API rate limits..."
        )
        time.sleep(API_CALL_DELAY_SECONDS)

    logger.info(f"Backfill complete for {symbol}.")


if __name__ == "__main__":
    # --- Example Usage ---
    # This demonstrates how to use the `backfill_data` generator.
    # Instead of printing, you would typically insert each `monthly_data_chunk`
    # into your database here.

    total_records = 0
    # You can specify any stock symbol you want to backfill.
    symbol_to_backfill = "V"

    for monthly_data_chunk in backfill_data(symbol=symbol_to_backfill):
        if monthly_data_chunk:
            total_records += len(monthly_data_chunk)
            logger.info(
                f"Received chunk for processing with {len(monthly_data_chunk)} records."
            )
            # **TODO**: Add your database insertion logic here
            # Example: insert_into_database(monthly_data_chunk)

    logger.info(
        f"Finished processing backfill for {symbol_to_backfill}. Total records processed: {total_records}"
    )
