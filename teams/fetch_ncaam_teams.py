

from typing import List, Dict, Any

import pandas as pd
from pathlib import Path
data_dir = Path(__file__).parent.parent / "data"
img_csv_path = data_dir / "ncaa_schools_imgs.csv"
img_conf_path = data_dir / "conference_short_mapping_m.csv"

def fetch_ncaam_teams() -> List[Dict[str, Any]]:
    # Get team code and short name
    df_team_codes = (
        pd.read_html("https://stats.ncaa.org/game_upload/team_codes")[0]
        .iloc[2:]
        .rename(columns={0: "orgId", 1: "name_short"})
    )
    df_team_codes["orgId"] = df_team_codes["orgId"].astype(str)

    # Men fetch
    men_df_json = pd.read_json(
        "https://web3.ncaa.org/directory/api/directory/memberList?type=12&sportCode=MVB"
    )[["orgId", "nameOfficial", "athleticWebUrl", "divisionRoman", "conferenceName"]].rename(columns={'conferenceName': 'conference'})
    men_df_json["gender"] = "M"
    men_df_json["orgId"] = men_df_json["orgId"].astype(str)
    men_df_json['level'] = 'NCAA M'

    # Read image df
    img_df = pd.read_csv(str(img_csv_path))[["orgId", "img", "nameOfficial"]]
    img_df["orgId"] = img_df["orgId"].astype(str)

    # Read conf df
    conf_m = pd.read_csv(str(img_conf_path))

    # Combine
    df = (pd.merge(
    pd.merge(
        pd.merge(
            men_df_json,
            df_team_codes,
            left_on="orgId",
            right_on="orgId",
            how="left",
        ),
        img_df,
    ),conf_m)
    .rename(
        columns={
            "orgId": "team_id",
            "nameOfficial": "name",
            "athleticWebUrl": "url",
            "divisionRoman": "division",
        }
    ))
    
    return df[['team_id', 'name', 'name_short', 'img', 'url', 'division', 'conference', 'level', 'conference_short']].to_dict(orient='records')
