from dataclasses import dataclass

@dataclass
class PossessionChange:
    phase: int
    zone: str
    player: str # name of player who won/lost the ball
    method: str # interception, tackle, error, out of play
    team: int # 0 or 1
    event_type: str = "possession_change"
    
@dataclass
class PassAttempt:
    phase: int
    zone: str
    passer: str
    target: str
    pass_type: str # short, long, through ball, switch
    success: bool
    event_type: str = "pass"

@dataclass
class DribbleAttempt:
    phase: int
    zone: str
    dribbler: str
    defender: str
    success: bool # did dribbler get past
    foul: bool # did defender commit a foul? (leads to set piece)
    event_type: str = "dribble"

@dataclass
class ShotAttempt:
    phase: int
    zone: str
    shooter: str
    shot_type: str # finesse, power, header, volley, long shot
    quality: float # the xG-like value (0.0-1.0)
    outcome: str # goal, save, block, miss
    assister: str | None # who created the chance for shot attempt
    event_type: str = "shot"

@dataclass
class SetPiece:
    phase: int
    zone: str
    taker: str
    piece_type: str # free kick, corner
    outcome: str # goal, save, cleared, short
    event_type: str = "set_piece"

@dataclass
class PhysicalDuel:
    phase: int
    zone: str
    player_a: str
    player_b: str
    winner: str
    event_type: str = "duel"

@dataclass
class SpecialEvent:
    phase: int
    zone: str
    player: str
    special_type: str # brilliance, error
    description: str
    resulted_in_goal: bool
    event_type: str = "special"


GameEvent = PossessionChange | PassAttempt | DribbleAttempt | ShotAttempt | SetPiece | PhysicalDuel | SpecialEvent

