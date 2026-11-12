from fastapi.testclient import TestClient

from app.main import app
from app.store import STORE

client = TestClient(app)


def setup_function() -> None:
    STORE.reset()


def test_health() -> None:
    assert client.get("/health").json() == {"ok": True}


def test_add_score_accumulates() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    r = client.post("/scores", json={"name": "ana", "points": 5})
    assert r.json() == {"name": "ana", "total": 15}


def test_leaderboard_sorted() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    top = client.get("/leaderboard").json()
    assert top[0] == {"name": "leo", "points": 30}


def test_reading_a_total_does_not_add_a_player() -> None:
    assert STORE.total("ghost") == 0
    assert client.get("/leaderboard").json() == []


def test_stats_empty_store() -> None:
    r = client.get("/stats")
    assert r.status_code == 200
    assert r.json() == {"players": 0, "average": 0.0}
    assert isinstance(r.json()["average"], float)


def test_stats_happy_path() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    r = client.get("/stats")
    assert r.status_code == 200
    assert r.json() == {"players": 2, "average": 20.0}


def test_stats_uses_per_player_totals() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "ana", "points": 5})
    client.post("/scores", json={"name": "leo", "points": 30})
    assert client.get("/stats").json() == {"players": 2, "average": 22.5}


def test_stats_does_not_create_players() -> None:
    first = client.get("/stats").json()
    assert client.get("/stats").json() == first
    assert client.get("/leaderboard").json() == []


def test_stats_ignores_unknown_query_param() -> None:
    assert client.get("/stats?x=1").status_code == 200


def test_rejects_bad_input() -> None:
    assert client.post("/scores", json={"name": "", "points": 10}).status_code == 422
    assert client.get("/leaderboard?limit=0").status_code == 422
