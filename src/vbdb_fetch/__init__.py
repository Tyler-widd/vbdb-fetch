"""VBDB SQLite database package for volleyball teams data."""

from .db import Database
from .schema import create_schema_file, get_schema_sql

__version__ = "0.1.0"

# Define a standard path for the database
import os
from pathlib import Path

def get_default_db_path() -> Path:
    """Get the default path for the database file."""
    # Calculate path relative to package root, then up one more level to the project root
    package_dir = Path(__file__).parent
    project_root = package_dir.parent.parent.parent  # One more level up to reach vbdb-sqlite
    
    # Create database directory at the project root level
    db_dir = project_root / "database"
    db_dir.mkdir(exist_ok=True)
    
    return db_dir / "vbdb.db"

# Easy function to initialize the database
def init_db(db_path=None, in_memory=False):
    """
    Initialize the database with the volleyball teams schema.
    
    Args:
        db_path: Path to the database file (None for default location)
        in_memory: If True, creates an in-memory database
        
    Returns:
        Database instance
    """
    if in_memory:
        db = Database(None)
    else:
        if db_path is None:
            db_path = get_default_db_path()
        db = Database(db_path)
    
    db.connect()
    db.create_tables(schema_sql=get_schema_sql())
    return db

__all__ = ["Database", "create_schema_file", "get_schema_sql", "init_db", "get_default_db_path"]