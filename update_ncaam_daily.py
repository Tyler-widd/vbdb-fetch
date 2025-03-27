#!/usr/bin/env python3
"""
Update NCAAM schedule data for yesterday only.
This script should be run daily to keep the database up-to-date.
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import database module
try:
    from vbdb_fetch import init_db
except ImportError:
    logger.error("Cannot import vbdb_fetch. Make sure you've installed the package.")
    logger.error("Run 'pip install vbdb-fetch' or install it from source.")
    sys.exit(1)

# Import schedule fetcher
try:
    from schedule.fetch_ncaam_schedule import fetch_ncaam_schedules
except ImportError:
    logger.error("Cannot import fetch_ncaam_schedule. Make sure the file exists.")
    sys.exit(1)


def main():
    """Main function to update the database with yesterday's NCAAM matches."""
    # Initialize database
    db_path = "./vbdb.db"
    logger.info(f"Initializing database at: {db_path}")
    db = init_db(db_path)

    # Fetch yesterday's matches only
    logger.info("Fetching NCAAM matches from yesterday...")
    matches = fetch_ncaam_schedules(year="2025", only_yesterday=True)
    
    if not matches:
        logger.info("No matches found for yesterday.")
        return

    # Add matches to database
    logger.info(f"Adding {len(matches)} matches to database...")
    count = db.add_ncaam_results(matches)
    
    logger.info(f"Successfully added {count} NCAAM matches to database.")


if __name__ == "__main__":
    main()