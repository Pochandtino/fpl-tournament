# 📂 File: app.py
# 🔹 Fantasy Premier League Tournament Management App
# 🔹 Fetches real FPL data, organizes teams into groups, schedules fixtures, and tracks live results.

import streamlit as st
import requests
import json
import random
import pandas as pd

# 📌 Streamlit UI Setup
st.set_page_config(page_title="⚽ Fantasy Premier League Tournament", layout="wide")
st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# 🎯 User Inputs
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)
randomize_groups = st.sidebar.button("Randomize Groups")

# 🔗 API Configuration
BASE_URL = "https://fantasy.premierleague.com/api"

def fetch_fpl_data(league_id):
    """Fetch league standings from FPL API."""
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}

def fetch_team_gameweek_points(manager_id):
    """Fetch a team's FPL points for each Game Week."""
    url = f"{BASE_URL}/entry/{manager_id}/history/"
    response = requests.get(url)

    if response.status_code != 200:
        return {}  # Return empty dict if API call fails

    data = response.json()
    if "current" in data:
        return {gw["event"]: gw["points"] for gw in data["current"]}
    return {}  # Return empty dict if 'current' key is missing

# 📌 Fetch League Data
if "fpl_data" not in st.session_state:
    if st.sidebar.button("Fetch Data"):
        st.session_state["fpl_data"] = fetch_fpl_data(league_id)

# 📌 Assign Teams to Groups
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    num_teams = len(teams)

    # ✅ Auto-assign teams into groups OR allow manual selection
    if "groups" not in st.session_state or randomize_groups:
        random.shuffle(teams)
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
    is_odd = teams_per_group % 2 == 1  
    required_gameweeks = teams_per_group if is_odd else teams_per_group - 1  

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

    # 📅 **Generate Fixtures**
    st.subheader("📅 Group Fixtures & Live Results")

    if len(selected_gameweeks) >= required_gameweeks:
        gameweek_schedule = {gw: [] for gw in selected_gameweeks}
        standings = {group: {} for group in st.session_state["groups"]}

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
                    gameweek_schedule[gameweek].append((group_name, home_team, away_team))

                team_list.insert(1, team_list.pop())

        # 🔹 **Fetch real-time FPL points and update standings**
        for gameweek, matches in gameweek_schedule.items():
            st.write(f"### Game Week {gameweek}")
            for group_name, home_team, away_team in matches:
                home_team_id = home_team.get("entry", None)
                away_team_id = away_team.get("entry", None)

                if home_team_id and away_team_id:
                    home_points = fetch_team_gameweek_points(home_team_id).get(gameweek, 0)
                    away_points = fetch_team_gameweek_points(away_team_id).get(gameweek, 0)
                else:
                    home_points, away_points = 0, 0  # Default to 0 if no valid ID

                result = f"**{home_team['entry_name']}** ({home_points}) vs **{away_team['entry_name']}** ({away_points})"
                st.write(result)

                if group_name not in standings:
                    standings[group_name] = {}

                for team, score, conceded in [(home_team, home_points, away_points), (away_team, away_points, home_points)]:
                    if team["entry"] not in standings[group_name]:
                        standings[group_name][team["entry"]] = {
                            "Team": team["entry_name"],
                            "P": 0, "W": 0, "D": 0, "L": 0, "F": 0, "A": 0, "GD": 0, "Pts": 0
                        }

                    standings[group_name][team["entry"]]["P"] += 1
                    standings[group_name][team["entry"]]["F"] += score
                    standings[group_name][team["entry"]]["A"] += conceded
                    standings[group_name][team["entry"]]["GD"] = standings[group_name][team["entry"]]["F"] - standings[group_name][team["entry"]]["A"]

                    if score > conceded:
                        standings[group_name][team["entry"]]["W"] += 1
                        standings[group_name][team["entry"]]["Pts"] += 3
                    elif score < conceded:
                        standings[group_name][team["entry"]]["L"] += 1
                    else:
                        standings[group_name][team["entry"]]["D"] += 1
                        standings[group_name][team["entry"]]["Pts"] += 1

        # 🔹 **Display Group Standings**
        st.subheader("📊 Group Standings")
        for group_name, group_standings in standings.items():
            st.markdown(f"### {group_name}")
            df = pd.DataFrame(list(group_standings.values()))
            df = df.sort_values(by=["Pts", "GD", "F"], ascending=[False, False, False])
            st.dataframe(df)
