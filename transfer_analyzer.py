"""Smart transfer analysis logic for FPL"""
from typing import List, Tuple
from models import Player, Transfer, Fixture
from config import DEFAULT_GAMES_AHEAD, MIN_POINT_GAIN, TRANSFER_COST


class TransferAnalyzer:
    """Analyzes potential transfers and recommends smart moves"""

    def __init__(self, players: List[Player], fixtures: List[Fixture], games_ahead: int = DEFAULT_GAMES_AHEAD):
        self.players = players
        self.fixtures = fixtures
        self.games_ahead = games_ahead

    def calculate_expected_points(self, player: Player) -> float:
        """
        Calculate expected points for a player over the next X games.
        
        This is a simplified model - you can enhance it with:
        - FDR (Fixture Difficulty Rating)
        - Recent form trend
        - Ownership consideration
        - Position-specific weighting
        """
        if not player.form:
            return 0.0

        # Simple calculation: average recent form * games ahead
        xp = player.form * self.games_ahead
        
        # Injury/unavailability penalty
        if player.status and player.status != "a":  # 'a' = available
            xp *= 0.5
        
        return xp

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
