import json

# Load data from JSON file
with open('data_test.json', 'r') as file:
    data = json.load(file)

#Robots End points test
def generate_oracle_data(user_request):
    request = {
        "asset": user_request.asset,
        "timeframe": user_request.timeframe,
        "request": user_request.request
    }

    binance_data = data

    return 'Hello from Oracle'