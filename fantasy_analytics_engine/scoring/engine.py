"""TODO: implement module."""
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import (
    HitterGameStat,
    PitcherGameStat,
    FantasyPointEvent,
)
from fantasy_analytics_engine.config import ScoringWeights

class FantasyScoringEngine:
    def __init__(self, weights: ScoringWeights) -> None: ...
    
    def score_hitter_games(self, rows: Sequence[HitterGameStat]) -> list[FantasyPointEvent]: ...
    def score_pitcher_games(self, rows: Sequence[PitcherGameStat]) -> list[FantasyPointEvent]: ...
    def score_all_games(
        self,
        hitters: Sequence[HitterGameStat],
        pitchers: Sequence[PitcherGameStat],
    ) -> list[FantasyPointEvent]: ...