# V1 Vertical Slice: Module Layout & Function Signatures

This is the **first production slice** for the Fantasy Analytics Engine: ingest raw MLB data, compute ESPN H2H points, compute replacement level, compute VOR, and export rankings.

## 1) Suggested package layout

```text
fantasy_analytics_engine/
  __init__.py
  config.py
  cli.py

  domain/
    __init__.py
    models.py

  ingestion/
    __init__.py
    mlb_client.py
    ingest_service.py

  storage/
    __init__.py
    schema.sql
    repository.py

  scoring/
    __init__.py
    rules.py
    engine.py
    aggregations.py

  replacement/
    __init__.py
    roster_assumptions.py
    replacement_engine.py
    vor_engine.py

  ranking/
    __init__.py
    ranking_engine.py
    tiering.py

  reporting/
    __init__.py
    csv_exporter.py
    markdown_report.py

  pipelines/
    __init__.py
    v1_vertical_slice.py

tests/
  test_scoring_engine.py
  test_replacement_engine.py
  test_vor_engine.py
```

---

## 2) Core domain models (`domain/models.py`)

```python
from dataclasses import dataclass
from datetime import date
from typing import Literal

LeagueSize = Literal[4, 12]
Position = Literal["C", "1B", "2B", "3B", "SS", "OF", "UTIL", "SP", "RP", "P"]
Role = Literal["SP", "RP", "UNKNOWN"]
RiskLabel = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass(frozen=True)
class Player:
    player_id: str
    name: str
    mlb_team: str
    primary_position: Position
    eligible_positions: tuple[Position, ...]


@dataclass(frozen=True)
class HitterGameStat:
    player_id: str
    game_date: date
    team: str
    lineup_position: int | None
    pa: int
    singles: int
    doubles: int
    triples: int
    hr: int
    bb: int
    k: int
    runs: int
    rbi: int
    sb: int


@dataclass(frozen=True)
class PitcherGameStat:
    player_id: str
    game_date: date
    team: str
    role: Role
    ip_outs: int  # store IP as outs to avoid float precision issues
    hits_allowed: int
    er: int
    bb_allowed: int
    k: int
    qs: int
    sv: int
    hd: int
    blown_sv: int


@dataclass(frozen=True)
class FantasyPointEvent:
    player_id: str
    game_date: date
    fantasy_points: float


@dataclass(frozen=True)
class WeeklyFantasyPoints:
    player_id: str
    week_start: date
    week_end: date
    weekly_fp: float


@dataclass(frozen=True)
class ReplacementLevelPoint:
    position: Position
    league_size: LeagueSize
    week_start: date
    rl_weekly_fp_raw: float
    rl_weekly_fp_smoothed: float


@dataclass(frozen=True)
class PlayerVOR:
    player_id: str
    league_size: LeagueSize
    best_eligible_position: Position
    expected_weekly_fp: float
    replacement_weekly_fp: float
    vor: float
    volatility_8w: float
    risk_label: RiskLabel
```

---

## 3) Config (`config.py`)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
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
    replacement_pool_size: int = 3  # N
    smoothing_window_weeks: int = 4
    volatility_window_weeks: int = 8


@dataclass(frozen=True)
class AppConfig:
    scoring: ScoringWeights = ScoringWeights()
    replacement: ReplacementConfig = ReplacementConfig()
```

---

## 4) Ingestion interfaces (`ingestion/mlb_client.py`, `ingestion/ingest_service.py`)

```python
from datetime import date
from collections.abc import Iterable
from fantasy_analytics_engine.domain.models import HitterGameStat, PitcherGameStat


class MLBStatsClientProtocol:
    def fetch_hitter_game_stats(self, start_date: date, end_date: date) -> Iterable[HitterGameStat]: ...
    def fetch_pitcher_game_stats(self, start_date: date, end_date: date) -> Iterable[PitcherGameStat]: ...


class IngestionService:
    def __init__(self, mlb_client: MLBStatsClientProtocol, repo: "Repository") -> None: ...

    def ingest_range(self, start_date: date, end_date: date) -> None:
        """Pull raw stats and upsert them into persistent storage."""
```

---

## 5) Storage interfaces (`storage/repository.py`)

```python
from datetime import date
from collections.abc import Iterable, Sequence
from fantasy_analytics_engine.domain.models import (
    HitterGameStat,
    PitcherGameStat,
    FantasyPointEvent,
    WeeklyFantasyPoints,
    ReplacementLevelPoint,
    PlayerVOR,
)


class Repository:
    # raw data
    def upsert_hitter_game_stats(self, rows: Iterable[HitterGameStat]) -> None: ...
    def upsert_pitcher_game_stats(self, rows: Iterable[PitcherGameStat]) -> None: ...
    def get_hitter_game_stats(self, start_date: date, end_date: date) -> Sequence[HitterGameStat]: ...
    def get_pitcher_game_stats(self, start_date: date, end_date: date) -> Sequence[PitcherGameStat]: ...

    # derived data
    def upsert_fantasy_point_events(self, rows: Iterable[FantasyPointEvent]) -> None: ...
    def get_fantasy_point_events(self, start_date: date, end_date: date) -> Sequence[FantasyPointEvent]: ...

    def upsert_weekly_fantasy_points(self, rows: Iterable[WeeklyFantasyPoints]) -> None: ...
    def get_weekly_fantasy_points(self, start_date: date, end_date: date) -> Sequence[WeeklyFantasyPoints]: ...

    def upsert_replacement_levels(self, rows: Iterable[ReplacementLevelPoint]) -> None: ...
    def get_replacement_levels(self, start_date: date, end_date: date) -> Sequence[ReplacementLevelPoint]: ...

    def upsert_player_vor(self, rows: Iterable[PlayerVOR]) -> None: ...
    def get_latest_player_vor(self, as_of: date) -> Sequence[PlayerVOR]: ...
```

---

## 6) Scoring engine (`scoring/rules.py`, `scoring/engine.py`, `scoring/aggregations.py`)

```python
# scoring/rules.py
from fantasy_analytics_engine.domain.models import HitterGameStat, PitcherGameStat
from fantasy_analytics_engine.config import ScoringWeights


def hitter_game_points(row: HitterGameStat, weights: ScoringWeights) -> float:
    tb = row.singles + (2 * row.doubles) + (3 * row.triples) + (4 * row.hr)
    return (
        tb * weights.tb
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
```

```python
# scoring/engine.py
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import (
    HitterGameStat,
    PitcherGameStat,
    FantasyPointEvent,
)
from fantasy_analytics_engine.config import ScoringWeights


class FantasyScoringEngine:
    def __init__(self, weights: ScoringWeights) -> None: ...

    def score_hitter_games(self, rows: Sequence[HitterGameStat]) -> list[FantasyPointEvent]: ...
    def score_pitcher_games(self, rows: Sequence[PitcherGameStat]) -> list[FantasyPointEvent]: ...
    def score_all_games(
        self,
        hitters: Sequence[HitterGameStat],
        pitchers: Sequence[PitcherGameStat],
    ) -> list[FantasyPointEvent]: ...
```

```python
# scoring/aggregations.py
from datetime import date
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import FantasyPointEvent, WeeklyFantasyPoints


def aggregate_weekly(events: Sequence[FantasyPointEvent]) -> list[WeeklyFantasyPoints]: ...

def rolling_average_weekly(
    weekly_rows: Sequence[WeeklyFantasyPoints],
    windows: tuple[int, ...] = (7, 14, 30),
) -> dict[int, dict[str, float]]:
    """Return {window_days: {player_id: rolling_fp}}."""
```

---

## 7) Replacement + VOR (`replacement/roster_assumptions.py`, `replacement/replacement_engine.py`, `replacement/vor_engine.py`)

```python
# replacement/roster_assumptions.py
from fantasy_analytics_engine.domain.models import LeagueSize, Position


def roster_cutoff(league_size: LeagueSize, position: Position) -> int:
    """
    Return League_Teams * Roster_Slots_at_Position for V1 assumptions.
    Example: 12-team C => 12, 12-team OF => 36.
    """
```

```python
# replacement/replacement_engine.py
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import (
    LeagueSize,
    Position,
    WeeklyFantasyPoints,
    ReplacementLevelPoint,
)
from fantasy_analytics_engine.config import ReplacementConfig


class ReplacementLevelEngine:
    def __init__(self, cfg: ReplacementConfig) -> None: ...

    def compute_weekly_replacement(
        self,
        weekly_points: Sequence[WeeklyFantasyPoints],
        player_positions: dict[str, tuple[Position, ...]],
        league_size: LeagueSize,
    ) -> list[ReplacementLevelPoint]:
        """
        For each week and position:
        1) sort players by weekly_fp desc
        2) select ranks [cutoff + 1, cutoff + N]
        3) average replacement pool => raw RL
        4) apply rolling mean smoothing window (4 weeks by default)
        """
```

```python
# replacement/vor_engine.py
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import (
    LeagueSize,
    WeeklyFantasyPoints,
    ReplacementLevelPoint,
    PlayerVOR,
)
from fantasy_analytics_engine.config import ReplacementConfig


class VOREngine:
    def __init__(self, cfg: ReplacementConfig) -> None: ...

    def expected_weekly_fp(self, weekly_points: Sequence[WeeklyFantasyPoints]) -> dict[str, float]:
        """Use rolling/weighted recent weekly points to estimate expected weekly FP."""

    def volatility_8w(self, weekly_points: Sequence[WeeklyFantasyPoints]) -> dict[str, float]:
        """Stddev of last 8 weeks weekly FP."""

    def compute_player_vor(
        self,
        league_size: LeagueSize,
        weekly_points: Sequence[WeeklyFantasyPoints],
        rl_points: Sequence[ReplacementLevelPoint],
        player_positions: dict[str, tuple[str, ...]],
        role_stability_factor: dict[str, float] | None = None,
    ) -> list[PlayerVOR]:
        """
        Compute VOR by position eligibility and choose max VOR position.
        Optionally apply pitcher role stability multiplier.
        """
```

---

## 8) Ranking + tiers (`ranking/ranking_engine.py`, `ranking/tiering.py`)

```python
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import PlayerVOR


def rank_players(rows: Sequence[PlayerVOR]) -> list[PlayerVOR]:
    """Sort by VOR desc, tie-break by lower volatility."""


def assign_tiers(sorted_rows: Sequence[PlayerVOR], dropoff_threshold: float = 1.5) -> dict[str, int]:
    """Return {player_id: tier_number} based on explainable VOR drop-offs."""
```

---

## 9) Report outputs (`reporting/csv_exporter.py`, `reporting/markdown_report.py`)

```python
from pathlib import Path
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import PlayerVOR


def write_draft_board_csv(rows: Sequence[PlayerVOR], out_path: Path) -> None: ...

def write_weekly_report_markdown(rows: Sequence[PlayerVOR], out_path: Path) -> None: ...
```

---

## 10) Orchestration (`pipelines/v1_vertical_slice.py`, `cli.py`)

```python
from datetime import date


def run_v1_vertical_slice(
    start_date: date,
    end_date: date,
    league_sizes: tuple[int, ...] = (4, 12),
) -> None:
    """
    1) ingest raw stats
    2) compute and persist game fantasy points
    3) compute and persist weekly fantasy points
    4) compute and persist replacement levels
    5) compute and persist VOR
    6) rank + tier
    7) emit CSV + Markdown + CLI summary
    """
```

```python
# cli.py
# example commands
#   fae ingest --start 2023-03-30 --end 2023-10-01
#   fae score --start 2023-03-30 --end 2023-10-01
#   fae replacement --start 2023-03-30 --end 2023-10-01 --league-size 12
#   fae rank --as-of 2026-03-14 --league-size 4 --out ./output/
```

---

## 11) First implementation order (1-week sprint)

1. `domain/models.py`, `config.py`  
2. `scoring/rules.py`, `scoring/engine.py`, `tests/test_scoring_engine.py`  
3. `scoring/aggregations.py`  
4. `replacement/roster_assumptions.py`, `replacement/replacement_engine.py`, `tests/test_replacement_engine.py`  
5. `replacement/vor_engine.py`, `tests/test_vor_engine.py`  
6. `ranking/*`, `reporting/*`  
7. `pipelines/v1_vertical_slice.py`, `cli.py`

This order ensures you produce useful outputs early while keeping the architecture aligned with the project requirements.
