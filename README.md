# Stocks ETL Pipeline

This project provides a robust, production-inspired ETL (Extract, Transform, Load) pipeline for fetching intraday stock data from the Alpha Vantage API and storing it in a PostgreSQL database. It features two main workflows: an automated, incremental daily pipeline and a manual historical backfill pipeline. The entire application is containerized using Docker for portability and ease of deployment.

## 🌿 Branching Strategy

| Branch | Data Provider | Status | Description |
| :--- | :--- | :--- | :--- |
| `yfinance-migration` | **yfinance** | **Active** | Primary development branch using `yfinance` for free intraday data. |
| `alphavantage-legacy` | **AlphaVantage** | **Legacy** | Archived version. Requires a Premium API key for intraday functionality. |

---

# Project Status: API Transition Notice

## ⚠️ Project Update: AlphaVantage Free Tier Changes
This project is currently undergoing a major transition. Due to recent changes in the **AlphaVantage API** policy, intraday time-series data (interval-based fetching) has been moved to their premium tier. The free tier is now limited to daily aggregate data only.

### The Problem
The current architecture relies on granular time intervals to function. Without access to intraday data, the core logic of the application is restricted.

---

## Strategic Decision
To keep this project functional and free to use, I have evaluated the following paths:

| Option | Strategy | Decision |
| :--- | :--- | :--- |
| **1** | **Purchase Premium API** | **Rejected**: Security concerns regarding the payment gateway and high subscription costs. |
| **2** | **Re-architecture** | **Rejected**: Limiting the project to "whole day" prices is inefficient and reduces the tool's utility. |
| **3** | **Migrate to `yfinance`** | **Selected**: Using the `yfinance` library allows for free, interval-based data retrieval while maintaining our current database structure. |

## Next Steps: Moving to `yfinance`
The next phase of development will involve:
1.  **Deprecating** the AlphaVantage API wrapper.
2.  **Integrating** the `yfinance` Python library for data ingestion.
3.  **Mapping** the new data objects to our existing database schema to ensure minimal downtime.

---

## Key Features

### General
*   **Containerized Environment:** Uses Docker and Docker Compose for a reproducible and isolated environment for the ETL application and PostgreSQL database.
*   **Robust Logging:** Implements comprehensive logging to files (`logs/YYYY-MM/YYYY-MM-DD.log`) and the console for clear monitoring and debugging.
*   **Email Notifications:** Automatically sends a summary of the daily ETL run via email, making it easy to monitor its status.
*   **Data Integrity:** Uses a composite `UNIQUE` constraint (`symbol`, `trade_timestamp_utc`) in the database to prevent duplicate data entries.
*   **Unit Tested:** Includes a unit test suite for the core API data fetching logic.

### 1. Incremental Daily Pipeline
*   **Automated Workflow:** The main pipeline is orchestrated by a master script that runs automatically via Docker Compose.
*   **Change Data Capture (CDC):** Efficiently fetches only new data since the last successful run by tracking the latest timestamp in `cdc_/last_cdc.json`.
*   **Scheduled Runs:** Designed to be run on a schedule (e.g., daily) to keep the database updated with the latest 30-minute intraday data.

### 2. Historical Backfill Pipeline
*   **Bulk Data Fetching:** Capable of fetching years of historical intraday data, month by month, for a comprehensive dataset.
*   **Memory Efficient:** Uses a generator-based approach to process data in monthly chunks, allowing it to handle very large datasets without running out of memory.
*   **Multi-Symbol Support:** Easily configurable to backfill data for a list of multiple stock symbols.
*   **Rate Limit Aware:** Includes delays to respect the Alpha Vantage API's rate limits during long-running backfill jobs.

## Architecture & Workflows

### 1. Incremental Daily Workflow
This is the primary, automated workflow for daily data collection.

1.  **Orchestration (`docker-compose.yml`):** The `docker-compose up` command starts the `etl` and `postgres` services. The `etl` service is configured to run the master script as its entry point.
2.  **Master Script (`scripts/master.py`):** This script orchestrates the pipeline. It executes `ETL/Load_psql.py` as a subprocess, captures its log output, and sends it as an email notification. It is currently hardcoded to process the symbol **IBM**.
3.  **Loading Script (`ETL/Load_psql.py`):** This script handles the core ETL logic for the incremental load.
    *   It calls `ETL/api_pipeline.py` to get the latest data.
    *   It connects to the PostgreSQL database, creates the `stocks_data` table if needed, and inserts the new data using an `ON CONFLICT DO NOTHING` clause to prevent duplicates.
    *   After a successful insert, it updates the timestamp in `cdc_/last_cdc.json` for the given symbol.
4.  **Extraction (`ETL/api_pipeline.py`):** This module reads the last CDC timestamp and fetches only newer 30-minute interval data from Alpha Vantage for the current month.

### 2. Historical Backfill Workflow
This workflow is designed for manually populating the database with a large amount of historical data.

1.  **Orchestrator (`scripts/backFill.py`):** This script is run manually. It contains a list of stock symbols and iterates through them.
2.  **Execution:** For each symbol, it should invoke a process that uses the `ETL/backFill_api_pipeline.py` to fetch all historical data and then loads it into the database.
    *   **Note:** The current implementation of `scripts/backFill.py` incorrectly calls the incremental loading script (`Load_psql.py`). For a true backfill, it should be modified to use `backFill_api_pipeline.py` and a corresponding loading script.
3.  **Extraction (`ETL/backFill_api_pipeline.py`):** This script is optimized for history. It fetches data for a given symbol month by month over a multi-year range (2000-present) and yields the data in chunks to be memory efficient.

## Getting Started

### Prerequisites

*   Python 3.11+
*   Docker & Docker Compose
*   Git

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Stocks_ETL
```

### 2. Set Up Environment Variables

Create a file named `.env` in the `Config/` directory (`Config/.env`). Copy the following content into it and replace the placeholder values.

```ini
# --- API Configuration ---
# Get your free API key from https://www.alphavantage.co/support/#api-key
alphavantage_API_KEY="YOUR_ALPHAVANTAGE_API_KEY"

# --- Database Configuration ---
# These credentials are used by the ETL service to connect to the Postgres container.
# The DB_HOST MUST match the service name in docker-compose.yml.
DB_NAME="stocksdb"
DB_USER="etl_user"
DB_PASS="etl_password"
DB_HOST="postgres"
DB_PORT="5432"

# --- Email Notification Configuration ---
# Use an app-specific password if using Gmail.
sender_email="your_email@gmail.com"
email_app_passwd="your_gmail_app_password"
receiver_email="recipient_email@example.com"
smtp_server="smtp.gmail.com"
smtp_port=587
```

## Usage

### Running the Daily Incremental Pipeline (Recommended)

This is the primary way to run the pipeline for daily updates.

1.  **Build and Run the Docker Containers:**
    ```bash
    docker-compose up --build
    ```
    This command will build the `etl` image, start the `postgres` and `etl` containers, and execute the pipeline. To run in the background, use `docker-compose up --build -d`.

2.  **Monitor Logs:**
    You can view the live logs of the ETL service with:
    ```bash
    docker-compose logs -f etl
    ```

3.  **Stopping the Services:**
    ```bash
    docker-compose down
    ```

### Running a Historical Backfill (Locally)

To perform a large historical backfill, you should run the backfill script directly.

1.  **Create a Virtual Environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .\.venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r Config/requirements.txt
    ```

3.  **Ensure Docker DB is Running:**
    Make sure the PostgreSQL database is running so the script can connect to it.
    ```bash
    docker-compose up -d postgres
    ```

4.  **Update `.env` for Local Connection:**
    In `Config/.env`, temporarily change `DB_HOST` to `localhost` since you are running the script from your local machine, not from within the Docker network.
    ```ini
    DB_HOST="localhost"
    ```

5.  **Run the Backfill Script:**
    The `scripts/backFill.py` script needs to be modified to use the correct backfill pipeline. A proper implementation would look like this:

    ```python
    # Example modification for scripts/backFill.py
    import sys
    sys.path.append('.') # Add project root to path
    from ETL.backFill_api_pipeline import backfill_data
    from ETL.Load_psql import load_chunk_to_db # Assuming a new function in Load_psql.py

    symbols_to_backfill = ["NVDA", "AAPL", "GOOGL"]
    for symbol in symbols_to_backfill:
        print(f"Starting backfill for {symbol}...")
        # backfill_data is a generator, so we process data in chunks
        for monthly_chunk in backfill_data(symbol):
            # You would need a function to load these chunks.
            # load_chunk_to_db(monthly_chunk)
            print(f"Loaded a chunk for {symbol} with {len(monthly_chunk)} records.")
    ```

## Testing

The project includes unit tests for the incremental API pipeline.

To run the tests, first ensure the services are running:
```bash
docker-compose up -d
```

Then, execute the test suite inside the `etl` container:
```bash
docker-compose exec etl python -m unittest tests/test_api_pipeline.py
```

## Project Structure

```
.
├── docker-compose.yml      # Defines and configures the Docker services (ETL app, Postgres DB).
├── Dockerfile              # Builds the Docker image for the ETL application.
├── README.md               # This file.
├── run_script.bat          # Windows convenience script to run the daily pipeline locally.
├── production_guide.md     # A developer's guide to writing production-grade code.
├── cdc_/
│   └── last_cdc.json       # Stores CDC timestamps (e.g., {"IBM_cdc": "2025-11-30 12:00:00"}).
├── Config/
│   ├── .env                # Holds all environment variables (API keys, DB credentials, etc.).
│   └── requirements.txt    # Python dependencies for the project.
├── ETL/
│   ├── api_pipeline.py     # (Incremental) Fetches data newer than the last CDC timestamp.
│   ├── backFill_api_pipeline.py # (Historical) Fetches all data for a symbol, month by month.
│   └── Load_psql.py        # Loads data into PostgreSQL and manages the CDC state.
├── logs/
│   └── ...                 # Contains structured, dated log files for monitoring.
├── scripts/
│   ├── master.py           # Orchestrator for the daily incremental run (entry point for Docker).
│   └── backFill.py         # Orchestrator for running historical backfills for multiple symbols.
├── tests/
│   └── test_api_pipeline.py # Unit tests for the incremental data fetching logic.
└── utils/
    ├── fetch_last_cdc.py   # Utility to read the last CDC timestamp from the JSON file.
    └── send_email.py       # Utility to send email notifications.
```
