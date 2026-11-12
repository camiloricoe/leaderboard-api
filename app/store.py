"""In-memory score store. All state lives here, per AGENTS.md."""
from collections import defaultdict


class Store:
    def __init__(self) -> None:
        self._scores: dict[str, int] = defaultdict(int)

    def add(self, name: str, points: int) -> None:
        self._scores[name] += points

    def add_many(self, entries: list[tuple[str, int]]) -> list[int]:
        totals: list[int] = []
        for name, points in entries:
            self.add(name, points)
            totals.append(self.total(name))
        return totals

    def total(self, name: str) -> int:
        return self._scores.get(name, 0)  # reading must not create a 0-point player

    def top(self, limit: int) -> list[dict]:
        ranked = sorted(self._scores.items(), key=lambda kv: kv[1], reverse=True)
        return [{"name": n, "points": p} for n, p in ranked[:limit]]

    def reset(self) -> None:
        self._scores.clear()


STORE = Store()
