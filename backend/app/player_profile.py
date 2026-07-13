from dataclasses import dataclass


@dataclass
class PlayerProfile:
    # Identity
    player_id: int
    name: str
    full_name: str
    image: str
    height_cm: int
    weight_kg: int
    dob: str
    positions: list[str]
    overall_rating: int
    potential: int
    preferred_foot: str
    weak_foot: int
    skill_moves: int
    international_reputation: int
    body_type: str

    # Club info
    club_name: str
    club_league_name: str
    club_position: str
    club_kit_number: int

    # Country info
    country_name: str
    country_position: str
    country_kit_number: int

    # Attacking
    crossing: int
    finishing: int
    heading_accuracy: int
    short_passing: int
    volleys: int

    # Skill
    dribbling: int
    curve: int
    fk_accuracy: int
    long_passing: int
    ball_control: int

    # Movement
    acceleration: int
    sprint_speed: int
    agility: int
    reactions: int
    balance: int

    # Power
    shot_power: int
    jumping: int
    stamina: int
    strength: int
    long_shots: int

    # Mentality
    aggression: int
    interceptions: int
    vision: int
    penalties: int
    composure: int
    attack_position: int

    # Defending
    defensive_awareness: int
    standing_tackle: int
    sliding_tackle: int

    # Goalkeeping
    gk_diving: int
    gk_handling: int
    gk_kicking: int
    gk_positioning: int
    gk_reflexes: int

    # Meta
    specialities: list[str]
    play_styles: list[str]
    value: int
    wage: int



