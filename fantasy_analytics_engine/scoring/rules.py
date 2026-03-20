"""Scoring rules for ESPN H2H points leagues."""

from __future__ import annotations

from fantasy_analytics_engine.config import ScoringWeights
from fantasy_analytics_engine.domain.models import HitterGameStat, PitcherGameStat


def hitter_game_points(row: HitterGameStat, weights: ScoringWeights) -> float:
    """Compute hitter fantasy points for one game."""
    total_bases = row.singles + (2 * row.doubles) + (3 * row.triples) + (4 * row.hr)
    return (
        total_bases * weights.tb
        + row.runs * weights.runs
        + row.rbi * weights.rbi
        + row.sb * weights.sb
        + row.bb * weights.hitter_bb
        + row.k * weights.hitter_k
    )
    
def pitcher_game_points(row: PitcherGameStat, weights: ScoringWeights) -> float:
    ip = row.ip_outs / 3.0
    return (
        ip * weights.ip
        + row.qs * weights.qs
        + row.hd * weights.hd
        + row.sv * weights.sv
        + row.k * weights.pitcher_k
        + row.er * weights.er
        + row.hits_allowed * weights.hits_allowed
        + row.bb_allowed * weights.pitcher_bb_allowed
        + row.blown_sv * weights.blown_sv
    )
