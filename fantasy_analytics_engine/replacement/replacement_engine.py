"""TODO: implement module."""
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import (
    LeagueSize,
    Position,
    WeeklyFantasyPoints,
    ReplacementLevelPoint,
)
from fantasy_analytics_engine.config import ReplacementConfig

class ReplacementLevelEngine:
    def __init__(self, cfg: ReplacementConfig) -> None: ...
    
    def compute_weekly_replacement(
        self,
        weekly_points: Sequence[WeeklyFantasyPoints],
        player_positions: dict[str, tuple[Position, ...]],
        league_size: LeagueSize,
    ) -> list[ReplacementLevelPoint]:
        """
        For each week and position:
        1) sort platers by weekly_fp desc
        2) select ranks [cutoff + 1, cutoff + N]
        3) average replacement pool => raw RL
        4) apply rolling mean smoothing window (4 weeks by default)
        """