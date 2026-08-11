from fastapi.testclient import TestClient

from app.main import app
from app.data_loader import get_all_players

client = TestClient(app)


def _total():
    return len(get_all_players())


def test_list_players_default():
    r = client.get("/players")
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == _total()
    assert len(body["items"]) == min(20, _total())


def test_list_players_summary_shape():
    r = client.get("/players", params={"page_size": 1})
    item = r.json()["items"][0]
    assert set(item.keys()) == {
        "player_id", "name", "image", "overall_rating",
        "club_name", "country_name", "positions",
    }
    assert isinstance(item["overall_rating"], int)


def test_page_size_respected():
    total = _total()
    r = client.get("/players", params={"page": 1, "page_size": 5})
    body = r.json()
    assert body["page_size"] == 5
    assert len(body["items"]) == min(5, total)


def test_page_size_clamped_to_max_100():
    r = client.get("/players", params={"page_size": 500})
    body = r.json()
    assert body["page_size"] == 100
    assert len(body["items"]) <= 100


def test_page_size_floored_to_1():
    r = client.get("/players", params={"page_size": 0})
    body = r.json()
    assert body["page_size"] == 1
    assert len(body["items"]) <= 1


def test_page_floored_to_1():
    r = client.get("/players", params={"page": -5})
    assert r.json()["page"] == 1


def test_high_page_returns_empty_with_correct_total():
    total = _total()
    r = client.get("/players", params={"page": total + 100, "page_size": 10})
    body = r.json()
    assert body["items"] == []
    assert body["total"] == total


def test_query_filter_narrows_and_matches():
    total = _total()
    r = client.get("/players", params={"query": "mbappé", "page_size": 100})
    body = r.json()
    assert 0 < body["total"] <= total
    for item in body["items"]:
        hay = " ".join([
            item["name"].lower(),
            (item["club_name"] or "").lower(),
            (item["country_name"] or "").lower(),
        ])
        assert "mbappé" in hay


def test_position_filter():
    r = client.get("/players", params={"position": "ST", "page_size": 100})
    body = r.json()
    assert body["total"] > 0
    for item in body["items"]:
        assert "ST" in item["positions"]


def test_rating_range_filter():
    r = client.get("/players", params={"min_rating": 88, "max_rating": 90, "page_size": 100})
    body = r.json()
    assert body["total"] > 0
    for item in body["items"]:
        assert 88 <= item["overall_rating"] <= 90


def test_filter_reduces_total():
    unfiltered = client.get("/players").json()["total"]
    filtered = client.get("/players", params={"min_rating": 90}).json()["total"]
    assert filtered < unfiltered


# ---------- GET /players/{player_id} (detail) ----------

MBAPPE = 231747


def test_player_detail_returns_all_curated_groups():
    r = client.get(f"/players/{MBAPPE}")
    assert r.status_code == 200
    body = r.json()
    assert body["player_id"] == MBAPPE
    assert isinstance(body["overall_rating"], int)
    for group in ("pace", "shooting", "passing", "dribbling", "defending", "physical"):
        assert group in body
        assert len(body[group]) > 0
        assert all(isinstance(v, int) for v in body[group].values())


def test_player_detail_not_found_returns_404():
    r = client.get("/players/9999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Player not found"


# ---------- POST /simulate ----------

TEAM_A = [231747, 237692, 238794]
TEAM_B = [192985, 188545, 212198]


def _assert_valid_match_response(body):
    for key in ("events", "final_score", "winner", "mvp", "team_a_names", "team_b_names"):
        assert key in body
    assert isinstance(body["events"], list)
    assert len(body["final_score"]) == 2
    assert len(body["team_a_names"]) == 3
    assert len(body["team_b_names"]) == 3


def test_simulate_all_explicit_returns_match():
    r = client.post("/simulate", json={"team_a": TEAM_A, "team_b": TEAM_B})
    assert r.status_code == 200
    _assert_valid_match_response(r.json())


def test_simulate_with_random_markers():
    r = client.post("/simulate", json={
        "team_a": [231747, "random", 237692],
        "team_b": ["random", 188545, "random"],
    })
    assert r.status_code == 200
    _assert_valid_match_response(r.json())


def test_simulate_all_random_yields_full_teams():
    r = client.post("/simulate", json={
        "team_a": ["random", "random", "random"],
        "team_b": ["random", "random", "random"],
    })
    assert r.status_code == 200
    body = r.json()
    _assert_valid_match_response(body)
    assert len(body["team_a_names"] + body["team_b_names"]) == 6


def test_simulate_duplicate_explicit_returns_400():
    r = client.post("/simulate", json={
        "team_a": [231747, 231747, 238794],
        "team_b": TEAM_B,
    })
    assert r.status_code == 400


def test_simulate_invalid_id_returns_404_naming_id():
    r = client.post("/simulate", json={
        "team_a": [9999999, 237692, 238794],
        "team_b": TEAM_B,
    })
    assert r.status_code == 404
    assert "9999999" in r.json()["detail"]
