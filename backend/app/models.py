from pydantic import BaseModel, Field, field_validator


class MatchRequest(BaseModel):
    team_a: list[int | str] = Field(min_length=3, max_length=3)
    team_b: list[int | str] = Field(min_length=3, max_length=3)

    @field_validator('team_a', 'team_b')
    @classmethod
    def _only_random_str(cls, v: list[int | str]) -> list[int | str]:
        for entry in v:
            if isinstance(entry, str) and entry != 'random':
                raise ValueError("string entries must be 'random'")
        return v

class PlayerSummary(BaseModel):
    player_id: int 
    name: str
    image: str
    overall_rating: str
    club_name: str
    country_name: str
    positions: list[str]

class PlayerListResponse(BaseModel):
    items: list[PlayerSummary]
    total: int
    page: int 
    page_size: int

class PlayerDetail(BaseModel):
    player_id: int
    name: str
    full_name: str
    image: str
    country_name: str 
    club_name: str 
    positions: list[str]
    overall_rating: int
    pace: dict[str, int]
    shooting: dict[str, int]
    passing: dict[str, int]
    dribbling: dict[str, int]
    defending: dict[str, int]
    physical: dict[str, int]


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


