# backend/conftest.py
import pytest
from app.data_loader import load_players

@pytest.fixture(autouse=True, scope="session")
def setup():
    load_players()