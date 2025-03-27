"""Module for fetching PVF match schedule and results."""

import requests
import logging


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_pvf_schedules():
    """
    Fetch PVF schedule data from API

    Returns:
        List of dictionaries with schedule data
    """
    logger.info("Fetching PVF schedules...")

    try:
        # API endpoints for past and upcoming games
        season_links = [
            "https://provolleyball.com/api/schedule-events/?filter%5Bevent_state%5D=past&per_page=500",
            "https://provolleyball.com/api/schedule-events/?filter%5Bevent_state%5D=upcoming&per_page=500",
        ]

        # Title corrections for known typos
        title_corrections = {
            "Indy Ignite at Orlando Valkryies": "Indy Ignite at Orlando Valkyries"
        }

        # Collect all games
        games = []
        for season_url in season_links:
            try:
                response = requests.get(season_url)
                response.raise_for_status()
                matches = response.json().get("data", [])
                games.extend(matches)
                logger.info(f"Fetched {len(matches)} matches from {season_url}")
            except requests.RequestException as e:
                logger.error(f"Error fetching from {season_url}: {e}")

        # Initialize the schedule list
        schedule = []

        # Process each game in the response
        for game in games:
            try:
                # Extract the title
                title = game.get("title", "")

                # Skip all-star matches or special events
                if "2025 PVF All-Star Match" in title or "All-Star" in title:
                    logger.info(f"Skipping All-Star match: {title}")
                    continue

                # Correct the title if it matches a known typo
                if title in title_corrections:
                    title = title_corrections[title]

                # Determine home and away teams from title
                home_team = ""
                away_team = ""

                if " at " in title:
                    away_team, home_team = title.split(" at ")
                elif " vs " in title:
                    home_team, away_team = title.split(" vs ")
                elif " vs. " in title:
                    home_team, away_team = title.split(" vs. ")
                else:
                    logger.warning(f"Skipping game with invalid title format: {title}")
                    continue  # Skip this game if the title format is invalid

                # Strip and clean the team names
                home_team = home_team.strip()
                away_team = away_team.strip()

                # Get team details directly from the flat structure
                first_team_name = game.get("first_team_name", "")
                first_team_id = str(first_team_name).lower().replace(" ", "-")
                first_team_score = game.get("first_team_score", "")

                second_team_name = game.get("second_team_name", "")
                second_team_id = str(second_team_name).lower().replace(" ", "-")
                second_team_score = game.get("second_team_score", "")

                # Determine which team is home and which is away based on venue_type or title match
                home_details = {}
                away_details = {}

                # Check if first team name matches home team from title
                if (
                    first_team_name.lower() in home_team.lower()
                    or home_team.lower() in first_team_name.lower()
                ):
                    # First team is home team
                    home_details = {
                        "id": first_team_id,
                        "name": first_team_name or home_team,
                        "score": first_team_score,
                    }
                    away_details = {
                        "id": second_team_id,
                        "name": second_team_name or away_team,
                        "score": second_team_score,
                    }
                elif (
                    second_team_name.lower() in home_team.lower()
                    or home_team.lower() in second_team_name.lower()
                ):
                    # Second team is home team
                    home_details = {
                        "id": second_team_id,
                        "name": second_team_name or home_team,
                        "score": second_team_score,
                    }
                    away_details = {
                        "id": first_team_id,
                        "name": first_team_name or away_team,
                        "score": first_team_score,
                    }
                else:
                    # If no match, use the title team names and IDs from API if possible
                    logger.warning(f"Team name mismatch in game: {title}")
                    logger.warning(f"  Title: home='{home_team}', away='{away_team}'")
                    logger.warning(
                        f"  API: first='{first_team_name}', second='{second_team_name}'"
                    )

                    # Check if venue_type can help determine home/away
                    venue_type = game.get("venue_type", "")

                    if venue_type == "home":
                        # First team is home
                        home_details = {
                            "id": first_team_id,
                            "name": first_team_name or home_team,
                            "score": first_team_score,
                        }
                        away_details = {
                            "id": second_team_id,
                            "name": second_team_name or away_team,
                            "score": second_team_score,
                        }
                    elif venue_type == "away":
                        # Second team is home
                        home_details = {
                            "id": second_team_id,
                            "name": second_team_name or home_team,
                            "score": second_team_score,
                        }
                        away_details = {
                            "id": first_team_id,
                            "name": first_team_name or away_team,
                            "score": first_team_score,
                        }
                    else:
                        # Default to using title names
                        home_details = {"id": "", "name": home_team, "score": ""}
                        away_details = {"id": "", "name": away_team, "score": ""}

                # Format the score string for database storage
                score_text = game.get("result_text", "")
                if home_details["score"] and away_details["score"]:
                    # If we have numeric scores, format them consistently
                    score_text = f"{home_details['score']}-{away_details['score']}"

                # Determine game status
                event_state = game.get("status", "").lower()
                if event_state == "completed":
                    status = "completed"
                elif event_state == "upcoming":
                    status = "scheduled"
                else:
                    status = event_state if event_state else "unknown"

                # Combine the details into the desired match entry structure
                match_entry = {
                    "pvf_match_id": game.get("id", ""),  # Original PVF match ID
                    "season_id": game.get("season_id"),
                    "score": score_text,
                    "date": game.get(
                        "start_datetime"
                    ),  # Keep as 'date' for utils_schedules.py
                    "location": game.get("location", ""),
                    "home_team_id": home_details["id"],
                    "home_team_name": home_details["name"],
                    "home_team_score": home_details["score"],
                    "away_team_id": away_details["id"],
                    "away_team_name": away_details["name"],
                    "away_team_score": away_details["score"],
                    "team_stats": "https://widgets.volleystation.com/team-stats/"
                    + str(game.get("volley_station_match_id", "")),
                    "scoreboard": "https://widgets.volleystation.com/scoreboard/"
                    + str(game.get("volley_station_match_id", "")),
                    "video": game.get("presented_by_url", ""),
                    "volley_station_match_id": str(
                        game.get("volley_station_match_id", "")
                    ),
                    "status": status,
                    "title": title,
                }

                # Add the match entry to the schedule
                schedule.append(match_entry)

            except Exception as e:
                logger.error(f"Error processing game: {e}")
                import traceback

                logger.error(traceback.format_exc())

        logger.info(f"Processed {len(schedule)} PVF matches")
        return schedule

    except Exception as e:
        logger.error(f"Error in fetch_pvf_schedules: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return []


def main():
    """
    Main function to fetch PVF schedules and insert into database
    """
    # Fetch PVF schedule data
    schedule_data = fetch_pvf_schedules()

    print(schedule_data)


if __name__ == "__main__":
    main()
