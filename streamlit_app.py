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

    # Sidebar configuration
    with st.sidebar:
        st.header("Settings")
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

    # Load data
    players, fixtures = load_data()

    if not players:
        st.error("Failed to fetch FPL data. Please check your internet connection.")
        return

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Quick Analysis", "Squad Transfer Plan", "Player Comparison"])

    with tab1:
        st.header("Quick Transfer Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_player = st.selectbox(
                "Select player to replace",
                options=players,
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

            if transfers:
                st.success(f"Found {len(transfers)} smart transfer(s)")
                
                df = pd.DataFrame([{
                    "Player In": t.player_in.name,
                    "Position": t.player_in.position,
                    "Price": f"£{t.player_in.price/10:.1f}m",
                    "Form": f"{t.player_in.form:.2f}",
                    "xP (next {})".format(games_ahead): f"{t.expected_points_gain:.1f}",
                    "Net Gain": f"{t.net_point_gain:.1f}",
                    "Recommendation": t.recommendation
                } for t in transfers])
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No smart transfers found for this player.")

    with tab2:
        st.header("Full Squad Transfer Plan")
        st.info("Upload your squad details (or we can auto-detect once login is implemented)")
        
        # Placeholder for squad management
        col1, col2 = st.columns(2)
        with col1:
            squad_size = st.number_input("Squad size", value=15, min_value=11, max_value=15)

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
