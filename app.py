import streamlit as st
import requests
import json
import random
import math

# Set up Streamlit UI
st.set_page_config(page_title="⚽ Fantasy Premier League Tournament", layout="wide")

st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# 🎯 User Inputs
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)
randomize_groups = st.sidebar.button("Randomize Groups")

# API Call Function
BASE_URL = "https://fantasy.premierleague.com/api"

def fetch_fpl_data(league_id):
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    response = requests.get(url)
    return response.json()

# Fetch and store data
if "fpl_data" not in st.session_state:
    if st.sidebar.button("Fetch Data"):
        st.session_state["fpl_data"] = fetch_fpl_data(league_id)

# 📌 Assign Teams to Groups (Manual + Randomization Option)
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    num_teams = len(teams)

    # ✅ Auto-assign teams into groups OR allow manual selection
    if "groups" not in st.session_state or randomize_groups:
        random.shuffle(teams)  # Shuffle if randomizing
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}
        for i, team in enumerate(teams):
            group_name = f"Group {chr(65 + (i % num_groups))}"
            st.session_state["groups"][group_name].append(team)

    # 📌 **Display Groups Clearly**
    st.subheader("🔀 Group Stage Teams")
    for group_name, members in st.session_state["groups"].items():
        st.markdown(f"### {group_name}")
        for team in members:
            st.write(f"**{team['entry_name']}** (Manager: {team['player_name']})")

    # 📌 **Calculate Required Game Weeks**
    teams_per_group = num_teams // num_groups
    is_odd = teams_per_group % 2 == 1  # Check if there’s a bye needed
    required_gameweeks = teams_per_group if is_odd else teams_per_group - 1  # Each team plays once per week

    st.sidebar.subheader("📅 Game Week Selection")
    selected_gameweeks = st.sidebar.multiselect(
        f"Choose Game Weeks (Required: {required_gameweeks})", 
        list(range(1, 39)), 
        default=list(range(1, required_gameweeks + 1))
    )

    # ⚠️ Warning if too few or too many Game Weeks are selected
    if len(selected_gameweeks) < required_gameweeks:
        st.sidebar.error(f"⚠️ Not enough Game Weeks selected! You need at least {required_gameweeks}.")
    elif len(selected_gameweeks) > required_gameweeks:
        st.sidebar.warning(f"⚠️ You have selected more Game Weeks than required ({len(selected_gameweeks)} vs {required_gameweeks}).")

    # 📅 **Fix Fixtures with Byes & Assign to Game Weeks**
    st.subheader("📅 Group Fixtures with Game Weeks")

    if len(selected_gameweeks) >= required_gameweeks:
        fixtures = []
        gameweek_schedule = {gw: [] for gw in selected_gameweeks}
        fixture_count = 0

        for group_name, members in st.session_state["groups"].items():
            team_list = members[:]  # Copy team list

            if len(team_list) % 2 == 1:
                team_list.append({"entry_name": "BYE", "player_name": ""})  # Add a Bye if odd number of teams

            round_robin_schedule = []
            num_rounds = len(team_list) - 1

            # **Round Robin Tournament Fixture Generator**
            for round_num in range(num_rounds):
                round_matches = []
                for i in range(len(team_list) // 2):
                    if team_list[i]['entry_name'] != "BYE" and team_list[-(i + 1)]['entry_name'] != "BYE":
                        round_matches.append(
                            f"{team_list[i]['entry_name']} vs {team_list[-(i + 1)]['entry_name']} (Group {group_name})"
                        )
                round_robin_schedule.append(round_matches)
                team_list.insert(1, team_list.pop())  # Rotate teams

            # Assign fixtures to Game Weeks
            for gw, matches in zip(selected_gameweeks, round_robin_schedule):
                for match in matches:
                    gameweek_schedule[gw].append(match)

        # ✅ **Display fixtures grouped by Game Week**
        for gw, games in gameweek_schedule.items():
            st.write(f"### Game Week {gw}")
            for game in games:
                st.write(game)
    else:
        st.error("❌ Cannot generate fixtures until enough Game Weeks are selected.")

    # 🏆 Knockout Stage Qualification
    st.subheader("🏆 Knockout Stage Qualification")
    qualified_teams = []
    
    for group_name, members in st.session_state["groups"].items():
        sorted_teams = sorted(members, key=lambda t: t['rank'])  # Placeholder for real points
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
