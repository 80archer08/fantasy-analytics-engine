"""Repository interfaces for persistence operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from datetime import date

from fantasy_analytics_engine.domain.models import (
    FantasyPointEvent,
    HitterGameStat,
    PitcherGameStat,
    PlayerVOR,
    ReplacementLevelPoint,
    WeeklyFantasyPoints,
)


class Repository(ABC):
    """Persistence contract for raw and derived tables."""

    @abstractmethod
    def upsert_hitter_game_stats(self, rows: Iterable[HitterGameStat]) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_pitcher_game_stats(self, rows: Iterable[PitcherGameStat]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_hitter_game_stats(self, start_date: date, end_date: date) -> Sequence[HitterGameStat]:
        raise NotImplementedError

    @abstractmethod
    def get_pitcher_game_stats(self, start_date: date, end_date: date) -> Sequence[PitcherGameStat]:
        raise NotImplementedError

    @abstractmethod
    def upsert_fantasy_point_events(self, rows: Iterable[FantasyPointEvent]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_fantasy_point_events(self, start_date: date, end_date: date) -> Sequence[FantasyPointEvent]:
        raise NotImplementedError

    @abstractmethod
    def upsert_weekly_fantasy_points(self, rows: Iterable[WeeklyFantasyPoints]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_weekly_fantasy_points(self, start_date: date, end_date: date) -> Sequence[WeeklyFantasyPoints]:
        raise NotImplementedError

    @abstractmethod
    def upsert_replacement_levels(self, rows: Iterable[ReplacementLevelPoint]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_replacement_levels(self, start_date: date, end_date: date) -> Sequence[ReplacementLevelPoint]:
        raise NotImplementedError

    @abstractmethod
    def upsert_player_vor(self, rows: Iterable[PlayerVOR]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_latest_player_vor(self, as_of: date) -> Sequence[PlayerVOR]:
        raise NotImplementedError
