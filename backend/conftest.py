# backend/conftest.py
import pytest
from app.data_loader import load_players, get_player

@pytest.fixture(autouse=True, scope="session")
def setup():
    load_players()

@pytest.fixture(scope="session")
def strong_team(setup):
    # Mbappé, Bellingham, Vinicius Jr
    return [get_player(231747), get_player(237692), get_player(238794)]

@pytest.fixture(scope="session")
def weak_team(setup):
    # Three solid but not elite players
    return [get_player(192985), get_player(188545), get_player(212198)]
