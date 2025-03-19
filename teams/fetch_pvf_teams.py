import requests
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_pvf_teams():
    """
    Fetch Pro Volleyball Federation teams.
    
    Returns:
        list: List of PVF team dictionaries
    """
    logger.info("Fetching PVF teams...")
    
    try:
        # Fetch JSON data
        url = "https://provolleyball.com/api/teams?include&sort%5B0%5D=sort&sort%5B1%5D=name"
        response = requests.get(url)
        response.raise_for_status()
        teams_json = response.json().get('data', [])
        
        # Process each team entry
        teams = []
        for team in teams_json:
            team_id = team.get("slug", "")
            name = team.get("name", '')
            img = team.get("featured_banner_image", {}).get("src", "")
            #current_roster_id = team.get('current_roster_id', '')
            #current_season_id = team.get("current_season_id", '')
            url = team.get("permalink", '')
            
            teams.append({
                'team_id': team_id,
                'name': name,
                'name_short': team_id,
                'img': img,
                #'current_roster_id': current_roster_id,
                #'current_season_id': current_season_id,
                'url': "https://provolleyball.com" + url,
                'division': 'Pro Women',
                'conference': 'PVF',
                'level': 'Pro',
                'conference_short': 'pro'
            })
            
        teams_to_remove = ['Dallas Team', 'Team Collier', 'Team Shondell', 'Kansas City']

        # New image URLs for specific teams
        image_updates = {
            'Atlanta Vibe': 'https://provolleyball.com/imgproxy/2GZgtgfNWw2chjNPpcVCUF7fV9uxge23mL1mkSJMPs4/rs:fit:2000:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyMy8xMC8xNi8wZTA5NDIxMC1kZTc0LTQ2NjEtOWZkMS1iMzE1YzZkNmNjYmQucG5n.png',
            'Columbus Fury': 'https://provolleyball.com/imgproxy/XQDp1AoZT1R8ptzTTRirUYe_pahz-0ouEEYodr98_jk/rs:fit:1200:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyNC8wMi8xMy83MzM2NzU1NC0wOGRhLTQ5MWEtOWYzNC00ZjFiMjkwNzc3MTIucG5n.png',
            'Grand Rapids Rise': 'https://provolleyball.com/imgproxy/Irfvk-mphkux4FUquretSCe9nsnAVjhxPsV4EmZ4dhM/rs:fit:1200:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyMy8xMi8xNC82ZDMxYjIxZS1kNGYxLTQ3MWMtOTI0OS1iYzBkOGFkYzJhMmEucG5n.png',
            'Indy Ignite': 'https://provolleyball.com/imgproxy/a4i1u6Y3QD4kBQNnWp4_6TTaxWL1-K-hKMsamRdfXU8/rs:fit:1200:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyNC8wNi8xMS9jMDk2MjRkYS0yOWM2LTRjNjQtOGUzOC0zNWMwYWEzOTcwMWQud2VicA.webp',
            'Omaha Supernovas': 'https://provolleyball.com/imgproxy/VHOKO7ucv3wcLbqSZQ4TUL8QTZ0pYUEaTNKgRjzMTMo/rs:fit:1200:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyNC8wMi8yMy9kZTA4NGQ1Yy04MDExLTQyMDktOTc2Ni02MjVhZjExYWZjY2EucG5n.png',
            'Orlando Valkyries': 'https://provolleyball.com/imgproxy/DY9GotrQGEDAj_zyS91egcAUGg6dAS6ZgTc5m1mVBLc/rs:fit:1200:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyMy8xMC8xNi83NTJjZTk5MC0wMTE5LTQ3MDAtOTFjZi1mNjJmNGQxYmRjYzIucG5n.png',
            'San Diego Mojo': 'https://storage.googleapis.com/provolleyball-prod/upload/2024/10/25/f683092e-3a8a-48e1-ae57-fe9d0acb287a.gif',
            'Vegas Thrill': 'https://provolleyball.com/imgproxy/YD9xIuMCP74IIGg25RouNto7VIppHdWA0SZH_QflEeM/rs:fit:1200:0:0/g:ce/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3Byb3ZvbGxleWJhbGwtcHJvZC91cGxvYWQvMjAyMy8xMS8yMi8yNTM3ZDFmMC1iMjgwLTQ0ZjctOWExNC1lNzhlY2RmODRlYWQucG5n.png'
        }

        # Remove specified teams
        pvf_teams = [team for team in teams if team['name'] not in teams_to_remove]
        # Define season ID to year mapping
        # season_id_year_map = {1: "2024", 3: "2025"}
        
        # Update image URLs and add season year
        for team in pvf_teams:
            # Update image if team is in image_updates dictionary
            if team['name'] in image_updates:
                team['img'] = image_updates[team['name']]
            
            # Add season year based on current_season_id
            # if team['current_season_id'] is not None and team['current_season_id'] in season_id_year_map:
                    # team['season_year'] = season_id_year_map[team['current_season_id']]
        
        logger.info(f"Found {len(teams)} PVF teams")
        return pvf_teams
        
    except requests.RequestException as e:
        logger.error(f"Error fetching PVF teams: {e}")
        return []
