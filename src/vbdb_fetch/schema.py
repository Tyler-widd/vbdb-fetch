"""SQLite database schema definitions for volleyball teams."""

import os
from pathlib import Path
from typing import Union

# Teams table schemas
LOVB_TEAMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS lovb_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    name_short TEXT,
    img TEXT,
    url TEXT,
    division TEXT,
    conference TEXT,
    conference_short TEXT,
    level TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_lovb_team_id ON lovb_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_lovb_conference ON lovb_teams(conference);
CREATE INDEX IF NOT EXISTS idx_lovb_conference_short ON lovb_teams(conference_short);
CREATE INDEX IF NOT EXISTS idx_lovb_division ON lovb_teams(division);
CREATE INDEX IF NOT EXISTS idx_lovb_level ON lovb_teams(level);
"""

PVF_TEAMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS pvf_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    name_short TEXT,
    img TEXT,
    url TEXT,
    division TEXT,
    conference TEXT,
    conference_short TEXT,
    level TEXT,
    current_roster_id TEXT,
    current_season_id TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_pvf_team_id ON pvf_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_pvf_conference ON pvf_teams(conference);
CREATE INDEX IF NOT EXISTS idx_pvf_conference_short ON pvf_teams(conference_short);
CREATE INDEX IF NOT EXISTS idx_pvf_division ON pvf_teams(division);
CREATE INDEX IF NOT EXISTS idx_pvf_level ON pvf_teams(level);
"""

NCAAM_TEAMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ncaam_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    name_short TEXT,
    img TEXT,
    url TEXT,
    division TEXT,
    conference TEXT,
    conference_short TEXT,
    level TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_ncaam_team_id ON ncaam_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_ncaam_conference ON ncaam_teams(conference);
CREATE INDEX IF NOT EXISTS idx_ncaam_conference_short ON ncaam_teams(conference_short);
CREATE INDEX IF NOT EXISTS idx_ncaam_division ON ncaam_teams(division);
CREATE INDEX IF NOT EXISTS idx_ncaam_level ON ncaam_teams(level);
"""

NCAAW_TEAMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ncaaw_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    name_short TEXT,
    img TEXT,
    url TEXT,
    division TEXT,
    conference TEXT,
    conference_short TEXT,
    level TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_ncaaw_team_id ON ncaaw_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_ncaaw_conference ON ncaaw_teams(conference);
CREATE INDEX IF NOT EXISTS idx_ncaaw_conference_short ON ncaaw_teams(conference_short);
CREATE INDEX IF NOT EXISTS idx_ncaaw_division ON ncaaw_teams(division);
CREATE INDEX IF NOT EXISTS idx_ncaaw_level ON ncaaw_teams(level);
"""

# Players table schema SQL
LOVB_PLAYERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS lovb_players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    jersey TEXT,
    profile_url TEXT,
    team_id TEXT,
    conference TEXT,
    level TEXT,
    division TEXT,
    data_source TEXT,
    position TEXT,
    height TEXT,
    hometown TEXT,
    FOREIGN KEY (team_id) REFERENCES lovb_teams(team_id)
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_lovb_player_id ON lovb_players(player_id);
CREATE INDEX IF NOT EXISTS idx_lovb_player_team_id ON lovb_players(team_id);
CREATE INDEX IF NOT EXISTS idx_lovb_player_conference ON lovb_players(conference);
CREATE INDEX IF NOT EXISTS idx_lovb_player_level ON lovb_players(level);
CREATE INDEX IF NOT EXISTS idx_lovb_player_division ON lovb_players(division);
"""

# Players table schema SQL
PVF_PLAYERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS pvf_players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT,
    name TEXT,
    jersey TEXT,
    profile_url TEXT,
    team_id TEXT,
    conference TEXT,
    level TEXT,
    division TEXT,
    data_source TEXT,
    position TEXT,
    height TEXT,
    hometown TEXT,
    college TEXT,
    pro_experience TEXT,
    FOREIGN KEY (team_id) REFERENCES pvf_teams(team_id)
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_pvf_player_id ON pvf_players(player_id);
CREATE INDEX IF NOT EXISTS idx_pvf_player_team_id ON pvf_players(team_id);
CREATE INDEX IF NOT EXISTS idx_pvf_player_conference ON pvf_players(conference);
CREATE INDEX IF NOT EXISTS idx_pvf_player_level ON pvf_players(level);
CREATE INDEX IF NOT EXISTS idx_pvf_player_division ON pvf_players(division);
"""

# NCAAM Players table schema SQL
NCAAM_PLAYERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ncaam_players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT,
    name TEXT,
    jersey TEXT,
    profile_url TEXT,
    team_id TEXT,
    data_source TEXT,
    position TEXT,
    height TEXT,
    hometown TEXT,
    high_school TEXT,
    team TEXT,
    class_year TEXT,
    team_short TEXT,
    year TEXT,
    season_id TEXT,
    FOREIGN KEY (team_id) REFERENCES ncaam_teams(team_id)
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_ncaam_player_id ON ncaam_players(player_id);
CREATE INDEX IF NOT EXISTS idx_ncaam_player_team_id ON ncaam_players(team_id);
"""

# NCAAW Players table schema SQL
NCAAW_PLAYERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ncaaw_players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT,
    name TEXT,
    jersey TEXT,
    profile_url TEXT,
    team_id TEXT,
    data_source TEXT,
    position TEXT,
    height TEXT,
    hometown TEXT,
    high_school TEXT,
    team TEXT,
    class_year TEXT,
    team_short TEXT,
    year TEXT,
    season_id TEXT,
    FOREIGN KEY (team_id) REFERENCES ncaaw_teams(team_id)
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_ncaaw_player_id ON ncaaw_players(player_id);
CREATE INDEX IF NOT EXISTS idx_ncaaw_player_team_id ON ncaaw_players(team_id);
"""

# LOVB Results table schema SQL
LOVB_RESULTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS lovb_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT UNIQUE NOT NULL,
    date TEXT,
    home_team_name TEXT,
    away_team_name TEXT,
    score TEXT,
    team_stats TEXT,
    scoreboard TEXT,
    match_url TEXT,
    home_team_id TEXT,
    away_team_id TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_lovb_match_id ON lovb_results(match_id);
CREATE INDEX IF NOT EXISTS idx_lovb_match_teams ON lovb_results(home_team_name, away_team_name);
"""

# PVF Results table schema SQL
PVF_RESULTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS pvf_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pvf_match_id TEXT UNIQUE NOT NULL,
    season_id TEXT,
    date TEXT,
    location TEXT,
    home_team_id TEXT,
    home_team_name TEXT,
    home_team_img TEXT,
    home_team_score TEXT,
    away_team_id TEXT,
    away_team_name TEXT,
    away_team_img TEXT,
    away_team_score TEXT,
    score TEXT,
    team_stats TEXT,
    scoreboard TEXT,
    video TEXT,
    volley_station_match_id TEXT,
    status TEXT,
    title TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_pvf_match_id ON pvf_results(pvf_match_id);
CREATE INDEX IF NOT EXISTS idx_pvf_teams ON pvf_results(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_pvf_date ON pvf_results(date);
CREATE INDEX IF NOT EXISTS idx_pvf_status ON pvf_results(status);
"""

# NCAAM Results table schema SQL
NCAAM_RESULTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ncaam_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT UNIQUE NOT NULL,
    date TEXT,
    time TEXT,
    location TEXT,
    home_team_id TEXT,
    home_team_name TEXT,
    away_team_id TEXT,
    away_team_name TEXT,
    score TEXT,
    attendance TEXT,
    box_score TEXT,
    officials TEXT,
    pbp TEXT,
    individual_stats TEXT,
    division TEXT,
    division_roman TEXT,
    year TEXT,
    status TEXT
);

-- Create index on common query fields
CREATE INDEX IF NOT EXISTS idx_ncaam_match_id ON ncaam_results(match_id);
CREATE INDEX IF NOT EXISTS idx_ncaam_teams ON ncaam_results(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_ncaam_date ON ncaam_results(date);
CREATE INDEX IF NOT EXISTS idx_ncaam_status ON ncaam_results(status);
"""

def create_schema_file(directory: Union[str, Path] = None) -> str:
    """
    Create a schema file with all schemas.

    Args:
        directory: Directory to create the schema file in (default: current directory)

    Returns:
        Path to the created schema file
    """
    if directory is None:
        directory = os.getcwd()

    directory_path = Path(directory)
    directory_path.mkdir(exist_ok=True, parents=True)

    schema_path = directory_path / "schema.sql"

    with open(schema_path, "w") as f:
        f.write(get_schema_sql())

    return str(schema_path)


def get_schema_sql() -> str:
    """
    Get all schema SQL.

    Returns:
        SQL for creating all schemas
    """
    return (
        LOVB_TEAMS_SCHEMA
        + PVF_TEAMS_SCHEMA
        + NCAAM_TEAMS_SCHEMA
        + NCAAW_TEAMS_SCHEMA
        + LOVB_PLAYERS_SCHEMA
        + PVF_PLAYERS_SCHEMA
        + NCAAM_PLAYERS_SCHEMA
        + NCAAW_PLAYERS_SCHEMA
        + LOVB_RESULTS_SCHEMA
        + PVF_RESULTS_SCHEMA
        + NCAAM_RESULTS_SCHEMA
    )
