import streamlit as st
import requests
import pandas as pd
import json
import random
import matplotlib.pyplot as plt

# Set up Streamlit UI
st.set_page_config(page_title="Fantasy PL Tournament", layout="wide")

st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# League ID input
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
    teams = st.session_state["fpl_data"]["standings"]["results"]
    
    # Create Groups Randomly
    num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
    random.shuffle(teams)
    groups = {f"Group {chr(65+i)}": teams[i::num_groups] for i in range(num_groups)}

    st.subheader("🔀 Group Stage Draw")
    for group, members in groups.items():
        st.markdown(f"### {group}")
        for team in members:
            st.write(f"**{team['entry_name']}** - Manager: {team['player_name']} (Rank: {team['rank']})")

    # Tournament Knockout Simulation
    st.subheader("🏆 Knockout Bracket")
    qualified_teams = []
    
    for group, members in groups.items():
        qualified_teams.extend(members[:2])  # Top 2 advance

    random.shuffle(qualified_teams)
    knockout_rounds = ["Quarter-Finals", "Semi-Finals", "Final"]
    
    for round_name in knockout_rounds:
        st.markdown(f"### {round_name}")
        new_round = []
        for i in range(0, len(qualified_teams), 2):
            if i+1 < len(qualified_teams):
                match = f"**{qualified_teams[i]['entry_name']}** vs **{qualified_teams[i+1]['entry_name']}**"
                st.write(match)
                winner = random.choice([qualified_teams[i], qualified_teams[i+1]])
                new_round.append(winner)
        
        qualified_teams = new_round

    st.success(f"🏆 **Winner:** {qualified_teams[0]['entry_name']}")
