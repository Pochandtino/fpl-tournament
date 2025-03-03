# 📂 File: app.py
# ⚽ Fantasy Premier League Tournament Management App

import streamlit as st
import requests
import json
import random
import pandas as pd
from datetime import datetime

# 📌 Streamlit UI Setup
st.set_page_config(page_title="⚽ Fantasy Premier League Tournament", layout="wide")
st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# 🎯 User Inputs
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)

# ✅ Manual Group Assignment Toggle
manual_grouping = st.sidebar.checkbox("Manually Assign Groups", value=True)
randomize_groups = st.sidebar.button("Randomize Groups")

# 📌 Get Current Game Week
BASE_URL = "https://fantasy.premierleague.com/api"

def get_current_gameweek():
    """Fetch current FPL gameweek from API"""
    url = f"{BASE_URL}/bootstrap-static/"
    response = requests.get(url).json()
    current_gw = next((gw["id"] for gw in response["events"] if gw["is_current"]), None)
    return current_gw if current_gw else 1  # Default to 1 if not found

CURRENT_GAMEWEEK = get_current_gameweek()

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

# 📌 Fetch League Data
if "fpl_data" not in st.session_state:
    if st.sidebar.button("Fetch Data"):
        st.session_state["fpl_data"] = fetch_fpl_data(league_id)

# 📌 Assign Teams to Groups (Manual or Random)
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    num_teams = len(teams)
    
    # ✅ Initialize group storage
    if "groups" not in st.session_state:
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}

    # 📌 Manual Group Assignment UI
    st.subheader("🔀 Assign Teams to Groups")
    
    if manual_grouping:
        # ✅ Manually assign teams to groups
        manual_team_groups = {}
        for team in teams:
            selected_group = st.selectbox(
                f"Select group for {team['entry_name']} ({team['player_name']})",
                [f"Group {chr(65+i)}" for i in range(num_groups)],
                key=f"group_select_{team['entry']}"
            )
            manual_team_groups[team["entry"]] = selected_group

        # ✅ Store manual group assignments
        if st.button("Save Manual Group Assignments"):
            st.session_state["groups"] = {group: [] for group in manual_team_groups.values()}
            for team in teams:
                assigned_group = manual_team_groups.get(team["entry"], None)
                if assigned_group:
                    st.session_state["groups"][assigned_group].append(team)
            st.success("✅ Groups updated manually!")

    else:
        # 📌 Randomly assign teams to groups
        if randomize_groups:
            random.shuffle(teams)
            st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}
            for i, team in enumerate(teams):
                group_name = f"Group {chr(65 + (i % num_groups))}"
                st.session_state["groups"][group_name].append(team)
            st.success("✅ Groups randomized!")

    # 📌 **Display Groups Clearly**
    st.subheader("📌 Group Stage Teams")
    for group_name, members in st.session_state["groups"].items():
        st.markdown(f"### {group_name}")
        for team in members:
            st.write(f"**{team['entry_name']}** ({team['player_name']})")

    # 📌 **Calculate Required Game Weeks**
    teams_per_group = num_teams // num_groups
    is_odd = teams_per_group % 2 == 1  
    required_gameweeks = teams_per_group if is_odd else teams_per_group - 1  

    st.sidebar.subheader("📅 Game Week Selection")
    selected_gameweeks = st.sidebar.multiselect(
        f"Choose Game Weeks (Required: {required_gameweeks})", 
        list(range(1, 39)), 
        default=list(range(1, required_gameweeks + 1))
    )

    # 📌 **Generate Fixtures & Scores**
    st.subheader("📅 Group Fixtures & Live Results")

    gameweek_schedule = {gw: [] for gw in selected_gameweeks}
    group_standings = {group_name: {} for group_name in st.session_state["groups"]}

    for group_name, members in st.session_state["groups"].items():
        team_list = members[:]
        if len(team_list) % 2 == 1:
            team_list.append({"entry_name": "BYE", "player_name": "", "entry": None})

        num_rounds = len(team_list) - 1
        for round_num in range(num_rounds):
            for i in range(len(team_list) // 2):
                home_team = team_list[i]
                away_team = team_list[-(i + 1)]
                if home_team["entry_name"] == "BYE" or away_team["entry_name"] == "BYE":
                    continue  # Skip bye matches

                gameweek = selected_gameweeks[(round_num) % required_gameweeks]
                home_points = fetch_team_gameweek_points(home_team["entry"]).get(gameweek, "-")
                away_points = fetch_team_gameweek_points(away_team["entry"]).get(gameweek, "-")

                # 🏆 Update Standings Only If Gameweek Is Completed
                if home_points != "-" and away_points != "-":
                    home_points = int(home_points)
                    away_points = int(away_points)

                    home_team_id = home_team["entry"]
                    away_team_id = away_team["entry"]

                    group_standings[group_name].setdefault(home_team_id, {"P": 0, "W": 0, "D": 0, "L": 0, "FPL_Points": 0, "FPL_Conceded": 0})
                    group_standings[group_name].setdefault(away_team_id, {"P": 0, "W": 0, "D": 0, "L": 0, "FPL_Points": 0, "FPL_Conceded": 0})

                    # Update results
                    group_standings[group_name][home_team_id]["P"] += 1
                    group_standings[group_name][away_team_id]["P"] += 1
                    group_standings[group_name][home_team_id]["FPL_Points"] += home_points
                    group_standings[group_name][away_team_id]["FPL_Points"] += away_points
                    group_standings[group_name][home_team_id]["FPL_Conceded"] += away_points
                    group_standings[group_name][away_team_id]["FPL_Conceded"] += home_points

                gameweek_schedule[gameweek].append((group_name, home_team, away_team, home_points, away_points))

    # 📌 **Show League Tables**
    st.subheader("📊 Group Standings")
    st.write(group_standings)  # TODO: Convert this into a DataFrame for better display
