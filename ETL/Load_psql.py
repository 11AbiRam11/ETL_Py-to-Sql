import os
import psycopg2
import json
import pytz
from dotenv import load_dotenv
import sys
from tenacity import retry


def load_data():
    """
    Load data from API pipeline into PostgreSQL database.
    """
    # Add project root to sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)

    import api_pipeline
    from utils.fetch_last_cdc import fetch_cdc

    last_cdc = fetch_cdc()

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

    data, new_last_cdc = api_pipeline.fetch_data(symbol="IBM")

    if not data or (isinstance(data, list) and len(data[0]) == 0):
        print("FROM: Load_psql.py - No new records found. Exiting!!")
        # sys.exit()
    else:
        print(f"Found {len(data)} new records after {last_cdc}")
        try:
            # First, connect to add the constraint if it doesn't exist.
            with psycopg2.connect(**db_config) as conn:
                conn.autocommit = True
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "ALTER TABLE stocks_data ADD CONSTRAINT trade_timestamp_utc_unique UNIQUE (trade_timestamp_utc);"
                        )
                        print(
                            "Successfully added UNIQUE constraint to 'trade_timestamp_utc'."
                        )
                except psycopg2.Error:
                    pass  # Ignore error if constraint already exists or table has duplicates

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
                                    ON CONFLICT (trade_timestamp_utc) DO NOTHING;
                                    """

                    inserted_rows = 0
                    for row in data:
                        cur.execute(insert_query, row)
                        if cur.rowcount > 0:
                            inserted_rows += cur.rowcount

                    skipped_rows = len(data) - inserted_rows

                    if inserted_rows > 0:
                        print(f"{inserted_rows} rows inserted successfully.")
                    if skipped_rows > 0:
                        print(f"{skipped_rows} records already exist. Skipping.")

                    # saving
                    conn.commit()
                    print("Commited the changes")

        except psycopg2.Error as e:
            print(e)

        print("Updating the last_cdc......")
        try:
            # Try reading existing
            try:
                with open("cdc_/last_cdc.json", "r") as f:
                    cdc = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                cdc = {}  # If missing or broken, create a fresh dict

            # Update value
            cdc["cdc"] = new_last_cdc

            # Write safely
            with open("cdc_/last_cdc.json", "w") as f:
                json.dump(cdc, f, indent=4)

            print("last_cdc has been updated:", cdc["cdc"])

        except Exception as e:
            print("Unexpected error updating CDC:", e)


if __name__ == "__main__":
    load_data()
