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


def test_top_happy_path() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    client.post("/scores", json={"name": "bo", "points": 20})
    r = client.get("/top")
    assert r.status_code == 200
    assert r.json() == {"name": "leo", "points": 30}


def test_top_sums_totals() -> None:
    client.post("/scores", json={"name": "ana", "points": 20})
    client.post("/scores", json={"name": "ana", "points": 20})
    client.post("/scores", json={"name": "leo", "points": 30})
    assert client.get("/top").json() == {"name": "ana", "points": 40}


def test_top_matches_leaderboard_first() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    assert client.get("/top").json() == client.get("/leaderboard").json()[0]


def test_top_empty_store_is_404() -> None:
    r = client.get("/top")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_top_does_not_create_player() -> None:
    client.get("/top")
    assert client.get("/leaderboard").json() == []


def test_rejects_bad_input() -> None:
    assert client.post("/scores", json={"name": "", "points": 10}).status_code == 422
    assert client.get("/leaderboard?limit=0").status_code == 422
