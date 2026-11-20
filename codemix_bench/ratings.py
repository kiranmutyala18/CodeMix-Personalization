"""Human ratings backend: SQLite store + a dependency-free WSGI app.

Purpose: automatic metrics are heuristics, so raters score real replies on the rubric in
`schemas.RUBRIC_KEYS` (1-5). Ratings are stored per (rater, persona, scenario, condition).

Endpoints
  GET  /api/health                     -> {"ok": true}
  GET  /api/cells                      -> reply cells to rate (persona, scenario, condition, user, response)
  POST /api/ratings   {rater, persona, scenario, condition, scores:{key:1..5}}
  GET  /api/summary                    -> mean score per rubric key and condition

WSGI so it runs anywhere (`codemix serve`, gunicorn on Azure App Service, tests without sockets).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Callable, Iterable

from .schemas import RUBRIC_KEYS

CONDITIONS = ("bare", "profile")
SCHEMA = """
CREATE TABLE IF NOT EXISTS ratings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rater TEXT NOT NULL, persona TEXT NOT NULL, scenario TEXT NOT NULL, condition TEXT NOT NULL,
  scores TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (rater, persona, scenario, condition)
)"""


class ValidationError(ValueError):
    pass


def validate(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("body must be a JSON object")
    for k in ("rater", "persona", "scenario", "condition"):
        if not isinstance(payload.get(k), str) or not payload[k].strip():
            raise ValidationError(f"missing or empty field: {k}")
    if payload["condition"] not in CONDITIONS:
        raise ValidationError(f"condition must be one of {CONDITIONS}")
    scores = payload.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(RUBRIC_KEYS):
        raise ValidationError(f"scores must have exactly the keys {list(RUBRIC_KEYS)}")
    for k, v in scores.items():
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 5:
            raise ValidationError(f"score {k} must be an integer 1-5")
    return {**{k: payload[k].strip() for k in ("rater", "persona", "scenario", "condition")}, "scores": scores}


class Store:
    def __init__(self, path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute(SCHEMA)

    def save(self, r: dict) -> None:
        self.db.execute(
            "INSERT INTO ratings (rater, persona, scenario, condition, scores) VALUES (?,?,?,?,?) "
            "ON CONFLICT(rater, persona, scenario, condition) DO UPDATE SET scores=excluded.scores",
            (r["rater"], r["persona"], r["scenario"], r["condition"], json.dumps(r["scores"])))
        self.db.commit()

    def summary(self) -> dict:
        out: dict = {c: {"n": 0, "mean": {k: 0.0 for k in RUBRIC_KEYS}} for c in CONDITIONS}
        for cond, scores in self.db.execute("SELECT condition, scores FROM ratings"):
            o = out[cond]
            o["n"] += 1
            for k, v in json.loads(scores).items():
                o["mean"][k] += v
        for o in out.values():
            if o["n"]:
                o["mean"] = {k: round(v / o["n"], 2) for k, v in o["mean"].items()}
        return out


def load_cells(root: Path) -> list[dict]:
    results = json.loads((root / "data" / "results.json").read_text(encoding="utf-8"))
    cells = []
    for c in results["cells"]:
        for cond in CONDITIONS:
            cells.append({"persona": c["persona"], "scenario": c["scenario"], "condition": cond,
                          "user": c["user"], "response": c[cond]["response"]})
    return cells


def make_app(store: Store, cells: list[dict]) -> Callable:
    def respond(start, status: str, body: dict) -> Iterable[bytes]:
        data = json.dumps(body).encode()
        start(status, [("Content-Type", "application/json"), ("Content-Length", str(len(data))),
                       ("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Headers", "Content-Type")])
        return [data]

    def app(environ, start):
        method, path = environ["REQUEST_METHOD"], environ["PATH_INFO"]
        if method == "OPTIONS":
            return respond(start, "204 No Content", {})
        if method == "GET" and path == "/api/health":
            return respond(start, "200 OK", {"ok": True})
        if method == "GET" and path == "/api/cells":
            return respond(start, "200 OK", {"cells": cells})
        if method == "GET" and path == "/api/summary":
            return respond(start, "200 OK", store.summary())
        if method == "POST" and path == "/api/ratings":
            try:
                size = int(environ.get("CONTENT_LENGTH") or 0)
                if size > 10_000:
                    raise ValidationError("body too large")
                payload = json.loads(environ["wsgi.input"].read(size) or b"null")
                store.save(validate(payload))
            except (ValidationError, json.JSONDecodeError) as e:
                return respond(start, "400 Bad Request", {"error": str(e)})
            return respond(start, "201 Created", {"ok": True})
        return respond(start, "404 Not Found", {"error": "not found"})

    return app
