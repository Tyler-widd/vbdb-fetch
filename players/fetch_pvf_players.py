import requests
import logging
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from teams.fetch_pvf_teams import fetch_pvf_teams

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_pvf_players():
    """
    Fetch Pro Volleyball Federation (PVF) player rosters

    Returns:
        list: List of player dictionaries with standardized fields
    """
    logger.info("Fetching PVF rosters...")

    try:
        teams = fetch_pvf_teams()
        players = []

        for team in teams:
            roster_id = team.get("current_roster_id")
            team_id = team.get("team_id")
            if not roster_id:
                logger.warning(
                    f"No roster ID found for team {team.get('name', 'Unknown')}"
                )
                continue

            try:
                logger.info(
                    f"Fetching roster for {team.get('name', 'Unknown')} (ID: {roster_id})"
                )
                url = (
                    f"https://provolleyball.com/api/rosters/{roster_id}/player-rosters"
                )
                params = {
                    "include[1]": "headshotImage",
                    "include[2]": "player.headshotImage",
                    "include[3]": "positions",
                    "sort[0]": "players.last_name",
                }

                response = requests.get(url, params=params)
                response.raise_for_status()
                rosters = response.json().get("data", [])

                for roster in rosters:
                    player_data = roster.get("player", {})
                    player_id = (
                        player_data.get("first_name", {}).lower()
                        + "-"
                        + player_data.get("last_name", {}).lower()
                    )
                    team_id = team_id
                    full_name = player_data.get("full_name", "")
                    college = player_data.get("college", "")
                    hometown = player_data.get("hometown", "")
                    height_feet = player_data.get("height_feet", "")
                    height_inches = player_data.get("height_inches", "")
                    height = (
                        f"{height_feet}'{height_inches}"
                        if height_feet and height_inches
                        else ""
                    )
                    jersey_number = player_data.get("jersey_number", "")
                    pro_experience = player_data.get("pro_experience", "")
                    player_positions = ", ".join(
                        pos.get("name", "")
                        for pos in roster.get("player_positions", [])
                    )
                    player_url = "https://provolleyball.com" + player_data.get(
                        "permalink", ""
                    )

                    # Standardized player entry
                    player_entry = {
                        "name": full_name,
                        "jersey": str(jersey_number) if jersey_number else "",
                        "position": player_positions,
                        "height": height,
                        "player_id": player_id,
                        "hometown": hometown,
                        "team": team.get("name", ""),
                        "conference": "PVF",
                        "level": "Pro Women",
                        "team_id": team_id,
                        "division": "Pro",
                        "profile_url": player_url,
                        "college": college,
                        "pro_experience": pro_experience,
                        "data_source": "PVF",
                    }

                    players.append(player_entry)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching players for roster_id {roster_id}: {e}")

        logger.info(f"Fetched {len(players)} PVF players")
        return players

    except Exception as e:
        logger.error(f"Error in fetch_pvf_rosters: {e}")
        return []


if __name__ == "__main__":
    # Test the function
    players = fetch_pvf_players()
    print(players)
    print(f"Found {len(players)} PVF players")
