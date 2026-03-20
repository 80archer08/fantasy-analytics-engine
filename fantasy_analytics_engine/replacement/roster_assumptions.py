"""League roster assumptions used for replacement-level calculations."""

from __future__ import annotations

from fantasy_analytics_engine.domain.models import LeagueSize, Position


_ROSTER_SLOTS: dict[int, dict[str, int]] = {
    12: {"C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3, "UTIL": 1, "SP": 7, "RP": 0, "P": 7},
    4: {"C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3, "UTIL": 2, "SP": 7, "RP": 0, "P": 7},
}


def roster_cutoff(league_size: LeagueSize, position: Position) -> int:
    """Return roster cutoff index = league teams * slots at position."""
    return int(league_size) * _ROSTER_SLOTS[int(league_size)][position]
