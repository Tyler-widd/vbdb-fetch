import requests
from bs4 import BeautifulSoup
import logging
import sys
from datetime import datetime, timedelta
import re
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define headers for requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Define season metadata for Men's NCAA Volleyball
men_meta_link_content = [
    {"year": "2025", "season_id": "18463", "division": "di"},
    {"year": "2025", "season_id": "18464", "division": "diii"}
]

def get_box_score_links(season_id, date_str):
    """
    Get box score links for a specific season and date

    Args:
        season_id: NCAA season ID
        date_str: Date string in MM/DD/YYYY format

    Returns:
        List of box score URLs
    """
    url = f"https://stats.ncaa.org/season_divisions/{season_id}/livestream_scoreboards?game_date={date_str}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all links with target attribute containing "box_score"
        box_score_links = []
        all_links = soup.find_all(
            "a", attrs={"target": lambda value: value and "box_score" in value}
        )

        for link in all_links:
            box_score_links.append("https://stats.ncaa.org" + link["href"])

        return box_score_links

    except Exception as e:
        logger.error(f"Error fetching box score links for {date_str}: {e}")
        return []


def parse_box_score(url, soup=None):
    """
    Parse an NCAA volleyball box score page and extract match information.

    Args:
        url (str): The URL of the box score page
        soup (BeautifulSoup, optional): Existing BeautifulSoup object if already parsed

    Returns:
        dict: Structured match data
    """
    if soup is None:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            logger.error(f"Error fetching box score page {url}: {e}")
            return None

    # Initialize data structure
    match_data = {
        "date": "",
        "time": "",
        "home_team_id": "",
        "away_team_id": "",
        "home_team_name": "",
        "away_team_name": "",
        "attendance": "",
        "location": "",
        "match_id": url.split('/')[-2],
        "score": "",
        "box_score": url,
        "officials": url.replace("box_score", "officials"),
        "pbp": url.replace("box_score", "play_by_play"),
        "individual_stats": url.replace("box_score", "individual_stats"),
    }

    # Find the main table
    top_tbl = soup.find("div", attrs={"class": "table-responsive"})
    if not top_tbl:
        # Try alternate method if the main table isn't found
        match_rows = soup.find_all("tr")
        if match_rows:
            top_tbl = match_rows[0].parent

    if not top_tbl:
        logger.warning(f"Could not find main table in {url}")
        return match_data

    # First, collect all team names, team IDs, and their positions in the table
    # NCAA box score: First team is typically away, second team is typically home
    team_info = []
    
    # Find all team name cells
    team_cells = top_tbl.find_all(
        "td", attrs={"class": "grey_text d-none d-sm-table-cell"}
    )
    
    # Collect team names
    for i, cell in enumerate(team_cells):
        team_name = ""
        team_id = ""
        position = i  # 0 for first team (away), 1 for second team (home)
        
        # Get team name from link or text
        team_link = cell.find("a")
        if team_link:
            team_name = team_link.text.strip()
        else:
            team_name = cell.text.strip()
        
        # Add to our team info collection
        team_info.append({
            "name": team_name,
            "id": team_id,
            "position": position
        })
    
    # Now look for team images that contain the team IDs
    img_tags = top_tbl.find_all("img", class_="large_logo_image")
    
    for img in img_tags:
        # Get team ID from image src
        if "src" in img.attrs:
            team_id = img["src"].split(".gif")[0].split("sm//")[-1]
            
            # Find which team this image belongs to
            img_cell = img.find_parent("td")
            if img_cell:
                # Find the closest team name cell to determine which team this is
                next_cell = img_cell.find_next_sibling("td", attrs={"class": "grey_text d-none d-sm-table-cell"})
                prev_cell = img_cell.find_previous_sibling("td", attrs={"class": "grey_text d-none d-sm-table-cell"})
                
                if next_cell:
                    # Image is before the team name (typical pattern)
                    team_name = ""
                    team_link = next_cell.find("a")
                    if team_link:
                        team_name = team_link.text.strip()
                    else:
                        team_name = next_cell.text.strip()
                    
                    # Find which team in our collection matches this name
                    for team in team_info:
                        if team["name"] == team_name:
                            team["id"] = team_id
                            break
                elif prev_cell:
                    # Image is after the team name (less common)
                    team_name = ""
                    team_link = prev_cell.find("a")
                    if team_link:
                        team_name = team_link.text.strip()
                    else:
                        team_name = prev_cell.text.strip()
                    
                    # Find which team in our collection matches this name
                    for team in team_info:
                        if team["name"] == team_name:
                            team["id"] = team_id
                            break
    
    # Look at score table to confirm team names and ordering
    score_table = top_tbl.find("table", style="border-collapse: collapse")
    if score_table:
        rows = score_table.find_all("tr")
        if len(rows) >= 3:  # Header row + 2 team rows
            # Get team names from the score table
            team1_name_cell = rows[1].find("td")  # First team row, first cell
            team2_name_cell = rows[2].find("td")  # Second team row, first cell
            
            if team1_name_cell and team2_name_cell:
                team1_name = team1_name_cell.text.strip()
                team2_name = team2_name_cell.text.strip()
                
                # Use these names to validate/correct our team_info collection
                if len(team_info) >= 2:
                    # Simple case: just make sure names match
                    if team_info[0]["name"] != team1_name and team1_name:
                        logger.info(f"Correcting team name: {team_info[0]['name']} -> {team1_name}")
                        team_info[0]["name"] = team1_name
                    
                    if team_info[1]["name"] != team2_name and team2_name:
                        logger.info(f"Correcting team name: {team_info[1]['name']} -> {team2_name}")
                        team_info[1]["name"] = team2_name
                elif len(team_info) == 1:
                    # Only one team found in cells, add the other from score table
                    if team_info[0]["name"] == team1_name:
                        team_info.append({
                            "name": team2_name,
                            "id": "",
                            "position": 1
                        })
                    else:
                        team_info.append({
                            "name": team1_name,
                            "id": "",
                            "position": 0
                        })
                else:
                    # No teams found in cells, create from score table
                    team_info = [
                        {"name": team1_name, "id": "", "position": 0},
                        {"name": team2_name, "id": "", "position": 1}
                    ]
    
    # Now assign teams to home and away based on NCAA convention (second team is home)
    if len(team_info) >= 2:
        # Away team is first in the table
        match_data["away_team_name"] = team_info[0]["name"]
        match_data["away_team_id"] = team_info[0]["id"]
        
        # Home team is second in the table
        match_data["home_team_name"] = team_info[1]["name"]
        match_data["home_team_id"] = team_info[1]["id"]
    elif len(team_info) == 1:
        # Only one team found, check if we can determine if it's home or away
        # For now, assume it's the home team (more likely to have data)
        match_data["home_team_name"] = team_info[0]["name"]
        match_data["home_team_id"] = team_info[0]["id"]

    # Get score information
    score_cells = top_tbl.find_all(
        "td", attrs={"style": lambda x: x and "font-size:36px" in x}
    )
    if len(score_cells) >= 2:
        away_score = score_cells[0].text.strip()
        home_score = score_cells[1].text.strip()

        # Extract set scores from the nested table
        if score_table:
            rows = score_table.find_all("tr")
            if len(rows) >= 3:  # Header row + 2 team rows
                away_row = rows[1]
                home_row = rows[2]

                # Get all set scores (excluding the team name and final score)
                away_set_scores = [
                    td.text.strip()
                    for td in away_row.find_all("td", class_="grey_text")
                ]
                home_set_scores = [
                    td.text.strip()
                    for td in home_row.find_all("td", class_="grey_text")
                ]

                # Format set scores as requested
                set_scores = []
                for i in range(len(away_set_scores)):
                    if i < len(home_set_scores):
                        set_scores.append(
                            f"{away_set_scores[i]}-{home_set_scores[i]}"
                        )

                match_data["score"] = (
                    f"{away_score}-{home_score} [{', '.join(set_scores)}]"
                )

            # Extract date, time, location, and attendance from the footer rows
            footer_rows = (
                score_table.find_all("tr")[3:]
                if len(score_table.find_all("tr")) > 3
                else []
            )

            # Process each footer row
            for row in footer_rows:
                row_text = row.get_text().strip()

                # Extract date and time
                date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", row_text)
                if date_match:
                    match_data["date"] = date_match.group(1)

                    # Extract and convert time if present
                    time_pattern = re.search(
                        r"(\d{1,2}):(\d{2})\s*([APM]{2})", row_text
                    )
                    if time_pattern:
                        hour = int(time_pattern.group(1))
                        minute = time_pattern.group(2)
                        am_pm = time_pattern.group(3).upper()

                        # Convert to military time
                        if am_pm == "PM" and hour < 12:
                            hour += 12
                        elif am_pm == "AM" and hour == 12:
                            hour = 0

                        # Format with leading zeros
                        match_data["time"] = f"{hour:02d}:{minute}"

                # Extract location
                if not re.search(r"Attendance", row_text) and not date_match:
                    match_data["location"] = row_text.strip()

                # Extract attendance - with or without commas
                attendance_match = re.search(r"Attendance:\s*([\d,]+)", row_text)
                if attendance_match:
                    # Remove commas from the attendance value
                    attendance_value = attendance_match.group(1).replace(",", "")
                    match_data["attendance"] = attendance_value

    # If we still don't have what we need, try to extract info from raw text
    if not match_data["date"] or not match_data["score"]:
        # Check all text content for date and location patterns
        all_text = soup.get_text()

        # Find date if not already set
        if not match_data["date"]:
            date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", all_text)
            if date_match:
                match_data["date"] = date_match.group(1)

        # Find time if not already set
        if not match_data["time"]:
            time_pattern = re.search(r"(\d{1,2}):(\d{2})\s*([APM]{2})", all_text)
            if time_pattern:
                hour = int(time_pattern.group(1))
                minute = time_pattern.group(2)
                am_pm = time_pattern.group(3).upper()

                # Convert to military time
                if am_pm == "PM" and hour < 12:
                    hour += 12
                elif am_pm == "AM" and hour == 12:
                    hour = 0

                # Format with leading zeros
                match_data["time"] = f"{hour:02d}:{minute}"

        # Find attendance if not already set
        if not match_data["attendance"]:
            attendance_match = re.search(r"Attendance:\s*([\d,]+)", all_text)
            if attendance_match:
                attendance_value = attendance_match.group(1).replace(",", "")
                match_data["attendance"] = attendance_value

        # Find location if not already set
        if not match_data["location"]:
            # Look for location patterns - often in parentheses after the date
            location_pattern = re.search(
                r"\d{1,2}/\d{1,2}/\d{4}.*?(\([^)]+\))", all_text
            )
            if location_pattern:
                match_data["location"] = location_pattern.group(1).strip()
            else:
                # Try to find Arena or Center names
                arena_pattern = re.search(
                    r"(.*Arena.*|.*Center.*|.*Stadium.*|.*Field.*|.*Court.*)", all_text
                )
                if arena_pattern:
                    match_data["location"] = arena_pattern.group(1).strip()

    # Debug output
    logger.debug(f"Match: {match_data['away_team_name']} vs {match_data['home_team_name']}")
    logger.debug(f"IDs: away={match_data['away_team_id']}, home={match_data['home_team_id']}")

    return match_data


def fetch_ncaam_schedules(year="2025", date_range=None, only_yesterday=False):
    """
    Fetch NCAA men's volleyball schedules for the specified parameters
    
    Args:
        year: Year to fetch data for (default: 2025)
        date_range: Optional tuple of (start_date, end_date) as strings in MM/DD/YYYY format
        only_yesterday: If True, only fetch yesterday's data, ignoring date_range
        
    Returns:
        List of dictionaries with schedule data
    """
    if only_yesterday:
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%m/%d/%Y")
        date_range = (yesterday_str, yesterday_str)
        logger.info(f"Only fetching data for yesterday: {yesterday_str}")
    
    logger.info(f"Fetching NCAA Men's volleyball schedules for {year}")
    
    division_roman_map = {
        "di": "I",
        "dii": "II",
        "diii": "III"
    }

    # Load metadata
    meta_links = men_meta_link_content

    # Filter metadata for the requested year
    year_meta = [link for link in meta_links if link["year"] == year]

    if not year_meta:
        logger.error(f"No metadata found for year {year}")
        return []

    # Determine date range
    if date_range:
        start_date_str, end_date_str = date_range
        start_date = datetime.strptime(start_date_str, "%m/%d/%Y")
        end_date = datetime.strptime(end_date_str, "%m/%d/%Y")
    else:
        # Default to the men's volleyball season (December 15 to May 24)
        year_int = int(year)
        start_date = datetime.strptime(f"12/15/{year_int-1}", "%m/%d/%Y")  # Season starts in previous year
        end_date = datetime.strptime(f"05/24/{year}", "%m/%d/%Y")

    all_matches = []
    box_score_links = []

    # First, collect all box score links for each division and date
    for meta in year_meta:
        season_id = meta["season_id"]
        division = meta["division"]

        logger.info(f"Processing Division {division} (Season ID: {season_id})")

        # Generate list of dates to process
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%m/%d/%Y")

            # Get box score links for this date and division
            links = get_box_score_links(season_id, date_str)

            if links:
                logger.info(
                    f"Found {len(links)} matches for {date_str} in Division {division}"
                )

                # Record division information with each link
                for link in links:
                    box_score_links.append(
                        {
                            "url": link,
                            "division": division,
                            "division_roman": division_roman_map.get(division, "")
                        }
                    )

            # Move to next day
            current_date += timedelta(days=1)

    logger.info(
        f"Found {len(box_score_links)} total box score links across all dates and divisions"
    )

    # Now process each box score link to extract match data
    for i, link_info in enumerate(box_score_links):
        try:
            url = link_info["url"]
            division = link_info["division"]
            division_roman = link_info["division_roman"]

            logger.info(f"Processing box score {i + 1}/{len(box_score_links)}: {url}")

            match_data = parse_box_score(url)

            if match_data:
                # Add NCAA-specific metadata
                match_data["division"] = division
                match_data["division_roman"] = division_roman
                match_data["year"] = year

                # Set status to completed if we have a score
                if match_data["score"]:
                    match_data["status"] = "completed"
                else:
                    match_data["status"] = "unknown"

                all_matches.append(match_data)

        except Exception as e:
            logger.error(
                f"Error processing box score {link_info.get('url', 'unknown')}: {e}"
            )

    logger.info(f"Processed {len(all_matches)} NCAA Men's matches for {year}")
    return all_matches


def fetch_ncaam_schedule(only_yesterday=False):
    """Wrapper function to fetch NCAAM schedules with appropriate parameters"""
    year = '2025'
    if only_yesterday:
        return fetch_ncaam_schedules(year, only_yesterday=True)
    else:
        return fetch_ncaam_schedules(year, date_range=("12/15/2024", "05/24/2025"))


def main():
    """
    Main function to fetch NCAA men's schedules 
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch NCAA men's volleyball schedules")
    parser.add_argument("--yesterday", action="store_true", help="Only fetch yesterday's data")
    parser.add_argument("--start-date", help="Start date (MM/DD/YYYY)")
    parser.add_argument("--end-date", help="End date (MM/DD/YYYY)")
    parser.add_argument("--year", default="2025", help="Season year")
    
    args = parser.parse_args()
    
    if args.yesterday:
        schedule_data = fetch_ncaam_schedules(year=args.year, only_yesterday=True)
    elif args.start_date and args.end_date:
        schedule_data = fetch_ncaam_schedules(year=args.year, date_range=(args.start_date, args.end_date))
    else:
        # Default to the full 2025 men's volleyball season
        schedule_data = fetch_ncaam_schedules(year=args.year, date_range=("12/15/2024", "05/24/2025"))
    
    print(f"Fetched {len(schedule_data)} NCAAM match records")
    
    # You could add code here to directly save to the database if needed


if __name__ == "__main__":
    main()