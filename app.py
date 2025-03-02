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

# 🎯 Tournament Configuration (User Input)
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)
teams_to_qualify = st.sidebar.slider("Teams to Qualify Per Group", 1, 4, 2)
best_records_to_qualify = st.sidebar.slider("Wildcard Teams (Best Records)", 0, 4, 2)
tie_breakers = st.sidebar.multiselect("Tie-Breakers", ["points", "goal_difference", "head_to_head"], default=["points", "goal_difference"])
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
    
    # Shuffle teams for random allocation
    random.shuffle(teams)
    groups = {f"Group {chr(65+i)}": teams[i::num_groups] for i in range(num_groups)}

    st.subheader("🔀 Group Stage Draw")
    for group, members in groups.items():
        st.markdown(f"### {group}")
        for team in members:
            st.write(f"**{team['entry_name']}** - Manager: {team['player_name']} (Rank: {team['rank']})")

    # ✅ Now we know how many times each team plays each other
    st.subheader("📅 Group Fixtures")
    fixtures = []
    for group_name, members in groups.items():
        num_teams = len(members)
        if num_teams % 2 != 0:
            members.append(None)  # Add a "bye" team if odd number

        group_fixtures = []
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                if members[i] and members[j]:  # Avoid "None" matches
                    for _ in range(matches_per_opponent):
                        group_fixtures.append(f"{members[i]['entry_name']} vs {members[j]['entry_name']}")

        fixtures.append({group_name: group_fixtures})
    
    # Display fixtures
    for fixture_group in fixtures:
        for group_name, games in fixture_group.items():
            st.write(f"### {group_name}")
            for game in games:
                st.write(game)

    # 🏆 Knockout Stage (Using Configurable Rules)
    st.subheader("🏆 Knockout Bracket")
    qualified_teams = []

    for group_name, members in groups.items():
        sorted_teams = sorted(members, key=lambda t: t['rank'])  # Sort by rank as a placeholder for points
        qualified_teams.extend(sorted_teams[:teams_to_qualify])

    # Wildcard spots (best records)
    wildcard_teams = sorted(teams, key=lambda t: t['rank'])[:best_records_to_qualify]
    qualified_teams.extend(wildcard_teams)

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
