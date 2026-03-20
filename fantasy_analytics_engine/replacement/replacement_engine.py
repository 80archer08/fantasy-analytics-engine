"""Replacement-level calculation engine."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from fantasy_analytics_engine.config import ReplacementConfig
from fantasy_analytics_engine.domain.models import LeagueSize, Position, ReplacementLevelPoint, WeeklyFantasyPoints
from fantasy_analytics_engine.replacement.roster_assumptions import roster_cutoff


class ReplacementLevelEngine:
    """Computes weekly replacement levels by position and league size."""

    def __init__(self, cfg: ReplacementConfig) -> None:
        self.cfg = cfg

    def compute_weekly_replacement(
        self,
        weekly_points: Sequence[WeeklyFantasyPoints],
        player_positions: dict[str, tuple[Position, ...]],
        league_size: LeagueSize,
    ) -> list[ReplacementLevelPoint]:
        week_to_pos_values: dict[tuple[object, Position], list[float]] = defaultdict(list)
        for row in weekly_points:
            for pos in player_positions.get(row.player_id, ()):  # multi-position eligibility
                week_to_pos_values[(row.week_start, pos)].append(row.weekly_fp)

        raw_rows: list[ReplacementLevelPoint] = []
        for (week_start, position), values in sorted(week_to_pos_values.items(), key=lambda x: (x[0][0], x[0][1])):
            values = sorted(values, reverse=True)
            cutoff = roster_cutoff(league_size=league_size, position=position)
            start_idx = cutoff
            end_idx = cutoff + self.cfg.replacement_pool_size
            pool = values[start_idx:end_idx]
            rl_raw = sum(pool) / len(pool) if pool else 0.0
            raw_rows.append(
                ReplacementLevelPoint(
                    position=position,
                    league_size=league_size,
                    week_start=week_start,
                    rl_weekly_fp_raw=rl_raw,
                    rl_weekly_fp_smoothed=rl_raw,
                )
            )

        # smooth by position over trailing N weeks
        by_position: dict[Position, list[ReplacementLevelPoint]] = defaultdict(list)
        for row in raw_rows:
            by_position[row.position].append(row)

        smoothed: list[ReplacementLevelPoint] = []
        for pos, rows in by_position.items():
            rows = sorted(rows, key=lambda r: r.week_start)
            for i, row in enumerate(rows):
                start = max(0, i + 1 - self.cfg.smoothing_window_weeks)
                sample = rows[start : i + 1]
                smooth = sum(r.rl_weekly_fp_raw for r in sample) / len(sample)
                smoothed.append(
                    ReplacementLevelPoint(
                        position=pos,
                        league_size=row.league_size,
                        week_start=row.week_start,
                        rl_weekly_fp_raw=row.rl_weekly_fp_raw,
                        rl_weekly_fp_smoothed=smooth,
                    )
                )

        return sorted(smoothed, key=lambda r: (r.week_start, r.position))
