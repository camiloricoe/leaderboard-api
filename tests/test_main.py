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


def _batch(entries: list) -> object:
    return client.post("/scores/batch", json=entries)


def test_batch_happy_path() -> None:
    assert client.get("/leaderboard").json() == []
    r = _batch([{"name": "ana", "points": 5}, {"name": "bob", "points": 7}])
    assert r.status_code == 200
    assert r.json() == [{"name": "ana", "total": 5}, {"name": "bob", "total": 7}]


def test_batch_running_totals() -> None:
    r = _batch([{"name": "ana", "points": 5}, {"name": "ana", "points": 3}])
    assert r.json() == [{"name": "ana", "total": 5}, {"name": "ana", "total": 8}]
    assert client.get("/leaderboard").json() == [{"name": "ana", "points": 8}]


def test_batch_adds_to_existing() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    r = _batch([{"name": "ana", "points": 5}])
    assert r.status_code == 200
    assert r.json() == [{"name": "ana", "total": 15}]


def test_batch_size_limits() -> None:
    assert _batch([{"name": "a", "points": 1}]).status_code == 200
    STORE.reset()
    assert _batch([{"name": "a", "points": 1}] * 50).status_code == 200
    STORE.reset()
    assert _batch([]).status_code == 422
    assert _batch([{"name": "a", "points": 1}] * 51).status_code == 422
    assert client.get("/leaderboard").json() == []


def test_batch_invalid_entry_is_atomic() -> None:
    bad = [
        {"name": "", "points": 1},
        {"name": "x" * 41, "points": 1},
        {"name": "b", "points": -1},
        {"name": "b", "points": 1001},
        {"name": "b", "points": "many"},
        {"name": "b"},
    ]
    for entry in bad:
        r = _batch([{"name": "ana", "points": 5}, entry])
        assert r.status_code == 422
        assert client.get("/leaderboard").json() == []


def test_batch_wrong_shape() -> None:
    r = client.post("/scores/batch", json={"name": "ana", "points": 5})
    assert r.status_code == 422
