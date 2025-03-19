"""SQLite database operations for volleyball teams."""

import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple


class Database:
    """SQLite database handler class for volleyball teams data."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file. If None, creates an in-memory database.
        """
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
        """
        Execute an SQL query.
        
        Args:
            query: SQL query to execute
            params: Parameters to bind to the query
            
        Returns:
            SQLite cursor object
        """
        if not self.conn:
            self.connect()
            
        return self.cursor.execute(query, params)

    def executemany(self, query: str, params_list: List[Union[tuple, dict]]) -> sqlite3.Cursor:
        """
        Execute an SQL query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples or dictionaries
            
        Returns:
            SQLite cursor object
        """
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

    def fetchone(self) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the result.
        
        Returns:
            Dictionary with row data or None if no more rows
        """
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the result.
        
        Returns:
            List of dictionaries with row data
        """
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def create_tables(self, schema_sql: Optional[str] = None, schema_file: Optional[Union[str, Path]] = None) -> None:
        """
        Create database tables from schema SQL or schema file.
        
        Args:
            schema_sql: SQL schema string
            schema_file: Path to the SQL schema file
        """
        if not self.conn:
            self.connect()
            
        if schema_file:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
                
        if schema_sql:
            # Split on semicolons to execute multiple statements
            statements = schema_sql.split(';')
            for statement in statements:
                if statement.strip():
                    self.execute(statement)
                    
            self.commit()

    # Team-specific methods
    def add_team(self, team_data: Dict[str, Any]) -> int:
        """
        Add a team to the database.
        
        Args:
            team_data: Dictionary containing team data
            
        Returns:
            ID of the inserted team
        """
        if not self.conn:
            self.connect()
            
        query = """
        INSERT OR REPLACE INTO teams 
        (team_id, name, name_short, img, url, division, conference, conference_short, level)
        VALUES (:team_id, :name, :name_short, :img, :url, :division, :conference, :conference_short, :level)
        """
        
        self.execute(query, team_data)
        self.commit()
        return self.cursor.lastrowid

    def add_teams(self, teams_data: List[Dict[str, Any]]) -> int:
        """
        Add multiple teams to the database.
        
        Args:
            teams_data: List of dictionaries containing team data
            
        Returns:
            Number of teams added
        """
        if not self.conn:
            self.connect()
            
        query = """
        INSERT OR REPLACE INTO teams 
        (team_id, name, name_short, img, url, division, conference, conference_short, level)
        VALUES (:team_id, :name, :name_short, :img, :url, :division, :conference, :conference_short, :level)
        """
        
        self.executemany(query, teams_data)
        self.commit()
        return len(teams_data)

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a team by its team_id.
        
        Args:
            team_id: The team's unique identifier
            
        Returns:
            Dictionary with team data or None if not found
        """
        if not self.conn:
            self.connect()
            
        self.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,))
        return self.fetchone()

    def get_teams(self, 
                 conference: Optional[str] = None, 
                 division: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get teams with optional filtering.
        
        Args:
            conference: Filter by conference
            division: Filter by division
            
        Returns:
            List of dictionaries with team data
        """
        if not self.conn:
            self.connect()
            
        query = "SELECT * FROM teams"
        params = []
        conditions = []
        
        if conference:
            conditions.append("conference = ?")
            params.append(conference)
            
        if division:
            conditions.append("division = ?")
            params.append(division)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        self.execute(query, tuple(params))
        return self.fetchall()

    def search_teams(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for teams by name or conference.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of dictionaries with team data
        """
        if not self.conn:
            self.connect()
            
        search_param = f"%{search_term}%"
        query = """
        SELECT * FROM teams 
        WHERE name LIKE ? OR name_short LIKE ? OR conference LIKE ?
        """
        
        self.execute(query, (search_param, search_param, search_param))
        return self.fetchall()

    def delete_team(self, team_id: str) -> bool:
        """
        Delete a team by its team_id.
        
        Args:
            team_id: The team's unique identifier
            
        Returns:
            True if a team was deleted, False otherwise
        """
        if not self.conn:
            self.connect()
            
        self.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
        self.commit()
        return self.cursor.rowcount > 0

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