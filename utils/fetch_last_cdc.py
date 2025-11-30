import json
import sys


def fetch_cdc(path="cdc_/last_cdc.json", symbol="Default"):
    try:
        if symbol == "Default":
            print("Missing symbol, Usage: fetch_last_cdc(symbol)")
            sys.exit()
        else:
            with open(path, "r") as f:
                json_data = json.load(f)

            key = f"{symbol}_cdc"
            last_cdc = json_data[key]
            return last_cdc
    except IndexError:
        print("Missing symbol, Usage: fetch_last_cdc(symbol)")
