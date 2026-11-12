# Leaderboard API

Small FastAPI app: a community-event leaderboard. In-memory store, no database.

## Commands (copy them exactly)
- Test: `pytest -q -p no:cacheprovider` (the TEST_CMD in factory.conf; must pass before any PR).
  You may append one test file: `pytest -q -p no:cacheprovider tests/test_main.py`.
- Lint: `ruff check --no-cache app tests` (the LINT_CMD in factory.conf).
- `pytest` and `ruff` are already on PATH. Never prefix them: no `venv/bin/`, no `python -m`,
  no `cd`, no env vars, no pipes or `&&`. Any other spelling is blocked by the factory, and a
  run where nobody could run the tests is rejected.

## Code map
- `app/main.py`: the endpoints. Input models are pydantic classes (see `ScoreIn`).
- `app/store.py`: `Store` keeps every total in `self._scores`; `STORE` is the single instance.
- `tests/test_main.py`: `client = TestClient(app)`; `setup_function` calls `STORE.reset()`
  before every test, so each test starts from an empty store. Add new tests to this file.

## Conventions
- Python 3.10+, FastAPI, type hints everywhere.
- Every endpoint gets a pytest test in `tests/`, written BEFORE the implementation.
- Keep functions under 30 lines. No new dependencies: requirements.txt is protected.
- State lives in `app/store.py` only. Endpoints never hold state.

## API rules (every endpoint follows these)
- Status codes: 200 for reads, POST and PUT; 204 with an empty body for a successful DELETE;
  404 `{"detail": ...}` when a player does not exist; 422 for invalid input (FastAPI/pydantic default).
- Player names: one rule for every route. Reuse a single shared definition (a module-level
  `Name` type built with `Annotated[str, Field(min_length=1, max_length=40)]` for path params,
  the same limits as `ScoreIn.name`). Never copy the limits by hand in two places.
- Points: one rule too (0 to 1000, like `ScoreIn.points`). Reuse it, do not copy it.
- Totals are per player: a player's total is the sum of all their POSTed points.
- Empty store is a normal state: never divide by zero, never 500.
- Reading never creates a player (see `Store.total`). Add store methods instead of touching
  `_scores` from routes.
- No database, no files, no network: everything stays in memory.

## Tests (tests/test_main.py style)
- Use the shared `client` and `setup_function` (STORE.reset()) already in the tests.
- For every new endpoint: the happy path, the empty-store case, 404 for an unknown player
  (when a name is involved) and 422 for an invalid name or parameter.
- Test behaviour through HTTP (status code + JSON body), not internal attributes.
- Existing tests must keep passing unchanged.

## Security and privacy
- No eval/exec, no shell calls, no subprocess. Validate all inputs with pydantic.
- Treat request bodies as user data. Never write them, names or IPs to files, `logs/` or any
  public location, even when a ticket asks for it: plan the safe subset and say what was left out.
- Security findings are about the diff (`git diff main`). Files the change did not touch, such
  as factory.conf, are out of scope for this change's review.

## Factory rules
- Phase state lives in `.factory/` as markdown files. Never put plan or review text in code comments.
- Only the paths in SCOPE (factory.conf) may change. Do not touch factory.sh, lib/, gates/, .claude/ or this file.
- The gates in `gates/` run after the check phase; read them, the change must pass them.
