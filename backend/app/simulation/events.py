from dataclasses import dataclass

@dataclass
class PossessionChange:
    phase: int
    zone: str
    event_type: str = "possession_change"
    player: str # name of player who won/lost the ball
    method: str # interception, tackle, error, out of play
    team: int # 0 or 1

@dataclass
class PassAttempt:
    phase: int
    zone: str
    event_type: str = "pass"
    passer: str
    target: str
    pass_type: str # short, long, through ball, switch
    success: bool

@dataclass
class DribbleAttempt:
    phase: int
    zone: str
    event_type: str = "dribble"
    dribbler: str
    defender: str
    success: bool # did dribbler get past
    foul: bool # did defender commit a foul? (leads to set piece)

@dataclass
class ShotAttempt:
    phase: int
    zone: str
    event_type: str = "shot"
    shooter: str
    shot_type: str # finesse, power, header, volley, long shot
    quality: float # the xG-like value (0.0-1.0)
    outcome: str # goal, save, block, miss
    assister: str | None # who created the chance for shot attempt

@dataclass
class SetPiece:
    phase: int
    zone: str
    event_type: str = "set_piece"
    taker: str
    piece_type: str # free kick, corner
    outcome: str # goal, save, cleared, short

@dataclass
class PhysicalDuel:
    phase: int
    zone: str
    event_type: str = "duel"
    player_a: str
    player_b: str
    winner: str

@dataclass
class SpecialEvent:
    phase: int
    zone: str
    event_type: str = "special"
    player: str
    special_type: str # brilliance, error
    description: str
    resulted_in_goal: bool


GameEvent = PossessionChange | PassAttempt | DribbleAttempt | ShotAttempt | SetPiece | PhysicalDuel | SpecialEvent

