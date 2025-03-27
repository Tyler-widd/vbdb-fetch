import json
import sqlite3
import os
import re

# Define database paths
db_paths = ["vbdb.db", "../vbdb-api/vbdb.db"]

# Function to extract match_id from URL
def extract_match_id(url):
    if not url:
        return ""
    match = re.search(r'/contests/(\d+)/', url)
    if match:
        return match.group(1)
    return ""

# Load the JSON data once
with open('data/ncaa_volleyball_schedules_2024.json', 'r') as file:
    data = json.load(file)

# Process each database path
for db_path in db_paths:
    # Check if database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        print(f"Directory for {db_path} does not exist. Skipping.")
        continue
    
    # Check if database exists
    db_exists = os.path.exists(db_path)
    if not db_exists:
        print(f"Creating new database: {db_path}")
    else:
        print(f"Using existing database: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop the table if it already exists to recreate with the new column
        cursor.execute("DROP TABLE IF EXISTS ncaaw_results")
        print(f"Dropped existing table in {db_path} if it existed.")
        
        # Create table with match_id column
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS ncaaw_results (
            match_id TEXT,
            date TEXT,
            time TEXT,
            attendance TEXT,
            location TEXT,
            score TEXT,
            box_score TEXT,
            officials TEXT,
            pbp TEXT,
            individual_stats TEXT,
            division TEXT,
            division_roman TEXT,
            year TEXT,
            home_team_name TEXT,
            away_team_name TEXT,
            home_team_id TEXT,
            away_team_id TEXT,
            status TEXT
        )
        '''
        cursor.execute(create_table_sql)
        print(f"Table 'ncaaw_results' created in {db_path} with match_id column.")
        
        # Insert data into the table
        insert_sql = '''
        INSERT INTO ncaaw_results (
            match_id, date, time, attendance, location, score, box_score, officials,
            pbp, individual_stats, division, division_roman, year,
            home_team_name, away_team_name, home_team_id, away_team_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # Insert each record
        for record in data:
            # Extract match_id from box_score URL
            match_id = extract_match_id(record.get('box_score', ''))
            
            values = (
                match_id,
                record.get('date', ''),
                record.get('time', ''),
                record.get('attendance', ''),
                record.get('location', ''),
                record.get('score', ''),
                record.get('box_score', ''),
                record.get('officials', ''),
                record.get('pbp', ''),
                record.get('individual_stats', ''),
                record.get('division', ''),
                record.get('division_roman', ''),
                record.get('year', ''),
                record.get('home_team_name', ''),
                record.get('away_team_name', ''),
                record.get('home_team_id', ''),
                record.get('away_team_id', ''),
                record.get('status', '')
            )
            cursor.execute(insert_sql, values)
        
        # Commit the changes and close the connection
        conn.commit()
        print(f"Successfully imported {len(data)} records into 'ncaaw_results' table in {db_path}.")
        conn.close()
        
    except Exception as e:
        print(f"Error processing database {db_path}: {str(e)}")
        continue

print("Import process completed.")