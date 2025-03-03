# 📊 Generate Standings for Each Group
st.subheader("📊 Group Standings")

# Define standings table structure
for group_name, members in st.session_state["groups"].items():
    st.markdown(f"### {group_name}")

    # Initialize standings data structure
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

    team_results = {team["entry"]: {"P": 0, "W": 0, "D": 0, "L": 0, "FPL Points": 0, "FPL Conceded": 0, "Tournament Points": 0} for team in members}

    # Process each fixture
    for gw, match_list in enumerate(fixtures[group_name], start=1):
        if gw > CURRENT_GAMEWEEK:
            continue  # Ignore future gameweeks

        for match in match_list:
            home_team = match["home"]
            away_team = match["away"]
            home_id, away_id = home_team["entry"], away_team["entry"]

            home_points = fetch_team_gameweek_points(home_id).get(gw, None)
            away_points = fetch_team_gameweek_points(away_id).get(gw, None)

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

    # Convert data to DataFrame
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

    df = pd.DataFrame(standings)
    
    # Sort by Tournament Points, then FPL Diff, then FPL Points
    df = df.sort_values(by=["Tournament Points", "FPL Diff", "FPL Points"], ascending=[False, False, False])

    # Display standings
    st.dataframe(df.set_index("Team"))
