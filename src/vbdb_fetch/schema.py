"""SQLite database schema definitions for volleyball teams."""

import os
from pathlib import Path
from typing import Union

# Teams table schema SQL
TEAMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
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
CREATE INDEX IF NOT EXISTS idx_team_id ON teams(team_id);
CREATE INDEX IF NOT EXISTS idx_conference ON teams(conference);
CREATE INDEX IF NOT EXISTS idx_conference_short ON teams(conference_short);
CREATE INDEX IF NOT EXISTS idx_division ON teams(division);
CREATE INDEX IF NOT EXISTS idx_level ON teams(level);
"""

def create_schema_file(directory: Union[str, Path] = None) -> str:
    """
    Create a schema file with the teams schema.
    
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
        f.write(TEAMS_SCHEMA)
    
    return str(schema_path)

def get_schema_sql() -> str:
    """
    Get the teams schema SQL.
    
    Returns:
        SQL for creating the teams schema
    """
    return TEAMS_SCHEMA