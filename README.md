# Stocks ETL Pipeline

This project implements a robust and automated ETL (Extract, Transform, Load) pipeline for fetching intraday stock data from the Alpha Vantage API and storing it in a PostgreSQL database. The entire application is containerized using Docker for portability and ease of deployment.

## Key Features

- **Automated ETL Workflow:** The pipeline is orchestrated by a master script that automates the entire ETL process.
- **Intraday Stock Data:** Fetches 30-minute intraday stock data for a specified symbol (default is "IBM").
- **Change Data Capture (CDC):** Efficiently fetches only new data since the last run by tracking the last timestamp.
- **Robust Error Handling:** Implements retry logic for API calls and provides clear error messages.
- **PostgreSQL Integration:** Stores the cleaned and transformed data in a PostgreSQL database.
- **Data Integrity:** Enforces data integrity by applying a `UNIQUE` constraint on the `trade_timestamp_utc` column, preventing duplicate entries.
- **Email Notifications:** Sends an email summary of the ETL run, including any errors.
- **Containerized and Isolated:** Uses Docker and Docker Compose to create a reproducible and isolated environment.
- **Unit Tested:** Includes unit tests for the API data fetching logic.

## Architecture

The ETL pipeline is designed with a modular and containerized architecture:

1.  **Docker Compose (`docker-compose.yml`):** Defines and orchestrates the two main services:
    *   `postgres`: A PostgreSQL database instance for storing the stock data.
    *   `etl`: The Python application that runs the ETL process. It is configured to start only after the `postgres` service is healthy.

2.  **ETL Service (`Dockerfile`):** The `etl` service is built from a Python image. The `Dockerfile` copies the application code and installs the required dependencies from `Config/requirements.txt`. The entry point for the container is `scripts/master.py`.

3.  **Orchestrator (`scripts/master.py`):** This script is the main entry point. It:
    *   Executes the core ETL script (`ETL/Load_psql.py`) as a subprocess.
    *   Captures all `stdout` and `stderr` from the subprocess.
    *   Logs the output to a timestamped file within a month-wise subdirectory (e.g., `logs/YYYY-MM/`) inside the `logs/` directory.
    *   Sends the log content as an email notification.

4.  **ETL Core (`ETL/Load_psql.py`):** This script contains the main ETL logic:
    *   It reads the last successful run's timestamp from `cdc_/last_cdc.json`.
    *   It calls the `api_pipeline.py` module to fetch new data from the Alpha Vantage API.
    *   It connects to the PostgreSQL database, creates the `stocks_data` table if it doesn't exist, and idempotently adds a `UNIQUE` constraint on the `trade_timestamp_utc` column.
    *   It inserts the fetched data using an `INSERT ... ON CONFLICT DO NOTHING` query. This prevents duplicate records by silently skipping any rows that would violate the unique constraint.
    *   The script logs the number of rows successfully inserted and the number of rows skipped.
    *   Upon successful insertion, it updates the `last_cdc.json` file with the latest timestamp from the newly fetched data.

5.  **Data Extraction (`ETL/api_pipeline.py`):** This module is responsible for:
    *   Fetching intraday stock data from the Alpha Vantage API.
    *   Filtering the data to include only records newer than the last CDC timestamp.
    *   Transforming the JSON response into a clean, structured format for database insertion.

## Getting Started

Follow these instructions to get the ETL pipeline running on your local machine.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Stocks_ETL.git
    cd Stocks_ETL
    ```

2.  **Set up the Environment File:**
    Create a file named `.env` inside the `Config/` directory. This file will store your secret keys and database configuration. 

    ```ini
    # --- API Configuration ---
    alphavantage_API_KEY="YOUR_ALPHAVANTAGE_API_KEY"

    # --- Database Configuration ---
    DB_NAME="stocksdb"
    DB_USER="etl_user"
    DB_PASS="etl_password"
    DB_HOST="postgres" # This should match the service name in docker-compose.yml
    DB_PORT="5432"

    # --- Email Configuration ---
    EMAIL_SENDER_ADDRESS="your_email@example.com"
    EMAIL_SENDER_PASSWORD="your_email_password"
    EMAIL_RECIPIENT_ADDRESS="recipient_email@example.com"
    ```
    - Replace `"YOUR_ALPHAVANTAGE_API_KEY"` with your actual key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
    - Update the email settings to enable notifications.

### Running the Pipeline

1.  **Build and Run with Docker Compose:**
    From the root of the project directory, run the following command:
    ```bash
    docker-compose up --build
    ```
    This will build the Docker image for the `etl` service, start both the `postgres` and `etl` containers, and execute the pipeline. Add the `-d` flag to run in detached mode.

2.  **Monitor the Logs:**
    You can monitor the real-time output of the ETL service using:
    ```bash
    docker-compose logs -f etl
    ```
    The full output of each run is also saved to a timestamped file in the `/logs` directory.

## Project Structure

```
.
├── docker-compose.yml      # Defines and configures the Docker services (ETL app, Postgres DB).
├── Dockerfile              # Instructions to build the Docker image for the ETL application.
├── README.md               # This file.
├── cdc_/
│   └── last_cdc.json       # Stores the timestamp of the last fetched record to prevent duplicates.
├── Config/
│   ├── .env                # Environment variables (API keys, DB credentials, email settings).
│   └── requirements.txt    # Python dependencies for the project.
├── ETL/
│   ├── api_pipeline.py     # Fetches, filters, and transforms data from the Alpha Vantage API.
│   └── Load_psql.py        # Connects to the database, creates the table, and loads the data.
├── logs/
│   └── ...                 # Contains month-wise subdirectories, each holding timestamped logs of ETL runs for that month (e.g., `logs/YYYY-MM/output_timestamp.txt`).
├── scripts/
│   └── master.py           # The entry point script that orchestrates the ETL run, logging, and notifications.
├── tests/
│   └── test_api_pipeline.py  # Unit tests for the data fetching and processing logic.
└── utils/
    ├── fetch_last_cdc.py   # Utility to safely read the last CDC timestamp.
    └── send_email.py       # Utility to send email notifications.
```

## Testing

The project includes unit tests for the API pipeline logic. To run the tests, execute the following command while the services are running:

```bash
docker-compose exec etl python -m unittest tests/test_api_pipeline.py
```
This command runs the tests inside the `etl` container to ensure the environment is consistent.