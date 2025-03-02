import streamlit as st
import requests
import json

# Set up Streamlit app
st.set_page_config(page_title="Fantasy PL Tournament", layout="wide")

st.title("⚽ Fantasy Premier League Tournament")

# Sidebar for settings
st.sidebar.header("Tournament Settings")
league_id = st.sidebar.text_input("Enter League ID", value="857")
update_data = st.sidebar.button("Fetch Data")

# API Call Function
BASE_URL = "https://fantasy.premierleague.com/api"

def fetch_fpl_data(league_id):
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    response = requests.get(url)
    return response.json()

if update_data:
    data = fetch_fpl_data(league_id)
    st.session_state["fpl_data"] = data

# Display Data
if "fpl_data" in st.session_state:
    st.subheader("League Standings")
    teams = st.session_state["fpl_data"]["standings"]["results"]
    
    for team in teams[:10]:  # Show only top 10 teams
        st.write(f"**{team['entry_name']}** - Manager: {team['player_name']} (Rank: {team['rank']})")
