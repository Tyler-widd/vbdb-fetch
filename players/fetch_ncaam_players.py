import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
import sys
from pathlib import Path
import sqlite3
import time

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_ncaam_players(db_path="vbdb.db"):
    """
    Fetch NCAA volleyball team rosters using team data from SQLite database

    Args:
        db_path (str): Path to the SQLite database

    Returns:
        list: List of player dictionaries with standardized fields
    """
    logger.info("Fetching NCAA Men's volleyball rosters...")

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)

    # Query to get team information from the database
    query = "SELECT * FROM teams WHERE level = 'NCAA M'"

    # Load team data into DataFrame
    teams_df = pd.read_sql_query(query, conn)

    # Create a roster list to hold all player data
    roster_list = []

    # Track stats for reporting
    teams_processed = 0
    teams_with_players = 0
    teams_without_players = 0
    total_players = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Fetch season_id function
    def fetch_season_id(team_id):
        url = f"https://stats.ncaa.org/teams/history/MVB/{team_id}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, "html.parser")
        try:
            season_id = soup.find("table").find("a")["href"]
            team = soup.find("option", attrs={"value": team_id}).text
            logger.info(f"Found Season {season_id} from {team}")
            return season_id
        except Exception as e:
            logger.warning(f"Could not find season for team_id {team_id}: {e}")
            return None

    team_ids = list(teams_df["team_id"].unique())
    for team_id in team_ids:
        teams_processed += 1

        # Get team data
        team = teams_df[teams_df["team_id"] == team_id].iloc[0]
        team_name = team.get("name", f"Team ID: {team_id}")
        team_short = team.get("name_short")

        # Get season_id for this team
        season_id = fetch_season_id(team_id)
        if not season_id:
            teams_without_players += 1
            continue

        # Build the roster URL
        roster_url = "https://stats.ncaa.org" + season_id + "/roster"
        logger.info(f"Fetching roster from {roster_url}")

        try:
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)

            response = requests.get(roster_url, headers=headers)

            if response.status_code != 200:
                logger.warning(
                    f"HTTP {response.status_code} error for team {team_name} (ID: {team_id})"
                )
                teams_without_players += 1
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # Check if we need to select a specific team first
            # If we're on a page with team selection options
            team_selection = soup.find("select", {"name": "id"})
            if team_selection:
                logger.info(
                    f"Team selection page detected, looking for team ID {team_id}"
                )

                # Find the option with our team ID
                found_team = False
                for option in team_selection.find_all("option"):
                    option_team_id = option.get("value")
                    if option_team_id == str(team_id):
                        found_team = True
                        team_roster_url = (
                            f"https://stats.ncaa.org{season_id}/roster/{option_team_id}"
                        )
                        logger.info(
                            f"Found team, fetching specific roster from {team_roster_url}"
                        )

                        # Get the roster page for this specific team
                        response = requests.get(team_roster_url, headers=headers)
                        if response.status_code != 200:
                            logger.warning(
                                f"HTTP {response.status_code} for team roster {team_name}"
                            )
                            continue

                        soup = BeautifulSoup(response.content, "html.parser")
                        break

                if not found_team:
                    logger.warning(f"Team ID {team_id} not found in selection list")
                    teams_without_players += 1
                    continue

            # Find and parse roster table - try different possible table IDs
            table = None
            for table_id_prefix in ["roster_", "rosters_form_players"]:
                table = soup.find(
                    "table", {"id": lambda x: x and x.startswith(table_id_prefix)}
                )
                if table:
                    break

            if not table:
                # Try a more generic approach if no table with expected ID is found
                table = soup.find("table", {"class": "dataTable"})
                if not table:
                    # Look for any table that might contain a roster
                    all_tables = soup.find_all("table")
                    for t in all_tables:
                        # Check if table likely contains player names
                        if (
                            t.find("td")
                            and t.find("td").text
                            and len(t.find_all("tr")) > 1
                        ):
                            table = t
                            break

            if not table:
                logger.warning(
                    f"No roster table found for team {team_name} (ID: {team_id})"
                )
                teams_without_players += 1
                continue

            # Make sure table has a thead
            thead = table.find("thead")
            if not thead:
                # Some NCAA pages use th elements in tr instead of thead
                header_row = table.find("tr", {"class": "heading"})
                if header_row:
                    thead = header_row
                else:
                    # Try to find the first row that might be headers
                    first_row = table.find("tr")
                    if first_row and first_row.find("th"):
                        thead = first_row
                    else:
                        logger.warning(
                            f"No table header found for team {team_name} (ID: {team_id})"
                        )
                        teams_without_players += 1
                        continue

            # Extract headers
            headers_row = []
            for th in thead.find_all(["th", "td"]):
                headers_row.append(th.text.strip())

            # If no headers found, try to create generic ones
            if not headers_row:
                sample_row = table.find("tr", {"class": None})  # Non-header row
                if sample_row:
                    num_cells = len(sample_row.find_all(["td", "th"]))
                    headers_row = [f"Column{i}" for i in range(num_cells)]

            headers_row.append("Player URL")  # Add a header for the player URL

            # Make sure table has a tbody or equivalent
            tbody = table.find("tbody")
            if not tbody:
                # If no tbody, use all rows except the first (header) row
                tbody_rows = table.find_all("tr")[1:]
            else:
                tbody_rows = tbody.find_all("tr")

            if not tbody_rows:
                logger.warning(
                    f"No player rows found for team {team_name} (ID: {team_id})"
                )
                teams_without_players += 1
                continue

            # Find the year
            year = team.get("year", "")
            if not year:
                year_select = soup.find("select", attrs={"name": "year_id"})
                if year_select and year_select.find("option", selected=True):
                    year = year_select.find("option", selected=True).text.strip()
                elif year_select and year_select.find("option"):
                    year = year_select.find("option").text.strip()

            # Extract player data
            players = []
            for tr in tbody_rows:
                cells = tr.find_all(["td", "th"])
                row_data = []
                player_url = None

                for cell in cells:
                    # Check if the cell contains a link
                    link = cell.find("a")
                    if link and "href" in link.attrs:
                        row_data.append(link.text.strip())
                        player_url = link["href"]
                    else:
                        row_data.append(cell.text.strip())

                # Only process rows that have data
                if len(row_data) > 0:
                    # Append the player URL as a separate field
                    row_data.append(player_url)
                    # Pad with empty strings if needed to match headers
                    while len(row_data) < len(headers_row):
                        row_data.append("")
                    # Trim extra cells if needed
                    row_data = row_data[: len(headers_row)]
                    players.append(row_data)

            # Create DataFrame for the current team - ONLY if we have players
            if players:
                teams_with_players += 1
                total_players += len(players)

                # Create DataFrame for this team's players
                roster_df = pd.DataFrame(players, columns=headers_row)
                roster_df["team_id"] = team_id
                roster_df["year"] = year
                roster_df["team_name"] = team_name
                roster_df["team_short"] = team_short
                roster_df["season_id"] = season_id

                roster_list.append(roster_df)
                logger.info(
                    f"Found {len(players)} players for team {team_name} (ID: {team_id})"
                )
            else:
                teams_without_players += 1
                logger.warning(
                    f"No players found for team {team_name} (ID: {team_id}) - skipping"
                )

        except Exception as e:
            teams_without_players += 1
            logger.error(f"Error processing team {team_name} (ID: {team_id}): {e}")

    # Close the database connection
    conn.close()

    # Log summary statistics
    logger.info(
        f"NCAA Men's roster stats: {teams_processed} teams processed, "
        f"{teams_with_players} teams with players, "
        f"{teams_without_players} teams without players, "
        f"{total_players} total players found"
    )

    # Combine all roster data
    if not roster_list:
        logger.warning("No roster data found for NCAA Men's volleyball")
        return []

    try:
        roster_df = pd.concat(roster_list, sort=False).reset_index(drop=True)
    except Exception as e:
        logger.error(f"Error combining roster data: {e}")

        # Try to identify problematic DataFrames
        for i, df in enumerate(roster_list):
            logger.info(
                f"DataFrame {i} shape: {df.shape}, columns: {df.columns.tolist()}"
            )

        return []

    # Convert to standardized player format
    players = []
    for _, row in roster_df.iterrows():
        # Try to identify the common column names
        name_col = next(
            (col for col in roster_df.columns if col.lower() in ["name", "player"]),
            "Name",
        )
        jersey_col = next(
            (
                col
                for col in roster_df.columns
                if col.lower() in ["#", "no.", "jersey", "number"]
            ),
            "#",
        )
        position_col = next(
            (
                col
                for col in roster_df.columns
                if col.lower() in ["position", "pos", "pos."]
            ),
            "Position",
        )
        height_col = next(
            (
                col
                for col in roster_df.columns
                if col.lower() in ["height", "ht", "ht."]
            ),
            "Height",
        )
        hometown_col = next(
            (
                col
                for col in roster_df.columns
                if col.lower() in ["hometown", "home town"]
            ),
            "Hometown",
        )
        highschool_col = next(
            (
                col
                for col in roster_df.columns
                if col.lower() in ["high school", "previous school"]
            ),
            "High School",
        )
        class_col = next(
            (
                col
                for col in roster_df.columns
                if col.lower() in ["class", "yr", "cl.", "year"]
            ),
            "Class",
        )

        player = {
            "name": row.get(name_col, ""),
            "jersey": row.get(jersey_col, ""),
            "position": row.get(position_col, ""),
            "height": row.get(height_col, ""),
            "hometown": row.get(hometown_col, ""),
            "team": row.get("team_name", ""),
            "team_short": row.get("team_short", ""),
            "profile_url": f"https://stats.ncaa.org{row.get('Player URL', '')}"
            if row.get("Player URL")
            else "",
            "player_id": row.get("Player URL", "").split("/")[-1]
            if row.get("Player URL")
            else "",
            "high_school": row.get(highschool_col, ""),
            "class_year": row.get(class_col, ""),
            "state": row.get("state", ""),
            "data_source": "NCAA",
            "team_id": row.get("team_id", ""),
            "year": row.get("year", ""),
            "season_id": row.get("season_id", "").split("/")[-1],
        }
        players.append(player)

    logger.info(f"Fetched {len(players)} NCAA Men's volleyball players")
    return players
