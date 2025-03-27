"""SQLite database operations for volleyball teams."""

import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Union


class Database:
    """SQLite database handler class for volleyball teams data."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Establish connection to the database."""
        if self.db_path is None:
            self.conn = sqlite3.connect(":memory:")
        else:
            # Ensure the directory exists
            if isinstance(self.db_path, str):
                db_dir = os.path.dirname(self.db_path)
            else:
                db_dir = self.db_path.parent

            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path)

        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Return rows as dictionaries
        self.conn.row_factory = sqlite3.Row

        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def execute(self, query: str, params: Union[tuple, dict] = ()) -> sqlite3.Cursor:
        """Execute an SQL query."""
        if not self.conn:
            self.connect()

        return self.cursor.execute(query, params)

    def executemany(
        self, query: str, params_list: List[Union[tuple, dict]]
    ) -> sqlite3.Cursor:
        """Execute an SQL query with multiple parameter sets."""
        if not self.conn:
            self.connect()

        return self.cursor.executemany(query, params_list)

    def commit(self) -> None:
        """Commit changes to the database."""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """Roll back changes."""
        if self.conn:
            self.conn.rollback()

    def create_tables(
        self,
        schema_sql: Optional[str] = None,
        schema_file: Optional[Union[str, Path]] = None,
    ) -> None:
        """Create database tables from schema SQL or schema file."""
        if not self.conn:
            self.connect()

        if schema_file:
            with open(schema_file, "r") as f:
                schema_sql = f.read()

        if schema_sql:
            # Split on semicolons to execute multiple statements
            statements = schema_sql.split(";")
            for statement in statements:
                if statement.strip():
                    self.execute(statement)

            self.commit()

    # LOVB Teams
    def add_lovb_teams(self, teams_data: List[Dict[str, Any]]) -> int:
        """Add multiple LOVB teams to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO lovb_teams 
        (team_id, name, name_short, img, url, division, conference, conference_short, level)
        VALUES (:team_id, :name, :name_short, :img, :url, :division, :conference, :conference_short, :level)
        """

        self.executemany(query, teams_data)
        self.commit()
        return len(teams_data)

    # PVF Teams
    def add_pvf_teams(self, teams_data: List[Dict[str, Any]]) -> int:
        """Add multiple PVF teams to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO pvf_teams 
        (team_id, name, name_short, img, url, division, conference, conference_short, level, 
         current_roster_id, current_season_id)
        VALUES (:team_id, :name, :name_short, :img, :url, :division, :conference, :conference_short, :level,
                :current_roster_id, :current_season_id)
        """

        self.executemany(query, teams_data)
        self.commit()
        return len(teams_data)

    # NCAAM Teams
    def add_ncaam_teams(self, teams_data: List[Dict[str, Any]]) -> int:
        """Add multiple NCAAM teams to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO ncaam_teams 
        (team_id, name, name_short, img, url, division, conference, conference_short, level)
        VALUES (:team_id, :name, :name_short, :img, :url, :division, :conference, :conference_short, :level)
        """

        self.executemany(query, teams_data)
        self.commit()
        return len(teams_data)

    # NCAAW Teams
    def add_ncaaw_teams(self, teams_data: List[Dict[str, Any]]) -> int:
        """Add multiple NCAAW teams to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO ncaaw_teams 
        (team_id, name, name_short, img, url, division, conference, conference_short, level)
        VALUES (:team_id, :name, :name_short, :img, :url, :division, :conference, :conference_short, :level)
        """

        self.executemany(query, teams_data)
        self.commit()
        return len(teams_data)

    # LOVB Players
    def add_lovb_players(self, players_data: List[Dict[str, Any]]) -> int:
        """Add multiple players to the lovb_players table."""
        if not self.conn:
            self.connect()

        # Get all existing team_ids
        self.execute("SELECT team_id FROM lovb_teams")
        valid_team_ids = {row["team_id"] for row in self.fetchall()}

        # Process players and validate team_ids
        processed_players = []

        for player in players_data:
            player_copy = player.copy()

            # Check team_id validity
            if player_copy["team_id"] not in valid_team_ids:
                print(
                    f"Skipping player {player_copy.get('name', 'Unknown')} - invalid team_id: {player_copy['team_id']}"
                )
                continue

            processed_players.append(player_copy)

        if not processed_players:
            print(
                f"Warning: All {len(players_data)} players skipped due to invalid team_ids"
            )
            return 0

        query = """
        INSERT OR REPLACE INTO lovb_players 
        (player_id, name, jersey, profile_url, team_id, conference, level, division, 
        data_source, position, height, hometown)
        VALUES (:player_id, :name, :jersey, :profile_url, :team_id, :conference, :level, 
                :division, :data_source, :position, :height, :hometown)
        """

        self.executemany(query, processed_players)
        self.commit()
        return len(processed_players)

    # PVF Players
    def add_pvf_players(self, players_data: List[Dict[str, Any]]) -> int:
        """Add multiple players to the pvf_players table."""
        if not self.conn:
            self.connect()

        # Get all existing team_ids
        self.execute("SELECT team_id FROM pvf_teams")
        valid_team_ids = {row["team_id"] for row in self.fetchall()}

        # Process players and validate team_ids
        processed_players = []

        for player in players_data:
            player_copy = player.copy()

            # Check team_id validity
            if player_copy["team_id"] not in valid_team_ids:
                print(
                    f"Skipping player {player_copy.get('name', 'Unknown')} - invalid team_id: {player_copy['team_id']}"
                )
                continue

            processed_players.append(player_copy)

        if not processed_players:
            print(
                f"Warning: All {len(players_data)} players skipped due to invalid team_ids"
            )
            return 0

        query = """
        INSERT OR REPLACE INTO pvf_players 
        (player_id, name, jersey, profile_url, team_id, conference, level, division, 
        data_source, position, height, hometown, college, pro_experience)
        VALUES (:player_id, :name, :jersey, :profile_url, :team_id, :conference, :level, 
                :division, :data_source, :position, :height, :hometown, :college, :pro_experience)
        """

        self.executemany(query, processed_players)
        self.commit()
        return len(processed_players)

    # NCAAM Players
    def add_ncaam_players(self, players_data: List[Dict[str, Any]]) -> int:
        """Add multiple players to the ncaam_players table."""
        if not self.conn:
            self.connect()

        # Get all existing team_ids
        self.execute("SELECT team_id FROM ncaam_teams")
        valid_team_ids = {row["team_id"] for row in self.fetchall()}

        # Process players and validate team_ids
        processed_players = []

        for player in players_data:
            player_copy = player.copy()

            # Check team_id validity
            if player_copy["team_id"] not in valid_team_ids:
                print(
                    f"Skipping player {player_copy.get('name', 'Unknown')} - invalid team_id: {player_copy['team_id']}"
                )
                continue

            processed_players.append(player_copy)

        if not processed_players:
            print(
                f"Warning: All {len(players_data)} players skipped due to invalid team_ids"
            )
            return 0

        query = """
        INSERT OR REPLACE INTO ncaam_players 
        (player_id, name, jersey, profile_url, team_id, 
        data_source, position, height, hometown, high_school, team, class_year,
        team_short, year, season_id)
        VALUES (:player_id, :name, :jersey, :profile_url, :team_id, :data_source, :position, :height, :hometown, 
                :high_school, :team, :class_year, :team_short, :year, :season_id)
        """

        self.executemany(query, processed_players)
        self.commit()
        return len(processed_players)

    # NCAAW Players
    def add_ncaaw_players(self, players_data: List[Dict[str, Any]]) -> int:
        """Add multiple players to the ncaaw_players table."""
        if not self.conn:
            self.connect()

        # Get all existing team_ids
        self.execute("SELECT team_id FROM ncaaw_teams")
        valid_team_ids = {row["team_id"] for row in self.fetchall()}

        # Process players and validate team_ids
        processed_players = []

        for player in players_data:
            player_copy = player.copy()

            # Check team_id validity
            if player_copy["team_id"] not in valid_team_ids:
                print(
                    f"Skipping player {player_copy.get('name', 'Unknown')} - invalid team_id: {player_copy['team_id']}"
                )
                continue

            processed_players.append(player_copy)

        if not processed_players:
            print(
                f"Warning: All {len(players_data)} players skipped due to invalid team_ids"
            )
            return 0

        query = """
        INSERT OR REPLACE INTO ncaaw_players 
        (player_id, name, jersey, profile_url, team_id,
        data_source, position, height, hometown, high_school, team, class_year,
        team_short, year, season_id)
        VALUES (:player_id, :name, :jersey, :profile_url, :team_id, :data_source, :position, :height, :hometown, 
                :high_school, :team, :class_year, :team_short, :year, :season_id)
        """

        self.executemany(query, processed_players)
        self.commit()
        return len(processed_players)

    # LOVB Results
    def add_lovb_results(self, results_data: List[Dict[str, Any]]) -> int:
        """Add multiple LOVB match results to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO lovb_results 
        (match_id, date, home_team_name, away_team_name, score, team_stats, scoreboard, match_url, home_team_id, away_team_id)
        VALUES (:match_id, :date, :home_team_name, :away_team_name, :score, :team_stats, :scoreboard, :match_url, :home_team_id, :away_team_id)
        """

        self.executemany(query, results_data)
        self.commit()
        return len(results_data)

    # PVF Results
    def add_pvf_results(self, results_data: List[Dict[str, Any]]) -> int:
        """Add multiple PVF match results to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO pvf_results 
        (pvf_match_id, season_id, date, location, home_team_id, home_team_name,
        home_team_score, away_team_id, away_team_name, away_team_score, 
        score, team_stats, scoreboard, video, volley_station_match_id, status, title)
        VALUES (:pvf_match_id, :season_id, :date, :location, :home_team_id, :home_team_name,
                :home_team_score, :away_team_id, :away_team_name, :away_team_score, 
                :score, :team_stats, :scoreboard, :video, :volley_station_match_id, :status, :title)
        """

        self.executemany(query, results_data)
        self.commit()
        return len(results_data)

    # NCAAM Results
    def add_ncaam_results(self, results_data: List[Dict[str, Any]]) -> int:
        """Add multiple NCAAM match results to the database."""
        if not self.conn:
            self.connect()

        query = """
        INSERT OR REPLACE INTO ncaam_results 
        (match_id, date, time, location, home_team_id, home_team_name,
        away_team_id, away_team_name, score, attendance, box_score,
        officials, pbp, individual_stats, division, division_roman, year, status)
        VALUES (:match_id, :date, :time, :location, :home_team_id, :home_team_name,
                :away_team_id, :away_team_name, :score, :attendance, :box_score,
                :officials, :pbp, :individual_stats, :division, :division_roman, :year, :status)
        """

        self.executemany(query, results_data)
        self.commit()
        return len(results_data)

    def fetchall(self):
        """Helper method to fetch results from the cursor."""
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()
