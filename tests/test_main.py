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


def _post(name: str, points: int) -> None:
    client.post("/scores", json={"name": name, "points": points})


def test_rank_happy_path() -> None:
    _post("alice", 50)
    _post("bob", 30)
    r = client.get("/rank/alice")
    assert r.status_code == 200
    assert r.json() == {"name": "alice", "rank": 1, "total": 50}
    assert client.get("/rank/bob").json() == {"name": "bob", "rank": 2, "total": 30}


def test_rank_follows_accumulated_total() -> None:
    _post("alice", 20)
    _post("bob", 30)
    _post("alice", 20)
    assert client.get("/rank/alice").json() == {"name": "alice", "rank": 1, "total": 40}
    assert client.get("/rank/bob").json()["rank"] == 2


def test_rank_ties_share_rank() -> None:
    _post("alice", 50)
    _post("bob", 50)
    _post("carol", 10)
    assert client.get("/rank/alice").json()["rank"] == 1
    assert client.get("/rank/bob").json()["rank"] == 1
    assert client.get("/rank/carol").json()["rank"] == 3


def test_rank_empty_store_is_404() -> None:
    r = client.get("/rank/ghost")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_rank_unknown_player_is_404() -> None:
    _post("alice", 5)
    assert client.get("/rank/ghost").status_code == 404


def test_rank_read_does_not_create_player() -> None:
    assert client.get("/rank/ghost").status_code == 404
    assert client.get("/leaderboard").json() == []
    assert client.get("/rank/ghost").status_code == 404


def test_rank_invalid_name_is_422() -> None:
    assert client.get("/rank/" + "x" * 41).status_code == 422


def test_rank_zero_points_player() -> None:
    _post("zed", 0)
    assert client.get("/rank/zed").json() == {"name": "zed", "rank": 1, "total": 0}
