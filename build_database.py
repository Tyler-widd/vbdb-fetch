#!/usr/bin/env python3
"""
Build volleyball teams database by importing data from all sources.
This script should be run from the project root to create or update the database.
"""
import logging
import time
import sys
import os
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
    from vbdb_fetch.teams.fetch_lovb_teams import fetch_lovb_teams
    from vbdb_fetch.teams.fetch_pvf_teams import fetch_pvf_teams
    from vbdb_fetch.teams.fetch_ncaam_teams import fetch_ncaam_teams
    from vbdb_fetch.teams.fetch_ncaaw_teams import fetch_ncaaw_teams

    FETCHERS = {
        "LOVB": fetch_lovb_teams,
        "PVF": fetch_pvf_teams,
        "NCAAM": fetch_ncaam_teams,
        "NCAAW": fetch_ncaaw_teams
    }
except ImportError as e:
    logger.error(f"Error importing team fetchers: {e}")
    logger.error("Make sure vbdb_fetch package is installed with all team fetchers")
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
        db_path: Path to the database file (default: use package default)
        
    Returns:
        Dictionary with count of teams imported by league
    """
    # Initialize database - now db_path should be in the current directory
    if db_path is None:
        db_path = "./vbdb.db"
    
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
    
    args = parser.parse_args()
    
    # Handle ALL option
    if "ALL" in args.leagues:
        leagues = list(FETCHERS.keys())
    else:
        leagues = args.leagues
    
    # Build database
    results = build_database(leagues, args.db_path)
    
    # Print summary
    print("\nSummary:")
    for league, count in results.items():
        print(f"  {league}: {count} teams")
    print(f"  Total: {sum(results.values())} teams")