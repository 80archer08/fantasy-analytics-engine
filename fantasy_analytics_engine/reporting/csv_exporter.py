"""TODO: implement module."""
from pathlib import Path
from collections.abc import Sequence
from fantasy_analytics_engine.domain.models import PlayerVOR

def write_draft_board_csv(rows: Sequence[PlayerVOR], out_path: Path) -> None: ...