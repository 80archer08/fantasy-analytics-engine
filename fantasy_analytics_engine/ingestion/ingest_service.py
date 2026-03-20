"""TODO: implement module."""
from datetime import date
from collections.abc import Iterable
from fantasy_analytics_engine.domain.models import HitterGameStat, PitcherGameStat

class IngestionService:
    def __init__(self, mlb_client: MLBStatsClientProtocol, repo: "Repository") -> None: ...
    
    def ingest_range(self, start_date: date, end_date: date) -> None:
        """Pull raw stats and insert them into persistent storage."""
