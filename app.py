# 📂 File: app.py
# ⚽ Fantasy Premier League Tournament Manager

import streamlit as st
import requests
import json
import random
import pandas as pd
from datetime import datetime

# 🎨 Streamlit UI Setup
st.set_page_config(page_title="Fantasy Premier League Tournament", layout="wide")
st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# 🎯 User Inputs
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)

# ✅ Manual Group Assignment Toggle
manual_grouping = st.sidebar.checkbox("Manually Assign Groups", value=True)
randomize_groups = st.sidebar.button("Randomize Groups")

# 📌 Fetch API Data
BASE_URL = "https://fantasy.premierleague.com/api"

def fetch_fpl_data(league_id):
    """Fetch league standings from FPL API."""
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}

def fetch_team_gameweek_points(manager_id):
    """Fetch team points for each gameweek"""
    url = f"{BASE_URL}/entry/{manager_id}/history/"
    response = requests.get(url).json()
    return {gw["event"]: gw["points"] for gw in response.get("current", [])}

def get_current_gameweek():
    """Fetch current FPL gameweek"""
    url = f"{BASE_URL}/bootstrap-static/"
    response = requests.get(url).json()
    current_gw = next((gw["id"] for gw in response["events"] if gw["is_current"]), None)
    return current_gw if current_gw else 1

CURRENT_GAMEWEEK = get_current_gameweek()

# 📌 Fetch League Data
if st.sidebar.button("Fetch Data"):
    st.session_state["fpl_data"] = fetch_fpl_data(league_id)

# 📌 Assign Teams to Groups
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    num_teams = len(teams)

    # ✅ Initialize Group Storage
    if "groups" not in st.session_state:
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}

    # 📌 Manual Group Assignment
    st.subheader("📌 Assign Teams to Groups")
    if manual_grouping:
        manual_team_groups = {}
        for team in teams:
            selected_group = st.selectbox(
                f"Select group for {team['entry_name']} ({team['player_name']})",
                [f"Group {chr(65+i)}" for i in range(num_groups)],
                key=f"group_select_{team['entry']}"
            )
            manual_team_groups[team["entry"]] = selected_group
        
        if st.button("Save Groups"):
            st.session_state["groups"] = {group: [] for group in manual_team_groups.values()}
            for team in teams:
                assigned_group = manual_team_groups.get(team["entry"], None)
                if assigned_group:
                    st.session_state["groups"][assigned_group].append(team)
            st.success("✅ Groups updated manually!")

    # 📌 Randomize Groups
    elif randomize_groups:
        random.shuffle(teams)
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}
        for i, team in enumerate(teams):
            group_name = f"Group {chr(65 + (i % num_groups))}"
            st.session_state["groups"][group_name].append(team)
        st.success("✅ Groups randomized!")

    # 📌 Display Groups
    st.subheader("📌 Group Stage Teams")
    for group_name, members in st.session_state["groups"].items():
        st.markdown(f"### {group_name}")
        for team in members:
            st.write(f"**{team['entry_name']}** ({team['player_name']})")

    # 📌 Generate Fixtures
    st.subheader("📅 Group Fixtures & Live Results")
    fixtures = {}
    group_standings = {group: {} for group in st.session_state["groups"]}

    for group_name, members in st.session_state["groups"].items():
        fixtures[group_name] = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                for _ in range(matches_per_opponent):
                    fixtures[group_name].append(
                        {"home": members[i], "away": members[j]}
                    )

    # 📌 Show Fixtures
    for gw, match_list in enumerate(fixtures.values(), start=1):
        st.markdown(f"### Game Week {gw}")
        for match in match_list:
            home_team = match["home"]["entry_name"]
            away_team = match["away"]["entry_name"]
            home_manager = match["home"]["player_name"]
            away_manager = match["away"]["player_name"]

            # Fetch results
            home_points = fetch_team_gameweek_points(match["home"]["entry"]).get(gw, None)
            away_points = fetch_team_gameweek_points(match["away"]["entry"]).get(gw, None)

            # Ensure future gameweeks remain blank
            if gw > CURRENT_GAMEWEEK:
                home_points = None
                away_points = None

            st.write(f"**{home_team} ({home_manager})** {home_points or '-'} vs {away_points or '-'} **{away_team} ({away_manager})**")

    # 📌 Generate Standings
    st.subheader("📊 Group Standings")

    for group_name, standings in group_standings.items():
        st.markdown(f"### {group_name}")

        df = pd.DataFrame(list(standings.values()))
        df = df.sort_values(by=["Tournament Points", "FPL Diff", "FPL Points"], ascending=[False, False, False])

        st.dataframe(df.set_index("Team"))
