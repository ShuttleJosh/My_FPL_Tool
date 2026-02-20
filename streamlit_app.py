"""
FPL Transfer Analyzer - Streamlit Web App
Helps you identify smart transfers based on expected points and fixture difficulty
"""
import streamlit as st
import pandas as pd
from api_client import FPLAPIClient
from transfer_analyzer import TransferAnalyzer
from config import DEFAULT_GAMES_AHEAD, TRANSFER_COST


def load_data():
    """Load data from FPL API"""
    with st.spinner("Fetching FPL data..."):
        client = FPLAPIClient()
        players = client.get_all_players()
        fixtures = client.get_fixtures()
        client.close()
    return players, fixtures


def main():
    st.set_page_config(page_title="FPL Transfer Analyzer", layout="wide")
    st.title("⚽ FPL Transfer Analyzer")
    st.markdown("Smart transfer recommendations based on expected points and fixture difficulty")

    # Load data
    players, fixtures = load_data()

    if not players:
        st.error("Failed to fetch FPL data. Please check your internet connection.")
        return

    # Sidebar configuration
    with st.sidebar:
        st.header("Your Squad")
        
        # FPL squad structure: 2 GK, 5 DEF, 5 MID, 3 FWD
        squad_positions = ["GKP", "GKP", "DEF", "DEF", "DEF", "DEF", "DEF", "MID", "MID", "MID", "MID", "MID", "FWD", "FWD", "FWD"]
        
        # Option to load from FPL manager ID
        st.subheader("Load Your Team")
        manager_id = st.number_input(
            "Enter your FPL Manager ID (optional)",
            min_value=0,
            help="Find this in your FPL profile URL (https://fantasy.premierleague.com/entry/[MANAGER_ID]/)"
        )
        
        if manager_id > 0 and st.button("Load My Team"):
            with st.spinner("Fetching your FPL team..."):
                client = FPLAPIClient()
                player_ids = client.get_manager_team(manager_id)
                client.close()
                
                if player_ids:
                    # Map player IDs to Player objects
                    fetched_players = [p for p in players if p.id in player_ids]
                    
                    if fetched_players:
                        # Organize fetched players by position
                        players_by_position = {}
                        for p in fetched_players:
                            if p.position not in players_by_position:
                                players_by_position[p.position] = []
                            players_by_position[p.position].append(p)
                        
                        # Assign players to squad slots by position
                        auto_filled_players = []
                        position_indices = {}
                        for i, position in enumerate(squad_positions):
                            if position not in position_indices:
                                position_indices[position] = 0
                            
                            if position in players_by_position and position_indices[position] < len(players_by_position[position]):
                                selected_player = players_by_position[position][position_indices[position]]
                                auto_filled_players.append(selected_player)
                                # Store in session state with the selectbox key
                                st.session_state[f"squad_player_{i}"] = selected_player
                                position_indices[position] += 1
                            else:
                                auto_filled_players.append(None)
                        
                        st.success(f"Loaded {len(fetched_players)} players from your team!")
                    else:
                        st.error("Could not match fetched players to current data.")
                else:
                    st.error("Could not fetch your team. Check your Manager ID is correct.")
        
        # Build current squad
        current_squad = []
        squad_values = []
        
        st.subheader("Select Players")
        
        for i, position in enumerate(squad_positions):
            col1, col2 = st.columns([3, 1])
            with col1:
                # Filter players by position
                available_players = [p for p in players if p.position == position]
                
                # Initialize session state for this player slot if not exists
                if f"squad_player_{i}" not in st.session_state:
                    st.session_state[f"squad_player_{i}"] = available_players[0] if available_players else None
                
                player = st.selectbox(                
                    f"{position}",
                    options=available_players,
                    key=f"squad_player_{i}",
                    format_func=lambda p: f"{p.name} - £{p.price/10:.1f}m"
                )
                if player:
                    current_squad.append(player)
                    squad_values.append(player.price)
        
        # Calculate budget
        total_squad_value = sum(squad_values) if squad_values else 0
        budget = 1000 - total_squad_value  # FPL budget is 100m = 1000 x 0.1m
        
        st.divider()
        st.subheader("Budget")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Squad Value", f"£{total_squad_value/10:.1f}m")
        with col2:
            st.metric("Available Budget", f"£{budget/10:.1f}m")
        with col3:
            st.metric("Players", f"{len(current_squad)}/15")
        
        st.divider()
        st.header("Settings")
        
        with st.expander("ℹ️ How expected points are calculated", expanded=False):
            st.write("""
            **Expected Points (xP) Formula:**
            ```
            xP = Form × Games Ahead × FDR_Multiplier × Position_Weight × Injury_Penalty
            ```
            
            **Components:**
            - **Form**: Player's recent form rating from FPL (higher = better)
            - **Games Ahead**: Number of upcoming games you select (1-19)
            - **FDR (Fixture Difficulty Rating)**: Average difficulty of next X games
              - 1-2 (Easy) = Better bonus
              - 3 (Neutral) = 1.0× multiplier
              - 4-5 (Hard) = Penalty
            - **Position Weight**: Natural scoring potential by position
              - GKP: 0.5× (goalkeepers score less)
              - DEF: 0.8×
              - MID: 1.2×
              - FWD: 1.5× (forwards score most)
            - **Injury Penalty**: -50% if player is unavailable
            
            **A transfer is marked "GOOD" if:**
            - Net Point Gain ≥ 5 points (accounts for 4-point transfer cost)
            """)
        
        games_ahead = st.slider(
            "Games to analyze ahead",
            min_value=1,
            max_value=19,
            value=DEFAULT_GAMES_AHEAD,
            help="Number of upcoming games to consider for xP calculation"
        )
        min_gain = st.slider(
            "Minimum point gain",
            min_value=0,
            max_value=20,
            value=TRANSFER_COST + 5,
            help="Minimum expected point gain to recommend a transfer"
        )

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Quick Analysis", "Squad Transfer Plan", "Player Comparison"])

    with tab1:
        st.header("Quick Transfer Analysis")
        
        if not current_squad:
            st.warning("Please select your current squad in the sidebar first.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                selected_player = st.selectbox(
                    "Select player to replace (from your squad)",
                    options=current_squad,
                    format_func=lambda p: f"{p.name} ({p.position}) - £{p.price/10:.1f}m"
                )
            
            with col2:
                position_filter = st.checkbox("Same position only", value=True)

            if selected_player:
                analyzer = TransferAnalyzer(players, fixtures, games_ahead)
                transfers = analyzer.find_smart_transfers(
                    selected_player,
                    position=selected_player.position if position_filter else None
                )

                # Filter by budget
                affordable_transfers = [
                    t for t in transfers 
                    if (t.player_in.price - selected_player.price) <= budget
                ]

                if affordable_transfers:
                    st.success(f"Found {len(affordable_transfers)} affordable transfer(s)")
                    if len(transfers) > len(affordable_transfers):
                        st.info(f"({len(transfers) - len(affordable_transfers)} transfer(s) filtered out due to budget)")
                    
                    # Get detailed analysis for both players
                    analyzer = TransferAnalyzer(players, fixtures, games_ahead)
                    current_player_analysis = analyzer.get_player_analysis(selected_player)
                    
                    # Show player comparison summary
                    st.subheader("Player You're Replacing")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Form", f"{current_player_analysis['form']}")
                    with col2:
                        st.metric("FDR (next {} games)".format(games_ahead), f"{current_player_analysis['fdr']}")
                    with col3:
                        st.metric("Position Weight", f"{current_player_analysis['position_weight']:.2f}x")
                    with col4:
                        st.metric("Expected Points", f"{current_player_analysis['xp']:.1f}")
                    
                    st.divider()
                    
                    # Build comparison table
                    df = pd.DataFrame([{
                        "Player Out": selected_player.name,
                        "Form Out": f"{current_player_analysis['form']}",
                        "FDR Out": f"{current_player_analysis['fdr']}",
                        "→": "→",
                        "Player In": t.player_in.name,
                        "Form In": f"{analyzer.get_player_analysis(t.player_in)['form']}",
                        "FDR In": f"{analyzer.get_player_analysis(t.player_in)['fdr']}",
                        "£ Cost": f"£{(t.player_in.price - selected_player.price)/10:.1f}m",
                        "xP Gain": f"{t.expected_points_gain:.1f}",
                        "Net Gain": f"{t.net_point_gain:.1f}",
                        "Rating": t.recommendation
                    } for t in affordable_transfers])
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    if len(transfers) > 0:
                        st.warning(f"No transfers within your budget of £{budget/10:.1f}m. Found {len(transfers)} matches outside budget.")
                    else:
                        st.info("No smart transfers found for this player.")

    with tab2:
        st.header("Full Squad Transfer Plan")
        
        if not current_squad:
            st.warning("Please select your current squad in the sidebar first.")
        else:
            st.info(f"Analyzing transfer plan for {len(current_squad)} players with £{budget/10:.1f}m budget")
            
            analyzer = TransferAnalyzer(players, fixtures, games_ahead)
            all_transfers = []
            
            for player in current_squad:
                transfers = analyzer.find_smart_transfers(player)
                affordable = [t for t in transfers if (t.player_in.price - player.price) <= budget]
                all_transfers.extend([(player, t) for t in affordable])
            
            if all_transfers:
                st.success(f"Found {len(all_transfers)} affordable transfer option(s)")
                
                df = pd.DataFrame([{
                    "Player Out": out.name,
                    "Out Form": f"{analyzer.get_player_analysis(out)['form']}",
                    "Out FDR": f"{analyzer.get_player_analysis(out)['fdr']}",
                    "→": "→",
                    "Player In": t.player_in.name,
                    "In Form": f"{analyzer.get_player_analysis(t.player_in)['form']}",
                    "In FDR": f"{analyzer.get_player_analysis(t.player_in)['fdr']}",
                    "£ Cost": f"£{(t.player_in.price - out.price)/10:.1f}m",
                    "xP Gain": f"{t.expected_points_gain:.1f}",
                    "Net Gain (pts)": f"{t.net_point_gain:.1f}",
                } for out, t in all_transfers])
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No smart transfers found within your budget for any squad players.")

    with tab3:
        st.header("Player Comparison")
        col1, col2 = st.columns(2)
        with col1:
            player1 = st.selectbox(
                "Player 1",
                options=players,
                format_func=lambda p: f"{p.name} - £{p.price/10:.1f}m",
                key="p1"
            )
        
        with col2:
            player2 = st.selectbox(
                "Player 2",
                options=players,
                format_func=lambda p: f"{p.name} - £{p.price/10:.1f}m",
                key="p2"
            )

        if player1 and player2:
            comparison_df = pd.DataFrame([{
                "Stat": stat,
                "Player 1": value1,
                "Player 2": value2
            } for stat, value1, value2 in [
                ("Name", player1.name, player2.name),
                ("Position", player1.position, player2.position),
                ("Price", f"£{player1.price/10:.1f}m", f"£{player2.price/10:.1f}m"),
                ("Total Points", player1.points, player2.points),
                ("Form", f"{player1.form:.2f}", f"{player2.form:.2f}"),
                ("Selected by %", f"{player1.selected_by_percent:.1f}%", f"{player2.selected_by_percent:.1f}%"),
            ]])
            
            st.dataframe(comparison_df, use_container_width=True)


if __name__ == "__main__":
    main()
