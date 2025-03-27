"""Module for fetching LOVB match schedule and results."""

import requests
from bs4 import BeautifulSoup
import logging
import re
from seleniumbase import Driver

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fix_salt_lake_url(url):
    """Fix Salt Lake URL by adding proper hyphen"""
    if url and isinstance(url, str):
        # Handle different patterns of Salt Lake in URLs
        patterns = [
            (r"Salt Lake", "Salt-Lake"),
            (r"/teams/lovb-salt lake", "/teams/lovb-salt-lake"),
            (r"Salt Lake-", "Salt-Lake-"),
        ]

        fixed_url = url
        for pattern, replacement in patterns:
            fixed_url = re.sub(pattern, replacement, fixed_url, flags=re.IGNORECASE)

        return fixed_url
    return url


def fetch_lovb_schedule():
    """
    Fetch LOVB schedules from their website

    Returns:
        List of dictionaries with schedule data
    """
    logger.info("Fetching LOVB schedules...")

    url = "https://www.lovb.com/schedule"
    driver = Driver(browser="chrome", headless=True)

    try:
        driver.get(url)
        logger.info(f"Fetching {url}")

        # Wait for the page to load completely
        driver.sleep(2)  # Add a small delay to ensure content loads

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Find all week containers
        week_containers = soup.find_all(
            "div", attrs={"class": "mb-lg grid w-full gap-lg"}
        )

        all_matches = []

        for week_idx, week in enumerate(week_containers):
            # Find all matches within this week
            matches = week.find_all(
                "div", attrs={"class": "[&>header]:first-of-type:rounded-t-md"}
            )

            # If no matches found with that specific class, try another approach
            if not matches:
                matches = week.find_all(
                    "div",
                    attrs={
                        "class": lambda x: x and "flex-1" in x and "[&>header]" in x
                    },
                )

            for match_idx, match in enumerate(matches):
                try:
                    # Get date for this match
                    date_div = match.find(
                        "div",
                        attrs={"class": "flex items-center gap-sm text-text-secondary"},
                    )
                    date = date_div.text.strip() if date_div else "Date not found"

                    # Get match details link
                    match_details_link_elem = match.find(
                        "a",
                        attrs={"class": "link-hover flex items-center gap-sm text-xs"},
                    )
                    match_details_link = (
                        match_details_link_elem["href"]
                        if match_details_link_elem
                        and match_details_link_elem.has_attr("href")
                        else ""
                    )

                    # Fix Salt Lake URL if needed
                    match_details_link = fix_salt_lake_url(match_details_link)

                    # Find the section with teams and scores
                    section = match.find("section")
                    if not section:
                        logger.warning("No section found, skipping match")
                        continue

                    # Get teams
                    team_links = section.find_all(
                        "a", class_="group link-hover flex items-center gap-sm"
                    )

                    teams = []
                    for team_link in team_links:
                        team_text_div = team_link.find(
                            "div", class_="text-pretty text-sm"
                        )
                        if team_text_div:
                            team_text = team_text_div.text.strip()
                            teams.append(team_text)

                    if len(teams) < 2:
                        logger.warning("Not enough teams found, skipping match")
                        continue

                    team_1 = teams[0]
                    team_2 = teams[1]

                    # Determine if this is a completed match or upcoming match
                    is_completed = False

                    # Get set scores
                    set_scores_divs = section.find_all(
                        "div", class_="flex items-center gap-sm"
                    )

                    team_1_set_wins = "0"
                    team_2_set_wins = "0"
                    team_1_set_scores = []
                    team_2_set_scores = []

                    score_divs_processed = 0

                    for score_div in set_scores_divs:
                        # Check if this div contains score information
                        score_elements = score_div.find_all(
                            "div", class_=lambda x: x and "size-4" in x
                        )
                        if not score_elements:
                            continue

                        # We found scores, so this is a completed match
                        is_completed = True

                        # Get sets won
                        sets_won_div = score_div.find(
                            "div", class_="text-pretty text-sm"
                        )
                        sets_won = sets_won_div.text.strip() if sets_won_div else "0"

                        # Get individual set scores
                        set_scores = [elem.text.strip() for elem in score_elements]

                        if score_divs_processed == 0:  # First team
                            team_1_set_wins = sets_won
                            team_1_set_scores = set_scores
                            score_divs_processed += 1
                        elif score_divs_processed == 1:  # Second team
                            team_2_set_wins = sets_won
                            team_2_set_scores = set_scores
                            score_divs_processed += 1
                            break  # We have both teams' scores, no need to continue

                    # Format the score string
                    score_string = ""
                    if is_completed:
                        score_parts = []
                        for j in range(
                            min(len(team_1_set_scores), len(team_2_set_scores))
                        ):
                            score_parts.append(
                                f"{team_1_set_scores[j]}-{team_2_set_scores[j]}"
                            )

                        score_string = f"{team_1_set_wins}-{team_2_set_wins} [{', '.join(score_parts)}]"

                    # Initialize iframe URLs
                    match_id = ""
                    team_stats_url = ""
                    scoreboard_url = ""

                    # Only fetch match details for completed matches with links
                    if match_details_link:
                        try:
                            # Ensure the URL is properly formatted with Salt-Lake
                            match_url = "https://lovb.com" + fix_salt_lake_url(
                                match_details_link
                            )

                            res = requests.get(match_url)
                            match_soup = BeautifulSoup(res.content, "html.parser")

                            # Try to find the iframe
                            iframe = match_soup.find(
                                "iframe",
                                attrs={
                                    "class": "mt-2xl h-[23.3125rem] w-full sm:h-[24.3125rem] xl:h-[44.1875rem]"
                                },
                            )

                            if iframe and iframe.has_attr("src"):
                                iframe_src = iframe["src"]
                                base_url = iframe_src.split("?side")[0]
                                team_stats_url = base_url.replace(
                                    "play-by-play", "team-stats"
                                )
                                scoreboard_url = base_url.replace(
                                    "play-by-play", "scoreboard"
                                )
                                match_id = scoreboard_url.split("/")[-1]
                        except Exception as e:
                            logger.error(
                                f"Error fetching match details for {match_details_link}: {e}"
                            )

                    # Extract home and away teams
                    # In LOVB, the second team listed is typically the home team
                    home_team = team_2
                    away_team = team_1

                    def generate_team_id(team_name):
                        return "-".join(team_name.lower().split())

                    home_team_id = generate_team_id(home_team)
                    away_team_id = generate_team_id(away_team)

                    # Create match object
                    match_data = {
                        "match_id": match_id,
                        "date": date,
                        "home_team_name": home_team,
                        "away_team_name": away_team,
                        "score": score_string,
                        "team_stats": team_stats_url,
                        "scoreboard": scoreboard_url,
                        "match_url": "https://lovb.com" + match_details_link
                        if match_details_link
                        else "",
                        "home_team_id": home_team_id + "-volleyball",
                        "away_team_id": away_team_id + "-volleyball",
                    }

                    all_matches.append(match_data)
                    logger.info(
                        f"Match added: {match_data['away_team_name']} at {match_data['home_team_name']}"
                        + (
                            f", Score: {match_data['score']}"
                            if is_completed
                            else " (Upcoming)"
                        )
                    )

                except Exception as e:
                    logger.error(f"Error processing match: {e}")

        logger.info(f"Processed {len(all_matches)} LOVB matches")
        return all_matches

    except Exception as e:
        logger.error(f"Error in fetch_lovb_schedule: {e}")
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    # For testing
    results = fetch_lovb_schedule()
    print(f"Found {len(results)} matches")
