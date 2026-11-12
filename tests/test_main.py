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


def _seed() -> None:
    for name, pts in (("ana", 10), ("leo", 30), ("bea", 20)):
        client.post("/scores", json={"name": name, "points": pts})


def _names(path: str) -> list[str]:
    return [p["name"] for p in client.get(path).json()]


def test_leaderboard_default_is_desc() -> None:
    _seed()
    assert _names("/leaderboard") == ["leo", "bea", "ana"]


def test_leaderboard_explicit_desc_matches_default() -> None:
    _seed()
    explicit = client.get("/leaderboard?order=desc").json()
    assert explicit == client.get("/leaderboard").json()


def test_leaderboard_asc() -> None:
    _seed()
    assert _names("/leaderboard?order=asc") == ["ana", "bea", "leo"]


def test_leaderboard_limit_applies_after_sorting() -> None:
    _seed()
    assert _names("/leaderboard?order=asc&limit=2") == ["ana", "bea"]
    assert _names("/leaderboard?order=desc&limit=2") == ["leo", "bea"]


def test_leaderboard_order_empty_store() -> None:
    for order in ("asc", "desc"):
        r = client.get("/leaderboard?order=" + order)
        assert r.status_code == 200
        assert r.json() == []


def test_leaderboard_invalid_order() -> None:
    for order in ("up", "ASC", ""):
        assert client.get("/leaderboard?order=" + order).status_code == 422


def test_leaderboard_invalid_limit_with_valid_order() -> None:
    assert client.get("/leaderboard?order=asc&limit=0").status_code == 422
    assert client.get("/leaderboard?order=desc&limit=101").status_code == 422
