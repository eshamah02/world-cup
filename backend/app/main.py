
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.data_loader import load_players, get_player, get_all_players, filter_players, to_summary, to_detail, resolve_random_entries
from app.models import MatchRequest, MatchResponse, MatchEvent, PlayerSummary, PlayerListResponse, PlayerDetail
from app.simulation.engine import simulate_match

from contextlib import asynccontextmanager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_players()
    yield

app = FastAPI(title='World-Cup', version='1.0.0', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/players")
def list_players(
    page: int = 1,
    page_size: int = 20,
    query: str | None = None,
    position: str | None = None,
    country: str | None = None,
    club: str | None = None,
    min_rating: int | None = None,
    max_rating: int | None = None
) -> PlayerListResponse:
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    filtered = filter_players(
        get_all_players(),
        query=query,
        position=position,
        country=country,
        club=club,
        min_rating=min_rating,
        max_rating=max_rating
    )

    total = len(filtered)
    start = (page - 1) * page_size
    window = filtered[start:start + page_size]
    items = [to_summary(p) for p in window]
    return PlayerListResponse(items=items, total=total, page=page, page_size=page_size)

@app.get("/players/{player_id}")
def get_player_profile(player_id: int) -> PlayerDetail:
    try:
        player = get_player(player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found")
    return to_detail(player)


@app.post("/simulate")
def simulate(request: MatchRequest) -> MatchResponse:
    entries = request.team_a + request.team_b 
    explicit = [e for e in entries if e != "random"]

    if len(explicit) != len(set(explicit)):
        raise HTTPException(status_code=400, detail="Duplicate players in teams")

    for pid in explicit:
        try:
            get_player(pid)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Player with id {pid} not found")

    resolved = resolve_random_entries(entries)
    players = [get_player(pid) for pid in resolved]
    return simulate_match(players[:3], players[3:])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")