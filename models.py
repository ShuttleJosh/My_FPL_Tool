"""Data models for FPL Transfer Analyzer"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Player:
    """Represents an FPL player"""
    id: int
    name: str
    team: str
    position: str  # GKP, DEF, MID, FWD
    price: float  # in £0.1m (e.g., 50 = £5.0m)
    points: int  # Total points this season
    games_played: int
    selected_by_percent: float
    form: Optional[float] = None  # Recent form
    xp: Optional[float] = None  # Expected points for next X games
    chance_of_playing: Optional[int] = None
    status: Optional[str] = None  # injured, unavailable, etc.


@dataclass
class Transfer:
    """Represents a potential transfer"""
    player_out: Player
    player_in: Player
    games_ahead: int
    expected_points_gain: float
    transfer_cost: int = 4  # Points deducted for transfer
    net_point_gain: float = 0.0
    recommendation: str = ""  # "GOOD", "NEUTRAL", "BAD"

    def calculate_net_gain(self):
        """Calculate net point gain after transfer cost"""
        self.net_point_gain = self.expected_points_gain - self.transfer_cost
        if self.net_point_gain >= 5:
            self.recommendation = "GOOD"
        elif self.net_point_gain >= 0:
            self.recommendation = "NEUTRAL"
        else:
            self.recommendation = "BAD"
        return self.net_point_gain


@dataclass
class Fixture:
    """Represents an upcoming fixture"""
    gameweek: int
    team: str
    opponent: str
    difficulty: int  # 1-5 (1 = easiest)
    is_home: bool
