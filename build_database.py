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
from typing import List, Dict, Callable, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import database module - assuming vbdb_fetch is installed as a package
try:
    from vbdb_fetch import init_db
except ImportError:
    logger.error("Cannot import vbdb_fetch. Make sure you've installed the package.")
    logger.error("Run 'pip install vbdb-fetch' or install it from source.")
    sys.exit(1)

# ========================
# Fetcher Registration
# ========================


class FetcherRegistry:
    """Registry for team and player data fetching functions."""

    def __init__(self):
        self.team_fetchers = {}
        self.player_fetchers = {}
        self.schedule_fetchers = {}

    def register_team_fetcher(self, league: str, fetcher: Callable) -> None:
        """Register a team fetcher function for a league."""
        self.team_fetchers[league.upper()] = fetcher

    def register_player_fetcher(self, league: str, fetcher: Callable) -> None:
        """Register a player fetcher function for a league."""
        self.player_fetchers[league.upper()] = fetcher

    def register_schedule_fetcher(self, league: str, fetcher: Callable) -> None:
        """Register a schedule fetcher function for a league."""
        self.schedule_fetchers[league.upper()] = fetcher

    def get_team_fetcher(self, league: str) -> Optional[Callable]:
        """Get the team fetcher function for a league."""
        return self.team_fetchers.get(league.upper())

    def get_player_fetcher(self, league: str) -> Optional[Callable]:
        """Get the player fetcher function for a league."""
        return self.player_fetchers.get(league.upper())

    def get_schedule_fetcher(self, league: str) -> Optional[Callable]:
        """Get the schedule fetcher function for a league."""
        return self.schedule_fetchers.get(league.upper())

    def get_all_leagues(self) -> List[str]:
        """Get a list of all registered leagues."""
        return list(
            set(self.team_fetchers.keys())
            | set(self.player_fetchers.keys())
            | set(self.schedule_fetchers.keys())
        )


# Create global registry
registry = FetcherRegistry()

# ========================
# Data Import Functions
# ========================


def fetch_and_add_teams(db: Any, league: str, fetch_func: Callable) -> int:
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
        levels = set(team.get("level", "None") for team in teams)
        logger.info(f"{league} teams have these levels: {levels}")

        # Use the appropriate method based on the league
        if league.upper() == "LOVB":
            count = db.add_lovb_teams(teams)
        elif league.upper() == "PVF":
            count = db.add_pvf_teams(teams)
        elif league.upper() == "NCAAM":
            count = db.add_ncaam_teams(teams)
        elif league.upper() == "NCAAW":
            count = db.add_ncaaw_teams(teams)

        logger.info(
            f"Imported {count} {league} teams in {time.time() - start_time:.2f}s"
        )
        return count
    except Exception as e:
        logger.error(f"Error importing {league} teams: {e}")
        logger.exception(e)  # This will print the full traceback
        return 0


def fetch_and_add_players(db: Any, league: str, fetch_func: Callable) -> int:
    """
    Import players for a specific league.

    Args:
        db: Database connection
        league: League name for logging
        fetch_func: Function to fetch players data

    Returns:
        Number of players imported
    """
    logger.info(f"Importing {league} players...")
    start_time = time.time()

    try:
        players = fetch_func()
        if not players:
            logger.warning(f"No {league} players found")
            return 0

        # Use the appropriate method based on the league
        if league.upper() == "LOVB":
            count = db.add_lovb_players(players)
        elif league.upper() == "PVF":
            count = db.add_pvf_players(players)
        elif league.upper() == "NCAAM":
            count = db.add_ncaam_players(players)
        elif league.upper() == "NCAAW":
            count = db.add_ncaaw_players(players)

        logger.info(
            f"Imported {count} {league} players in {time.time() - start_time:.2f}s"
        )
        return count
    except Exception as e:
        logger.error(f"Error importing {league} players: {e}")
        logger.exception(e)
        return 0


def fetch_and_add_schedule(db: Any, league: str, fetch_func: Callable) -> int:
    """
    Import schedule for a specific league.

    Args:
        db: Database connection
        league: League name for logging
        fetch_func: Function to fetch schedule data

    Returns:
        Number of matches imported
    """
    logger.info(f"Importing {league} schedule...")
    start_time = time.time()

    try:
        matches = fetch_func()
        if not matches:
            logger.warning(f"No {league} matches found")
            return 0

        # Use the appropriate method based on the league
        if league.upper() == "LOVB":
            count = db.add_lovb_results(matches)
        elif league.upper() == "PVF":
            count = db.add_pvf_results(matches)  # Added this line
        elif league.upper() == "NCAAM":
            count = db.add_ncaam_results(matches)  # Add this line for NCAAM
        else:
            logger.warning(f"No method to add {league} schedule")
            return 0

        logger.info(
            f"Imported {count} {league} matches in {time.time() - start_time:.2f}s"
        )
        return count
    except Exception as e:
        logger.error(f"Error importing {league} schedule: {e}")
        logger.exception(e)  # This will print the full traceback
        return 0

# ========================
# Database Build Function
# ========================


def build_database(
    leagues: List[str] = None,
    db_path: str = None,
    should_import_teams: bool = True,
    import_rosters: bool = True,
    import_schedules: bool = True,
) -> Dict[str, Dict[str, int]]:
    """
    Build the volleyball database by importing teams, players, and schedules data.

    Args:
        leagues: List of leagues to import (default: all leagues)
        db_path: Path to the database file (default: ./vbdb.db)
        should_import_teams: Whether to import team data (default: True)
        import_rosters: Whether to import player rosters (default: True)
        import_schedules: Whether to import schedules (default: True)

    Returns:
        Dictionary with count of teams, players, and schedules imported by league
    """
    # Initialize database with appropriate path
    if db_path is None:
        db_path = "./vbdb.db"

    # Create directory if it doesn't exist
    ensure_directory_exists(os.path.dirname(db_path))

    logger.info(f"Initializing database at: {db_path}")
    db = init_db(db_path)

    # Default to all leagues if none specified
    if not leagues:
        leagues = registry.get_all_leagues()

    # Initialize results dictionary
    results = {"teams": {}, "players": {}, "schedules": {}}

    for league in leagues:
        # Initialize result counts for this league
        results["teams"][league] = 0
        results["players"][league] = 0
        results["schedules"][league] = 0

        # Import teams if specified
        if should_import_teams:
            team_fetcher = registry.get_team_fetcher(league)
            if team_fetcher:
                results["teams"][league] = fetch_and_add_teams(db, league, team_fetcher)
            else:
                logger.warning(f"No team fetcher for: {league}")

        # Import rosters if specified
        if import_rosters:
            player_fetcher = registry.get_player_fetcher(league)
            if player_fetcher:
                results["players"][league] = fetch_and_add_players(
                    db, league, player_fetcher
                )
            else:
                logger.warning(f"No player fetcher for: {league}")

        # Import schedules if specified
        if import_schedules:
            schedule_fetcher = registry.get_schedule_fetcher(league)
            if schedule_fetcher:
                results["schedules"][league] = fetch_and_add_schedule(
                    db, league, schedule_fetcher
                )
            else:
                logger.warning(f"No schedule fetcher for: {league}")

    # Log summary
    log_build_summary(results)

    return results


# ========================
# Utility Functions
# ========================


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure that a directory exists, creating it if necessary."""
    if directory_path and not os.path.exists(directory_path):
        logger.info(f"Creating directory: {directory_path}")
        os.makedirs(directory_path, exist_ok=True)


def log_build_summary(results: Dict[str, Dict[str, int]]) -> None:
    """Log a summary of the database build results."""
    total_teams = sum(results["teams"].values())
    total_players = sum(results["players"].values())
    total_matches = sum(results["schedules"].values())
    logger.info(
        f"Database build complete. Total teams: {total_teams}, Total players: {total_players}, Total matches: {total_matches}"
    )


def copy_database_file(source_path: str, target_path: str) -> None:
    """Copy a database file to a new location."""
    # Create target directory if needed
    ensure_directory_exists(os.path.dirname(target_path))

    # Copy the file
    logger.info(f"Copying database to: {target_path}")
    shutil.copy2(source_path, target_path)


# ========================
# Command Line Interface
# ========================


def parse_arguments():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Build volleyball teams database")
    parser.add_argument(
        "--leagues",
        nargs="+",
        choices=["LOVB", "PVF", "NCAAM", "NCAAW", "ALL"],
        default=["ALL"],
        help="Leagues to import (default: ALL)",
    )
    parser.add_argument(
        "--db-path", help="Path to the database file (default: ./vbdb.db)"
    )
    parser.add_argument(
        "--no-api", action="store_true", help="Do not copy database to API directory"
    )
    parser.add_argument(
        "--no-local",
        action="store_true",
        help="Do not save database to current directory",
    )
    parser.add_argument("--teams", action="store_true", help="Import team information")
    parser.add_argument("--rosters", action="store_true", help="Import player rosters")
    parser.add_argument(
        "--schedules", action="store_true", help="Import match schedules"
    )

    return parser.parse_args()


def print_results_summary(
    leagues: List[str], results: Dict[str, Dict[str, int]]
) -> None:
    """Print a summary of the results."""
    print("\nSummary:")
    for league in leagues:
        team_count = results["teams"].get(league, 0)
        player_count = results["players"].get(league, 0)
        print(f"  {league}: {team_count} teams, {player_count} players")

    total_teams = sum(results["teams"].values())
    total_players = sum(results["players"].values())
    print(f"  Total: {total_teams} teams, {total_players} players")


def print_database_locations(
    local_db_path: str, api_db_path: str, no_local: bool, no_api: bool
) -> None:
    """Print the locations where the database was saved."""
    print("\nDatabase saved to:")
    if not no_local:
        print(f"  Local: {os.path.abspath(local_db_path)}")
    if not no_api:
        print(f"  API: {os.path.abspath(api_db_path)}")


# ========================
# Register Fetchers
# ========================


def register_fetchers():
    """Register all team and player fetchers."""
    try:
        # Import team fetchers
        from teams.fetch_lovb_teams import fetch_lovb_teams
        from teams.fetch_pvf_teams import fetch_pvf_teams
        from teams.fetch_ncaam_teams import fetch_ncaam_teams
        from teams.fetch_ncaaw_teams import fetch_ncaaw_teams

        # Register team fetchers
        registry.register_team_fetcher("LOVB", fetch_lovb_teams)
        registry.register_team_fetcher("PVF", fetch_pvf_teams)
        registry.register_team_fetcher("NCAAM", fetch_ncaam_teams)
        registry.register_team_fetcher("NCAAW", fetch_ncaaw_teams)

    except ImportError as e:
        logger.error(f"Error importing team fetchers: {e}")
        logger.error("Make sure team fetchers are in the teams directory")
        sys.exit(1)

    try:
        # Import player fetchers
        from players.fetch_lovb_players import fetch_lovb_players
        from players.fetch_pvf_players import fetch_pvf_players
        from players.fetch_ncaam_players import fetch_ncaam_players
        from players.fetch_ncaaw_players import fetch_ncaaw_players

        # Register player fetchers
        registry.register_player_fetcher("LOVB", fetch_lovb_players)
        registry.register_player_fetcher("PVF", fetch_pvf_players)
        registry.register_player_fetcher("NCAAM", fetch_ncaam_players)
        registry.register_player_fetcher("NCAAW", fetch_ncaaw_players)

    except ImportError as e:
        logger.error(f"Error importing player fetchers: {e}")
        logger.error("Make sure player fetchers are in the players directory")
        sys.exit(1)

    try:
        # Import results fetchers
        from schedule.fetch_lovb_schedule import fetch_lovb_schedule
        from schedule.fetch_pvf_schedule import fetch_pvf_schedules
        from schedule.fetch_ncaam_schedule import fetch_ncaam_schedule

        # Register results fetchers
        registry.register_schedule_fetcher("LOVB", fetch_lovb_schedule)
        registry.register_schedule_fetcher("PVF", fetch_pvf_schedules)
        registry.register_schedule_fetcher("NCAAM", fetch_ncaam_schedule)

    except ImportError as e:
        logger.error(f"Error importing schedule fetchers: {e}")
        logger.error("Make sure schedule fetchers are in the schedule directory")
        sys.exit(1)


# ========================
# Main Function
# ========================


def main():
    """Main function."""
    # Register team and player fetchers
    register_fetchers()

    # Parse command line arguments
    args = parse_arguments()

    # Handle ALL option
    if "ALL" in args.leagues:
        leagues = registry.get_all_leagues()
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

    # Determine what to import based on command line flags
    import_teams = False  # Default to False now
    import_rosters = False  # Default to False now
    import_schedules = False  # Default to False now

    # If any specific import flags are set, use them to determine what to import
    if args.teams:
        import_teams = True
    if args.rosters:
        import_rosters = True
    if args.schedules:
        import_schedules = True

    # If no import flags were set, import everything
    if not (args.teams or args.rosters or args.schedules):
        import_teams = True
        import_rosters = True
        import_schedules = True

    # Build database with specified import options
    results = build_database(
        leagues,
        primary_db_path,
        should_import_teams=import_teams,
        import_rosters=import_rosters,
        import_schedules=import_schedules,  # Pass this parameter to build_database
    )

    # Copy to API directory if needed
    api_db_path = "../vbdb-api/vbdb.db"
    if not args.no_api and primary_db_path != api_db_path:
        copy_database_file(primary_db_path, api_db_path)

    # Copy to local directory if needed
    local_db_path = "./vbdb.db"
    if not args.no_local and primary_db_path != local_db_path:
        copy_database_file(primary_db_path, local_db_path)

    # Print summaries
    print_results_summary(leagues, results)
    print_database_locations(local_db_path, api_db_path, args.no_local, args.no_api)


if __name__ == "__main__":
    main()
