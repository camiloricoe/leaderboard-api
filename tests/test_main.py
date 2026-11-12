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


def test_delete_removes_player() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    r = client.delete("/scores/ana")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get("/leaderboard").json() == [{"name": "leo", "points": 30}]


def test_delete_empty_store_is_404() -> None:
    r = client.delete("/scores/ghost")
    assert r.status_code == 404
    assert "detail" in r.json()
    assert client.get("/leaderboard").json() == []


def test_delete_unknown_player_is_404() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    assert client.delete("/scores/bob").status_code == 404
    assert client.get("/leaderboard").json() == [{"name": "ana", "points": 10}]


def test_delete_twice_is_404() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    assert client.delete("/scores/ana").status_code == 204
    assert client.delete("/scores/ana").status_code == 404


def test_delete_invalid_name_is_422() -> None:
    assert client.delete("/scores/" + "x" * 41).status_code == 422


def test_delete_name_limit_boundary() -> None:
    name = "x" * 40
    client.post("/scores", json={"name": name, "points": 1})
    assert client.delete("/scores/" + name).status_code == 204


def test_delete_then_repost_starts_from_zero() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.delete("/scores/ana")
    r = client.post("/scores", json={"name": "ana", "points": 5})
    assert r.json() == {"name": "ana", "total": 5}


def test_delete_zero_point_player() -> None:
    client.post("/scores", json={"name": "ana", "points": 0})
    assert client.delete("/scores/ana").status_code == 204


def test_rejects_bad_input() -> None:
    assert client.post("/scores", json={"name": "", "points": 10}).status_code == 422
    assert client.get("/leaderboard?limit=0").status_code == 422
