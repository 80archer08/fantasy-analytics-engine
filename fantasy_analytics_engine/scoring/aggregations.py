"""Aggregations for fantasy point events."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import timedelta

from fantasy_analytics_engine.domain.models import FantasyPointEvent, WeeklyFantasyPoints


def _week_start(d):
    return d - timedelta(days=d.weekday())


def aggregate_weekly(events: Sequence[FantasyPointEvent]) -> list[WeeklyFantasyPoints]:
    """Aggregate game fantasy points into Monday-Sunday weekly buckets."""
    buckets: dict[tuple[str, object], float] = defaultdict(float)
    for event in events:
        ws = _week_start(event.game_date)
        buckets[(event.player_id, ws)] += event.fantasy_points

    result: list[WeeklyFantasyPoints] = []
    for (player_id, ws), weekly_fp in sorted(buckets.items(), key=lambda x: (x[0][0], x[0][1])):
        result.append(
            WeeklyFantasyPoints(
                player_id=player_id,
                week_start=ws,
                week_end=ws + timedelta(days=6),
                weekly_fp=weekly_fp,
            )
        )
    return result


def rolling_average_weekly(
    weekly_rows: Sequence[WeeklyFantasyPoints],
    windows: tuple[int, ...] = (7, 14, 30),
) -> dict[int, dict[str, float]]:
    """Return rolling averages by requested day windows."""
    by_player: dict[str, list[WeeklyFantasyPoints]] = defaultdict(list)
    for row in weekly_rows:
        by_player[row.player_id].append(row)

    output: dict[int, dict[str, float]] = {window: {} for window in windows}
    for player_id, rows in by_player.items():
        rows = sorted(rows, key=lambda r: r.week_start)
        for window in windows:
            lookback_weeks = max(1, window // 7)
            sample = rows[-lookback_weeks:]
            if sample:
                output[window][player_id] = sum(r.weekly_fp for r in sample) / len(sample)
    return output
