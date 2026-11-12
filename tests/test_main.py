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


def _seed() -> None:
    for name, pts in (("alice", 100), ("bob", 50), ("carol", 10)):
        client.post("/scores", json={"name": name, "points": pts})


def test_min_points_filters_inclusive() -> None:
    _seed()
    r = client.get("/leaderboard?min_points=50")
    assert r.status_code == 200
    assert r.json() == [
        {"name": "alice", "points": 100},
        {"name": "bob", "points": 50},
    ]


def test_min_points_default_matches_zero() -> None:
    _seed()
    base = client.get("/leaderboard").json()
    assert base == client.get("/leaderboard?min_points=0").json()
    assert len(base) == 3


def test_min_points_limit_applied_after_filter() -> None:
    _seed()
    r = client.get("/leaderboard?min_points=50&limit=1")
    assert r.json() == [{"name": "alice", "points": 100}]


def test_min_points_empty_store() -> None:
    r = client.get("/leaderboard?min_points=10")
    assert r.status_code == 200
    assert r.json() == []


def test_min_points_above_all_totals() -> None:
    _seed()
    r = client.get("/leaderboard?min_points=101")
    assert r.status_code == 200
    assert r.json() == []


def test_min_points_invalid_values() -> None:
    for value in ("-1", "100001", "abc"):
        assert client.get(f"/leaderboard?min_points={value}").status_code == 422


def test_min_points_boundaries() -> None:
    assert client.get("/leaderboard?min_points=0").status_code == 200
    assert client.get("/leaderboard?min_points=100000").status_code == 200


def test_rejects_bad_input() -> None:
    assert client.post("/scores", json={"name": "", "points": 10}).status_code == 422
    assert client.get("/leaderboard?limit=0").status_code == 422
