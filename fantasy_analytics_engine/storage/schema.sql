-- Fantasy Analytics Engine V1 schema (PostgreSQL)
-- Design goals:
-- 1) Preserve immutable raw game-level stats as source of truth.
-- 2) Separate raw, derived, and fantasy valuation layers.
-- 3) Support weekly reporting, rolling windows, and VOR ranking workflows.

BEGIN;

-- -----------------------------------------------------------------------------
-- Layer 1: Reference data
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS teams (
    team_id BIGSERIAL PRIMARY KEY,
    mlb_team_id INT UNIQUE,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL UNIQUE,
    league TEXT,
    division TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seasons (
    season INT PRIMARY KEY,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    bats CHAR(1) CHECK (bats IN ('L', 'R', 'S') OR bats IS NULL),
    throws CHAR(1) CHECK (throws IN ('L', 'R') OR throws IS NULL),
    primary_position TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    current_team_id BIGINT REFERENCES teams(team_id),
    debut_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS player_position_eligibility (
    player_id BIGINT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    position TEXT NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'internal',
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, position, source_system)
);

-- -----------------------------------------------------------------------------
-- Layer 2: Raw game/event data (immutable source of truth)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS games (
    game_id BIGINT PRIMARY KEY,
    season INT NOT NULL REFERENCES seasons(season),
    game_date DATE NOT NULL,
    game_datetime_utc TIMESTAMPTZ,
    home_team_id BIGINT NOT NULL REFERENCES teams(team_id),
    away_team_id BIGINT NOT NULL REFERENCES teams(team_id),
    home_score INT,
    away_score INT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (home_team_id <> away_team_id)
);

CREATE TABLE IF NOT EXISTS player_game_batting_stats (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    team_id BIGINT REFERENCES teams(team_id),
    lineup_position SMALLINT,
    plate_appearances SMALLINT,
    at_bats SMALLINT,
    singles SMALLINT NOT NULL DEFAULT 0,
    doubles SMALLINT NOT NULL DEFAULT 0,
    triples SMALLINT NOT NULL DEFAULT 0,
    home_runs SMALLINT NOT NULL DEFAULT 0,
    runs SMALLINT NOT NULL DEFAULT 0,
    rbi SMALLINT NOT NULL DEFAULT 0,
    walks SMALLINT NOT NULL DEFAULT 0,
    strikeouts SMALLINT NOT NULL DEFAULT 0,
    stolen_bases SMALLINT NOT NULL DEFAULT 0,
    hit_by_pitch SMALLINT NOT NULL DEFAULT 0,
    sacrifice_flies SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

CREATE TABLE IF NOT EXISTS player_game_pitching_stats (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    team_id BIGINT REFERENCES teams(team_id),
    role TEXT NOT NULL CHECK (role IN ('SP', 'RP', 'UNKNOWN')),
    innings_pitched_outs SMALLINT NOT NULL DEFAULT 0,
    strikeouts SMALLINT NOT NULL DEFAULT 0,
    walks_allowed SMALLINT NOT NULL DEFAULT 0,
    hits_allowed SMALLINT NOT NULL DEFAULT 0,
    earned_runs SMALLINT NOT NULL DEFAULT 0,
    quality_start BOOLEAN NOT NULL DEFAULT FALSE,
    saves SMALLINT NOT NULL DEFAULT 0,
    holds SMALLINT NOT NULL DEFAULT 0,
    blown_saves SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

-- -----------------------------------------------------------------------------
-- Layer 3: Derived / aggregated stat layer
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS player_weekly_stats (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    games_played SMALLINT NOT NULL DEFAULT 0,
    pa INT,
    ip_outs INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, week_start),
    CHECK (week_end >= week_start)
);

CREATE TABLE IF NOT EXISTS player_rolling_stats (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    as_of_date DATE NOT NULL,
    window_days SMALLINT NOT NULL CHECK (window_days IN (7, 14, 30)),
    -- hitter metrics
    obp NUMERIC(8, 5),
    slg NUMERIC(8, 5),
    babip NUMERIC(8, 5),
    k_rate NUMERIC(8, 5),
    bb_rate NUMERIC(8, 5),
    hitter_k_bb_ratio NUMERIC(10, 5),
    lineup_stability NUMERIC(10, 5),
    -- pitcher metrics
    pitcher_k_bb_ratio NUMERIC(10, 5),
    ip_per_appearance NUMERIC(10, 5),
    rolling_er_rate NUMERIC(10, 5),
    role_stability NUMERIC(10, 5),
    save_hold_opportunity_rate NUMERIC(10, 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, as_of_date, window_days)
);

-- -----------------------------------------------------------------------------
-- Layer 4: Fantasy scoring and valuation layer
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS player_game_fantasy_points (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    game_date DATE NOT NULL,
    fantasy_points NUMERIC(10, 3) NOT NULL,
    scorer_version TEXT NOT NULL DEFAULT 'v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, game_id)
);

CREATE TABLE IF NOT EXISTS player_weekly_fantasy_points (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    weekly_fantasy_points NUMERIC(10, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, week_start),
    CHECK (week_end >= week_start)
);

CREATE TABLE IF NOT EXISTS replacement_levels (
    week_start DATE NOT NULL,
    league_size SMALLINT NOT NULL CHECK (league_size IN (4, 12)),
    position TEXT NOT NULL,
    replacement_pool_size SMALLINT NOT NULL DEFAULT 3,
    replacement_weekly_fp_raw NUMERIC(10, 3) NOT NULL,
    replacement_weekly_fp_smoothed NUMERIC(10, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (week_start, league_size, position)
);

CREATE TABLE IF NOT EXISTS player_value_over_replacement (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    week_start DATE NOT NULL,
    league_size SMALLINT NOT NULL CHECK (league_size IN (4, 12)),
    best_eligible_position TEXT NOT NULL,
    expected_weekly_fp NUMERIC(10, 3) NOT NULL,
    replacement_weekly_fp NUMERIC(10, 3) NOT NULL,
    vor NUMERIC(10, 3) NOT NULL,
    volatility_8w NUMERIC(10, 3),
    risk_label TEXT CHECK (risk_label IN ('LOW', 'MEDIUM', 'HIGH')),
    role_stability_factor NUMERIC(6, 3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, week_start, league_size)
);

-- Future-facing projection layer for V2
CREATE TABLE IF NOT EXISTS player_weekly_projections (
    player_id BIGINT NOT NULL REFERENCES players(player_id),
    week_start DATE NOT NULL,
    projection_source TEXT NOT NULL,
    projected_weekly_fp NUMERIC(10, 3) NOT NULL,
    projection_low NUMERIC(10, 3),
    projection_high NUMERIC(10, 3),
    model_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, week_start, projection_source)
);

-- -----------------------------------------------------------------------------
-- Indexes tuned for ingestion, date-range filtering, and weekly ranking queries
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);

CREATE INDEX IF NOT EXISTS idx_batting_game_id ON player_game_batting_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_batting_player_id ON player_game_batting_stats(player_id);

CREATE INDEX IF NOT EXISTS idx_pitching_game_id ON player_game_pitching_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_pitching_player_id ON player_game_pitching_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pitching_role ON player_game_pitching_stats(role);

CREATE INDEX IF NOT EXISTS idx_game_fp_game_date ON player_game_fantasy_points(game_date);
CREATE INDEX IF NOT EXISTS idx_game_fp_player_id ON player_game_fantasy_points(player_id);

CREATE INDEX IF NOT EXISTS idx_weekly_fp_week_start ON player_weekly_fantasy_points(week_start);
CREATE INDEX IF NOT EXISTS idx_weekly_fp_player_id ON player_weekly_fantasy_points(player_id);

CREATE INDEX IF NOT EXISTS idx_replacement_lookup
    ON replacement_levels(week_start, league_size, position);

CREATE INDEX IF NOT EXISTS idx_vor_lookup
    ON player_value_over_replacement(week_start, league_size, vor DESC);

CREATE INDEX IF NOT EXISTS idx_rolling_stats_lookup
    ON player_rolling_stats(as_of_date, window_days, player_id);

COMMIT;
