-- Core relational schema for fantasy analytics engine v1.
-- Target dialect: PostgreSQL.

BEGIN;

CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mlb_team VARCHAR(3) NOT NULL,
    primary_position TEXT NOT NULL CHECK (primary_position IN ('C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL', 'SP', 'RP', 'P')),
    eligible_positions TEXT[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (array_length(eligible_positions, 1) >= 1)
);

CREATE TABLE IF NOT EXISTS hitter_game_stats (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    game_date DATE NOT NULL,
    team VARCHAR(3) NOT NULL,
    lineup_position SMALLINT,
    pa INTEGER NOT NULL DEFAULT 0 CHECK (pa >= 0),
    singles INTEGER NOT NULL DEFAULT 0 CHECK (singles >= 0),
    doubles INTEGER NOT NULL DEFAULT 0 CHECK (doubles >= 0),
    triples INTEGER NOT NULL DEFAULT 0 CHECK (triples >= 0),
    hr INTEGER NOT NULL DEFAULT 0 CHECK (hr >= 0),
    bb INTEGER NOT NULL DEFAULT 0 CHECK (bb >= 0),
    k INTEGER NOT NULL DEFAULT 0 CHECK (k >= 0),
    runs INTEGER NOT NULL DEFAULT 0 CHECK (runs >= 0),
    rbi INTEGER NOT NULL DEFAULT 0 CHECK (rbi >= 0),
    sb INTEGER NOT NULL DEFAULT 0 CHECK (sb >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_date)
);

CREATE INDEX IF NOT EXISTS idx_hitter_game_stats_game_date
    ON hitter_game_stats (game_date);

CREATE TABLE IF NOT EXISTS pitcher_game_stats (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    game_date DATE NOT NULL,
    team VARCHAR(3) NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('SP', 'RP', 'UNKNOWN')),
    ip_outs INTEGER NOT NULL DEFAULT 0 CHECK (ip_outs >= 0),
    hits_allowed INTEGER NOT NULL DEFAULT 0 CHECK (hits_allowed >= 0),
    er INTEGER NOT NULL DEFAULT 0 CHECK (er >= 0),
    bb_allowed INTEGER NOT NULL DEFAULT 0 CHECK (bb_allowed >= 0),
    k INTEGER NOT NULL DEFAULT 0 CHECK (k >= 0),
    qs INTEGER NOT NULL DEFAULT 0 CHECK (qs >= 0),
    sv INTEGER NOT NULL DEFAULT 0 CHECK (sv >= 0),
    hd INTEGER NOT NULL DEFAULT 0 CHECK (hd >= 0),
    blown_sv INTEGER NOT NULL DEFAULT 0 CHECK (blown_sv >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_date)
);

CREATE INDEX IF NOT EXISTS idx_pitcher_game_stats_game_date
    ON pitcher_game_stats (game_date);

CREATE TABLE IF NOT EXISTS fantasy_point_events (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    game_date DATE NOT NULL,
    fantasy_points NUMERIC(8, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_date)
);

CREATE INDEX IF NOT EXISTS idx_fantasy_point_events_game_date
    ON fantasy_point_events (game_date);

CREATE TABLE IF NOT EXISTS weekly_fantasy_points (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    weekly_fp NUMERIC(10, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, week_start),
    CHECK (week_end >= week_start)
);

CREATE INDEX IF NOT EXISTS idx_weekly_fantasy_points_window
    ON weekly_fantasy_points (week_start, week_end);

CREATE TABLE IF NOT EXISTS replacement_levels (
    position TEXT NOT NULL CHECK (position IN ('C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL', 'SP', 'RP', 'P')),
    league_size SMALLINT NOT NULL CHECK (league_size IN (4, 12)),
    week_start DATE NOT NULL,
    rl_weekly_fp_raw NUMERIC(10, 3) NOT NULL,
    rl_weekly_fp_smoothed NUMERIC(10, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (position, league_size, week_start)
);

CREATE INDEX IF NOT EXISTS idx_replacement_levels_week_start
    ON replacement_levels (week_start);

CREATE TABLE IF NOT EXISTS player_vor (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    league_size SMALLINT NOT NULL CHECK (league_size IN (4, 12)),
    as_of_date DATE NOT NULL,
    best_eligible_position TEXT NOT NULL CHECK (best_eligible_position IN ('C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL', 'SP', 'RP', 'P')),
    expected_weekly_fp NUMERIC(10, 3) NOT NULL,
    replacement_weekly_fp NUMERIC(10, 3) NOT NULL,
    vor NUMERIC(10, 3) NOT NULL,
    volatility_8w NUMERIC(10, 3) NOT NULL CHECK (volatility_8w >= 0),
    risk_label TEXT NOT NULL CHECK (risk_label IN ('LOW', 'MEDIUM', 'HIGH')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, league_size, as_of_date)
);

CREATE INDEX IF NOT EXISTS idx_player_vor_lookup
    ON player_vor (league_size, as_of_date, vor DESC);


-- Backfill-oriented per-game identity tables (2024 season pipeline).
CREATE TABLE IF NOT EXISTS games (
    game_id BIGINT PRIMARY KEY,
    season INTEGER NOT NULL,
    game_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_games_game_date
    ON games (game_date);

CREATE TABLE IF NOT EXISTS player_game_batting_stats (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    at_bats INTEGER NOT NULL DEFAULT 0,
    hits INTEGER NOT NULL DEFAULT 0,
    home_runs INTEGER NOT NULL DEFAULT 0,
    runs INTEGER NOT NULL DEFAULT 0,
    rbi INTEGER NOT NULL DEFAULT 0,
    walks INTEGER NOT NULL DEFAULT 0,
    strikeouts INTEGER NOT NULL DEFAULT 0,
    stolen_bases INTEGER NOT NULL DEFAULT 0,
    total_bases INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

CREATE TABLE IF NOT EXISTS player_game_pitching_stats (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    innings_pitched TEXT NOT NULL DEFAULT '0',
    strikeouts INTEGER NOT NULL DEFAULT 0,
    walks INTEGER NOT NULL DEFAULT 0,
    hits_allowed INTEGER NOT NULL DEFAULT 0,
    earned_runs INTEGER NOT NULL DEFAULT 0,
    saves INTEGER NOT NULL DEFAULT 0,
    holds INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

CREATE TABLE IF NOT EXISTS player_game_fantasy_points (
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    fantasy_points NUMERIC(10, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

COMMIT;
