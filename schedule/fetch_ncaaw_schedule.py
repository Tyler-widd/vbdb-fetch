import requests
from bs4 import BeautifulSoup
import logging
import sys
from datetime import datetime, timedelta
import re
from pathlib import Path
import json

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

# Define season metadata for Women's NCAA Volleyball
women_meta_link_content = [
    {"year": "2024", "season_id": "18323", "division": "di"},
    {"year": "2024", "season_id": "18324", "division": "dii"},
    {"year": "2024", "season_id": "18325", "division": "diii"},
    #     {'year': '2023', 'season_id': '18200', 'division': 'di'},
    #     {'year': '2023', 'season_id': '18201', 'division': 'dii'},
    #     {'year': '2023', 'season_id': '18202', 'division': 'diii'},
    #     {'year': '2022', 'season_id': '17900', 'division': 'di'},
    #     {'year': '2022', 'season_id': '17901', 'division': 'dii'},
    #     {'year': '2022', 'season_id': '17905', 'division': 'diii'},
    #     {'year': '2021', 'season_id': '17720', 'division': 'di'},
    #     {'year': '2021', 'season_id': '17723', 'division': 'dii'},
    #     {'year': '2021', 'season_id': '17725', 'division': 'diii'}
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
        "team_1_id": "",
        "team_2_id": "",
        "team_1_name": "",
        "team_2_name": "",
        "attendance": "",
        "location": "",
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

    # Get team information
    team_cells = top_tbl.find_all(
        "td", attrs={"class": "grey_text d-none d-sm-table-cell"}
    )

    # Get team images - these contain the team IDs
    imgs = top_tbl.find_all("img", class_="large_logo_image")
    img_count = len(imgs)

    # Extract team 1 information
    if img_count > 0:
        match_data["team_1_id"] = imgs[0]["src"].split(".gif")[0].split("sm//")[-1]

    if len(team_cells) > 0:
        team1_link = team_cells[0].find("a")
        if team1_link:
            match_data["team_1_name"] = team1_link.text.strip()
        else:
            match_data["team_1_name"] = team_cells[0].text.strip()

    # Extract team 2 information
    if img_count > 1:
        match_data["team_2_id"] = imgs[1]["src"].split(".gif")[0].split("sm//")[-1]

    if len(team_cells) > 1:
        team2_link = team_cells[1].find("a")
        if team2_link:
            match_data["team_2_name"] = team2_link.text.strip()
        else:
            match_data["team_2_name"] = team_cells[1].text.strip()
    elif top_tbl.find_all(
        "td",
        text=lambda text: text
        and not isinstance(text, str)
        and not text.has_attr("class"),
    ):
        # For cases where the second team has no image and a different HTML structure
        plain_team_name = [
            td
            for td in top_tbl.find_all("td")
            if td.get_text().strip() and not td.has_attr("class")
        ]
        if plain_team_name:
            match_data["team_2_name"] = plain_team_name[0].get_text().strip()

    # Get score information
    score_cells = top_tbl.find_all(
        "td", attrs={"style": lambda x: x and "font-size:36px" in x}
    )
    if len(score_cells) >= 2:
        team1_score = score_cells[0].text.strip()
        team2_score = score_cells[1].text.strip()

        # Extract set scores from the nested table
        score_table = top_tbl.find("table", style="border-collapse: collapse")
        if score_table:
            rows = score_table.find_all("tr")
            if len(rows) >= 3:  # Header row + 2 team rows
                team1_row = rows[1]
                team2_row = rows[2]

                # Get all set scores (excluding the team name and final score)
                team1_set_scores = [
                    td.text.strip()
                    for td in team1_row.find_all("td", class_="grey_text")
                ]
                team2_set_scores = [
                    td.text.strip()
                    for td in team2_row.find_all("td", class_="grey_text")
                ]

                # Format set scores as requested
                set_scores = []
                for i in range(len(team1_set_scores)):
                    if i < len(team2_set_scores):
                        set_scores.append(
                            f"{team1_set_scores[i]}-{team2_set_scores[i]}"
                        )

                match_data["score"] = (
                    f"{team1_score}-{team2_score} [{', '.join(set_scores)}]"
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

    return match_data


def fetch_ncaa_schedules(year="2022", date_range=None):
    """
    Fetch NCAA volleyball schedules for the specified year, and date range

    Args:
        year: Year to fetch data for
        date_range: Optional tuple of (start_date, end_date) as strings in MM/DD/YYYY format

    Returns:
        List of dictionaries with schedule data
    """
    logger.info(f"Fetching NCAA Women's volleyball schedules for {year}")
    
    division_roman_map = {
        "di": "I",
        "dii": "II",
        "diii": "III"
    }

    # Load metadata
    meta_links = women_meta_link_content

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
        # Default to current season (August 15 to December 23)
        start_date = datetime.strptime(f"08/15/{year}", "%m/%d/%Y")
        end_date = datetime.strptime(f"12/23/{year}", "%m/%d/%Y")

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

                # Determine home and away teams
                # In NCAA box scores, team_1 is typically the home team
                match_data["home_team_name"] = match_data.pop("team_1_name", "")
                match_data["away_team_name"] = match_data.pop("team_2_name", "")
                match_data["home_team_id"] = match_data.pop("team_1_id", "")
                match_data["away_team_id"] = match_data.pop("team_2_id", "")

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

    logger.info(f"Processed {len(all_matches)} NCAA Women's matches for {year}")
    return all_matches


def save_to_json(data, filename):
    """
    Save data to a JSON file
    
    Args:
        data: Data to save
        filename: Path to save the file
    """
    try:
        # Create directory if it doesn't exist
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Data successfully saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")
        return False


def main():
    """
    Main function to fetch NCAA schedules and save to JSON
    """
    start_date = "08/15/2024"
    end_date = "12/24/2024"
    year = '2024'

    # Create output directory
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Define output filename with year and date range
    output_filename = output_dir / f"ncaa_volleyball_schedules_{year}.json"
    
    # Fetch schedule data
    schedule_data = fetch_ncaa_schedules(year, (start_date, end_date))
    
    # Save data to JSON file
    if schedule_data:
        save_to_json(schedule_data, output_filename)
        print(f"Fetched and processed {len(schedule_data)} NCAA matches")
        print(f"Data saved to {output_filename}")
    else:
        print("No data was fetched. Check logs for errors.")


if __name__ == "__main__":
    main()