"""Value-over-replacement (VOR) calculations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from math import sqrt

from fantasy_analytics_engine.config import ReplacementConfig
from fantasy_analytics_engine.domain.models import (
    LeagueSize,
    PlayerVOR,
    ReplacementLevelPoint,
    RiskLabel,
    WeeklyFantasyPoints,
)


class VOREngine:
    """Computes expected weekly points, volatility, and VOR."""

    def __init__(self, cfg: ReplacementConfig) -> None:
        self.cfg = cfg

    def expected_weekly_fp(self, weekly_points: Sequence[WeeklyFantasyPoints]) -> dict[str, float]:
        by_player: dict[str, list[float]] = defaultdict(list)
        for row in weekly_points:
            by_player[row.player_id].append(row.weekly_fp)
        return {pid: (sum(vals) / len(vals) if vals else 0.0) for pid, vals in by_player.items()}

    def volatility_8w(self, weekly_points: Sequence[WeeklyFantasyPoints]) -> dict[str, float]:
        by_player: dict[str, list[float]] = defaultdict(list)
        for row in sorted(weekly_points, key=lambda r: (r.player_id, r.week_start)):
            by_player[row.player_id].append(row.weekly_fp)

        out: dict[str, float] = {}
        for pid, vals in by_player.items():
            sample = vals[-self.cfg.volatility_window_weeks :]
            if len(sample) < 2:
                out[pid] = 0.0
                continue
            mean = sum(sample) / len(sample)
            var = sum((x - mean) ** 2 for x in sample) / len(sample)
            out[pid] = sqrt(var)
        return out

    def compute_player_vor(
        self,
        league_size: LeagueSize,
        weekly_points: Sequence[WeeklyFantasyPoints],
        rl_points: Sequence[ReplacementLevelPoint],
        player_positions: dict[str, tuple[str, ...]],
        role_stability_factor: dict[str, float] | None = None,
    ) -> list[PlayerVOR]:
        expected = self.expected_weekly_fp(weekly_points)
        vol = self.volatility_8w(weekly_points)

        rl_by_position: dict[str, float] = {}
        for row in rl_points:
            rl_by_position[row.position] = row.rl_weekly_fp_smoothed

        role_stability_factor = role_stability_factor or {}

        rows: list[PlayerVOR] = []
        for player_id, exp in expected.items():
            eligible = player_positions.get(player_id, tuple())
            if not eligible:
                continue

            best_pos = eligible[0]
            best_vor = float("-inf")
            best_rl = 0.0
            for pos in eligible:
                rl = rl_by_position.get(pos, 0.0)
                vor = exp - rl
                if vor > best_vor:
                    best_vor = vor
                    best_pos = pos
                    best_rl = rl

            best_vor *= role_stability_factor.get(player_id, 1.0)
            risk_label: RiskLabel = "LOW" if vol.get(player_id, 0.0) < 3 else "MEDIUM" if vol.get(player_id, 0.0) < 6 else "HIGH"
            rows.append(
                PlayerVOR(
                    player_id=player_id,
                    league_size=league_size,
                    best_eligible_position=best_pos,
                    expected_weekly_fp=exp,
                    replacement_weekly_fp=best_rl,
                    vor=best_vor,
                    volatility_8w=vol.get(player_id, 0.0),
                    risk_label=risk_label,
                )
            )

        return sorted(rows, key=lambda r: (-r.vor, r.volatility_8w))
