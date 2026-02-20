"""Smart transfer analysis logic for FPL"""
from typing import List, Tuple
from models import Player, Transfer, Fixture
from config import DEFAULT_GAMES_AHEAD, MIN_POINT_GAIN, TRANSFER_COST


class TransferAnalyzer:
    """Analyzes potential transfers and recommends smart moves"""

    # Position-specific average points multiplier (based on historical FPL data)
    POSITION_WEIGHTS = {
        "GKP": 0.5,   # Goalkeepers score ~0.5 points per game
        "DEF": 0.8,   # Defenders score ~0.8 points per game
        "MID": 1.2,   # Midfielders score ~1.2 points per game
        "FWD": 1.5    # Forwards score ~1.5 points per game
    }

    def __init__(self, players: List[Player], fixtures: List[Fixture], games_ahead: int = DEFAULT_GAMES_AHEAD):
        self.players = players
        self.fixtures = fixtures
        self.games_ahead = games_ahead
        
        # Build team fixture map for quick FDR lookup
        self.team_fixtures = self._build_team_fixtures()

    def _build_team_fixtures(self) -> dict:
        """Build a map of team -> list of upcoming fixtures"""
        team_fixtures = {}
        for fixture in self.fixtures:
            if fixture.team not in team_fixtures:
                team_fixtures[fixture.team] = []
            team_fixtures[fixture.team].append(fixture)
        return team_fixtures

    def get_average_fdr(self, player: Player) -> float:
        """
        Calculate average Fixture Difficulty Rating for a player's team.
        
        FDR ranges from 1 (easiest) to 5 (hardest).
        Lower FDR is better (easier fixtures incoming).
        """
        if player.team not in self.team_fixtures:
            return 3.0  # Default to neutral if no fixtures found
        
        team_fixtures = self.team_fixtures[player.team][:self.games_ahead]
        if not team_fixtures:
            return 3.0
        
        avg_fdr = sum(f.difficulty for f in team_fixtures) / len(team_fixtures)
        return round(avg_fdr, 2)

    def calculate_expected_points(self, player: Player) -> float:
        """
        Calculate expected points for a player over the next X games.
        
        Factors considered:
        - Recent form (from FPL)
        - Fixture Difficulty Rating (easier = more points)
        - Position-specific scoring potential
        - Injury/unavailability status
        """
        if not player.form:
            return 0.0

        # Base calculation: form * games ahead
        xp = player.form * self.games_ahead
        
        # Apply fixture difficulty adjustment (lower FDR is better)
        # Normalize FDR to a multiplier (3 = 1.0x, lower is better)
        fdr = self.get_average_fdr(player)
        fdr_multiplier = (6 - fdr) / 3  # Maps 1->1.67x, 3->1.0x, 5->0.33x
        xp *= fdr_multiplier
        
        # Apply position-specific weighting
        position_weight = self.POSITION_WEIGHTS.get(player.position, 1.0)
        xp *= position_weight
        
        # Injury/unavailability penalty
        if player.status and player.status != "a":  # 'a' = available
            xp *= 0.5
        
        return round(xp, 2)

    def get_player_analysis(self, player: Player) -> dict:
        """Get detailed analysis metrics for a player"""
        return {
            "form": round(player.form, 2) if player.form else 0.0,
            "fdr": self.get_average_fdr(player),
            "position_weight": self.POSITION_WEIGHTS.get(player.position, 1.0),
            "xp": self.calculate_expected_points(player)
        }

    def find_smart_transfers(self, current_player: Player, position: str = None) -> List[Transfer]:
        """
        Find all smart transfers for a given player.
        
        Args:
            current_player: Player to potentially transfer out
            position: Filter by position (if None, match current player's position)
        
        Returns:
            List of Transfer objects, sorted by net point gain
        """
        if position is None:
            position = current_player.position

        # Get all available players in the same position
        candidates = [p for p in self.players if p.position == position and p.id != current_player.id]

        transfers = []
        current_xp = self.calculate_expected_points(current_player)

        for candidate in candidates:
            candidate_xp = self.calculate_expected_points(candidate)
            expected_gain = candidate_xp - current_xp
            
            transfer = Transfer(
                player_out=current_player,
                player_in=candidate,
                games_ahead=self.games_ahead,
                expected_points_gain=expected_gain,
                transfer_cost=TRANSFER_COST
            )
            transfer.calculate_net_gain()
            
            transfers.append(transfer)

        # Sort by net point gain (best first)
        transfers.sort(key=lambda t: t.net_point_gain, reverse=True)
        
        # Return only good recommendations
        return [t for t in transfers if t.recommendation == "GOOD"]

    def recommend_transfers(self, current_squad: List[Player]) -> List[Transfer]:
        """
        Recommend smart transfers for the entire squad.
        
        Args:
            current_squad: List of players currently in the squad
        
        Returns:
            Prioritized list of recommended transfers
        """
        all_recommendations = []
        
        for player in current_squad:
            transfers = self.find_smart_transfers(player)
            all_recommendations.extend(transfers)
        
        # Sort by net point gain
        all_recommendations.sort(key=lambda t: t.net_point_gain, reverse=True)
        
        return all_recommendations
