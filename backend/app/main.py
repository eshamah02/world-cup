
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data_loader import load_players, get_player, search_players, get_all_players
from models import MatchRequest, MatchResponse, MatchEvent, PlayerSummary
from simulation.engine import simulate_match

from dataclasses import asdict
from contextlib import asynccontextmanager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_players()
    yield

app = FastAPI(title='World-Cup', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
))


@app.get("/players/search")
def search(query: str) -> list[PlayerSummary]:
    res = search_players(query)
    
    if res is None:
        raise HTTPException(status_code=404, detail="No players found")
    
    player_summaries = []
    for player in res:
        summary = PlayerSummary(
            player_id=player.player_id,
            name=player.name,
            image=player.image,
            overall_rating=str(player.overall_rating),
            club_name=player.club_name,
            country_name=player.country_name,
            positions=player.positions
        )
        player_summaries.append(summary)
    return player_summaries


@app.get("/players/{player_id}")
def get_player_profile(player_id: int) -> PlayerSummary:
    res = get_player(player_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return asdict(res)

@app.get("/simulate")
def simulate(request: MatchRequest) -> MatchResponse:
    all_players = request.team_a.extend(request.team_b)
    if len(all_players) != len(set(all_players)):
        raise HTTPException(status_code=400, detail="Duplicate players in teams")

    res = simulate_match(request.team_a, request.team_b)
    
    # TODO: build MatchResponse from result, return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")