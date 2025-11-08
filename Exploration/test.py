import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("alphavantage_API_KEY")
# month_date = date.today()
symbol = "IBM"

url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=30min&apikey={API_KEY}$&month=2025-01&outputsize=full"
r = requests.get(url)
data = r.json()

# with open('Exploration/data_IBM_30min2025-10-28.pkl', 'rb') as f:
#     data = pickle.load(f)

all_dates = list(data["Time Series (30min)"].keys())

print(all_dates)
