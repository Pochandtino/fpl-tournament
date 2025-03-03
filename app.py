# 🏆 Ensure Groups & Fixtures are Loaded Before Proceeding
if "groups" not in st.session_state or not st.session_state["groups"]:
    st.warning("No groups have been assigned yet. Please assign teams to groups first.")
    st.stop()  # Stop execution to prevent further errors

if "fixtures" not in st.session_state or not st.session_state["fixtures"]:
    st.warning("No fixtures have been generated yet. Please generate fixtures first.")
    st.stop()

if "CURRENT_GAMEWEEK" not in st.session_state:
    st.warning("Current gameweek data is missing. Fetch league data first.")
    st.stop()

# 📊 Generate Standings for Each Group
st.subheader("📊 Group Standings")

# Iterate through groups
for group_name, members in st.session_state["groups"].items():
    st.markdown(f"### {group_name}")

    # Initialize standings table
    standings = {
        "Team": [],
        "Manager": [],
        "P": [],  # Games Played
        "W": [],  # Wins
        "D": [],  # Draws
        "L": [],  # Losses
        "FPL Points": [],  # Total FPL points scored
        "FPL Conceded": [],  # Total FPL points conceded
        "FPL Diff": [],  # FPL Goal Difference
        "Tournament Points": [],  # 3 for win, 1 for draw
    }

    # Prepare a dictionary to track stats
    team_results = {team["entry"]: {
        "P": 0, "W": 0, "D": 0, "L": 0, 
        "FPL Points": 0, "FPL Conceded": 0, 
        "Tournament Points": 0
    } for team in members}

    # Process each fixture
    for gw, match_list in st.session_state["fixtures"][group_name].items():
        if gw > st.session_state["CURRENT_GAMEWEEK"]:
            continue  # Ignore future gameweeks

        for match in match_list:
            home_team = match["home"]
            away_team = match["away"]
            home_id, away_id = home_team["entry"], away_team["entry"]

            home_points = st.session_state["team_points"].get(home_id, {}).get(gw, None)
            away_points = st.session_state["team_points"].get(away_id, {}).get(gw, None)

            if home_points is not None and away_points is not None:
                # Update stats
                team_results[home_id]["P"] += 1
                team_results[away_id]["P"] += 1

                team_results[home_id]["FPL Points"] += home_points
                team_results[away_id]["FPL Points"] += away_points

                team_results[home_id]["FPL Conceded"] += away_points
                team_results[away_id]["FPL Conceded"] += home_points

                if home_points > away_points:
                    team_results[home_id]["W"] += 1
                    team_results[home_id]["Tournament Points"] += 3
                    team_results[away_id]["L"] += 1
                elif away_points > home_points:
                    team_results[away_id]["W"] += 1
                    team_results[away_id]["Tournament Points"] += 3
                    team_results[home_id]["L"] += 1
                else:
                    team_results[home_id]["D"] += 1
                    team_results[away_id]["D"] += 1
                    team_results[home_id]["Tournament Points"] += 1
                    team_results[away_id]["Tournament Points"] += 1

    # Convert to DataFrame
    for team in members:
        team_id = team["entry"]
        standings["Team"].append(team["entry_name"])
        standings["Manager"].append(team["player_name"])
        standings["P"].append(team_results[team_id]["P"])
        standings["W"].append(team_results[team_id]["W"])
        standings["D"].append(team_results[team_id]["D"])
        standings["L"].append(team_results[team_id]["L"])
        standings["FPL Points"].append(team_results[team_id]["FPL Points"])
        standings["FPL Conceded"].append(team_results[team_id]["FPL Conceded"])
        standings["FPL Diff"].append(team_results[team_id]["FPL Points"] - team_results[team_id]["FPL Conceded"])
        standings["Tournament Points"].append(team_results[team_id]["Tournament Points"])

    # Convert to DataFrame & Sort
    df = pd.DataFrame(standings)
    
    if not df.empty:
        df = df.sort_values(by=["Tournament Points", "FPL Diff", "FPL Points"], ascending=[False, False, False])
        st.dataframe(df.set_index("Team"))
    else:
        st.warning(f"No matches played yet for {group_name}.")
