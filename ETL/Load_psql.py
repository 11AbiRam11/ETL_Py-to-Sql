import os
import psycopg2
import json
import pytz
from dotenv import load_dotenv
import sys
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


def load_data(symbol):
    """
    Load data from API pipeline into PostgreSQL database.
    """
    # Add project root to sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)

    import api_pipeline
    from utils.fetch_last_cdc import fetch_cdc

    last_cdc = fetch_cdc(symbol=symbol)

    load_dotenv()
    db_config = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    }

    # Standard time zone for stocks
    EASTERN = pytz.timezone("America/New_York")
    UTC = pytz.utc

    data, new_last_cdc = api_pipeline.fetch_data(symbol=symbol)

    if not data or (isinstance(data, list) and len(data[0]) == 0):
        logging.info(
            f"FROM: Load_psql.py - No new records found for {symbol}. Exiting!!"
        )
        # sys.exit()
    else:
        logging.info(f"Found {len(data)} new records after {last_cdc}")
        try:
            # First, connect to manage constraints.
            with psycopg2.connect(**db_config) as conn:
                conn.autocommit = True
                try:
                    with conn.cursor() as cur:
                        # Drop the old, incorrect constraint if it exists for idempotency
                        cur.execute(
                            "ALTER TABLE stocks_data DROP CONSTRAINT IF EXISTS trade_timestamp_utc_unique;"
                        )
                        logging.info(
                            "Dropped old constraint 'trade_timestamp_utc_unique' if it existed."
                        )

                        # Add the new, correct composite unique constraint
                        cur.execute(
                            "ALTER TABLE stocks_data ADD CONSTRAINT symbol_trade_timestamp_utc_unique UNIQUE (symbol, trade_timestamp_utc);"
                        )
                        logging.info(
                            "Successfully added composite UNIQUE constraint on 'symbol' and 'trade_timestamp_utc'."
                        )
                except psycopg2.Error:
                    pass  # Ignore error if constraint already exists

            # Now, connect again for the main ETL process
            with psycopg2.connect(**db_config) as conn:
                with conn.cursor() as cur:
                    create_table = """
                                        CREATE TABLE IF NOT EXISTS stocks_data(
                                        trade_timestamp_utc TIMESTAMPTZ NOT NULL,
                                        symbol VARCHAR(20) NOT NULL,
                                        open DECIMAL(10, 4) NOT NULL,
                                        high DECIMAL(10, 4) NOT NULL,
                                        low DECIMAL(10, 4) NOT NULL,
                                        close DECIMAL(10, 4) NOT NULL,
                                        volume BIGINT NOT NULL);
                                    """
                    cur.execute(create_table)

                    insert_query = """
                                    INSERT INTO stocks_data (trade_timestamp_utc, symbol, open, high, low, close, volume)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (symbol, trade_timestamp_utc) DO NOTHING;
                                    """

                    inserted_rows = 0
                    for row in data:
                        cur.execute(insert_query, row)
                        if cur.rowcount > 0:
                            inserted_rows += cur.rowcount

                    skipped_rows = len(data) - inserted_rows

                    if inserted_rows > 0:
                        logging.info(
                            f"{inserted_rows} {symbol} new rows inserted successfully."
                        )
                    if skipped_rows > 0:
                        logging.info(
                            f"{skipped_rows} {symbol} records already exist. Skipping."
                        )

                    # saving
                    conn.commit()
                    logging.info("Committed the changes")

        except psycopg2.Error as e:
            logging.error(e)

        logging.info(f"Updating the last_cdc...... for {symbol}")

        try:
            # Try reading existing
            try:
                with open("cdc_/last_cdc.json", "r") as f:
                    cdc = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                cdc = {}  # If missing or broken, create a fresh dict

            # Ensure key exists (and update value)
            cdc_key = f"{symbol}_cdc"
            if cdc_key not in cdc:
                logging.info(f"{cdc_key} not found. Creating with default value.")
                cdc[cdc_key] = "1900-01-01 00:00:00"  # default init value

            # Now update with new value
            cdc[cdc_key] = new_last_cdc

            # Write safely
            with open("cdc_/last_cdc.json", "w") as f:
                json.dump(cdc, f, indent=4)

            logging.info(f"last_cdc updated for {cdc_key}: {cdc[cdc_key]}")

        except Exception as e:
            logging.error(f"Unexpected error updating CDC: {e}")


if __name__ == "__main__":
    arg1 = sys.argv[1]
    load_data(symbol=arg1)
