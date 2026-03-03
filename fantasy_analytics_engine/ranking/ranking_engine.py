"""TODO: implement module."""
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import PlayerVOR

def rank_players(rows: Sequence[PlayerVOR]) -> list[PlayerVOR]:
    """Sort by VOR desc, tie-break by lower volatility."""
    