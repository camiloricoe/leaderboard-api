"""In-memory score store. All state lives here, per AGENTS.md."""
from collections import defaultdict


class Store:
    def __init__(self) -> None:
        self._scores: dict[str, int] = defaultdict(int)

    def add(self, name: str, points: int) -> None:
        self._scores[name] += points

    def total(self, name: str) -> int:
        return self._scores.get(name, 0)  # reading must not create a 0-point player

    def top(self, limit: int, min_points: int = 0) -> list[dict]:
        ranked = sorted(self._scores.items(), key=lambda kv: kv[1], reverse=True)
        kept = [(n, p) for n, p in ranked if p >= min_points]
        return [{"name": n, "points": p} for n, p in kept[:limit]]

    def reset(self) -> None:
        self._scores.clear()


STORE = Store()
