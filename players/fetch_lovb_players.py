import re
import logging
from bs4 import BeautifulSoup
from seleniumbase import Driver
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from teams.fetch_lovb_teams import fetch_lovb_teams

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_lovb_players():
    """
    Fetch and process LOVB team rosters

    Returns:
        list: List of player dictionaries with standardized fields
    """
    logger.info("Fetching LOVB rosters...")

    try:
        teams = fetch_lovb_teams()
        roster_urls = []
        for team in teams:
            roster_urls.append(team["url"] + "/roster")

        if not roster_urls:
            logger.warning("No roster URLs found for LOVB teams")
            return []

        driver = Driver(browser="chrome", headless=True)
        all_data = []
        unwanted_terms = ["Founding Athlete", "NEW", "-founding-athlete"]

        for url in roster_urls:
            try:
                logger.info(f"Fetching roster from {url}")
                driver.get(url)  # Open the URL
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")

                # Find all the tables with class 'roster-table'
                tables = soup.find_all("table", class_="roster-table")

                if not tables:  # If no tables are found, skip this URL
                    logger.warning(f"No roster table found at {url}")
                    continue

                # Loop through each table
                for table in tables:
                    headers = [header.text.strip() for header in table.find_all("th")]

                    # Extract data from each row in the table
                    for row in table.find_all("tr")[1:]:  # Skip the header row
                        columns = row.find_all("td")

                        if columns:
                            row_data = {}
                            row_data["url"] = (
                                url  # Store URL for team name extraction later
                            )

                            # Extract and clean up the player's name and number from the first column
                            player_name_column = columns[0].get_text(strip=True)

                            # Use regex to separate the player number from the name
                            match = re.match(r"(\d+)([A-Za-z\s]+)", player_name_column)
                            if match:
                                player_number = match.group(1)  # The number (e.g., '1')
                                raw_player_name = match.group(
                                    2
                                ).strip()  # The name (e.g., 'Jordyn Poulter')
                                player_name = re.sub(
                                    r"(?<!^)([A-Z])", r" \1", raw_player_name
                                )
                            else:
                                player_number = ""
                                player_name = player_name_column

                            for term in unwanted_terms:
                                player_name = player_name.replace(term, "").strip()
                                player_name = player_name.replace("  ", " ").strip()

                            # Add the player number and name to the dictionary
                            row_data["Player Number"] = player_number
                            row_data["Name"] = player_name

                            # For each other column, map it to the corresponding header
                            for header, column in zip(headers[1:], columns[1:]):
                                column_text = column.get_text(strip=True)
                                row_data[header] = column_text

                            # Add the row's dictionary to all_data
                            all_data.append(row_data)

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")

        # Clean up the driver
        driver.quit()

        # Now process all the data after collecting it
        processed_data = []
        for item in all_data:
            # Determine team name from URL
            if "atlanta" in item["url"]:
                team_name = "LOVB Atlanta"
                team_id = "lovb-atlanta-volleyball"  # Make sure this matches EXACTLY what's in the teams table
            elif "salt" in item["url"]:
                team_name = "LOVB Salt Lake"
                team_id = "lovb-salt-lake-volleyball"  # Make sure this matches EXACTLY what's in the teams table
            elif "austin" in item["url"]:
                team_name = "LOVB Austin"
                team_id = "lovb-austin-volleyball"  # Make sure this matches EXACTLY what's in the teams table
            elif "houston" in item["url"]:
                team_name = "LOVB Houston"
                team_id = "lovb-houston-volleyball"  # Make sure this matches EXACTLY what's in the teams table
            elif "madison" in item["url"]:
                team_name = "LOVB Madison"
                team_id = "lovb-madison-volleyball"  # Make sure this matches EXACTLY what's in the teams table
            elif "omaha" in item["url"]:
                team_name = "LOVB Omaha"
                team_id = "lovb-omaha-volleyball"  # Make sure this matches EXACTLY what's in the teams table
            else:
                team_name = None
                team_id = None

            city = team_name.replace("LOVB ", "") if team_name else ""

            # Create links
            clean_name = item["Name"].replace("Founding Athlete", "").strip()
            # Handle potential double spaces after removal
            final_name = " ".join(clean_name.split())
            url_name = "-".join(clean_name.split()).lower()
            # Create processed entry with all transformations
            player_url = (
                "https://www.lovb.com/teams/lovb-"
                + city.lower()
                + "-volleyball/athletes/"
                + url_name
            )
            processed_entry = {
                "name": final_name,
                "jersey": item["Player Number"]
                if item["Player Number"] != ""
                else "Staff",
                "profile_url": player_url,
                "team": team_name,
                "team_id": team_id,
                "conference": "LOVB",
                "level": "Pro Women",
                "player_id": "-".join(final_name.split()),
                "division": "Pro",
                "data_source": "LOVB",
            }

            # Handle position mapping
            position = item.get("Position", item.get("Title", ""))
            if position == "Opposite Hitter":
                processed_entry["position"] = "OPP"
            elif position == "Middle Blocker":
                processed_entry["position"] = "MB"
            elif position == "Setter":
                processed_entry["position"] = "S"
            elif position == "Outside Hitter":
                processed_entry["position"] = "OH"
            elif position == "Libero":
                processed_entry["position"] = "L"
            else:
                processed_entry["position"] = position

            # Add height and hometown if available
            if "Height" in item:
                processed_entry["height"] = item["Height"]

            # Rename columns
            if "College / Home Club" in item:
                processed_entry["hometown"] = item["College / Home Club"]

            processed_data.append(processed_entry)

        logger.info(f"Processed {len(processed_data)} LOVB players")
        return processed_data

    except Exception as e:
        logger.error(f"Error in fetch_lovb_rosters: {e}")
        return []


if __name__ == "__main__":
    # Test the function
    players = fetch_lovb_players()
    print(f"Found {len(players)} LOVB players")
    print(players[0])
