import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import PropOffer, PropProjection
from app.seed import seed


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    seed(db)
    db.close()

    yield TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session_factory):
    with TestClient(app) as test_client:
        yield test_client


def test_markets_endpoint(client):
    response = client.get("/v1/props/markets", params={"sport": "NBA"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["sport"] == "NBA"
    assert payload["markets"] == ["PRA", "Points"]


def test_search_endpoint(client):
    response = client.get("/v1/props/search", params={"query": "LeB", "sport": "NBA"})
    assert response.status_code == 200
    payload = response.json()
    assert "LeBron James" in payload["players"]


def test_top_endpoint_returns_scored_picks(client):
    response = client.get(
        "/v1/props/top",
        params={"sport": "NBA", "market": "PRA", "limit": 3},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3

    top_pick = payload[0]
    assert top_pick["player_name"] == "LeBron James"
    assert top_pick["book"] == "DK"
    assert top_pick["has_edge"] is True
    assert top_pick["score"] >= payload[1]["score"]


def test_top_best_dedupes_players_and_filters_edges(client, db_session_factory):
    db = db_session_factory()
    db.add(
        PropOffer(
            sport="NBA",
            market_group="PRA",
            player_name="Edge Case",
            book="DK",
            line=10.0,
        )
    )
    db.add(
        PropProjection(
            sport="NBA",
            market_group="PRA",
            player_name="Edge Case",
            projection=10.4,
            confidence=90,
        )
    )
    db.commit()
    db.close()

    response = client.get(
        "/v1/props/top_best",
        params={"sport": "NBA", "market": "PRA", "limit": 10},
    )
    assert response.status_code == 200
    payload = response.json()

    player_names = [pick["player_name"] for pick in payload]
    assert len(player_names) == len(set(player_names))
    assert "Edge Case" not in player_names

    top_pick = payload[0]
    assert top_pick["player_name"] == "LeBron James"
    assert top_pick["book"] == "DK"
    assert all(pick["has_edge"] for pick in payload)
