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


def _seed_three() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "leo", "points": 30})
    client.post("/scores", json={"name": "bea", "points": 20})


def test_offset_skips_ranked_players() -> None:
    _seed_three()
    r = client.get("/leaderboard?limit=2&offset=1")
    assert r.status_code == 200
    assert r.json() == [
        {"name": "bea", "points": 20},
        {"name": "ana", "points": 10},
    ]


def test_offset_default_matches_zero() -> None:
    _seed_three()
    base = client.get("/leaderboard").json()
    assert client.get("/leaderboard?offset=0").json() == base
    assert base[0] == {"name": "leo", "points": 30}
    assert len(base) == 3


def test_offset_empty_store() -> None:
    for q in ("offset=0", "offset=5"):
        r = client.get(f"/leaderboard?{q}")
        assert r.status_code == 200
        assert r.json() == []


def test_offset_beyond_players() -> None:
    _seed_three()
    r = client.get("/leaderboard?offset=3")
    assert r.status_code == 200
    assert r.json() == []


def test_offset_boundaries() -> None:
    assert client.get("/leaderboard?offset=0").status_code == 200
    assert client.get("/leaderboard?offset=1000").status_code == 200


def test_offset_invalid() -> None:
    for v in ("-1", "1001", "abc"):
        assert client.get(f"/leaderboard?offset={v}").status_code == 422
