"""TODO: implement module."""
from fantasy_analytics_engine.domain.models import LeagueSize, Position

def roster_cutoff(league_size: LeagueSize, position: Position) -> int:
    """
    Return League_Teams & Roster_Slots_at_Position for V1 assumptions.
    Example: 12-team C => 12, 12-team OF => 36.
    """