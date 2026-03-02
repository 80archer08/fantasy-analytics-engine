"""TODO: implement module."""
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import (
    LeagueSize,
    Position,
    WeeklyFantasyPoints,
    ReplacementLevelPoint,
)
from fantasy_analytics_engine.config import ReplacementConfig

class VOREngine:
    def __init__(self, cfg: ReplacementConfig) -> None: ...
    
    def expected_weekly_fp(self, weekly_points: Sequence[WeeklyFantasyPoints]) -> dict[str, float]:
        """Use rolling/weighted recent weekly points to estimate expected weekly FP."""
        
    def volatility_8w(self, weekly_points: Sequence[WeeklyFantasyPoints]) -> dict[str, float]:
        """Stddev of last 8 weeks weekly FP."""
        
    def compute_player_vor(
        self,
        league_size: LeagueSize,
        weekly_points: Sequence[WeeklyFantasyPoints],
        rl_points: Sequence[ReplacementLevelPoint],
        player_positions: dict[str, tuple[str, ...]],
        role_stability_factor: dict[str, float] | None = None,
    ) -> list[PlayerVOR]:
        """
        Compute VOR by position eligibility and choose max VOR position.
        Optionally apply pitcher role stability multiplier.
        """