"""Core domain models for the fantasy analytics engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

LeagueSize = Literal[4, 12]
Position = Literal["C", "1B", "2B", "3B", "SS", "OF", "UTIL", "SP", "RP", "P"]
Role = Literal["SP", "RP", "UNKNOWN"]
RiskLabel = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass(frozen=True)
class Player:
    """Player identity and position eligibility."""

    player_id: str
    name: str
    mlb_team: str
    primary_position: Position
    eligible_positions: tuple[Position, ...]


@dataclass(frozen=True)
class HitterGameStat:
    """Raw per-game stat line for a hitter."""

    player_id: str
    game_date: date
    team: str
    lineup_position: int | None
    pa: int
    singles: int
    doubles: int
    triples: int
    hr: int
    bb: int
    k: int
    runs: int
    rbi: int
    sb: int


@dataclass(frozen=True)
class PitcherGameStat:
    """Raw per-game stat line for a pitcher."""

    player_id: str
    game_date: date
    team: str
    role: Role
    ip_outs: int
    hits_allowed: int
    er: int
    bb_allowed: int
    k: int
    qs: int
    sv: int
    hd: int
    blown_sv: int


@dataclass(frozen=True)
class FantasyPointEvent:
    """Per-game fantasy points output from the scoring engine."""

    player_id: str
    game_date: date
    fantasy_points: float


@dataclass(frozen=True)
class WeeklyFantasyPoints:
    """Weekly-aggregated fantasy points."""

    player_id: str
    week_start: date
    week_end: date
    weekly_fp: float


@dataclass(frozen=True)
class ReplacementLevelPoint:
    """Replacement level baseline for a league-size/position/week."""

    position: Position
    league_size: LeagueSize
    week_start: date
    rl_weekly_fp_raw: float
    rl_weekly_fp_smoothed: float


@dataclass(frozen=True)
class PlayerVOR:
    """Value-over-replacement output record for one player and league size."""

    player_id: str
    league_size: LeagueSize
    best_eligible_position: Position
    expected_weekly_fp: float
    replacement_weekly_fp: float
    vor: float
    volatility_8w: float
    risk_label: RiskLabel
