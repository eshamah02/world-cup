from pydantic import BaseModel, Field

class MatchRequest(BaseModel):
    team_a: list[int] = Field(min_length=3, max_length=3)
    team_b: list[int] = Field(min_length=3, max_length=3)

class PlayerSummary(BaseModel):
    player_id: int 
    name: str
    image: str
    overall_rating: str
    club_name: str
    country_name: str
    positions: list[str]

class MatchEvent(BaseModel):
    phase: int = Field(ge=1, le=32)
    zone: str
    event_type: str
    outcome: str
    text: str
    score: list[int]

class MatchResponse(BaseModel):
    events: list[MatchEvent]
    final_score: list[int]
    winner: str | None
    mvp: str
    team_a_names: list[str]
    team_b_names: list[str]
