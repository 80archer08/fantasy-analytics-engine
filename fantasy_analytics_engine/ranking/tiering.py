"""TODO: implement module."""
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import PlayerVOR

def assign_tiers(sorted_rows: Sequence[PlayerVOR], dropoff_threshold: float = 1.5) -> dict[str, int]:
    """Return {player_id: tier_number} based on explainable VOR drop-offs."""