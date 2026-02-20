"""FPL API Client for fetching data from the official Fantasy Premier League API"""
import requests
from typing import Dict, List, Optional
from config import FPL_API_BASE_URL, API_TIMEOUT, MAX_RETRIES
from models import Player, Fixture


class FPLAPIClient:
    """Client for interacting with the FPL API"""

    def __init__(self):
        self.base_url = FPL_API_BASE_URL
        self.timeout = API_TIMEOUT
        self.session = requests.Session()

    def _get(self, endpoint: str) -> Optional[Dict]:
        """Make a GET request to the FPL API with retries"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"Error fetching {url}: {e}")
                    return None
                continue

    def get_all_players(self) -> List[Player]:
        """Fetch all players and their stats"""
        data = self._get("/bootstrap-static/")
        if not data:
            return []

        players = []
        for player_data in data.get("elements", []):
            player = Player(
                id=player_data["id"],
                name=f"{player_data['first_name']} {player_data['second_name']}",
                team=player_data.get("team", ""),
                position=self._get_position(player_data["element_type"]),
                price=player_data["now_cost"],
                points=player_data["total_points"],
                games_played=player_data["minutes"] // 90,  # Approximate
                selected_by_percent=float(player_data.get("selected_by_percent", 0)),
                form=float(player_data.get("form", 0)),
                chance_of_playing=player_data.get("chance_of_playing_next_round"),
                status=player_data.get("status"),
            )
            players.append(player)

        return players

    def get_fixtures(self) -> List[Fixture]:
        """Fetch upcoming fixtures"""
        data = self._get("/fixtures/")
        if not data:
            return []

        fixtures = []
        for fixture_data in data:
            if fixture_data.get("status") == "scheduled":
                fixture = Fixture(
                    gameweek=fixture_data.get("event", 0),
                    team=fixture_data.get("team_h_name", ""),
                    opponent=fixture_data.get("team_a_name", ""),
                    difficulty=fixture_data.get("team_h_difficulty", 3),
                    is_home=True,
                )
                fixtures.append(fixture)

        return fixtures

    def get_player_history(self, player_id: int) -> Optional[Dict]:
        """Fetch historical data for a specific player"""
        return self._get(f"/element/{player_id}/")

    @staticmethod
    def _get_position(position_id: int) -> str:
        """Convert FPL position ID to position string"""
        positions = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return positions.get(position_id, "Unknown")

    def close(self):
        """Close the session"""
        self.session.close()
