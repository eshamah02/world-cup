
import pandas as pd
from player_profile import PlayerProfile

FILE_PATH = 'data/fc26_sofifa_player_stats.csv'

COLUMN_MAP = {
    "player_id": "player_id",
    "name": "name",
    "full_name": "full_name",
    "image": "image",
    "height_cm": "height_cm",
    "weight_kg": "weight_kg",
    "dob": "dob",
    "positions": "positions",
    "overall_rating": "overall_rating",
    "potential": "potential",
    "preferred_foot": "preferred_foot",
    "weak_foot": "weak_foot",
    "skill_moves": "skill_moves",
    "international_reputation": "international_reputation",
    "body_type": "body_type",

    # Club info
    "club_name": "club_name",
    "club_league_name": "club_league_name",
    "club_position": "club_position",
    "club_kit_number": "club_kit_number",

    # Country info
    "country_name": "country_name",
    "country_position": "country_position",
    "country_kit_number": "country_kit_number",

    # Attacking
    "attacking_crossing": "crossing",
    "attacking_finishing": "finishing",
    "attacking_heading_accuracy": "heading_accuracy",
    "attacking_short_passing": "short_passing",
    "attacking_volleys": "volleys",

    # Skill
    "skill_dribbling": "dribbling",
    "skill_curve": "curve",
    "skill_fk_accuracy": "fk_accuracy",
    "skill_long_passing": "long_passing",
    "skill_ball_control": "ball_control",

    # Movement
    "movement_acceleration": "acceleration",
    "movement_sprint_speed": "sprint_speed",
    "movement_agility": "agility",
    "movement_reactions": "reactions",
    "movement_balance": "balance",

    # Power
    "power_shot_power": "shot_power",
    "power_jumping": "jumping",
    "power_stamina": "stamina",
    "power_strength": "strength",
    "power_long_shots": "long_shots",

    # Mentality
    "mentality_aggression": "aggression",
    "mentality_interceptions": "interceptions",
    "mentality_vision": "vision",
    "mentality_penalties": "penalties",
    "mentality_composure": "composure",
    "mentality_attack_position": "attack_position",

    # Defending
    "defending_defensive_awareness": "defensive_awareness",
    "defending_standing_tackle": "standing_tackle",
    "defending_sliding_tackle": "sliding_tackle",

    # Goalkeeping
    "goalkeeping_gk_diving": "gk_diving",
    "goalkeeping_gk_handling": "gk_handling",
    "goalkeeping_gk_kicking": "gk_kicking",
    "goalkeeping_gk_positioning": "gk_positioning",
    "goalkeeping_gk_reflexes": "gk_reflexes",

    # Meta
    "specialities": "specialities",
    "play_styles": "play_styles",
    "value": "value",
    "wage": "wage",
}

_players = {}

def parse_list(value, strip_hash=False) -> list[str]:
    if not isinstance(value, str):
        return []
    if strip_hash:
        value = value.lstrip('#')
    return [item.strip() for item in value.split(',') if item.strip()]

def load_from_path(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df = _clean(df)
    print(df.head())
    return df

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    # Remove rows with missing required columns
    df = df.dropna(subset=REQUIRED_COLUMNS)

    # Convert numeric columns to numeric type
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0, inplace=True)

    # Remove rows with invalid data (e.g., negative minutes played)
    df = df[df['minutes_played'] >= 0]

    # Turn match_date column into datetime type
    df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')

    return df


load_from_path(FILE_PATH)