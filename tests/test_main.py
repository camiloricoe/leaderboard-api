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


def test_rejects_bad_input() -> None:
    assert client.post("/scores", json={"name": "", "points": 10}).status_code == 422
    assert client.get("/leaderboard?limit=0").status_code == 422


def test_get_score_happy_path() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "ana", "points": 5})
    r = client.get("/scores/ana")
    assert r.status_code == 200
    assert r.json() == {"name": "ana", "total": 15}


def test_get_score_empty_store_is_404() -> None:
    r = client.get("/scores/ana")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_get_score_unknown_player_is_404() -> None:
    client.post("/scores", json={"name": "bob", "points": 3})
    assert client.get("/scores/ana").status_code == 404


def test_get_score_does_not_create_player() -> None:
    assert client.get("/scores/ana").status_code == 404
    assert client.get("/leaderboard").json() == []


def test_get_score_zero_points_player_exists() -> None:
    client.post("/scores", json={"name": "ana", "points": 0})
    r = client.get("/scores/ana")
    assert r.status_code == 200
    assert r.json() == {"name": "ana", "total": 0}


def test_get_score_name_too_long_is_422() -> None:
    assert client.get("/scores/" + "a" * 41).status_code == 422


def test_get_score_name_boundary_40_chars() -> None:
    name = "a" * 40
    client.post("/scores", json={"name": name, "points": 7})
    r = client.get("/scores/" + name)
    assert r.status_code == 200
    assert r.json() == {"name": name, "total": 7}
