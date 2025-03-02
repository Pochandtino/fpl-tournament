import streamlit as st
import requests
import json
import random
import math

# Set up Streamlit UI
st.set_page_config(page_title="Fantasy PL Tournament", layout="wide")

st.title("⚽ Fantasy Premier League Tournament")
st.sidebar.header("Tournament Settings")

# 🎯 User Inputs
league_id = st.sidebar.text_input("Enter League ID", value="857")
num_groups = st.sidebar.slider("Number of Groups", 2, 8, 4)
matches_per_opponent = st.sidebar.radio("Matches Against Each Opponent", [1, 2], index=1)
randomize_groups = st.sidebar.button("Randomize Groups")

# Game Week Selection
st.sidebar.subheader("📅 Select Game Weeks for Group Stage")
selected_gameweeks = st.sidebar.multiselect("Choose Game Weeks", list(range(1, 39)), default=list(range(1, 9)))

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

# 📌 Assign Teams to Groups (Manually + Randomization Option)
if "fpl_data" in st.session_state:
    teams = st.session_state["fpl_data"]["standings"]["results"]
    num_teams = len(teams)

    # Auto-assign teams into groups OR allow manual selection
    if "groups" not in st.session_state or randomize_groups:
        random.shuffle(teams)  # Shuffle if randomizing
        st.session_state["groups"] = {f"Group {chr(65+i)}": [] for i in range(num_groups)}
        for i, team in enumerate(teams):
            group_name = f"Group {chr(65 + (i % num_groups))}"
            st.session_state["groups"][group_name].append(team)

    st.subheader("🔀 Group Stage Setup")
    for group_name in st.session_state["groups"]:
        st.markdown(f"### {group_name}")
        for i, team in enumerate(st.session_state["groups"][group_name]):
            selected_team = st.selectbox(
                f"{group_name} - Team {i+1}",
                [team["entry_name"] for team in teams],
                index=[team["entry_name"] for team in teams].index(team["entry_name"]),
                key=f"{group_name}_{i}"
            )
            # Assign the selected team to the group
            st.session_state["groups"][group_name][i] = next(t for t in teams if t["entry_name"] == selected_team)

    # 📅 Fixture Generation with Game Week Assignments
    st.subheader("📅 Group Fixtures with Game Weeks")
    
    total_fixtures = sum(len(members) * (len(members) - 1) // 2 * matches_per_opponent for members in st.session_state["groups"].values())
    total_gameweeks = len(selected_gameweeks)

    if total_gameweeks < math.ceil(total_fixtures / (num_teams // num_groups)):
        st.error("⚠️ Not enough Game Weeks selected to fit all matches! Increase the number of Game Weeks.")
    else:
        fixtures = []
        gameweek_schedule = {gw: [] for gw in selected_gameweeks}
        fixture_count = 0

        for group_name, members in st.session_state["groups"].items():
            group_fixtures = []
            for i in range(len(members)):
                for j in range(i+1, len(members)):  
                    for _ in range(matches_per_opponent):
                        fixture_count += 1
                        gameweek = selected_gameweeks[(fixture_count - 1) % total_gameweeks]
                        game = f"{members[i]['entry_name']} vs {members[j]['entry_name']} (GW {gameweek})"
                        gameweek_schedule[gameweek].append(game)

        # Display fixtures by Game Week
        for gw, games in gameweek_schedule.items():
            st.write(f"### Game Week {gw}")
            for game in games:
                st.write(game)

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
