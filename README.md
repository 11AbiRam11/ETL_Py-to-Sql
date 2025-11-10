# Stocks ETL Pipeline

This project implements a robust and automated ETL (Extract, Transform, Load) pipeline for fetching intraday stock data from the Alpha Vantage API and storing it in a PostgreSQL database. The entire application is containerized using Docker for portability and ease of deployment.

## Key Features

- **Automated ETL Workflow:** The pipeline is orchestrated by a master script that automates the entire ETL process.
- **Intraday Stock Data:** Fetches 30-minute intraday stock data for a specified symbol (default is "IBM").
- **Change Data Capture (CDC):** Efficiently fetches only new data since the last run by tracking the last timestamp.
- **Robust Error Handling:** Implements retry logic for API calls and provides clear error messages.
- **PostgreSQL Integration:** Stores the cleaned and transformed data in a PostgreSQL database.
- **Email Notifications:** Sends an email summary of the ETL run, including any errors.
- **Containerized an-d Isolated:** Uses Docker and Docker Compose to create a reproducible and isolated environment.
- **Unit Tested:** Includes unit tests for the API data fetching logic.

## ETL Workflow

1.  **Orchestration:** The `docker-compose up` command starts the `etl` service, which runs the `scripts/master.py` script.
2.  **Execution:** The `master.py` script executes the main ETL logic in `ETL/Load_psql.py`.
3.  **CDC Check:** `Load_psql.py` fetches the timestamp of the last successfully processed record from the `cdc_/last_cdc.json` file.
4.  **Extract:** It then calls `ETL/api_pipeline.py`, which makes a request to the Alpha Vantage API for new intraday data for the "IBM" stock symbol, published after the last CDC timestamp.
5.  **Transform:** The raw JSON response is transformed into a structured format (a list of tuples) ready for database insertion.
6.  **Load:** `Load_psql.py` connects to the PostgreSQL database and inserts the new records into the `stocks_data` table.
7.  **Update CDC:** After a successful database commit, the CDC timestamp is updated in the `cdc_/last_cdc.json` file with the timestamp of the latest record.
8.  **Logging:** The `master.py` script captures all output (both standard output and errors) from the ETL process and writes it to a timestamped log file in the `logs/` directory.
9.  **Notification:** Finally, `master.py` sends the captured output in an email, providing a summary of the ETL run.

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
│   └── ...                 # Contains timestamped logs of each ETL run.
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