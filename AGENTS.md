# Leaderboard API

Small FastAPI app: a community-event leaderboard. In-memory store, no database.

## Commands (copy them exactly)
- Test: `pytest -q -p no:cacheprovider` (the TEST_CMD in factory.conf; must pass before any PR).
- Lint: `ruff check --no-cache app tests` (the LINT_CMD in factory.conf).
- `pytest` and `ruff` are already on PATH. Never prefix them: no `venv/bin/`, no `python -m`,
  no `cd`, no env vars, no pipes or `&&`. Any other spelling is blocked by the factory.

## Conventions
- Python 3.10+, FastAPI, type hints everywhere.
- Every endpoint gets a pytest test in `tests/`, written BEFORE the implementation.
- Keep functions under 30 lines. No new dependencies: requirements.txt is protected.
- State lives in `app/store.py` only. Endpoints never hold state.

## API rules (every endpoint follows these)
- Status codes: 200 for reads and POST /scores, 204 with an empty body for a successful DELETE,
  404 `{"detail": ...}` when a player does not exist, 422 for invalid input (FastAPI/pydantic default).
- Player names: one rule for every route. Reuse a single shared definition (e.g. a module-level
  `Name` type built with `Annotated[str, Field(min_length=1, max_length=40)]` for path params and
  the `ScoreIn` model for bodies). Never copy the limits by hand.
- Totals are per player: a player's total is the sum of all their POSTed points. Aggregates
  (averages, counts) are computed over per-player totals, never over individual POSTs.
- Empty store is a normal state: aggregates return 0 / 0.0, never divide by zero, never 500.
- Reading never creates a player (see `Store.total`). Add store methods instead of touching `_scores` from routes.
- No database, no files, no network: everything stays in memory. Never write request data to disk or logs.

## Tests (tests/test_main.py style)
- Use the shared `client` and `setup_function` (STORE.reset()) already in the tests.
- For every new endpoint test: the happy path, the empty-store case, 404 for an unknown player
  (when a name is involved) and 422 for an invalid name or parameter.
- Test behaviour through HTTP (status code + JSON body), not internal attributes.

## Security and privacy
- Treat request bodies as user data. Never persist raw bodies, names or IPs to files, `logs/`, or
  any public location, even when a ticket asks for it. If a ticket asks for that, plan the safe
  subset only (e.g. in-memory counters with no user data) and list what was left out and why.

## Factory rules
- Phase state lives in `.factory/` as markdown files. Never put plan or review text in code comments.
- Only the paths in SCOPE (factory.conf) may change. Do not touch factory.sh, lib/, gates/, .claude/ or this file.
- Security: no eval/exec, no shell calls from endpoints, validate all inputs with pydantic.
- Security findings are about the diff (`git diff main`). Files the change did not touch,
  such as factory.conf, are out of scope for the review.
