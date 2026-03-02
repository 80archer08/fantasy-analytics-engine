"""MLB ingestion interfaces.

Planned implementation target: MLB-StatsAPI package.
https://pypi.org/project/MLB-StatsAPI/
"""

from datetime import date
from collections.abc import Iterable
from fantasy_analytics_engine.domain.models import HitterGameStat, PitcherGameStat

class MLBStatsClientProtocol:
    def fetch_hitter_game_stats(self, start_date: date, end_date: date) -> Iterable[HitterGameStat]: ...
    def fetch_pitcher_game_stats(self, start_date: date, end_date: date) -> Iterable[PitcherGameStat]: ...
    
