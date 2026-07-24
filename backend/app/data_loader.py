
import pandas as pd
import random
from app.player_profile import PlayerProfile
from typing import List

FILE_PATH = 'data/FC26_20250921.csv'

INT_FIELDS = [
    'player_id', 'height_cm', 'weight_kg', 'overall_rating', 'potential', 'value', 'wage', 'weak_foot', 'skill_moves', 'international_reputation',
    'club_kit_number', 'country_kit_number', 'crossing', 'finishing', 'heading_accuracy', 'short_passing', 'volleys',
    'dribbling', 'curve', 'fk_accuracy', 'long_passing', 'ball_control', 'acceleration', 'sprint_speed', 'agility', 'reactions', 'balance',
    'shot_power', 'jumping', 'stamina', 'strength', 'long_shots', 'aggression', 'interceptions', 'vision', 'penalties', 'composure',
    'attack_position', 'defensive_awareness', 'standing_tackle', 'sliding_tackle', 'gk_diving', 'gk_handling', 'gk_kicking', 'gk_positioning', 'gk_reflexes',
]

COLUMN_MAP = {
    "player_id": "player_id",
    "short_name": "name",
    "long_name": "full_name",
    "player_face_url": "image",
    "height_cm": "height_cm",
    "weight_kg": "weight_kg",
    "dob": "dob",
    "player_positions": "positions",
    "overall": "overall_rating",
    "potential": "potential",
    "preferred_foot": "preferred_foot",
    "weak_foot": "weak_foot",
    "skill_moves": "skill_moves",
    "international_reputation": "international_reputation",
    "body_type": "body_type",

    # Club info
    "club_name": "club_name",
    "league_name": "club_league_name",
    "club_position": "club_position",
    "club_jersey_number": "club_kit_number",

    # Country info
    "nationality_name": "country_name",
    "nation_position": "country_position",
    "nation_jersey_number": "country_kit_number",

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
    "mentality_positioning": "attack_position",

    # Defending
    "defending_marking_awareness": "defensive_awareness",
    "defending_standing_tackle": "standing_tackle",
    "defending_sliding_tackle": "sliding_tackle",

    # Goalkeeping
    "goalkeeping_diving": "gk_diving",
    "goalkeeping_handling": "gk_handling",
    "goalkeeping_kicking": "gk_kicking",
    "goalkeeping_positioning": "gk_positioning",
    "goalkeeping_reflexes": "gk_reflexes",

    # Meta
    "player_tags": "specialities",
    "player_traits": "play_styles",
    "value_eur": "value",
    "wage_eur": "wage",
}

_players = {}

def parse_list(value, strip_hash=False, strip_plus=False) -> list[str]:
    if not isinstance(value, str):
        return []
    items = [item.strip() for item in value.split(',')]
    if strip_hash:
        items = [item.lstrip('#') for item in items]
    if strip_plus:
        items = [item.rstrip(' +') for item in items]
    return items

def _row_to_player(row: pd.Series) -> PlayerProfile:
    """Converts a pandas row to a PlayerProfile object."""
    player_data = {}
    for sofifa_key, field_name in COLUMN_MAP.items():
        value = row[sofifa_key]
        if field_name in INT_FIELDS:
            try:
                value = int(float(value)) if pd.notna(value) and str(value).strip() != '' else 0
            except (ValueError, TypeError):
                value = 0
        elif field_name == 'positions':
            value = parse_list(value)
        elif field_name == 'specialities':
            value = parse_list(value, strip_hash=True)
        elif field_name == 'play_styles':
            value = parse_list(value, strip_plus=True)
        elif isinstance(value, float) and pd.isna(value):
            value = ""
        player_data[field_name] = value
        
    # Normalizing skill moves field
    player_data['skill_moves'] = player_data['skill_moves'] * 20
    return PlayerProfile(**player_data)


def load_players(path: str=FILE_PATH) -> dict[int, PlayerProfile]:
    if not path:
        path = FILE_PATH
    df = pd.read_csv(path, low_memory=False)
    for index, row in df.iterrows():
        try:
            profile = _row_to_player(row)
            _players[profile.player_id] = profile
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue
    return _players

def get_player(player_id: int, path: str=FILE_PATH) -> PlayerProfile:
    if player_id not in _players:
        raise ValueError(f"Player with id {player_id} not found.")

    return _players.get(player_id)


def get_all_players(path: str=FILE_PATH) -> List[PlayerProfile]:
    if _players:
        return list(_players.values())
    else:
        load_players(path)
        return list(_players.values())
    
def search_players(query: str) -> List[PlayerProfile]:
    q = query.lower()
    matches = [player for player in _players.values() 
               if q in player.name.lower()
               or (isinstance(player.club_name, str) and q in player.club_name.lower())
               or (isinstance(player.country_name, str) and q in player.country_name.lower())
               ]
    return matches

def get_random_players(n: int = 3) -> List[PlayerProfile]:
    if _players:
        return random.sample(list(_players.values()), k=n)