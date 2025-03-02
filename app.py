import streamlit as st
import requests
import json
import random

# Set up Streamlit UI
st.set_page_config(page_title="Fantasy PL Tournament", layout="wide")

st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# 🎯 User Inputs
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

# 💡 Smart Group Allocation Function
def allocate_groups(teams):
    num_teams = len(teams)

    # ✅ Best group sizes for fairness
    ideal_group_sizes = [4, 5, 6]  # Common formats
    best_group_size = min(ideal_group_sizes, key=lambda x: abs(num_teams // x - num_teams / x))
    
    num_groups = num_teams // best_group_size
    remainder = num_teams % best_group_size

    # If remainder exists, some groups will have an extra team
    groups = [[] for _ in range(num_groups)]
    random.shuffle(teams)  # Shuffle to randomize distribution

    index = 0
    for team in teams:
        groups[index % num_groups].append(team)
        index += 1

    return groups

# 🎯 Process API Data
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    num_teams = len(teams)

    # 📌 Smart group allocation
    groups = allocate_groups(teams)

    # 🔀 Display Group Stage Draw
    st.subheader("🔀 Group Stage Draw")
    for i, group in enumerate(groups):
        st.markdown(f"### Group {chr(65+i)}")
        for team in group:
            st.write(f"**{team['entry_name']}** - Manager: {team['player_name']} (Rank: {team['rank']})")

    # 📅 Fixture Generation (Each team plays all other teams once)
    st.subheader("📅 Fixtures")
    fixtures = []
    for i, group in enumerate(groups):
        group_fixtures = []
        for j in range(len(group)):
            for k in range(j+1, len(group)):  # Each team plays each other once
                game = f"{group[j]['entry_name']} vs {group[k]['entry_name']}"
                group_fixtures.append(game)
        fixtures.append((f"Group {chr(65+i)}", group_fixtures))

    for group_name, games in fixtures:
        st.write(f"### {group_name}")
        for game in games:
            st.write(game)

    # 🏆 Knockout Stage Qualification
    st.subheader("🏆 Knockout Stage Qualification")
    qualified_teams = []
    
    for group in groups:
        sorted_teams = sorted(group, key=lambda t: t['rank'])  # Placeholder for real points
        qualified_teams.extend(sorted_teams[:2])  # Top 2 advance

    st.write("**Teams progressing to Knockouts:**")
    for team in qualified_teams:
        st.write(f"**{team['entry_name']}**")

    # 🏆 Knockout Bracket
    st.subheader("🏆 Knockout Bracket")
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
