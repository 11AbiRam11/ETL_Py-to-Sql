import json


def fetch_cdc(path="cdc_/last_cdc.json"):
    with open(path, "r") as f:
        json_data = json.load(f)
    last_cdc = json_data["cdc"]

    return last_cdc
