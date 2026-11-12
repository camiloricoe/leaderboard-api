"""Community-event leaderboard. Demo app for the software-factory talk."""
from typing import Annotated

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from app.store import STORE

app = FastAPI(title="Leaderboard")

Name = Annotated[str, Field(min_length=1, max_length=40)]


class ScoreIn(BaseModel):
    name: Name
    points: int = Field(ge=0, le=1000)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/scores")
def add_score(score: ScoreIn) -> dict:
    STORE.add(score.name, score.points)
    return {"name": score.name, "total": STORE.total(score.name)}


@app.delete("/scores/{name}", status_code=204)
def delete_score(name: Name) -> Response:
    if not STORE.remove(name):
        raise HTTPException(status_code=404, detail="player not found")
    return Response(status_code=204)


@app.get("/leaderboard")
def leaderboard(limit: int = 10) -> list[dict]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be 1-100")
    return STORE.top(limit)
