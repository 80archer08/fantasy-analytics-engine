"""TODO: implement module."""
from datetime import date
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import FantasyPointEvent, WeeklyFantasyPoints]: ...

def aggregate_weekly(events: Sequence[FantasyPointEvent]) -> list[WeeklyFantasyPoints]: ...

def rolling_average_weekly(
    weekly_rows: Sequence[WeeklyFantasyPoints],
    windows: tuple[int, ...] = (7, 14, 30),
) -> dict[int, dict[str, float]]:
    """Return {window_days: {player_id: rolling_fp}}."""