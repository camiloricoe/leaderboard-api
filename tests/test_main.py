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


def _rename(old: str, body: dict) -> object:
    return client.patch(f"/players/{old}", json=body)


def test_rename_happy_path() -> None:
    client.post("/scores", json={"name": "ana", "points": 30})
    r = _rename("ana", {"new_name": "bea"})
    assert r.status_code == 200
    assert r.json() == {"name": "bea", "total": 30}
    assert client.get("/leaderboard").json() == [{"name": "bea", "points": 30}]


def test_rename_preserves_summed_total() -> None:
    client.post("/scores", json={"name": "ana", "points": 10})
    client.post("/scores", json={"name": "ana", "points": 15})
    assert _rename("ana", {"new_name": "bea"}).json() == {"name": "bea", "total": 25}


def test_rename_empty_store_404_creates_nothing() -> None:
    r = _rename("ghost", {"new_name": "bea"})
    assert r.status_code == 404
    assert "detail" in r.json()
    assert client.get("/leaderboard").json() == []


def test_rename_unknown_with_other_players_404() -> None:
    client.post("/scores", json={"name": "ana", "points": 5})
    assert _rename("ghost", {"new_name": "bea"}).status_code == 404


def test_rename_conflict_409_keeps_totals() -> None:
    client.post("/scores", json={"name": "ana", "points": 5})
    client.post("/scores", json={"name": "bea", "points": 7})
    assert _rename("ana", {"new_name": "bea"}).status_code == 409
    top = client.get("/leaderboard").json()
    assert {"name": "ana", "points": 5} in top
    assert {"name": "bea", "points": 7} in top


def test_rename_to_same_name_409() -> None:
    client.post("/scores", json={"name": "ana", "points": 5})
    assert _rename("ana", {"new_name": "ana"}).status_code == 409


def test_rename_invalid_new_name_422() -> None:
    client.post("/scores", json={"name": "ana", "points": 5})
    for body in ({"new_name": ""}, {"new_name": "x" * 41}, {}, {"new_name": 5}):
        assert _rename("ana", body).status_code == 422


def test_rename_invalid_path_name_422() -> None:
    assert _rename("x" * 41, {"new_name": "bea"}).status_code == 422


def test_rename_accepts_40_char_names() -> None:
    old, new = "a" * 40, "b" * 40
    client.post("/scores", json={"name": old, "points": 4})
    r = _rename(old, {"new_name": new})
    assert r.status_code == 200
    assert r.json() == {"name": new, "total": 4}
