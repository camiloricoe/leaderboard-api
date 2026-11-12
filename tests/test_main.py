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


def _board() -> list[dict]:
    return client.get("/leaderboard").json()


def test_put_replaces_total() -> None:
    client.post("/scores", json={"name": "ana", "points": 50})
    r = client.put("/scores/ana", json={"points": 10})
    assert r.status_code == 200
    assert r.json() == {"name": "ana", "total": 10}
    assert _board() == [{"name": "ana", "points": 10}]


def test_put_can_raise_total() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    r = client.put("/scores/ana", json={"points": 500})
    assert r.json() == {"name": "ana", "total": 500}


def test_put_boundaries() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    assert client.put("/scores/ana", json={"points": 0}).status_code == 200
    assert client.put("/scores/ana", json={"points": 1000}).status_code == 200


def test_put_unknown_player_empty_store() -> None:
    r = client.put("/scores/ghost", json={"points": 5})
    assert r.status_code == 404
    assert "detail" in r.json()
    assert _board() == []


def test_put_unknown_player_keeps_others() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    assert client.put("/scores/ghost", json={"points": 5}).status_code == 404
    assert _board() == [{"name": "ana", "points": 10}]


def test_put_invalid_points_422() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    for body in ({"points": -1}, {"points": 1001}, {"points": "abc"}, {}):
        assert client.put("/scores/ana", json=body).status_code == 422
    assert client.put("/scores/ana").status_code == 422
    assert _board() == [{"name": "ana", "points": 10}]


def test_put_name_length() -> None:
    ok = "a" * 40
    client.post("/scores", json={"name": ok, "points": 10})
    assert client.put(f"/scores/{ok}", json={"points": 7}).status_code == 200
    assert client.put(f"/scores/{'a' * 41}", json={"points": 7}).status_code == 422


def test_post_after_put_adds() -> None:
    client.post("/scores", json={"name": "ana", "points": 50})
    client.put("/scores/ana", json={"points": 10})
    r = client.post("/scores", json={"name": "ana", "points": 5})
    assert r.json() == {"name": "ana", "total": 15}
