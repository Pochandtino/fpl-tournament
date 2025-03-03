# 📂 File: app.py
# ⚽ Fantasy Premier League Tournament Setup

import streamlit as st
import requests
import json
import random
import os
import pandas as pd

# 🎯 UI Setup
st.set_page_config(page_title="⚽ Fantasy Premier League Tournament", layout="wide")
st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# ✅ Inputs for tournament setup
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)

# ✅ Manual or Random Assignment
manual_grouping = st.sidebar.checkbox("Manually Assign Groups", value=True)
randomize_groups = st.sidebar.button("Randomize Groups")

CONFIG_FILE = "tournament_config.json"

# 📌 Fetch League Data
@st.cache_data
def fetch_fpl_data(league_id):
    url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}

# 🎯 Load or fetch team data
if "fpl_data" not in st.session_state:
    if st.sidebar.button("Fetch Data"):
        st.session_state["fpl_data"] = fetch_fpl_data(league_id)

# 📌 Group Assignment
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    
    if "groups" not in st.session_state:
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}

    st.subheader("🔀 Assign Teams to Groups")

    if manual_grouping:
        manual_team_groups = {}
        for team in teams:
            selected_group = st.selectbox(
                f"{team['entry_name']} ({team['player_name']})",
                [f"Group {chr(65+i)}" for i in range(num_groups)],
                key=f"group_select_{team['entry']}"
            )
            manual_team_groups[team["entry"]] = selected_group

        if st.button("Save Group Assignments"):
            st.session_state["groups"] = {group: [] for group in manual_team_groups.values()}
            for team in teams:
                assigned_group = manual_team_groups.get(team["entry"], None)
                if assigned_group:
                    st.session_state["groups"][assigned_group].append(team)
            st.success("✅ Groups updated manually!")

    elif randomize_groups:
        random.shuffle(teams)
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}
        for i, team in enumerate(teams):
            st.session_state["groups"][f"Group {chr(65 + (i % num_groups))}"].append(team)
        st.success("✅ Groups randomized!")

    st.subheader("📌 Group Stage Teams")
    for group_name, members in st.session_state["groups"].items():
        st.markdown(f"### {group_name}")
        for team in members:
            st.write(f"**{team['entry_name']}** ({team['player_name']})")

    def save_settings():
        settings = {
            "league_id": league_id,
            "num_groups": num_groups,
            "matches_per_opponent": matches_per_opponent,
            "groups": st.session_state["groups"]
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        st.success("✅ Tournament settings saved!")

    if st.button("📥 Save Tournament Settings"):
        save_settings()
