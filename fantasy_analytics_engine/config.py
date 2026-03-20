"""Application configuration objects for V1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringWeights:
    """ESPN H2H points settings described in Requirements.pdf."""

    # hitters
    tb: float = 1.0
    runs: float = 1.0
    rbi: float = 1.0
    sb: float = 1.0
    hitter_bb: float = 1.0
    hitter_k: float = -1.0

    # pitchers
    ip: float = 3.0
    qs: float = 5.0
    hd: float = 2.0
    sv: float = 5.0
    pitcher_k: float = 1.0
    er: float = -2.0
    hits_allowed: float = -1.0
    pitcher_bb_allowed: float = -1.0
    blown_sv: float = -3.0


@dataclass(frozen=True)
class ReplacementConfig:
    """Knobs for replacement-level and VOR calculations."""

    replacement_pool_size: int = 3
    smoothing_window_weeks: int = 4
    volatility_window_weeks: int = 8


@dataclass(frozen=True)
class AppConfig:
    """Top-level app config container."""

    scoring: ScoringWeights = field(default_factory=ScoringWeights)
    replacement: ReplacementConfig = field(default_factory=ReplacementConfig)
