"""Backfill the full 2024 MLB season into PostgreSQL.

Pipeline:
1) games
2) players
3) batting stats
4) pitching stats
5) fantasy points

This script intentionally writes to per-game tables to preserve game identity
for double-headers.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import psycopg2
import statsapi

START_DATE = "2024-03-20"
END_DATE = "2024-09-30"
BATCH_COMMIT_DAYS = 5
API_SLEEP_SECONDS = 0.5
SEASON = 2024


@dataclass(frozen=True)
class DBConfig:
    dbname: str = os.getenv("FANTASY_DB_NAME", "fantasy_baseball")
    user: str = os.getenv("FANTASY_DB_USER", "fantasy_user")
    password: str = os.getenv("FANTASY_DB_PASSWORD", "yourpassword")
    host: str = os.getenv("FANTASY_DB_HOST", "localhost")
    port: str = os.getenv("FANTASY_DB_PORT", "5432")


def daterange(start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    for n in range((end - start).days + 1):
        yield (start + timedelta(days=n)).strftime("%Y-%m-%d")


def compute_batting_fp(batting: dict[str, Any]) -> Decimal:
    value = (
        batting.get("totalBases", 0)
        + batting.get("rbi", 0)
        + batting.get("runs", 0)
        + batting.get("stolenBases", 0)
        + batting.get("baseOnBalls", 0)
        - batting.get("strikeOuts", 0)
    )
    return Decimal(value)


def _innings_to_outs(innings_pitched: str | int | float | None) -> int:
    """Convert MLB innings representation to outs.

    MLB uses tenths to represent outs: 5.2 means 5 innings + 2 outs, not 5.2 innings.
    """

    if innings_pitched in (None, "", 0, 0.0):
        return 0

    text = str(innings_pitched)
    if "." not in text:
        return int(text) * 3

    whole, frac = text.split(".", maxsplit=1)
    whole_outs = int(whole) * 3
    frac_outs = int(frac)
    if frac_outs not in (0, 1, 2):
        raise ValueError(f"Unexpected innings format: {innings_pitched}")
    return whole_outs + frac_outs


def compute_pitching_fp(pitching: dict[str, Any]) -> Decimal:
    outs = _innings_to_outs(pitching.get("inningsPitched", 0))
    innings_points = Decimal(outs)
    value = (
        innings_points
        + Decimal(pitching.get("strikeOuts", 0))
        - Decimal(pitching.get("earnedRuns", 0)) * 2
        - Decimal(pitching.get("hits", 0))
        - Decimal(pitching.get("baseOnBalls", 0))
        + Decimal(pitching.get("saves", 0)) * 5
        + Decimal(pitching.get("holds", 0)) * 2
        + (Decimal(5) if pitching.get("qualityStart", False) else Decimal(0))
    )
    return value


def insert_game(cursor: psycopg2.extensions.cursor, game: dict[str, Any]) -> None:
    cursor.execute(
        """
        INSERT INTO games (game_id, season, game_date)
        VALUES (%s, %s, %s)
        ON CONFLICT (game_id) DO NOTHING;
        """,
        (
            game["game_id"],
            SEASON,
            game["game_date"],
        ),
    )


def _position_payload(player_info: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    raw = player_info.get("primaryPosition", {}).get("abbreviation")
    if raw in {"SP", "RP", "P", "C", "1B", "2B", "3B", "SS", "OF", "UTIL"}:
        primary = raw
    elif raw in {"LF", "CF", "RF"}:
        primary = "OF"
    else:
        primary = "UTIL"

    if primary in {"SP", "RP", "P"}:
        eligible = ("P", primary) if primary != "P" else ("P",)
    elif primary == "UTIL":
        eligible = ("UTIL",)
    else:
        eligible = (primary, "UTIL")
    return primary, eligible


def insert_player(
    cursor: psycopg2.extensions.cursor,
    player_id: int,
    player_info: dict[str, Any],
) -> None:
    primary, eligible = _position_payload(player_info)
    team = player_info.get("currentTeam", {}).get("abbreviation", "UNK")
    first = player_info.get("firstName", "")
    last = player_info.get("lastName", "")
    full_name = player_info.get("fullName") or f"{first} {last}".strip() or str(player_id)

    cursor.execute(
        """
        INSERT INTO players (player_id, name, mlb_team, primary_position, eligible_positions)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (player_id) DO UPDATE
        SET name = EXCLUDED.name,
            mlb_team = EXCLUDED.mlb_team,
            primary_position = EXCLUDED.primary_position,
            eligible_positions = EXCLUDED.eligible_positions,
            updated_at = NOW();
        """,
        (
            str(player_id),
            full_name,
            team,
            primary,
            list(eligible),
        ),
    )


def upsert_batting(
    cursor: psycopg2.extensions.cursor,
    player_id: str,
    game_id: int,
    batting: dict[str, Any],
) -> Decimal:
    cursor.execute(
        """
        INSERT INTO player_game_batting_stats (
            player_id, game_id, at_bats, hits,
            home_runs, runs, rbi, walks, strikeouts,
            stolen_bases, total_bases
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id, game_id) DO UPDATE
        SET at_bats = EXCLUDED.at_bats,
            hits = EXCLUDED.hits,
            home_runs = EXCLUDED.home_runs,
            runs = EXCLUDED.runs,
            rbi = EXCLUDED.rbi,
            walks = EXCLUDED.walks,
            strikeouts = EXCLUDED.strikeouts,
            stolen_bases = EXCLUDED.stolen_bases,
            total_bases = EXCLUDED.total_bases;
        """,
        (
            player_id,
            game_id,
            batting.get("atBats", 0),
            batting.get("hits", 0),
            batting.get("homeRuns", 0),
            batting.get("runs", 0),
            batting.get("rbi", 0),
            batting.get("baseOnBalls", 0),
            batting.get("strikeOuts", 0),
            batting.get("stolenBases", 0),
            batting.get("totalBases", 0),
        ),
    )
    return compute_batting_fp(batting)


def upsert_pitching(
    cursor: psycopg2.extensions.cursor,
    player_id: str,
    game_id: int,
    pitching: dict[str, Any],
) -> Decimal:
    cursor.execute(
        """
        INSERT INTO player_game_pitching_stats (
            player_id, game_id, innings_pitched,
            strikeouts, walks, hits_allowed, earned_runs,
            saves, holds
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id, game_id) DO UPDATE
        SET innings_pitched = EXCLUDED.innings_pitched,
            strikeouts = EXCLUDED.strikeouts,
            walks = EXCLUDED.walks,
            hits_allowed = EXCLUDED.hits_allowed,
            earned_runs = EXCLUDED.earned_runs,
            saves = EXCLUDED.saves,
            holds = EXCLUDED.holds;
        """,
        (
            player_id,
            game_id,
            str(pitching.get("inningsPitched", 0)),
            pitching.get("strikeOuts", 0),
            pitching.get("baseOnBalls", 0),
            pitching.get("hits", 0),
            pitching.get("earnedRuns", 0),
            pitching.get("saves", 0),
            pitching.get("holds", 0),
        ),
    )
    return compute_pitching_fp(pitching)


def upsert_fantasy_points(
    cursor: psycopg2.extensions.cursor,
    player_id: str,
    game_id: int,
    fantasy_points: Decimal,
) -> None:
    cursor.execute(
        """
        INSERT INTO player_game_fantasy_points (
            player_id, game_id, fantasy_points
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (player_id, game_id) DO UPDATE
        SET fantasy_points = EXCLUDED.fantasy_points;
        """,
        (player_id, game_id, fantasy_points),
    )


def run_backfill(start_date: str = START_DATE, end_date: str = END_DATE) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = DBConfig()

    conn = psycopg2.connect(
        dbname=config.dbname,
        user=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
    )

    day_count = 0
    try:
        with conn:
            with conn.cursor() as cursor:
                for date_str in daterange(start_date, end_date):
                    day_count += 1
                    logging.info("Processing %s", date_str)
                    schedule = statsapi.schedule(start_date=date_str, end_date=date_str)

                    for game in schedule:
                        game_id = game["game_id"]
                        insert_game(cursor, game)

                        try:
                            boxscore = statsapi.boxscore_data(game_id)
                        except Exception:
                            logging.exception("Boxscore fetch failed for game_id=%s", game_id)
                            continue

                        players_info = boxscore.get("playerInfo", {})
                        players_stats = boxscore.get("players", {})

                        for pid, pdata in players_stats.items():
                            player_id = int(pid.replace("ID", ""))
                            player_info = players_info.get(pid, {})
                            insert_player(cursor, player_id, player_info)

                            stats = pdata.get("stats", {})
                            batting = stats.get("batting", {})
                            pitching = stats.get("pitching", {})

                            fp_total = Decimal(0)
                            if batting:
                                fp_total += upsert_batting(cursor, str(player_id), game_id, batting)

                            if pitching:
                                fp_total += upsert_pitching(cursor, str(player_id), game_id, pitching)

                            if batting or pitching:
                                upsert_fantasy_points(cursor, str(player_id), game_id, fp_total)
                                logging.info("Inserted player_id=%s game_id=%s", player_id, game_id)

                        time.sleep(API_SLEEP_SECONDS)

                    if day_count % BATCH_COMMIT_DAYS == 0:
                        conn.commit()
                        logging.info("Committed batch ending on %s", date_str)

                conn.commit()
                logging.info("Backfill completed from %s to %s", start_date, end_date)
    finally:
        conn.close()


if __name__ == "__main__":
    run_backfill()
