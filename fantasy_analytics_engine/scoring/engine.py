"""Fantasy scoring engine."""

from __future__ import annotations

from collections.abc import Sequence

from fantasy_analytics_engine.config import ScoringWeights
from fantasy_analytics_engine.domain.models import FantasyPointEvent, HitterGameStat, PitcherGameStat
from fantasy_analytics_engine.scoring.rules import hitter_game_points, pitcher_game_points


class FantasyScoringEngine:
    """Deterministic game-level fantasy scoring engine."""

    def __init__(self, weights: ScoringWeights) -> None:
        self.weights = weights

    def score_hitter_games(self, rows: Sequence[HitterGameStat]) -> list[FantasyPointEvent]:
        return [
            FantasyPointEvent(
                player_id=row.player_id,
                game_date=row.game_date,
                fantasy_points=hitter_game_points(row, self.weights),
            )
            for row in rows
        ]

    def score_pitcher_games(self, rows: Sequence[PitcherGameStat]) -> list[FantasyPointEvent]:
        return [
            FantasyPointEvent(
                player_id=row.player_id,
                game_date=row.game_date,
                fantasy_points=pitcher_game_points(row, self.weights),
            )
            for row in rows
        ]

    def score_all_games(
        self,
        hitters: Sequence[HitterGameStat],
        pitchers: Sequence[PitcherGameStat],
    ) -> list[FantasyPointEvent]:
        return self.score_hitter_games(hitters) + self.score_pitcher_games(pitchers)
