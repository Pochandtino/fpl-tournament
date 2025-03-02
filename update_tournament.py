import requests
import json

LEAGUE_ID = "857"
BASE_URL = "https://fantasy.premierleague.com/api"

def fetch_fpl_data(league_id):
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    response = requests.get(url)
    return response.json()

# Fetch and save data
data = fetch_fpl_data(LEAGUE_ID)
with open("data.json", "w") as f:
    json.dump(data, f, indent=4)

print("✅ Data updated successfully.")
