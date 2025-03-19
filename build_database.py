#!/usr/bin/env python3
"""
Build volleyball teams database by importing data from all sources.
This script should be run from the project root to create or update the database.
"""
import logging
import time
import sys
import os
import shutil
from pathlib import Path
from typing import List, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import database module - assuming vbdb_fetch is installed as a package
try:
    from vbdb_fetch import init_db
except ImportError:
    logger.error("Cannot import vbdb_fetch. Make sure you've installed the package.")
    logger.error("Run 'pip install vbdb-fetch' or install it from source.")
    sys.exit(1)

# Import team fetchers
try:
    from teams.fetch_lovb_teams import fetch_lovb_teams
    from teams.fetch_pvf_teams import fetch_pvf_teams
    from teams.fetch_ncaam_teams import fetch_ncaam_teams
    from teams.fetch_ncaaw_teams import fetch_ncaaw_teams

    FETCHERS = {
        "LOVB": fetch_lovb_teams,
        "PVF": fetch_pvf_teams,
        "NCAAM": fetch_ncaam_teams,
        "NCAAW": fetch_ncaaw_teams
    }
except ImportError as e:
    logger.error(f"Error importing team fetchers: {e}")
    logger.error("Make sure team fetchers are in the teams directory")
    sys.exit(1)

def import_teams(db, league: str, fetch_func) -> int:
    """
    Import teams for a specific league.
    
    Args:
        db: Database connection
        league: League name for logging
        fetch_func: Function to fetch teams data
        
    Returns:
        Number of teams imported
    """
    logger.info(f"Importing {league} teams...")
    start_time = time.time()
    
    try:
        teams = fetch_func()
        if not teams:
            logger.warning(f"No {league} teams found")
            return 0
        
        # Debug: Check level values
        levels = set(team.get('level', 'None') for team in teams)
        logger.info(f"{league} teams have these levels: {levels}")
        
        count = db.add_teams(teams)
        logger.info(f"Imported {count} {league} teams in {time.time() - start_time:.2f}s")
        return count
    except Exception as e:
        logger.error(f"Error importing {league} teams: {e}")
        logger.exception(e)  # This will print the full traceback
        return 0

def build_database(leagues: List[str] = None, db_path: str = None) -> Dict[str, int]:
    """
    Build the volleyball teams database by importing data from specified sources.
    
    Args:
        leagues: List of leagues to import (default: all leagues)
        db_path: Path to the database file (default: ./vbdb.db)
        
    Returns:
        Dictionary with count of teams imported by league
    """
    # Initialize database with appropriate path
    if db_path is None:
        db_path = "./vbdb.db"
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        logger.info(f"Creating directory: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
    
    logger.info(f"Initializing database at: {db_path}")
    db = init_db(db_path)
    
    # Default to all leagues if none specified
    if not leagues:
        leagues = list(FETCHERS.keys())
    
    # Import teams for each league
    results = {}
    for league in leagues:
        if league.upper() in FETCHERS:
            results[league] = import_teams(db, league, FETCHERS[league.upper()])
        else:
            logger.warning(f"Unknown league: {league}")
            results[league] = 0
    
    # Log summary
    total = sum(results.values())
    logger.info(f"Database build complete. Total teams: {total}")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build volleyball teams database")
    parser.add_argument(
        "--leagues", 
        nargs="+", 
        choices=["LOVB", "PVF", "NCAAM", "NCAAW", "ALL"],
        default=["ALL"],
        help="Leagues to import (default: ALL)"
    )
    parser.add_argument(
        "--db-path",
        help="Path to the database file (default: ./vbdb.db)"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Do not copy database to API directory"
    )
    parser.add_argument(
        "--no-local",
        action="store_true",
        help="Do not save database to current directory"
    )
    
    args = parser.parse_args()
    
    # Handle ALL option
    if "ALL" in args.leagues:
        leagues = list(FETCHERS.keys())
    else:
        leagues = args.leagues
    
    # Set the primary database path
    primary_db_path = args.db_path
    if primary_db_path is None:
        if args.no_local and not args.no_api:
            # Only save to API
            primary_db_path = "../vbdb-api/vbdb.db"
        else:
            # Default to local first
            primary_db_path = "./vbdb.db"
    
    # Build database
    results = build_database(leagues, primary_db_path)
    
    # Copy to API directory if needed
    api_db_path = "../vbdb-api/vbdb.db"
    if not args.no_api and primary_db_path != api_db_path:
        api_dir = os.path.dirname(api_db_path)
        if not os.path.exists(api_dir):
            logger.info(f"Creating API directory: {api_dir}")
            os.makedirs(api_dir, exist_ok=True)
        
        logger.info(f"Copying database to API directory: {api_db_path}")
        shutil.copy2(primary_db_path, api_db_path)
    
    # Copy to local directory if needed
    local_db_path = "./vbdb.db"
    if not args.no_local and primary_db_path != local_db_path:
        logger.info(f"Copying database to local directory: {local_db_path}")
        shutil.copy2(primary_db_path, local_db_path)
    
    # Print summary
    print("\nSummary:")
    for league, count in results.items():
        print(f"  {league}: {count} teams")
    print(f"  Total: {sum(results.values())} teams")
    
    # Print database locations
    print("\nDatabase saved to:")
    if not args.no_local:
        print(f"  Local: {os.path.abspath(local_db_path)}")
    if not args.no_api:
        print(f"  API: {os.path.abspath(api_db_path)}")